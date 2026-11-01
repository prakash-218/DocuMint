import { useId } from 'react';
import { ask } from '../../app/ui';
import { day, money } from '../../format';
import { Icon } from '../../icons';
import type { Tone } from '../project/types';

// An invoice's credit and debit notes (document_page._notes), each with its state and amount, a credit note's taken
// off; and a credit note's refunds (document_page._refunds): what was paid back, and the form to record more while its
// invoice owes the customer something back.

export interface NoteRow {
  id: string;
  number: string;
  kind: string;
  date: string | null;
  pill: { text: string; tone: Tone };
  reason: string;
  amount: number;
  url: string;
}

export interface Refunds {
  rows: { id: string; date: string | null; amount: number; reference: string; by: string; delete: string | null }[];
  /** What its invoice still owes back to the customer. */
  owed: number;
  against: string;
  currency: string;
  record: { action: string; today: string; suggested: number } | null;
}

const signed = (v: number, currency: string) => (v < 0 ? `−${money(-v, currency)}` : money(v, currency));

export function NotesCard({ notes, currency }: { notes: NoteRow[]; currency: string }) {
  const id = useId();
  return (
    <section className="card" aria-labelledby={`${id}-h`} id="notes">
      <div className="card-h"><h2 id={`${id}-h`}>Credit and debit notes</h2></div>
      <div className="card-b">
        <ul className="pays" aria-label="Notes">
          {notes.map((n) => (
            <li key={n.id}>
              <span>
                <a href={n.url} className="mono">{n.number}</a>{' '}
                <span className={`tag tone-${n.pill.tone}`}>{n.pill.text}</span>
                <br /><span className="muted">{[n.kind, day(n.date), n.reason].filter(Boolean).join(' · ')}</span>
              </span>
              <span className="mono">{signed(n.amount, currency)}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function RefundsCard({ refunds: r }: { refunds: Refunds }) {
  const id = useId();
  return (
    <section className="card" aria-labelledby={`${id}-h`} id="refunds">
      <div className="card-h">
        <h2 id={`${id}-h`}>Refunds</h2>
        <span className="doc-type">{r.owed > 0.005 ? `${money(r.owed, r.currency)} to refund on ${r.against}` : 'Nothing to refund'}</span>
      </div>
      <div className="card-b">
        {r.rows.length > 0 && (
          <ul className="pays" aria-label="Refunded">
            {r.rows.map((x) => (
              <li key={x.id}>
                <span>
                  {[day(x.date), x.reference, x.by].filter(Boolean).join(' · ')}
                  {x.delete && (
                    <form method="post" action={x.delete} style={{ display: 'inline' }} onSubmit={ask('Take this refund off?')}>
                      {' · '}<button type="submit" className="link-button">Take off</button>
                    </form>
                  )}
                </span>
                <span className="mono">{money(x.amount, r.currency)}</span>
              </li>
            ))}
          </ul>
        )}
        {r.record && (
          <details className="fold-in" open={r.rows.length === 0}>
            <summary>Record a refund</summary>
            <form method="post" action={r.record.action}>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor={`${id}-amount`} className="form-label">Amount ({r.currency})</label>
                  <input type="number" step="0.01" min="0.01" max={r.owed} id={`${id}-amount`} name="amount" className="form-input"
                         defaultValue={r.record.suggested.toFixed(2)} required />
                </div>
                <div className="form-group">
                  <label htmlFor={`${id}-on`} className="form-label">Refunded on</label>
                  <input type="date" id={`${id}-on`} name="refunded_on" className="form-input" defaultValue={r.record.today} max={r.record.today} required />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor={`${id}-ref`} className="form-label">Bank reference</label>
                <input type="text" id={`${id}-ref`} name="reference" className="form-input" maxLength={100} placeholder="UTR or cheque no." />
              </div>
              <button type="submit" className="btn btn-primary btn-sm"><Icon name="check" />Record refund</button>
            </form>
          </details>
        )}
      </div>
    </section>
  );
}
