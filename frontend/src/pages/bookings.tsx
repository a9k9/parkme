import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  apiBookingsDriveInCreate,
  apiBookingsList,
  apiBookingsReserveCreate,
  apiParkingSpotsList,
  apiVehiclesCreate,
  apiVehiclesList,
} from "@/api/generated/api/api";
import { BookingStatusEnum } from "@/api/generated/schemas/bookingStatusEnum";
import { BookingTypeEnum } from "@/api/generated/schemas/bookingTypeEnum";
import type { BookingRequest } from "@/api/generated/schemas/bookingRequest";
import { VehicleTypeEnum } from "@/api/generated/schemas/vehicleTypeEnum";

type BookingRow = {
  id: string;
  driver: string;
  spot: string;
  status: BookingStatusEnum;
  start: string;
  duration: string;
};

type Filters = {
  query: string;
  status: "all" | BookingStatusEnum;
};

const tableHeaders = [
  "Booking ID",
  "Driver",
  "Spot",
  "Status",
  "Start",
  "Duration",
];

const statusOptions: Array<{
  label: string;
  value: BookingStatusEnum | "all";
}> = [
  { label: "All", value: "all" },
  { label: "Pending", value: BookingStatusEnum.PENDING },
  { label: "Confirmed", value: BookingStatusEnum.CONFIRMED },
  { label: "Active", value: BookingStatusEnum.ACTIVE },
  { label: "Completed", value: BookingStatusEnum.COMPLETED },
  { label: "Cancelled", value: BookingStatusEnum.CANCELLED },
  { label: "No show", value: BookingStatusEnum.NO_SHOW },
];

const formatDateTime = (value: unknown) => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value as string);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString();
};

export function BookingsPage() {
  const queryClient = useQueryClient();
  type BookingFormState = {
    bookingType: BookingTypeEnum;
    vehicleId: string;
    spotId: string;
    entryTime: string;
    expectedExit: string;
  };
  type VehicleFormState = {
    plateNumber: string;
    vehicleType: VehicleTypeEnum;
    make: string;
    model: string;
    color: string;
    year: string;
  };
  const [filters, setFilters] = useState<Filters>({
    query: "",
    status: "all",
  });
  const [draftFilters, setDraftFilters] = useState<Filters>({
    query: "",
    status: "all",
  });
  const [bookingForm, setBookingForm] = useState<BookingFormState>({
    bookingType: BookingTypeEnum.DRIVE_IN,
    vehicleId: "",
    spotId: "",
    entryTime: "",
    expectedExit: "",
  });
  const [vehicleForm, setVehicleForm] = useState<VehicleFormState>({
    plateNumber: "",
    vehicleType: VehicleTypeEnum.CAR,
    make: "",
    model: "",
    color: "",
    year: "",
  });

  const bookingsQuery = useQuery({
    queryKey: ["bookings", filters],
    queryFn: () => apiBookingsList(),
    staleTime: 30_000,
  });

  const vehiclesQuery = useQuery({
    queryKey: ["vehicles"],
    queryFn: () => apiVehiclesList(),
    staleTime: 60_000,
  });

  const spotsQuery = useQuery({
    queryKey: ["spots", "available"],
    queryFn: () => apiParkingSpotsList({ status: "AVAILABLE" }),
    staleTime: 30_000,
  });

  const bookingMutation = useMutation({
    mutationFn: async () => {
      if (bookingForm.bookingType === BookingTypeEnum.RESERVATION) {
        const payload = {
          vehicle_id: bookingForm.vehicleId,
          spot_id: bookingForm.spotId,
          entry_time: new Date(bookingForm.entryTime).toISOString(),
          expected_exit: new Date(bookingForm.expectedExit).toISOString(),
        };
        return apiBookingsReserveCreate(payload as unknown as BookingRequest);
      }

      const payload = {
        vehicle_id: bookingForm.vehicleId,
        spot_id: bookingForm.spotId,
      };
      return apiBookingsDriveInCreate(payload as unknown as BookingRequest);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["bookings"] }),
        queryClient.invalidateQueries({ queryKey: ["spots"] }),
      ]);
      setBookingForm((previous) => ({
        ...previous,
        spotId: "",
        entryTime: "",
        expectedExit: "",
      }));
    },
  });

  const vehicleMutation = useMutation({
    mutationFn: () =>
      apiVehiclesCreate({
        plate_number: vehicleForm.plateNumber,
        vehicle_type: vehicleForm.vehicleType,
        make: vehicleForm.make || undefined,
        model: vehicleForm.model || undefined,
        color: vehicleForm.color || undefined,
        year: vehicleForm.year ? Number(vehicleForm.year) : undefined,
        is_active: true,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      setVehicleForm({
        plateNumber: "",
        vehicleType: VehicleTypeEnum.CAR,
        make: "",
        model: "",
        color: "",
        year: "",
      });
    },
  });

  const data = useMemo(() => {
    const rows: BookingRow[] =
      bookingsQuery.data?.data?.results.map((booking) => ({
        id: booking.ticket_number ?? booking.id,
        driver: booking.user_email ?? booking.user,
        spot: booking.spot_number ?? booking.spot,
        status: booking.status ?? BookingStatusEnum.PENDING,
        start: formatDateTime(booking.entry_time),
        duration: `${booking.duration}m`,
      })) ?? [];

    return rows.filter((row) => {
      const matchesQuery =
        filters.query.length === 0 ||
        row.driver.toLowerCase().includes(filters.query.toLowerCase()) ||
        row.id.toLowerCase().includes(filters.query.toLowerCase());
      const matchesStatus =
        filters.status === "all" || row.status === filters.status;
      return matchesQuery && matchesStatus;
    });
  }, [bookingsQuery.data, filters]);

  const rows = data;
  const vehicles = vehiclesQuery.data?.data?.results ?? [];
  const spots = spotsQuery.data?.data?.results ?? [];
  const bookingError = bookingMutation.error
    ? bookingMutation.error instanceof Error
      ? bookingMutation.error.message
      : "Unable to create booking."
    : null;
  const vehicleError = vehicleMutation.error
    ? vehicleMutation.error instanceof Error
      ? vehicleMutation.error.message
      : "Unable to create vehicle."
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Bookings</h1>
        <p className="text-sm text-muted-foreground">
          Review recent booking sessions and filter by status.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add vehicle</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              vehicleMutation.mutate();
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Plate number</label>
                <Input
                  value={vehicleForm.plateNumber}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      plateNumber: event.target.value.toUpperCase(),
                    }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Vehicle type</label>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={vehicleForm.vehicleType}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      vehicleType: event.target.value as VehicleTypeEnum,
                    }))
                  }
                >
                  {Object.values(VehicleTypeEnum).map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Make</label>
                <Input
                  value={vehicleForm.make}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      make: event.target.value,
                    }))
                  }
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Input
                  value={vehicleForm.model}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      model: event.target.value,
                    }))
                  }
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Color</label>
                <Input
                  value={vehicleForm.color}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      color: event.target.value,
                    }))
                  }
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Year</label>
                <Input
                  type="number"
                  value={vehicleForm.year}
                  onChange={(event) =>
                    setVehicleForm((previous) => ({
                      ...previous,
                      year: event.target.value,
                    }))
                  }
                  placeholder="Optional"
                />
              </div>
            </div>

            {vehicleError ? (
              <p className="text-sm text-destructive">{vehicleError}</p>
            ) : null}

            <Button type="submit" disabled={vehicleMutation.isPending}>
              {vehicleMutation.isPending ? "Saving vehicle..." : "Save vehicle"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create booking</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              bookingMutation.mutate();
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Booking type</label>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={bookingForm.bookingType}
                  onChange={(event) =>
                    setBookingForm((previous) => ({
                      ...previous,
                      bookingType: event.target.value as BookingTypeEnum,
                    }))
                  }
                >
                  <option value={BookingTypeEnum.DRIVE_IN}>Drive-in</option>
                  <option value={BookingTypeEnum.RESERVATION}>
                    Reservation
                  </option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Vehicle</label>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={bookingForm.vehicleId}
                  onChange={(event) =>
                    setBookingForm((previous) => ({
                      ...previous,
                      vehicleId: event.target.value,
                    }))
                  }
                  required
                >
                  <option value="">Select vehicle</option>
                  {vehicles.map((vehicle) => (
                    <option key={vehicle.id} value={vehicle.id}>
                      {vehicle.plate_number} · {vehicle.vehicle_type}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">Spot</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={bookingForm.spotId}
                  onChange={(event) =>
                    setBookingForm((previous) => ({
                      ...previous,
                      spotId: event.target.value,
                    }))
                  }
                  required
                >
                  <option value="">Select available spot</option>
                  {spots.map((spot) => (
                    <option key={spot.id} value={spot.id}>
                      {spot.spot_number} · {spot.zone_name} ·{" "}
                      {spot.facility_name}
                    </option>
                  ))}
                </select>
              </div>
              {bookingForm.bookingType === BookingTypeEnum.RESERVATION ? (
                <>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Entry time</label>
                    <Input
                      type="datetime-local"
                      value={bookingForm.entryTime}
                      onChange={(event) =>
                        setBookingForm((previous) => ({
                          ...previous,
                          entryTime: event.target.value,
                        }))
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Expected exit</label>
                    <Input
                      type="datetime-local"
                      value={bookingForm.expectedExit}
                      onChange={(event) =>
                        setBookingForm((previous) => ({
                          ...previous,
                          expectedExit: event.target.value,
                        }))
                      }
                      required
                    />
                  </div>
                </>
              ) : null}
            </div>

            {vehicles.length === 0 ? (
              <p className="text-xs text-destructive">
                No vehicles found for this user.
              </p>
            ) : null}
            {spots.length === 0 ? (
              <p className="text-xs text-destructive">
                No available spots. Try again later.
              </p>
            ) : null}
            {bookingError ? (
              <p className="text-sm text-destructive">{bookingError}</p>
            ) : null}

            <Button type="submit" disabled={bookingMutation.isPending}>
              {bookingMutation.isPending
                ? "Creating booking..."
                : "Create booking"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Search bookings</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-4 md:flex-row md:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              setFilters(draftFilters);
            }}
          >
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Search</label>
              <Input
                placeholder="Search by driver or booking ID"
                value={draftFilters.query}
                onChange={(event) =>
                  setDraftFilters((previous) => ({
                    ...previous,
                    query: event.target.value,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <select
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={draftFilters.status}
                onChange={(event) =>
                  setDraftFilters((previous) => ({
                    ...previous,
                    status: event.target.value as Filters["status"],
                  }))
                }
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <Button type="submit">Apply</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[420px] overflow-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {tableHeaders.map((header) => (
                    <TableHead key={header}>{header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={tableHeaders.length}>
                      {bookingsQuery.isLoading
                        ? "Loading bookings..."
                        : "No bookings found."}
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>{row.id}</TableCell>
                      <TableCell>{row.driver}</TableCell>
                      <TableCell>{row.spot}</TableCell>
                      <TableCell>{row.status}</TableCell>
                      <TableCell>{row.start}</TableCell>
                      <TableCell>{row.duration}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
