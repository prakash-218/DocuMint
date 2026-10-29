import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Doc, Page, Tone } from './types';

const GROUPS: { key: 'quote' | 'proforma' | 'invoice'; label: string; empty: string; types: Doc['doc_type'][] }[] = [
  { key: 'quote', label: 'Quotation', empty: 'No quotation yet', types: ['quote'] },
  { key: 'proforma', label: 'Proforma', empty: 'No proforma (only when an advance is asked for)', types: ['proforma'] },
  { key: 'invoice', label: 'Tax invoice', empty: 'Not invoiced yet', types: ['invoice', 'export_invoice'] },
];

export function status(d: Doc): { text: string; tone: Tone } {
  if (d.status === 'draft') return { text: 'Draft', tone: 'draft' };
  if (d.status === 'declined') return { text: 'Declined', tone: 'late' };
  if (d.status === 'accepted') return { text: 'Accepted', tone: 'done' };
  if (d.status === 'converted') return { text: d.doc_type === 'quote' ? 'Accepted' : 'Invoiced', tone: 'done' };
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
}

/** The chain from quotation to payment; revisions sit under their document, the next one waits as a slot. */
export function Documents({ docs, newDocument, canEdit, sales, onEmail }: Props) {
  const groups = sales ? GROUPS.slice(0, 1) : GROUPS;
  return (
    <section className="card pp-card" aria-labelledby="pp-docs">
      <div className="card-header"><h2 className="card-title" id="pp-docs">Documents</h2></div>
      <ol className="pp-chain">
        {groups.map((g) => {
          const mine = docs.filter((d) => g.types.includes(d.doc_type));
          if (!mine.length) {
            const href = newDocument[g.key];
            return (
              <li key={g.key} className="pp-node is-empty">
                <span className="pp-dot" aria-hidden="true"><Icon name="file" size={14} /></span>
                <div className="pp-slot">
                  <span>{g.empty}</span>
                  {canEdit && href && <a className="btn btn-ghost btn-xs" href={href}>New {g.label.toLowerCase()}</a>}
                </div>
              </li>
            );
          }
          return mine.map((d) => <DocNode key={d.invoice_id} doc={d} canEdit={canEdit} onEmail={onEmail} />);
        })}
      </ol>
    </section>
  );
}

function DocNode({ doc: d, canEdit, onEmail }: { doc: Doc; canEdit: boolean; onEmail: (id: string) => void }) {
  const s = status(d);
  return (
    <li className="pp-node">
      <span className="pp-dot is-doc" aria-hidden="true"><Icon name="file" size={14} /></span>
      <div className="pp-doc">
        <div className="pp-doc-top">
          <span className="pp-doc-kind">{d.kind}</span>
          <span className={`pp-tag tone-${s.tone}`}>{s.text}</span>
        </div>
        <div className="pp-doc-row">
          <a className="pp-doc-no" href={d.url}>{d.number}</a>
          <span className="pp-doc-amount">{money(d.total, d.currency)}</span>
        </div>
        <div className="pp-doc-meta">
          {[day(d.issue_date),
            d.balance !== null && d.paid > 0 ? `${money(d.paid, d.currency)} received` : '',
            d.balance ? `${money(d.balance, d.currency)} due` : ''].filter(Boolean).join(' · ')}
        </div>
        {d.versions.length > 0 && (
          <ul className="pp-versions" aria-label="Earlier versions">
            {d.versions.map((v) => (
              <li key={v.invoice_id}>
                <a href={v.url}>{v.number}</a><span>{day(v.issue_date)}</span><span>{money(v.total, d.currency)}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="pp-doc-actions">
          <a className="btn btn-secondary btn-xs" href={d.url}>Open</a>
          <a className="btn btn-secondary btn-xs" href={d.pdf} target="_blank" rel="noopener"><Icon name="download" size={14} />PDF</a>
          {canEdit && d.status !== 'draft' && (
            <button type="button" className="btn btn-secondary btn-xs" onClick={() => onEmail(d.invoice_id)}>
              <Icon name="mail" size={14} />Email
            </button>
          )}
        </div>
      </div>
    </li>
  );
}
