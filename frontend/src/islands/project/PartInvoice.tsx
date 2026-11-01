import { useState } from 'react';
import { money } from '../../format';
import type { PartInvoice } from './types';

// A tax invoice for part of the quotation the job took (project_view.part_invoice): by percent or by an amount
// before GST, never past what's left; its GST, the advance on the proforma that goes with it (whole payments, while
// they fit), and what's left after it. The form posts to invoices_bp.convert, which makes the draft and opens it.

const round = (n: number) => Math.round(n * 100) / 100;
const pc = (n: number) => `${Math.round(n * 10) / 10}%`;

export function PartInvoiceCard({ part }: { part: PartInvoice }) {
  const left = Math.max(0, part.base - part.invoiced);
  const leftPct = (left / part.base) * 100;
  const [mode, setMode] = useState<'percent' | 'amount'>('percent');
  const [percent, setPercent] = useState(() => Math.min(50, Math.floor(leftPct)) || Math.floor(leftPct * 10) / 10);
  const [amount, setAmount] = useState(() => String(Math.round(left)));
  const cur = part.currency;

  const taxable = mode === 'percent' ? round((part.base * percent) / 100) : Math.max(0, round(Number(amount.replace(/,/g, '')) || 0));
  const gst = round((taxable * part.tax.rate) / 100);
  const total = round(taxable + gst);
  let held = 0;                                                   // whole advance payments, in order, while they fit
  for (const a of part.advances) if (held + a <= total + 0.005) held += a;
  const tax = part.tax.mode === 'cgst_sgst' ? `CGST + SGST ${part.tax.rate}%` : `IGST ${part.tax.rate}%`;
  const over = taxable > left + 1;

  return (
    <section className="card" aria-labelledby="pp-part">
      <div className="card-h">
        <h2 id="pp-part">Invoice part of {part.quote}</h2>
        <span className="doc-type">{pc((part.invoiced / part.base) * 100)} invoiced</span>
      </div>
      <form className="card-b part-form" method="post" action={part.action}>
        <input type="hidden" name="target" value="invoice" />
        {mode === 'percent' ? <input type="hidden" name="part_percent" value={percent} />
          : <input type="hidden" name="part_amount" value={taxable} />}
        <div className="seg2" role="group" aria-label="Invoice by">
          <button type="button" aria-pressed={mode === 'percent'} onClick={() => setMode('percent')}>Percent</button>
          <button type="button" aria-pressed={mode === 'amount'} onClick={() => setMode('amount')}>Amount</button>
        </div>
        {mode === 'percent' ? (
          <div className="part-slide">
            <input type="range" id="pp-part-pc" min={1} max={Math.max(1, Math.floor(leftPct))} step={1} value={percent}
                   aria-label={`Percent of ${part.quote}`} onChange={(e) => setPercent(Number(e.target.value))} />
            <output htmlFor="pp-part-pc">{pc(percent)}</output>
          </div>
        ) : (
          <label className="part-amount">
            <span>Before GST</span>
            <input type="text" inputMode="decimal" id="pp-part-amt" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </label>
        )}
        <dl className="part-rows">
          <div><dt>{part.quote}, before GST</dt><dd>{money(part.base, cur)}</dd></div>
          <div><dt>Invoiced so far</dt><dd>{money(part.invoiced, cur)}</dd></div>
          <div className="pr-this"><dt>This invoice</dt><dd>{money(total, cur)}</dd></div>
          {part.tax.rate > 0 && <div className="pr-sub"><dt>Before GST + {tax}</dt><dd>{money(taxable, cur)} + {money(gst, cur)}</dd></div>}
          {part.advances.length > 0 && <div className="pr-sub"><dt>Advance on {part.source.number} with it</dt><dd>{held ? `−${money(held, cur)}` : '—'}</dd></div>}
          {held > 0 && <div><dt>To pay on it</dt><dd>{money(total - held, cur)}</dd></div>}
          <div className="pr-sub"><dt>Left to invoice after it</dt><dd>{money(Math.max(0, left - taxable), cur)} · {pc(Math.max(0, ((left - taxable) / part.base) * 100))}</dd></div>
        </dl>
        {over && <p className="error" role="alert">That's more than the {money(left, cur)} left to invoice.</p>}
        <button type="submit" className="btn btn-primary btn-block" disabled={over || taxable <= 0}>
          Make the tax invoice for {money(total, cur)}
        </button>
      </form>
    </section>
  );
}
