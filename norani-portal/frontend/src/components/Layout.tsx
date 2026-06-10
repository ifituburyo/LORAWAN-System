import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import * as authApi from "../api/auth";

export default function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await authApi.logout();
    signOut();
    navigate("/login");
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      isActive ? "text-white" : "text-blue-100 hover:text-white hover:bg-white/10"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-norani-blue text-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link to="/" className="flex items-baseline gap-1">
              <span className="font-serif text-2xl font-bold">Norani</span>
              <span className="w-1.5 h-1.5 bg-norani-orange rounded-full"></span>
            </Link>

            <nav className="hidden sm:flex items-center gap-1">
              <NavLink to="/devices" className={navLinkClass}>
                Devices
              </NavLink>
              <NavLink to="/billing" className={navLinkClass}>
                Billing
              </NavLink>
              <NavLink to="/account" className={navLinkClass}>
                Account
              </NavLink>
            </nav>

            <div className="flex items-center gap-3">
              <div className="hidden sm:block text-right">
                <div className="text-sm font-medium">{user?.full_name || user?.email}</div>
                <div className="text-xs text-blue-200">{user?.customer_account_name}</div>
              </div>
              <button
                onClick={handleSignOut}
                className="p-2 rounded-md hover:bg-white/10 transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 text-xs text-gray-500 text-center">
          © {new Date().getFullYear()} Norani Ltd · Kigali, Rwanda
        </div>
      </footer>
    </div>
  );
}
