import { Dropdown } from '../../mantine/Dropdown';
import { useEffect, useMemo, useState } from 'react';
import { api, ApiError } from '../../api';
import { money, totals } from '../../format';
import { Skeleton } from '../../Skeleton';
import { PageHeader } from '../../app/PageHeader';
import { fiscalYear } from '../documents/DocumentList';

// Every payment received (payments_view.py), as the document lists draw theirs: tabs with how many and how much,
// one search, the customer and the year, and a row per payment with its document, how it came and its bank reference.

export interface PaymentRow {
  id: string;
  date: string;
  amount: number;
  currency: string;
  /** A payment in another currency: the rupees the bank credited. */
  credited: { amount: number; currency: string } | null;
  method: string;
  reference: string;
  tab: 'advance' | 'invoice';
  note: string;
  document: { number: string; kind: string; url: string };
  customer: { id: string; name: string; site: string | null };
  project: { label: string; title: string; url: string } | null;
}

export interface PaymentList {
  title: string;
  tabs: { key: string; label: string }[];
  rows: PaymentRow[];
}

/** Every word typed is in the document's number, the customer, the project, the method or the bank reference. */
export function matches(row: PaymentRow, query: string): boolean {
  const hay = [row.document.number, row.customer.name, row.customer.site ?? '', row.project?.label ?? '', row.project?.title ?? '',
    row.method, row.reference, row.note].join(' ').toLowerCase();
  return query.toLowerCase().split(/\s+/).filter(Boolean).every((w) => hay.includes(w));
}

const dated = (iso: string) => {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
};

function sum(rows: PaymentRow[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of rows) out[r.currency] = (out[r.currency] ?? 0) + r.amount;
  return out;
}

/** Keep the tab, the search and the year in the address, so reloading or going back shows the same list. */
function remember(tab: string, query: string, year: string) {
  try {
    const url = new URL(window.location.href);
    for (const [key, value, empty] of [['tab', tab, 'all'], ['q', query.trim(), ''], ['fy', year, '']]) {
      if (value && value !== empty) url.searchParams.set(key, value); else url.searchParams.delete(key);
    }
    window.history.replaceState(window.history.state, '', url);
  } catch { /* the address stays as it was */ }
}

export default function Payments({ tab: firstTab = 'all', query: firstQuery = '', year: firstYear = '' }:
  { tab?: string; query?: string; year?: string }) {
  const [data, setData] = useState<PaymentList | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(firstTab);
  const [query, setQuery] = useState(firstQuery);
  const [customer, setCustomer] = useState('');
  const [year, setYear] = useState(firstYear);

  useEffect(() => {
    api.get<PaymentList>('/api/payments').then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the payments. Check your connection."));
  }, []);
  useEffect(() => { remember(tab, query, year); }, [tab, query, year]);

  const customers = useMemo(() => {
    const seen = new Map<string, string>();
    for (const r of data?.rows ?? []) seen.set(r.customer.id, r.customer.site ? `${r.customer.name} · ${r.customer.site}` : r.customer.name);
    return [...seen].sort((a, b) => a[1].localeCompare(b[1]));
  }, [data]);
  const years = useMemo(() => [...new Set((data?.rows ?? []).map((r) => fiscalYear(r.date)).filter(Boolean))].sort().reverse(), [data]);
  const filtered = useMemo(() => (data?.rows ?? []).filter((r) =>
    (!customer || r.customer.id === customer) && (!year || fiscalYear(r.date) === year) && (!query.trim() || matches(r, query))),
  [data, customer, year, query]);

  const page = <PageHeader title="Payments" />;
  if (!data) return <>{page}{error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="list" label="Loading the payments…" />}</>;

  const inTab = (key: string) => filtered.filter((r) => key === 'all' || r.tab === key);
  const shown = inTab(tab);
  const grid = { gridTemplateColumns: '96px minmax(0, 1.6fr) minmax(0, 1.3fr) minmax(0, 1.3fr) 128px' };

  return (
    <>
      {page}
      <div className="ui">
        <header className="head">
          <div>
            <h1>{data.title}</h1>
            <div className="meta"><span>{year ? `FY ${year}` : 'All years'}</span><span>Every payment received, with its bank reference</span></div>
          </div>
        </header>

        <div className="tabs" role="tablist" aria-label="Kind of payment">
          {data.tabs.map((t) => {
            const rows = inTab(t.key);
            return (
              <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}>
                {t.label}<span className="tc">{rows.length}</span><span className="tt">{totals(sum(rows))}</span>
              </button>
            );
          })}
        </div>

        <div className="toolbar">
          <label htmlFor="pay-q" className="sr-only">Search payments</label>
          <input id="pay-q" type="search" placeholder="Search document, customer, project or bank reference" value={query}
                 onChange={(e) => setQuery(e.target.value)} />
          <label htmlFor="pay-customer" className="sr-only">Customer</label>
          <Dropdown id="pay-customer" value={customer} onChange={setCustomer}
                    data={[{ value: '', label: 'All customers' }, ...customers.map(([id, name]) => ({ value: id, label: name }))]} />
          <label htmlFor="pay-year" className="sr-only">Financial year</label>
          <Dropdown id="pay-year" value={year} onChange={setYear}
                    data={[{ value: '', label: 'All years' }, ...years.map((y) => ({ value: y, label: `FY ${y}` }))]} />
        </div>

        <div className="rows" aria-label="Payments">
          <div className="rh" style={grid}>
            <span>Date</span><span>Customer</span><span>Document</span><span>How it came</span><span className="c-num">Amount</span>
          </div>
          {shown.map((r) => (
            <a key={r.id} className="rr" href={r.document.url} style={grid}>
              <div className="c-date">{dated(r.date)}</div>
              <div className="c-main">
                <div className="c-title">{r.customer.name}{r.customer.site ? ` · ${r.customer.site}` : ''}</div>
                {r.project && <div className="c-sub"><span className="mono">{r.project.label}</span> {r.project.title}</div>}
              </div>
              <div>
                <div className="mono">{r.document.number}</div>
                <div className="c-sub">{r.note || r.document.kind}</div>
              </div>
              <div className="c-sub">
                {r.method || 'Not said'}
                {r.reference && <div className="mono">{r.reference}</div>}
              </div>
              <div className="c-num">
                {money(r.amount, r.currency)}
                {r.credited && <div className="c-sub">{money(r.credited.amount, r.credited.currency)} credited</div>}
              </div>
            </a>
          ))}
          {shown.length === 0 && (
            <p className="empty-rows">{data.rows.length ? 'Nothing matches. Clear the search or the filters to see them all.'
              : 'No payments yet. Record one on an invoice, or an advance on a proforma.'}</p>
          )}
        </div>
      </div>
    </>
  );
}
