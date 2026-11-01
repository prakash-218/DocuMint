import { useState, type FormEvent } from 'react';
import { Dropdown } from '../../mantine/Dropdown';
import { money, when } from '../../format';
import { Icon, type IconName } from '../../icons';
import { DocBox } from './Documents';
import type { Doc, Page, ThreadItem, TimelineItem } from './types';

// Everything on the job in one thread, newest first (project_view.thread): each document once, sold or bought, with
// what happened to it folded in; payments, emails, notes and the rest as entries of their own. Filters by kind; a note
// or an email from the top; the documents that can be started for it.

type Filter = 'all' | 'document' | 'payment' | 'email' | 'note';
const SHOWN = 10;
const NEW: [keyof Page['new_document'], string][] = [['quote', 'New quotation'], ['proforma', 'New proforma'], ['invoice', 'New invoice'],
                                                     ['purchase_order', 'New purchase order']];

const sortOf = (i: ThreadItem): Filter =>
  i.type === 'document' ? 'document' : i.type === 'email' ? 'email' : i.type === 'note' ? 'note' : i.kind === 'payment' ? 'payment' : 'all';

function icon(item: TimelineItem): IconName {
  if (item.type === 'email') return item.direction === 'out' ? 'send' : 'mail';
  if (item.type === 'note') return 'note';
  if (item.kind === 'payment') return 'rupee';
  if (item.kind === 'file_uploaded') return 'paperclip';
  if (item.kind?.startsWith('quote_') || item.kind?.startsWith('document_')) return 'file';
  return 'flag';
}

/** The prototype's colour for each kind of entry: emails blue, payments green, notes amber, documents violet. */
function tint(item: TimelineItem): string {
  if (item.type === 'email') return 't-email';
  if (item.type === 'note') return 't-note';
  if (item.kind === 'payment') return 't-pay';
  if (item.kind?.startsWith('quote_') || item.kind?.startsWith('document_')) return 't-doc';
  return '';
}

interface Props {
  page: Page;
  onNote: (text: string) => Promise<boolean>;
  onReply: (threadId: string) => void;
  /** The email form: for a document, or a new email when there's none. */
  onEmail: (invoiceId?: string) => void;
}

export function Thread({ page, onNote, onReply, onEmail }: Props) {
  const { can } = page;
  const [filter, setFilter] = useState<Filter>('all');
  const [all, setAll] = useState(false);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const docs = new Map<string, Doc>([...page.documents, ...(page.purchases ?? [])].map((d) => [d.invoice_id, d]));
  const items = page.timeline.filter((i) => i.type !== 'document' || docs.has(i.invoice_id));
  const count = (f: Filter) => items.filter((i) => sortOf(i) === f).length;
  const filters = ([['all', 'All'], ['document', 'Documents'], ['payment', 'Payments'],
                    ...(can.read_mail ? [['email', 'Emails']] : []), ['note', 'Notes']] as [Filter, string][])
    .filter(([key]) => key === 'all' || count(key) > 0);
  const shown = items.filter((i) => filter === 'all' || sortOf(i) === filter);
  const visible = all ? shown : shown.slice(0, SHOWN);
  const starts = can.edit ? NEW.filter(([key]) => page.new_document[key]) : [];
  const addable = can.edit && page.links?.documents ? page.addable ?? [] : [];

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    setSaving(true);
    if (await onNote(note.trim())) setNote('');
    setSaving(false);
  }

  return (
    <section className="card" aria-labelledby="pp-thread">
      <div className="card-h">
        <h2 id="pp-thread">Everything on this job</h2>
        <div className="filters" role="group" aria-label="Show">
          {filters.map(([key, label]) => (
            <button key={key} type="button" className="chip" aria-pressed={filter === key} onClick={() => setFilter(key)}>
              {label}{key !== 'all' && <span className="chip-n" aria-hidden="true">{count(key)}</span>}
            </button>
          ))}
        </div>
      </div>
      <div className="card-b">
        {starts.length > 0 && (
          <div className="thread-new">
            {starts.map(([key, label]) => (
              <a key={key} className="btn btn-secondary btn-sm" href={page.new_document[key]}><Icon name="plus" size={14} />{label}</a>
            ))}
          </div>
        )}
        {can.edit && (
          <form className="composer-row" onSubmit={add}>
            <label htmlFor="pp-note" className="sr-only">Add a note</label>
            <textarea id="pp-note" rows={1} value={note} maxLength={4000}
                      placeholder="Add a note" onChange={(e) => setNote(e.target.value)} />
            <button type="submit" className="btn btn-secondary" disabled={saving || !note.trim()}>{saving ? 'Adding…' : 'Add note'}</button>
            <button type="button" className="btn btn-secondary" onClick={() => onEmail()}><Icon name="mail" />Email</button>
          </form>
        )}
        {visible.length === 0 && <p className="empty-feed">Nothing here yet.</p>}
        <ul className="feed">
          {visible.map((item) => (item.type === 'document' ? (
            <li key={item.id} className="ev t-doc ev-doc">
              <span className="ico" aria-hidden="true"><Icon name={item.purchase ? 'shoppingCart' : 'file'} size={14} /></span>
              <div style={{ minWidth: 0 }}>
                <DocBox doc={docs.get(item.invoice_id)!} canEdit={can.edit} onEmail={item.purchase ? undefined : (id) => onEmail(id)}
                        documentsUrl={item.purchase ? null : page.links?.documents} />
                {item.history.length > 0 && (
                  <div className="ev-by">{item.history[0].title}{item.history[0].who ? ` · ${item.history[0].who}` : ''}</div>
                )}
                {item.history.length > 1 && (
                  <details className="ev-history">
                    <summary>{item.history.length - 1} earlier</summary>
                    <ul>
                      {item.history.slice(1).map((h, k) => (
                        <li key={k}><span>{h.title}{h.who ? ` · ${h.who}` : ''}</span><span className="ev-date">{when(h.when)}</span></li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
              <span className="ev-date">{when(item.when)}</span>
            </li>
          ) : (
            <li key={item.id} className={`ev ${tint(item)}`}>
              <span className="ico" aria-hidden="true"><Icon name={icon(item)} size={14} /></span>
              <div style={{ minWidth: 0 }}>
                <div className="ev-title">
                  {item.link && item.type !== 'note' ? <a href={item.link}>{item.title}</a> : item.title}
                </div>
                {item.body && <div className="ev-body">{item.body}</div>}
                {(item.who || item.files) && (
                  <div className="ev-by">
                    {[item.who, item.files ? `${item.files} attachment${item.files === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ')}
                  </div>
                )}
                {can.edit && can.read_mail && item.type === 'email' && item.direction !== 'out' && item.thread_id && (
                  <div className="ev-act">
                    <button type="button" className="btn btn-secondary btn-xs" onClick={() => onReply(item.thread_id!)}>
                      <Icon name="reply" size={14} />Reply
                    </button>
                  </div>
                )}
              </div>
              <span className="ev-date">{when(item.when)}</span>
            </li>
          )))}
        </ul>
        {shown.length > SHOWN && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAll(!all)}>
            {all ? `Show the latest ${SHOWN}` : `Show all ${shown.length}`}
          </button>
        )}
        {addable.length > 0 && (
          <form method="post" action={page.links!.documents!} className="add-existing">
            <label htmlFor="pp-add-doc" className="muted">Add one of their documents that's in no project</label>
            <div className="add-existing-row">
              <Dropdown id="pp-add-doc" name="invoice_id" required placeholder="Choose a document…"
                        data={addable.map((d) => ({ value: d.invoice_id, label: `${d.number} · ${d.kind}`, sub: money(d.total, d.currency) }))} />
              <button type="submit" className="btn btn-secondary btn-sm">Add</button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}
