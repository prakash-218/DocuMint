import { money } from '../../format';
import type { Page, Profit } from './types';

// What the job makes, before GST (project_view.profit): as costed, as committed (the quotation it took, and every
// costing line bought on a purchase order at that order's price) and as it actually stands (invoiced, and what
// has arrived). The costing's lines on no order, the job's own work, count as costed throughout.

const COLUMNS: ['costed' | 'committed' | 'actual', string][] = [['costed', 'Costed'], ['committed', 'Committed'], ['actual', 'Actual']];

export function ProfitCard({ profit, costings }: { profit: Profit; costings: Page['costings'] }) {
  const cur = profit.currency;
  const revenue = profit.rows.find((r) => r.key === 'revenue');
  const link = profit.costing && costings?.find((k) => k.id === profit.costing!.id)?.url;
  const cell = (key: string, v: number | null) =>
    v === null ? '—' : key === 'revenue' || key === 'margin' ? money(v, cur) : `−${money(v, cur)}`;
  return (
    <section className="card" aria-labelledby="pp-profit">
      <div className="card-h">
        <h2 id="pp-profit">Profit on this job</h2>
        {profit.costing && (link ? <a className="doc-type" href={link}>{profit.costing.title}</a> : <span className="doc-type">{profit.costing.title}</span>)}
      </div>
      <div className="card-b">
        <div className="profit-wrap">
          <table className="profit-table">
            <caption className="sr-only">Before GST</caption>
            <thead><tr><th scope="col"><span className="sr-only">What</span></th>{COLUMNS.map(([k, label]) => <th key={k} scope="col">{label}</th>)}</tr></thead>
            <tbody>
              {profit.rows.map((r) => (
                <tr key={r.key} className={r.key === 'margin' ? 'pt-margin' : undefined}>
                  <th scope="row">{r.label}</th>
                  {COLUMNS.map(([k]) => {
                    const v = r[k];
                    const base = revenue?.[k];
                    return (
                      <td key={k} className={r.key === 'margin' && v !== null && v < 0 ? 'late' : undefined}>
                        {cell(r.key, v)}
                        {r.key === 'margin' && v !== null && base ? <small>{Math.round((v / base) * 1000) / 10}%</small> : null}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {profit.notes.map((n) => <p key={n.text} className={`profit-note${n.tone ? ` tone-${n.tone}` : ''}`}>{n.text}</p>)}
      </div>
    </section>
  );
}
