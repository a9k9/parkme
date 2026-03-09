import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  apiFacilitiesCreate,
  apiFacilitiesList,
  apiParkingSpotsCreate,
  apiZonesCreate,
  apiZonesList,
} from "@/api/generated/api/api";
import { FacilityTypeEnum } from "@/api/generated/schemas/facilityTypeEnum";
import { SizeEnum } from "@/api/generated/schemas/sizeEnum";

const facilityTypeOptions = Object.values(FacilityTypeEnum);
const sizeOptions = Object.values(SizeEnum);

const parseOptionalNumberString = (value: string) =>
  value.trim().length > 0 ? value.trim() : undefined;

const parseOptionalInteger = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
};

export function ParkingManagementPage() {
  const queryClient = useQueryClient();
  const [facilityForm, setFacilityForm] = useState({
    name: "",
    address: "",
    city: "",
    state: "",
    postal_code: "",
    owner: "",
    country: "",
    phone: "",
    email: "",
    latitude: "",
    longitude: "",
    facility_type: "",
    is_active: true,
    has_cctv: false,
    has_covered_parking: false,
    has_ev_charging: false,
    has_security: false,
    has_valet: false,
  });

  const [spotForm, setSpotForm] = useState({
    spot_number: "",
    zone: "",
    size: "",
    is_active: true,
    is_accessible: false,
    is_covered: false,
    is_vip: false,
    has_ev_charger: false,
  });

  const [zoneForm, setZoneForm] = useState({
    name: "",
    code: "",
    facility: "",
    description: "",
    display_order: "",
    is_active: true,
    is_accessible: false,
    is_covered: false,
  });

  const facilitiesQuery = useQuery({
    queryKey: ["facilities"],
    queryFn: () => apiFacilitiesList(),
    staleTime: 60_000,
  });

  const zonesQuery = useQuery({
    queryKey: ["zones"],
    queryFn: () => apiZonesList(),
    staleTime: 60_000,
  });

  const facilityMutation = useMutation({
    mutationFn: () =>
      apiFacilitiesCreate({
        name: facilityForm.name,
        address: facilityForm.address,
        city: facilityForm.city,
        state: facilityForm.state,
        postal_code: facilityForm.postal_code,
        owner: facilityForm.owner,
        country: facilityForm.country || undefined,
        phone: facilityForm.phone || undefined,
        email: facilityForm.email || undefined,
        latitude: parseOptionalNumberString(facilityForm.latitude) ?? null,
        longitude: parseOptionalNumberString(facilityForm.longitude) ?? null,
        facility_type:
          facilityForm.facility_type.length > 0
            ? (facilityForm.facility_type as FacilityTypeEnum)
            : undefined,
        is_active: facilityForm.is_active,
        has_cctv: facilityForm.has_cctv,
        has_covered_parking: facilityForm.has_covered_parking,
        has_ev_charging: facilityForm.has_ev_charging,
        has_security: facilityForm.has_security,
        has_valet: facilityForm.has_valet,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["facilities"] });
      setFacilityForm((previous) => ({
        ...previous,
        name: "",
        address: "",
        city: "",
        state: "",
        postal_code: "",
        owner: "",
        country: "",
        phone: "",
        email: "",
        latitude: "",
        longitude: "",
        facility_type: "",
      }));
    },
  });

  const spotMutation = useMutation({
    mutationFn: () =>
      apiParkingSpotsCreate({
        spot_number: spotForm.spot_number,
        zone: spotForm.zone,
        size:
          spotForm.size.length > 0 ? (spotForm.size as SizeEnum) : undefined,
        is_active: spotForm.is_active,
        is_accessible: spotForm.is_accessible,
        is_covered: spotForm.is_covered,
        is_vip: spotForm.is_vip,
        has_ev_charger: spotForm.has_ev_charger,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["spots"] });
      setSpotForm((previous) => ({
        ...previous,
        spot_number: "",
      }));
    },
  });

  const zoneMutation = useMutation({
    mutationFn: () =>
      apiZonesCreate({
        name: zoneForm.name,
        code: zoneForm.code,
        facility: zoneForm.facility,
        description: zoneForm.description || undefined,
        display_order: parseOptionalInteger(zoneForm.display_order),
        is_active: zoneForm.is_active,
        is_accessible: zoneForm.is_accessible,
        is_covered: zoneForm.is_covered,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["zones"] });
      setZoneForm((previous) => ({
        ...previous,
        name: "",
        code: "",
        facility: "",
        description: "",
        display_order: "",
      }));
    },
  });

  const facilityError = facilityMutation.error
    ? facilityMutation.error instanceof Error
      ? facilityMutation.error.message
      : "Unable to create facility."
    : null;

  const spotError = spotMutation.error
    ? spotMutation.error instanceof Error
      ? spotMutation.error.message
      : "Unable to create spot."
    : null;

  const zoneError = zoneMutation.error
    ? zoneMutation.error instanceof Error
      ? zoneMutation.error.message
      : "Unable to create zone."
    : null;

  const facilityOptions = useMemo(() => {
    const facilities = facilitiesQuery.data?.data?.results ?? [];
    return facilities.map((facility) => ({
      id: facility.id,
      label: `${facility.name} (${facility.city})`,
    }));
  }, [facilitiesQuery.data]);

  const zoneOptions = useMemo(() => {
    const zones = zonesQuery.data?.data?.results ?? [];
    return zones.map((zone) => ({
      id: zone.id,
      label: `${zone.name} (${zone.facility_name})`,
    }));
  }, [zonesQuery.data]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Parking Management</h1>
        <p className="text-sm text-muted-foreground">
          Create facilities and parking spots for your organization.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Create facility</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                facilityMutation.mutate();
              }}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Name</label>
                  <Input
                    value={facilityForm.name}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        name: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Owner ID</label>
                  <Input
                    value={facilityForm.owner}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        owner: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Address</label>
                  <Input
                    value={facilityForm.address}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        address: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">City</label>
                  <Input
                    value={facilityForm.city}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        city: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">State</label>
                  <Input
                    value={facilityForm.state}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        state: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Postal code</label>
                  <Input
                    value={facilityForm.postal_code}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        postal_code: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Country</label>
                  <Input
                    value={facilityForm.country}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        country: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Facility type</label>
                  <select
                    className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    value={facilityForm.facility_type}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        facility_type: event.target.value,
                      }))
                    }
                  >
                    <option value="">Select type</option>
                    {facilityTypeOptions.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Latitude</label>
                  <Input
                    value={facilityForm.latitude}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        latitude: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Longitude</label>
                  <Input
                    value={facilityForm.longitude}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        longitude: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Phone</label>
                  <Input
                    value={facilityForm.phone}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        phone: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    value={facilityForm.email}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        email: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="grid gap-2 md:grid-cols-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.is_active}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        is_active: event.target.checked,
                      }))
                    }
                  />
                  Active
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.has_security}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        has_security: event.target.checked,
                      }))
                    }
                  />
                  On-site security
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.has_cctv}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        has_cctv: event.target.checked,
                      }))
                    }
                  />
                  CCTV
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.has_ev_charging}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        has_ev_charging: event.target.checked,
                      }))
                    }
                  />
                  EV charging
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.has_covered_parking}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        has_covered_parking: event.target.checked,
                      }))
                    }
                  />
                  Covered parking
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={facilityForm.has_valet}
                    onChange={(event) =>
                      setFacilityForm((previous) => ({
                        ...previous,
                        has_valet: event.target.checked,
                      }))
                    }
                  />
                  Valet service
                </label>
              </div>

              {facilityError ? (
                <p className="text-sm text-destructive">{facilityError}</p>
              ) : null}

              <Button type="submit" disabled={facilityMutation.isPending}>
                {facilityMutation.isPending
                  ? "Creating facility..."
                  : "Create facility"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create zone</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                zoneMutation.mutate();
              }}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Zone name</label>
                  <Input
                    value={zoneForm.name}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        name: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Code</label>
                  <Input
                    value={zoneForm.code}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        code: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium">Facility</label>
                  <select
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={zoneForm.facility}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        facility: event.target.value,
                      }))
                    }
                    required
                  >
                    <option value="">Select facility</option>
                    {facilityOptions.map((facility) => (
                      <option key={facility.id} value={facility.id}>
                        {facility.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium">Description</label>
                  <Input
                    value={zoneForm.description}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        description: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Display order</label>
                  <Input
                    type="number"
                    value={zoneForm.display_order}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        display_order: event.target.value,
                      }))
                    }
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="grid gap-2 md:grid-cols-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={zoneForm.is_active}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        is_active: event.target.checked,
                      }))
                    }
                  />
                  Active
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={zoneForm.is_accessible}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        is_accessible: event.target.checked,
                      }))
                    }
                  />
                  Accessible
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={zoneForm.is_covered}
                    onChange={(event) =>
                      setZoneForm((previous) => ({
                        ...previous,
                        is_covered: event.target.checked,
                      }))
                    }
                  />
                  Covered
                </label>
              </div>

              {zoneError ? (
                <p className="text-sm text-destructive">{zoneError}</p>
              ) : null}

              {facilitiesQuery.isError ? (
                <p className="text-xs text-destructive">
                  Unable to load facilities. Create a facility first.
                </p>
              ) : null}

              <Button type="submit" disabled={zoneMutation.isPending}>
                {zoneMutation.isPending ? "Creating zone..." : "Create zone"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create parking spot</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                spotMutation.mutate();
              }}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Spot number</label>
                  <Input
                    value={spotForm.spot_number}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        spot_number: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Zone</label>
                  <select
                    className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    value={spotForm.zone}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        zone: event.target.value,
                      }))
                    }
                    required
                  >
                    <option value="">Select zone</option>
                    {zoneOptions.map((zone) => (
                      <option key={zone.id} value={zone.id}>
                        {zone.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Size</label>
                  <select
                    className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    value={spotForm.size}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        size: event.target.value,
                      }))
                    }
                  >
                    <option value="">Select size</option>
                    {sizeOptions.map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid gap-2 md:grid-cols-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={spotForm.is_active}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        is_active: event.target.checked,
                      }))
                    }
                  />
                  Active
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={spotForm.is_accessible}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        is_accessible: event.target.checked,
                      }))
                    }
                  />
                  Accessible
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={spotForm.is_covered}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        is_covered: event.target.checked,
                      }))
                    }
                  />
                  Covered
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={spotForm.is_vip}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        is_vip: event.target.checked,
                      }))
                    }
                  />
                  VIP
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={spotForm.has_ev_charger}
                    onChange={(event) =>
                      setSpotForm((previous) => ({
                        ...previous,
                        has_ev_charger: event.target.checked,
                      }))
                    }
                  />
                  EV charger
                </label>
              </div>

              {spotError ? (
                <p className="text-sm text-destructive">{spotError}</p>
              ) : null}

              <Button type="submit" disabled={spotMutation.isPending}>
                {spotMutation.isPending ? "Creating spot..." : "Create spot"}
              </Button>

              {zonesQuery.isError ? (
                <p className="text-xs text-destructive">
                  Unable to load zones. Create a zone first.
                </p>
              ) : null}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
