import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import * as devicesApi from "../api/devices";
import type { Device, DeviceList as DeviceListType } from "../api/types";
import StatusBadge from "../components/StatusBadge";
import { getErrorMessage } from "../api/client";

export default function DeviceList() {
  const [data, setData] = useState<DeviceListType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    const timer = setTimeout(() => {
      load();
    }, 300); // debounce search
    return () => clearTimeout(timer);
  }, [search, statusFilter]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await devicesApi.listDevices({
        page_size: 100,
        search: search || undefined,
        status: statusFilter || undefined,
      });
      setData(res);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-norani-blue">My Devices</h1>
          {data && (
            <p className="text-sm text-gray-500 mt-0.5">
              {data.total} total {data.total === 1 ? "device" : "devices"}
            </p>
          )}
        </div>
        <Link to="/devices/new" className="btn-primary">
          <Plus className="w-4 h-4 mr-1" /> Add device
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              className="input pl-9"
              placeholder="Search by name or DevEUI..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input sm:w-40"
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="offline">Offline</option>
            <option value="disabled">Disabled</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {error && (
          <div className="bg-red-50 text-red-800 px-4 py-2 text-sm border-b border-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading…</div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState search={search || statusFilter ? true : false} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <Th>Name / EUI</Th>
                  <Th>Type</Th>
                  <Th>Location</Th>
                  <Th>Last seen</Th>
                  <Th>Status</Th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((d) => (
                  <DeviceRow key={d.id} device={d} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="text-left px-4 py-2.5 font-semibold text-xs text-gray-600 uppercase tracking-wide">
      {children}
    </th>
  );
}

function DeviceRow({ device }: { device: Device }) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3">
        <Link
          to={`/devices/${device.dev_eui}`}
          className="font-medium text-gray-900 hover:text-norani-blue-light block"
        >
          {device.name}
        </Link>
        <div className="font-mono text-xs text-gray-500 mt-0.5">{device.dev_eui}</div>
      </td>
      <td className="px-4 py-3 text-gray-700">
        {device.device_type.manufacturer} {device.device_type.model}
      </td>
      <td className="px-4 py-3 text-gray-700">{device.location_name || "—"}</td>
      <td className="px-4 py-3 text-gray-600">
        {device.last_seen_at
          ? formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })
          : "Never"}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={device.status} />
      </td>
    </tr>
  );
}

function EmptyState({ search }: { search: boolean }) {
  return (
    <div className="p-12 text-center">
      {search ? (
        <p className="text-gray-500">No devices match your filters.</p>
      ) : (
        <>
          <p className="text-gray-600 mb-3">You don't have any devices yet.</p>
          <Link to="/devices/new" className="btn-primary">
            <Plus className="w-4 h-4 mr-1" /> Add your first device
          </Link>
        </>
      )}
    </div>
  );
}
