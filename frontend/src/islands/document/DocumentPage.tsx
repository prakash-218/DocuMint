import { Dropdown, choices } from '../../mantine/Dropdown';
import { useCallback, useEffect, useId, useState, type FormEvent } from 'react';
import { api, ApiError } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { day, money, when } from '../../format';
import { Icon, type IconName } from '../../icons';
import { Skeleton } from '../../Skeleton';
import { ACCEPT } from '../project/Side';
import DocumentNext from './DocumentNext';
import { ShareDialog } from './Share';
import { ReceivingCard } from './Receiving';
import type { Change, DocumentData, Payments, PdfMenu } from './types';

// A document's page, as the prototype draws it: its number, state and what to do next with the money under it,
// then its payments and the document, with the project's documents, who gets it, what happened, converting it,
// its project and its files beside them. The document and its versions are the server's own HTML (the PDF's
// layout); the forms post to the document routes and come back here.

const ICONS: Record<string, IconName> = {
  'file-down': 'fileDown', file: 'file', package: 'package', 'file-plus': 'filePlus', 'indian-rupee': 'rupee', send: 'send',
  mail: 'mail', 'sticky-note': 'note', 'file-text': 'fileText',
};
const SEAL_KEY = 'documint.pdfSeal';

const ask = (message: string) => (e: FormEvent) => {
  if (!window.confirm(message)) e.preventDefault();
};

/** HTML the server drew (the document, its versions), with its Lucide icons drawn once it's in. */
function ServerHtml({ html }: { html: string }) {
  useEffect(() => {
    (window as unknown as { lucide?: { createIcons: () => void } }).lucide?.createIcons();
  }, [html]);
  return <div style={{ display: 'contents' }} dangerouslySetInnerHTML={{ __html: html }} />;
}

/** The PDF menu in the header: copies, extra pages, packing, deleting a draft; with or without the seal. */
export function Pdf({ pdf }: { pdf: PdfMenu }) {
  const [seal, setSeal] = useState(() => {
    try { return window.localStorage.getItem(SEAL_KEY) !== 'off'; } catch { return true; }
  });
  const withSeal = (href: string) => {
    if (!pdf.seal || seal) return href;
    const url = new URL(href, window.location.href);
    url.searchParams.set('seal', '0');
    return url.pathname + url.search;
  };
  return (
    <details className="menu">
      <summary className="btn btn-secondary"><Icon name="download" /><span className="btn-label">PDF</span><Icon name="chevronDown" className="hide-mobile" /></summary>
      <div className="menu-items">
        {pdf.seal && (
          <>
            <label className="menu-check">
              <input type="checkbox" checked={seal} onChange={(e) => {
                setSeal(e.target.checked);
                try { window.localStorage.setItem(SEAL_KEY, e.target.checked ? 'on' : 'off'); } catch { /* not remembered */ }
              }} />
              <span>Print with seal</span>
            </label>
            <hr />
          </>
        )}
        {pdf.links.map((l) => (
          <a key={l.href} href={withSeal(l.href)} target="_blank" rel="noopener"><Icon name={ICONS[l.icon] ?? 'file'} />{l.label}</a>
        ))}
        {pdf.packing && <><hr /><a href={pdf.packing}><Icon name="packageOpen" />Edit packing</a></>}
        {pdf.delete && (
          <>
            <hr />
            <form method="post" action={pdf.delete} onSubmit={ask("Delete this draft? This can't be undone.")}>
              <button type="submit" className="danger"><Icon name="trash" />Delete draft</button>
            </form>
          </>
        )}
      </div>
    </details>
  );
}

/** What the header's button on a sent document says: Revise where a revision can be made, otherwise Edit (a correction). */
const changeWord = (change: Change) => (change.revise?.possible ? 'Revise' : 'Edit');

/** "Revise" or "Edit" on a sent document: make a revision, correct it (same number), or move it back to draft. */
function ChangeDialog({ change }: { change: Change }) {
  const r = change.revise;
  const correct = (
    <section className="change-option">
      <div>
        <h3>Correct this {change.short}</h3>
        <p>Fix a mistake: a wrong PO number, date, rate or spelling. It keeps its number{change.takes_payments ? ' and its payments' : ''},
          and the correction replaces what was {change.sent_word}. Recorded in the audit log.</p>
      </div>
      <a href={change.correct} className="btn btn-secondary btn-sm"><Icon name="pencil" />Correct it</a>
    </section>
  );
  return (
    <dialog className="k-dialog" id="change-dialog" aria-labelledby="change-title">
      <div className="k-dialog-head">
        <h2 id="change-title">{changeWord(change)} {change.number}</h2>
        <button type="button" className="btn btn-ghost btn-xs" data-close aria-label="Close"><Icon name="x" /></button>
      </div>
      <div className="k-dialog-body change-options">
        {!r?.possible && correct}
        {r && (
          <section className="change-option">
            <div>
              <h3>Make a revision</h3>
              {r.possible ? (
                <p>A new version, <strong>{r.number}</strong>, for a changed offer: other prices, items or terms. This one stays as it was{' '}
                  {change.sent_word}, marked revised{change.proforma ? '; advances received move to the revision' : ''}.</p>
              ) : <p className="text-tertiary">{r.note}</p>}
            </div>
            {r.possible && (
              <form method="post" action={r.action} className="change-revise">
                {r.templates.length > 1 && (
                  <>
                    <label htmlFor="revise_template" className="form-label">Template</label>
                    <Dropdown id="revise_template" name="template_id" size="xs" defaultValue={r.current_template}
                              data={r.templates.map((t) => ({ value: t.id, label: `${t.name}${t.same ? ' (same as now)' : ''}` }))} />
                  </>
                )}
                <button type="submit" className="btn btn-secondary btn-sm"><Icon name="fileDiff" />Make {r.number}</button>
              </form>
            )}
          </section>
        )}
        {r?.possible && correct}
        <section className="change-option">
          <div>
            <h3>Back to draft</h3>
            {change.reopen.blocker ? (
              <p className="text-tertiary">Not possible: {change.reopen.blocker.slice(0, 1).toLowerCase()}{change.reopen.blocker.slice(1)}</p>
            ) : (
              <p>Undo "{change.undo}" when it was done by mistake. It keeps its number; edit it and {change.again} it again.</p>
            )}
          </div>
          {!change.reopen.blocker && (
            <form method="post" action={change.reopen.action}>
              <button type="submit" className="btn btn-secondary btn-sm"><Icon name="undo2" />Back to draft</button>
            </form>
          )}
        </section>
      </div>
    </dialog>
  );
}

function RecordForm({ form }: { form: NonNullable<Payments['record']> }) {
  const id = useId();
  const [amount, setAmount] = useState(form.suggested ? form.suggested.toFixed(2) : '');
  const [received, setReceived] = useState('');
  const rate = parseFloat(received) > 0 && parseFloat(amount) > 0 ? (parseFloat(received) / parseFloat(amount)).toFixed(2) : '';
  return (
    <form method="post" action={form.action}>
      {form.advance && <p className="form-text" style={{ marginTop: 0 }}>Money received against this proforma. It moves to the invoice when the proforma is converted.</p>}
      <div className="form-group">
        <label htmlFor={`${id}-amount`} className="form-label">Amount ({form.currency})</label>
        <input type="number" step="0.01" min="0.01" id={`${id}-amount`} name="amount" className="form-input" value={amount}
               onChange={(e) => setAmount(e.target.value)} required />
      </div>
      {form.currency !== form.base_currency && (
        <div className="form-group">
          <label htmlFor={`${id}-received`} className="form-label">Credited to your bank ({form.base_currency}) <span className="text-tertiary">(optional)</span></label>
          <input type="number" step="0.01" min="0" id={`${id}-received`} name="received_amount" className="form-input" value={received}
                 onChange={(e) => setReceived(e.target.value)} placeholder="e.g. from the bank advice / FIRC" />
          {rate && <p className="form-text">Exchange rate: 1 {form.currency} = {rate} {form.base_currency}</p>}
        </div>
      )}
      <div className="form-group">
        <label htmlFor={`${id}-date`} className="form-label">Received on</label>
        <input type="date" id={`${id}-date`} name="payment_date" className="form-input" defaultValue={form.today} max={form.today} />
      </div>
      <div className="form-group">
        <label htmlFor={`${id}-method`} className="form-label">Method</label>
        <Dropdown id={`${id}-method`} name="method" defaultValue={form.methods[0]} data={choices(form.methods)} />
      </div>
      <div className="form-group">
        <label htmlFor={`${id}-ref`} className="form-label">Reference <span className="text-tertiary">(optional)</span></label>
        <input type="text" id={`${id}-ref`} name="reference_number" className="form-input" />
      </div>
      <button type="submit" className="btn btn-primary btn-block">{form.button}</button>
    </form>
  );
}

function PaymentsCard({ payments: p, currency }: { payments: Payments; currency: string }) {
  return (
    <section className="card" aria-labelledby="doc-payments">
      <div className="card-h">
        <h2 id="doc-payments">{p.title}</h2>
        {p.record_label && <a href="#payment" className="btn btn-secondary btn-sm"><Icon name="rupee" />{p.record_label}</a>}
      </div>
      <div className="card-b">
        {p.rows.length ? (
          <ul className="pays">
            {p.rows.map((r) => (
              <li key={r.id}>
                <span>
                  {[day(r.date), r.label, r.method].filter(Boolean).join(' · ')}
                  {r.reference && <><br /><span className="muted">{r.reference}</span></>}
                  {r.credited && <><br /><span className="muted">Credited {money(r.credited.amount, r.credited.currency)}{r.credited.rate ? ` @ ${r.credited.rate}` : ''}</span></>}
                  {p.title === 'Advances' && (
                    <><br /><span className="muted">{r.applied ? <>Applied to <a href={r.applied.url}>{r.applied.number}</a></> : 'Goes to the invoice when this proforma is converted'}</span></>
                  )}
                  {r.take_off && (
                    <form method="post" action={r.take_off.action} style={{ display: 'inline' }} onSubmit={ask(r.take_off.confirm)}>
                      {' · '}<button type="submit" className="link-button">Take off this invoice</button>
                    </form>
                  )}
                </span>
                <span className="mono">{money(r.amount, currency)}</span>
              </li>
            ))}
          </ul>
        ) : <p className="muted" style={{ margin: 0 }}>{p.empty}</p>}
        {p.apply && (
          <details className="fold-in" id="advances" open>
            <summary>Apply an advance</summary>
            <form method="post" action={p.apply.action}>
              <p className="form-text" style={{ marginTop: 0 }}>{p.apply.note}</p>
              {p.apply.rows.map((a) => (
                <label key={a.payment_id} className="advance-pick">
                  <input type="checkbox" name="payment_id" value={a.payment_id} defaultChecked={a.checked} />
                  <span><strong>{money(a.amount, currency)}</strong> on {a.number}
                    <span className="text-tertiary">{[day(a.date), a.reference].filter(Boolean).map((x) => ` · ${x}`).join('')}</span></span>
                </label>
              ))}
              <button type="submit" className="btn btn-secondary btn-block" style={{ marginTop: 'var(--spacing-sm)' }}>{p.apply.button}</button>
            </form>
          </details>
        )}
        {p.record && (
          <details className="fold-in" id="payment">
            <summary>{p.record.title}</summary>
            <RecordForm form={p.record} />
          </details>
        )}
      </div>
    </section>
  );
}

function Convert({ convert }: { convert: NonNullable<DocumentData['convert']> }) {
  const id = useId();
  const [template, setTemplate] = useState(convert.targets[0]?.template ?? '');
  return (
    <section className="side-sec">
      <details className="fold-in" id="convert" style={{ border: 0, margin: 0, padding: 0 }}>
        <summary>{convert.label}</summary>
        <form method="post" action={convert.action}>
          <div className="form-group">
            <label htmlFor={`${id}-target`} className="form-label">Convert to</label>
            <Dropdown id={`${id}-target`} name="target" defaultValue={convert.targets[0]?.key}
                      data={convert.targets.map((t) => ({ value: t.key, label: t.label }))}
                      onChange={(v) => { const t = convert.targets.find((x) => x.key === v)?.template; if (t) setTemplate(t); }} />
          </div>
          <div className="form-group">
            <label htmlFor={`${id}-template`} className="form-label">Using template</label>
            <Dropdown id={`${id}-template`} name="template_id" value={template} onChange={setTemplate}
                      data={convert.templates.map((t) => ({ value: t.id, label: t.name }))} />
          </div>
          {convert.discount && (
            <fieldset className="form-group convert-discount">
              <legend className="form-label">Its discount</legend>
              <p className="form-text">{convert.discount[0].toUpperCase() + convert.discount.slice(1)}.</p>
              <label className="form-check"><input type="radio" name="discount" value="keep" defaultChecked /> Keep it as a discount</label>
              <label className="form-check"><input type="radio" name="discount" value="spread" /> Take it into the item prices</label>
            </fieldset>
          )}
          <button type="submit" className="btn btn-primary btn-block"><Icon name="arrowRightLeft" />Convert</button>
        </form>
      </details>
    </section>
  );
}

interface Option { id: string; no: string; title: string; fy: string; status: string }

/** The project it's in, its other documents, and moving it to another of the customer's projects. */
function ProjectCard({ card, current }: { card: DocumentData['project']; current: string | null }) {
  const id = useId();
  const [options, setOptions] = useState<Option[] | null>(null);
  const [open, setOpen] = useState(!card.project);
  useEffect(() => {
    if (!open || options || !card.change) return;
    api.get<{ projects: Option[] }>(card.change.options).then((d) => setOptions(d.projects)).catch(() => setOptions([]));
  }, [open, options, card.change]);
  const p = card.project;
  const others = options?.filter((o) => o.id !== current) ?? [];
  return (
    <section className="side-sec">
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Project</h2>
          {p && <a href={p.url} className="btn btn-ghost btn-xs">Open</a>}
        </div>
        <div className="card-body">
          {p ? (
            <>
              <p style={{ margin: '0 0 var(--spacing-sm)' }}>
                <a href={p.url}><strong>{p.title}</strong></a><br />
                <span className="text-tertiary" style={{ fontSize: 'var(--font-size-xs)' }}>
                  {[p.label, p.fy && `FY ${p.fy}`, p.reference && `Ref. ${p.reference}`].filter(Boolean).join(' · ')}
                </span>
              </p>
              {card.others.length > 0 && (
                <ul className="project-card-docs">
                  {card.others.map((d) => (
                    <li key={d.url}><a href={d.url}>{d.number}</a>
                      <span className="text-tertiary">{d.kind}{d.versions ? ` · ${d.versions} versions` : ''}</span></li>
                  ))}
                </ul>
              )}
            </>
          ) : !card.change && <p className="text-tertiary" style={{ margin: 0 }}>Not part of a project.</p>}
          {card.change && (
            <details className="pp-toggle" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
              <summary className="btn btn-secondary btn-sm">{p ? 'Move to another project' : 'Add to a project'}</summary>
              {options === null ? <p className="muted" style={{ fontSize: 13 }}>Loading projects…</p> : (
                <>
                  {others.length > 0 && (
                    <form method="post" action={card.change.action} className="stack-form">
                      <label htmlFor={`${id}-project`} className="form-label">{p ? 'Move it to' : 'Put it in'}</label>
                      <div className="add-existing-row">
                        <Dropdown id={`${id}-project`} name="project_id" required placeholder="Choose a project"
                                  data={others.map((o) => ({ value: o.id, label: `${o.no} · ${o.title}`, sub: [o.fy ? `FY ${o.fy}` : '', o.status !== 'open' ? o.status : ''].filter(Boolean).join(' · ') || undefined }))} />
                        <button type="submit" className="btn btn-secondary btn-sm">{p ? 'Move' : 'Add'}</button>
                      </div>
                    </form>
                  )}
                  <div className="pp-actions">
                    <form method="post" action={card.change.action} style={{ display: 'inline' }}>
                      <button type="submit" name="project_id" value="new" className="link-button">Start a new project{p ? ' instead' : ''}</button>
                    </form>
                    {p && (
                      <form method="post" action={card.change.action} style={{ display: 'inline' }}>
                        <button type="submit" name="project_id" value="" className="link-button">Remove from the project</button>
                      </form>
                    )}
                  </div>
                </>
              )}
            </details>
          )}
        </div>
      </div>
    </section>
  );
}

function DocFiles({ data }: { data: DocumentData }) {
  const id = useId();
  const n = data.files.length;
  return (
    <section className="side-sec" aria-labelledby="doc-files">
      <h2 id="doc-files">Files <span className="muted" style={{ fontWeight: 400, fontSize: 12.5 }}>{n} file{n === 1 ? '' : 's'}</span></h2>
      {n > 0 && (
        <ul className="files">
          {data.files.map((f) => (
            <li key={f.id}>
              <span className="fi" aria-hidden="true"><Icon name={f.kind === 'po' ? 'fileCheck' : 'paperclip'} size={15} /></span>
              <div style={{ minWidth: 0 }}>
                <a href={f.url} className="fn">{f.title || f.name}</a>
                <div className="fs"><span className="tag tone-draft">{f.kind_label}</span>{' '}
                  {[f.reference_no && `No. ${f.reference_no}`, f.from_email ? 'From email' : '', day(f.date), f.size].filter(Boolean).join(' · ')}</div>
              </div>
              <a href={`${f.url}?download=1`} className="btn btn-ghost btn-xs" aria-label={`Download ${f.name}`}><Icon name="download" size={14} /></a>
            </li>
          ))}
        </ul>
      )}
      {data.upload && (
        <>
          <form className="drop" data-dropzone method="post" action={data.upload.action} encType="multipart/form-data">
            <input type="hidden" name="invoice_id" value={data.invoice_id} />
            <input type="file" id={`${id}-file`} name="file" multiple className="sr-only" accept={ACCEPT} />
            <span data-drop-label>Drop files here or <label htmlFor={`${id}-file`} className="linkish">choose files</label></span>
          </form>
          {data.project.project && (
            <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>To say what a file is or give its number, open its tag on the{' '}
              <a href={data.project.project.url}>project page</a>.</p>
          )}
        </>
      )}
    </section>
  );
}

export default function DocumentPage({ invoiceId }: { invoiceId: string }) {
  const [data, setData] = useState<DocumentData | null>(null);
  const [error, setError] = useState('');
  const [sharing, setSharing] = useState(false);
  const load = useCallback(async () => {
    try {
      setData(await api.get<DocumentData>(`/api/document/${invoiceId}`));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't load the document. Check your connection.");
    }
  }, [invoiceId]);
  useEffect(() => {
    void load();
  }, [load]);

  if (!data) {
    return (
      <>
        <PageHeader title="Document" crumbs={[{ label: '…' }]} />
        {error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="doc" label="Loading the document…" />}
      </>
    );
  }

  return (
    <>
      <PageHeader title={data.number} crumbs={[{ label: data.list.label, href: data.list.url }, { label: data.number }]}
                  actions={<>
                    {data.share && (
                      <button type="button" className="btn btn-secondary" onClick={() => setSharing(true)}><Icon name="share" /><span className="btn-label">Share</span></button>
                    )}
                    <Pdf pdf={data.pdf} />
                    {data.edit && <a href={data.edit} className="btn btn-secondary"><Icon name="pencil" /><span className="btn-label">Edit</span></a>}
                    {data.change && (
                      <button type="button" className="btn btn-secondary" data-open-dialog="change-dialog">
                        <Icon name={data.change.revise?.possible ? 'fileDiff' : 'pencil'} /><span className="btn-label">{changeWord(data.change)}</span>
                      </button>
                    )}
                  </>} />
      {data.change && <ChangeDialog change={data.change} />}
      {sharing && data.share && (
        <ShareDialog url={data.share} projectId={data.project_id} invoiceId={data.invoice_id} onClose={() => { setSharing(false); void load(); }} />
      )}
      <div className="ui doc-page">
        <DocumentNext next={data.next} head={data.head} money={data.money} currency={data.currency} invoiceId={data.invoice_id}
                      projectId={data.project_id} />
        <div className="cols">
          <div className="col-main">
            {data.payments && <PaymentsCard payments={data.payments} currency={data.currency} />}
            {data.receiving && <ReceivingCard receiving={data.receiving} />}
            {data.versions_html && <ServerHtml html={data.versions_html} />}
            <ServerHtml html={data.document_html} />
          </div>
          <aside className="col-side" aria-label="Its project, people and activity">
            {data.chain.length > 0 && (
              <section className="side-sec" aria-labelledby="doc-chain">
                <h2 id="doc-chain">Documents</h2>
                <ol className="chain">
                  {data.chain.map((d) => (
                    <li key={d.url} className={`node is-doc${d.paid ? ' is-paid' : ''}${d.here ? ' is-here' : ''}`}>
                      <span className="dot" aria-hidden="true"><Icon name={d.paid && !d.here ? 'check' : 'fileText'} size={14} /></span>
                      <div className="doc-box">
                        <div className="doc-top"><span className="doc-type">{d.kind}</span><span className={`tag tone-${d.pill.tone}`}>{d.pill.text}</span></div>
                        <div className="doc-row">
                          {d.here ? <span className="doc-no" style={{ color: 'inherit' }}>{d.number}</span> : <a className="doc-no" href={d.url}>{d.number}</a>}
                          <span className="doc-amt">{money(d.total, d.currency)}</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
            )}
            {data.people && (
              <section className="side-sec" aria-labelledby="doc-people">
                <h2 id="doc-people">Who gets it {data.people.url && <a className="btn btn-secondary btn-xs" href={data.people.url}>People</a>}</h2>
                {data.people.list.length ? (
                  <ul className="people">
                    {data.people.list.map((p) => (
                      <li key={`${p.name}-${p.email}`}><span className="avatar" aria-hidden="true">{p.initials}</span>
                        <div><div className="pn">{p.name}{p.role && <span> · {p.role}</span>}</div><div className="pe">{p.email}</div></div></li>
                    ))}
                  </ul>
                ) : <p className="muted" style={{ margin: 0, fontSize: 13 }}>{data.people.empty}</p>}
              </section>
            )}
            {data.activity.length > 0 && (
              <section className="side-sec" aria-labelledby="doc-activity">
                <h2 id="doc-activity">Activity</h2>
                <ul className="feed" style={{ margin: 0 }}>
                  {data.activity.map((e, i) => (
                    <li key={i} className={`ev ${e.tone}`}>
                      <span className="ico" aria-hidden="true"><Icon name={ICONS[e.icon] ?? 'fileText'} size={14} /></span>
                      <div style={{ minWidth: 0 }}><div className="ev-title">{e.title}</div>
                        {e.body && <div className="ev-body">{e.body}</div>}
                        {e.who && <div className="ev-by">{e.who}</div>}</div>
                      <span className="ev-date">{when(e.when)}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {data.convert && <Convert convert={data.convert} />}
            <ProjectCard card={data.project} current={data.project_id} />
            <DocFiles data={data} />
          </aside>
        </div>
      </div>
    </>
  );
}
