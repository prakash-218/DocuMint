import { Icon, type IconName } from '../../icons';
import type { Action, Page, Progress, Step } from './types';

const STEP_ICON: Partial<Record<Step['state'], IconName>> = { done: 'check', late: 'alert' };
const TONE_ICON: Record<string, IconName> = { action: 'flag', wait: 'clock', late: 'alert', done: 'done', draft: 'info' };

/** Quoted → Accepted → Advance → Invoiced → Paid, worked out from the documents. */
export function Tracker({ steps }: { steps: Step[] }) {
  return (
    <ol className="tracker" aria-label="Where the job is" style={{ ['--steps' as string]: steps.length }}>
      {steps.map((s) => (
        <li key={s.key} className={s.state} aria-current={s.state === 'now' || s.state === 'late' ? 'step' : undefined}>
          <span className="lbl">{STEP_ICON[s.state] && <Icon name={STEP_ICON[s.state]!} size={14} />}{s.label}</span>
          {s.sub && <span className="sub">{s.sub}</span>}
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
    <div className={`next tone-${next.tone}`}>
      <div className="next-text">
        <span className="next-ico"><Icon name={TONE_ICON[next.tone] ?? 'info'} size={18} /></span>
        <div>
          <p>{next.text}</p>
          {next.sub && <small>{next.sub}</small>}
        </div>
      </div>
      {next.actions.length > 0 && (
        <div className="next-actions">
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
        <form method="post" action={a.action} className="inline-form"
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

/** Where the job stands on each count, apart from the others: the quotation, the advance, the material bought for
 *  it, how much is invoiced and how much has come in (project_view.statuses). */
export function ProgressChips({ items }: { items: Progress[] }) {
  return (
    <ul className="progress" aria-label="Where the job stands" style={{ ['--n' as string]: items.length }}>
      {items.map((p) => (
        <li key={p.key} className={`pg pg-${p.tone}`}>
          <small>{p.label}</small>
          <b>{p.text}</b>
          <span className="pg-bar" aria-hidden="true"><i style={{ width: `${Math.round(p.bar * 100)}%` }} /></span>
          {p.sub && <span className="pg-sub">{p.sub}</span>}
        </li>
      ))}
    </ul>
  );
}
