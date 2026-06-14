import { api } from "./api";
import type { ComplianceSummary, ComplianceViolation, Paginated, ViolationSeverityLevel } from "../types";

export async function fetchComplianceSummary(): Promise<ComplianceSummary> {
  const { data } = await api.get<ComplianceSummary>("/api/compliance/summary/");
  return data;
}

export async function fetchSeverityLevels(): Promise<ViolationSeverityLevel[]> {
  const { data } = await api.get<Paginated<ViolationSeverityLevel> | ViolationSeverityLevel[]>("/api/compliance/severity-levels/");
  return Array.isArray(data) ? data : data.results;
}

export interface CreateViolationPayload {
  checklist_item_compliance_rule_id: string;
  violation_severity_level_id: string;
  violation_date: string;
  violation_description?: string;
  checklist_response_id: string;
}

export async function createViolation(payload: CreateViolationPayload): Promise<ComplianceViolation> {
  const { data } = await api.post<ComplianceViolation>("/api/compliance/violations/", payload);
  return data;
}

export async function deleteViolation(violationId: string): Promise<void> {
  await api.delete(`/api/compliance/violations/${violationId}/`);
}

export interface ViolationListParams {
  page?: number;
  pageSize?: number;
}

export async function fetchViolations(params: ViolationListParams = {}): Promise<Paginated<ComplianceViolation>> {
  const { data } = await api.get<Paginated<ComplianceViolation>>("/api/compliance/violations/", {
    params: {
      page: params.page,
      page_size: params.pageSize ?? 20,
    },
  });
  return data;
}
