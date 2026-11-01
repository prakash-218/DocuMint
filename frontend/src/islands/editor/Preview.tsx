import { useEffect, useRef, useState, type RefObject } from 'react';
import { Icon } from '../../icons';

// The editor's live preview, beside it: what's typed, drawn by the server as the document's page shows it, with its
// PDF, the email and the WhatsApp message it would go with (POST data.preview, api_bp.preview_document). Nothing is
// saved. A change asks again after a moment; a newer change cancels the last request.

interface Drawn { html: string; total: number; email: { subject: string; body: string }; whatsapp: string }
type Tab = 'page' | 'pdf' | 'email' | 'whatsapp';
const TABS: [Tab, string][] = [['page', 'Page'], ['pdf', 'PDF'], ['email', 'Email'], ['whatsapp', 'WhatsApp']];

/** The form's fields as the API takes them: {name: value} */
export function fields(form: HTMLFormElement | null): Record<string, string> {
  const out: Record<string, string> = {};
  if (form) new FormData(form).forEach((v, k) => { if (typeof v === 'string') out[k] = v; });
  return out;
}

async function post(url: string, form: HTMLFormElement | null, signal: AbortSignal): Promise<Response> {
  const response = await fetch(url, {
    method: 'POST', credentials: 'same-origin', signal,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json, application/pdf' },
    body: JSON.stringify({ fields: fields(form) }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || `The server said ${response.status}`);
  return response;
}

export function Preview({ url, form, version }: { url: string; form: RefObject<HTMLFormElement | null>; version: number }) {
  const [tab, setTab] = useState<Tab>('page');
  const [drawn, setDrawn] = useState<Drawn | null>(null);
  const [pdf, setPdf] = useState<string | null>(null);
  const [problem, setProblem] = useState('');
  const [busy, setBusy] = useState(false);
  const pdfUrl = useRef<string | null>(null);

  // the page, the email and the message: soon after each change
  useEffect(() => {
    const abort = new AbortController();
    const timer = setTimeout(() => {
      setBusy(true);
      post(url, form.current, abort.signal).then((r) => r.json()).then((d: Drawn) => { setDrawn(d); setProblem(''); })
        .catch((e: Error) => { if (e.name !== 'AbortError') setProblem(e.message); })
        .finally(() => { if (!abort.signal.aborted) setBusy(false); });
    }, 350);
    return () => { clearTimeout(timer); abort.abort(); };
  }, [url, form, version]);

  // the PDF: only while its tab is open, a little later (it takes the server longer)
  useEffect(() => {
    if (tab !== 'pdf') return undefined;
    const abort = new AbortController();
    const timer = setTimeout(() => {
      setBusy(true);
      post(`${url}?as=pdf`, form.current, abort.signal).then((r) => r.blob()).then((blob) => {
        const next = URL.createObjectURL(blob);
        if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current);
        pdfUrl.current = next; setPdf(next); setProblem('');
      }).catch((e: Error) => { if (e.name !== 'AbortError') setProblem(e.message); })
        .finally(() => { if (!abort.signal.aborted) setBusy(false); });
    }, 900);
    return () => { clearTimeout(timer); abort.abort(); };
  }, [tab, url, form, version]);
  useEffect(() => () => { if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current); }, []);

  return (
    <section className="editor-preview" aria-label="Preview">
      <div className="editor-preview-bar">
        <div className="seg-tabs" role="tablist" aria-label="Preview as">
          {TABS.map(([key, label]) => (
            <button key={key} type="button" role="tab" aria-selected={tab === key} className={tab === key ? 'active' : undefined}
                    onClick={() => setTab(key)}>{label}</button>
          ))}
        </div>
        <span className="editor-preview-state" aria-live="polite">
          {problem ? <span className="text-danger">{problem}</span> : busy ? 'Updating…' : drawn ? 'Up to date' : ''}
        </span>
      </div>
      <div className="editor-preview-body" role="tabpanel">
        {tab === 'page' && (drawn ? <div className="editor-preview-page" dangerouslySetInnerHTML={{ __html: drawn.html }} />
          : <p className="text-tertiary">Drawing it…</p>)}
        {tab === 'pdf' && (pdf ? <iframe className="editor-preview-pdf" src={pdf} title="PDF preview" />
          : <p className="text-tertiary">Making the PDF…</p>)}
        {tab === 'email' && drawn && (
          <div className="editor-preview-mail">
            <div className="text-tertiary">Subject</div>
            <div className="editor-preview-subject">{drawn.email.subject}</div>
            <div className="editor-preview-text">{drawn.email.body}</div>
            <div className="text-tertiary"><Icon name="paperclip" /> The PDF</div>
          </div>
        )}
        {tab === 'whatsapp' && drawn && (
          <div className="editor-preview-chat"><div className="editor-preview-bubble">{drawn.whatsapp}</div></div>
        )}
      </div>
    </section>
  );
}
