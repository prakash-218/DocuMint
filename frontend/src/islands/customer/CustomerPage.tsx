import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { day, money } from '../../format';
import { Icon } from '../../icons';
import { status } from '../project/Documents';
import type { ContactFields } from '../project/People';
import { Contacts } from './Contacts';
import { Owed, Statement } from './Money';
import type { CustomerData } from './types';
import '../project/project.css';
import './customer.css';

// The new customer page: what they owe and how old it is, then their projects, documents, statement and files
// (one at a time, by tab), with their people, details and sites beside them.

type Tab = 'projects' | 'documents' | 'statement' | 'files';
const DOC_FILTERS = [
  { key: '', label: 'All' },
  { key: 'quote', label: 'Quotations' },
  { key: 'proforma', label: 'Proformas' },
  { key: 'invoice', label: 'Invoices' },
] as const;

function startTab(): Tab {
  const hash = window.location.hash.slice(1);
  return (['projects', 'documents', 'statement', 'files'] as const).find((t) => t === hash) ?? 'projects';
}

export default function CustomerPage({ customerId }: { customerId: string }) {
  const [data, setData] = useState<CustomerData | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [tab, setTab] = useState<Tab>(startTab);
  const base = `/api/customers/${customerId}`;

  const load = useCallback(async () => {
    try {
      setData(await api.get<CustomerData>(base));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't load the customer. Check your connection.");
    }
  }, [base]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {                         // a link to #statement (or another tab) on this page opens it
    const follow = () => setTab(startTab());
    window.addEventListener('hashchange', follow);
    return () => window.removeEventListener('hashchange', follow);
  }, []);

  async function change(run: () => Promise<unknown>, done: string): Promise<boolean> {
    try {
      await run();
      setError('');
      setNotice(done);
      await load();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong. Nothing was changed.');
      return false;
    }
  }

  if (!data) {
    return error ? <p className="pp-error" role="alert">{error}</p> : <p className="text-tertiary pp-loading">Loading the customer…</p>;
  }

  const { customer, can } = data;
  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: 'projects', label: 'Projects', count: data.projects.length },
    { key: 'documents', label: 'Documents', count: data.documents.length },
    ...(data.money ? [{ key: 'statement' as const, label: 'Statement' }] : []),
    { key: 'files', label: 'Files', count: data.files_count },
  ];
  const shown = tabs.some((t) => t.key === tab) ? tab : 'projects';
  const pick = (t: Tab) => {
    setTab(t);
    window.history.replaceState(null, '', `#${t}`);
  };

  return (
    <div className="pp cp">
      {error && (
        <div className="pp-error" role="alert">
          <span>{error}</span>
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setError('')}>Dismiss</button>
        </div>
      )}
      {customer.archived && <p className="cp-archived">Archived: hidden from the lists. Their documents are kept.</p>}
      {data.money && <Owed money={data.money} />}

      <div className="pp-cols">
        <div className="pp-main">
          <div className="cp-tabs" role="tablist" aria-label="About this customer">
            {tabs.map((t) => (
              <button key={t.key} type="button" role="tab" id={`cp-tab-${t.key}`} aria-controls="cp-panel"
                      aria-selected={shown === t.key} className={`cp-tab${shown === t.key ? ' is-on' : ''}`} onClick={() => pick(t.key)}>
                {t.label}{t.count !== undefined && <span className="cp-count">{t.count}</span>}
              </button>
            ))}
          </div>
          <section className="card pp-card cp-panel" id="cp-panel" role="tabpanel" aria-labelledby={`cp-tab-${shown}`}>
            {shown === 'projects' && <Projects data={data} />}
            {shown === 'documents' && <Documents data={data} />}
            {shown === 'statement' && data.money && <Statement accounts={data.money.statement} />}
            {shown === 'files' && <Files data={data} />}
          </section>
        </div>

        <aside className="pp-side" aria-label="People, details and sites">
          <Contacts people={data.people} usually={data.usually} canEdit={can.edit} name={customer.site || customer.name}
                    onSave={(f: ContactFields) => change(
                      () => api.post(`/api/customers/${f.customer_id || customerId}/contacts${f.contact_id ? `/${f.contact_id}` : ''}`, f),
                      f.contact_id ? `${f.name} saved` : `${f.name || f.email} added`)}
                    onDelete={(p) => void change(() => api.del(`/api/customers/${p.customer_id}/contacts/${p.contact_id}`),
                                                 `${p.name} removed`)} />
          <Details data={data} />
          {(data.sites.length > 0 || data.links.add_site) && <Sites data={data} />}
        </aside>
      </div>
      <p className="sr-only" role="status" aria-live="polite">{notice}</p>
    </div>
  );
}

function Projects({ data }: { data: CustomerData }) {
  const [all, setAll] = useState(false);
  const open = data.projects.filter((p) => p.status === 'open');
  const closed = data.projects.filter((p) => p.status !== 'open');
  const rows = all ? data.projects : open;
  const withSites = data.sites.length > 0;
  if (!data.projects.length) {
    return (
      <div className="card-body">
        <p className="text-tertiary pp-empty">No projects yet.</p>
        {data.links.new_project && <a className="btn btn-secondary btn-sm cp-gap" href={data.links.new_project}>New project</a>}
      </div>
    );
  }
  return (
    <>
      {rows.length === 0 && <div className="card-body"><p className="text-tertiary pp-empty">No open projects.</p></div>}
      <ul className="cp-rows">
        {rows.map((r) => (
          <li key={r.id}>
            <a href={r.url} className="cp-row">
              <span className="cp-row-main">
                <span className="cp-row-title">{r.title}</span>
                <span className="cell-secondary">
                  {[r.label, withSites && r.customer.site, r.status !== 'open' && data.statuses[r.status]].filter(Boolean).join(' · ')}
                </span>
              </span>
              <span className={`pp-tag tone-${r.pill.tone}`}>{r.pill.text}</span>
              <span className="cp-row-next">{r.status === 'open' ? (r.action ?? r.next) : ''}</span>
              <span className={`cp-row-amount${r.due ? ' is-due' : ''}`}>
                {r.due ? `${money(r.due, r.currency)} due` : r.quoted ? money(r.quoted, r.currency) : ''}
              </span>
            </a>
          </li>
        ))}
      </ul>
      {closed.length > 0 && (
        <div className="card-body cp-more">
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setAll(!all)}>
            {all ? 'Hide finished projects' : `Show ${closed.length} finished project${closed.length === 1 ? '' : 's'}`}
          </button>
        </div>
      )}
    </>
  );
}

function Documents({ data }: { data: CustomerData }) {
  const [only, setOnly] = useState('');
  const sales = data.can.sales;
  const kind = (t: string) => (t === 'export_invoice' ? 'invoice' : t);
  const docs = data.documents.filter((d) => !only || kind(d.doc_type) === only);
  if (!data.documents.length) return <div className="card-body"><p className="text-tertiary pp-empty">No documents yet.</p></div>;
  return (
    <>
      {!sales && (
        <div className="card-body cp-filter-row">
          <div className="segmented" role="group" aria-label="Show">
          {DOC_FILTERS.map((f) => {
            const n = data.documents.filter((d) => !f.key || kind(d.doc_type) === f.key).length;
            return (
              <button key={f.key} type="button" className={`filter-btn${only === f.key ? ' active' : ''}`} aria-pressed={only === f.key}
                      onClick={() => setOnly(f.key)} disabled={!n && !!f.key}>
                {f.label} <span className="cp-count">{n}</span>
              </button>
            );
          })}
          </div>
        </div>
      )}
      <div className="table-container cp-table-wrap">
        <table className="table cp-table cp-docs">
          <thead><tr><th>Number</th><th>Date</th><th>Status</th><th className="num">Total</th>{!sales && <th className="num">Due</th>}</tr></thead>
          <tbody>
            {docs.map((d) => {
              const s = status(d);
              return (
                <tr key={d.invoice_id}>
                  <td>
                    <a href={d.url} className="cell-primary">{d.number}</a>
                    <span className="cell-secondary">{[d.kind, data.sites.length > 0 && d.site].filter(Boolean).join(' · ')}
                      {d.versions.length > 0 && ` · ${d.versions.length + 1} versions`}</span>
                  </td>
                  <td className="cp-date">{day(d.issue_date) || '—'}</td>
                  <td><span className={`pp-tag tone-${s.tone}`}>{s.text}</span></td>
                  <td className="num">{money(d.total, d.currency)}</td>
                  {!sales && <td className={`num${d.balance ? ' is-due' : ''}`}>{d.balance ? money(d.balance, d.currency) : ''}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Files({ data }: { data: CustomerData }) {
  if (!data.files.length) {
    return <div className="card-body"><p className="text-tertiary pp-empty">No files yet. Drawings, POs and email attachments go in a project.</p></div>;
  }
  return (
    <div className="cp-file-groups">
      {data.files.map((g, i) => (
        <details key={g.project?.id ?? 'none'} className="cp-file-group" open={i === 0}>
          <summary>
            <span className="cp-row-title">{g.project ? g.project.title : 'Not in a project'}</span>
            <span className="cell-secondary">{[g.project?.label, `${g.files.length} file${g.files.length === 1 ? '' : 's'}`].filter(Boolean).join(' · ')}</span>
          </summary>
          {g.project?.url && <a className="btn btn-ghost btn-xs cp-open" href={g.project.url}>Open the project</a>}
          <ul className="pp-files">
            {g.files.map((f) => (
              <li key={f.id}>
                <span className="pp-file-icon" aria-hidden="true"><Icon name={f.kind === 'po' ? 'file' : 'paperclip'} size={14} /></span>
                <div className="pp-file-main">
                  <a href={f.url} className="pp-file-name">{f.title || f.name}</a>
                  <div className="pp-person-sub">
                    <span className="pp-tag tone-draft">{f.kind_label}</span>{' '}
                    {[f.reference_no && `No. ${f.reference_no}`, day(f.date), f.size, f.from_email && 'from email'].filter(Boolean).join(' · ')}
                  </div>
                </div>
                <a href={f.url} className="btn btn-ghost btn-xs" aria-label={`Download ${f.name}`}><Icon name="download" size={14} /></a>
              </li>
            ))}
          </ul>
        </details>
      ))}
    </div>
  );
}

function Details({ data }: { data: CustomerData }) {
  const c = data.customer;
  return (
    <section className="card pp-card" aria-labelledby="cp-details">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="cp-details">Details</h2>
        {data.links.edit && <a className="btn btn-ghost btn-xs" href={data.links.edit}><Icon name="pencil" size={14} />Edit</a>}
      </div>
      <div className="card-body">
        <dl className="cp-details">
          <div><dt>GSTIN / Tax ID</dt><dd>{c.tax_id || '—'}</dd></div>
          {c.address.length > 0 && <div><dt>Address</dt><dd>{c.address.map((line) => <span key={line}>{line}</span>)}</dd></div>}
          {c.email_domains && <div><dt>Email domains</dt><dd>{c.email_domains}</dd></div>}
          {c.custom.map((f) => <div key={f.label}><dt>{f.label}</dt><dd>{f.value}</dd></div>)}
        </dl>
        <p className="cp-note cp-gap">The customer portal and archiving are on the <a href={c.classic_url}>classic page</a>.</p>
      </div>
    </section>
  );
}

function Sites({ data }: { data: CustomerData }) {
  return (
    <section className="card pp-card" aria-labelledby="cp-sites">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="cp-sites">Sites</h2>
        {data.links.add_site && <a className="btn btn-ghost btn-xs" href={data.links.add_site}>Add site</a>}
      </div>
      {data.sites.length ? (
        <ul className="cp-rows">
          {data.sites.map((s) => (
            <li key={s.id}>
              <a href={s.url} className="cp-row cp-site">
                <span className="cp-row-main">
                  <span className="cp-row-title">{s.name}</span>
                  <span className="cell-secondary">{[s.tax_id || 'No GSTIN', s.archived && 'Archived'].filter(Boolean).join(' · ')}</span>
                </span>
                <span className="cp-count">{s.documents}</span>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <div className="card-body"><p className="text-tertiary pp-empty">Plants, branches or sister companies billed separately go here.</p></div>
      )}
    </section>
  );
}
