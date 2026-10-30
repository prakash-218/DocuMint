import { Dropdown } from '../../mantine/Dropdown';
import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Doc, Page, Tone } from './types';

const GROUPS: { key: 'quote' | 'proforma' | 'invoice'; label: string; empty: string; later: string; types: Doc['doc_type'][] }[] = [
  { key: 'quote', label: 'Quotation', empty: 'No quotation yet', later: 'The offer, first of all', types: ['quote'] },
  { key: 'proforma', label: 'Proforma for the advance', empty: 'No proforma', later: 'After the quotation is accepted, when an advance is asked for', types: ['proforma'] },
  { key: 'invoice', label: 'Tax invoice', empty: 'Not invoiced yet', later: 'After the advance, on delivery', types: ['invoice', 'export_invoice'] },
];

export function status(d: Doc): { text: string; tone: Tone } {
  if (d.status === 'draft') return { text: 'Draft', tone: 'draft' };
  if (d.status === 'declined') return { text: 'Declined', tone: 'late' };
  if (d.status === 'accepted') return { text: 'Accepted', tone: 'done' };
  if (d.status === 'converted') return { text: d.doc_type === 'quote' ? 'Accepted' : 'Invoiced', tone: 'done' };
  if (d.status === 'revised') return { text: 'Revised', tone: 'draft' };
  if (d.status === 'paid') return { text: 'Paid', tone: 'done' };
  if (d.doc_type === 'proforma' && d.paid > 0) return { text: 'Advance received', tone: 'done' };
  if (d.status === 'pending') return d.paid > 0 ? { text: 'Part paid', tone: 'wait' } : { text: 'Unpaid', tone: 'wait' };
  return { text: 'Sent', tone: 'wait' };
}

interface Props {
  docs: Doc[];
  newDocument: Page['new_document'];
  canEdit: boolean;
  sales: boolean;
  onEmail: (invoiceId: string) => void;
  /** Where the job is (stage.current): the empty slot for its next document is the highlighted one. */
  current?: string | null;
  /** The customer's documents in no project, and where adding or taking one out posts (projects_bp.project_document). */
  addable?: Page['addable'];
  documentsUrl?: string | null;
}

const NEXT_SLOT: Record<string, string> = { quoted: 'quote', advance: 'proforma', invoiced: 'invoice' };

/** The chain from quotation to payment; revisions sit under their document, the next one waits as a slot. */
export function Documents({ docs, newDocument, canEdit, sales, onEmail, current, addable = [], documentsUrl = null }: Props) {
  const groups = sales ? GROUPS.slice(0, 1) : GROUPS;
  const firstEmpty = current ? NEXT_SLOT[current] : undefined;
  return (
    <section className="card" aria-labelledby="pp-docs">
      <div className="card-h">
        <h2 id="pp-docs">Documents</h2>
        {!sales && <span className="muted" style={{ fontSize: 12.5 }}>Quotation → Proforma → Tax invoice</span>}
      </div>
      <div className="card-b">
        <ol className="chain">
          {groups.map((g) => {
            const mine = docs.filter((d) => g.types.includes(d.doc_type));
            if (!mine.length) {
              const href = newDocument[g.key];
              const next = g.key === firstEmpty;
              return (
                <li key={g.key} className="node">
                  <span className="dot" aria-hidden="true"><Icon name="file" size={14} /></span>
                  <div className={`slot${next ? ' next-slot' : ' later'}`}>
                    <span><span className="doc-type">{g.label}</span><br />{next ? g.empty : g.later}</span>
                    {canEdit && href && <a className={`btn btn-xs ${next ? 'btn-primary' : 'btn-ghost'}`} href={href}>New {g.label.split(' ')[0].toLowerCase()}</a>}
                  </div>
                </li>
              );
            }
            return mine.map((d) => <DocNode key={d.invoice_id} doc={d} canEdit={canEdit} onEmail={onEmail} documentsUrl={documentsUrl} />);
          })}
        </ol>
        {canEdit && documentsUrl && addable.length > 0 && (
          <form method="post" action={documentsUrl} className="add-existing">
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

function DocNode({ doc: d, canEdit, onEmail, documentsUrl }: { doc: Doc; canEdit: boolean; onEmail: (id: string) => void; documentsUrl: string | null }) {
  const s = status(d);
  const paid = d.status === 'paid' || (d.doc_type === 'proforma' && d.paid > 0);
  return (
    <li className={`node is-doc${paid ? ' is-paid' : ''}`}>
      <span className="dot" aria-hidden="true"><Icon name={paid ? 'check' : 'file'} size={14} /></span>
      <div className="doc-box">
        <div className="doc-top">
          <span className="doc-type">{d.kind}</span>
          <span className={`tag tone-${s.tone}`}>{s.text}</span>
        </div>
        <div className="doc-row">
          <a className="doc-no" href={d.url}>{d.number}</a>
          <span className="doc-amt">{money(d.total, d.currency)}</span>
        </div>
        <div className="doc-meta">
          {[day(d.issue_date) && `${d.status === 'draft' ? 'started' : 'sent'} ${day(d.issue_date)}`,
            d.balance !== null && d.paid > 0 ? `${money(d.paid, d.currency)} received` : '',
            d.balance ? `${money(d.balance, d.currency)} due` : ''].filter(Boolean).join(' · ')}
        </div>
        {d.versions.length > 0 && (
          <ul className="versions" aria-label="Earlier versions">
            {d.versions.map((v, i) => (
              <li key={v.invoice_id}>
                <a href={v.url}>{i === 0 ? 'Original' : `Revision ${i}`} · <span className="mono">{v.number}</span>{v.issue_date ? ` · ${day(v.issue_date)}` : ''}</a>
                <span className="mono">{money(v.total, d.currency)}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="doc-actions">
          <a className="btn btn-secondary btn-xs" href={d.url}>Open</a>
          <a className="btn btn-secondary btn-xs" href={d.pdf} target="_blank" rel="noopener"><Icon name="download" size={14} />PDF</a>
          {canEdit && d.status !== 'draft' && (
            <button type="button" className="btn btn-secondary btn-xs" onClick={() => onEmail(d.invoice_id)}>
              <Icon name="mail" size={14} />Email
            </button>
          )}
          {canEdit && documentsUrl && (
            <form method="post" action={documentsUrl} className="inline-form"
                  onSubmit={(e) => { if (!window.confirm(`Take ${d.number} out of this project? The document itself is kept.`)) e.preventDefault(); }}>
              <input type="hidden" name="invoice_id" value={d.invoice_id} />
              <input type="hidden" name="action" value="remove" />
              <button type="submit" className="btn btn-ghost btn-xs">Take out of the project</button>
            </form>
          )}
        </div>
      </div>
    </li>
  );
}
