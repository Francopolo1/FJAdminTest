import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { fetchInspectorLanding } from "../lib/coreApi";
import type { InspectorLanding } from "../types";

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

export function InspectorLandingPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<InspectorLanding | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [programFilter, setProgramFilter] = useState("");
  const [districtFilter, setDistrictFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchInspectorLanding()
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load your assignments.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const facilities = data?.program_facilities ?? [];

  const facilityTypes = useMemo(
    () => Array.from(new Set(facilities.map((f) => f.facility_type).filter((v): v is string => !!v))).sort(),
    [facilities]
  );
  const programCodes = useMemo(
    () => Array.from(new Set(facilities.map((f) => f.program_code).filter(Boolean))).sort(),
    [facilities]
  );
  const districts = useMemo(
    () => Array.from(new Set(facilities.map((f) => f.district).filter((v): v is number => v != null))).sort((a, b) => a - b),
    [facilities]
  );

  const filteredFacilities = useMemo(() => {
    const term = search.trim().toLowerCase();
    return facilities.filter((f) => {
      if (term && !(f.facility_name ?? "").toLowerCase().includes(term)) return false;
      if (typeFilter && f.facility_type !== typeFilter) return false;
      if (programFilter && f.program_code !== programFilter) return false;
      if (districtFilter && String(f.district) !== districtFilter) return false;
      return true;
    });
  }, [facilities, search, typeFilter, programFilter, districtFilter]);

  return (
    <AppLayout title="My Assignments" breadcrumb={["Inspector"]}>
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading ? (
        <div className="empty-state">Loading…</div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: "1.25rem" }}>
            <div className="card-header">
              <span className="card-title">Assigned Programs</span>
            </div>
            {data && data.programs.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Title</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.programs.map((program) => (
                      <tr key={program.program_id}>
                        <td>{program.code}</td>
                        <td>{program.title}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No programs assigned.</p>
              </div>
            )}
          </div>

          <div className="card" style={{ marginBottom: "1.25rem" }}>
            <div className="card-header">
              <span className="card-title">Assigned Program Districts</span>
            </div>
            {data && data.program_districts.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Program</th>
                      <th>District</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.program_districts.map((district) => (
                      <tr key={district.program_district_id}>
                        <td>{district.program_code}</td>
                        <td>{district.district ?? "—"}</td>
                        <td>{district.description ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No program districts assigned.</p>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Facilities in Your Districts</span>
            </div>
            <div className="card-body" style={{ paddingBottom: 0 }}>
              <div className="form-row">
                <input
                  type="text"
                  className="input"
                  placeholder="Search by facility name…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select className="select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  <option value="">All types</option>
                  {facilityTypes.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <select className="select" value={programFilter} onChange={(e) => setProgramFilter(e.target.value)}>
                  <option value="">All programs</option>
                  {programCodes.map((code) => (
                    <option key={code} value={code}>{code}</option>
                  ))}
                </select>
                <select className="select" value={districtFilter} onChange={(e) => setDistrictFilter(e.target.value)}>
                  <option value="">All districts</option>
                  {districts.map((district) => (
                    <option key={district} value={district}>District {district}</option>
                  ))}
                </select>
              </div>
            </div>
            {filteredFacilities.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Facility</th>
                      <th>Type</th>
                      <th>Program</th>
                      <th>District</th>
                      <th>License #</th>
                      <th>Risk</th>
                      <th>Last Visit</th>
                      <th>Next Visit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFacilities.map((facility) => (
                      <tr
                        key={facility.program_facility_id}
                        onClick={() => navigate(`/my-assignments/facilities/${facility.facility_id}`)}
                        style={{ cursor: "pointer" }}
                      >
                        <td>{facility.facility_name ?? "—"}</td>
                        <td>{facility.facility_type ?? "—"}</td>
                        <td>{facility.program_code}</td>
                        <td>{facility.district ?? "—"}</td>
                        <td>{facility.license_number ?? "—"}</td>
                        <td>
                          {facility.risk_assessment ? (
                            <span className={`badge ${RISK_BADGE[facility.risk_assessment] ?? "badge-gray"}`}>
                              {facility.risk_assessment}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td>{formatDate(facility.last_visit_date)}</td>
                        <td>{formatDate(facility.next_visit_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>
                  {facilities.length === 0
                    ? "No facilities found for your assigned districts."
                    : "No facilities match the current filters."}
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </AppLayout>
  );
}
