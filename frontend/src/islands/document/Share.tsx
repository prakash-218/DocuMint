import { useEffect, useId, useRef, useState } from 'react';
import { api, ApiError } from '../../api';
import { money } from '../../format';
import { Icon } from '../../icons';
import { Composer } from '../EmailComposer';
import './Share.css';

// Sharing a sent document (sharing.py): WhatsApp, a copied link, its PDF, or an email from the shared mailbox. WhatsApp
// and the copied link need the document's private link, made the first time either is asked for; it opens the
// document without signing in until it's turned off. A proforma or invoice with something due shows its UPI QR code.

export interface SharePerson { name: string; role: string; phone: string; number: string; gets_it: boolean }

export interface ShareData {
  link: { url: string; opens: number; last_opened: string; made: string } | null;
  number: string;
  kind: string;
  /** The message after its greeting; [link] stands for the link until there is one. */
  body: string;
  people: SharePerson[];
  pay: { upi_id: string; amount: number; link: string; qr: string } | null;
  /** Something is due in rupees, but there's no UPI ID in the business profile yet. */
  upi_missing: boolean;
  pdf: string;
  email: boolean;
  actions: { make: string; off: string };
}

export const LINK = '[link]';

/** wa.me with the message ready, to a number or to whoever is picked in WhatsApp (sharing.wa_link). */
export function waLink(text: string, number = ''): string {
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`;
}

export function ShareDialog({ url, projectId, invoiceId, onClose }: { url: string; projectId: string | null; invoiceId: string; onClose: () => void }) {
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const [data, setData] = useState<ShareData | null>(null);
  const [body, setBody] = useState('');
  const [open, setOpen] = useState<'whatsapp' | 'link' | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [emailing, setEmailing] = useState(false);

  useEffect(() => {
    if (dialog.current && !dialog.current.open) dialog.current.showModal();
    api.get<ShareData>(url).then((d) => { setData(d); setBody(d.body); })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load this. Check your connection."));
  }, [url]);

  /** The private link, made now if it isn't there yet; the message's [link] becomes it. */
  async function withLink(then: 'whatsapp' | 'link') {
    setError('');
    if (data?.link) { setOpen(then); return; }
    setBusy(true);
    try {
      const d = await api.post<ShareData>(data!.actions.make, {});
      setData(d);
      setBody((b) => b.split(LINK).join(d.link?.url ?? LINK));
      setOpen(then);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't make the link. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function turnOff() {
    setBusy(true);
    try {
      const d = await api.del<ShareData>(data!.actions.off);
      setData(d);
      setBody(d.body);
      setOpen(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't turn the link off. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      (document.getElementById(`${id}-url`) as HTMLInputElement | null)?.select();     // select it to copy by hand
    }
  }

  if (emailing && projectId) return <Composer projectId={projectId} invoiceId={invoiceId} onClose={() => onClose()} />;

  const greet = (name: string) => `${name ? `Dear ${name},` : 'Hello,'}\n${body}`;
  const link = data?.link;
  return (
    <dialog ref={dialog} className="k-dialog dm-share" aria-labelledby={`${id}-title`} onClose={onClose}>
      <div className="k-dialog-head">
        <h2 id={`${id}-title`}>Share {data?.number ?? ''}</h2>
        <button type="button" className="btn btn-ghost btn-xs" onClick={() => dialog.current?.close()} aria-label="Close"><Icon name="x" /></button>
      </div>
      <div className="k-dialog-body share-body">
        {!data ? <p className="text-tertiary">{error || 'Loading…'}</p> : (
          <>
            <div className="share-opts">
              <button type="button" className="btn btn-secondary" aria-pressed={open === 'whatsapp'} disabled={busy}
                      onClick={() => void withLink('whatsapp')}><Icon name="messageCircle" />WhatsApp</button>
              <button type="button" className="btn btn-secondary" aria-pressed={open === 'link'} disabled={busy}
                      onClick={() => void withLink('link')}><Icon name="link" />Copy link</button>
              <a className="btn btn-secondary" href={`${data.pdf}?download=1`}><Icon name="download" />Download PDF</a>
              {data.email && projectId && (
                <button type="button" className="btn btn-secondary" onClick={() => setEmailing(true)}><Icon name="mail" />Email</button>
              )}
            </div>
            {error && <p className="error" role="alert">{error}</p>}

            {open === 'whatsapp' && link && (
              <section className="share-sec" aria-label="WhatsApp">
                <label htmlFor={`${id}-msg`} className="form-label">Message</label>
                <textarea id={`${id}-msg`} className="form-input" rows={7} value={body} onChange={(e) => setBody(e.target.value)} />
                <p className="form-text">“Dear …,” goes on top, with the name of whoever you send it to.</p>
                <ul className="share-people">
                  {data.people.map((p) => (
                    <li key={`${p.number}-${p.name}`}>
                      <a className="btn btn-secondary" href={waLink(greet(p.name), p.number)} target="_blank" rel="noopener noreferrer">
                        <Icon name="messageCircle" />{p.name}
                      </a>
                      <span className="text-tertiary">{[p.role, p.phone, p.gets_it ? '' : 'not on this document'].filter(Boolean).join(' · ')}</span>
                    </li>
                  ))}
                  <li>
                    <a className="btn btn-secondary" href={waLink(greet(''))} target="_blank" rel="noopener noreferrer">
                      <Icon name="messageCircle" />Someone else
                    </a>
                    <span className="text-tertiary">{data.people.length ? 'Pick them in WhatsApp' : 'No contact on this project has a phone number; pick someone in WhatsApp'}</span>
                  </li>
                </ul>
              </section>
            )}

            {open === 'link' && link && (
              <section className="share-sec" aria-label="The link">
                <label htmlFor={`${id}-url`} className="form-label">Link</label>
                <div className="share-url">
                  <input id={`${id}-url`} className="form-input mono" readOnly value={link.url} onFocus={(e) => e.target.select()} />
                  <button type="button" className="btn btn-primary" onClick={() => void copy(link.url)}>{copied ? 'Copied' : 'Copy'}</button>
                </div>
              </section>
            )}

            {link && (
              <p className="form-note share-link-note">
                <Icon name="info" />
                <span>
                  Anyone with the link can open this {data.kind.toLowerCase()} and its PDF, without signing in.{' '}
                  {link.opens ? `Opened ${link.opens} time${link.opens === 1 ? '' : 's'}, last on ${link.last_opened}.` : 'Not opened yet.'}{' '}
                  <button type="button" className="linkish" disabled={busy} onClick={() => void turnOff()}>Turn the link off</button>
                </span>
              </p>
            )}

            {data.pay && (
              <section className="share-pay" aria-label="Pay by UPI">
                <img src={data.pay.qr} alt={`UPI QR code to pay ${money(data.pay.amount)}`} />
                <div>
                  <b>Scan to pay {money(data.pay.amount)}</b>
                  <div className="text-tertiary">UPI to <span className="mono">{data.pay.upi_id}</span>. The link’s page and the PDF show it too.</div>
                </div>
              </section>
            )}
            {!data.pay && data.upi_missing && (
              <p className="form-note"><Icon name="info" /><span>Add your UPI ID in Settings → Business profile, and a “Scan to pay” QR code for what’s due shows here, on the PDF and on the link’s page.</span></p>
            )}
          </>
        )}
      </div>
      <div className="k-dialog-foot">
        <button type="button" className="btn btn-ghost" onClick={() => dialog.current?.close()}>Close</button>
      </div>
    </dialog>
  );
}
