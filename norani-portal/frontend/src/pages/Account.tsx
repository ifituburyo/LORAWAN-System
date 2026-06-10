import { useEffect, useState } from "react";
import { api, getErrorMessage } from "../api/client";
import type { CustomerAccount } from "../api/types";
import { useAuth } from "../hooks/useAuth";
import { format } from "date-fns";

export default function Account() {
  const { user } = useAuth();
  const [account, setAccount] = useState<CustomerAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CustomerAccount>("/account")
      .then((r) => setAccount(r.data))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center text-gray-500 py-12">Loading…</div>;

  return (
    <div className="space-y-4 max-w-3xl">
      <h1 className="text-2xl font-bold text-norani-blue">Account</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
          {error}
        </div>
      )}

      {account && (
        <>
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">
              Organisation
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <Field label="Name">{account.name}</Field>
              <Field label="Plan">
                <span className="capitalize">{account.plan_tier}</span>
              </Field>
              <Field label="Contact email">{account.contact_email}</Field>
              <Field label="Phone">{account.phone || "—"}</Field>
              <Field label="Address" wide>
                {account.address || "—"}
              </Field>
              <Field label="Account created">
                {format(new Date(account.created_at), "PPP")}
              </Field>
            </dl>
            <p className="mt-4 text-xs text-gray-500">
              To update organisation details, contact your Norani representative.
            </p>
          </div>

          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">
              Your profile
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <Field label="Name">{user?.full_name || "—"}</Field>
              <Field label="Email">{user?.email}</Field>
              <Field label="Role">
                <span className="capitalize">{user?.role}</span>
              </Field>
            </dl>
          </div>
        </>
      )}
    </div>
  );
}

function Field({
  label,
  children,
  wide,
}: {
  label: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "sm:col-span-2" : ""}>
      <dt className="text-gray-500">{label}</dt>
      <dd className="text-gray-900 mt-0.5">{children}</dd>
    </div>
  );
}
