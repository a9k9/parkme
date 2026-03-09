import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/map", label: "Parking Map" },
  { to: "/parking", label: "Parking Management" },
  { to: "/bookings", label: "Bookings" },
  { to: "/pricing", label: "Pricing" },
  { to: "/analytics", label: "Analytics" },
];

export function AppShell() {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              P
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight">ParkMe</p>
              <p className="text-xs text-muted-foreground">
                Universal Parking Solution
              </p>
            </div>
          </div>
          <Button size="sm" variant="outline" onClick={() => logout()}>
            Sign out
          </Button>
        </div>
      </header>
      <div className="mx-auto flex max-w-7xl">
        <aside className="hidden w-60 border-r bg-card px-4 py-6 md:block">
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }: { isActive: boolean }) =>
                  cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-muted",
                    isActive && "bg-muted text-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="flex-1 px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
