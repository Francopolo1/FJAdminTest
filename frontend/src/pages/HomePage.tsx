import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { StatCard } from "../components/ui/StatCard";
import type { StatCardColor } from "../components/ui/StatCard";
import { useAuth } from "../contexts/AuthContext";
import { InspectorLandingPage } from "./InspectorLandingPage";
import {
  fetchInstanceCount,
  fetchOverdueTaskCount,
  fetchTaskCount,
} from "../lib/workflowsApi";
import { fetchComplianceSummary } from "../lib/complianceApi";
import { assignDirectReportProgram, fetchSupervisorLanding, unassignDirectReportProgram } from "../lib/coreApi";
import type { SupervisorDirectReport, SupervisorLanding, UserRole } from "../types";

interface Metrics {
  total: number;
  inProgress: number;
  approved: number;
  tasks: number;
  overdue: number;
  violations30d: number;
}

interface QuickStat {
  label: string;
  key: keyof Metrics;
  color: StatCardColor;
}

interface Shortcut {
  to: string;
  label: string;
  description: string;
}

const QUICK_STATS: Record<UserRole, QuickStat[]> = {
  admin: [
    { label: "Total Requests", key: "total", color: "blue" },
    { label: "In Progress", key: "inProgress", color: "blue" },
    { label: "Open Tasks", key: "tasks", color: "amber" },
    { label: "Overdue Tasks", key: "overdue", color: "red" },
  ],
  director_manager: [
    { label: "Total Requests", key: "total", color: "blue" },
    { label: "Approved", key: "approved", color: "green" },
    { label: "Overdue Tasks", key: "overdue", color: "red" },
    { label: "Violations (30d)", key: "violations30d", color: "amber" },
  ],
  supervisor: [
    { label: "My Open Tasks", key: "tasks", color: "amber" },
    { label: "Overdue Tasks", key: "overdue", color: "red" },
    { label: "Requests In Progress", key: "inProgress", color: "blue" },
  ],
  inspector: [],
  it_staff: [
    { label: "Total Requests", key: "total", color: "blue" },
    { label: "Open Tasks", key: "tasks", color: "amber" },
  ],
  support_staff: [
    { label: "My Open Tasks", key: "tasks", color: "amber" },
    { label: "Overdue Tasks", key: "overdue", color: "red" },
  ],
  readonly: [
    { label: "Total Requests", key: "total", color: "blue" },
    { label: "In Progress", key: "inProgress", color: "blue" },
    { label: "Approved", key: "approved", color: "green" },
  ],
};

const SHORTCUTS: Record<UserRole, Shortcut[]> = {
  admin: [
    { to: "/instances", label: "Requests", description: "View and manage all workflow requests." },
    { to: "/compliance", label: "Compliance", description: "Review violations and compliance rules." },
    { to: "/financials", label: "Financials", description: "Browse transactions and FOAPAL strings." },
    { to: "/facilities", label: "Facilities", description: "Search the facility directory." },
    { to: "/checklists", label: "Checklists", description: "View checklist runs and progress." },
    { to: "/admin/", label: "Admin Panel", description: "Manage users, roles, and configuration." },
  ],
  director_manager: [
    { to: "/instances", label: "Requests", description: "Oversee workflow requests across the org." },
    { to: "/compliance", label: "Compliance", description: "Review violations and compliance rules." },
    { to: "/financials", label: "Financials", description: "Browse transactions and FOAPAL strings." },
    { to: "/facilities", label: "Facilities", description: "Search the facility directory." },
  ],
  supervisor: [
    { to: "/tasks", label: "Tasks", description: "Review and act on assigned tasks." },
    { to: "/instances", label: "Requests", description: "View workflow requests needing decisions." },
    { to: "/checklists", label: "Checklists", description: "Track checklist completion." },
  ],
  inspector: [],
  it_staff: [
    { to: "/admin/", label: "Admin Panel", description: "Manage users, roles, and configuration." },
    { to: "/facilities", label: "Facilities", description: "Search the facility directory." },
    { to: "/checklists", label: "Checklists", description: "View checklist runs and progress." },
  ],
  support_staff: [
    { to: "/checklists", label: "Checklists", description: "Help track checklist completion." },
    { to: "/facilities", label: "Facilities", description: "Search the facility directory." },
    { to: "/tasks", label: "Tasks", description: "Review your assigned tasks." },
  ],
  readonly: [
    { to: "/instances", label: "Requests", description: "View workflow requests." },
    { to: "/compliance", label: "Compliance", description: "Review violations and compliance rules." },
    { to: "/financials", label: "Financials", description: "Browse transactions and FOAPAL strings." },
  ],
};

function DirectReportRow({
  report,
  availablePrograms,
  onAssign,
  onUnassign,
}: {
  report: SupervisorDirectReport;
  availablePrograms: SupervisorLanding["assigned_programs"];
  onAssign: (userId: number, programId: string) => Promise<void>;
  onUnassign: (userId: number, programId: string) => Promise<void>;
}) {
  const [isSaving, setIsSaving] = useState(false);

  const assignedIds = new Set(report.assigned_programs.map((p) => p.program_id));
  const addablePrograms = availablePrograms.filter((p) => !assignedIds.has(p.program_id));

  const handleAdd = async (programId: string) => {
    if (!programId) return;
    setIsSaving(true);
    try {
      await onAssign(report.user_id, programId);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemove = async (programId: string) => {
    setIsSaving(true);
    try {
      await onUnassign(report.user_id, programId);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <tr>
      <td>{report.full_name}</td>
      <td>{report.job_title || "—"}</td>
      <td>{report.department || "—"}</td>
      <td>
        <div style={{ display: "flex", flexWrap: "wrap", gap: ".375rem", alignItems: "center" }}>
          {report.assigned_programs.map((program) => (
            <span key={program.program_id} className="badge badge-blue">
              {program.code}
              <button
                type="button"
                onClick={() => void handleRemove(program.program_id)}
                disabled={isSaving}
                title={`Remove ${program.title}`}
                style={{
                  border: "none", background: "none", cursor: "pointer", padding: 0,
                  marginLeft: ".25rem", color: "inherit", font: "inherit", lineHeight: 1,
                }}
              >
                ×
              </button>
            </span>
          ))}
          {addablePrograms.length > 0 && (
            <select
              value=""
              disabled={isSaving}
              onChange={(e) => void handleAdd(e.target.value)}
              style={{ fontSize: ".75rem", padding: ".125rem .375rem" }}
            >
              <option value="">+ Assign program…</option>
              {addablePrograms.map((program) => (
                <option key={program.program_id} value={program.program_id}>
                  {program.code} — {program.title}
                </option>
              ))}
            </select>
          )}
        </div>
      </td>
    </tr>
  );
}

function RoleHome({ role, name }: { role: UserRole; name: string }) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [supervisorData, setSupervisorData] = useState<SupervisorLanding | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const quickStats = QUICK_STATS[role] ?? [];
  const shortcuts  = SHORTCUTS[role] ?? [];
  const needsViolations = quickStats.some((s) => s.key === "violations30d");
  const isSupervisor = role === "supervisor";

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [total, inProgress, approved, tasks, overdue, summary, supervisor] = await Promise.all([
          fetchInstanceCount(),
          fetchInstanceCount("InProgress"),
          fetchInstanceCount("Approved"),
          fetchTaskCount(),
          fetchOverdueTaskCount(),
          needsViolations ? fetchComplianceSummary() : Promise.resolve(null),
          isSupervisor ? fetchSupervisorLanding() : Promise.resolve(null),
        ]);

        if (cancelled) return;
        setMetrics({
          total, inProgress, approved, tasks, overdue,
          violations30d: summary?.violations_last_30_days ?? 0,
        });
        setSupervisorData(supervisor);
      } catch {
        if (!cancelled) setError("Unable to load summary data.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [needsViolations, isSupervisor]);

  const updateReportPrograms = (userId: number, programs: SupervisorLanding["assigned_programs"]) => {
    setSupervisorData((prev) =>
      prev
        ? {
            ...prev,
            direct_reports: prev.direct_reports.map((report) =>
              report.user_id === userId ? { ...report, assigned_programs: programs } : report
            ),
          }
        : prev
    );
  };

  const handleAssign = async (userId: number, programId: string) => {
    const programs = await assignDirectReportProgram(userId, programId);
    updateReportPrograms(userId, programs);
  };

  const handleUnassign = async (userId: number, programId: string) => {
    const programs = await unassignDirectReportProgram(userId, programId);
    updateReportPrograms(userId, programs);
  };

  return (
    <AppLayout title="Home">
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <div className="card-body">
          <h2 style={{ margin: 0, fontFamily: "'Sora', sans-serif" }}>Welcome back, {name}</h2>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {quickStats.length > 0 && (
        isLoading ? (
          <div className="empty-state">Loading summary…</div>
        ) : (
          <div className="stat-grid">
            {quickStats.map((stat) => (
              <StatCard key={stat.key} label={stat.label} value={metrics?.[stat.key] ?? 0} color={stat.color} />
            ))}
          </div>
        )
      )}

      {isSupervisor && !isLoading && (
        <div className="charts-grid" style={{ marginBottom: "1.25rem" }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Assigned Programs</span>
            </div>
            <div className="card-body">
              {supervisorData && supervisorData.assigned_programs.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
                  {supervisorData.assigned_programs.map((program) => (
                    <li key={program.program_id}>{program.code} — {program.title}</li>
                  ))}
                </ul>
              ) : (
                <div className="empty-state"><p>No programs assigned.</p></div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Direct Reports</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Title</th>
                    <th>Department</th>
                    <th>Programs</th>
                  </tr>
                </thead>
                <tbody>
                  {supervisorData && supervisorData.direct_reports.length > 0 ? (
                    supervisorData.direct_reports.map((report) => (
                      <DirectReportRow
                        key={report.user_id}
                        report={report}
                        availablePrograms={supervisorData.assigned_programs}
                        onAssign={handleAssign}
                        onUnassign={handleUnassign}
                      />
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4}>
                        <div className="empty-state"><p>No direct reports.</p></div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {shortcuts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Quick Links</span>
          </div>
          <div className="card-body">
            <div className="charts-grid">
              {shortcuts.map((shortcut) => (
                <Link
                  key={shortcut.to}
                  to={shortcut.to}
                  className="card"
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className="card-body">
                    <div className="card-title" style={{ marginBottom: ".25rem" }}>{shortcut.label}</div>
                    <div style={{ fontSize: ".875rem", color: "var(--ink-500)" }}>{shortcut.description}</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}

export function HomePage() {
  const { user } = useAuth();

  if (user?.role === "inspector" || user?.is_inspector) {
    return <InspectorLandingPage />;
  }

  return <RoleHome role={user?.role ?? "readonly"} name={user?.full_name || user?.username || ""} />;
}
