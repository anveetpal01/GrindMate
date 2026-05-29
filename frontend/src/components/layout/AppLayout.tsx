import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { Code2, LogOut, Trophy, Users } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const APP_NAME = import.meta.env.VITE_APP_NAME || "GrindMate";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: Trophy },
  { to: "/groups", label: "Groups", icon: Users },
  { to: "/account", label: "Account", icon: Code2 },
];

export function AppLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur sticky top-0 z-40">
        <div className="container flex h-16 items-center justify-between gap-6">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Trophy className="h-5 w-5" />
            </div>
            <span className="font-bold text-lg">{APP_NAME}</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-secondary text-secondary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground hidden sm:inline">
              @{user?.username}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              aria-label="Log out"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <Outlet />
      </main>
    </div>
  );
}
