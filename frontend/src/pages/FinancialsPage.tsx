import { useEffect, useState } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { Pagination } from "../components/ui/Pagination";
import { fetchFinancialsSummary, fetchTransactions } from "../lib/financialsApi";
import type { FinancialsSummary, Transaction } from "../types";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "Pending", label: "Pending" },
  { value: "Approved", label: "Approved" },
  { value: "Posted", label: "Posted" },
  { value: "Voided", label: "Voided" },
];

const STATUS_BADGE: Record<string, string> = {
  Pending: "badge-amber",
  Approved: "badge-blue",
  Posted: "badge-green",
  Voided: "badge-gray",
};

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const currencyFormatter = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
});

function formatAmount(value: string) {
  const n = Number(value);
  return Number.isFinite(n) ? currencyFormatter.format(n) : value;
}

export function FinancialsPage() {
  const [summary, setSummary] = useState<FinancialsSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    Promise.all([fetchFinancialsSummary(), fetchTransactions({ page, pageSize: PAGE_SIZE, status })])
      .then(([summaryData, txData]) => {
        if (cancelled) return;
        setSummary(summaryData);
        setTransactions(txData.results);
        setCount(txData.count);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load financial data.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, status]);

  return (
    <AppLayout title="Financials">
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading ? (
        <div className="empty-state">Loading…</div>
      ) : (
        <>
          <div className="stat-grid">
            <StatCard label="Total Transactions" value={summary?.total_transactions ?? 0} sub={summary ? formatAmount(summary.total_amount) : undefined} />
            <StatCard label="Pending" value={summary?.pending_count ?? 0} sub={summary ? formatAmount(summary.pending_amount) : undefined} color="amber" />
            <StatCard label="Approved" value={summary?.approved_count ?? 0} sub={summary ? formatAmount(summary.approved_amount) : undefined} color="blue" />
            <StatCard label="Posted" value={summary?.posted_count ?? 0} sub={summary ? formatAmount(summary.posted_amount) : undefined} color="green" />
          </div>

          <div className="charts-grid">
            <div className="card">
              <div className="card-header">
                <span className="card-title">Top Funds</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Fund</th>
                      <th>Code</th>
                      <th>Count</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(summary?.top_funds ?? []).length === 0 ? (
                      <tr><td colSpan={4}><div className="empty-state"><p>No data.</p></div></td></tr>
                    ) : (
                      summary?.top_funds.map((fund) => (
                        <tr key={fund.fund__code}>
                          <td>{fund.fund__title}</td>
                          <td>{fund.fund__code}</td>
                          <td>{fund.count}</td>
                          <td>{formatAmount(fund.total)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Top Accounts</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Account</th>
                      <th>Code</th>
                      <th>Type</th>
                      <th>Count</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(summary?.top_accounts ?? []).length === 0 ? (
                      <tr><td colSpan={5}><div className="empty-state"><p>No data.</p></div></td></tr>
                    ) : (
                      summary?.top_accounts.map((acc) => (
                        <tr key={acc.account__code}>
                          <td>{acc.account__title}</td>
                          <td>{acc.account__code}</td>
                          <td>{acc.account__account_type}</td>
                          <td>{acc.count}</td>
                          <td>{formatAmount(acc.total)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Transactions</span>
            </div>
            <div className="form-row">
              <div>
                <label className="field-label" htmlFor="status">Status</label>
                <select
                  id="status"
                  className="select"
                  value={status}
                  onChange={(e) => {
                    setPage(1);
                    setStatus(e.target.value);
                  }}
                >
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Reference</th>
                    <th>Description</th>
                    <th>FOAPAL</th>
                    <th>Status</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr><td colSpan={6}><div className="empty-state"><p>No transactions found.</p></div></td></tr>
                  ) : (
                    transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>{dateFormatter.format(new Date(tx.transaction_date))}</td>
                        <td>{tx.reference_number}</td>
                        <td>{tx.description}</td>
                        <td>{tx.foapal_code ?? "—"}</td>
                        <td><span className={`badge ${STATUS_BADGE[tx.status] ?? "badge-gray"}`}>{tx.status}</span></td>
                        <td>{formatAmount(tx.amount)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
          </div>
        </>
      )}
    </AppLayout>
  );
}

function StatCard({ label, value, sub, color = "blue" }: { label: string; value: number; sub?: string; color?: "blue" | "green" | "amber" | "red" }) {
  const colorMap: Record<string, { bg: string; fg: string }> = {
    blue: { bg: "var(--blue-50)", fg: "var(--blue-600)" },
    green: { bg: "var(--green-50)", fg: "var(--green-600)" },
    amber: { bg: "var(--amber-50)", fg: "#92400E" },
    red: { bg: "var(--red-50)", fg: "var(--red-600)" },
  };
  const { bg, fg } = colorMap[color];

  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bg, color: fg }}>
        <svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-label" style={{ marginTop: 2 }}>{sub}</div>}
    </div>
  );
}
