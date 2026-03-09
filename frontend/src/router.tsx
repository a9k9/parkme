import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/app-shell";
import { AnalyticsPage } from "@/pages/analytics";
import { BookingsPage } from "@/pages/bookings";
import { DashboardPage } from "@/pages/dashboard";
import { ParkingManagementPage } from "@/pages/parking-management";
import { ParkingMapPage } from "@/pages/parking-map";
import { PricingPage } from "@/pages/pricing";
import { LoginPage } from "@/pages/login";
import { RequireAuth } from "@/lib/auth-context";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "map", element: <ParkingMapPage /> },
      { path: "parking", element: <ParkingManagementPage /> },
      { path: "bookings", element: <BookingsPage /> },
      { path: "pricing", element: <PricingPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
    ],
  },
]);
