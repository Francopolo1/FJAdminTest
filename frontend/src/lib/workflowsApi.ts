import { api } from "./api";
import type {
  AuditLogEntry,
  AvailableTransition,
  Paginated,
  WorkflowInstance,
  WorkflowInstanceDetail,
  WorkflowTask,
} from "../types";

export async function fetchInstanceCount(status?: string): Promise<number> {
  const { data } = await api.get<Paginated<WorkflowInstance>>("/api/workflows/instances/", {
    params: { page_size: 1, ...(status ? { status } : {}) },
  });
  return data.count;
}

export async function fetchOverdueTaskCount(): Promise<number> {
  const { data } = await api.get<Paginated<unknown>>("/api/workflows/tasks/", {
    params: { page_size: 1, overdue_only: true },
  });
  return data.count;
}

export async function fetchTaskCount(): Promise<number> {
  const { data } = await api.get<Paginated<unknown>>("/api/workflows/tasks/", {
    params: { page_size: 1 },
  });
  return data.count;
}

export async function fetchRecentInstances(limit = 5): Promise<WorkflowInstance[]> {
  const { data } = await api.get<Paginated<WorkflowInstance>>("/api/workflows/instances/", {
    params: { page_size: limit, ordering: "-started_at" },
  });
  return data.results;
}

export interface InstanceListParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
  ordering?: string;
}

export async function fetchInstances(params: InstanceListParams = {}): Promise<Paginated<WorkflowInstance>> {
  const { data } = await api.get<Paginated<WorkflowInstance>>("/api/workflows/instances/", {
    params: {
      page: params.page,
      page_size: params.pageSize ?? 20,
      status: params.status || undefined,
      search: params.search || undefined,
      ordering: params.ordering,
    },
  });
  return data;
}

export async function fetchInstance(id: string): Promise<WorkflowInstanceDetail> {
  const { data } = await api.get<WorkflowInstanceDetail>(`/api/workflows/instances/${id}/`);
  return data;
}

export async function fetchInstanceAuditLog(id: string): Promise<AuditLogEntry[]> {
  const { data } = await api.get<AuditLogEntry[]>(`/api/workflows/instances/${id}/audit-log/`);
  return data;
}

export async function fetchAvailableTransitions(id: string): Promise<AvailableTransition[]> {
  const { data } = await api.get<AvailableTransition[]>(`/api/workflows/instances/${id}/available-transitions/`);
  return data;
}

export async function advanceInstance(
  id: string,
  triggerEvent: string,
  comments?: string,
): Promise<WorkflowInstanceDetail> {
  const { data } = await api.post<WorkflowInstanceDetail>(`/api/workflows/instances/${id}/advance/`, {
    trigger_event: triggerEvent,
    comments,
  });
  return data;
}

export async function cancelInstance(id: string, notes?: string): Promise<WorkflowInstanceDetail> {
  const { data } = await api.post<WorkflowInstanceDetail>(`/api/workflows/instances/${id}/cancel/`, { notes });
  return data;
}

export interface TaskListParams {
  page?: number;
  pageSize?: number;
  status?: string;
  overdueOnly?: boolean;
  ordering?: string;
}

export async function fetchTasks(params: TaskListParams = {}): Promise<Paginated<WorkflowTask>> {
  const { data } = await api.get<Paginated<WorkflowTask>>("/api/workflows/tasks/", {
    params: {
      page: params.page,
      page_size: params.pageSize ?? 20,
      status: params.status || undefined,
      overdue_only: params.overdueOnly || undefined,
      ordering: params.ordering,
    },
  });
  return data;
}
