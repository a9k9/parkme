import { useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFacilitiesList } from "@/api/generated/api/api";

const center: [number, number] = [37.7749, -122.4194];

type MapFacility = {
  id: string;
  name: string;
  capacity: number;
  available: number;
  position: [number, number];
};

const markerIcon = new L.Icon({
  iconUrl: new URL("leaflet/dist/images/marker-icon.png", import.meta.url).href,
  iconRetinaUrl: new URL(
    "leaflet/dist/images/marker-icon-2x.png",
    import.meta.url,
  ).href,
  shadowUrl: new URL("leaflet/dist/images/marker-shadow.png", import.meta.url)
    .href,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export function ParkingMapPage() {
  const facilitiesQuery = useQuery({
    queryKey: ["facilities"],
    queryFn: () => apiFacilitiesList(),
    staleTime: 60_000,
  });

  const markers = useMemo<MapFacility[]>(() => {
    const facilities = facilitiesQuery.data?.data?.results ?? [];
    return facilities
      .map((facility) => {
        const latitude = facility.latitude
          ? Number.parseFloat(facility.latitude)
          : null;
        const longitude = facility.longitude
          ? Number.parseFloat(facility.longitude)
          : null;
        if (latitude === null || longitude === null) {
          return null;
        }
        return {
          id: facility.id,
          name: facility.name,
          capacity: facility.total_spots ?? 0,
          available: facility.available_spots ?? 0,
          position: [latitude, longitude] as [number, number],
        };
      })
      .filter((facility): facility is MapFacility => Boolean(facility));
  }, [facilitiesQuery.data]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Parking Map</h1>
        <p className="text-sm text-muted-foreground">
          Monitor live occupancy by location.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Active locations</CardTitle>
        </CardHeader>
        <CardContent>
          {markers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {facilitiesQuery.isLoading
                ? "Loading facilities..."
                : "No facilities with map coordinates available."}
            </p>
          ) : (
            <div className="h-[520px] w-full overflow-hidden rounded-lg">
              <MapContainer center={center} zoom={14} className="h-full w-full">
                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {markers.map((lot) => (
                  <Marker
                    key={lot.id}
                    position={lot.position}
                    icon={markerIcon}
                  >
                    <Popup>
                      <div className="text-sm">
                        <p className="font-semibold">{lot.name}</p>
                        <p>Capacity: {lot.capacity}</p>
                        <p>Available: {lot.available}</p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
