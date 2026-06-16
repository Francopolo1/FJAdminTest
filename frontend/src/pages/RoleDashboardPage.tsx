import { useEffect, useState } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAuth } from "../contexts/AuthContext";
import {
  fetchInstanceCount,
  fetchInstanceDistributions,
  fetchOverdueTaskCount,
  fetchRecentInstances,
  fetchTaskCount,
  fetchTasks,
} from "../lib/workflowsApi";
import { fetchComplianceSummary } from "../lib/complianceApi";
import { fetchFinancialsSummary } from "../lib/financialsApi";
import { fetchChecklistRuns } from "../lib/checklistsApi";
import type {
  ChecklistRunListItem,
  ComplianceSummary,
  FinancialsSummary,
  InstanceDistributions,
  UserRole,
  WorkflowInstance,
  WorkflowTask,
} from "../types";

const STATUS_COLORS: Record<string, string> = {
  Approved: "#10B981",
  InProgress: "#2563EB",
  OnHold: "#F59E0B",
  Rejected: "#E11D48",
  Cancelled: "#ADB5BD",
  Pending: "#6366F1",
};

const PRIORITY_LABELS: Record<number, string> = { 1: "Low", 2: "Normal", 3: "High", 4: "Urgent" };
const PRIORITY_COLORS: Record<string, string> = {
  "1": "#ADB5BD",
  "2": "#2563EB",
  "3": "#F59E0B",
  "4": "#E11D48",
};

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const currencyFormatter = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

interface Stats {
  total: number;
  inProgress: number;
  approved: number;
  tasks: number;
  overdue: number;
}

// Which extra panels each role's dashboard shows, beyond the core stat grid.
const PANELS: Record<UserRole, { recentInstances?: boolean; myTasks?: boolean; checklists?: boolean; compliance?: boolean; financials?: boolean; distributions?: boolean }> = {
  admin:             { recentInstances: true, compliance: true, financials: true, distributions: true },
  director_manager:  { recentInstances: true, compliance: true, financials: true, distributions: true },
  supervisor:        { recentInstances: true, myTasks: true, distributions: true },
  inspector:         { myTasks: true, checklists: true, distributions: true },
  it_staff:          { recentInstances: true, distributions: true },
  support_staff:     { myTasks: true, checklists: true, distributions: true },
  readonly:          { recentInstances: true, compliance: true, financials: true, distributions: true },
};

function DistributionBars<T extends { count: number }>({
  items,
  getLabel,
  colorMap,
  getColorKey,
}: {
  items: T[];
  getLabel: (item: T) => string;
  colorMap?: Record<string, string>;
  getColorKey?: (item: T) => string;
}) {
  if (items.length === 0) {
    return <div className="empty-state"><p>No data yet.</p></div>;
  }
  const max = Math.max(...items.map((item) => item.count), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: ".5rem" }}>
      {items.map((item, index) => {
        const color = colorMap && getColorKey ? (colorMap[getColorKey(item)] ?? "#2563eb") : "#2563eb";
        return (
          <div key={index}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: ".875rem", marginBottom: ".15rem" }}>
              <span>{getLabel(item)}</span>
              <span>{item.count}</span>
            </div>
            <div style={{ background: "var(--color-border, #e5e7eb)", borderRadius: "4px", height: "8px" }}>
              <div
                style={{
                  width: `${(item.count / max) * 100}%`,
                  background: color,
                  borderRadius: "4px",
                  height: "8px",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RoleDashboardPage() {
  const { user } = useAuth();
  const role: UserRole = user?.role ?? "readonly";
  const panels = PANELS[role] ?? PANELS.readonly;

  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<WorkflowInstance[]>([]);
  const [myTasks, setMyTasks] = useState<WorkflowTask[]>([]);
  const [checklistRuns, setChecklistRuns] = useState<ChecklistRunListItem[]>([]);
  const [compliance, setCompliance] = useState<ComplianceSummary | null>(null);
  const [financials, setFinancials] = useState<FinancialsSummary | null>(null);
  const [distributions, setDistributions] = useState<InstanceDistributions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [total, inProgress, approved, tasks, overdue] = await Promise.all([
          fetchInstanceCount(),
          fetchInstanceCount("InProgress"),
          fetchInstanceCount("Approved"),
          fetchTaskCount(),
          fetchOverdueTaskCount(),
        ]);

        const [recentInstances, taskPage, runsPage, complianceSummary, financialsSummary, distributionData] = await Promise.all([
          panels.recentInstances ? fetchRecentInstances(5) : Promise.resolve([]),
          panels.myTasks ? fetchTasks({ pageSize: 5, ordering: "due_date" }).catch((e: unknown) => { throw new Error(`tasks: ${e instanceof Error ? e.message : e}`); }) : Promise.resolve(null),
          panels.checklists ? fetchChecklistRuns({ pageSize: 5 }).catch((e: unknown) => { throw new Error(`checklists: ${e instanceof Error ? e.message : e}`); }) : Promise.resolve(null),
          panels.compliance ? fetchComplianceSummary().catch((e: unknown) => { throw new Error(`compliance: ${e instanceof Error ? e.message : e}`); }) : Promise.resolve(null),
          panels.financials ? fetchFinancialsSummary().catch((e: unknown) => { throw new Error(`financials: ${e instanceof Error ? e.message : e}`); }) : Promise.resolve(null),
          panels.distributions ? fetchInstanceDistributions().catch((e: unknown) => { throw new Error(`distributions: ${e instanceof Error ? e.message : e}`); }) : Promise.resolve(null),
        ]);

        if (cancelled) return;
        setStats({ total, inProgress, approved, tasks, overdue });
        setRecent(recentInstances);
        setMyTasks(taskPage?.results ?? []);
        setChecklistRuns(runsPage?.results ?? []);
        setCompliance(complianceSummary);
        setFinancials(financialsSummary);
        setDistributions(distributionData);
      } catch (err: unknown) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(`Unable to load dashboard data: ${msg}`);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [panels.recentInstances, panels.myTasks, panels.checklists, panels.compliance, panels.financials, panels.distributions]);

  const statCards = role === "supervisor" || role === "inspector" || role === "support_staff"
    ? [
        { label: "My Open Tasks", value: stats?.tasks ?? 0, color: "amber" as const },
        { label: "Overdue Tasks", value: stats?.overdue ?? 0, color: "red" as const },
        { label: "Requests In Progress", value: stats?.inProgress ?? 0, color: "blue" as const },
      ]
    : [
        { label: "Total Requests", value: stats?.total ?? 0, color: "blue" as const },
        { label: "In Progress", value: stats?.inProgress ?? 0, color: "blue" as const },
        { label: "Approved", value: stats?.approved ?? 0, color: "green" as const },
        { label: "Open Tasks", value: stats?.tasks ?? 0, color: "amber" as const },
        { label: "Overdue Tasks", value: stats?.overdue ?? 0, color: "red" as const },
      ];

  return (
    <AppLayout title="Dashboard">
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading ? (
        <div className="empty-state">Loading dashboard…</div>
      ) : (
        <>
          <div className="stat-grid">
            {statCards.map((card) => (
              <StatCard key={card.label} label={card.label} value={card.value} color={card.color} />
            ))}
          </div>

          {panels.distributions && distributions && (
            <>
              <div className="charts-grid" style={{ marginBottom: "1.25rem" }}>
                <div className="card">
                  <div className="card-header"><span className="card-title">Request Status</span></div>
                  <div className="card-body">
                    <DistributionBars
                      items={distributions.by_status ?? []}
                      getLabel={(item) => item.status}
                      colorMap={STATUS_COLORS}
                      getColorKey={(item) => item.status}
                    />
                  </div>
                </div>
                <div className="card">
                  <div className="card-header"><span className="card-title">Requests by Priority</span></div>
                  <div className="card-body">
                    <DistributionBars
                      items={distributions.by_priority ?? []}
                      getLabel={(item) => PRIORITY_LABELS[item.priority] ?? `P${item.priority}`}
                      colorMap={PRIORITY_COLORS}
                      getColorKey={(item) => String(item.priority)}
                    />
                  </div>
                </div>
                {(distributions.by_category ?? []).length > 0 && (
                  <div className="card">
                    <div className="card-header"><span className="card-title">Requests by Category</span></div>
                    <div className="card-body">
                      <DistributionBars
                        items={distributions.by_category ?? []}
                        getLabel={(item) => item.category}
                      />
                    </div>
                  </div>
                )}
              </div>
              <div className="detail-grid" style={{ marginBottom: "1.25rem" }}>
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">Requests by Program</span>
                  </div>
                  <div className="card-body">
                    <DistributionBars
                      items={distributions.by_program}
                      getLabel={(item) => item.program_title || item.program_code || "Unassigned"}
                    />
                  </div>
                </div>
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">Requests by Activity</span>
                  </div>
                  <div className="card-body">
                    <DistributionBars
                      items={distributions.by_activity}
                      getLabel={(item) => item.activity || "Unassigned"}
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {panels.compliance && compliance && (
            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <div className="card-header">
                <span className="card-title">Compliance Summary</span>
              </div>
              <div className="card-body">
                <div className="detail-grid">
                  <StatCard label="Total Violations" value={compliance.total_violations} color="red" />
                  <StatCard label="Violations (30d)" value={compliance.violations_last_30_days} color="amber" />
                  <StatCard label="Active Rules" value={compliance.active_rules} color="blue" />
                  <StatCard label="Active Fine Schedules" value={compliance.active_fine_schedules} color="purple" />
                </div>
                {compliance.top_violated_rules.length > 0 && (
                  <div style={{ marginTop: "1rem" }}>
                    <strong>Top Violated Rules</strong>
                    <ul style={{ margin: ".5rem 0 0", paddingLeft: "1.25rem" }}>
                      {compliance.top_violated_rules.map((rule) => (
                        <li key={rule.compliance_rule__code}>
                          {rule.compliance_rule__code} — {rule.compliance_rule__name} ({rule.count})
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {panels.financials && financials && (
            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <div className="card-header">
                <span className="card-title">Financials Summary</span>
              </div>
              <div className="card-body">
                <div className="detail-grid">
                  <StatCard label="Total Amount" value={currencyFormatter.format(Number(financials.total_amount))} color="green" />
                  <StatCard label="Pending" value={financials.pending_count} color="amber" />
                  <StatCard label="Approved" value={financials.approved_count} color="blue" />
                  <StatCard label="Posted" value={financials.posted_count} color="green" />
                </div>
              </div>
            </div>
          )}

          {panels.myTasks && (
            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <div className="card-header">
                <span className="card-title">My Tasks</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Step</th>
                      <th>Status</th>
                      <th>Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myTasks.length === 0 ? (
                      <tr>
                        <td colSpan={3}>
                          <div className="empty-state"><p>No tasks assigned.</p></div>
                        </td>
                      </tr>
                    ) : (
                      myTasks.map((task) => (
                        <tr key={task.task_id}>
                          <td>{task.step_name}</td>
                          <td><StatusBadge status={task.status} /></td>
                          <td>{task.due_date ? dateFormatter.format(new Date(task.due_date)) : "—"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {panels.checklists && (
            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <div className="card-header">
                <span className="card-title">Checklist Runs</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Checklist</th>
                      <th>Status</th>
                      <th>Completion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {checklistRuns.length === 0 ? (
                      <tr>
                        <td colSpan={4}>
                          <div className="empty-state"><p>No checklist runs.</p></div>
                        </td>
                      </tr>
                    ) : (
                      checklistRuns.map((run) => (
                        <tr key={run.run_id}>
                          <td>{run.reference_no}</td>
                          <td>{run.template_title}</td>
                          <td><StatusBadge status={run.status} /></td>
                          <td>{Math.round(run.completion_pct)}%</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {panels.recentInstances && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Recent Requests</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Workflow</th>
                      <th>Status</th>
                      <th>Initiated By</th>
                      <th>Started</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.length === 0 ? (
                      <tr>
                        <td colSpan={5}>
                          <div className="empty-state">
                            <p>No requests yet.</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      recent.map((instance) => (
                        <tr key={instance.instance_id}>
                          <td>{instance.reference_no}</td>
                          <td>{instance.workflow_name}</td>
                          <td><StatusBadge status={instance.status} /></td>
                          <td>{instance.initiated_by_name}</td>
                          <td>{dateFormatter.format(new Date(instance.started_at))}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </AppLayout>
  );
}
