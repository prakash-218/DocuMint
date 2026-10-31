import { Dropdown } from '../../mantine/Dropdown';
import { useEffect, useMemo, useState } from 'react';
import { api, ApiError } from '../../api';
import { download } from '../../download';
import { day, money, totals } from '../../format';
import { Icon } from '../../icons';
import { Skeleton } from '../../Skeleton';
import { PageHeader } from '../../app/PageHeader';
import type { Tone } from '../project/types';

// Quotations, proformas or invoices, as the prototype's list draws them: tabs with how many and how much, one
// search, and a row per document (a revised one once, as its latest version) with its state and what that means.

export interface DocRow {
  id: string;
  number: string;
  kind: string;
  subject: string;
  project: { label: string; title: string; url: string } | null;
  customer: { id: string; name: string; site: string | null };
  date: string | null;
  /** Valid until (quotations) or due (invoices). */
  until: string | null;
  tab: string;
  tag: { text: string; tone: Tone };
  note: string;
  currency: string;
  total: number;
  /** What's still to come in on an unpaid invoice. */
  balance: number | null;
  url: string;
  pdf: string;
  versions: { number: string; url: string }[];
  /** More to match a search on: the PO, earlier numbers. */
  search: string[];
}

export interface DocList {
  group: 'quotes' | 'proformas' | 'invoices';
  title: string;
  until: string | null;
  tabs: { key: string; label: string }[];
  rows: DocRow[];
  new_url: string | null;
  new_label: string;
  /** Several at once (exports.py): post their ids. */
  exports: { csv: string; zip: string };
}

const words = (text: string) => text.toLowerCase().normalize('NFKD').replace(/[^a-z0-9/]+/g, ' ').split(' ').filter(Boolean);

export function matches(row: DocRow, query: string): boolean {
  const hay = words([row.number, row.subject, row.customer.name, row.customer.site ?? '', row.project?.label ?? '',
    row.project?.title ?? '', ...row.search].join(' '));
  return words(query).every((q) => hay.some((w) => w.includes(q)));
}

/** The Indian financial year a date falls in: '26-27' for 2026-04-01 to 2027-03-31. */
export function fiscalYear(iso: string | null): string {
  if (!iso) return '';
  const [y, m] = iso.slice(0, 7).split('-').map(Number);
  const start = m >= 4 ? y : y - 1;
  return `${String(start % 100).padStart(2, '0')}-${String((start + 1) % 100).padStart(2, '0')}`;
}

/** What a tab adds up: what's still due for unpaid and overdue invoices, otherwise the documents' totals. */
function tabSum(rows: DocRow[], tab: string): Record<string, number> {
  const due = tab === 'pending' || tab === 'overdue';
  const sums: Record<string, number> = {};
  for (const r of rows) {
    const v = due ? r.balance ?? 0 : r.total;
    if (v) sums[r.currency] = (sums[r.currency] ?? 0) + v;
  }
  return sums;
}

/** Keep the tab and the search in the address, so reloading or going back shows the same list. */
function remember(tab: string, query: string) {
  try {
    const url = new URL(window.location.href);
    if (tab && tab !== 'all') url.searchParams.set('status', tab); else url.searchParams.delete('status');
    if (query.trim()) url.searchParams.set('q', query.trim()); else url.searchParams.delete('q');
    window.history.replaceState(window.history.state, '', url);
  } catch { /* the address stays as it was */ }
}

const TITLES: Record<string, string> = { quotes: 'Quotations', proformas: 'Proforma invoices', invoices: 'Invoices' };

export default function DocumentList(props: { group: string; tab?: string; query?: string }) {
  return (
    <>
      <PageHeader title={TITLES[props.group] ?? 'Documents'} />
      <ListScreen {...props} />
    </>
  );
}

function ListScreen({ group, tab: firstTab = 'all', query: firstQuery = '' }: { group: string; tab?: string; query?: string }) {
  const [data, setData] = useState<DocList | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(firstTab);
  const [query, setQuery] = useState(firstQuery);
  const [customer, setCustomer] = useState('');
  const [year, setYear] = useState('');
  const [picked, setPicked] = useState<Set<string> | null>(null);     // choosing rows: their ids; null when not

  useEffect(() => {
    api.get<DocList>(`/api/documents/${group}`).then((d) => {
      setData(d);
      if (!d.tabs.some((t) => t.key === firstTab)) setTab('all');
    }).catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the list. Check your connection."));
  }, [group, firstTab]);

  useEffect(() => { remember(tab, query); }, [tab, query]);

  const customers = useMemo(() => {
    const seen = new Map<string, string>();
    for (const r of data?.rows ?? []) seen.set(r.customer.id, r.customer.site ? `${r.customer.name} · ${r.customer.site}` : r.customer.name);
    return [...seen].sort((a, b) => a[1].localeCompare(b[1]));
  }, [data]);
  const years = useMemo(() => [...new Set((data?.rows ?? []).map((r) => fiscalYear(r.date)).filter(Boolean))].sort().reverse(), [data]);
  const filtered = useMemo(() => (data?.rows ?? []).filter((r) =>
    (!customer || r.customer.id === customer) && (!year || fiscalYear(r.date) === year) && (!query.trim() || matches(r, query))),
  [data, customer, year, query]);

  if (!data) return error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="list" label="Loading the list…" />;

  const inTab = (key: string) => filtered.filter((r) => key === 'all' || r.tab === key);
  const shown = inTab(tab);
  const what = data.title.toLowerCase();

  return (
    <div className="ui">
      <header className="head">
        <div>
          <h1>{data.title}</h1>
          <div className="meta"><span>{year ? `FY ${year}` : 'All years'}</span></div>
        </div>
        {data.new_url && <a className="btn btn-primary" href={data.new_url}><Icon name="plus" />{data.new_label}</a>}
      </header>

      <div className="tabs" role="tablist" aria-label="By status">
        {data.tabs.map((t) => {
          const rows = inTab(t.key);
          const sums = tabSum(rows, t.key);
          return (
            <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}>
              {t.label}<span className="tc">{rows.length}</span>
              <span className="tt">{Object.keys(sums).length ? totals(sums) : money(0)}</span>
            </button>
          );
        })}
      </div>

      <div className="toolbar">
        <label htmlFor="dl-q" className="sr-only">Search {what}</label>
        <input id="dl-q" type="search" placeholder="Search number, subject, customer, project or PO" value={query} onChange={(e) => setQuery(e.target.value)} />
        <label htmlFor="dl-customer" className="sr-only">Customer</label>
        <Dropdown id="dl-customer" value={customer} onChange={setCustomer}
                  data={[{ value: '', label: 'All customers' }, ...customers.map(([id, name]) => ({ value: id, label: name }))]} />
        <label htmlFor="dl-year" className="sr-only">Financial year</label>
        <Dropdown id="dl-year" value={year} onChange={setYear}
                  data={[{ value: '', label: 'All years' }, ...years.map((y) => ({ value: y, label: `FY ${y}` }))]} />
        {!picked && shown.length > 0 && (
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setPicked(new Set())}><Icon name="checkCheck" />Select</button>
            <button type="button" className="btn btn-secondary" onClick={() => download(data.exports.csv, shown.map((r) => r.id))}
                    title={`A row for each of the ${shown.length} shown, with the taxable value and GST`}><Icon name="download" />Export CSV</button>
          </>
        )}
      </div>

      {picked && (
        <div className="bulkbar" role="region" aria-label="Chosen documents">
          <span>{picked.size} selected</span>
          <button type="button" className="btn btn-xs" onClick={() => setPicked(picked.size === shown.length ? new Set() : new Set(shown.map((r) => r.id)))}>
            {picked.size === shown.length ? 'Clear' : `Select all ${shown.length}`}
          </button>
          <span className="spacer" />
          <button type="button" className="btn btn-xs" disabled={!picked.size || picked.size > MAX_PDFS} title={picked.size > MAX_PDFS ? `Up to ${MAX_PDFS} at a time` : undefined}
                  onClick={() => download(data.exports.zip, [...picked])}><Icon name="download" />Download PDFs</button>
          <button type="button" className="btn btn-xs" disabled={!picked.size} onClick={() => download(data.exports.csv, [...picked])}>Export CSV</button>
          <button type="button" className="btn btn-xs" onClick={() => setPicked(null)}>Done</button>
        </div>
      )}

      <Rows data={data} rows={shown} picked={picked}
            onPick={(id) => setPicked((now) => { const next = new Set(now); if (next.has(id)) next.delete(id); else next.add(id); return next; })} />
    </div>
  );
}

/** As exports.MAX_PDFS: a ZIP is made while you wait. */
const MAX_PDFS = 60;

function Rows({ data, rows, picked, onPick }: { data: DocList; rows: DocRow[]; picked: Set<string> | null; onPick: (id: string) => void }) {
  const invoices = data.group === 'invoices';
  const until = data.until && rows.some((r) => r.until) ? data.until : null;      // no column when none has a date
  const grid = { gridTemplateColumns: [picked && '20px', 'minmax(0, 2.2fr)', 'minmax(0, 1.5fr)', '64px', until && '84px', 'minmax(0, 1.1fr)', '112px',
    invoices && '104px'].filter(Boolean).join(' ') };
  return (
    <div className="rows" aria-label={data.title}>
      <div className="rh" style={grid}>
        {picked && <span />}<span>Number</span><span>Customer</span><span>Date</span>{until && <span>{until}</span>}<span>Status</span>
        <span className="c-num">Total</span>{invoices && <span className="c-num">Balance</span>}
      </div>
      {rows.map((r) => {
        const about = [r.subject || r.project?.title, invoices && r.kind !== 'Tax Invoice' ? r.kind : ''].filter(Boolean).join(' · ');
        const late = r.tab === 'overdue' ? ' late' : '';
        // choosing: the row is the checkbox's label, rather than a link to the document
        const Row = picked ? 'label' : 'a';
        return (
          <Row key={r.id} className={`rr${picked ? ' picking' : ''}`} {...(picked ? {} : { href: r.url })} style={grid}>
            {picked && <input type="checkbox" checked={picked.has(r.id)} onChange={() => onPick(r.id)} aria-label={`Choose ${r.number}`} />}
            <div className="c-main">
              <div className="c-title mono">{r.number}</div>
              <div className="c-sub">
                {about}{about && r.project ? ' · ' : ''}{r.project && <span className="nowrap">{r.project.label}</span>}
                {r.versions.length > 0 && <> · <span className="nowrap">{r.versions.length} earlier version{r.versions.length === 1 ? '' : 's'}</span></>}
              </div>
            </div>
            <div className="c-sub">{r.customer.name}{r.customer.site ? ` · ${r.customer.site}` : ''}</div>
            <div className="c-date c-hide">{day(r.date) || '—'}</div>
            {until && <div className={`c-date c-hide${late}`}>{day(r.until) || '—'}</div>}
            <div>
              <span className={`tag tone-${r.tag.tone}`}>{r.tag.text}</span>
              {r.note && <div className={`c-sub${late}`}>{r.note}</div>}
            </div>
            <div className="c-num">{money(r.total, r.currency)}</div>
            {invoices && (
              // on a phone, only when it isn't the whole total
              <div className={`c-num${late}${r.balance === r.total ? ' c-hide' : ''}`}><span className="c-lbl">Due</span>{r.balance ? money(r.balance, r.currency) : '—'}</div>
            )}
          </Row>
        );
      })}
      {rows.length === 0 && <p className="empty-rows">{data.rows.length ? 'Nothing matches. Clear the search or the filters to see them all.' : `No ${data.title.toLowerCase()} yet.`}</p>}
    </div>
  );
}
