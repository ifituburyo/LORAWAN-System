import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Radio, Activity, AlertCircle, Plus } from "lucide-react";
import * as devicesApi from "../api/devices";
import * as billingApi from "../api/billing";
import type { DeviceList, CurrentBilling } from "../api/types";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  const { user } = useAuth();
  const [devices, setDevices] = useState<DeviceList | null>(null);
  const [billing, setBilling] = useState<CurrentBilling | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      devicesApi.listDevices({ page_size: 5 }),
      billingApi.getCurrentBilling().catch(() => null),
    ])
      .then(([dev, bill]) => {
        setDevices(dev);
        setBilling(bill);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center text-gray-500 py-12">Loading…</div>;
  }

  const activeCount = devices?.items.filter((d) => d.status === "active").length ?? 0;
  const offlineCount = devices?.items.filter((d) => d.status === "offline").length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-norani-blue">
          Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-gray-500 text-sm">{user?.customer_account_name}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<Radio className="w-5 h-5" />}
          label="Total devices"
          value={devices?.total ?? 0}
          color="blue"
        />
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Active"
          value={activeCount}
          color="green"
        />
        <StatCard
          icon={<AlertCircle className="w-5 h-5" />}
          label="Offline"
          value={offlineCount}
          color="red"
        />
      </div>

      {/* Billing summary */}
      {billing && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
              Current period
            </h2>
            <Link to="/billing" className="text-sm text-norani-blue-light hover:underline">
              View details →
            </Link>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold text-gray-900">
              {billing.amount_rwf.toLocaleString()} RWF
            </span>
            <span className="text-sm text-gray-500">
              ≈ ${billing.amount_usd.toFixed(2)} · {billing.device_count} devices
            </span>
          </div>
        </div>
      )}

      {/* Quick action */}
      <div className="card p-5 flex items-center justify-between bg-gradient-to-r from-norani-blue-bg to-white">
        <div>
          <h3 className="font-semibold text-norani-blue">Ready to add a sensor?</h3>
          <p className="text-sm text-gray-600 mt-1">
            Provision a new device in 30 seconds and print its sticker.
          </p>
        </div>
        <Link to="/devices/new" className="btn-primary">
          <Plus className="w-4 h-4 mr-1" /> Add device
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: "blue" | "green" | "red";
}) {
  const colors = {
    blue: "bg-blue-50 text-norani-blue",
    green: "bg-green-50 text-green-700",
    red: "bg-red-50 text-red-700",
  };
  return (
    <div className="card p-5">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-md ${colors[color]}`}>{icon}</div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}
