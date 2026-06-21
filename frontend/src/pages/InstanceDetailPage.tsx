import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useParams } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { StatusBadge } from "../components/ui/StatusBadge";
import {
  advanceInstance,
  cancelInstance,
  fetchAvailableTransitions,
  fetchInstance,
  fetchInstanceAuditLog,
} from "../lib/workflowsApi";
import type { AuditLogEntry, AvailableTransition, WorkflowInstanceDetail } from "../types";

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function formatDateTime(value: string | null) {
  return value ? dateTimeFormatter.format(new Date(value)) : "—";
}

export function InstanceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [instance, setInstance] = useState<WorkflowInstanceDetail | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [transitions, setTransitions] = useState<AvailableTransition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = async (instanceId: string) => {
    setIsLoading(true);
    try {
      const [inst, logs, trans] = await Promise.all([
        fetchInstance(instanceId),
        fetchInstanceAuditLog(instanceId),
        fetchAvailableTransitions(instanceId),
      ]);
      setInstance(inst);
      setAuditLog(logs);
      setTransitions(trans);
      setError(null);
    } catch {
      setError("Unable to load this request.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (id) void load(id);
  }, [id]);

  const handleAdvance = async (triggerEvent: string) => {
    if (!id) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await advanceInstance(id, triggerEvent);
      await load(id);
    } catch (err) {
      let errorMessage = "Unable to advance this request.";
      if (axios.isAxiosError(err)) {
        // Try to get error message from response
        if (err.response?.data?.detail) {
          errorMessage = String(err.response.data.detail);
        } else if (err.response?.data?.message) {
          errorMessage = String(err.response.data.message);
        } else if (err.response?.statusText) {
          errorMessage = err.response.statusText;
        } else if (err.message) {
          errorMessage = err.message;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setActionError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!id) return;
    if (!window.confirm("Cancel this request? This cannot be undone.")) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await cancelInstance(id);
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setActionError(String(err.response.data.detail));
      } else {
        setActionError("Unable to cancel this request.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <AppLayout title="Request" breadcrumb={["Requests"]}>
        <div className="empty-state">Loading…</div>
      </AppLayout>
    );
  }

  if (error || !instance) {
    return (
      <AppLayout title="Request" breadcrumb={["Requests"]}>
        <div className="alert alert-error">{error ?? "Request not found."}</div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/instances")}>
          Back to Requests
        </button>
      </AppLayout>
    );
  }

  const isFinalized = ["Approved", "Rejected", "Cancelled"].includes(instance.status);

  return (
    <AppLayout
      title={instance.reference_no}
      breadcrumb={["Requests"]}
      actions={
        !isFinalized && (
          <button type="button" className="btn btn-secondary btn-sm" disabled={isSubmitting} onClick={() => void handleCancel()}>
            Cancel Request
          </button>
        )
      }
    >
      {actionError && <div className="alert alert-error">{actionError}</div>}

      <div className="card">
        <div className="card-header">
          <span className="card-title">{instance.workflow_name}</span>
          <StatusBadge status={instance.status} />
        </div>
        <div className="detail-grid">
          <div>
            <div className="detail-field-label">Current Step</div>
            <div className="detail-field-value">{instance.current_step_name ?? "—"}</div>
          </div>
          <div>
            <div className="detail-field-label">Priority</div>
            <div className="detail-field-value">{instance.priority}</div>
          </div>
          <div>
            <div className="detail-field-label">Initiated By</div>
            <div className="detail-field-value">{instance.initiated_by_name}</div>
          </div>
          <div>
            <div className="detail-field-label">Started</div>
            <div className="detail-field-value">{formatDateTime(instance.started_at)}</div>
          </div>
          <div>
            <div className="detail-field-label">Due</div>
            <div className="detail-field-value">{formatDateTime(instance.due_date)}</div>
          </div>
          <div>
            <div className="detail-field-label">Completed</div>
            <div className="detail-field-value">{formatDateTime(instance.completed_at)}</div>
          </div>
        </div>
      </div>

      {!isFinalized && transitions.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Available Actions</span>
          </div>
          <div className="form-row">
            {transitions.map((t) => (
              <button
                key={t.trigger_event}
                type="button"
                className="btn btn-primary btn-sm"
                disabled={isSubmitting}
                onClick={() => void handleAdvance(t.trigger_event)}
              >
                {t.transition_name} → {t.to_step__step_name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <span className="card-title">Tasks</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Step</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Due</th>
                <th>Completed</th>
              </tr>
            </thead>
            <tbody>
              {instance.tasks.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state"><p>No tasks yet.</p></div>
                  </td>
                </tr>
              ) : (
                instance.tasks.map((task) => (
                  <tr key={task.task_id}>
                    <td>{task.step_name}</td>
                    <td><span className="badge badge-blue">{task.status}</span></td>
                    <td>{task.assigned_to_name ?? "—"}</td>
                    <td>{formatDateTime(task.due_date)}</td>
                    <td>{formatDateTime(task.completed_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Audit Log</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>From</th>
                <th>To</th>
                <th>Actor</th>
                <th>Notes</th>
                <th>Logged At</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state"><p>No audit history.</p></div>
                  </td>
                </tr>
              ) : (
                auditLog.map((entry) => (
                  <tr key={entry.log_id}>
                    <td>{entry.action}</td>
                    <td>{entry.from_status ?? "—"}</td>
                    <td>{entry.to_status ?? "—"}</td>
                    <td>{entry.actor_name ?? "—"}</td>
                    <td>{entry.notes ?? "—"}</td>
                    <td>{formatDateTime(entry.logged_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
