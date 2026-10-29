import { useId, useMemo, useState } from 'react';
import { day, money, totals } from '../../format';
import type { Account, Money } from './types';

/** What they owe on sent invoices, how old it is, and the advances held and asked for. */
export function Owed({ money: m }: { money: Money }) {
  const held = Object.keys(m.advance_held).length > 0;
  return (
    <section className="card cp-owed" aria-labelledby="cp-owed">
      <div className="card-body">
        <div className="cp-owed-top">
          <div>
            <h2 className="cp-cap" id="cp-owed">Due on invoices</h2>
            <p className={`cp-big${m.count ? ' is-due' : ''}`}>{m.count ? totals(m.total) : 'Nothing due'}</p>
            {m.count > 0 && <p className="cp-note">on {m.count} invoice{m.count === 1 ? '' : 's'}</p>}
          </div>
          {held && (
            <div>
              <span className="cp-cap">Advance held</span>
              <p className="cp-mid">{totals(m.advance_held)}</p>
              <p className="cp-note">received on proformas, not on an invoice yet</p>
            </div>
          )}
          {m.advances.count > 0 && (
            <div>
              <span className="cp-cap">Advances asked for</span>
              <p className="cp-mid">{totals(m.advances.total)}</p>
              <p className="cp-note">on {m.advances.count} project{m.advances.count === 1 ? '' : 's'}</p>
            </div>
          )}
        </div>
        {m.count > 0 && (
          <ul className="cp-ages" aria-label="How old what's due is">
            {m.ages.map((a) => (
              <li key={a.label} className={a.count ? 'has-due' : ''}>
                <span className="cp-cap">{a.label}</span>
                <b>{a.count ? totals(a.total) : '—'}</b>
              </li>
            ))}
          </ul>
        )}
        {m.customers && m.customers.length > 1 && (
          <ul className="cp-by-site" aria-label="Due by site">
            {m.customers.map((c) => <li key={c.id}><span>{c.name}</span><b>{totals(c.total)}</b></li>)}
          </ul>
        )}
      </div>
    </section>
  );
}

/** Their account: each invoice they owe and each payment they made, oldest first, with the balance after it. */
export function Statement({ accounts }: { accounts: Account[] }) {
  const id = useId();
  const [currency, setCurrency] = useState(accounts[0]?.currency ?? 'INR');
  const account = accounts.find((a) => a.currency === currency) ?? accounts[0];
  const years = useMemo(() => [...new Set((account?.lines ?? []).map((l) => l.fy).filter(Boolean))].reverse() as string[],
                        [account]);
  const [year, setYear] = useState('');

  if (!account) {
    return <div className="card-body"><p className="text-tertiary pp-empty">No invoices or payments yet.</p></div>;
  }
  const first = year ? account.lines.findIndex((l) => l.fy === year) : 0;
  const lines = year ? account.lines.filter((l) => l.fy === year) : account.lines;
  const opening = year && first > 0 ? account.lines[first - 1].balance : 0;
  const closing = lines.length ? lines[lines.length - 1].balance : opening;
  const cur = account.currency;

  return (
    <div className="cp-statement">
      <div className="cp-bar">
        <p className="cp-note">
          Invoices they owe and payments they made, advances included from the day they came in. Quotations and
          proformas aren't owed, so they aren't here.
        </p>
        <div className="cp-filters">
          {accounts.length > 1 && (
            <>
              <label htmlFor={`${id}-cur`} className="sr-only">Currency</label>
              <select id={`${id}-cur`} className="form-select" value={currency} onChange={(e) => { setCurrency(e.target.value); setYear(''); }}>
                {accounts.map((a) => <option key={a.currency} value={a.currency}>{a.currency}</option>)}
              </select>
            </>
          )}
          <label htmlFor={`${id}-fy`} className="sr-only">Financial year</label>
          <select id={`${id}-fy`} className="form-select" value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="">All years</option>
            {years.map((y) => <option key={y} value={y}>FY {y}</option>)}
          </select>
        </div>
      </div>
      <div className="table-container cp-table-wrap">
        <table className="table cp-table cp-ledger">
          <thead>
            <tr><th>Date</th><th>Details</th><th className="num">Owed</th><th className="num">Paid</th><th className="num">Balance</th></tr>
          </thead>
          <tbody>
            {year && (
              <tr className="cp-opening"><td /><td>Brought forward</td><td /><td /><td className="num">{money(opening, cur)}</td></tr>
            )}
            {lines.map((l, i) => (
              <tr key={`${l.url}-${i}`}>
                <td className="cp-date">{day(l.date)}{l.fy && <span className="cell-secondary">FY {l.fy}</span>}</td>
                <td><a href={l.url}>{l.text}</a>{l.sub && <span className="cell-secondary">{l.sub}</span>}</td>
                <td className="num">{l.owed ? money(l.owed, cur) : ''}</td>
                <td className="num cp-paid">{l.paid ? money(l.paid, cur) : ''}</td>
                <td className="num">{money(l.balance, cur)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td />
              <th scope="row">{year ? `Balance at the end of FY ${year}` : 'Balance now'}</th>
              <td className="num">{money(lines.reduce((s, l) => s + l.owed, 0), cur)}</td>
              <td className="num">{money(lines.reduce((s, l) => s + l.paid, 0), cur)}</td>
              <td className={`num${closing > 0.005 ? ' is-due' : ''}`}><b>{money(closing, cur)}</b></td>
            </tr>
          </tfoot>
        </table>
      </div>
      {closing < -0.005 && (
        <p className="cp-note">A balance below zero is money they paid ahead: an advance not taken off an invoice yet.</p>
      )}
    </div>
  );
}
