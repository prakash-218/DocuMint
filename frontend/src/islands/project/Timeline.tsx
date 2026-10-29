import { useState, type FormEvent } from 'react';
import { when } from '../../format';
import { Icon, type IconName } from '../../icons';
import type { TimelineItem } from './types';

type Filter = 'all' | 'email' | 'note' | 'event';
const SHOWN = 8;

function icon(item: TimelineItem): IconName {
  if (item.type === 'email') return item.direction === 'out' ? 'send' : 'mail';
  if (item.type === 'note') return 'note';
  if (item.kind === 'payment') return 'rupee';
  if (item.kind === 'file_uploaded') return 'paperclip';
  if (item.kind?.startsWith('quote_') || item.kind?.startsWith('document_')) return 'file';
  return 'flag';
}

interface Props {
  items: TimelineItem[];
  canEdit: boolean;
  readMail: boolean;
  onNote: (text: string) => Promise<boolean>;
  onReply: (threadId: string) => void;
}

/** Emails, notes and what happened, newest first, with filters; a note tells whoever comes next what was agreed. */
export function Timeline({ items, canEdit, readMail, onNote, onReply }: Props) {
  const [filter, setFilter] = useState<Filter>('all');
  const [all, setAll] = useState(false);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const filters: [Filter, string][] = [['all', 'All'], ...(readMail ? [['email', 'Emails'] as [Filter, string]] : []),
                                       ['note', 'Notes'], ['event', 'Activity']];
  const shown = items.filter((i) => filter === 'all' || i.type === filter);
  const visible = all ? shown : shown.slice(0, SHOWN);

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    setSaving(true);
    if (await onNote(note.trim())) setNote('');
    setSaving(false);
  }

  return (
    <section className="card pp-card" aria-labelledby="pp-timeline">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="pp-timeline">Timeline</h2>
        <div className="pp-chips" role="group" aria-label="Show">
          {filters.map(([key, label]) => (
            <button key={key} type="button" className="pp-chip" aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}</button>
          ))}
        </div>
      </div>
      <div className="card-body">
        {canEdit && (
          <form className="pp-note-form" onSubmit={add}>
            <label htmlFor="pp-note" className="sr-only">Add a note</label>
            <textarea id="pp-note" className="form-textarea" rows={2} value={note} maxLength={4000}
                      placeholder="Add a note: a call, what was agreed, what's next" onChange={(e) => setNote(e.target.value)} />
            <button type="submit" className="btn btn-secondary" disabled={saving || !note.trim()}>{saving ? 'Adding…' : 'Add note'}</button>
          </form>
        )}
        {visible.length === 0 && <p className="text-tertiary pp-empty">Nothing here yet.</p>}
        <ul className="pp-feed">
          {visible.map((item) => (
            <li key={item.id} className={`pp-ev type-${item.type}${item.direction === 'out' ? ' is-out' : ''}`}>
              <span className="pp-ev-icon" aria-hidden="true"><Icon name={icon(item)} size={14} /></span>
              <div className="pp-ev-main">
                <div className="pp-ev-title">
                  {item.link && item.type !== 'note' ? <a href={item.link}>{item.title}</a> : item.title}
                </div>
                {item.body && <div className="pp-ev-body">{item.body}</div>}
                <div className="pp-ev-meta">
                  {[item.who, item.files ? `${item.files} attachment${item.files === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ')}
                </div>
                {canEdit && readMail && item.type === 'email' && item.direction !== 'out' && item.thread_id && (
                  <button type="button" className="btn btn-ghost btn-xs pp-reply" onClick={() => onReply(item.thread_id!)}>
                    <Icon name="reply" size={14} />Reply
                  </button>
                )}
              </div>
              <span className="pp-ev-when">{when(item.when)}</span>
            </li>
          ))}
        </ul>
        {shown.length > SHOWN && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setAll(!all)}>
            {all ? `Show the latest ${SHOWN}` : `Show all ${shown.length}`}
          </button>
        )}
      </div>
    </section>
  );
}
