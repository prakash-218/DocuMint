import { Dropdown, choices } from '../../mantine/Dropdown';
import { useId, useState, type FormEvent } from 'react';
import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Page } from './types';

export const ACCEPT = '.pdf,.png,.jpg,.jpeg,.webp,.doc,.docx,.xls,.xlsx,.csv,.txt,.dwg,.dxf,.step,.stp,.igs,.iges,.zip,.eml,.msg';

/** The project's files (drawings, POs, email attachments), and the prototype's drop zone to add more: dropped or
    chosen files are uploaded straight away (static/js/app.js), each one's kind guessed from its name; its tag opens
    a small form to say what it is and its number. */

/** A project status's dot: open (mint), completed (blue), cancelled (grey) */
const STATUS_DOTS: Record<string, string> = { open: 'var(--mint)', completed: 'var(--info)', cancelled: 'var(--neutral)' };

export function Files({ page, onSave }: { page: Page; onSave?: (fileId: string, kind: string, referenceNo: string) => Promise<boolean> }) {
  const { files, upload, project } = page;
  const id = useId();
  const [editing, setEditing] = useState<string | null>(null);
  return (
    <section className="side-sec" aria-labelledby="pp-files">
      <h2 id="pp-files">Files <span className="muted" style={{ fontWeight: 400, fontSize: 12.5 }}>{files.length ? `${files.length} file${files.length === 1 ? '' : 's'}` : ''}</span></h2>
      {files.length > 0 && (
        <ul className="files">
          {files.map((f) => (
            <li key={f.id}>
              <span className="fi" aria-hidden="true"><Icon name={f.kind === 'po' ? 'fileCheck' : 'paperclip'} size={15} /></span>
              <div style={{ minWidth: 0 }}>
                <a href={f.url} className="fn">{f.title || f.name}</a>
                <div className="fs">
                  {upload && onSave ? (
                    <button type="button" className="tag tone-draft tag-button" aria-expanded={editing === f.id}
                            aria-label={`${f.kind_label}: change what ${f.name} is`} onClick={() => setEditing(editing === f.id ? null : f.id)}>
                      {f.kind_label}
                    </button>
                  ) : <span className="tag tone-draft">{f.kind_label}</span>}{' '}
                  {[f.reference_no && `No. ${f.reference_no}`, f.from_email ? 'From email' : '', day(f.date), f.size].filter(Boolean).join(' · ')}
                </div>
                {editing === f.id && upload && onSave && (
                  <FileForm file={f} kinds={upload.kinds} onCancel={() => setEditing(null)}
                            onSave={async (kind, ref) => { const ok = await onSave(f.id, kind, ref); if (ok) setEditing(null); return ok; }} />
                )}
              </div>
              <a href={f.url} className="btn btn-ghost btn-xs" aria-label={`Download ${f.name}`}><Icon name="download" size={14} /></a>
            </li>
          ))}
        </ul>
      )}
      {upload && (
        <form className="drop" data-dropzone method="post" action={upload.action} encType="multipart/form-data">
          <input type="hidden" name="project_id" value={project.id} />
          <input id={`${id}-file`} type="file" name="file" multiple accept={ACCEPT} className="sr-only" />
          <span data-drop-label>Drop files here or <label htmlFor={`${id}-file`} className="linkish">choose files</label></span>
        </form>
      )}
    </section>
  );
}

interface FileFormProps {
  file: Page['files'][number];
  kinds: Record<string, string>;
  onSave: (kind: string, referenceNo: string) => Promise<boolean>;
  onCancel: () => void;
  /** Moving it into one of the customer's projects (projects_bp.link_file), on the customer page. */
  move?: { action: string; projects: { id: string; label: string; title: string }[]; current: string | null };
}

/** What a file is and its number (a PO's goes onto the project's documents), which project it's in, or delete it. */
export function FileForm({ file, kinds, onSave, onCancel, move }: FileFormProps) {
  const id = useId();
  const [kind, setKind] = useState(file.kind);
  const [ref, setRef] = useState(file.reference_no ?? '');
  const [saving, setSaving] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    await onSave(kind, ref);
    setSaving(false);
  }
  return (
    <div className="file-form">
      <form className="stack-form" onSubmit={submit} aria-label={`What ${file.name} is`}>
        <label htmlFor={`${id}-kind`} className="form-label">What it is</label>
        <Dropdown id={`${id}-kind`} value={kind} onChange={setKind} data={choices(Object.entries(kinds))} />
        <label htmlFor={`${id}-ref`} className="form-label">Number <span className="muted">(PO or drawing no.)</span></label>
        <input id={`${id}-ref`} className="form-input" value={ref} maxLength={100} onChange={(e) => setRef(e.target.value)} />
        <div className="form-actions-row">
          <button type="submit" className="btn btn-primary btn-xs" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
          <button type="button" className="btn btn-ghost btn-xs" onClick={onCancel}>Cancel</button>
        </div>
      </form>
      {move && move.projects.length > 0 && (
        <form method="post" action={move.action} className="stack-form">
          <label htmlFor={`${id}-project`} className="form-label">In the project</label>
          <div className="add-existing-row">
            <Dropdown id={`${id}-project`} name="project_id" defaultValue={move.current ?? ''}
                      data={[{ value: '', label: 'Not in a project' }, ...move.projects.map((p) => ({ value: p.id, label: `${p.label} ${p.title}` }))]} />
            <button type="submit" className="btn btn-secondary btn-xs">Move</button>
          </div>
        </form>
      )}
      {file.delete && (
        <form method="post" action={file.delete} onSubmit={(e) => { if (!window.confirm(`Delete ${file.name}? This can't be undone.`)) e.preventDefault(); }}>
          <button type="submit" className="btn btn-ghost btn-xs file-delete"><Icon name="trash" size={14} />Delete the file</button>
        </form>
      )}
    </div>
  );
}

/** Owners and admins: the costing sheets behind the quoted price, a new one, and the rates list. */
export function Costings({ costings, projectId, links }: { costings: NonNullable<Page['costings']>; projectId?: string; links?: Page['links'] }) {
  return (
    <section className="side-sec" aria-labelledby="pp-costings">
      <h2 id="pp-costings">Costing <span className="tag tone-draft">Owners and admins</span></h2>
      {costings.length === 0 && <p className="muted" style={{ margin: 0 }}>No costing for this project. Work out the prices before the quotation.</p>}
      {costings.map((k) => (
        <div key={k.id} className="costing">
          <span className="big">Cost {money(k.cost, k.currency)}</span>
          <span>{k.quote_number ? <>Quoted at <span className="mono">{money(k.price, k.currency)}</span> in {k.quote_number}</> : <>Price {money(k.price, k.currency)}</>}
            {k.profit_on_cost !== null && <> leaves <b>{k.profit_on_cost}%</b> on cost</>}</span>
          <small>{k.title}</small>
          <div><a className="btn btn-secondary btn-xs" href={k.url}>Open costing</a></div>
        </div>
      ))}
      {(links?.new_costing || links?.rates) && (
        <div className="form-actions-row" style={{ marginTop: 0 }}>
          {links.new_costing && projectId && (
            <form method="post" action={links.new_costing} className="inline-form">
              <input type="hidden" name="project_id" value={projectId} />
              <button type="submit" className="btn btn-secondary btn-xs">New costing</button>
            </form>
          )}
          {links.rates && <a className="btn btn-ghost btn-xs" href={links.rates}>Rates list</a>}
        </div>
      )}
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
    <section className="side-sec" aria-labelledby="pp-details">
      <h2 id="pp-details">Details
        {can.edit && !editing && (
          <button type="button" className="btn btn-secondary btn-xs" onClick={() => setEditing({
            title: project.title, reference: project.reference, fiscal_year: project.fiscal_year, status: project.status, notes: project.notes,
          })}>Edit</button>
        )}
      </h2>
      {editing ? (
        <form className="stack-form" onSubmit={submit}>
          <label htmlFor={`${id}-title`} className="form-label">Name</label>
          <input id={`${id}-title`} className="form-input" value={editing.title} maxLength={200} required
                 onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
          <label htmlFor={`${id}-ref`} className="form-label">Customer reference</label>
          <input id={`${id}-ref`} className="form-input" value={editing.reference} maxLength={100}
                 onChange={(e) => setEditing({ ...editing, reference: e.target.value })} />
          <label htmlFor={`${id}-fy`} className="form-label">Financial year</label>
          <Dropdown id={`${id}-fy`} value={editing.fiscal_year} onChange={(v) => setEditing({ ...editing, fiscal_year: v })} data={choices(years)} />
          <label htmlFor={`${id}-status`} className="form-label">Status</label>
          <Dropdown id={`${id}-status`} value={editing.status} onChange={(v) => setEditing({ ...editing, status: v })}
                    data={Object.entries(statuses).map(([k, label]) => ({ value: k, label, dot: STATUS_DOTS[k] }))} />
          <label htmlFor={`${id}-notes`} className="form-label">Notes</label>
          <textarea id={`${id}-notes`} className="form-textarea" rows={3} value={editing.notes}
                    onChange={(e) => setEditing({ ...editing, notes: e.target.value })} />
          <div className="form-actions-row">
            <button type="submit" className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </form>
      ) : (
        <dl className="facts">
          <div><dt>Customer</dt><dd><a href={project.customer.url}>{project.customer.name}</a>
            {project.customer.site && ` · ${project.customer.site}`}</dd></div>
          <div><dt>Their reference</dt><dd>{project.reference || project.po?.number && `PO ${project.po.number}` || '—'}</dd></div>
          {project.po && (
            <div><dt>Purchase order</dt><dd><span className="mono">{project.po.number}</span>{project.po.date && ` · ${day(project.po.date)}`}
              {project.po.amount ? ` · ${money(project.po.amount, project.po.currency)}` : ''}</dd></div>
          )}
          <div><dt>Financial year</dt><dd>{project.fiscal_year}</dd></div>
          <div><dt>Status</dt><dd>{statuses[project.status]}</dd></div>
          {can.read_mail && (
            <div><dt>Email code</dt><dd><span className="mono">{project.label}</span> in a subject puts the thread here</dd></div>
          )}
          {project.notes && <div><dt>Notes</dt><dd>{project.notes}</dd></div>}
        </dl>
      )}
      {!editing && page.links?.delete && (
        <form method="post" action={page.links.delete}
              onSubmit={(e) => { if (!window.confirm("Delete this project? Its documents and files are kept; they just won't be grouped any more.")) e.preventDefault(); }}>
          <button type="submit" className="btn btn-ghost btn-xs file-delete"><Icon name="trash" size={14} />Delete the project</button>
        </form>
      )}
    </section>
  );
}
