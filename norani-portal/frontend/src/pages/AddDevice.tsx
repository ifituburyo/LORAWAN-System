import { useEffect, useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChevronLeft, KeyRound } from "lucide-react";
import * as devicesApi from "../api/devices";
import type { DeviceType } from "../api/types";
import { getErrorMessage } from "../api/client";

export default function AddDevice() {
  const navigate = useNavigate();
  const [deviceTypes, setDeviceTypes] = useState<DeviceType[]>([]);
  const [form, setForm] = useState({
    name: "",
    device_type_id: "",
    dev_eui: "",
    join_eui: "0000000000000000",
    location_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    devicesApi
      .listDeviceTypes()
      .then((types) => setDeviceTypes(types))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoadingTypes(false));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await devicesApi.createDevice({
        name: form.name.trim(),
        device_type_id: form.device_type_id,
        dev_eui: form.dev_eui,
        join_eui: form.join_eui || "0000000000000000",
        location_name: form.location_name.trim() || undefined,
      });

      // Navigate to the sticker view, passing the plaintext AppKey via state
      navigate(`/devices/${res.dev_eui}/sticker`, {
        state: { appKey: res.app_key, justCreated: true },
      });
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Breadcrumb */}
      <div className="mb-4 text-sm">
        <Link
          to="/devices"
          className="text-gray-500 hover:text-norani-blue inline-flex items-center"
        >
          <ChevronLeft className="w-4 h-4" /> Back to devices
        </Link>
      </div>

      <div className="card p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-norani-blue mb-2">Add a new device</h1>
        <p className="text-gray-600 mb-6">
          We'll generate the security key and prepare a printable sticker.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Device name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Office Tank #1"
              required
              maxLength={255}
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Device type <span className="text-red-500">*</span>
            </label>
            <select
              className="input"
              value={form.device_type_id}
              onChange={(e) => setForm({ ...form, device_type_id: e.target.value })}
              required
              disabled={loadingTypes}
            >
              <option value="">
                {loadingTypes ? "Loading device types..." : "Select a device type..."}
              </option>
              {deviceTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.manufacturer ? `${t.manufacturer} ${t.model} — ` : ""}
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* DevEUI */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Device EUI (from sticker) <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className="input font-mono"
              value={form.dev_eui}
              onChange={(e) => setForm({ ...form, dev_eui: e.target.value })}
              placeholder="a8404117c1862aff"
              required
              minLength={16}
              maxLength={23}
            />
            <p className="mt-1 text-xs text-gray-500">
              16-character hex ID printed on the sensor's label. Colons and spaces are ignored.
            </p>
          </div>

          {/* Join EUI (advanced, collapsed by default) */}
          <details className="group">
            <summary className="cursor-pointer text-sm text-norani-blue-light hover:underline">
              Advanced (JoinEUI)
            </summary>
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">JoinEUI</label>
              <input
                type="text"
                className="input font-mono"
                value={form.join_eui}
                onChange={(e) => setForm({ ...form, join_eui: e.target.value })}
                placeholder="0000000000000000"
              />
              <p className="mt-1 text-xs text-gray-500">
                Leave as all zeros for ChirpStack's internal join server (default).
              </p>
            </div>
          </details>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
            <input
              type="text"
              className="input"
              value={form.location_name}
              onChange={(e) => setForm({ ...form, location_name: e.target.value })}
              placeholder="e.g. Kacyiru Office, Building A"
              maxLength={500}
            />
          </div>

          {/* AppKey explainer */}
          <div className="bg-norani-blue-bg border border-blue-200 rounded-md p-3 flex items-start gap-3">
            <KeyRound className="w-4 h-4 text-norani-blue mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <div className="font-medium text-norani-blue">App Key</div>
              <p className="text-gray-600 mt-0.5">
                A unique 128-bit security key will be generated automatically when you submit.
                We never reuse keys across devices.
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex justify-between pt-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Creating..." : "Create & Print"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
