import { useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { money, when } from '../../format';
import { Icon, type IconName } from '../../icons';
import './home.css';

// Home: what needs doing (from where each project is, as on the projects list) and the money still to come in.

type Totals = Record<string, number>;

export interface HomeData {
  attention: {
    key: string;
    title: string;
    count: number;
    total: Totals;
    items: { title: string; sub: string; amount: number | null; currency: string; url: string; action: string | null }[];
    more: number;
  }[];
  unfiled_emails: { count: number; url: string } | null;
  to_receive: {
    total: Totals;
    count: number;
    ages: { label: string; count: number; total: Totals }[];
    customers: { id: string; name: string; count: number; total: Totals }[];
    advances: { count: number; total: Totals };
  };
  month: { label: string; invoiced: Totals; received: Totals };
  recent: { id: string; kind: string; title: string; when: string; link: string | null; who: string | null;
            project: string | null; project_url: string | null }[];
  links: { projects: string; classic: string };
}

const ICONS: Record<string, IconName> = {
  follow_up: 'clock', accepted: 'flag', advance: 'rupee', invoice: 'file', payment: 'rupee', drafts: 'pencil', paid_open: 'done',
};

/** ₹65,69,390 + $8,701: each currency's total, biggest first. */
export function totals(t: Totals): string {
  const parts = Object.entries(t).sort((a, b) => b[1] - a[1]).map(([c, v]) => money(v, c));
  return parts.length ? parts.join(' + ') : money(0);
}

export default function Home() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<HomeData>('/api/home').then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the home page. Check your connection."));
  }, []);

  if (!data) return error ? <p className="hm-error" role="alert">{error}</p> : <p className="text-tertiary">Loading…</p>;

  const r = data.to_receive;
  return (
    <div className="hm-wrap">
      <div className="hm">
        <section className="hm-attention" aria-labelledby="hm-attention">
          <h2 id="hm-attention" className="hm-heading">Needs attention</h2>
          {data.attention.length === 0 && !data.unfiled_emails && (
            <p className="card card-body text-tertiary">Nothing waiting on you. New enquiries and payments will show here.</p>
          )}
          {data.attention.map((g) => (
            <details key={g.key} className="card hm-group" open={g.key !== 'paid_open'}>
              <summary>
                <span className="hm-group-icon" aria-hidden="true"><Icon name={ICONS[g.key] ?? 'flag'} size={16} /></span>
                <span className="hm-group-title">{g.title}</span>
                <span className="hm-group-count">{g.count}</span>
                {Object.keys(g.total).length > 0 && g.key !== 'paid_open' && <span className="hm-group-total">{totals(g.total)}</span>}
              </summary>
              <ul className="hm-items">
                {g.items.map((it) => (
                  <li key={it.url}>
                    <a href={it.url}>
                      <span className="hm-item-main">
                        <span className="hm-item-title">{it.title}</span>
                        <span className="hm-item-sub">{it.sub}</span>
                      </span>
                      <span className="hm-item-side">
                        {!!it.amount && <span className="hm-item-amount">{money(it.amount, it.currency)}</span>}
                        {it.action && <span className="hm-item-action">{it.action} →</span>}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
              {g.more > 0 && <a className="hm-more" href={data.links.projects}>and {g.more} more on the projects board</a>}
            </details>
          ))}
          {data.unfiled_emails && (
            <a className="card hm-group hm-emails" href={data.unfiled_emails.url}>
              <span className="hm-group-icon" aria-hidden="true"><Icon name="mail" size={16} /></span>
              <span className="hm-group-title">Emails not filed to a project</span>
              <span className="hm-group-count">{data.unfiled_emails.count}</span>
              <span className="hm-item-action">File them →</span>
            </a>
          )}
        </section>

        <aside className="hm-side" aria-label="Money">
          <section className="card hm-card" aria-labelledby="hm-receive">
            <div className="card-header"><h2 className="card-title" id="hm-receive">To receive</h2></div>
            <div className="card-body">
              <p className="hm-big">{totals(r.total)}</p>
              <p className="hm-cap">on {r.count} tax invoice{r.count === 1 ? '' : 's'}, by how long ago each was sent</p>
              <ul className="hm-ages">
                {r.ages.map((a, i) => (
                  <li key={a.label} className={`age-${i}`}>
                    <span className="hm-age-label">{a.label}</span>
                    <span className="hm-age-total">{a.count ? totals(a.total) : '—'}</span>
                    <span className="hm-age-count">{a.count || ''}</span>
                  </li>
                ))}
              </ul>
              {r.advances.count > 0 && (
                <p className="hm-advances">Plus {totals(r.advances.total)} in advances asked for on {r.advances.count} project{r.advances.count === 1 ? '' : 's'}.</p>
              )}
              {r.customers.length > 0 && (
                <>
                  <h3 className="hm-sub">Who owes the most</h3>
                  <ul className="hm-customers">
                    {r.customers.map((c) => (
                      <li key={c.id}><span>{c.name}</span><span className="hm-age-total">{totals(c.total)}</span></li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </section>

          <section className="card hm-card" aria-labelledby="hm-month">
            <div className="card-header"><h2 className="card-title" id="hm-month">{data.month.label}</h2></div>
            <div className="card-body hm-month">
              <div><span className="hm-cap">Invoiced</span><b>{totals(data.month.invoiced)}</b></div>
              <div><span className="hm-cap">Received</span><b>{totals(data.month.received)}</b></div>
            </div>
          </section>

          <section className="card hm-card" aria-labelledby="hm-recent">
            <div className="card-header"><h2 className="card-title" id="hm-recent">Lately</h2></div>
            <ul className="hm-recent">
              {data.recent.map((e) => (
                <li key={e.id}>
                  <span className="hm-recent-title">{e.link ? <a href={e.link}>{e.title}</a> : e.title}</span>
                  <span className="hm-item-sub">
                    {[e.project, e.who, when(e.when)].filter(Boolean).join(' · ')}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
