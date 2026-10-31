import { day, money, totals } from '../../format';
import { Icon } from '../../icons';
import type { Doc } from './types';

// What's bought for the project: its purchase orders to suppliers (project_view's purchases), apart from what's sold.
// Each says who it's to, where it stands and its value; the open ones add up to what's still on order.

const STATES: Record<string, { text: string; tone: string }> = {
  draft: { text: 'Draft', tone: 'draft' }, sent: { text: 'Sent', tone: 'wait' }, confirmed: { text: 'Confirmed', tone: 'wait' },
  received: { text: 'Received', tone: 'done' }, cancelled: { text: 'Cancelled', tone: 'draft' },
};

export function Purchases({ docs, newUrl }: { docs: Doc[]; newUrl?: string }) {
  if (!docs.length && !newUrl) return null;
  const sums = (rows: Doc[]) => {
    const out: Record<string, number> = {};
    for (const d of rows) out[d.currency || 'INR'] = (out[d.currency || 'INR'] ?? 0) + d.total;
    return out;
  };
  const live = docs.filter((d) => d.status !== 'cancelled');
  const open = live.filter((d) => d.status !== 'received' && d.status !== 'draft');
  return (
    <section className="card" aria-labelledby="pp-purchases">
      <div className="card-h">
        <h2 id="pp-purchases">Purchases</h2>
        {live.length > 0 && (
          <span className="doc-type">{totals(sums(live))} ordered{open.length ? ` · ${totals(sums(open))} still to arrive` : ''}</span>
        )}
      </div>
      <div className="card-b">
        {docs.length ? (
          <ul className="purchase-list">
            {docs.map((d) => {
              const st = STATES[d.status] ?? STATES.sent;
              return (
                <li key={d.invoice_id}>
                  <div className="pl-main">
                    <a className="doc-no link mono" href={d.url}>{d.number}</a>
                    <span className="doc-meta">{[d.party, d.site].filter(Boolean).join(' · ')}{d.issue_date ? ` · ${day(d.issue_date)}` : ''}</span>
                  </div>
                  <span className={`tag tone-${st.tone}`}>{st.text}</span>
                  <span className="doc-amt">{money(d.total, d.currency)}</span>
                </li>
              );
            })}
          </ul>
        ) : <p className="muted" style={{ margin: 0 }}>Nothing bought for it yet. A purchase order goes to one of your suppliers.</p>}
        {newUrl && (
          <div className="doc-actions">
            <a className="btn btn-secondary btn-sm" href={newUrl}><Icon name="plus" />New purchase order</a>
          </div>
        )}
      </div>
    </section>
  );
}
