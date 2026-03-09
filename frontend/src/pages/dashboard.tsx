import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiBookingsList, apiFacilitiesList } from "@/api/generated/api/api";
import { BookingStatusEnum } from "@/api/generated/schemas/bookingStatusEnum";

export function DashboardPage() {
  const facilitiesQuery = useQuery({
    queryKey: ["facilities"],
    queryFn: () => apiFacilitiesList(),
    staleTime: 60_000,
  });

  const bookingsQuery = useQuery({
    queryKey: ["bookings"],
    queryFn: () => apiBookingsList(),
    staleTime: 30_000,
  });

  const stats = useMemo(() => {
    const facilities = facilitiesQuery.data?.data?.results ?? [];
    const facilityCount =
      facilitiesQuery.data?.data?.count ?? facilities.length;
    const totalSpots = facilities.reduce(
      (sum, facility) => sum + (facility.total_spots ?? 0),
      0,
    );
    const availableSpots = facilities.reduce(
      (sum, facility) => sum + (facility.available_spots ?? 0),
      0,
    );
    const occupiedSpots = totalSpots - availableSpots;

    const bookings = bookingsQuery.data?.data?.results ?? [];
    const activeBookings = bookings.filter(
      (booking) => booking.status === BookingStatusEnum.ACTIVE,
    ).length;
    const completedBookings = bookings.filter(
      (booking) => booking.status === BookingStatusEnum.COMPLETED,
    ).length;

    return [
      {
        label: "Active facilities",
        value: facilityCount.toLocaleString(),
        delta: `${availableSpots.toLocaleString()} available spots`,
      },
      {
        label: "Occupied spots",
        value: occupiedSpots.toLocaleString(),
        delta: `${availableSpots.toLocaleString()} open`,
      },
      {
        label: "Active bookings",
        value: activeBookings.toLocaleString(),
        delta: `${completedBookings.toLocaleString()} completed`,
      },
      {
        label: "Total bookings",
        value: bookings.length.toLocaleString(),
        delta: "Latest page of results",
      },
    ];
  }, [bookingsQuery.data, facilitiesQuery.data]);

  const apiStatus =
    facilitiesQuery.isLoading || bookingsQuery.isLoading
      ? "Checking"
      : facilitiesQuery.isError || bookingsQuery.isError
        ? "Offline"
        : "Connected";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Real-time overview of parking operations.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => (
          <Card key={item.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {item.label}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <span className="text-2xl font-semibold">{item.value}</span>
              <Badge variant="secondary">{item.delta}</Badge>
            </CardContent>
          </Card>
        ))}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              API status
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <span className="text-2xl font-semibold">{apiStatus}</span>
            <Badge
              variant={apiStatus === "Connected" ? "secondary" : "destructive"}
            >
              {apiStatus}
            </Badge>
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s highlights</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm text-muted-foreground">
          <p>Peak occupancy reached at 5:45 PM in Downtown Zone.</p>
          <p>3 new enforcement requests were opened across West Side lots.</p>
          <p>Average session length is holding steady at 1h 24m.</p>
        </CardContent>
      </Card>
    </div>
  );
}
