import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { fetchFacilities, fetchFacilityFilterOptions } from "../lib/coreApi";
import type { FacilityFilterOptions, FacilityListItem } from "../types";

type SortColumn = "facility_name" | "program_code" | "facility_type";
type SortDirection = "asc" | "desc";

const SORT_COLUMNS: { key: SortColumn; label: string }[] = [
  { key: "facility_name", label: "Facility" },
  { key: "program_code", label: "Program" },
  { key: "facility_type", label: "Facility Type" },
];

export function FacilitiesPage() {
  const navigate = useNavigate();

  const [filterOptions, setFilterOptions] = useState<FacilityFilterOptions>({ programs: [], facility_types: [] });
  const [results, setResults] = useState<FacilityListItem[]>([]);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [program, setProgram] = useState("");
  const [facilityType, setFacilityType] = useState("");

  const [sortColumn, setSortColumn] = useState<SortColumn>("facility_name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFacilityFilterOptions()
      .then(setFilterOptions)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchFacilities({ search, program, facility_type: facilityType })
      .then((data) => {
        if (cancelled) return;
        setResults(data);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load facilities.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [search, program, facilityType]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
  };

  const handleSort = (column: SortColumn) => {
    if (column === sortColumn) {
      setSortDirection((dir) => (dir === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const sortedResults = [...results].sort((a, b) => {
    const aValue = (a[sortColumn] ?? "").toString().toLowerCase();
    const bValue = (b[sortColumn] ?? "").toString().toLowerCase();
    const cmp = aValue.localeCompare(bValue);
    return sortDirection === "asc" ? cmp : -cmp;
  });

  return (
    <AppLayout title="Facilities">
      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "var(--space-3)" }}>
        <button className="btn btn-primary" onClick={() => navigate("/facilities/new")}>
          + New Facility
        </button>
      </div>

      <div className="card">
        <form className="form-row" onSubmit={handleSearchSubmit}>
          <div>
            <label className="field-label" htmlFor="search">Search</label>
            <input
              id="search"
              className="input"
              placeholder="Facility name or license number"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <div>
            <label className="field-label" htmlFor="program">Program</label>
            <select
              id="program"
              className="select"
              value={program}
              onChange={(e) => setProgram(e.target.value)}
            >
              <option value="">All Programs</option>
              {filterOptions.programs.map((p) => (
                <option key={p.program_id} value={p.program_id}>{p.title}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="facility_type">Facility Type</label>
            <select
              id="facility_type"
              className="select"
              value={facilityType}
              onChange={(e) => setFacilityType(e.target.value)}
            >
              <option value="">All Facility Types</option>
              {filterOptions.facility_types.map((ft) => (
                <option key={ft.facility_type_id} value={ft.facility_type_id}>
                  {ft.description ?? ft.code}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary" style={{ alignSelf: "flex-end" }}>
            Search
          </button>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {SORT_COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    style={{ cursor: "pointer", userSelect: "none" }}
                  >
                    {col.label}
                    {sortColumn === col.key && (sortDirection === "asc" ? " ▲" : " ▼")}
                  </th>
                ))}
                <th>District</th>
                <th>City</th>
                <th>State</th>
                <th>License #</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state"><p>Loading…</p></div>
                  </td>
                </tr>
              ) : sortedResults.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state"><p>No facilities found.</p></div>
                  </td>
                </tr>
              ) : (
                sortedResults.map((item) => (
                  <tr
                    key={item.program_facility_id}
                    style={{ cursor: "pointer" }}
                    onClick={() => navigate(`/facilities/${item.facility_id}`)}
                  >
                    <td>{item.facility_name ?? "—"}</td>
                    <td>{item.program_code}</td>
                    <td>{item.facility_type ?? "—"}</td>
                    <td>{item.district ?? "—"}</td>
                    <td>{item.city ?? "—"}</td>
                    <td>{item.state ?? "—"}</td>
                    <td>{item.license_number ?? "—"}</td>
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
