import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { Pagination } from "../components/ui/Pagination";
import { fetchTasks } from "../lib/workflowsApi";
import type { WorkflowTask } from "../types";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "Pending", label: "Pending" },
  { value: "InProgress", label: "In Progress" },
  { value: "Completed", label: "Completed" },
  { value: "Delegated", label: "Delegated" },
];

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const TASK_STATUS_BADGE: Record<string, string> = {
  Pending: "badge-amber",
  InProgress: "badge-blue",
  Completed: "badge-green",
  Delegated: "badge-gray",
};

export function TasksPage() {
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchTasks({ page, pageSize: PAGE_SIZE, status, overdueOnly })
      .then((data) => {
        if (cancelled) return;
        setTasks(data.results);
        setCount(data.count);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load tasks.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, status, overdueOnly]);

  return (
    <AppLayout title="Tasks">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="form-row">
          <div>
            <label className="field-label" htmlFor="status">Status</label>
            <select
              id="status"
              className="select"
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <label style={{ display: "flex", alignItems: "center", gap: ".375rem", marginTop: "1.4rem" }}>
            <input
              type="checkbox"
              checked={overdueOnly}
              onChange={(e) => {
                setPage(1);
                setOverdueOnly(e.target.checked);
              }}
            />
            Overdue only
          </label>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Step</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Due</th>
                <th>Hours Remaining</th>
                <th>Request</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state"><p>Loading…</p></div>
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state"><p>No tasks found.</p></div>
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.task_id}>
                    <td>{task.step_name}</td>
                    <td><span className={`badge ${TASK_STATUS_BADGE[task.status] ?? "badge-gray"}`}>{task.status}</span></td>
                    <td>{task.assigned_to_name ?? "—"}</td>
                    <td>{task.due_date ? dateTimeFormatter.format(new Date(task.due_date)) : "—"}</td>
                    <td>{task.hours_remaining ?? "—"}</td>
                    <td>
                      <Link to={`/instances/${task.instance}`}>View Request</Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
      </div>
    </AppLayout>
  );
}
