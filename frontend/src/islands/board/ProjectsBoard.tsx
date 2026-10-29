import { useEffect, useMemo, useState } from 'react';
import { api, ApiError } from '../../api';
import { day, money, totals } from '../../format';
import { Icon } from '../../icons';
import { Skeleton } from '../../Skeleton';
import type { Tone } from '../project/types';

// The projects list, and a board by stage, as the prototype draws them: each project shows the step it has
// reached (worked out from its documents, as on the project page) and what to do next.

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
  /** The step it has reached: Quoted, Accepted, Advance, Invoiced, Paid. */
  stage_label: string;
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

const sumQuoted = (rows: Row[]) => {
  const sums: Record<string, number> = {};
  for (const r of rows) if (r.quoted) sums[r.currency] = (sums[r.currency] ?? 0) + r.quoted;
  return sums;
};

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
  const inTab = (t: Tab) => filtered.filter((r) => t === 'all' || r.status === t);
  const shown = useMemo(() => {
    const rows = filtered.filter((r) => tab === 'all' || r.status === tab);
    const by: Record<Sort, (a: Row, b: Row) => number> = {
      activity: (a, b) => (b.last_activity ?? '').localeCompare(a.last_activity ?? ''),
      newest: (a, b) => b.label.localeCompare(a.label, undefined, { numeric: true }),
      due: (a, b) => (b.due ?? 0) - (a.due ?? 0),
    };
    return [...rows].sort(by[sort]);
  }, [filtered, tab, sort]);

  if (!data) return error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="list" label="Loading the projects…" />;

  return (
    <div className="ui">
      <header className="head">
        <div>
          <h1>Projects</h1>
          <div className="meta"><span>One row per customer job, with where it stands</span></div>
        </div>
        {data.new_project && <a className="btn btn-primary" href={data.new_project}><Icon name="plus" />New project</a>}
      </header>

      <div className="tabs" role="tablist" aria-label="By status">
        {TABS.map(([key, label]) => {
          const rows = inTab(key);
          const sums = sumQuoted(rows);
          return (
            <button key={key} type="button" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>
              {label}<span className="tc">{rows.length}</span>
              {!data.can.sales && <span className="tt">{Object.keys(sums).length ? totals(sums) : money(0)}</span>}
            </button>
          );
        })}
      </div>

      <div className="toolbar">
        <label htmlFor="pb-q" className="sr-only">Search projects</label>
        <input id="pb-q" type="search" placeholder="Search name, number, customer or document" value={query} onChange={(e) => setQuery(e.target.value)} />
        <label htmlFor="pb-customer" className="sr-only">Customer</label>
        <select id="pb-customer" value={customer} onChange={(e) => setCustomer(e.target.value)}>
          <option value="">All customers</option>
          {data.customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <label htmlFor="pb-year" className="sr-only">Financial year</label>
        <select id="pb-year" value={year} onChange={(e) => setYear(e.target.value)}>
          <option value="">All years</option>
          {data.years.map((y) => <option key={y} value={y}>FY {y}</option>)}
        </select>
        {view === 'list' && (
          <>
            <label htmlFor="pb-sort" className="sr-only">Sort</label>
            <select id="pb-sort" value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
              <option value="activity">Latest activity</option>
              <option value="newest">Newest project</option>
              {!data.can.sales && <option value="due">Most due</option>}
            </select>
          </>
        )}
        <div className="seg2" role="group" aria-label="View">
          <button type="button" aria-pressed={view === 'list'} onClick={() => pickView('list')}>List</button>
          <button type="button" aria-pressed={view === 'board'} onClick={() => pickView('board')}>Board</button>
        </div>
      </div>

      {view === 'list' ? <List rows={shown} sales={data.can.sales} /> : <Board data={data} rows={filtered} />}
    </div>
  );
}

const GRID = { gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1.5fr) 104px 104px minmax(0, 1.6fr) 72px' };
const SALES_GRID = { gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1.5fr) 104px minmax(0, 1.6fr) 72px' };

function List({ rows, sales }: { rows: Row[]; sales: boolean }) {
  const grid = sales ? SALES_GRID : GRID;
  return (
    <div className="rows" aria-label="Projects">
      <div className="rh" style={grid}>
        <span>Project</span><span>Stage</span><span className="c-num">Quoted</span>{!sales && <span className="c-num">Due</span>}<span>Next step</span><span>Last</span>
      </div>
      {rows.map((r) => (
        <a key={r.id} className="rr" href={r.url} style={grid}>
          <div className="c-main">
            <div className="c-title">{r.title}</div>
            <div className="c-sub"><span className="mono">{r.label}</span> · {r.customer.name}{r.customer.site ? ` · ${r.customer.site}` : ''}
              {r.status !== 'open' ? ` · ${r.status === 'completed' ? 'Completed' : 'Cancelled'}` : ''}</div>
          </div>
          <div><span className={`tag tone-${r.tone}`}>{r.stage_label}</span><div className="c-sub">{r.sub || r.pill.text}</div></div>
          <div className="c-num c-hide">{r.quoted ? money(r.quoted, r.currency) : '—'}</div>
          {!sales && <div className={`c-num${r.tone === 'late' && r.due ? ' late' : ''}`}><span className="c-lbl">Due</span>{r.due ? money(r.due, r.currency) : '—'}</div>}
          <div className="c-next c-hide">{r.status === 'open' ? (r.action ?? r.next) || '—' : '—'}</div>
          <div className="c-date c-hide">{day(r.last_activity)}</div>
        </a>
      ))}
      {rows.length === 0 && <p className="empty-rows">No projects match. Clear the filters to see all of them.</p>}
    </div>
  );
}

const GROUPS: [Tone, string, string][] = [['late', 'Overdue', 'var(--red)'], ['action', 'Needs action', 'var(--amber)'], ['wait', 'Waiting', 'var(--info)']];

/** Open projects in their stage's column, grouped by how urgent they are; paid ones are off the board. */
function Board({ data, rows }: { data: Projects; rows: Row[] }) {
  const open = rows.filter((r) => r.status === 'open' && r.stage);
  const columns = data.board.filter((c) => !data.can.sales || c.key === 'quoted' || c.key === 'accepted');
  const offBoard = rows.filter((r) => r.status === 'open' && !r.stage).length;
  return (
    <>
      <div className="board" style={{ ['--cols' as string]: columns.length }}>
        {columns.map((col) => {
          const cards = open.filter((r) => r.stage === col.key).sort((a, b) => (b.last_activity ?? '').localeCompare(a.last_activity ?? ''));
          const quoted = sumQuoted(cards);
          const groups = GROUPS.map(([t, label, colour]) => ({
            t, label, colour, cards: cards.filter((r) => (t === 'wait' ? r.tone !== 'late' && r.tone !== 'action' : r.tone === t)),
          })).filter((g) => g.cards.length);
          return (
            <section key={col.key} className="bcol" aria-labelledby={`pb-col-${col.key}`}>
              <h3 id={`pb-col-${col.key}`}>{col.label}<span>{cards.length}{!data.can.sales && Object.keys(quoted).length ? ` · ${totals(quoted)}` : ''}</span></h3>
              {cards.length === 0 && <p className="bempty">Nothing here</p>}
              {groups.map((g) => (
                <div key={g.t} style={{ display: 'grid', gap: 8 }}>
                  <div className="bgroup"><i style={{ background: g.colour }} />{g.label}</div>
                  {g.cards.map((r) => (
                    <a key={r.id} href={r.url} className={`pcard t-${r.tone}`}>
                      <b>{r.title}</b>
                      <span className="pc-sub"><span className="mono">{r.label}</span> · {r.customer.site || r.customer.name}</span>
                      <span className="pc-amt">{r.quoted ? money(r.quoted, r.currency) : ''}{r.due ? ` · due ${money(r.due, r.currency)}` : ''}</span>
                      <span className="pc-next">{r.action ?? (r.sub || r.pill.text)}</span>
                    </a>
                  ))}
                </div>
              ))}
            </section>
          );
        })}
      </div>
      {offBoard > 0 && (
        <p className="muted" style={{ margin: '10px 0 0', fontSize: 13 }}>
          {offBoard} paid project{offBoard === 1 ? ' is' : 's are'} off the board: mark them completed, or see them in the list.
        </p>
      )}
    </>
  );
}
