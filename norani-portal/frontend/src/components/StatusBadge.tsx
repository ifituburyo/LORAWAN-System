interface StatusBadgeProps {
  status: string;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  active: { bg: "bg-green-50", text: "text-green-700", dot: "bg-green-500", label: "Online" },
  pending: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500", label: "Pending" },
  offline: { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500", label: "Offline" },
  disabled: { bg: "bg-gray-100", text: "text-gray-600", dot: "bg-gray-400", label: "Disabled" },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`}></span>
      {s.label}
    </span>
  );
}
