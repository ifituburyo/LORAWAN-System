import { useEffect, useState } from "react";
import { format } from "date-fns";
import { Receipt } from "lucide-react";
import * as billingApi from "../api/billing";
import type { CurrentBilling } from "../api/types";
import { getErrorMessage } from "../api/client";

export default function Billing() {
  const [current, setCurrent] = useState<CurrentBilling | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    billingApi
      .getCurrentBilling()
      .then(setCurrent)
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center text-gray-500 py-12">Loading…</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-norani-blue">Billing</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
          {error}
        </div>
      )}

      {current && (
        <>
          <div className="card p-6">
            <div className="flex items-baseline justify-between flex-wrap gap-3">
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                Current period
              </h2>
              <span className="text-sm text-gray-500">
                {format(new Date(current.period_start), "MMM d")} –{" "}
                {format(new Date(current.period_end), "MMM d, yyyy")}
              </span>
            </div>

            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-4xl font-bold text-gray-900">
                {current.amount_rwf.toLocaleString()}
              </span>
              <span className="text-lg text-gray-600">RWF</span>
              <span className="text-sm text-gray-500">≈ ${current.amount_usd.toFixed(2)} USD</span>
            </div>

            <div className="mt-5 pt-5 border-t border-gray-200 grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Active devices</div>
                <div className="text-lg font-semibold mt-0.5">{current.device_count}</div>
              </div>
              <div>
                <div className="text-gray-500">Price per device</div>
                <div className="text-lg font-semibold mt-0.5">
                  {current.price_per_device_rwf.toLocaleString()} RWF / month
                </div>
              </div>
            </div>
          </div>

          <div className="card p-5 bg-norani-blue-bg/40">
            <div className="flex items-start gap-3">
              <Receipt className="w-5 h-5 text-norani-blue mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-gray-900">How billing works</p>
                <p className="text-gray-600 mt-1">
                  You're billed monthly for active devices. Invoices are generated on the 1st of
                  each month and sent to your account contact email. Payment terms are 30 days,
                  via bank transfer or mobile money.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
