import { api } from "./api";
import type {
  ChecklistProgress,
  ChecklistResponseItem,
  ChecklistRunDetail,
  ChecklistRunListItem,
  Paginated,
} from "../types";

export interface ChecklistRunListParams {
  page?: number;
  pageSize?: number;
  status?: string;
}

export async function fetchChecklistRuns(params: ChecklistRunListParams = {}): Promise<Paginated<ChecklistRunListItem>> {
  const { data } = await api.get<Paginated<ChecklistRunListItem>>("/api/checklists/runs/", {
    params: {
      page: params.page,
      page_size: params.pageSize ?? 20,
      status: params.status || undefined,
    },
  });
  return data;
}

export async function fetchChecklistRun(id: string): Promise<ChecklistRunDetail> {
  const { data } = await api.get<ChecklistRunDetail>(`/api/checklists/runs/${id}/`);
  return data;
}

export async function fetchChecklistProgress(id: string): Promise<ChecklistProgress> {
  const { data } = await api.get<ChecklistProgress>(`/api/checklists/runs/${id}/progress/`);
  return data;
}

export interface ChecklistAnswer {
  item: string;
  response_value?: string;
  notes?: string;
  box_folder_url?: string;
}

export async function submitChecklistResponses(id: string, answers: ChecklistAnswer[]): Promise<ChecklistRunDetail> {
  const { data } = await api.post<ChecklistRunDetail>(`/api/checklists/runs/${id}/respond/`, answers);
  return data;
}

export async function skipChecklistRun(id: string): Promise<ChecklistRunDetail> {
  const { data } = await api.post<ChecklistRunDetail>(`/api/checklists/runs/${id}/skip/`);
  return data;
}

export async function createBoxFolder(runId: string, itemId: string): Promise<ChecklistResponseItem> {
  const { data } = await api.post<ChecklistResponseItem>(
    `/api/checklists/runs/${runId}/items/${itemId}/box-folder/`
  );
  return data;
}
