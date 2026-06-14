import { useEffect, useState } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { StatusBadge } from "../components/ui/StatusBadge";
import { StatCard } from "../components/ui/StatCard";
import {
  fetchInstanceCount,
  fetchOverdueTaskCount,
  fetchRecentInstances,
  fetchTaskCount,
} from "../lib/workflowsApi";
import type { WorkflowInstance } from "../types";

interface Stats {
  total: number;
  inProgress: number;
  approved: number;
  tasks: number;
  overdue: number;
}

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<WorkflowInstance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [total, inProgress, approved, tasks, overdue, recentInstances] = await Promise.all([
          fetchInstanceCount(),
          fetchInstanceCount("InProgress"),
          fetchInstanceCount("Approved"),
          fetchTaskCount(),
          fetchOverdueTaskCount(),
          fetchRecentInstances(5),
        ]);

        if (cancelled) return;
        setStats({ total, inProgress, approved, tasks, overdue });
        setRecent(recentInstances);
      } catch {
        if (!cancelled) {
          setError("Unable to load dashboard data.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppLayout title="Dashboard">
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading ? (
        <div className="empty-state">Loading dashboard…</div>
      ) : (
        <>
          <div className="stat-grid">
            <StatCard label="Total Requests" value={stats?.total ?? 0} color="blue" />
            <StatCard label="In Progress" value={stats?.inProgress ?? 0} color="blue" />
            <StatCard label="Approved" value={stats?.approved ?? 0} color="green" />
            <StatCard label="Open Tasks" value={stats?.tasks ?? 0} color="amber" />
            <StatCard label="Overdue Tasks" value={stats?.overdue ?? 0} color="red" />
          </div>

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
        </>
      )}
    </AppLayout>
  );
}
