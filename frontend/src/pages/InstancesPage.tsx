import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { Pagination } from "../components/ui/Pagination";
import { StatusBadge } from "../components/ui/StatusBadge";
import { fetchInstances } from "../lib/workflowsApi";
import type { WorkflowInstance } from "../types";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "Draft", label: "Draft" },
  { value: "InProgress", label: "In Progress" },
  { value: "Approved", label: "Approved" },
  { value: "Rejected", label: "Rejected" },
  { value: "Cancelled", label: "Cancelled" },
  { value: "OnHold", label: "On Hold" },
];

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

interface InstanceGroup {
  key: string;
  programTitle: string;
  activity: string;
  instances: WorkflowInstance[];
}

function groupInstances(instances: WorkflowInstance[]): InstanceGroup[] {
  const groups = new Map<string, InstanceGroup>();
  for (const instance of instances) {
    const programTitle = instance.program_title || "Unassigned Program";
    const activity = instance.activity || "Unassigned Activity";
    const key = `${programTitle}|${activity}`;
    let group = groups.get(key);
    if (!group) {
      group = { key, programTitle, activity, instances: [] };
      groups.set(key, group);
    }
    group.instances.push(instance);
  }
  return [...groups.values()].sort((a, b) =>
    a.programTitle.localeCompare(b.programTitle) || a.activity.localeCompare(b.activity),
  );
}

export function InstancesPage() {
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchInstances({ page, pageSize: PAGE_SIZE, status, search })
      .then((data) => {
        if (cancelled) return;
        setInstances(data.results);
        setCount(data.count);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load requests.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, status, search]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  return (
    <AppLayout title="Requests">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <form className="form-row" onSubmit={handleSearchSubmit}>
          <div>
            <label className="field-label" htmlFor="search">Search</label>
            <input
              id="search"
              className="input"
              placeholder="Reference number or workflow"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
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
          <button type="submit" className="btn btn-primary" style={{ alignSelf: "flex-end" }}>
            Search
          </button>
        </form>

        <div className="table-wrap">
          {isLoading ? (
            <div className="empty-state"><p>Loading…</p></div>
          ) : instances.length === 0 ? (
            <div className="empty-state"><p>No requests found.</p></div>
          ) : (
            groupInstances(instances).map((group) => (
              <div key={group.key} style={{ marginBottom: "1.5rem" }}>
                <h3 style={{ margin: "0 0 .5rem" }}>
                  {group.programTitle} — {group.activity}
                </h3>
                <table>
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Workflow</th>
                      <th>Status</th>
                      <th>Current Step</th>
                      <th>Initiated By</th>
                      <th>Started</th>
                      <th>Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.instances.map((instance) => (
                      <tr key={instance.instance_id}>
                        <td>
                          <Link to={`/instances/${instance.instance_id}`}>{instance.reference_no}</Link>
                        </td>
                        <td>{instance.workflow_name}</td>
                        <td><StatusBadge status={instance.status} /></td>
                        <td>{instance.current_step_name ?? "—"}</td>
                        <td>{instance.initiated_by_name}</td>
                        <td>{dateFormatter.format(new Date(instance.started_at))}</td>
                        <td>{instance.due_date ? dateFormatter.format(new Date(instance.due_date)) : "—"}</td>
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
