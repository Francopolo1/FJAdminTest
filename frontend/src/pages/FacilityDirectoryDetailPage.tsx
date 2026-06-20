import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { FacilityMap } from "../components/ui/FacilityMap";
import { StatusBadge } from "../components/ui/StatusBadge";
import { fetchFacilityDetail, startFacilityActivityWorkflow, updateFacilityProgramFacilityProfile } from "../lib/coreApi";
import type { FacilityDetail } from "../types";

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const RISK_BADGE: Record<string, string> = {
  LOW: "badge-green",
  MED: "badge-amber",
  HIGH: "badge-red",
};

function formatDate(value: string | null) {
  return value ? dateFormatter.format(new Date(value)) : "—";
}

function FacilityLocationCard({ location }: { location: FacilityDetail["location"] }) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!location) return null;

  const addressLines = [location.address_line1, location.address_line2].filter(Boolean);
  const cityStateZip = location.city_state_zip
    ?? [location.city, [location.state, location.postal_code].filter(Boolean).join(" ")].filter(Boolean).join(", ");

  const hasValidCoordinates =
    location.latitude != null && location.longitude != null
    && Math.abs(location.latitude) <= 90 && Math.abs(location.longitude) <= 180;

  if (addressLines.length === 0 && !cityStateZip && !hasValidCoordinates) return null;

  return (
    <div className="card" style={{ marginBottom: "1.25rem" }}>
      <div
        className="card-header"
        style={{ cursor: "pointer" }}
        onClick={() => setIsExpanded((expanded) => !expanded)}
      >
        <span className="card-title">Location</span>
        <span aria-hidden="true">{isExpanded ? "▾" : "▸"}</span>
      </div>
      {isExpanded && (
        <div className="card-body">
          <div className="detail-field-value" style={{ marginBottom: ".75rem" }}>
            {addressLines.map((line) => (
              <div key={line}>{line}</div>
            ))}
            {cityStateZip && <div>{cityStateZip}</div>}
          </div>
          {hasValidCoordinates && (
            <FacilityMap latitude={location.latitude!} longitude={location.longitude!} />
          )}
        </div>
      )}
    </div>
  );
}

function ProfileFields({
  programFacilityId,
  profile,
  onSaved,
}: {
  programFacilityId: string;
  profile: string | null;
  onSaved: (profile: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  let parsed: Record<string, unknown> | null = null;
  if (profile) {
    try {
      parsed = JSON.parse(profile) as Record<string, unknown>;
    } catch {
      parsed = null;
    }
  }

  if (!profile || !parsed) {
    return <div className="detail-field-value">{profile ?? "—"}</div>;
  }

  const entries = Object.entries(parsed);
  if (entries.length === 0) return <div className="detail-field-value">—</div>;

  function startEditing() {
    setDraft({ ...parsed });
    setSaveError(null);
    setIsEditing(true);
  }

  function cancelEditing() {
    setIsEditing(false);
    setSaveError(null);
  }

  async function save() {
    setIsSaving(true);
    setSaveError(null);
    try {
      const result = await updateFacilityProgramFacilityProfile(programFacilityId, draft);
      onSaved(result.profile);
      setIsEditing(false);
    } catch {
      setSaveError("Unable to save profile changes. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  if (!isEditing) {
    return (
      <>
        <div className="detail-grid">
          {entries.map(([key, value]) => (
            <div key={key}>
              <div className="detail-field-label">{key.replace(/_/g, " ")}</div>
              <div className="detail-field-value">{String(value)}</div>
            </div>
          ))}
        </div>
        <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: ".5rem" }} onClick={startEditing}>
          Edit Profile
        </button>
      </>
    );
  }

  return (
    <>
      <div className="detail-grid">
        {entries.map(([key, originalValue]) => {
          const isNumber = typeof originalValue === "number";
          const isBoolean = typeof originalValue === "boolean";
          return (
            <div key={key}>
              <div className="detail-field-label">{key.replace(/_/g, " ")}</div>
              {isBoolean ? (
                <select
                  className="select"
                  value={String(draft[key])}
                  onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.value === "true" }))}
                >
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              ) : (
                <input
                  type={isNumber ? "number" : "text"}
                  className="input"
                  value={draft[key] === undefined || draft[key] === null ? "" : String(draft[key])}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      [key]: isNumber ? Number(e.target.value) : e.target.value,
                    }))
                  }
                />
              )}
            </div>
          );
        })}
      </div>
      {saveError && <div className="alert alert-error" style={{ marginTop: ".5rem" }}>{saveError}</div>}
      <div style={{ display: "flex", gap: ".5rem", marginTop: ".5rem" }}>
        <button type="button" className="btn btn-primary btn-sm" disabled={isSaving} onClick={save}>
          {isSaving ? "Saving…" : "Save"}
        </button>
        <button type="button" className="btn btn-secondary btn-sm" disabled={isSaving} onClick={cancelEditing}>
          Cancel
        </button>
      </div>
    </>
  );
}

function AssignmentCard({
  assignment,
  startingWorkflowId,
  onProfileSaved,
  onStartWorkflow,
}: {
  assignment: FacilityDetail["assignments"][number];
  startingWorkflowId: string | null;
  onProfileSaved: (profile: string) => void;
  onStartWorkflow: (activityId: string, workflowId: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="card" style={{ marginBottom: "1.25rem" }}>
      <div
        className="card-header"
        style={{ cursor: "pointer" }}
        onClick={() => setIsExpanded((expanded) => !expanded)}
      >
        <span className="card-title">
          {assignment.program_code} — District {assignment.district ?? "—"}
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: ".5rem" }}>
          {assignment.risk_assessment && (
            <span className={`badge ${RISK_BADGE[assignment.risk_assessment] ?? "badge-gray"}`}>
              {assignment.risk_assessment_label ?? assignment.risk_assessment}
            </span>
          )}
          <span aria-hidden="true">{isExpanded ? "▾" : "▸"}</span>
        </div>
      </div>
      {isExpanded && (
        <>
          <div className="card-body">
            <div className="detail-grid" style={{ marginBottom: "1.25rem" }}>
              <div>
                <div className="detail-field-label">Type</div>
                <div className="detail-field-value">{assignment.facility_type ?? "—"}</div>
              </div>
              <div>
                <div className="detail-field-label">License #</div>
                <div className="detail-field-value">{assignment.license_number ?? "—"}</div>
              </div>
              <div>
                <div className="detail-field-label">Visit Frequency</div>
                <div className="detail-field-value">
                  {assignment.visit_frequency_days != null ? `Every ${assignment.visit_frequency_days} days` : "—"}
                </div>
              </div>
              <div>
                <div className="detail-field-label">Last Visit</div>
                <div className="detail-field-value">{formatDate(assignment.last_visit_date)}</div>
              </div>
              <div>
                <div className="detail-field-label">Next Visit</div>
                <div className="detail-field-value">{formatDate(assignment.next_visit_date)}</div>
              </div>
            </div>

            <div className="detail-field-label" style={{ marginBottom: ".5rem" }}>Profile</div>
            <ProfileFields
              programFacilityId={assignment.program_facility_id}
              profile={assignment.profile}
              onSaved={onProfileSaved}
            />

            <div className="detail-field-label" style={{ marginTop: "1.25rem", marginBottom: ".5rem" }}>Activities</div>
            {assignment.activities.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: "1.25rem", listStyle: "none" }}>
                {assignment.activities.map((activity) => (
                  <li key={activity.program_facility_type_activity_id} style={{ marginBottom: ".5rem" }}>
                    <div>
                      {activity.description}
                      {activity.specialtracking ? ` — ${activity.specialtracking}` : ""}
                    </div>
                    {activity.workflows.length > 0 && (
                      <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap", marginTop: ".25rem" }}>
                        {activity.workflows.map((workflow) => (
                          <button
                            key={workflow.workflow_id}
                            type="button"
                            className="btn btn-secondary btn-sm"
                            disabled={startingWorkflowId !== null}
                            onClick={() =>
                              onStartWorkflow(activity.program_facility_type_activity_id, workflow.workflow_id)
                            }
                          >
                            {startingWorkflowId === workflow.workflow_id ? "Starting…" : `Start ${workflow.name}`}
                          </button>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="detail-field-value">—</div>
            )}
          </div>

          <div className="table-wrap">
            {assignment.instances.length > 0 ? (
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
                  {assignment.instances.map((instance) => (
                    <tr key={instance.instance_id}>
                      <td>{instance.reference_no}</td>
                      <td>{instance.workflow_name}</td>
                      <td><StatusBadge status={instance.status} /></td>
                      <td>{instance.current_step_name ?? "—"}</td>
                      <td>{instance.initiated_by_name}</td>
                      <td>{formatDate(instance.started_at)}</td>
                      <td>{formatDate(instance.due_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p>No workflow requests for this assignment.</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function FacilityDirectoryDetailPage() {
  const { facilityId } = useParams<{ facilityId: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<FacilityDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [startingWorkflowId, setStartingWorkflowId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadData = useCallback(() => {
    if (!facilityId) return;
    let cancelled = false;
    setIsLoading(true);

    fetchFacilityDetail(facilityId)
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load this facility.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [facilityId]);

  useEffect(() => {
    return loadData();
  }, [loadData]);

  function handleProfileSaved(programFacilityId: string, profile: string) {
    setData((current) => {
      if (!current) return current;
      return {
        ...current,
        assignments: current.assignments.map((a) =>
          a.program_facility_id === programFacilityId ? { ...a, profile } : a
        ),
      };
    });
  }

  async function handleStartWorkflow(activityId: string, workflowId: string) {
    if (!facilityId) return;
    setActionError(null);
    setStartingWorkflowId(workflowId);
    try {
      await startFacilityActivityWorkflow(facilityId, activityId, workflowId);
      loadData();
    } catch {
      setActionError("Unable to start the workflow. Please try again.");
    } finally {
      setStartingWorkflowId(null);
    }
  }

  if (isLoading) {
    return (
      <AppLayout title="Facility" breadcrumb={["Facilities"]}>
        <div className="empty-state">Loading…</div>
      </AppLayout>
    );
  }

  if (error || !data) {
    return (
      <AppLayout title="Facility" breadcrumb={["Facilities"]}>
        <div className="alert alert-error">{error ?? "Facility not found."}</div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/facilities")}>
          Back to Facilities
        </button>
      </AppLayout>
    );
  }

  return (
    <AppLayout title={data.facility_name ?? "Facility"} breadcrumb={["Facilities"]}>
      <button type="button" className="btn btn-secondary btn-sm" style={{ marginBottom: "1rem" }} onClick={() => navigate("/facilities")}>
        Back to Facilities
      </button>

      {actionError && <div className="alert alert-error" style={{ marginBottom: "1rem" }}>{actionError}</div>}

      <FacilityLocationCard location={data.location} />

      {data.assignments.map((assignment) => (
        <AssignmentCard
          key={assignment.program_facility_id}
          assignment={assignment}
          startingWorkflowId={startingWorkflowId}
          onProfileSaved={(profile) => handleProfileSaved(assignment.program_facility_id, profile)}
          onStartWorkflow={handleStartWorkflow}
        />
      ))}
    </AppLayout>
  );
}
