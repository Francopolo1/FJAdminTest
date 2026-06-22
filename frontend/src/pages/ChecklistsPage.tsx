import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { Pagination } from "../components/ui/Pagination";
import { fetchChecklistRuns } from "../lib/checklistsApi";
import type { ChecklistRunListItem } from "../types";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "NotStarted", label: "Not Started" },
  { value: "InProgress", label: "In Progress" },
  { value: "Completed", label: "Completed" },
  { value: "Skipped", label: "Skipped" },
];

const RUN_STATUS_BADGE: Record<string, string> = {
  NotStarted: "badge-gray",
  InProgress: "badge-blue",
  Completed: "badge-green",
  Skipped: "badge-amber",
};

interface ChecklistRunGroup {
  key: string;
  programTitle: string;
  activity: string;
  runs: ChecklistRunListItem[];
}

function groupChecklistRuns(runs: ChecklistRunListItem[]): ChecklistRunGroup[] {
  const groups = new Map<string, ChecklistRunGroup>();
  for (const run of runs) {
    const programTitle = run.program_title || "Unassigned Program";
    const activity = run.activity || "Unassigned Activity";
    const key = `${programTitle}|${activity}`;
    let group = groups.get(key);
    if (!group) {
      group = { key, programTitle, activity, runs: [] };
      groups.set(key, group);
    }
    group.runs.push(run);
  }
  return [...groups.values()].sort((a, b) =>
    a.programTitle.localeCompare(b.programTitle) || a.activity.localeCompare(b.activity),
  );
}

export function ChecklistsPage() {
  const [runs, setRuns] = useState<ChecklistRunListItem[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchChecklistRuns({ page, pageSize: PAGE_SIZE, status })
      .then((data) => {
        if (cancelled) return;
        setRuns(data.results);
        setCount(data.count);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load checklists.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, status]);

  return (
    <AppLayout title="Checklists">
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
        </div>

        <div className="table-wrap">
          {isLoading ? (
            <div className="empty-state"><p>Loading…</p></div>
          ) : runs.length === 0 ? (
            <div className="empty-state"><p>No checklist runs found.</p></div>
          ) : (
            groupChecklistRuns(runs).map((group) => (
              <div key={group.key} style={{ marginBottom: "1.5rem" }}>
                <h3 style={{ margin: "0 0 .5rem" }}>
                  {group.programTitle} — {group.activity}
                </h3>
                <table>
                  <thead>
                    <tr>
                      <th>Facility</th>
                      <th>Request</th>
                      <th>Workflow</th>
                      <th>Checklist</th>
                      <th>Status</th>
                      <th>Required</th>
                      <th>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.runs.map((run) => (
                      <tr key={run.run_id}>
                        <td>{run.facility_name ?? "—"}</td>
                        <td>{run.reference_no}</td>
                        <td>{run.workflow_name}</td>
                        <td>
                          <Link to={`/checklists/${run.run_id}`}>{run.template_title}</Link>
                        </td>
                        <td><span className={`badge ${RUN_STATUS_BADGE[run.status] ?? "badge-gray"}`}>{run.status}</span></td>
                        <td>{run.blocks_advance ? "Yes" : "No"}</td>
                        <td>
                          <div className="progress" style={{ width: 120 }}>
                            <div
                              className={`progress-fill${run.completion_pct >= 100 ? " fill-green" : ""}`}
                              style={{ width: `${run.completion_pct}%` }}
                            />
                          </div>
                          <span style={{ fontSize: 12, color: "var(--ink-500)" }}>{run.answered_items}/{run.total_items}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))
          )}
        </div>

        <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
      </div>
    </AppLayout>
  );
}
