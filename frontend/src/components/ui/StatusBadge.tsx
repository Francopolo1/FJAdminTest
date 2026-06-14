const STATUS_BADGE: Record<string, string> = {
  Draft: "badge-gray",
  InProgress: "badge-blue",
  Approved: "badge-green",
  Rejected: "badge-red",
  Cancelled: "badge-gray",
  OnHold: "badge-amber",
};

const STATUS_LABEL: Record<string, string> = {
  Draft: "Draft",
  InProgress: "In Progress",
  Approved: "Approved",
  Rejected: "Rejected",
  Cancelled: "Cancelled",
  OnHold: "On Hold",
};

export function StatusBadge({ status }: { status: string }) {
  const className = STATUS_BADGE[status] ?? "badge-gray";
  const label = STATUS_LABEL[status] ?? status;
  return <span className={`badge ${className}`}>{label}</span>;
}
