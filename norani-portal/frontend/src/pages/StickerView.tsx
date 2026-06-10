import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams, Link } from "react-router-dom";
import { Download, Printer, CheckCircle2, AlertCircle } from "lucide-react";
import * as devicesApi from "../api/devices";
import type { Device } from "../api/types";
import { getErrorMessage } from "../api/client";

export default function StickerView() {
  const { devEui } = useParams<{ devEui: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as { appKey?: string; justCreated?: boolean } | null;
  const appKey = state?.appKey;
  const justCreated = state?.justCreated;

  const [device, setDevice] = useState<Device | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!devEui) return;
    devicesApi
      .getDevice(devEui)
      .then(setDevice)
      .catch((e) => setError(getErrorMessage(e)));

    // Fetch the sticker PDF as a blob for inline display
    const token = localStorage.getItem("norani_token");
    const url = `/api/v1${devicesApi.getStickerUrl(devEui, appKey)}`;
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load sticker (HTTP ${r.status})`);
        return r.blob();
      })
      .then((blob) => setPdfUrl(URL.createObjectURL(blob)))
      .catch((e) => setError(e.message));

    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [devEui, appKey]);

  const handlePrint = () => {
    if (!pdfUrl) return;
    const printWindow = window.open(pdfUrl, "_blank");
    if (printWindow) {
      printWindow.addEventListener("load", () => printWindow.print());
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {justCreated && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-green-900">Device created successfully!</h3>
            <p className="text-sm text-green-800 mt-1">
              Print this sticker and apply it to the sensor enclosure before installation. The
              QR code can be scanned by provisioning tools to auto-configure the device.
            </p>
          </div>
        </div>
      )}

      {!justCreated && (
        <div className="bg-amber-50 border border-amber-200 rounded-md p-3 flex items-start gap-2 text-sm">
          <AlertCircle className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
          <div className="text-amber-900">
            Reprinting an existing device's sticker is logged for audit purposes.
          </div>
        </div>
      )}

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-norani-blue">Device Sticker</h1>
            {device && (
              <p className="text-sm text-gray-600 mt-0.5">
                {device.name} · <span className="font-mono">{device.dev_eui}</span>
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handlePrint}
              disabled={!pdfUrl}
              className="btn-secondary"
              title="Print"
            >
              <Printer className="w-4 h-4 mr-1" /> Print
            </button>
            {pdfUrl && (
              <a
                href={pdfUrl}
                download={`sticker-${devEui}.pdf`}
                className="btn-primary"
              >
                <Download className="w-4 h-4 mr-1" /> Download PDF
              </a>
            )}
          </div>
        </div>

        {error ? (
          <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
            {error}
          </div>
        ) : pdfUrl ? (
          <div className="bg-gray-100 rounded-md p-2 flex justify-center">
            <iframe
              src={pdfUrl}
              title="Device sticker"
              className="w-full h-[600px] border border-gray-300 bg-white"
            />
          </div>
        ) : (
          <div className="text-center text-gray-500 py-12">Loading sticker…</div>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <Link to="/devices" className="btn-secondary">
          Back to devices
        </Link>
        <button
          onClick={() => navigate(`/devices/${devEui}`)}
          className="btn-primary"
        >
          View device details →
        </button>
      </div>
    </div>
  );
}
