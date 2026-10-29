import { useId, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { api, ApiError } from '../api';
import { Icon } from '../icons';
import './EmailComposer.css';

// An "Email" button that opens the email form for a project: who it goes to (the project's people), the
// thread it replies in, the documents attached as PDFs. It sends through POST /api/projects/<id>/emails.

export interface Person {
  name: string;
  email: string;
  role?: string | null;
  gets?: string | null;
}

export interface Thread {
  thread_id: string;
  subject: string;
  last_message_at?: string | null;
}

export interface Doc {
  invoice_id: string;
  doc_type: string;
  label: string;
  why_not?: string | null;
}

/** GET /api/projects/<id>/compose (mailsend.compose_context) */
export interface Compose {
  from: string | null;
  from_name: string;
  can_send: boolean;
  why_not: string | null;
  people: Person[];
  found: Person[];
  to: string[];
  cc: string[];
  threads: Thread[];
  thread_id: string | null;
  subject: string;
  new_subject: string;
  body: string;
  documents: Doc[];
  attach: string[];
}

interface Sent {
  thread_id: string | null;
  to: string[];
  cc: string[];
  attached: string[];
  saved_to: string | null;
}

interface Props {
  projectId: string;
  invoiceId?: string;
  threadId?: string;
  label?: string;
}

const EMAIL = /^[^@\s,;<>"]+@[^@\s,;<>"]+\.[^@\s,;<>"]+$/;
const replySubject = (subject: string) => (/^\s*re\s*:/i.test(subject) ? subject : `Re: ${subject}`);

export default function EmailComposer({ projectId, invoiceId, threadId, label = 'Email' }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const id = useId();
  const [context, setContext] = useState<Compose | null>(null);
  const [loadError, setLoadError] = useState('');
  const [to, setTo] = useState<string[]>([]);
  const [cc, setCc] = useState<string[]>([]);
  const [thread, setThread] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [attach, setAttach] = useState<string[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState<Sent | null>(null);

  async function open() {
    setContext(null);
    setLoadError('');
    setError('');
    setSent(null);
    dialog.current?.showModal();
    const query = new URLSearchParams();
    if (invoiceId) query.set('invoice_id', invoiceId);
    if (threadId) query.set('thread_id', threadId);
    try {
      const c = await api.get<Compose>(`/api/projects/${projectId}/compose?${query}`);
      setContext(c);
      setTo(c.to);
      setCc(c.cc);
      setThread(c.thread_id ?? '');
      setSubject(c.subject);
      setBody(c.body);
      setAttach(c.attach);
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Couldn't load the email form. Check your connection.");
    }
  }

  function pickThread(threadId: string) {
    setThread(threadId);
    const picked = context?.threads.find((t) => t.thread_id === threadId);
    setSubject(picked ? replySubject(picked.subject) : (context?.new_subject ?? subject));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!to.length) {
      setError('Add at least one person in To.');
      return;
    }
    setSending(true);
    setError('');
    try {
      setSent(await api.post<Sent>(`/api/projects/${projectId}/emails`,
                                   { to, cc, subject, body, thread_id: thread || null, invoice_ids: attach }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send. Check your connection and try again.");
    } finally {
      setSending(false);
    }
  }

  const known = context ? [...context.people, ...context.found.map((p) => ({ ...p, role: 'found in emails' }))] : [];
  const nameOf = (email: string) => known.find((p) => p.email === email)?.name ?? email;

  return (
    <>
      <button type="button" className="btn btn-secondary" onClick={open}>
        <Icon name="mail" />
        <span className="btn-label">{label}</span>
      </button>
      <dialog ref={dialog} className="k-dialog dm-composer" aria-labelledby={`${id}-title`}
              onClose={() => { if (sent) window.location.reload(); }}>
        <form onSubmit={submit} noValidate>
          <div className="k-dialog-head">
            <h2 id={`${id}-title`}>{sent ? 'Sent' : 'Email'}</h2>
            <button type="button" className="btn btn-ghost btn-xs" onClick={() => dialog.current?.close()} aria-label="Close">
              <Icon name="x" />
            </button>
          </div>

          <div className="k-dialog-body">
            {loadError && <p className="dm-error" role="alert">{loadError}</p>}
            {!context && !loadError && <p className="text-tertiary">Loading…</p>}

            {context && sent && (
              <div className="dm-sent">
                <span className="dm-sent-icon"><Icon name="check" size={20} /></span>
                <div>
                  <p className="dm-sent-title">Sent to {sent.to.map(nameOf).join(', ')}</p>
                  {sent.cc.length > 0 && <p>Copied: {sent.cc.map(nameOf).join(', ')}</p>}
                  {sent.attached.length > 0 && <p>Attached: {sent.attached.join(', ')}</p>}
                  <p className="text-tertiary">
                    {sent.saved_to ? `A copy is in the mailbox's ${sent.saved_to} folder. ` : ''}Replies come back to this project.
                  </p>
                </div>
              </div>
            )}

            {context && !sent && (
              <>
                {!context.can_send && (
                  <p className="dm-notice"><Icon name="info" />{context.why_not}</p>
                )}
                <div className="dm-field">
                  <span className="dm-field-label">From</span>
                  <span>{context.from_name}{context.from ? ` · ${context.from}` : ''}</span>
                </div>
                <Recipients id={`${id}-to`} label="To" value={to} onChange={setTo} known={known} />
                <Recipients id={`${id}-cc`} label="Cc" value={cc} onChange={setCc} known={known} />
                {context.threads.length > 0 && (
                  <div className="dm-field">
                    <label htmlFor={`${id}-thread`} className="dm-field-label">Thread</label>
                    <select id={`${id}-thread`} className="form-select" value={thread} onChange={(e) => pickThread(e.target.value)}>
                      <option value="">New email</option>
                      {context.threads.map((t) => (
                        <option key={t.thread_id} value={t.thread_id}>Reply in: {t.subject}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="dm-field">
                  <label htmlFor={`${id}-subject`} className="dm-field-label">Subject</label>
                  <input id={`${id}-subject`} className="form-input" value={subject} maxLength={300}
                         onChange={(e) => setSubject(e.target.value)} />
                </div>
                <label htmlFor={`${id}-body`} className="sr-only">Message</label>
                <textarea id={`${id}-body`} className="form-textarea dm-body" value={body} rows={9}
                          onChange={(e) => setBody(e.target.value)} />
                {context.documents.length > 0 && (
                  <fieldset className="dm-attach">
                    <legend>Attach as PDF</legend>
                    {context.documents.map((d) => (
                      <label key={d.invoice_id} className={d.why_not ? 'is-off' : ''}>
                        <input type="checkbox" disabled={!!d.why_not} checked={attach.includes(d.invoice_id)}
                               onChange={(e) => setAttach(e.target.checked ? [...attach, d.invoice_id]
                                                                           : attach.filter((x) => x !== d.invoice_id))} />
                        <Icon name="paperclip" size={14} />
                        <span>{d.label}</span>
                        {d.why_not && <span className="text-tertiary"> · {d.why_not}</span>}
                      </label>
                    ))}
                  </fieldset>
                )}
                {error && <p className="dm-error" role="alert">{error}</p>}
              </>
            )}
          </div>

          <div className="k-dialog-foot">
            {sent ? (
              <button type="button" className="btn btn-primary" onClick={() => dialog.current?.close()}>Done</button>
            ) : (
              <>
                <span className="dm-foot-note">{context?.from ? 'Replies come back to this project.' : ''}</span>
                <button type="button" className="btn btn-ghost" onClick={() => dialog.current?.close()}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={!context?.can_send || sending}>
                  <Icon name="send" />
                  {sending ? 'Sending…' : 'Send'}
                </button>
              </>
            )}
          </div>
        </form>
      </dialog>
    </>
  );
}

interface RecipientsProps {
  id: string;
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  known: Person[];
}

/** Chips for the people an email goes to; type an address (Enter, comma or leaving the box adds it) or pick one. */
export function Recipients({ id, label, value, onChange, known }: RecipientsProps) {
  const [draft, setDraft] = useState('');
  const [problem, setProblem] = useState('');
  const options = known.filter((p) => !value.includes(p.email));

  function add(raw: string) {
    const parts = raw.split(/[,;\s]+/).map((s) => s.trim().toLowerCase()).filter(Boolean);
    const bad = parts.find((p) => !EMAIL.test(p));
    if (bad) {
      setProblem(`"${bad}" isn't an email address.`);
      return;
    }
    onChange([...value, ...parts.filter((p, i) => !value.includes(p) && parts.indexOf(p) === i)]);
    setDraft('');
    setProblem('');
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if ((e.key === 'Enter' || e.key === ',' || e.key === ';') && draft.trim()) {
      e.preventDefault();
      add(draft);
    } else if (e.key === 'Backspace' && !draft && value.length) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="dm-field">
      <label htmlFor={id} className="dm-field-label">{label}</label>
      <div className="dm-recipients">
        {value.map((email) => {
          const person = known.find((p) => p.email === email);
          return (
            <span className="dm-chip" key={email} title={email}>
              <span>{person ? `${person.name} · ${email}` : email}</span>
              <button type="button" onClick={() => onChange(value.filter((v) => v !== email))}
                      aria-label={`Remove ${person?.name ?? email}`}>
                <Icon name="x" size={12} />
              </button>
            </span>
          );
        })}
        <input id={id} list={`${id}-people`} type="text" inputMode="email" autoComplete="off" value={draft}
               placeholder={value.length ? '' : 'Name or email'} onKeyDown={onKeyDown}
               onBlur={() => { if (draft.trim()) add(draft); }}
               onChange={(e) => {
                 const typed = e.target.value;
                 if (options.some((o) => o.email === typed)) {      // picked from the list
                   onChange([...value, typed]);
                   setDraft('');
                 } else {
                   setDraft(typed);
                 }
               }} />
        <datalist id={`${id}-people`}>
          {options.map((p) => (
            <option key={p.email} value={p.email}>{p.name}{p.role ? ` · ${p.role}` : ''}</option>
          ))}
        </datalist>
      </div>
      {problem && <span className="dm-error-inline" role="alert">{problem}</span>}
    </div>
  );
}
