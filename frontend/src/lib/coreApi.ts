import { api } from "./api";
import type {
  AddressValidationResult,
  FacilityCreatePayload,
  FacilityCreateResult,
  FacilityDetail,
  FacilityFilterOptions,
  FacilityListItem,
  InspectorFacilityDetail,
  InspectorLanding,
  InspectorProgram,
  ProgramDistrictOption,
  ProgramFacilityTypeOption,
  RiskAssessmentLevelOption,
  SupervisorLanding,
  WorkflowInstanceSummary,
} from "../types";

export async function fetchInspectorLanding(): Promise<InspectorLanding> {
  const { data } = await api.get<InspectorLanding>("/api/core/inspector/landing/");
  return data;
}

export async function fetchSupervisorLanding(): Promise<SupervisorLanding> {
  const { data } = await api.get<SupervisorLanding>("/api/core/supervisor/landing/");
  return data;
}

export async function assignDirectReportProgram(userId: number, programId: string): Promise<InspectorProgram[]> {
  const { data } = await api.post<InspectorProgram[]>(
    `/api/core/supervisor/direct-reports/${userId}/programs/`,
    { program_id: programId }
  );
  return data;
}

export async function unassignDirectReportProgram(userId: number, programId: string): Promise<InspectorProgram[]> {
  const { data } = await api.delete<InspectorProgram[]>(
    `/api/core/supervisor/direct-reports/${userId}/programs/`,
    { data: { program_id: programId } }
  );
  return data;
}

export async function fetchInspectorFacilityDetail(facilityId: string): Promise<InspectorFacilityDetail> {
  const { data } = await api.get<InspectorFacilityDetail>(`/api/core/inspector/facilities/${facilityId}/`);
  return data;
}

export async function startActivityWorkflow(
  facilityId: string,
  activityId: string,
  workflowId: string
): Promise<WorkflowInstanceSummary> {
  const { data } = await api.post<WorkflowInstanceSummary>(
    `/api/core/inspector/facilities/${facilityId}/activities/${activityId}/start/`,
    { workflow_id: workflowId }
  );
  return data;
}

export async function updateProgramFacilityProfile(
  programFacilityId: string,
  profile: Record<string, unknown>
): Promise<{ profile: string }> {
  const { data } = await api.patch<{ profile: string }>(
    `/api/core/inspector/program-facilities/${programFacilityId}/profile/`,
    { profile }
  );
  return data;
}

export interface FacilitySearchParams {
  search?: string;
  program?: string;
  facility_type?: string;
}

export async function fetchFacilities(params: FacilitySearchParams = {}): Promise<FacilityListItem[]> {
  const { data } = await api.get<FacilityListItem[]>("/api/core/facilities/", { params });
  return data;
}

export async function fetchFacilityFilterOptions(): Promise<FacilityFilterOptions> {
  const { data } = await api.get<FacilityFilterOptions>("/api/core/facilities/filters/");
  return data;
}

export async function fetchFacilityDetail(facilityId: string): Promise<FacilityDetail> {
  const { data } = await api.get<FacilityDetail>(`/api/core/facilities/${facilityId}/`);
  return data;
}

export async function updateFacilityProgramFacilityProfile(
  programFacilityId: string,
  profile: Record<string, unknown>
): Promise<{ profile: string }> {
  const { data } = await api.patch<{ profile: string }>(
    `/api/core/facilities/program-facilities/${programFacilityId}/profile/`,
    { profile }
  );
  return data;
}

export async function validateAddress(payload: {
  address_line1: string;
  city?: string;
  state?: string;
  postal_code?: string;
}): Promise<AddressValidationResult> {
  const { data } = await api.post<AddressValidationResult>("/api/core/facilities/validate-address/", payload);
  return data;
}

export async function fetchProgramFacilityTypes(programId?: string): Promise<ProgramFacilityTypeOption[]> {
  const { data } = await api.get<ProgramFacilityTypeOption[]>("/api/core/facilities/program-facility-types/", {
    params: programId ? { program: programId } : {},
  });
  return data;
}

export async function fetchProgramDistricts(programId?: string): Promise<ProgramDistrictOption[]> {
  const { data } = await api.get<ProgramDistrictOption[]>("/api/core/facilities/program-districts/", {
    params: programId ? { program: programId } : {},
  });
  return data;
}

export async function fetchRiskAssessmentLevels(programFacilityTypeId?: string): Promise<RiskAssessmentLevelOption[]> {
  const { data } = await api.get<RiskAssessmentLevelOption[]>("/api/core/facilities/risk-assessment-levels/", {
    params: programFacilityTypeId ? { program_facility_type_id: programFacilityTypeId } : {},
  });
  return data;
}

export async function fetchNextTrackingId(programFacilityTypeId: string): Promise<string> {
  const { data } = await api.get<{ tracking_id: string }>("/api/core/facilities/next-tracking-id/", {
    params: { program_facility_type_id: programFacilityTypeId },
  });
  return data.tracking_id;
}

export async function createFacility(payload: FacilityCreatePayload): Promise<FacilityCreateResult> {
  const { data } = await api.post<FacilityCreateResult>("/api/core/facilities/create/", payload);
  return data;
}

export async function startFacilityActivityWorkflow(
  facilityId: string,
  activityId: string,
  workflowId: string
): Promise<WorkflowInstanceSummary> {
  const { data } = await api.post<WorkflowInstanceSummary>(
    `/api/core/facilities/${facilityId}/activities/${activityId}/start/`,
    { workflow_id: workflowId }
  );
  return data;
}
