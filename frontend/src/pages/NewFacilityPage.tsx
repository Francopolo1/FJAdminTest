import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import {
  createFacility,
  fetchActivityFlags,
  fetchFacilityFilterOptions,
  fetchNextTrackingId,
  fetchProgramDistricts,
  fetchProgramFacilityTypes,
  fetchRiskAssessmentLevels,
} from "../lib/coreApi";
import type {
  ActivityFlagOption,
  AddressValidationResult,
  FacilityFilterOptions,
  ProgramDistrictOption,
  ProgramFacilityTypeOption,
  RiskAssessmentLevelOption,
} from "../types";

const US_STATES = [
  ["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],["CA","California"],
  ["CO","Colorado"],["CT","Connecticut"],["DE","Delaware"],["FL","Florida"],["GA","Georgia"],
  ["HI","Hawaii"],["ID","Idaho"],["IL","Illinois"],["IN","Indiana"],["IA","Iowa"],
  ["KS","Kansas"],["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],
  ["MA","Massachusetts"],["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],["MO","Missouri"],
  ["MT","Montana"],["NE","Nebraska"],["NV","Nevada"],["NH","New Hampshire"],["NJ","New Jersey"],
  ["NM","New Mexico"],["NY","New York"],["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],
  ["OK","Oklahoma"],["OR","Oregon"],["PA","Pennsylvania"],["RI","Rhode Island"],["SC","South Carolina"],
  ["SD","South Dakota"],["TN","Tennessee"],["TX","Texas"],["UT","Utah"],["VT","Vermont"],
  ["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],["WI","Wisconsin"],["WY","Wyoming"],
];

const STEPS = ["Facility Info", "Program Assignment", "Program Facility Details"];

// ── Step 1 state ──────────────────────────────────────────────────────────────
interface Step1 {
  facility_name: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
}

// ── Step 2 state ──────────────────────────────────────────────────────────────
interface Step2 {
  program_id: string;
  program_facility_type_id: string;
  program_district_id: string;
}

// ── Step 3 state ──────────────────────────────────────────────────────────────
interface Step3 {
  license_number: string;
  license_expire_date: string;
  facility_phone: string;
  tracking_id: string;
  risk_assessment_levels_id: number | "";
  start_date: string;
  activity_flag: string;
  comments: string;
}

export function NewFacilityPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  // ── Step 1 ──────────────────────────────────────────────────────────────────
  const [s1, setS1] = useState<Step1>({
    facility_name: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    postal_code: "",
  });
  const [validating, setValidating] = useState(false);
  const [validated, setValidated] = useState<AddressValidationResult | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [s1Errors, setS1Errors] = useState<Partial<Record<keyof Step1, string>>>({});

  // ── Step 2 ──────────────────────────────────────────────────────────────────
  const [filterOptions, setFilterOptions] = useState<FacilityFilterOptions>({ programs: [], facility_types: [] });
  const [pfts, setPfts] = useState<ProgramFacilityTypeOption[]>([]);
  const [districts, setDistricts] = useState<ProgramDistrictOption[]>([]);
  const [s2, setS2] = useState<Step2>({
    program_id: "",
    program_facility_type_id: "",
    program_district_id: "",
  });
  const [s2Errors, setS2Errors] = useState<Partial<Record<keyof Step2, string>>>({});

  // ── Activity flags (global lookup, loaded once) ──────────────────────────────
  const [activityFlags, setActivityFlags] = useState<ActivityFlagOption[]>([]);
  useEffect(() => { fetchActivityFlags().then(setActivityFlags).catch(() => undefined); }, []);

  // ── Risk assessment levels (loaded when PFT is chosen) ──────────────────────
  const [riskLevels, setRiskLevels] = useState<RiskAssessmentLevelOption[]>([]);

  // ── Step 3 ──────────────────────────────────────────────────────────────────
  const [s3, setS3] = useState<Step3>({
    license_number: "",
    license_expire_date: "",
    facility_phone: "",
    tracking_id: "",
    risk_assessment_levels_id: "",
    start_date: "",
    activity_flag: "A",
    comments: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // ── Initialise filter options ────────────────────────────────────────────────
  useEffect(() => {
    fetchFacilityFilterOptions().then(setFilterOptions).catch(() => undefined);
  }, []);

  // ── Load PFTs and districts when program changes ────────────────────────────
  useEffect(() => {
    if (!s2.program_id) {
      setPfts([]);
      setDistricts([]);
      setS2((prev) => ({ ...prev, program_facility_type_id: "", program_district_id: "" }));
      return;
    }
    fetchProgramFacilityTypes(s2.program_id).then(setPfts).catch(() => undefined);
    fetchProgramDistricts(s2.program_id).then(setDistricts).catch(() => undefined);
    setS2((prev) => ({ ...prev, program_facility_type_id: "", program_district_id: "" }));
    setRiskLevels([]);
  }, [s2.program_id]);

  useEffect(() => {
    if (!s2.program_facility_type_id) { setRiskLevels([]); return; }
    fetchRiskAssessmentLevels(s2.program_facility_type_id).then(setRiskLevels).catch(() => undefined);
  }, [s2.program_facility_type_id]);

  // ── Helpers ──────────────────────────────────────────────────────────────────
  const updateS1 = (field: keyof Step1) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setS1((prev) => ({ ...prev, [field]: e.target.value }));
    setValidated(null);
    setValidationError(null);
    setS1Errors((prev) => ({ ...prev, [field]: undefined }));
  };

  const updateS2 = (field: keyof Step2) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setS2((prev) => ({ ...prev, [field]: e.target.value }));
    setS2Errors((prev) => ({ ...prev, [field]: undefined }));
  };

  const updateS3 = (field: keyof Step3) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setS3((prev) => ({ ...prev, [field]: e.target.value }));
  };

  // ── Address validation (calls Nominatim directly from the browser) ───────────
  const handleValidateAddress = async () => {
    setValidationError(null);
    setValidated(null);
    setValidating(true);
    try {
      const query = [s1.address_line1, s1.city, s1.state, s1.postal_code]
        .filter(Boolean)
        .join(", ");
      const params = new URLSearchParams({
        q: query,
        format: "json",
        addressdetails: "1",
        limit: "1",
        countrycodes: "us",
      });
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/search?${params}`,
        { headers: { "Accept-Language": "en" } }
      );
      if (!resp.ok) throw new Error("Nominatim returned an error.");
      const results = await resp.json() as Array<{
        lat: string; lon: string; display_name: string;
        address: Record<string, string>;
      }>;

      if (!results.length) {
        setValidationError("Address not found. Please verify the details and try again.");
        return;
      }

      const r    = results[0];
      const addr = r.address ?? {};
      const normalized: AddressValidationResult = {
        valid:           true,
        latitude:        parseFloat(r.lat),
        longitude:       parseFloat(r.lon),
        display_address: r.display_name,
        city:     addr.city ?? addr.town ?? addr.village ?? s1.city,
        state:    addr.state ?? s1.state,
        postal_code: addr.postcode ?? s1.postal_code,
        county:   addr.county ?? undefined,
      };
      setValidated(normalized);
      setS1((prev) => ({
        ...prev,
        city:        normalized.city        ?? prev.city,
        state:       normalized.state       ?? prev.state,
        postal_code: normalized.postal_code ?? prev.postal_code,
      }));
    } catch {
      setValidationError("Address validation is unavailable right now. You may continue without it.");
    } finally {
      setValidating(false);
    }
  };

  // ── Step validation ──────────────────────────────────────────────────────────
  const validateStep1 = (): boolean => {
    const errs: Partial<Record<keyof Step1, string>> = {};
    if (!s1.facility_name.trim()) errs.facility_name = "Required";
    if (!s1.address_line1.trim()) errs.address_line1 = "Required";
    if (!s1.city.trim())          errs.city          = "Required";
    if (!s1.state)                errs.state         = "Required";
    if (!s1.postal_code.trim())   errs.postal_code   = "Required";
    setS1Errors(errs);
    return Object.keys(errs).length === 0;
  };

  const validateStep2 = (): boolean => {
    const errs: Partial<Record<keyof Step2, string>> = {};
    if (!s2.program_id)                errs.program_id                = "Required";
    if (!s2.program_facility_type_id)  errs.program_facility_type_id  = "Required";
    if (!s2.program_district_id)       errs.program_district_id       = "Required";
    setS2Errors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleNext = async () => {
    if (step === 0 && !validateStep1()) return;
    if (step === 1) {
      if (!validateStep2()) return;
      // Pre-populate tracking ID with the server-generated default
      if (!s3.tracking_id && s2.program_facility_type_id) {
        try {
          const tid = await fetchNextTrackingId(s2.program_facility_type_id);
          setS3((prev) => ({ ...prev, tracking_id: tid }));
        } catch {
          // Non-fatal — user can fill it in manually
        }
      }
    }
    setStep((s) => s + 1);
  };

  // ── Submit ───────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);
    try {
      const result = await createFacility({
        facility_name:            s1.facility_name,
        address_line1:            s1.address_line1,
        address_line2:            s1.address_line2 || undefined,
        city:                     s1.city,
        state:                    s1.state,
        postal_code:              s1.postal_code,
        latitude:                 validated?.latitude,
        longitude:                validated?.longitude,
        county:                   validated?.county,
        program_facility_type_id: s2.program_facility_type_id,
        program_district_id:      s2.program_district_id,
        license_number:           s3.license_number || undefined,
        license_expire_date:      s3.license_expire_date || undefined,
        facility_phone:           s3.facility_phone || undefined,
        tracking_id:              s3.tracking_id || undefined,
        risk_assessment_levels_id: s3.risk_assessment_levels_id || undefined,
        start_date:               s3.start_date || undefined,
        activity_flag:            s3.activity_flag || undefined,
        comments:                 s3.comments || undefined,
      });
      navigate(`/facilities/${result.facility_id}`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: Record<string, string> } };
      const detail = e?.response?.data
        ? Object.values(e.response.data).flat().join(" ")
        : "Failed to create facility. Please try again.";
      setSubmitError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedPft = pfts.find((p) => p.program_facility_type_id === s2.program_facility_type_id);

  return (
    <AppLayout title="New Facility">
      {/* Stepper */}
      <div className="card" style={{ marginBottom: "var(--space-4)" }}>
        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
          {STEPS.map((label, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flex: i < STEPS.length - 1 ? 1 : undefined }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center",
                justifyContent: "center", fontWeight: 600, fontSize: 13, flexShrink: 0,
                background: i < step ? "var(--color-success)" : i === step ? "var(--color-primary)" : "var(--color-border)",
                color: i <= step ? "#fff" : "var(--color-muted)",
              }}>
                {i < step ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: 13, fontWeight: i === step ? 600 : 400, color: i === step ? "var(--color-text)" : "var(--color-muted)", whiteSpace: "nowrap" }}>
                {label}
              </span>
              {i < STEPS.length - 1 && (
                <div style={{ flex: 1, height: 1, background: "var(--color-border)", margin: "0 var(--space-2)" }} />
              )}
            </div>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* ── Step 1: Facility Info ─────────────────────────────────────────── */}
        {step === 0 && (
          <div className="card">
            <h2 style={{ marginBottom: "var(--space-4)" }}>Facility Information</h2>
            <div className="form-row" style={{ flexDirection: "column" }}>
              <div>
                <label className="field-label" htmlFor="facility_name">
                  Facility Name <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <input
                  id="facility_name"
                  className={`input${s1Errors.facility_name ? " input-error" : ""}`}
                  value={s1.facility_name}
                  onChange={updateS1("facility_name")}
                  placeholder="e.g. Sunshine Daycare Center"
                />
                {s1Errors.facility_name && <p className="field-error">{s1Errors.facility_name}</p>}
              </div>

              <div>
                <label className="field-label" htmlFor="address_line1">
                  Address Line 1 <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <input
                  id="address_line1"
                  className={`input${s1Errors.address_line1 ? " input-error" : ""}`}
                  value={s1.address_line1}
                  onChange={updateS1("address_line1")}
                  placeholder="123 Main St"
                />
                {s1Errors.address_line1 && <p className="field-error">{s1Errors.address_line1}</p>}
              </div>

              <div>
                <label className="field-label" htmlFor="address_line2">Address Line 2</label>
                <input
                  id="address_line2"
                  className="input"
                  value={s1.address_line2}
                  onChange={updateS1("address_line2")}
                  placeholder="Suite, Floor, Unit, etc. (optional)"
                />
              </div>

              <div className="form-row" style={{ gap: "var(--space-3)" }}>
                <div style={{ flex: 2 }}>
                  <label className="field-label" htmlFor="city">
                    City <span style={{ color: "var(--color-danger)" }}>*</span>
                  </label>
                  <input
                    id="city"
                    className={`input${s1Errors.city ? " input-error" : ""}`}
                    value={s1.city}
                    onChange={updateS1("city")}
                    placeholder="City"
                  />
                  {s1Errors.city && <p className="field-error">{s1Errors.city}</p>}
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="state">
                    State <span style={{ color: "var(--color-danger)" }}>*</span>
                  </label>
                  <select
                    id="state"
                    className={`select${s1Errors.state ? " input-error" : ""}`}
                    value={s1.state}
                    onChange={updateS1("state")}
                  >
                    <option value="">State</option>
                    {US_STATES.map(([code, name]) => (
                      <option key={code} value={code}>{code} – {name}</option>
                    ))}
                  </select>
                  {s1Errors.state && <p className="field-error">{s1Errors.state}</p>}
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="postal_code">
                    Zip Code <span style={{ color: "var(--color-danger)" }}>*</span>
                  </label>
                  <input
                    id="postal_code"
                    className={`input${s1Errors.postal_code ? " input-error" : ""}`}
                    value={s1.postal_code}
                    onChange={updateS1("postal_code")}
                    placeholder="12345"
                    maxLength={10}
                  />
                  {s1Errors.postal_code && <p className="field-error">{s1Errors.postal_code}</p>}
                </div>
              </div>

              {/* Address validation */}
              <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-start", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleValidateAddress}
                  disabled={validating || !s1.address_line1.trim()}
                  style={{ marginTop: "auto" }}
                >
                  {validating ? "Validating…" : "Validate Address"}
                </button>

                {validated && (
                  <div style={{
                    flex: 1,
                    padding: "var(--space-3)",
                    background: "var(--color-success-bg, #f0fdf4)",
                    border: "1px solid var(--color-success, #16a34a)",
                    borderRadius: "var(--radius)",
                    fontSize: 13,
                  }}>
                    <strong style={{ color: "var(--color-success, #16a34a)" }}>✓ Address validated</strong>
                    <p style={{ margin: "var(--space-1) 0 0", color: "var(--color-muted)" }}>
                      {validated.display_address}
                    </p>
                    {validated.latitude != null && (
                      <p style={{ margin: "2px 0 0", color: "var(--color-muted)", fontSize: 12 }}>
                        {validated.latitude.toFixed(5)}, {validated.longitude?.toFixed(5)} (geocoded)
                      </p>
                    )}
                  </div>
                )}

                {validationError && (
                  <div style={{
                    flex: 1,
                    padding: "var(--space-3)",
                    background: "var(--color-danger-bg, #fef2f2)",
                    border: "1px solid var(--color-danger, #dc2626)",
                    borderRadius: "var(--radius)",
                    fontSize: 13,
                    color: "var(--color-danger, #dc2626)",
                  }}>
                    {validationError}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Step 2: Program Assignment ─────────────────────────────────────── */}
        {step === 1 && (
          <div className="card">
            <h2 style={{ marginBottom: "var(--space-4)" }}>Program Assignment</h2>
            <div className="form-row" style={{ flexDirection: "column" }}>
              <div>
                <label className="field-label" htmlFor="program_id">
                  Program <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <select
                  id="program_id"
                  className={`select${s2Errors.program_id ? " input-error" : ""}`}
                  value={s2.program_id}
                  onChange={updateS2("program_id")}
                >
                  <option value="">Select a program…</option>
                  {filterOptions.programs.map((p) => (
                    <option key={p.program_id} value={p.program_id}>
                      {p.code} – {p.title}
                    </option>
                  ))}
                </select>
                {s2Errors.program_id && <p className="field-error">{s2Errors.program_id}</p>}
              </div>

              <div>
                <label className="field-label" htmlFor="program_facility_type_id">
                  Facility Type <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <select
                  id="program_facility_type_id"
                  className={`select${s2Errors.program_facility_type_id ? " input-error" : ""}`}
                  value={s2.program_facility_type_id}
                  onChange={updateS2("program_facility_type_id")}
                  disabled={!s2.program_id}
                >
                  <option value="">
                    {s2.program_id ? "Select facility type…" : "Select a program first"}
                  </option>
                  {pfts.map((pft) => (
                    <option key={pft.program_facility_type_id} value={pft.program_facility_type_id}>
                      {pft.facility_type_code}
                      {pft.facility_type_description ? ` – ${pft.facility_type_description}` : ""}
                      {pft.description ? ` (${pft.description})` : ""}
                    </option>
                  ))}
                </select>
                {s2Errors.program_facility_type_id && (
                  <p className="field-error">{s2Errors.program_facility_type_id}</p>
                )}
              </div>

              {selectedPft && (
                <div style={{
                  padding: "var(--space-3)",
                  background: "var(--color-surface-2, #f8f9fa)",
                  borderRadius: "var(--radius)",
                  fontSize: 13,
                  color: "var(--color-muted)",
                }}>
                  <strong>Program:</strong> {selectedPft.program_code} – {selectedPft.program_title}<br />
                  <strong>Facility Type:</strong> {selectedPft.facility_type_code}
                  {selectedPft.facility_type_description ? ` – ${selectedPft.facility_type_description}` : ""}
                </div>
              )}

              <div>
                <label className="field-label" htmlFor="program_district_id">
                  District <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <select
                  id="program_district_id"
                  className={`select${s2Errors.program_district_id ? " input-error" : ""}`}
                  value={s2.program_district_id}
                  onChange={updateS2("program_district_id")}
                  disabled={!s2.program_id}
                >
                  <option value="">
                    {s2.program_id ? "Select district…" : "Select a program first"}
                  </option>
                  {districts.map((d) => (
                    <option key={d.program_district_id} value={d.program_district_id}>
                      District {d.district}{d.description ? ` – ${d.description}` : ""}
                    </option>
                  ))}
                </select>
                {s2Errors.program_district_id && (
                  <p className="field-error">{s2Errors.program_district_id}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Step 3: Program Facility Details ──────────────────────────────── */}
        {step === 2 && (
          <div className="card">
            <h2 style={{ marginBottom: "var(--space-4)" }}>Program Facility Details</h2>
            <p style={{ color: "var(--color-muted)", fontSize: 13, marginBottom: "var(--space-4)" }}>
              All fields are optional. You can update them later from the facility detail page.
            </p>
            <div className="form-row" style={{ flexDirection: "column" }}>
              <div className="form-row" style={{ gap: "var(--space-3)" }}>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="license_number">License Number</label>
                  <input
                    id="license_number"
                    className="input"
                    value={s3.license_number}
                    onChange={updateS3("license_number")}
                    placeholder="e.g. LIC-00123"
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="license_expire_date">License Expire Date</label>
                  <input
                    id="license_expire_date"
                    type="date"
                    className="input"
                    value={s3.license_expire_date}
                    onChange={updateS3("license_expire_date")}
                  />
                </div>
              </div>

              <div className="form-row" style={{ gap: "var(--space-3)" }}>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="facility_phone">Phone</label>
                  <input
                    id="facility_phone"
                    className="input"
                    value={s3.facility_phone}
                    onChange={updateS3("facility_phone")}
                    placeholder="(555) 555-5555"
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="tracking_id">Tracking ID</label>
                  <input
                    id="tracking_id"
                    className="input"
                    value={s3.tracking_id}
                    onChange={updateS3("tracking_id")}
                    placeholder="e.g. TRK-9999"
                  />
                </div>
              </div>

              <div className="form-row" style={{ gap: "var(--space-3)" }}>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="risk_assessment_levels_id">Risk Assessment</label>
                  <select
                    id="risk_assessment_levels_id"
                    className="select"
                    value={s3.risk_assessment_levels_id}
                    onChange={(e) =>
                      setS3((prev) => ({
                        ...prev,
                        risk_assessment_levels_id: e.target.value ? Number(e.target.value) : "",
                      }))
                    }
                    disabled={riskLevels.length === 0}
                  >
                    <option value="">— None —</option>
                    {riskLevels.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label} ({r.visit_frequency_days}d)
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="start_date">Start Date</label>
                  <input
                    id="start_date"
                    type="date"
                    className="input"
                    value={s3.start_date}
                    onChange={updateS3("start_date")}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="field-label" htmlFor="activity_flag">Status</label>
                  <select
                    id="activity_flag"
                    className="select"
                    value={s3.activity_flag}
                    onChange={updateS3("activity_flag")}
                  >
                    {activityFlags.length > 0
                      ? activityFlags.map((f) => (
                          <option key={f.code} value={f.code}>{f.label}</option>
                        ))
                      : <>
                          <option value="A">Active</option>
                          <option value="I">Inactive</option>
                          <option value="C">Closed</option>
                        </>
                    }
                  </select>
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="comments">Comments</label>
                <textarea
                  id="comments"
                  className="input"
                  rows={3}
                  style={{ resize: "vertical" }}
                  value={s3.comments}
                  onChange={updateS3("comments")}
                  placeholder="Any additional notes…"
                />
              </div>
            </div>

            {/* Summary card */}
            <div style={{
              marginTop: "var(--space-4)",
              padding: "var(--space-4)",
              background: "var(--color-surface-2, #f8f9fa)",
              borderRadius: "var(--radius)",
              fontSize: 13,
            }}>
              <strong>Review</strong>
              <div style={{ marginTop: "var(--space-2)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-1) var(--space-4)" }}>
                <span style={{ color: "var(--color-muted)" }}>Facility:</span>
                <span>{s1.facility_name}</span>
                <span style={{ color: "var(--color-muted)" }}>Address:</span>
                <span>
                  {s1.address_line1}{s1.address_line2 ? `, ${s1.address_line2}` : ""}, {s1.city}, {s1.state} {s1.postal_code}
                  {validated && <span style={{ color: "var(--color-success, #16a34a)", marginLeft: 6 }}>✓ geocoded</span>}
                </span>
                <span style={{ color: "var(--color-muted)" }}>Program:</span>
                <span>{filterOptions.programs.find((p) => p.program_id === s2.program_id)?.title ?? "—"}</span>
                <span style={{ color: "var(--color-muted)" }}>Facility Type:</span>
                <span>
                  {selectedPft
                    ? `${selectedPft.facility_type_code}${selectedPft.facility_type_description ? ` – ${selectedPft.facility_type_description}` : ""}`
                    : "—"}
                </span>
                <span style={{ color: "var(--color-muted)" }}>District:</span>
                <span>
                  {(() => {
                    const d = districts.find((x) => x.program_district_id === s2.program_district_id);
                    return d ? `District ${d.district}${d.description ? ` – ${d.description}` : ""}` : "—";
                  })()}
                </span>
              </div>
            </div>

            {submitError && (
              <div className="alert alert-error" style={{ marginTop: "var(--space-3)" }}>
                {submitError}
              </div>
            )}
          </div>
        )}

        {/* ── Navigation buttons ────────────────────────────────────────────── */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "var(--space-4)",
          gap: "var(--space-2)",
        }}>
          <div>
            {step > 0 && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setStep((s) => s - 1)}
                disabled={submitting}
              >
                ← Back
              </button>
            )}
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate("/facilities")}
              disabled={submitting}
            >
              Cancel
            </button>
            {step < STEPS.length - 1 ? (
              <button type="button" className="btn btn-primary" onClick={handleNext}>
                Next →
              </button>
            ) : (
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Creating…" : "Create Facility"}
              </button>
            )}
          </div>
        </div>
      </form>
    </AppLayout>
  );
}
