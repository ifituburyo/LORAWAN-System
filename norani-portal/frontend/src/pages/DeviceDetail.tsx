import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ChevronLeft,
  MapPin,
  Calendar,
  Printer,
  Trash2,
  Download,
  FileText,
  FileSpreadsheet,
  Braces,
} from "lucide-react";
import { format, formatDistanceToNow, subHours } from "date-fns";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import * as devicesApi from "../api/devices";
import type { MeasurementParams } from "../api/devices";
import type { Device, DeviceMeasurement } from "../api/types";
import StatusBadge from "../components/StatusBadge";
import { getErrorMessage } from "../api/client";

// ─── Presets ────────────────────────────────────────────────────────────────

const PRESETS = [
  { label: "6 h",   hours: 6 },
  { label: "24 h",  hours: 24 },
  { label: "7 d",   hours: 168 },
  { label: "30 d",  hours: 720 },
  { label: "Custom", hours: 0 },
] as const;

function toLocalDatetimeValue(d: Date): string {
  // Returns value compatible with <input type="datetime-local">
  return format(d, "yyyy-MM-dd'T'HH:mm");
}

function toISO(local: string): string {
  // Convert datetime-local string to ISO for the API
  return new Date(local).toISOString();
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function DeviceDetail() {
  const { devEui } = useParams<{ devEui: string }>();
  const navigate = useNavigate();

  const [device, setDevice] = useState<Device | null>(null);
  const [latest, setLatest] = useState<Record<string, number> | null>(null);
  const [latestTime, setLatestTime] = useState<string | null>(null);
  const [measurements, setMeasurements] = useState<DeviceMeasurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Date range state
  const [preset, setPreset] = useState<number>(24);           // hours; 0 = custom
  const [fromVal, setFromVal] = useState(() => toLocalDatetimeValue(subHours(new Date(), 24)));
  const [toVal, setToVal]     = useState(() => toLocalDatetimeValue(new Date()));

  // Build params for API calls
  const measureParams: MeasurementParams = preset > 0
    ? { hours: preset }
    : { from_time: toISO(fromVal), to_time: toISO(toVal) };

  useEffect(() => {
    if (!devEui) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [devEui, preset, fromVal, toVal]);

  async function load() {
    if (!devEui) return;
    setLoading(true);
    setError(null);
    try {
      const [dev, lat, meas] = await Promise.all([
        devicesApi.getDevice(devEui),
        devicesApi.getDeviceLatest(devEui).catch(() => null),
        devicesApi.getDeviceMeasurements(devEui, measureParams).catch(() => ({
          measurements: [],
          count: 0,
          from: "",
          to: "",
        })),
      ]);
      setDevice(dev);
      if (lat?.latest) {
        setLatest(lat.latest.fields);
        setLatestTime(lat.latest.timestamp);
      }
      setMeasurements(meas.measurements);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  function selectPreset(hours: number) {
    setPreset(hours);
    if (hours > 0) {
      setFromVal(toLocalDatetimeValue(subHours(new Date(), hours)));
      setToVal(toLocalDatetimeValue(new Date()));
    }
  }

  async function handleExport(fmt: "csv" | "json" | "xlsx") {
    if (!devEui) return;
    setExporting(fmt);
    try {
      await devicesApi.exportDeviceData(devEui, fmt, measureParams);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setExporting(null);
    }
  }

  async function handleDelete() {
    if (!devEui) return;
    if (!confirm(`Delete device "${device?.name}"? This cannot be undone.`)) return;
    try {
      await devicesApi.deleteDevice(devEui);
      navigate("/devices");
    } catch (e) {
      setError(getErrorMessage(e));
    }
  }

  if (loading) return <div className="text-center text-gray-500 py-12">Loading…</div>;
  if (error || !device) {
    return (
      <div className="card p-6">
        <p className="text-red-600">{error || "Device not found"}</p>
        <Link to="/devices" className="btn-secondary mt-4 inline-flex">
          Back to devices
        </Link>
      </div>
    );
  }

  const fields = [...new Set(measurements.map((m) => m.field))];
  const chartData = groupMeasurementsByTime(measurements);

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <Link
        to="/devices"
        className="text-sm text-gray-500 hover:text-norani-blue inline-flex items-center"
      >
        <ChevronLeft className="w-4 h-4" /> Back to devices
      </Link>

      {/* Header card */}
      <div className="card p-6">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold text-norani-blue">{device.name}</h1>
            <div className="font-mono text-sm text-gray-500 mt-1">{device.dev_eui}</div>
            <div className="text-sm text-gray-600 mt-2">
              {device.device_type.manufacturer} {device.device_type.model}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusBadge status={device.status} />
            <div className="text-xs text-gray-500">
              {device.last_seen_at
                ? `Last seen ${formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })}`
                : "Never seen"}
            </div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <Info icon={<MapPin className="w-4 h-4" />} label="Location">
            {device.location_name || "—"}
          </Info>
          <Info icon={<Calendar className="w-4 h-4" />} label="Added">
            {format(new Date(device.created_at), "PPP")}
          </Info>
        </div>

        <div className="mt-5 flex gap-2">
          <Link to={`/devices/${device.dev_eui}/sticker`} className="btn-secondary">
            <Printer className="w-4 h-4 mr-1" /> Sticker
          </Link>
          <button onClick={handleDelete} className="btn-secondary text-red-600 hover:bg-red-50">
            <Trash2 className="w-4 h-4 mr-1" /> Delete
          </button>
        </div>
      </div>

      {/* Latest reading */}
      {latest && Object.keys(latest).length > 0 && (
        <div className="card p-5">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
              Latest reading
            </h2>
            {latestTime && (
              <span className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(latestTime), { addSuffix: true })}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(latest).map(([key, value]) => (
              <div key={key} className="bg-norani-blue-bg rounded-md p-3">
                <div className="text-xs text-gray-600 capitalize">{key.replace(/_/g, " ")}</div>
                <div className="text-xl font-semibold text-norani-blue mt-1">
                  {typeof value === "number" ? value.toFixed(2) : String(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical data + export */}
      <div className="card p-5">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide self-center">
            Historical data
          </h2>

          {/* Export buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500 mr-1">
              <Download className="w-3.5 h-3.5 inline mr-0.5" />
              Export:
            </span>
            <ExportButton
              label="CSV"
              icon={<FileText className="w-3.5 h-3.5" />}
              loading={exporting === "csv"}
              disabled={!!exporting || chartData.length === 0}
              onClick={() => handleExport("csv")}
            />
            <ExportButton
              label="Excel"
              icon={<FileSpreadsheet className="w-3.5 h-3.5" />}
              loading={exporting === "xlsx"}
              disabled={!!exporting || chartData.length === 0}
              onClick={() => handleExport("xlsx")}
            />
            <ExportButton
              label="JSON"
              icon={<Braces className="w-3.5 h-3.5" />}
              loading={exporting === "json"}
              disabled={!!exporting || chartData.length === 0}
              onClick={() => handleExport("json")}
            />
          </div>
        </div>

        {/* Time range controls */}
        <div className="flex flex-wrap items-end gap-3 mb-5 p-3 bg-gray-50 rounded-lg border border-gray-200">
          {/* Preset buttons */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Quick range</label>
            <div className="flex gap-1">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => selectPreset(p.hours)}
                  className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
                    preset === p.hours
                      ? "bg-norani-blue text-white border-norani-blue"
                      : "bg-white text-gray-600 border-gray-300 hover:border-norani-blue"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom date inputs — always visible but only active in custom mode */}
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">From</label>
              <input
                type="datetime-local"
                className="input text-sm py-1"
                value={fromVal}
                max={toVal}
                onChange={(e) => {
                  setFromVal(e.target.value);
                  setPreset(0);
                }}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">To</label>
              <input
                type="datetime-local"
                className="input text-sm py-1"
                value={toVal}
                min={fromVal}
                max={toLocalDatetimeValue(new Date())}
                onChange={(e) => {
                  setToVal(e.target.value);
                  setPreset(0);
                }}
              />
            </div>
            {preset === 0 && (
              <button
                onClick={load}
                className="btn-primary text-sm py-1"
              >
                Apply
              </button>
            )}
          </div>

          <div className="text-xs text-gray-400 self-end pb-1">
            {measurements.length} readings
          </div>
        </div>

        {/* Chart */}
        {chartData.length === 0 ? (
          <div className="text-center text-gray-500 py-12 bg-gray-50 rounded-md">
            No data in the selected period. New devices may take a few minutes to appear
            after their first uplink.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 11 }}
                tickFormatter={(t) =>
                  preset <= 24
                    ? format(new Date(t), "HH:mm")
                    : format(new Date(t), "MMM d HH:mm")
                }
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                labelFormatter={(t) => format(new Date(t), "PPpp")}
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
              <Legend />
              {fields.map((f, i) => (
                <Line
                  key={f}
                  type="monotone"
                  dataKey={f}
                  stroke={CHART_COLORS[i % CHART_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  name={f.replace(/_/g, " ")}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ExportButton({
  label,
  icon,
  loading,
  disabled,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  loading: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium border border-gray-300
                 rounded bg-white text-gray-700 hover:bg-gray-50 hover:border-norani-blue
                 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
    >
      {loading ? (
        <span className="animate-spin inline-block w-3 h-3 border border-gray-400 border-t-norani-blue rounded-full" />
      ) : (
        icon
      )}
      {label}
    </button>
  );
}

function Info({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
        {icon} {label}
      </div>
      <div className="text-gray-900">{children}</div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const CHART_COLORS = ["#1F4E79", "#F57C00", "#2E7D32", "#C62828", "#6A1B9A"];

function groupMeasurementsByTime(measurements: DeviceMeasurement[]): Array<Record<string, unknown>> {
  const map = new Map<string, Record<string, unknown>>();
  for (const m of measurements) {
    const t = m.timestamp;
    if (!map.has(t)) map.set(t, { time: t });
    map.get(t)![m.field] = m.value;
  }
  return Array.from(map.values()).sort(
    (a, b) => new Date(a.time as string).getTime() - new Date(b.time as string).getTime(),
  );
}
