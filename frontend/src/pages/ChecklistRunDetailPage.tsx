import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useParams } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import {
  createBoxFolder,
  fetchChecklistProgress,
  fetchChecklistRun,
  reopenChecklistRun,
  skipChecklistRun,
  submitChecklistResponses,
} from "../lib/checklistsApi";
import type { ChecklistAnswer } from "../lib/checklistsApi";
import { createViolation, deleteViolation, fetchSeverityLevels } from "../lib/complianceApi";
import { useAuth } from "../contexts/AuthContext";
import { API_BASE_URL } from "../lib/api";
import type { ChecklistProgress, ChecklistRunDetail, ViolationSeverityLevel } from "../types";

const RUN_STATUS_BADGE: Record<string, string> = {
  NotStarted: "badge-gray",
  InProgress: "badge-blue",
  Completed: "badge-green",
  Skipped: "badge-amber",
};

interface AnswerState {
  value: string;
  notes: string;
  boxFolderUrl: string;
}

interface ViolationFormState {
  isOpen: boolean;
  ruleId: string;
  severityId: string;
  description: string;
  date: string;
}

function normalizeDefaultValue(defaultValue: string | null): string {
  if (!defaultValue) return "";
  try {
    const parsed = JSON.parse(defaultValue);
    if (typeof parsed === "string") return parsed;
  } catch {
    // not JSON-encoded, use as-is
  }
  return defaultValue;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

type ExampleKind = "image" | "video" | "pdf" | "other";

function resolveExampleUrl(url: string): string {
  return /^https?:\/\//i.test(url) ? url : `${API_BASE_URL}${url}`;
}

function exampleKind(url: string): ExampleKind {
  const path = url.split(/[?#]/)[0].toLowerCase();
  if (/\.(png|jpe?g|gif|webp|svg|bmp)$/.test(path)) return "image";
  if (/\.(mp4|webm|ogg|mov)$/.test(path)) return "video";
  if (/\.pdf$/.test(path)) return "pdf";
  return "other";
}

export function ChecklistRunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [run, setRun] = useState<ChecklistRunDetail | null>(null);
  const [progress, setProgress] = useState<ChecklistProgress | null>(null);
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [severityLevels, setSeverityLevels] = useState<ViolationSeverityLevel[]>([]);
  const [violationForms, setViolationForms] = useState<Record<string, ViolationFormState>>({});
  const [violationError, setViolationError] = useState<string | null>(null);
  const [violationSubmittingItem, setViolationSubmittingItem] = useState<string | null>(null);
  const [violationDeletingId, setViolationDeletingId] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [creatingBoxFolder, setCreatingBoxFolder] = useState<Record<string, boolean>>({});
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  const toggleCategory = (category: string) => {
    setCollapsedCategories((prev) => ({ ...prev, [category]: !prev[category] }));
  };

  const groupedItems = (progress?.items ?? []).reduce<{ category: string; items: ChecklistProgress["items"] }[]>(
    (groups, item) => {
      const category = item.category || "Items";
      const last = groups[groups.length - 1];
      if (last && last.category === category) {
        last.items.push(item);
      } else {
        groups.push({ category, items: [item] });
      }
      return groups;
    },
    [],
  );

  const load = async (runId: string) => {
    setIsLoading(true);
    try {
      const [runData, progressData] = await Promise.all([
        fetchChecklistRun(runId),
        fetchChecklistProgress(runId),
      ]);
      setRun(runData);
      setProgress(progressData);
      setAnswers((prev) => {
        const next: Record<string, AnswerState> = {};
        for (const item of progressData.items) {
          next[item.item_id] = prev[item.item_id] ?? {
            value: item.response_value ?? (item.response_type === "MultiChoice" ? normalizeDefaultValue(item.default_value) : ""),
            notes: item.notes ?? "",
            boxFolderUrl: item.box_folder_url ?? "",
          };
        }
        return next;
      });
      setError(null);
    } catch {
      setError("Unable to load this checklist.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (id) void load(id);
  }, [id]);

  useEffect(() => {
    fetchSeverityLevels()
      .then(setSeverityLevels)
      .catch(() => setSeverityLevels([]));
  }, []);

  const toggleViolationForm = (item: ChecklistProgress["items"][number]) => {
    setViolationForms((prev) => {
      const existing = prev[item.item_id];
      if (existing?.isOpen) {
        return { ...prev, [item.item_id]: { ...existing, isOpen: false } };
      }
      return {
        ...prev,
        [item.item_id]: {
          isOpen: true,
          ruleId: existing?.ruleId ?? item.compliance_rules[0]?.checklist_item_compliance_rule_id ?? "",
          severityId: existing?.severityId ?? severityLevels[0]?.violation_severity_level_id ?? "",
          description: existing?.description ?? "",
          date: existing?.date ?? todayIso(),
        },
      };
    });
  };

  const updateViolationForm = (itemId: string, patch: Partial<ViolationFormState>) => {
    setViolationForms((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], ...patch } as ViolationFormState,
    }));
  };

  const handleReportViolation = async (item: ChecklistProgress["items"][number]) => {
    if (!id) return;
    const form = violationForms[item.item_id];
    if (!form || !item.response_id) return;

    setViolationSubmittingItem(item.item_id);
    setViolationError(null);
    try {
      await createViolation({
        checklist_item_compliance_rule_id: form.ruleId,
        violation_severity_level_id: form.severityId,
        violation_date: form.date,
        violation_description: form.description || undefined,
        checklist_response_id: item.response_id,
      });
      setViolationForms((prev) => ({ ...prev, [item.item_id]: { ...form, isOpen: false, description: "" } }));
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setViolationError(String(err.response.data.detail));
      } else {
        setViolationError("Unable to record this violation.");
      }
    } finally {
      setViolationSubmittingItem(null);
    }
  };

  const handleDeleteViolation = async (violationId: string) => {
    if (!id) return;
    if (!window.confirm("Remove this compliance violation?")) return;

    setViolationDeletingId(violationId);
    setViolationError(null);
    try {
      await deleteViolation(violationId);
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setViolationError(String(err.response.data.detail));
      } else {
        setViolationError("Unable to remove this violation.");
      }
    } finally {
      setViolationDeletingId(null);
    }
  };

  const setAnswerValue = (itemId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [itemId]: { ...prev[itemId], value } }));
  };

  const setAnswerNotes = (itemId: string, notes: string) => {
    setAnswers((prev) => ({ ...prev, [itemId]: { ...prev[itemId], notes } }));
  };

  const setAnswerBoxFolderUrl = (itemId: string, boxFolderUrl: string) => {
    setAnswers((prev) => ({ ...prev, [itemId]: { ...prev[itemId], boxFolderUrl } }));
  };

  const handleCreateBoxFolder = async (itemId: string) => {
    if (!id) return;
    setCreatingBoxFolder((prev) => ({ ...prev, [itemId]: true }));
    setActionError(null);
    try {
      const resp = await createBoxFolder(id, itemId);
      const url = resp.box_folder_url ?? "";
      setAnswerBoxFolderUrl(itemId, url);
      if (url) {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as { detail?: string };
        setActionError(data.detail || "Failed to create Box folder.");
      } else {
        setActionError("Failed to create Box folder.");
      }
    } finally {
      setCreatingBoxFolder((prev) => ({ ...prev, [itemId]: false }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !progress) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      const payload: ChecklistAnswer[] = progress.items.map((item) => ({
        item: item.item_id,
        response_value: answers[item.item_id]?.value ?? "",
        notes: answers[item.item_id]?.notes ?? "",
        box_folder_url: answers[item.item_id]?.boxFolderUrl ?? "",
      }));
      await submitChecklistResponses(id, payload);
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as { detail?: string; errors?: { detail: string }[] };
        setActionError(data.detail ?? data.errors?.map((e) => e.detail).join("; ") ?? "Unable to save responses.");
      } else {
        setActionError("Unable to save responses.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReopen = async () => {
    if (!id) return;
    if (!window.confirm("Reopen this checklist for editing? This will set it back to In Progress.")) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await reopenChecklistRun(id);
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setActionError(String(err.response.data.detail));
      } else {
        setActionError("Unable to reopen this checklist.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async () => {
    if (!id) return;
    if (!window.confirm("Skip this checklist?")) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await skipChecklistRun(id);
      await load(id);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setActionError(String(err.response.data.detail));
      } else {
        setActionError("Unable to skip this checklist.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <AppLayout title="Checklist" breadcrumb={["Checklists"]}>
        <div className="empty-state">Loading…</div>
      </AppLayout>
    );
  }

  if (error || !run || !progress) {
    return (
      <AppLayout title="Checklist" breadcrumb={["Checklists"]}>
        <div className="alert alert-error">{error ?? "Checklist not found."}</div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/checklists")}>
          Back to Checklists
        </button>
      </AppLayout>
    );
  }

  const isLocked = run.status === "Completed" || run.status === "Skipped";

  return (
    <AppLayout title={run.template_title} breadcrumb={["Checklists", run.reference_no]}>
      {actionError && <div className="alert alert-error">{actionError}</div>}
      {violationError && <div className="alert alert-error">{violationError}</div>}

      <div className="card">
        <div className="card-header">
          <span className="card-title">{run.reference_no} — {run.workflow_name}</span>
          <span className={`badge ${RUN_STATUS_BADGE[run.status] ?? "badge-gray"}`}>{run.status}</span>
        </div>
        {run.template_description && <p style={{ color: "var(--ink-600)", fontSize: 13 }}>{run.template_description}</p>}

        <div className="detail-grid">
          {run.facility_name && (
            <div>
              <div className="detail-field-label">Facility</div>
              <div className="detail-field-value">{run.facility_name}</div>
              {(run.facility_address || run.facility_city_state_zip) && (
                <div style={{ fontSize: 12, color: "var(--ink-500)", marginTop: 2 }}>
                  {run.facility_address && <div>{run.facility_address}</div>}
                  {run.facility_city_state_zip && <div>{run.facility_city_state_zip}</div>}
                </div>
              )}
            </div>
          )}
          {run.facility_phone && (
            <div>
              <div className="detail-field-label">Phone</div>
              <div className="detail-field-value">{run.facility_phone}</div>
            </div>
          )}
          {run.license_number && (
            <div>
              <div className="detail-field-label">License #</div>
              <div className="detail-field-value">{run.license_number}</div>
            </div>
          )}
          {run.license_expire_date && (
            <div>
              <div className="detail-field-label">License Expires</div>
              <div className="detail-field-value">
                {new Date(run.license_expire_date).toLocaleDateString()}
              </div>
            </div>
          )}
          {run.tracking_id && (
            <div>
              <div className="detail-field-label">Tracking ID</div>
              <div className="detail-field-value">{run.tracking_id}</div>
            </div>
          )}
          {run.started_at && (
            <div>
              <div className="detail-field-label">Started</div>
              <div className="detail-field-value">
                {new Date(run.started_at).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        <div className="detail-grid" style={{ marginTop: "1rem" }}>
          <div>
            <div className="detail-field-label">Overall Completion</div>
            <div className="progress" style={{ marginTop: 4 }}>
              <div className={`progress-fill${progress.completion_pct >= 100 ? " fill-green" : ""}`} style={{ width: `${progress.completion_pct}%` }} />
            </div>
            <div className="detail-field-value" style={{ marginTop: 4 }}>{progress.answered_items}/{progress.total_items}</div>
          </div>
          <div>
            <div className="detail-field-label">Required Completion</div>
            <div className="progress" style={{ marginTop: 4 }}>
              <div className={`progress-fill${progress.required_completion_pct >= 100 ? " fill-green" : " fill-amber"}`} style={{ width: `${progress.required_completion_pct}%` }} />
            </div>
            <div className="detail-field-value" style={{ marginTop: 4 }}>{progress.answered_required}/{progress.total_required}</div>
          </div>
          <div>
            <div className="detail-field-label">Blocks Advance</div>
            <div className="detail-field-value">{run.blocks_advance ? "Yes" : "No"}</div>
          </div>
        </div>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)}>
        {groupedItems.map((group) => (
          <div className="card" key={group.category}>
            <div
              className="card-header"
              style={{ cursor: "pointer" }}
              onClick={() => toggleCategory(group.category)}
            >
              <span className="card-title">{group.category}</span>
              <span style={{ fontSize: 12, color: "var(--ink-400)" }}>
                {collapsedCategories[group.category] ? "Show ▾" : "Hide ▴"}
              </span>
            </div>

            {!collapsedCategories[group.category] && group.items.map((item) => (
          <div className="checklist-item" key={item.item_id}>
            <div className="checklist-item-text">
              {item.item_text}{item.is_required && <span style={{ color: "var(--red-600)" }}> *</span>}
            </div>
            {item.help_text && <div className="checklist-item-help">{item.help_text}</div>}
            {(item.example_file_url || item.example_url) && (
              <div className="checklist-item-help">
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setPreviewUrl(
                    item.example_file_url ?? resolveExampleUrl(item.example_url!)
                  )}
                >
                  View example
                </button>
              </div>
            )}

            {renderInput(item, answers[item.item_id]?.value ?? "", (value) => setAnswerValue(item.item_id, value), isLocked)}

            <div style={{ marginTop: ".5rem" }}>
              <input
                className="input"
                style={{ width: "100%" }}
                placeholder="Notes (optional)"
                value={answers[item.item_id]?.notes ?? ""}
                onChange={(e) => setAnswerNotes(item.item_id, e.target.value)}
                disabled={isLocked}
              />
            </div>

            <div style={{ marginTop: ".5rem", display: "flex", gap: ".5rem", alignItems: "center" }}>
              <input
                className="input"
                style={{ width: "100%" }}
                type="url"
                placeholder="Box.com documents folder link (optional)"
                value={answers[item.item_id]?.boxFolderUrl ?? ""}
                onChange={(e) => setAnswerBoxFolderUrl(item.item_id, e.target.value)}
                disabled={isLocked}
              />
              {!isLocked && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ whiteSpace: "nowrap" }}
                  onClick={() => {
                    const url = answers[item.item_id]?.boxFolderUrl;
                    if (url) {
                      window.open(url, "_blank", "noopener,noreferrer");
                    } else {
                      void handleCreateBoxFolder(item.item_id);
                    }
                  }}
                  disabled={creatingBoxFolder[item.item_id]}
                >
                  {creatingBoxFolder[item.item_id] ? "Creating…" : "Create Substantiation and Documentation Folder"}
                </button>
              )}
              {isLocked && item.box_folder_url && (
                <a href={item.box_folder_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12 }}>
                  Open Box folder
                </a>
              )}
            </div>

            {item.responded_by && (
              <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: ".375rem" }}>
                Last answered by {item.responded_by}
              </div>
            )}

            {item.compliance_rules.length > 0 && (
              <div style={{ marginTop: ".5rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: 12 }}
                  onClick={() => toggleViolationForm(item)}
                  disabled={!item.response_id}
                  title={!item.response_id ? "Save this response before reporting a violation." : undefined}
                >
                  {violationForms[item.item_id]?.isOpen ? "Cancel" : "Report Violation"}
                </button>

                {violationForms[item.item_id]?.isOpen && (
                  <div style={{ marginTop: ".5rem", display: "flex", flexDirection: "column", gap: ".5rem", maxWidth: 420 }}>
                    {item.compliance_rules.length > 1 && (
                      <select
                        className="select"
                        value={violationForms[item.item_id]?.ruleId ?? ""}
                        onChange={(e) => updateViolationForm(item.item_id, { ruleId: e.target.value })}
                      >
                        {item.compliance_rules.map((rule) => (
                          <option key={rule.checklist_item_compliance_rule_id} value={rule.checklist_item_compliance_rule_id}>
                            {rule.rule_code} — {rule.rule_name}
                          </option>
                        ))}
                      </select>
                    )}
                    <select
                      className="select"
                      value={violationForms[item.item_id]?.severityId ?? ""}
                      onChange={(e) => updateViolationForm(item.item_id, { severityId: e.target.value })}
                    >
                      {severityLevels.map((level) => (
                        <option key={level.violation_severity_level_id} value={level.violation_severity_level_id}>
                          {level.name}
                        </option>
                      ))}
                    </select>
                    <input
                      type="date"
                      className="input"
                      value={violationForms[item.item_id]?.date ?? todayIso()}
                      onChange={(e) => updateViolationForm(item.item_id, { date: e.target.value })}
                    />
                    <textarea
                      className="input"
                      placeholder="Violation description (optional)"
                      value={violationForms[item.item_id]?.description ?? ""}
                      onChange={(e) => updateViolationForm(item.item_id, { description: e.target.value })}
                    />
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ alignSelf: "flex-start" }}
                      disabled={violationSubmittingItem === item.item_id || !violationForms[item.item_id]?.severityId || !violationForms[item.item_id]?.ruleId}
                      onClick={() => void handleReportViolation(item)}
                    >
                      Save Violation
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
            ))}
          </div>
        ))}

        {progress.violations.length > 0 && (
          <div className="card">
            <div
              className="card-header"
              style={{ cursor: "pointer" }}
              onClick={() => toggleCategory("__violations")}
            >
              <span className="card-title">Compliance Violations</span>
              <span style={{ fontSize: 12, color: "var(--ink-400)" }}>
                {collapsedCategories.__violations ? "Show ▾" : "Hide ▴"}
              </span>
            </div>
            {!collapsedCategories.__violations && progress.violations.map((violation) => (
              <div key={violation.compliance_violation_id} className="checklist-item">
                <div className="checklist-item-text" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                  <span>
                    {violation.rule_code} — {violation.rule_name}
                    <span className="badge badge-red" style={{ marginLeft: ".5rem" }}>
                      {violation.severity_name}
                    </span>
                  </span>
                  {user?.is_staff && (
                    <button
                      type="button"
                      className="link-button"
                      style={{ color: "var(--red-600)", flexShrink: 0 }}
                      disabled={violationDeletingId === violation.compliance_violation_id}
                      onClick={() => void handleDeleteViolation(violation.compliance_violation_id)}
                    >
                      Remove
                    </button>
                  )}
                </div>
                {violation.item_text && (
                  <div className="checklist-item-help">Item: {violation.item_text}</div>
                )}
                {violation.violation_description && (
                  <div style={{ fontSize: 13, color: "var(--ink-600)", marginTop: ".25rem" }}>
                    {violation.violation_description}
                  </div>
                )}
                <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: ".375rem" }}>
                  Violation date: {violation.violation_date}
                </div>
              </div>
            ))}
          </div>
        )}

        {!isLocked && (
          <div className="form-row" style={{ marginTop: "1rem" }}>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              Save Responses
            </button>
            {!run.blocks_advance && (
              <button type="button" className="btn btn-secondary" disabled={isSubmitting} onClick={() => void handleSkip()}>
                Skip Checklist
              </button>
            )}
          </div>
        )}

        {isLocked && (user?.is_staff || user?.role === "supervisor") && (
          <div className="form-row" style={{ marginTop: "1rem" }}>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={isSubmitting}
              onClick={() => void handleReopen()}
            >
              Reopen Checklist
            </button>
          </div>
        )}
      </form>

      {previewUrl && (
        <div className="modal-overlay" onClick={() => setPreviewUrl(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="card-title">Example</span>
              <button type="button" className="btn btn-secondary" onClick={() => setPreviewUrl(null)}>
                Close
              </button>
            </div>
            <div className="modal-body"><ExamplePreview url={previewUrl} /></div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}

function ExamplePreview({ url }: { url: string }) {
  const [imgError, setImgError] = useState(false);
  const kind = exampleKind(url);

  if (kind === "image") {
    if (imgError) {
      return (
        <div className="example-unavailable">
          <p>This example image could not be loaded.</p>
          <a href={url} target="_blank" rel="noopener noreferrer">
            Try opening it directly
          </a>
        </div>
      );
    }
    return (
      <img
        src={url}
        alt="Example"
        onError={() => setImgError(true)}
      />
    );
  }

  if (kind === "video") {
    return (
      <video src={url} controls autoPlay>
        Your browser does not support embedded video.
      </video>
    );
  }

  if (kind === "pdf") {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: ".5rem", width: "100%" }}>
        <iframe src={url} title="Example" />
        <a href={url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: "var(--ink-500)" }}>
          Open in new tab ↗
        </a>
      </div>
    );
  }

  return (
    <div className="example-unavailable">
      <a href={url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
        Open example in a new tab ↗
      </a>
    </div>
  );
}

function renderInput(
  item: ChecklistProgress["items"][number],
  value: string,
  onChange: (value: string) => void,
  disabled: boolean,
) {
  switch (item.response_type) {
    case "YesNo":
      return (
        <div className="choice-options">
          {["Yes", "No"].map((opt) => (
            <label key={opt} style={{ display: "flex", alignItems: "center", gap: ".25rem" }}>
              <input
                type="radio"
                name={item.item_id}
                checked={value === opt}
                onChange={() => onChange(opt)}
                disabled={disabled}
              />
              {opt}
            </label>
          ))}
        </div>
      );
    case "Number":
      return <input type="number" className="input" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
    case "Date":
      return <input type="date" className="input" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
    case "SingleChoice":
      return (
        <select className="select" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
          <option value="">— Select —</option>
          {(item.options ?? []).map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    case "MultiChoice": {
      const selected = value ? value.split(",").map((v) => v.trim()) : [];
      return (
        <div className="choice-options">
          {(item.options ?? []).map((opt) => (
            <label key={opt} style={{ display: "flex", alignItems: "center", gap: ".25rem" }}>
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                disabled={disabled}
                onChange={(e) => {
                  const next = e.target.checked ? [...selected, opt] : selected.filter((v) => v !== opt);
                  onChange(next.join(", "));
                }}
              />
              {opt}
            </label>
          ))}
        </div>
      );
    }
    case "FileUpload":
      return <input className="input" style={{ width: "100%" }} placeholder="File reference / URL" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
    case "Signature":
      return <input className="input" style={{ width: "100%" }} placeholder="Type your full name to sign" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
    default:
      return <input className="input" style={{ width: "100%" }} value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
  }
}
