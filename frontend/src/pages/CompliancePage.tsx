import { useEffect, useState } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { Pagination } from "../components/ui/Pagination";
import { fetchComplianceSummary, fetchViolations } from "../lib/complianceApi";
import type { ComplianceSummary, ComplianceViolation } from "../types";

const PAGE_SIZE = 20;

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const SEVERITY_BADGE: Record<string, string> = {
  Low: "badge-gray",
  Medium: "badge-amber",
  High: "badge-red",
  Critical: "badge-red",
};

export function CompliancePage() {
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [violations, setViolations] = useState<ComplianceViolation[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    Promise.all([fetchComplianceSummary(), fetchViolations({ page, pageSize: PAGE_SIZE })])
      .then(([summaryData, violationsData]) => {
        if (cancelled) return;
        setSummary(summaryData);
        setViolations(violationsData.results);
        setCount(violationsData.count);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load compliance data.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page]);

  return (
    <AppLayout title="Compliance">
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading ? (
        <div className="empty-state">Loading…</div>
      ) : (
        <>
          <div className="stat-grid">
            <StatCard label="Active Rules" value={summary?.active_rules ?? 0} />
            <StatCard label="Total Violations" value={summary?.total_violations ?? 0} color="red" />
            <StatCard label="Violations (30 days)" value={summary?.violations_last_30_days ?? 0} color="amber" />
            <StatCard label="Active Fine Schedules" value={summary?.active_fine_schedules ?? 0} color="blue" />
          </div>

          <div className="charts-grid">
            <div className="card">
              <div className="card-header">
                <span className="card-title">Top Violated Rules</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Rule</th>
                      <th>Code</th>
                      <th>Violations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(summary?.top_violated_rules ?? []).length === 0 ? (
                      <tr><td colSpan={3}><div className="empty-state"><p>No violations recorded.</p></div></td></tr>
                    ) : (
                      summary?.top_violated_rules.map((rule) => (
                        <tr key={rule.compliance_rule__code}>
                          <td>{rule.compliance_rule__name}</td>
                          <td>{rule.compliance_rule__code}</td>
                          <td>{rule.count}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Severity Breakdown</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Severity</th>
                      <th>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(summary?.severity_breakdown ?? []).length === 0 ? (
                      <tr><td colSpan={2}><div className="empty-state"><p>No data.</p></div></td></tr>
                    ) : (
                      summary?.severity_breakdown.map((row) => (
                        <tr key={row.violation_severity_level__code}>
                          <td>
                            <span className={`badge ${SEVERITY_BADGE[row.violation_severity_level__name] ?? "badge-gray"}`}>
                              {row.violation_severity_level__name}
                            </span>
                          </td>
                          <td>{row.count}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Violations</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Rule</th>
                    <th>Severity</th>
                    <th>Item</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {violations.length === 0 ? (
                    <tr><td colSpan={5}><div className="empty-state"><p>No violations found.</p></div></td></tr>
                  ) : (
                    violations.map((v) => (
                      <tr key={v.compliance_violation_id}>
                        <td>{dateFormatter.format(new Date(v.violation_date))}</td>
                        <td>{v.rule_name} <span style={{ color: "var(--ink-400)" }}>({v.rule_code})</span></td>
                        <td><span className={`badge ${SEVERITY_BADGE[v.severity_name] ?? "badge-gray"}`}>{v.severity_name}</span></td>
                        <td>{v.item_text ?? "—"}</td>
                        <td>{v.violation_description ?? "—"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
          </div>
        </>
      )}
    </AppLayout>
  );
}

function StatCard({ label, value, color = "blue" }: { label: string; value: number; color?: "blue" | "green" | "amber" | "red" }) {
  const colorMap: Record<string, { bg: string; fg: string }> = {
    blue: { bg: "var(--blue-50)", fg: "var(--blue-600)" },
    green: { bg: "var(--green-50)", fg: "var(--green-600)" },
    amber: { bg: "var(--amber-50)", fg: "#92400E" },
    red: { bg: "var(--red-50)", fg: "var(--red-600)" },
  };
  const { bg, fg } = colorMap[color];

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
