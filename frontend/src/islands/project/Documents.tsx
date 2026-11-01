import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Doc, Tone } from './types';

// A document as the project's thread shows it (Thread.tsx): what it is, where it stands, its number and amount, its
// earlier versions and what can be done with it.

export function status(d: Doc): { text: string; tone: Tone } {
  if (d.status === 'draft') return { text: 'Draft', tone: 'draft' };
  if (d.status === 'issued') return { text: 'Issued', tone: 'done' };
  if (d.status === 'cancelled') return { text: 'Cancelled', tone: 'draft' };
  if (d.status === 'declined') return { text: 'Declined', tone: 'late' };
  if (d.status === 'accepted') return { text: 'Accepted', tone: 'done' };
  if (d.status === 'converted') return { text: d.doc_type === 'quote' ? 'Accepted' : 'Invoiced', tone: 'done' };
  if (d.status === 'revised') return { text: 'Revised', tone: 'draft' };
  if (d.status === 'paid') return { text: 'Paid', tone: 'done' };
  if (d.status === 'confirmed') return { text: 'Confirmed', tone: 'wait' };
  if (d.status === 'received') return { text: 'Received', tone: 'done' };
  if (d.doc_type === 'proforma' && d.paid > 0) return { text: 'Advance received', tone: 'done' };
  if (d.status === 'pending') return d.paid > 0 ? { text: 'Part paid', tone: 'wait' } : { text: 'Unpaid', tone: 'wait' };
  return { text: 'Sent', tone: 'wait' };
}

interface BoxProps {
  doc: Doc;
  canEdit: boolean;
  onEmail?: (invoiceId: string) => void;
  /** Where taking it out of the project posts (projects_bp.project_document); none for purchase orders. */
  documentsUrl?: string | null;
}

export function DocBox({ doc: d, canEdit, onEmail, documentsUrl = null }: BoxProps) {
  const s = status(d);
  return (
    <div className="doc-box">
      <div className="doc-top">
        <span className="doc-type">{d.kind}{d.party && d.doc_type === 'purchase_order' ? ` · ${d.party}` : ''}</span>
        <span className={`tag tone-${s.tone}`}>{s.text}</span>
      </div>
      <div className="doc-row">
        <a className="doc-no" href={d.url}>{d.number}</a>
        <span className="doc-amt">{d.adjusts === -1 ? '−' : d.adjusts === 1 ? '+' : ''}{money(d.total, d.currency)}</span>
      </div>
      <div className="doc-meta">
        {[day(d.issue_date) && `${d.status === 'draft' ? 'started' : d.adjusts ? 'issued' : 'sent'} ${day(d.issue_date)}`,
          d.against ? `against ${d.against}` : '',
          d.refunded ? `${money(d.refunded, d.currency)} refunded` : '',
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
        {canEdit && onEmail && d.status !== 'draft' && (
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
  );
}
