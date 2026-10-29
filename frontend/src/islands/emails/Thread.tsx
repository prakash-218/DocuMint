import { useEffect, useState } from 'react';
import { api } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { when } from '../../format';
import { Icon } from '../../icons';
import type { ProjectOption, Thread as Data } from './types';

// An email thread: its messages oldest first with their files, and the project it's in. Adding it to a project (or
// moving or taking it out) posts project_id to emails_bp.link_project, which also adds or takes away its files.

function ProjectCard({ data }: { data: Data }) {
  const p = data.project;
  const [open, setOpen] = useState(!p);
  const [options, setOptions] = useState<ProjectOption[] | null>(null);
  useEffect(() => {
    if (!open || options) return;
    api.get<{ projects: ProjectOption[] }>(data.link.options).then((r) => setOptions(r.projects)).catch(() => setOptions([]));
  }, [open, options, data.link.options]);
  // The customer's own projects first, as the server page's picker put them
  const mine = data.customer?.id;
  const others = (options ?? []).filter((o) => o.id !== p?.id)
    .sort((a, b) => Number(b.customer_id === mine) - Number(a.customer_id === mine));
  return (
    <div className="card">
      <div className="card-header"><h2 className="card-title">Project</h2></div>
      <div className="card-body">
        {p && (
          <p style={{ margin: '0 0 var(--spacing-sm)' }}>
            <a href={p.url}><strong>{p.title}</strong></a><br />
            <span className="text-tertiary" style={{ fontSize: 'var(--font-size-xs)' }}>{p.label}</span>
          </p>
        )}
        <details className="pp-toggle" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
          <summary className="btn btn-secondary btn-sm">{p ? 'Move to another project' : 'Add to a project'}</summary>
          {options === null ? <p className="text-tertiary" style={{ fontSize: 13 }}>Loading projects…</p> : (
            <>
              {others.length > 0 ? (
                <form method="post" action={data.link.action} className="stack-form">
                  <label htmlFor="thread-project" className="form-label">{p ? 'Move it to' : 'Put it in'}</label>
                  <div className="add-existing-row">
                    <select id="thread-project" name="project_id" className="form-select" required defaultValue="">
                      <option value="" disabled>Choose a project</option>
                      {others.map((o) => <option key={o.id} value={o.id}>{o.no} · {o.title}{o.fy ? ` · FY ${o.fy}` : ''}{o.status !== 'open' ? ` (${o.status})` : ''}</option>)}
                    </select>
                    <button type="submit" className="btn btn-secondary btn-sm">{p ? 'Move' : 'Add'}</button>
                  </div>
                </form>
              ) : <p className="text-tertiary" style={{ fontSize: 13 }}>No {p ? 'other ' : ''}projects yet.</p>}
              {p && (
                <div className="pp-actions">
                  <form method="post" action={data.link.action} style={{ display: 'inline' }}>
                    <button type="submit" name="project_id" value="" className="link-button">Remove from the project</button>
                  </form>
                </div>
              )}
            </>
          )}
        </details>
        {data.link.auto && <p className="form-text">{data.link.auto}</p>}
      </div>
    </div>
  );
}

function ThreadView({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title} heading
                  description={<>
                    {data.count} message{data.count === 1 ? '' : 's'}
                    {data.customer && <> · <a href={data.customer.url}>{data.customer.name}</a></>}
                    {data.project && <> · <a href={data.project.url}>{data.project.label} · {data.project.title}</a></>}
                  </>}
                  actions={<a href={data.back} className="btn btn-ghost"><Icon name="arrowLeft" /><span className="btn-label">Back</span></a>} />
      <div className="invoice-layout">
        <div className="stack">
          {data.messages.map((m) => (
            <article key={m.id} className={`card email-message${m.outgoing ? ' is-outgoing' : ''}`}>
              <header className="email-head">
                <div>
                  <strong>{m.from_name || m.from_address}</strong> <span className="text-tertiary">&lt;{m.from_address}&gt;</span>
                  <div className="email-to text-tertiary">To {m.to}{m.cc && ` · Cc ${m.cc}`}</div>
                </div>
                <time className="text-tertiary" dateTime={m.sent_at ?? undefined}>{when(m.sent_at)}</time>
              </header>
              <div className="email-body">{m.body}</div>
              {m.files.length > 0 && (
                <ul className="email-files">
                  {m.files.map((f) => (
                    <li key={f.url}><a href={f.url} target="_blank" rel="noopener"><Icon name="paperclip" />{f.name}</a>{' '}
                      <span className="text-tertiary">{f.size}</span></li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>
        <aside><ProjectCard data={data} /></aside>
      </div>
    </>
  );
}

export default function Thread({ threadId }: { threadId: string }) {
  const { data, error } = useLoad<Data>(`/api/emails/${threadId}`, "Couldn't load the email. Check your connection.");
  return data ? <ThreadView data={data} /> : <Loading title="Email" kind="page" error={error} heading />;
}
