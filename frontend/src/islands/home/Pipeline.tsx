import { useEffect, useRef, useState } from 'react';
import { money, totals } from '../../format';
import { Icon } from '../../icons';
import type { Action } from '../project/types';

// The Work home's money bar and pipeline (home_view.work): what's waiting on an answer, to bill, asked as an
// advance, unpaid and received, each picking out its columns; and every open job in its stage's column with how long
// it has been there and its next step. Dropping a job on the next column (or → on it) offers the step that moves it
// on, as the project page has it; dropping it anywhere else offers its project.

type Totals = Record<string, number>;
export interface Card {
  id: string; label: string; title: string; url: string; customer: { name: string | null; site?: string | null };
  tone: string; next: string; action: string | null;
  /** What moves it to the next column (project_view.next_step's 'move'), or null */
  move: Action | null;
  days: number | null; late: number | null; amount: number | null; currency: string;
}
export interface Work {
  bar: { key: string; label: string; total: Totals; count: number | null; columns: string[]; late?: Totals | null; url?: string }[];
  columns: { key: string; label: string; count: number; total: Totals; cards: Card[] }[];
}

// Each tile's and column's colour: the bar's tile and the column it picks out share one
const SEG: Record<string, string> = {
  answer: 'var(--amber)', bill: 'var(--info)', advance: 'var(--accent)', unpaid: 'var(--red)', received: 'var(--mint)',
  quoted: 'var(--line-2)', accepted: 'var(--amber)', invoiced: 'var(--info)', paid: 'var(--red)',
};

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;
const sum = (t: Totals) => (Object.keys(t).length ? totals(t) : money(0));

/** How long it has been there: amber after five days, red after ten, and an unpaid invoice's days past due */
function Since({ card, paying }: { card: Card; paying: boolean }) {
  if (card.late) return <span className="pill tone-late">{plural(card.late, 'day', 'days')} late</span>;
  if (card.days == null) return <span />;
  if (paying) return <span className="pill tone-draft">{plural(card.days, 'day', 'days')}</span>;
  const tone = card.days > 10 ? 'late' : card.days > 5 ? 'action' : 'done';
  return <span className={`pill tone-${tone}`}>{card.days > 5 ? `${card.days} days here` : plural(card.days, 'day', 'days')}</span>;
}

export function MoneyBar({ work, picked, onPick }: { work: Work; picked: string | null; onPick: (key: string | null) => void }) {
  return (
    <div className="moneybar" role="group" aria-label="Money" style={{ ['--n' as string]: work.bar.length }}>
      {work.bar.map((b) => {
        const body = (
          <>
            <span>{b.label}</span>
            <b>{sum(b.total)}</b>
            <small className={b.late ? 'late' : undefined}>
              {b.late ? `${totals(b.late)} late` : b.count == null ? ' '
                : b.key === 'unpaid' ? plural(b.count, 'invoice', 'invoices') : plural(b.count, 'job', 'jobs')}
            </small>
          </>
        );
        const style = { ['--seg' as string]: SEG[b.key] ?? 'var(--line-2)' };
        return b.url ? <a key={b.key} href={b.url} style={style}>{body}</a> : (
          <button key={b.key} type="button" style={style} aria-pressed={picked === b.key}
                  onClick={() => onPick(picked === b.key ? null : b.key)}>{body}</button>
        );
      })}
    </div>
  );
}

interface Move { card: Card; to: string; next: boolean }

/** The step a drop offers, to take or cancel: a link, a form to post, or (for what the project page does itself) its page */
function MoveDialog({ move, onClose }: { move: Move; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (d.showModal) d.showModal();
    else d.setAttribute('open', '');
    d.querySelector<HTMLElement>('[data-go]')?.focus();
  }, []);
  const c = move.card;
  const a = move.next ? c.move : null;
  const go = a?.kind === 'link' || a?.kind === 'post' ? a : null;
  return (
    <dialog ref={ref} className="k-dialog wh-dialog" aria-labelledby="wh-move-title" onClose={onClose}
            onClick={(e) => { if (e.target === ref.current) onClose(); }}>
      <div className="k-dialog-head">
        <h2 id="wh-move-title">{a ? a.label : c.title}</h2>
        <button type="button" className="btn btn-ghost btn-xs" aria-label="Close" onClick={onClose}><Icon name="x" /></button>
      </div>
      <div className="k-dialog-body">
        {a && <p className="k-dialog-sub">{c.title}</p>}
        <p className="muted">{c.label} · {c.customer.site || c.customer.name}{c.amount ? ` · ${money(c.amount, c.currency)}` : ''}</p>
        {a?.kind === 'post' && a.confirm && <p>{a.confirm}</p>}
      </div>
      <div className="k-dialog-foot">
        <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
        {go?.kind === 'link' && <a className="btn btn-primary" href={go.href} data-go>{go.label}</a>}
        {go?.kind === 'post' && (
          <form method="post" action={go.action} className="inline-form">
            {Object.entries(go.fields).map(([k, v]) => <input key={k} type="hidden" name={k} value={v} />)}
            <button type="submit" className="btn btn-primary" data-go>{go.label}</button>
          </form>
        )}
        {!go && <a className="btn btn-primary" href={c.url} data-go>Open the project</a>}
      </div>
    </dialog>
  );
}

export function Pipeline({ work, picked }: { work: Work; picked: string | null }) {
  const [move, setMove] = useState<Move | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const lit = picked ? work.bar.find((b) => b.key === picked)?.columns ?? [] : null;
  const order = work.columns.map((c) => c.key);
  const offer = (card: Card, from: string, to: string) => {
    if (from !== to) setMove({ card, to, next: order.indexOf(to) === order.indexOf(from) + 1 });
  };
  const at = (id: string | null) => work.columns.find((x) => x.cards.some((k) => k.id === id));
  return (
    <>
      <div className="board pipeline" style={{ ['--cols' as string]: work.columns.length }}>
        {work.columns.map((col, i) => {
          const last = i === work.columns.length - 1;
          return (
            <section key={col.key} aria-labelledby={`wh-col-${col.key}`} data-col={col.key}
                     className={`pcol${lit && !lit.includes(col.key) ? ' dim' : ''}${over === col.key ? ' over' : ''}`}
                     onDragOver={(e) => { if (dragging) { e.preventDefault(); setOver(col.key); } }}
                     onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setOver(null); }}
                     onDrop={(e) => {
                       e.preventDefault(); setOver(null);
                       const from = at(dragging), card = from?.cards.find((k) => k.id === dragging);
                       if (from && card) offer(card, from.key, col.key);
                     }}>
              <h3 id={`wh-col-${col.key}`} style={{ ['--seg' as string]: SEG[col.key] ?? 'var(--line-2)' }}>
                <b>{col.label}</b><span className="n">{col.count}</span><span className="t">{Object.keys(col.total).length ? totals(col.total) : ''}</span>
              </h3>
              {col.cards.map((card) => (
                <article key={card.id} className={`jcard${dragging === card.id ? ' dragging' : ''}`} draggable tabIndex={0}
                         aria-label={`${card.title}, ${card.customer.site || card.customer.name}`} aria-keyshortcuts={last ? undefined : 'ArrowRight'}
                         onDragStart={(e) => { setDragging(card.id); e.dataTransfer.effectAllowed = 'move';
                                               try { e.dataTransfer.setData('text/plain', card.label); } catch { /* older browsers */ } }}
                         onDragEnd={() => { setDragging(null); setOver(null); }}
                         onKeyDown={(e) => { if (e.key === 'ArrowRight' && !last && e.target === e.currentTarget) { e.preventDefault(); offer(card, col.key, order[i + 1]); } }}>
                  <a href={card.url} className="t1" draggable={false}>{card.title}</a>
                  <span className="t2"><span className="mono">{card.label}</span> · {card.customer.site || card.customer.name}</span>
                  <span className="row"><Since card={card} paying={col.key === 'paid'} />
                    <span className="amt">{card.amount ? money(card.amount, card.currency) : '—'}</span></span>
                  {card.move && !last ? (
                    <button type="button" className="jnext" onClick={() => offer(card, col.key, order[i + 1])}>Next: {card.move.label}</button>
                  ) : <span className="jnext">{card.action ? `Next: ${card.action}` : card.next}</span>}
                </article>
              ))}
            </section>
          );
        })}
      </div>
      {move && <MoveDialog move={move} onClose={() => setMove(null)} />}
    </>
  );
}
