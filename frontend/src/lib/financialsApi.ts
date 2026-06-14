import { api } from "./api";
import type { FinancialsSummary, Paginated, Transaction } from "../types";

export async function fetchFinancialsSummary(): Promise<FinancialsSummary> {
  const { data } = await api.get<FinancialsSummary>("/api/financials/summary/");
  return data;
}

export interface TransactionListParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

export async function fetchTransactions(params: TransactionListParams = {}): Promise<Paginated<Transaction>> {
  const { data } = await api.get<Paginated<Transaction>>("/api/financials/transactions/", {
    params: {
      page: params.page,
      page_size: params.pageSize ?? 20,
      status: params.status || undefined,
      search: params.search || undefined,
    },
  });
  return data;
}
