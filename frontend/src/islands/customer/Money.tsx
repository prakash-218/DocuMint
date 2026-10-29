import { useId, useMemo, useState } from 'react';
import { day, money } from '../../format';
import type { Account } from './types';

/** Their account, as a ledger: each invoice they owe (debit) and each payment they made (credit), oldest first,
    with the balance after it; one financial year at a time, with what was brought forward. */
export function Statement({ accounts }: { accounts: Account[] }) {
  const id = useId();
  const [currency, setCurrency] = useState(accounts[0]?.currency ?? 'INR');
  const account = accounts.find((a) => a.currency === currency) ?? accounts[0];
  const years = useMemo(() => [...new Set((account?.lines ?? []).map((l) => l.fy).filter(Boolean))].reverse() as string[], [account]);
  const [year, setYear] = useState(years[0] ?? '');

  if (!account) {
    return <div className="rows"><p className="empty-rows" style={{ borderTop: 0 }}>No invoices or payments yet.</p></div>;
  }
  const fy = years.includes(year) ? year : '';
  const first = fy ? account.lines.findIndex((l) => l.fy === fy) : 0;
  const lines = fy ? account.lines.filter((l) => l.fy === fy) : account.lines;
  const opening = fy && first > 0 ? account.lines[first - 1].balance : 0;
  const closing = lines.length ? lines[lines.length - 1].balance : opening;
  const cur = account.currency;

  return (
    <>
      <div className="toolbar">
        <span className="muted">{fy ? `FY ${fy}` : 'Every year'}, as of {day(new Date().toISOString())}. Proformas aren't on a statement until paid.</span>
        <span style={{ flex: 1 }} />
        {accounts.length > 1 && (
          <>
            <label htmlFor={`${id}-cur`} className="sr-only">Currency</label>
            <select id={`${id}-cur`} value={currency} onChange={(e) => { setCurrency(e.target.value); setYear(''); }}>
              {accounts.map((a) => <option key={a.currency} value={a.currency}>{a.currency}</option>)}
            </select>
          </>
        )}
        <label htmlFor={`${id}-fy`} className="sr-only">Financial year</label>
        <select id={`${id}-fy`} value={fy} onChange={(e) => setYear(e.target.value)}>
          {years.map((y) => <option key={y} value={y}>FY {y}</option>)}
          <option value="">Every year</option>
        </select>
      </div>
      <div className="xscroll ctable" style={{ marginTop: 12 }}>
        <table className="ledger">
          <thead><tr><th>Date</th><th>Entry</th><th className="r">Debit</th><th className="r">Credit</th><th className="r">Balance</th></tr></thead>
          <tbody>
            {fy && <tr><td /><td>Opening balance</td><td /><td /><td className="r">{money(opening, cur)}</td></tr>}
            {lines.map((l, i) => (
              <tr key={`${l.url}-${i}`}>
                <td style={{ whiteSpace: 'nowrap' }}>{day(l.date)}</td>
                <td><a href={l.url}>{l.text}</a>{l.sub && <small>{l.sub}</small>}</td>
                <td className="r">{l.owed ? money(l.owed, cur) : ''}</td>
                <td className="r">{l.paid ? money(l.paid, cur) : ''}</td>
                <td className="r">{money(l.balance, cur)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr><td /><td>{closing < -0.005 ? 'Paid ahead (an advance not on an invoice yet)' : 'Balance due'}</td><td /><td />
              <td className="r">{money(closing, cur)}</td></tr>
          </tfoot>
        </table>
      </div>
    </>
  );
}
