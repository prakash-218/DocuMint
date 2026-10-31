import { useId } from 'react';
import { ask } from '../../app/ui';
import { day } from '../../format';
import { Icon } from '../../icons';

// What's arrived on a purchase order (document_page._receiving, receiving.py): each line's ordered, received and
// still to come; each delivery with the supplier's challan no.; and the form for the next one, each line's quantity
// starting at what's still to come. Once everything has come, the order is received by itself.

export interface ReceivingLine { line: number; description: string; qty: number; unit: string; received: number; left: number }
export interface Receiving {
  lines: ReceivingLine[];
  state: 'none' | 'part' | 'all';
  deliveries: { id: string; date: string | null; challan: string; note: string; by: string;
                lines: { description: string; qty: number; unit: string }[]; delete: string | null }[];
  record: { action: string; today: string } | null;
}

const n = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(2).replace(/\.?0+$/, ''));
const qty = (v: number, unit: string) => `${n(v)}${unit ? ` ${unit}` : ''}`;

export function ReceivingCard({ receiving: r }: { receiving: Receiving }) {
  const id = useId();
  const arrived = r.lines.filter((l) => l.left <= 1e-9).length;
  return (
    <section className="card" aria-labelledby={`${id}-h`} id="receiving">
      <div className="card-h">
        <h2 id={`${id}-h`}>What arrived</h2>
        <span className="doc-type">{r.state === 'all' ? 'Everything has arrived' : r.state === 'part' ? `${arrived} of ${r.lines.length} lines in full` : 'Nothing yet'}</span>
      </div>
      <div className="card-b">
        <table className="recv-table">
          <thead><tr><th>Line</th><th className="num">Ordered</th><th className="num">Arrived</th><th className="num">Still to come</th></tr></thead>
          <tbody>
            {r.lines.map((l) => (
              <tr key={l.line} className={l.left <= 1e-9 ? 'recv-done' : undefined}>
                <td>{l.line}. {l.description}</td>
                <td className="num">{qty(l.qty, l.unit)}</td>
                <td className="num">{l.received ? qty(l.received, l.unit) : '—'}</td>
                <td className="num">{l.left > 1e-9 ? qty(l.left, l.unit) : <Icon name="check" />}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {r.deliveries.length > 0 && (
          <ul className="pays recv-deliveries" aria-label="Deliveries">
            {r.deliveries.map((d) => (
              <li key={d.id}>
                <span>
                  {[day(d.date), d.challan && `Challan ${d.challan}`, d.by].filter(Boolean).join(' · ')}
                  <br /><span className="muted">{d.lines.map((x) => `${qty(x.qty, x.unit)} ${x.description}`).join('; ')}</span>
                  {d.note && <><br /><span className="muted">{d.note}</span></>}
                  {d.delete && (
                    <form method="post" action={d.delete} style={{ display: 'inline' }} onSubmit={ask('Take this delivery off? What arrived is counted again.')}>
                      {' · '}<button type="submit" className="link-button">Take off</button>
                    </form>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}

        {r.record && (
          <details className="fold-in" open={r.deliveries.length === 0}>
            <summary>Record what arrived</summary>
            <form method="post" action={r.record.action} className="recv-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor={`${id}-on`} className="form-label">Arrived on</label>
                  <input type="date" id={`${id}-on`} name="received_on" className="form-input" defaultValue={r.record.today} required />
                </div>
                <div className="form-group">
                  <label htmlFor={`${id}-dc`} className="form-label">Their delivery challan no.</label>
                  <input type="text" id={`${id}-dc`} name="challan_no" className="form-input" maxLength={60} />
                </div>
              </div>
              {r.lines.filter((l) => l.left > 1e-9).map((l) => (
                <div className="form-group recv-line" key={l.line}>
                  <label htmlFor={`${id}-q${l.line}`} className="form-label">{l.line}. {l.description}</label>
                  <input type="number" id={`${id}-q${l.line}`} name={`qty_${l.line}`} className="form-input" min={0} max={l.left} step="any"
                         defaultValue={n(l.left)} />
                  <span className="form-text">of {qty(l.left, l.unit)} still to come</span>
                </div>
              ))}
              <div className="form-group">
                <label htmlFor={`${id}-note`} className="form-label">Note</label>
                <input type="text" id={`${id}-note`} name="note" className="form-input" placeholder="Two short; the rest next week" />
              </div>
              <button type="submit" className="btn btn-primary btn-sm"><Icon name="check" />Record it</button>
            </form>
          </details>
        )}
      </div>
    </section>
  );
}
