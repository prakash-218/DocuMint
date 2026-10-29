import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { day, money, totals } from '../../format';
import { Icon } from '../../icons';
import { status } from '../project/Documents';
import type { ContactFields } from '../project/People';
import { ACCEPT, FileForm } from '../project/Side';
import { Contacts } from './Contacts';
import { Statement } from './Money';
import type { CustomerData } from './types';

// The new customer page, as the prototype draws it: who they are and what they owe at the top (the balance,
// and the money due by how old it is), then Overview, Contacts, Documents, Statement and Files, one at a time.

type Tab = 'overview' | 'contacts' | 'documents' | 'statement' | 'files';
const TABS: Tab[] = ['overview', 'contacts', 'documents', 'statement', 'files'];
const DOC_FILTERS = [
  { key: '', label: 'All' },
  { key: 'quote', label: 'Quotations' },
  { key: 'proforma', label: 'Proformas' },
  { key: 'invoice', label: 'Invoices' },
] as const;

function startTab(): Tab {
  return TABS.find((t) => t === window.location.hash.slice(1)) ?? 'overview';
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
    return <div className="ui">{error ? <p className="error" role="alert">{error}</p> : <p className="loading">Loading the customer…</p>}</div>;
  }

  const { customer, can } = data;
  const m = data.money;
  const labels: Record<Tab, string> = {
    overview: 'Overview', contacts: `Contacts (${data.people.length})`, documents: `Documents (${data.documents.length})`,
    statement: 'Statement', files: `Files (${data.files_count})`,
  };
  const tabs = TABS.filter((t) => t !== 'statement' || m);
  const shown = tabs.includes(tab) ? tab : 'overview';
  const pick = (t: Tab) => {
    setTab(t);
    window.history.replaceState(null, '', `#${t}`);
  };
  const balance = Object.fromEntries((m?.statement ?? []).map((a) => [a.currency, a.balance]));

  return (
    <div className="ui">
      {error && (
        <div className="error" role="alert">
          <span>{error}</span>
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setError('')}>Dismiss</button>
        </div>
      )}

      <header className="head">
        <div>
          <h1>{customer.site || customer.name}</h1>
          <div className="meta">
            {customer.site && <span>{customer.parent ? <a href={customer.parent.url}>{customer.parent.name}</a> : customer.name}</span>}
            {customer.tax_id && <span className="mono">{customer.tax_id}</span>}
            {customer.tax_note && <span>{customer.tax_note}</span>}
            {customer.archived && <span>Archived: hidden from the lists</span>}
          </div>
          {m && (
            <div className="ageline" aria-label="Due by how old the invoice is">
              {m.count ? m.ages.filter((a) => a.count).map((a) => (
                <span key={a.label}><i className={`g-${m.ages.indexOf(a)}`} />{a.label} old: <span className="num">{totals(a.total)}</span></span>
              )) : <span>Nothing owed right now</span>}
            </div>
          )}
        </div>
        {m && (
          <div className="balance">
            <small>Balance</small>
            <b>{Object.keys(balance).length ? totals(balance) : money(0)}</b>
            <small>
              {m.count ? `${totals(m.total)} due on ${m.count} invoice${m.count === 1 ? '' : 's'}` : 'Nothing due'}
              {Object.keys(m.advance_held).length > 0 && `, less ${totals(m.advance_held)} advance held`}
            </small>
          </div>
        )}
      </header>

      <div className="tabs" role="tablist" aria-label="About this customer">
        {tabs.map((t) => (
          <button key={t} type="button" role="tab" id={`cp-tab-${t}`} aria-controls="cp-panel" aria-selected={shown === t} onClick={() => pick(t)}>
            {labels[t]}
          </button>
        ))}
      </div>

      <div id="cp-panel" role="tabpanel" aria-labelledby={`cp-tab-${shown}`}>
        {shown === 'overview' && <Overview data={data} />}
        {shown === 'contacts' && (
          <Contacts people={data.people} usually={data.usually} canEdit={can.edit} name={customer.site || customer.name}
                    onSave={(f: ContactFields) => change(
                      () => api.post(`/api/customers/${f.customer_id || customerId}/contacts${f.contact_id ? `/${f.contact_id}` : ''}`, f),
                      f.contact_id ? `${f.name} saved` : `${f.name || f.email} added`)}
                    onDelete={(p) => void change(() => api.del(`/api/customers/${p.customer_id}/contacts/${p.contact_id}`), `${p.name} removed`)} />
        )}
        {shown === 'documents' && <Documents data={data} />}
        {shown === 'statement' && m && <Statement accounts={m.statement} />}
        {shown === 'files' && (
          <Files data={data} onSave={(fileId, kind, referenceNo) => change(() => api.patch(`/api/files/${fileId}`, { kind, reference_no: referenceNo }), 'File saved')} />
        )}
      </div>
      <p className="sr-only" role="status" aria-live="polite">{notice}</p>
    </div>
  );
}

const PROJECT_GRID = { gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1.5fr) 112px 112px' };

function Overview({ data }: { data: CustomerData }) {
  const [all, setAll] = useState(false);
  const open = data.projects.filter((p) => p.status === 'open');
  const closed = data.projects.filter((p) => p.status !== 'open');
  const rows = all ? data.projects : open;
  const sales = data.can.sales;
  const c = data.customer;
  return (
    <>
      {(data.links.new_quote || data.links.new_project) && (
        <div className="toolbar">
          {data.links.new_quote && <a className="btn btn-primary" href={data.links.new_quote}><Icon name="plus" />New quotation</a>}
          {data.links.new_project && <a className="btn btn-secondary" href={data.links.new_project}>New project</a>}
        </div>
      )}
      <div className="rows" aria-label="Projects">
        <div className="rh" style={PROJECT_GRID}>
          <span>{all ? 'Project' : 'Open project'}</span><span>Stage</span><span className="c-num">Quoted</span>
          <span className="c-num">{sales ? '' : 'Due'}</span>
        </div>
        {rows.length === 0 && <p className="empty-rows">{data.projects.length ? 'No open projects.' : 'No projects yet.'}</p>}
        {rows.map((r) => (
          <a key={r.id} className="rr" href={r.url} style={PROJECT_GRID}>
            <div className="c-main">
              <div className="c-title">{r.title}</div>
              <div className="c-sub"><span className="mono">{r.label}</span>{data.sites.length > 0 && r.customer.site ? ` · ${r.customer.site}` : ''}
                {r.status !== 'open' ? ` · ${data.statuses[r.status]}` : ''}</div>
            </div>
            <div><span className={`tag tone-${r.tone}`}>{r.stage_label}</span><div className="c-sub">{r.sub || r.pill.text}</div></div>
            <div className="c-num c-hide">{r.quoted ? money(r.quoted, r.currency) : '—'}</div>
            <div className={`c-num${r.due && r.tone === 'late' ? ' late' : ''}`}>{!sales && <><span className="c-lbl">Due</span>{r.due ? money(r.due, r.currency) : '—'}</>}</div>
          </a>
        ))}
      </div>
      {closed.length > 0 && (
        <div className="toolbar">
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setAll(!all)}>
            {all ? 'Only the open projects' : `Show ${closed.length} finished project${closed.length === 1 ? '' : 's'} too`}
          </button>
        </div>
      )}

      {(data.sites.length > 0 || data.links.add_site) && (
        <section className="card" aria-labelledby="cp-sites" style={{ marginTop: 20 }}>
          <div className="card-h">
            <h2 id="cp-sites">Sites</h2>
            {data.links.add_site && <a className="btn btn-ghost btn-xs" href={data.links.add_site}><Icon name="plus" size={14} />Add site</a>}
          </div>
          {data.sites.length ? data.sites.map((s) => (
            <a key={s.id} className="rr" href={s.url} style={{ gridTemplateColumns: 'minmax(0, 1fr) auto' }}>
              <div className="c-main"><div className="c-title">{s.name}</div>
                <div className="c-sub">{[s.tax_id || 'No GSTIN', s.archived && 'Archived'].filter(Boolean).join(' · ')}</div></div>
              <div className="c-date">{s.documents} document{s.documents === 1 ? '' : 's'}</div>
            </a>
          )) : <div className="card-b muted">Plants, branches or sister companies billed separately go here.</div>}
        </section>
      )}

      <section className="card" aria-labelledby="cp-details" style={{ marginTop: 20 }}>
        <div className="card-h">
          <h2 id="cp-details">Details</h2>
          {data.links.edit && <a className="btn btn-ghost btn-xs" href={data.links.edit}><Icon name="pencil" size={14} />Edit</a>}
        </div>
        <div className="card-b">
          <dl className="facts facts-wide">
            <div><dt>GSTIN</dt><dd className="mono">{c.tax_id || '—'}</dd></div>
            {c.address.length > 0 && <div><dt>Address</dt><dd>{c.address.join('\n')}</dd></div>}
            {c.email_domains && <div><dt>Email domains</dt><dd>{c.email_domains}</dd></div>}
            <div><dt>Payment terms</dt><dd>{c.payment_terms || 'Not set: invoices count as due only when they have a due date'}</dd></div>
            {c.custom.map((f) => <div key={f.label}><dt>{f.label}</dt><dd>{f.value}</dd></div>)}
          </dl>
          {data.portal && <Portal portal={data.portal} />}
          {data.links.archive && (
            <form method="post" action={data.links.archive} style={{ marginTop: 12 }}
                  onSubmit={(e) => { if (!c.archived && !window.confirm(`Archive ${c.site || c.name}? They'll be hidden from the lists; their documents are kept.`)) e.preventDefault(); }}>
              <button type="submit" className="btn btn-ghost btn-xs">{c.archived ? 'Restore the customer' : 'Archive the customer'}</button>
            </form>
          )}
        </div>
      </section>
    </>
  );
}

const DOC_GRID = { gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr) 72px minmax(0, 1fr) 112px' };

function Documents({ data }: { data: CustomerData }) {
  const [only, setOnly] = useState('');
  const kind = (t: string) => (t === 'export_invoice' ? 'invoice' : t);
  const docs = data.documents.filter((d) => !only || kind(d.doc_type) === only);
  const projects = Object.fromEntries(data.projects.map((p) => [p.id, p]));
  if (!data.documents.length) return <div className="rows"><p className="empty-rows" style={{ borderTop: 0 }}>No documents yet.</p></div>;
  return (
    <>
      {!data.can.sales && (
        <div className="toolbar filters" role="group" aria-label="Show">
          {DOC_FILTERS.map((f) => {
            const n = data.documents.filter((d) => !f.key || kind(d.doc_type) === f.key).length;
            return (
              <button key={f.key} type="button" className="chip" aria-pressed={only === f.key} onClick={() => setOnly(f.key)} disabled={!n && !!f.key}>
                {f.label} <span className="mono">{n}</span>
              </button>
            );
          })}
        </div>
      )}
      <div className="rows" aria-label="Documents">
        <div className="rh" style={DOC_GRID}><span>Document</span><span>Project</span><span>Date</span><span>Status</span><span className="c-num">Total</span></div>
        {docs.map((d) => {
          const s = status(d);
          const p = d.project_id ? projects[d.project_id] : undefined;
          return (
            <a key={d.invoice_id} className="rr" href={d.url} style={DOC_GRID}>
              <div className="c-main">
                <div className="c-title mono">{d.number}</div>
                <div className="c-sub">{[d.kind, data.sites.length > 0 && d.site, d.versions.length > 0 && `${d.versions.length + 1} versions`].filter(Boolean).join(' · ')}</div>
              </div>
              <div className="c-sub c-hide">{p ? <><span className="mono">{p.label}</span> {p.title}</> : '—'}</div>
              <div className="c-date">{day(d.issue_date) || '—'}</div>
              <div><span className={`tag tone-${s.tone}`}>{s.text}</span>{d.balance ? <div className="c-sub">{money(d.balance, d.currency)} due</div> : null}</div>
              <div className="c-num">{money(d.total, d.currency)}</div>
            </a>
          );
        })}
      </div>
    </>
  );
}

function Files({ data, onSave }: { data: CustomerData; onSave: (fileId: string, kind: string, referenceNo: string) => Promise<boolean> }) {
  const [editing, setEditing] = useState<string | null>(null);
  const upload = data.upload;
  const projects = data.projects.filter((p) => p.status === 'open');
  return (
    <div style={{ marginTop: 14 }}>
      {upload && (
        <form className="drop" data-dropzone method="post" action={upload.action} encType="multipart/form-data" style={{ marginBottom: 12 }}>
          <input type="hidden" name="customer_id" value={data.customer.id} />
          <input id="cp-file" type="file" name="file" multiple accept={ACCEPT} className="sr-only" />
          <span data-drop-label>Drop files for {data.customer.site || data.customer.name} here or <label htmlFor="cp-file" className="linkish">choose files</label>.
            They go in no project; move them into one from their tag.</span>
        </form>
      )}
      {!data.files.length && <div className="rows"><p className="empty-rows" style={{ borderTop: 0 }}>No files yet.</p></div>}
      {data.files.map((g, i) => (
        <details key={g.project?.id ?? 'none'} className="fgroup" open={i === 0}>
          <summary>
            <span style={{ color: 'inherit', fontSize: 'inherit', fontWeight: 500, whiteSpace: 'normal' }}>
              {g.project ? <><span className="mono">{g.project.label}</span> {g.project.title}</> : 'Not in a project'}
            </span>
            <span>{g.files.length} file{g.files.length === 1 ? '' : 's'}</span>
          </summary>
          <ul className="files">
            {g.files.map((f) => (
              <li key={f.id}>
                <span className="fi" aria-hidden="true"><Icon name={f.kind === 'po' ? 'fileCheck' : 'paperclip'} size={15} /></span>
                <div style={{ minWidth: 0 }}>
                  <a href={f.url} className="fn">{f.title || f.name}</a>
                  <div className="fs">
                    {upload ? (
                      <button type="button" className="tag tone-draft tag-button" aria-expanded={editing === f.id}
                              aria-label={`${f.kind_label}: change what ${f.name} is`} onClick={() => setEditing(editing === f.id ? null : f.id)}>
                        {f.kind_label}
                      </button>
                    ) : <span className="tag tone-draft">{f.kind_label}</span>}{' '}
                    {[f.reference_no && `No. ${f.reference_no}`, f.from_email ? 'From email' : 'Uploaded', day(f.date), f.size].filter(Boolean).join(' · ')}
                  </div>
                  {editing === f.id && upload && (
                    <FileForm file={f} kinds={upload.kinds} onCancel={() => setEditing(null)}
                              onSave={async (kind, ref) => { const ok = await onSave(f.id, kind, ref); if (ok) setEditing(null); return ok; }}
                              move={f.move ? { action: f.move, current: g.project?.id ?? null,
                                               projects: projects.filter((p) => !f.customer_id || p.customer.id === f.customer_id)
                                                 .map((p) => ({ id: p.id, label: p.label, title: p.title })) } : undefined} />
                  )}
                </div>
                <a href={f.url} className="btn btn-ghost btn-xs" aria-label={`Download ${f.name}`}><Icon name="download" size={14} /></a>
              </li>
            ))}
          </ul>
          {g.project?.url && <p style={{ margin: '0 14px 12px' }}><a className="btn btn-ghost btn-xs" href={g.project.url}>Open the project</a></p>}
        </details>
      ))}
    </div>
  );
}

/** Owners and admins: who can sign in to the customer portal, or giving someone a login. */
function Portal({ portal }: { portal: NonNullable<CustomerData['portal']> }) {
  const [open, setOpen] = useState(false);
  if (portal.email) {
    return <p className="muted" style={{ margin: '12px 0 0', fontSize: 13 }}>Customer portal: <b>{portal.email}</b> can sign in at <a href={portal.login_url}>{portal.login_url}</a>.</p>;
  }
  if (!portal.create) return null;
  return open ? (
    <form method="post" action={portal.create} className="stack-form" style={{ marginTop: 12, maxWidth: 360 }}>
      <label htmlFor="cp-portal-email" className="form-label">Their email, to sign in to the customer portal</label>
      <input id="cp-portal-email" type="email" name="email" className="form-input" required />
      <label htmlFor="cp-portal-password" className="form-label">A password for them <span className="muted">(8 characters or more)</span></label>
      <input id="cp-portal-password" type="password" name="password" className="form-input" required minLength={8} autoComplete="new-password" />
      <div className="form-actions-row">
        <button type="submit" className="btn btn-primary btn-xs">Give portal access</button>
        <button type="button" className="btn btn-ghost btn-xs" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </form>
  ) : (
    <p className="muted" style={{ margin: '12px 0 0', fontSize: 13 }}>
      No customer portal login. <button type="button" className="linkish" onClick={() => setOpen(true)}>Give them one</button>
    </p>
  );
}
