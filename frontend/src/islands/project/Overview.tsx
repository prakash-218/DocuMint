import { money } from '../../format';
import { Icon, type IconName } from '../../icons';
import type { Action, MoneyRow, Page, Step } from './types';

const STEP_ICON: Partial<Record<Step['state'], IconName>> = { done: 'check', late: 'alert' };
const TONE_ICON: Record<string, IconName> = { action: 'flag', wait: 'clock', late: 'alert', done: 'done', draft: 'info' };

/** Quoted → Accepted → Advance → Invoiced → Paid, worked out from the documents. */
export function Tracker({ steps }: { steps: Step[] }) {
  return (
    <ol className="pp-tracker" aria-label="Where the job is">
      {steps.map((s) => (
        <li key={s.key} className={`is-${s.state}`} aria-current={s.state === 'now' || s.state === 'late' ? 'step' : undefined}>
          <span className="pp-step-label">{STEP_ICON[s.state] && <Icon name={STEP_ICON[s.state]!} size={14} />}{s.label}</span>
          {s.sub && <span className="pp-step-sub">{s.sub}</span>}
        </li>
      ))}
    </ol>
  );
}

interface NextProps {
  next: Page['next'];
  onEmail: (invoiceId: string | null) => void;
  onStatus: (status: string) => void;
}

/** What to do next, with every action that fits; the one that moves the job on is the coloured one. */
export function NextStep({ next, onEmail, onStatus }: NextProps) {
  return (
    <div className={`pp-next tone-${next.tone}`}>
      <div className="pp-next-text">
        <Icon name={TONE_ICON[next.tone] ?? 'info'} size={18} />
        <div>
          <p>{next.text}</p>
          {next.sub && <p className="pp-next-sub">{next.sub}</p>}
        </div>
      </div>
      {next.actions.length > 0 && (
        <div className="pp-next-actions">
          {next.actions.map((a) => <ActionButton key={a.label} action={a} onEmail={onEmail} onStatus={onStatus} />)}
        </div>
      )}
    </div>
  );
}

export function ActionButton({ action: a, onEmail, onStatus }: { action: Action } & Omit<NextProps, 'next'>) {
  const cls = `btn ${a.primary ? 'btn-primary' : 'btn-secondary'}`;
  switch (a.kind) {
    case 'link':
      return <a className={cls} href={a.href}>{a.label}</a>;
    case 'post':
      return (
        <form method="post" action={a.action} className="pp-inline-form"
              onSubmit={(e) => { if (a.confirm && !window.confirm(a.confirm)) e.preventDefault(); }}>
          {Object.entries(a.fields).map(([k, v]) => <input key={k} type="hidden" name={k} value={v} />)}
          <button type="submit" className={cls}>{a.label}</button>
        </form>
      );
    case 'email':
      return <button type="button" className={cls} onClick={() => onEmail(a.invoice_id)}><Icon name="mail" />{a.label}</button>;
    case 'status':
      return <button type="button" className={cls} onClick={() => onStatus(a.status)}>{a.label}</button>;
    case 'dialog': // a <dialog> on the page, which static/js/app.js opens
      return <button type="button" className={cls} data-open-dialog={a.dialog}>{a.label}</button>;
  }
}

/** The four amounts that matter, per currency. Sales see what was quoted only. */
export function MoneyStrip({ rows, quotedOnly }: { rows: MoneyRow[]; quotedOnly: boolean }) {
  return (
    <div className="pp-money-rows">
      {rows.map((r) => {
        const base = r.quoted || r.invoiced || 0;
        const received = r.received ?? 0;
        return (
          <section className="pp-money" key={r.currency} aria-label={`Amounts in ${r.currency}`}>
            <div>
              <span className="pp-money-label">Quoted</span><b>{r.quoted ? money(r.quoted, r.currency) : '—'}</b>
              {!r.quoted && <span className="pp-money-cap">No quotation</span>}
            </div>
            {!quotedOnly && (
              <>
                <div><span className="pp-money-label">Invoiced</span><b>{money(r.invoiced, r.currency)}</b></div>
                <div>
                  <span className="pp-money-label">Received</span><b>{money(received, r.currency)}</b>
                  {!!r.advance_held && <span className="pp-money-cap">incl. {money(r.advance_held, r.currency)} advance</span>}
                </div>
                <div className={r.due ? 'is-due' : ''}>
                  <span className="pp-money-label">Due</span><b>{money(r.due, r.currency)}</b>
                  {!r.due && <span className="pp-money-cap">Nothing due</span>}
                </div>
                {base > 0 && (
                  <div className="pp-money-bar">
                    <span>{money(received, r.currency)} of {money(base, r.currency)} received</span>
                    <span className="pp-track" aria-hidden="true"><i style={{ width: `${Math.min(100, (received / base) * 100)}%` }} /></span>
                  </div>
                )}
              </>
            )}
          </section>
        );
      })}
    </div>
  );
}
