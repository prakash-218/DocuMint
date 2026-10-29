import { useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { money, totals, when } from '../../format';
import { Icon, type IconName } from '../../icons';
import { Skeleton } from '../../Skeleton';
import type { Tone } from '../project/types';

// Home, as the prototype draws it: a greeting and the three numbers that matter, what needs doing (one row a
// kind, each opening to its projects), the money to come in by how old it is, and what happened lately.

type Totals = Record<string, number>;

export interface HomeData {
  hello?: { name: string; today: string; fy: string; greeting: string };
  open_quotes?: { count: number; total: Totals };
  attention: {
    key: string;
    title: string;
    label?: string;
    names?: string;
    count: number;
    total: Totals;
    items: { title: string; sub: string; amount: number | null; currency: string; url: string; action: string | null }[];
    more: number;
    /** Where the rest are, when not on the projects list (overdue invoices: the invoices list). */
    more_url?: string;
    more_label?: string;
  }[];
  unfiled_emails: { count: number; url: string } | null;
  to_receive: {
    total: Totals;
    count: number;
    /** 'due': by how late (every unpaid invoice has a due date); 'date': by how long ago it was sent. */
    aged_by: 'due' | 'date';
    overdue: { count: number; total: Totals };
    ages: { label: string; count: number; total: Totals }[];
    customers: { id: string; name: string; count: number; total: Totals; url?: string }[];
    advances: { count: number; total: Totals };
  };
  month: { label: string; invoiced: Totals; received: Totals };
  recent: { id: string; kind: string; title: string; when: string; link: string | null; who: string | null;
            project: string | null; project_url: string | null }[];
  links: { projects: string };
}

// Each kind of thing to do: its icon and tone, as in the prototype
const KINDS: Record<string, { icon: IconName; tone: Tone }> = {
  overdue: { icon: 'alert', tone: 'late' },
  follow_up: { icon: 'clock', tone: 'action' },
  accepted: { icon: 'done', tone: 'action' },
  advance: { icon: 'rupee', tone: 'wait' },
  invoice: { icon: 'file', tone: 'action' },
  payment: { icon: 'receipt', tone: 'late' },
  drafts: { icon: 'pencil', tone: 'draft' },
  paid_open: { icon: 'done', tone: 'done' },
};
export const EVENT_ICONS: Record<string, IconName> = {
  email_received: 'mail', email_sent: 'send', payment: 'rupee', note: 'note', file_uploaded: 'paperclip', project_created: 'plus',
  project_status: 'flag', document_created: 'pencil', document_sent: 'send', document_converted: 'file', document_corrected: 'pencil',
  document_reopened: 'pencil', quote_revised: 'file', quote_status: 'done',
};

/** ₹65,69,390 + $8,701: each currency's total, biggest first. */
export { totals };

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;
const primary = (t: Totals) => t.INR ?? Object.values(t)[0] ?? 0;

export default function Home() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<HomeData>('/api/home').then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the home page. Check your connection."));
  }, []);

  if (!data) return error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="home" label="Loading the home page…" />;

  const r = data.to_receive;
  const old = r.ages[r.ages.length - 1];
  const hello = data.hello;
  const today = hello ? new Date(`${hello.today}T00:00:00`) : new Date();
  const ageWidth = r.ages.map((a) => primary(a.total));
  return (
    <div className="ui">
      <header className="head">
        <div>
          <h1>{hello ? `${hello.greeting}${hello.name ? `, ${hello.name}` : ''}` : 'Home'}</h1>
          <div className="meta">
            <span>{today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })}</span>
            {hello?.fy && <span>FY {hello.fy}</span>}
          </div>
        </div>
        <div className="head-right"><a className="btn btn-secondary" href={data.links.projects}>All projects</a></div>
      </header>

      <div className="stats">
        <div className="stat"><small>To receive</small><b>{r.count ? totals(r.total) : money(0)}</b>
          <span className="cap">{plural(r.count, 'invoice', 'invoices')}</span></div>
        {r.aged_by === 'due' ? (
          <div className={`stat${r.overdue.count ? ' late' : ''}`}><small>Overdue</small><b>{r.overdue.count ? totals(r.overdue.total) : money(0)}</b>
            <span className="cap">{plural(r.overdue.count, 'invoice', 'invoices')} past the due date</span></div>
        ) : (
          <div className={`stat${old?.count ? ' late' : ''}`}><small>Over 90 days old</small><b>{old?.count ? totals(old.total) : money(0)}</b>
            <span className="cap">{plural(old?.count ?? 0, 'invoice', 'invoices')}</span></div>
        )}
        <div className="stat"><small>Open quotations</small><b>{data.open_quotes?.count ? totals(data.open_quotes.total) : money(0)}</b>
          <span className="cap">{plural(data.open_quotes?.count ?? 0, 'quotation', 'quotations')} not answered yet</span></div>
      </div>

      <div className="home-cols">
        <section className="card" aria-labelledby="hm-attention">
          <div className="card-h"><h2 id="hm-attention">Needs attention</h2><span className="muted">Open a row for its projects</span></div>
          <div className="card-b">
            {data.attention.length === 0 && !data.unfiled_emails && (
              <p className="empty-feed">Nothing waiting on you. New enquiries and payments will show here.</p>
            )}
            <ul className="attn">
              {data.attention.map((g) => {
                const k = KINDS[g.key] ?? { icon: 'flag' as IconName, tone: 'action' as Tone };
                return (
                  <li key={g.key}>
                    <details>
                      <summary>
                        <span className={`ai tone-${k.tone}`}><Icon name={k.icon} size={15} /></span>
                        <span><span className="at">{g.label ?? g.title}</span><span className="as">{g.names}</span></span>
                        <span className="aa">{Object.keys(g.total).length > 0 && g.key !== 'paid_open' ? totals(g.total) : ''}</span>
                        <span className="chev" aria-hidden="true"><Icon name="chevronRight" size={16} /></span>
                      </summary>
                      <ul className="attn-items">
                        {g.items.map((i) => (
                          <li key={i.url + i.title}>
                            <a href={i.url}>
                              <span><span className="at">{i.title}</span><span className="as">{i.sub}</span></span>
                              <span className="attn-side">
                                {i.amount ? <span className="aa">{money(i.amount, i.currency)}</span> : null}
                                {i.action && <span className="attn-act">{i.action} →</span>}
                              </span>
                            </a>
                          </li>
                        ))}
                        {g.more > 0 && <li><a href={g.more_url ?? data.links.projects} className="attn-more">and {g.more} more {g.more_label ?? 'on the projects list'}</a></li>}
                      </ul>
                    </details>
                  </li>
                );
              })}
              {data.unfiled_emails && (
                <li>
                  <a href={data.unfiled_emails.url}>
                    <span className="ai tone-draft"><Icon name="mail" size={15} /></span>
                    <span><span className="at">{plural(data.unfiled_emails.count, 'email not filed to a project', 'emails not filed to a project')}</span>
                      <span className="as">Each is offered a project to go in</span></span>
                    <span className="aa" />
                    <span className="chev" aria-hidden="true"><Icon name="chevronRight" size={16} /></span>
                  </a>
                </li>
              )}
            </ul>
          </div>
        </section>

        <div className="col-side">
          <section className="card" aria-labelledby="hm-receive">
            <div className="card-h"><h2 id="hm-receive">To receive</h2><span className="num">{r.count ? totals(r.total) : money(0)}</span></div>
            <div className="card-b">
              {r.count > 0 && (
                <div className="agebar" aria-hidden="true">
                  {r.ages.map((a, i) => ageWidth[i] > 0 && <span key={a.label} className={`g-${i}`} style={{ flex: ageWidth[i] }} title={`${a.label}: ${totals(a.total)}`} />)}
                </div>
              )}
              <ul className="agetiles" aria-label={r.aged_by === 'due' ? 'By how late each invoice is' : 'By how long ago each invoice was sent'}>
                {r.ages.map((a, i) => (
                  <li key={a.label}>
                    <small><i className={`g-${i}`} />{a.label}</small>
                    <b>{a.count ? totals(a.total) : '—'}</b>
                    <span className="cnt">{plural(a.count, 'invoice', 'invoices')}</span>
                  </li>
                ))}
              </ul>
              {r.advances.count > 0 && (
                <p className="muted" style={{ margin: '10px 0 0', fontSize: 13 }}>
                  Advances requested on proformas: <span className="num">{totals(r.advances.total)}</span> ({plural(r.advances.count, 'project', 'projects')}).
                  They count once paid.
                </p>
              )}
              {r.customers.length > 0 && (
                <>
                  <h3 className="hm-sub">Who owes the most</h3>
                  <ul className="hm-owe">
                    {r.customers.map((c) => (
                      <li key={c.id}>{c.url ? <a href={c.url}>{c.name}</a> : <span>{c.name}</span>}<span className="num">{totals(c.total)}</span></li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </section>

          <section className="card" aria-labelledby="hm-recent">
            <div className="card-h"><h2 id="hm-recent">Recent activity</h2></div>
            <div className="card-b">
              {data.recent.length === 0 ? <p className="empty-feed">Nothing yet.</p> : (
                <ul className="act">
                  {data.recent.map((e) => (
                    <li key={e.id}>
                      <span className="ico"><Icon name={EVENT_ICONS[e.kind] ?? 'file'} size={14} /></span>
                      <div>
                        {e.link ? <a href={e.link}>{e.title}</a> : e.title}
                        <small>{[when(e.when), e.project, e.who].filter(Boolean).join(' · ')}</small>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
