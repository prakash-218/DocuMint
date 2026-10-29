import { useEffect, useMemo, useState } from 'react';
import { api, ApiError } from '../../api';
import { day, money } from '../../format';
import type { Tone } from '../project/types';
import './board.css';

// The projects list, and a board by stage: each project shows where it is (worked out from its documents,
// as on the project page) and what to do next.

export interface Row {
  id: string;
  label: string;
  title: string;
  reference: string;
  url: string;
  customer: { id: string; name: string; site: string | null };
  fiscal_year: string;
  status: 'open' | 'completed' | 'cancelled';
  stage: string | null;
  pill: { text: string; tone: Tone };
  sub: string;
  next: string;
  action: string | null;
  tone: Tone;
  currency: string;
  quoted: number;
  due: number | null;
  last_activity: string | null;
  numbers: string[];
}

export interface Projects {
  can: { edit: boolean; sales: boolean };
  projects: Row[];
  board: { key: string; label: string }[];
  years: string[];
  customers: { id: string; name: string }[];
  new_project: string | null;
  classic_url: string;
}

type Tab = 'open' | 'completed' | 'cancelled' | 'all';
type View = 'list' | 'board';
type Sort = 'activity' | 'newest' | 'due';
const VIEW_KEY = 'documint.projectsView';
const TABS: [Tab, string][] = [['open', 'Open'], ['completed', 'Completed'], ['cancelled', 'Cancelled'], ['all', 'All']];

function savedView(): View {
  try {
    return window.localStorage.getItem(VIEW_KEY) === 'board' ? 'board' : 'list';
  } catch {
    return 'list';
  }
}

const words = (text: string) => text.toLowerCase().normalize('NFKD').replace(/[^a-z0-9/]+/g, ' ').split(' ').filter(Boolean);

export function matches(row: Row, query: string): boolean {
  const hay = words([row.title, row.label, row.reference, row.customer.name, row.customer.site ?? '', ...row.numbers].join(' '));
  return words(query).every((q) => hay.some((w) => w.includes(q)));
}

export default function ProjectsBoard() {
  const [data, setData] = useState<Projects | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('open');
  const [view, setView] = useState<View>(savedView);
  const [query, setQuery] = useState('');
  const [customer, setCustomer] = useState('');
  const [year, setYear] = useState('');
  const [sort, setSort] = useState<Sort>('activity');

  useEffect(() => {
    api.get<Projects>('/api/projects').then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the projects. Check your connection."));
  }, []);

  function pickView(next: View) {
    setView(next);
    try { window.localStorage.setItem(VIEW_KEY, next); } catch { /* not remembered */ }
  }

  const filtered = useMemo(() => (data?.projects ?? []).filter((r) =>
    (!customer || r.customer.id === customer) && (!year || r.fiscal_year === year) && (!query.trim() || matches(r, query))), [data, customer, year, query]);
  const counts = useMemo(() => Object.fromEntries(TABS.map(([t]) => [t, filtered.filter((r) => t === 'all' || r.status === t).length])), [filtered]);
  const shown = useMemo(() => {
    const rows = filtered.filter((r) => tab === 'all' || r.status === tab);
    const by: Record<Sort, (a: Row, b: Row) => number> = {
      activity: (a, b) => (b.last_activity ?? '').localeCompare(a.last_activity ?? ''),
      newest: (a, b) => b.label.localeCompare(a.label, undefined, { numeric: true }),
      due: (a, b) => (b.due ?? 0) - (a.due ?? 0),
    };
    return [...rows].sort(by[sort]);
  }, [filtered, tab, sort]);

  if (!data) return error ? <p className="pb-error" role="alert">{error}</p> : <p className="text-tertiary">Loading the projects…</p>;

  return (
    <div className="pb">
      <div className="pb-bar">
        {view === 'list' && (
          <nav className="segmented" aria-label="Filter by status">
            {TABS.map(([key, label]) => (
              <button key={key} type="button" className={`filter-btn${tab === key ? ' active' : ''}`} aria-pressed={tab === key} onClick={() => setTab(key)}>
                {label} <span className="count">{counts[key]}</span>
              </button>
            ))}
          </nav>
        )}
        <div className="pb-filters">
          <label htmlFor="pb-q" className="sr-only">Search projects</label>
          <input id="pb-q" type="search" className="form-input" placeholder="Search name, number, customer or document"
                 value={query} onChange={(e) => setQuery(e.target.value)} />
          <label htmlFor="pb-customer" className="sr-only">Customer</label>
          <select id="pb-customer" className="form-select" value={customer} onChange={(e) => setCustomer(e.target.value)}>
            <option value="">All customers</option>
            {data.customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <label htmlFor="pb-year" className="sr-only">Financial year</label>
          <select id="pb-year" className="form-select" value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="">All years</option>
            {data.years.map((y) => <option key={y} value={y}>FY {y}</option>)}
          </select>
          {view === 'list' && (
            <>
              <label htmlFor="pb-sort" className="sr-only">Sort</label>
              <select id="pb-sort" className="form-select" value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
                <option value="activity">Latest activity</option>
                <option value="newest">Newest project</option>
                {!data.can.sales && <option value="due">Most due</option>}
              </select>
            </>
          )}
          <div className="segmented pb-view" role="group" aria-label="View">
            <button type="button" className={`filter-btn${view === 'list' ? ' active' : ''}`} aria-pressed={view === 'list'} onClick={() => pickView('list')}>List</button>
            <button type="button" className={`filter-btn${view === 'board' ? ' active' : ''}`} aria-pressed={view === 'board'} onClick={() => pickView('board')}>Board</button>
          </div>
        </div>
      </div>

      {view === 'list' ? <List rows={shown} sales={data.can.sales} /> : <Board data={data} rows={filtered} />}
    </div>
  );
}

function List({ rows, sales }: { rows: Row[]; sales: boolean }) {
  if (!rows.length) return <p className="text-tertiary pb-empty">No projects match.</p>;
  return (
    <div className="table-container">
      <table className="table pb-table">
        <thead>
          <tr>
            <th>Project</th><th className="hide-mobile">Customer</th><th>Where it is</th><th className="hide-mobile">Next</th>
            <th className="num">Quoted</th>{!sales && <th className="num">Due</th>}<th className="num hide-mobile">Last activity</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>
                <a href={r.url} className="cell-primary">{r.title}</a>
                <span className="cell-secondary">{r.label} · FY {r.fiscal_year}{r.reference ? ` · ${r.reference}` : ''}</span>
              </td>
              <td className="hide-mobile">{r.customer.name}{r.customer.site && <span className="cell-secondary">{r.customer.site}</span>}</td>
              <td>
                <span className={`pb-pill tone-${r.pill.tone}`}>{r.pill.text}</span>
                {r.sub && <span className="cell-secondary">{r.sub}</span>}
              </td>
              <td className="hide-mobile pb-next">{r.action ?? <span className="text-tertiary">—</span>}</td>
              <td className="num">{r.quoted ? money(r.quoted, r.currency) : '—'}</td>
              {!sales && <td className={`num${r.due ? ' pb-due' : ''}`}>{r.due ? money(r.due, r.currency) : '—'}</td>}
              <td className="num hide-mobile">{day(r.last_activity)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const NEEDS_ACTION: Tone[] = ['action', 'late'];

/** Open projects in their stage's column, the ones needing action on top; paid ones are off the board. */
function Board({ data, rows }: { data: Projects; rows: Row[] }) {
  const open = rows.filter((r) => r.status === 'open' && r.stage);
  const columns = data.board.filter((c) => !data.can.sales || c.key === 'quoted' || c.key === 'accepted');
  const offBoard = rows.filter((r) => r.status === 'open' && !r.stage).length;
  return (
    <>
      <div className="pb-board">
        {columns.map((col) => {
          const cards = open.filter((r) => r.stage === col.key)
            .sort((a, b) => Number(NEEDS_ACTION.includes(b.tone)) - Number(NEEDS_ACTION.includes(a.tone))
                         || (b.last_activity ?? '').localeCompare(a.last_activity ?? ''));
          return (
            <section key={col.key} className="pb-column" aria-labelledby={`pb-col-${col.key}`}>
              <h2 id={`pb-col-${col.key}`}>{col.label} <span className="count">{cards.length}</span></h2>
              {cards.length === 0 && <p className="text-tertiary pb-empty">Nothing here.</p>}
              {cards.map((r) => (
                <a key={r.id} href={r.url} className={`pb-card tone-${r.tone}`}>
                  <span className="pb-card-title">{r.title}</span>
                  <span className="pb-card-sub">{r.customer.site || r.customer.name} · <span className="pb-nowrap">{r.label}</span></span>
                  <span className="pb-card-row">
                    <span className={`pb-pill tone-${r.pill.tone}`}>{r.sub || r.pill.text}</span>
                    <span className="pb-card-amount">{r.quoted ? money(r.quoted, r.currency) : ''}</span>
                  </span>
                  {r.action && <span className="pb-card-action">{r.action} →</span>}
                </a>
              ))}
            </section>
          );
        })}
      </div>
      {offBoard > 0 && (
        <p className="text-tertiary pb-note">{offBoard} paid project{offBoard === 1 ? ' is' : 's are'} off the board: mark them completed, or see them in the list.</p>
      )}
    </>
  );
}
