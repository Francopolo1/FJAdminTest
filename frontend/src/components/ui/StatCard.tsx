export type StatCardColor = "blue" | "green" | "amber" | "red" | "purple";

const COLOR_MAP: Record<StatCardColor, { bg: string; fg: string }> = {
  blue: { bg: "var(--blue-50)", fg: "var(--blue-600)" },
  green: { bg: "var(--green-50)", fg: "var(--green-600)" },
  amber: { bg: "var(--amber-50)", fg: "#92400E" },
  red: { bg: "var(--red-50)", fg: "var(--red-600)" },
  purple: { bg: "#F5F3FF", fg: "#6D28D9" },
};

export function StatCard({ label, value, color }: { label: string; value: number | string; color: StatCardColor }) {
  const { bg, fg } = COLOR_MAP[color];

  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bg, color: fg }}>
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /></svg>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
