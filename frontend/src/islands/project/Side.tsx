import { useId, useState, type FormEvent } from 'react';
import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Page } from './types';

/** The project's files (drawings, POs, email attachments) and a way to add one. */
export function Files({ page }: { page: Page }) {
  const { files, upload, project } = page;
  const id = useId();
  return (
    <section className="card pp-card" aria-labelledby="pp-files">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="pp-files">Files</h2>
        <span className="text-tertiary">{files.length || ''}</span>
      </div>
      {files.length > 0 && (
        <ul className="pp-files">
          {files.map((f) => (
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
      )}
      {upload && (
        <form className="card-body pp-upload" method="post" action={upload.action} encType="multipart/form-data">
          <input type="hidden" name="project_id" value={project.id} />
          <label htmlFor={`${id}-kind`} className="sr-only">What it is</label>
          <select id={`${id}-kind`} name="kind" className="form-select" defaultValue="drawing">
            {Object.entries(upload.kinds).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
          </select>
          <label htmlFor={`${id}-file`} className="sr-only">File</label>
          <input id={`${id}-file`} type="file" name="file" required className="pp-file-input" />
          <button type="submit" className="btn btn-secondary btn-sm"><Icon name="upload" size={14} />Upload</button>
        </form>
      )}
    </section>
  );
}

/** Owners and admins: the costing sheets behind the quoted price. */
export function Costings({ costings }: { costings: NonNullable<Page['costings']> }) {
  return (
    <section className="card pp-card" aria-labelledby="pp-costings">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="pp-costings">Costing</h2>
        <span className="pp-tag tone-draft">Owners and admins</span>
      </div>
      <div className="card-body">
        {costings.length === 0 && <p className="text-tertiary pp-empty">No costing for this project.</p>}
        <ul className="pp-costings">
          {costings.map((k) => (
            <li key={k.id}>
              <a href={k.url}>{k.title}</a>{k.quote_number && <span className="text-tertiary"> · {k.quote_number}</span>}
              <div className="pp-person-sub">
                Cost {money(k.cost, k.currency)} · price {money(k.price, k.currency)}
                {k.profit_on_cost !== null && <> · <b>{k.profit_on_cost}%</b> on cost</>}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export interface DetailFields {
  title: string;
  reference: string;
  fiscal_year: string;
  status: string;
  notes: string;
}

/** Read-only until Edit, instead of a form that's always open. */
export function Details({ page, onSave }: { page: Page; onSave: (fields: DetailFields) => Promise<boolean> }) {
  const { project, can, years, statuses } = page;
  const id = useId();
  const [editing, setEditing] = useState<DetailFields | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setSaving(true);
    if (await onSave(editing)) setEditing(null);
    setSaving(false);
  }

  return (
    <section className="card pp-card" aria-labelledby="pp-details">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="pp-details">Details</h2>
        {can.edit && !editing && (
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setEditing({
            title: project.title, reference: project.reference, fiscal_year: project.fiscal_year, status: project.status, notes: project.notes,
          })}><Icon name="pencil" size={14} />Edit</button>
        )}
      </div>
      <div className="card-body">
        {editing ? (
          <form className="pp-contact-form" onSubmit={submit}>
            <label htmlFor={`${id}-title`} className="form-label">Name</label>
            <input id={`${id}-title`} className="form-input" value={editing.title} maxLength={200} required
                   onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
            <label htmlFor={`${id}-ref`} className="form-label">Customer reference</label>
            <input id={`${id}-ref`} className="form-input" value={editing.reference} maxLength={100}
                   onChange={(e) => setEditing({ ...editing, reference: e.target.value })} />
            <label htmlFor={`${id}-fy`} className="form-label">Financial year</label>
            <select id={`${id}-fy`} className="form-select" value={editing.fiscal_year}
                    onChange={(e) => setEditing({ ...editing, fiscal_year: e.target.value })}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <label htmlFor={`${id}-status`} className="form-label">Status</label>
            <select id={`${id}-status`} className="form-select" value={editing.status}
                    onChange={(e) => setEditing({ ...editing, status: e.target.value })}>
              {Object.entries(statuses).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
            </select>
            <label htmlFor={`${id}-notes`} className="form-label">Notes</label>
            <textarea id={`${id}-notes`} className="form-textarea" rows={3} value={editing.notes}
                      onChange={(e) => setEditing({ ...editing, notes: e.target.value })} />
            <div className="pp-form-actions">
              <button type="submit" className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </form>
        ) : (
          <dl className="pp-facts">
            <div><dt>Customer</dt><dd><a href={project.customer.url}>{project.customer.name}</a>
              {project.customer.site && ` · ${project.customer.site}`}</dd></div>
            <div><dt>Their reference</dt><dd>{project.reference || project.po?.number && `PO ${project.po.number}` || '—'}</dd></div>
            {project.po && (
              <div><dt>Purchase order</dt><dd>{project.po.number}{project.po.date && ` · ${day(project.po.date)}`}
                {project.po.amount ? ` · ${money(project.po.amount, project.po.currency)}` : ''}</dd></div>
            )}
            <div><dt>Financial year</dt><dd>{project.fiscal_year}</dd></div>
            <div><dt>Status</dt><dd>{statuses[project.status]}</dd></div>
            {can.read_mail && (
              <div><dt>Email code</dt><dd><code>{project.label}</code> in a subject puts the email here</dd></div>
            )}
            {project.notes && <div><dt>Notes</dt><dd className="pp-notes">{project.notes}</dd></div>}
          </dl>
        )}
      </div>
    </section>
  );
}
