import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { Select, Text } from '@mantine/core';
import { api, ApiError } from '../api';
import { Icon } from '../icons';
import { IN_DIALOG } from '../mantine/Mantine';
import { Skeleton } from '../Skeleton';
import './EmailComposer.css';
import { RecipientPicker } from './RecipientPicker';

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

/** An email that isn't a project's (a customer's statement): where the form loads from and sends to, what else
    the send takes, and where replies go. */
export interface Endpoints {
  compose: string;
  send: string;
  extra?: Record<string, unknown>;
  replies?: string;
}

export interface ComposerProps {
  projectId?: string;
  invoiceId?: string | null;
  threadId?: string | null;
  endpoints?: Endpoints;
  /** The form closed; sent says whether an email went out. */
  onClose: (sent: boolean) => void;
}

const replySubject = (subject: string) => (/^\s*re\s*:/i.test(subject) ? subject : `Re: ${subject}`);
const NEW = 'new';            // the Thread picker's "New email"
const shortDay = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

/** The island on today's pages: an Email button; after sending, the page reloads to show it. */
export default function EmailComposer({ projectId, invoiceId, threadId, label = 'Email' }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" className="btn btn-secondary" onClick={() => setOpen(true)}>
        <Icon name="mail" />
        <span className="btn-label">{label}</span>
      </button>
      {open && (
        <Composer projectId={projectId} invoiceId={invoiceId} threadId={threadId}
                  onClose={(sent) => { setOpen(false); if (sent) window.location.reload(); }} />
      )}
    </>
  );
}

/** The email form, open as soon as it's shown. */
export function Composer({ projectId, invoiceId, threadId, endpoints, onClose }: ComposerProps) {
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

  useEffect(() => {
    void open();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function open() {
    if (dialog.current && !dialog.current.open) dialog.current.showModal();
    const query = new URLSearchParams();
    if (invoiceId) query.set('invoice_id', invoiceId);
    if (threadId) query.set('thread_id', threadId);
    try {
      const c = await api.get<Compose>(endpoints?.compose ?? `/api/projects/${projectId}/compose?${query}`);
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
      setSent(await api.post<Sent>(endpoints?.send ?? `/api/projects/${projectId}/emails`,
                                   { to, cc, subject, body, thread_id: thread || null, invoice_ids: attach, ...endpoints?.extra }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send. Check your connection and try again.");
    } finally {
      setSending(false);
    }
  }

  const known = context ? [...context.people, ...context.found] : [];
  const replies = endpoints?.replies ?? 'Replies come back to this project.';
  const nameOf = (email: string) => known.find((p) => p.email === email)?.name ?? email;

  return (
    <>
      <dialog ref={dialog} className="k-dialog dm-composer" aria-labelledby={`${id}-title`}
              onClose={() => onClose(!!sent)}>
        <form onSubmit={submit} noValidate>
          <div className="k-dialog-head">
            <h2 id={`${id}-title`}>{sent ? 'Sent' : 'Email'}</h2>
            <button type="button" className="btn btn-ghost btn-xs" onClick={() => dialog.current?.close()} aria-label="Close">
              <Icon name="x" />
            </button>
          </div>

          <div className="k-dialog-body">
            {loadError && <p className="dm-error" role="alert">{loadError}</p>}
            {!context && !loadError && <Skeleton kind="form" label="Loading the email form…" ui={false} />}

            {context && sent && (
              <div className="dm-sent">
                <span className="dm-sent-icon"><Icon name="check" size={20} /></span>
                <div>
                  <p className="dm-sent-title">Sent to {sent.to.map(nameOf).join(', ')}</p>
                  {sent.cc.length > 0 && <p>Copied: {sent.cc.map(nameOf).join(', ')}</p>}
                  {sent.attached.length > 0 && <p>Attached: {sent.attached.join(', ')}</p>}
                  <p className="text-tertiary">
                    {sent.saved_to ? `A copy is in the mailbox's ${sent.saved_to} folder. ` : ''}{replies}
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
                <RecipientPicker id={`${id}-to`} label="To" value={to} onChange={setTo} people={context.people} found={context.found} />
                <RecipientPicker id={`${id}-cc`} label="Cc" value={cc} onChange={setCc} people={context.people} found={context.found} />
                {context.threads.length > 0 && (
                  <div className="dm-field">
                    <label htmlFor={`${id}-thread`} className="dm-field-label">Thread</label>
                    <Select id={`${id}-thread`} value={thread || NEW} allowDeselect={false} comboboxProps={IN_DIALOG}
                            onChange={(v) => pickThread(v && v !== NEW ? v : '')}
                            data={[{ value: NEW, label: 'New email' },
                                   ...context.threads.map((t) => ({ value: t.thread_id, label: `Reply in: ${t.subject}` }))]}
                            renderOption={({ option }) => {
                              const t = context.threads.find((x) => x.thread_id === option.value);
                              return (
                                <div>
                                  <Text size="sm">{t ? t.subject : option.label}</Text>
                                  <Text size="xs" c="dimmed">{t ? `Reply in this thread${t.last_message_at ? ` · last message ${shortDay(t.last_message_at)}` : ''}`
                                                                : 'Starts a thread of its own'}</Text>
                                </div>
                              );
                            }} />
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
                <span className="dm-foot-note">{context?.from ? replies : ''}</span>
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
