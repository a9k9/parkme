import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactECharts from "echarts-for-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiBookingsList } from "@/api/generated/api/api";
import { BookingStatusEnum } from "@/api/generated/schemas/bookingStatusEnum";

export function AnalyticsPage() {
  const [now] = useState(() => Date.now());
  const bookingsQuery = useQuery({
    queryKey: ["bookings", "analytics"],
    queryFn: () => apiBookingsList(),
    staleTime: 60_000,
  });

  const option = useMemo(() => {
    const labels = Array.from({ length: 7 }).map((_, index) => {
      const date = new Date(now);
      date.setDate(date.getDate() - (6 - index));
      return date.toLocaleDateString(undefined, { weekday: "short" });
    });

    const revenue = Array.from({ length: 7 }).fill(0) as number[];
    const occupancy = Array.from({ length: 7 }).fill(0) as number[];

    const bookings = bookingsQuery.data?.data?.results ?? [];
    bookings.forEach((booking) => {
      const entryDate = booking.entry_time
        ? new Date(booking.entry_time as unknown as string)
        : null;
      if (!entryDate || Number.isNaN(entryDate.getTime())) {
        return;
      }
      const daysAgo = Math.floor(
        (now - entryDate.getTime()) / (24 * 60 * 60 * 1000),
      );
      if (daysAgo < 0 || daysAgo > 6) {
        return;
      }
      const index = 6 - daysAgo;
      const priceString = booking.final_price ?? booking.estimated_price;
      const price = priceString ? Number.parseFloat(priceString) : 0;
      if (!Number.isNaN(price)) {
        revenue[index] += price;
      }
      if (booking.status === BookingStatusEnum.ACTIVE) {
        occupancy[index] += 1;
      }
    });

    return {
      tooltip: { trigger: "axis" },
      legend: { data: ["Revenue", "Active bookings"] },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: labels,
      },
      yAxis: { type: "value" },
      series: [
        {
          name: "Revenue",
          type: "line",
          smooth: true,
          data: revenue.map((value) => Number(value.toFixed(2))),
        },
        {
          name: "Active bookings",
          type: "line",
          smooth: true,
          data: occupancy,
        },
      ],
    };
  }, [bookingsQuery.data, now]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Revenue and occupancy trends across the week.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Weekly performance</CardTitle>
        </CardHeader>
        <CardContent>
          {bookingsQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">
              Loading analytics...
            </p>
          ) : (
            <ReactECharts option={option} style={{ height: 420 }} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
