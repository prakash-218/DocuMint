import { Dropdown, choices } from '../../mantine/Dropdown';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Autocomplete, Text } from '@mantine/core';
import { PageHeader } from '../../app/PageHeader';
import { ask, Loading, useLoad } from '../../app/ui';
import { Icon } from '../../icons';
import { CopyDialog, ImportDialog, PurchaseDialog } from './Dialogs';
import { BLANK_LINE, BLANK_SHARED, blankItem, fromStored, money, num } from './sheet';
import type { CostingData, Item, Line, Rate, Result, Settings, Shared } from './types';

// A costing: the quote's items, each with a typed cost or cost lines, and a profit; or a known total worked back.
// Shared costs are spread over the items. The numbers come from the server (POST .../preview, the same costing.py
// that saves), sent the sheet as it's edited, so what's shown is what's saved. It posts the server page's form to
// costings_bp.save: sheet_json (the sheet as typed), title, mode, profit_percent, target_total, round_to, currency,
// notes, template_id and the button's action (save, quote, update_quote). Costs are in the business's currency
// (base); prices in the quote's.

const plain = (v: number | null | undefined) => (v === null || v === undefined || !Number.isFinite(v) ? '' : String(Math.round(v * 100) / 100));
const pct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : plain(v));

const isBlank = (it: Item) => !it.lines.length && (['name', 'description', 'qty', 'unit', 'cost_each', 'price_each', 'profit_percent'] as const)
  .every((k) => !it[k].trim());
const filledLine = (l: Line) => l.description.trim() || l.unit_cost;
const filledShare = (s: Shared) => s.description.trim() || s.unit_cost || s.percent;

/** The rate a cost line's description names ("MS plate — Tata" or just "MS plate") */
function rateFor(rates: Rate[], value: string): Rate | null {
  const typed = value.trim().toLowerCase();
  if (!typed) return null;
  let hit: Rate | null = null;
  for (const r of rates) {
    const full = (r.description + (r.make ? ` — ${r.make}` : '')).toLowerCase();
    if (full === typed) return r;
    if (!hit && r.description.toLowerCase() === typed) hit = r;
  }
  return hit;
}

/** A picked rate fills the row's empty fields */
function withRate<T extends Partial<Line>>(row: T, hit: Rate, fields: (keyof Line)[]): Partial<T> {
  const patch: Partial<Line> = { description: hit.description };
  for (const k of fields) {
    const v = hit[k as keyof Rate];
    if (!row[k] && v !== null && v !== undefined && v !== '') patch[k] = typeof v === 'number' ? num(v) : String(v);
  }
  return patch as Partial<T>;
}

/** onChange for a description with the rates list: a pick from the list (not typing) fills from the rate */
const rateLabel = (r: Rate) => r.description + (r.make ? ` — ${r.make}` : '');

/** A cost line's (or shared cost's) description, offering the rates list as it's typed: picking a rate, or typing one
 *  exactly, fills in what it says (make, unit, cost, markup) */
function RateInput({ rates, base, value, label, placeholder, onType, onRate }: {
  rates: Rate[]; base: string; value: string; label: string; placeholder: string;
  onType: (description: string) => void; onRate: (rate: Rate) => void;
}) {
  const labels = useMemo(() => [...new Set(rates.map(rateLabel))], [rates]);
  const pick = (text: string) => {
    const hit = rateFor(rates, text);
    if (hit) onRate(hit);
  };
  return (
    <Autocomplete value={value} aria-label={label} placeholder={placeholder} data={labels} limit={8}
                  onChange={onType} onOptionSubmit={pick} onBlur={(e) => pick(e.currentTarget.value)}
                  renderOption={({ option }) => {
                    const r = rates.find((x) => rateLabel(x) === option.value);
                    const cost = r && r.unit_cost !== null ? `${money(r.unit_cost, base)}${r.unit ? ` / ${r.unit}` : ''}${r.markup ? ` + ${num(r.markup)}%` : ''}` : '';
                    return <div><Text size="sm">{option.value}</Text>{cost && <Text size="xs" c="dimmed">{cost}</Text>}</div>;
                  }} />
  );
}

function grow(el: HTMLTextAreaElement | null) {
  if (el && el.value) {
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
  }
}

function overLabel(picked: number[]): string {
  if (!picked.length) return 'All items';
  if (picked.length <= 3) return (picked.length === 1 ? 'Item ' : 'Items ') + picked.join(', ');
  return `${picked.length} items`;
}

export function CostingEditor({ data }: { data: CostingData }) {
  const first = useMemo(() => fromStored(data.sheet), [data.sheet]);
  const [items, setItems] = useState<Item[]>(() => (first.items.length ? first.items : [blankItem()]));
  const [shared, setShared] = useState<Shared[]>(first.shared);
  const [settings, setSettings] = useState<Settings>({
    mode: data.result.mode, profit_percent: num(data.result.profit_percent), target_total: num(data.settings.target_total),
    round_to: String(data.result.round_to), currency: data.settings.currency, exchange_rate: num(data.sheet.exchange_rate) });
  const [result, setResult] = useState<Result>(data.result);
  const [problem, setProblem] = useState('');
  const [open, setOpen] = useState<Set<string>>(() => new Set(first.items.filter((i) => i.lines.length).map((i) => i.key)));
  const [dialog, setDialog] = useState<'copy' | 'import' | 'purchase' | null>(null);
  const focus = useRef<string | null>(null);
  const base = data.base;
  const cur = settings.currency;
  const t = result.totals;

  useEffect(() => {
    document.title = `${data.tab} · DocuMint`;
  }, [data.tab]);
  useEffect(() => {
    if (!focus.current) return;
    (document.querySelector(focus.current) as HTMLElement | null)?.focus();
    focus.current = null;
  });

  const sheet = useMemo(() => ({ items, shared, exchange_rate: settings.exchange_rate }), [items, shared, settings.exchange_rate]);
  const [asSaved] = useState(() => JSON.stringify(sheet));          // the sheet as the page came, to tell a change since

  // Work the numbers out again a moment after each change; a newer change cancels the last request
  const changed = useRef(false);
  const { mode, profit_percent: profit, target_total: target, round_to: rounding } = settings;
  useEffect(() => {
    if (!changed.current) {                       // the first numbers came with the page
      changed.current = true;
      return undefined;
    }
    const abort = new AbortController();
    const timer = setTimeout(() => {
      const body = new FormData();
      body.set('sheet_json', JSON.stringify(sheet));
      Object.entries({ mode, profit_percent: profit, target_total: target, round_to: rounding, currency: cur }).forEach(([k, v]) => body.set(k, v));
      fetch(data.urls.preview, { method: 'POST', body, credentials: 'same-origin', signal: abort.signal })
        .then((r) => {
          if (!r.ok) throw new Error(String(r.status));
          return r.json() as Promise<Result>;
        })
        .then((r) => {
          setResult(r);
          setProblem('');
        })
        .catch((e: Error) => {
          if (e.name !== 'AbortError') setProblem("Couldn't work out the numbers; they're updated when you save.");
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      abort.abort();
    };
  }, [sheet, mode, profit, target, rounding, cur, data.urls.preview]);

  const byKey = useMemo(() => new Map(result.items.map((r) => [r.key, r])), [result]);
  const setItem = (key: string, patch: Partial<Item>) => setItems((all) => all.map((it) => (it.key === key ? { ...it, ...patch } : it)));
  const setLine = (key: string, j: number, patch: Partial<Line>) =>
    setItems((all) => all.map((it) => (it.key === key ? { ...it, lines: it.lines.map((l, i) => (i === j ? { ...l, ...patch } : l)) } : it)));
  const setShare = (j: number, patch: Partial<Shared>) => setShared((all) => all.map((s, i) => (i === j ? { ...s, ...patch } : s)));
  const set = (patch: Partial<Settings>) => setSettings((s) => ({ ...s, ...patch }));

  function addLine(key: string, line: Line = { ...BLANK_LINE }) {
    setItems((all) => all.map((it) => (it.key === key ? { ...it, lines: [...it.lines, line] } : it)));
    setOpen((s) => new Set(s).add(key));
    focus.current = `[data-item="${key}"] .k-line:last-child input`;
  }
  function addItem() {
    const it = blankItem();
    setItems((all) => [...all, it]);
    focus.current = `[data-item="${it.key}"] .k-name`;
  }
  function removeItem(key: string) {
    setItems((all) => all.filter((it) => it.key !== key));
    setShared((all) => all.map((s) => ({ ...s, items: s.items.filter((k) => k !== key) })));       // removed items drop out
  }
  /** Items from elsewhere (an earlier costing, a spreadsheet): the empty starter row makes way */
  function addItems(list: Item[]) {
    setItems((all) => [...(list.length ? all.filter((it) => !isBlank(it)) : all), ...list]);
    setOpen((s) => new Set([...s, ...list.filter((it) => it.lines.length).map((it) => it.key)]));
  }
  function addLinesTo(index: number, lines: Line[]) {
    const key = items[index]?.key;
    if (!key) return;
    setItems((all) => all.map((it) => (it.key === key ? { ...it, lines: [...it.lines, ...lines] } : it)));
    setOpen((s) => new Set(s).add(key));
  }
  function toggleLines(it: Item) {
    if (!it.lines.length) addLine(it.key);
    else setOpen((s) => {
      const next = new Set(s);
      if (next.has(it.key)) next.delete(it.key);
      else next.add(it.key);
      return next;
    });
  }

  const labels = items.map((it, i) => `${i + 1}. ${it.name.trim() || `Item ${i + 1}`}`);
  const filledShares = shared.map((s, i) => [s, i] as const).filter(([s]) => filledShare(s)).map(([, i]) => i);
  const c = data.costing;
  const foreign = cur !== base;

  return (
    <>
      <PageHeader title={data.title} heading
                  description={<><a href={c.project.url}>{c.project.label} · {c.project.title}</a> · {c.customer} ·{' '}
                    <span className="text-tertiary">Only owners and admins see costings</span></>} />
      <form method="post" action={data.urls.save} className="k-form" data-mode={settings.mode} data-foreign={String(foreign)}>
        <input type="hidden" name="sheet_json" value={JSON.stringify(sheet)} />
        <div className="k-top">
          <section className="card">
            <div className="card-body">
              <div className="form-group">
                <label htmlFor="title" className="form-label">Costing for</label>
                <input type="text" id="title" name="title" className="form-input" defaultValue={c.title} maxLength={200} required />
                <p className="form-text">Becomes the quote's subject.</p>
              </div>
              <div className="form-group">
                <span className="form-label">How are you pricing this?</span>
                <div className="segmented k-modes" role="radiogroup" aria-label="Pricing">
                  {data.options.modes.map(([key, label]) => (
                    <label key={key} className={settings.mode === key ? 'active' : undefined}>
                      <input type="radio" name="mode" value={key} className="sr-only" checked={settings.mode === key}
                             onChange={() => set({ mode: key })} />{label}
                    </label>
                  ))}
                </div>
              </div>
              <div className="k-settings">
                <div className="form-group k-target-only">
                  <label htmlFor="target_total" className="form-label">Known total</label>
                  <input type="number" step="any" id="target_total" name="target_total" className="form-input" value={settings.target_total}
                         onChange={(e) => set({ target_total: e.target.value })} placeholder="What the customer will pay" />
                </div>
                <div className="form-group">
                  <label htmlFor="profit_percent" className="form-label">Profit on cost, %</label>
                  <input type="number" step="any" id="profit_percent" name="profit_percent" className="form-input" value={settings.profit_percent}
                         onChange={(e) => set({ profit_percent: e.target.value })} />
                </div>
                <div className="form-group">
                  <label htmlFor="round_to" className="form-label">Round prices to</label>
                  <Dropdown id="round_to" name="round_to" value={String(settings.round_to)} onChange={(v) => set({ round_to: v })}
                            data={data.options.rounding.map((r) => ({ value: String(r), label: r ? `nearest ${r.toLocaleString('en-US')}` : 'No rounding' }))} />
                </div>
                <div className="form-group">
                  <label htmlFor="currency" className="form-label">Quote in</label>
                  <Dropdown id="currency" name="currency" value={cur} onChange={(v) => set({ currency: v })} data={choices(data.options.currencies)} />
                </div>
                <div className="form-group k-fx-only">
                  <label htmlFor="exchange_rate" className="form-label">{base} per {cur}</label>
                  <input type="number" step="any" min="0" id="exchange_rate" className="form-input" value={settings.exchange_rate}
                         onChange={(e) => set({ exchange_rate: e.target.value })} placeholder="e.g. 84" />
                </div>
              </div>
              <p className="form-text k-fx-only">Costs stay in {base}; prices, profit and the quote are in {cur} at this rate.</p>
              <p className="form-text k-build-only" style={{ marginBottom: 0 }}>Each item's price is its cost plus the profit (an item can have its own %). Type a price to set one yourself.</p>
              <p className="form-text k-target-only" style={{ marginBottom: 0 }}>The known total is shared over the items by their cost; the cost budget is what's left after your profit. Type a price to fix one item's share.</p>
            </div>
          </section>

          <section className="card k-summary">
            <div className="card-header"><h2 className="card-title">Summary</h2></div>
            <div className="card-body">
              <dl className="kv">
                <dt className="k-target-only">Known total</dt><dd className="k-target-only">{t.target !== undefined ? money(t.target, cur) : '—'}</dd>
                <dt className="k-target-only">Cost budget at {pct(result.profit_percent)}%</dt>
                <dd className="k-target-only">{t.budget !== undefined && t.budget !== null ? money(t.budget, cur) : '—'}</dd>
                <dt>Costs</dt><dd>{money(t.cost, cur)}</dd>
                <dt className="k-fx-only">Costs in {base}</dt><dd className="k-fx-only">{money(t.cost_base, base)}</dd>
                {t.shared ? <><dt className="k-shared-only">of which shared</dt><dd className="k-shared-only text-tertiary">{money(t.shared, base)}</dd></> : null}
                <dt className="k-target-only">Left in the budget</dt>
                <dd className={`k-target-only k-left${t.left !== undefined && t.left !== null && t.left < 0 ? ' k-over' : ''}`}>
                  {t.left !== undefined && t.left !== null ? money(t.left, cur) : '—'}</dd>
                <dt>Profit</dt><dd>{money(t.profit, cur)}</dd>
                <dt /><dd className="text-tertiary k-pcts">{pct(t.profit_on_cost)}% on cost · {pct(t.margin_of_price)}% of price</dd>
                <dt className="grand">Quote total</dt><dd className="grand">{money(t.price, cur)}</dd>
              </dl>
              {result.needs_rate && <p className="form-text k-needs-rate">Enter the exchange rate: until then the costs count as if they were in {cur}.</p>}
              {t.off_target ? <p className="form-text k-off">Rounding leaves the total {money(t.off_target, cur)} off the known total.</p> : null}
              <p className="form-text k-status" aria-live="polite">{problem}</p>
              <button type="submit" name="action" value="save" className="btn btn-primary btn-block"><Icon name="check" />Save costing</button>
            </div>
          </section>
        </div>

        <section className="card items-card">
          <div className="card-header">
            <h2 className="card-title">Items</h2>
            <span className="text-tertiary">Cost lines stay here; the quote gets the items and prices. Costs in {base}.</span>
            <a href={data.urls.rates} className="btn btn-ghost btn-sm k-rates-link"><Icon name="note" />Rates list</a>
          </div>
          <div className="items-wrap">
            <table className="items-editor k-items">
              <thead>
                <tr>
                  <th className="col-no">#</th><th className="long">Item</th><th className="c-qty num">Qty</th><th className="c-unit">Unit</th>
                  <th className="c-cost num">Cost / unit</th><th className="c-pct num col-profit-in">Profit %</th><th className="c-price num">Price / unit</th>
                  <th className="c-amount num">Amount</th><th className="c-gain num">Profit</th><th className="col-x"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              {items.map((it, i) => {
                const r = byKey.get(it.key);
                const lineCosts = r?.lines ?? [];
                let filled = -1;
                return (
                  <tbody key={it.key} className={`k-item${it.price_each.trim() ? ' manual' : ''}`} data-item={it.key}>
                    <tr className="k-item-row">
                      <td className="col-no" data-label="#"><span className="row-no">{i + 1}</span></td>
                      <td className="long" data-label="Item">
                        <input type="text" className="form-input k-name" value={it.name} placeholder="What the customer sees on the quote" aria-label="Item"
                               onChange={(e) => setItem(it.key, { name: e.target.value })} />
                        <textarea rows={1} className="form-textarea line-text k-desc" value={it.description} placeholder="Description (optional)" aria-label="Description"
                                  ref={grow} onChange={(e) => { setItem(it.key, { description: e.target.value }); grow(e.target); }} />
                      </td>
                      <td className="short num" data-label="Qty"><input type="number" step="any" className="form-input" value={it.qty} placeholder="1" aria-label="Quantity"
                                                                        onChange={(e) => setItem(it.key, { qty: e.target.value })} /></td>
                      <td className="short" data-label="Unit"><input type="text" className="form-input" value={it.unit} aria-label="Unit"
                                                                     onChange={(e) => setItem(it.key, { unit: e.target.value })} /></td>
                      <td className="short num" data-label="Cost / unit">
                        {it.lines.length ? <output className="k-cost-out" title="The total of the cost lines">{money(r?.own_cost_each, base)}</output>
                          : <input type="number" step="any" className="form-input k-cost-input" value={it.cost_each} aria-label="Cost per unit"
                                   onChange={(e) => setItem(it.key, { cost_each: e.target.value })} />}
                        {r?.shared_each ? <span className="k-sub k-shared-sub">+ {money(r.shared_each, base)} shared</span> : null}
                      </td>
                      <td className="short num col-profit-in" data-label="Profit %">
                        <input type="number" step="any" className="form-input" value={it.profit_percent} placeholder={plain(result.profit_percent)}
                               aria-label="Profit percent for this item" onChange={(e) => setItem(it.key, { profit_percent: e.target.value })} />
                      </td>
                      <td className="short num" data-label="Price / unit">
                        <input type="number" step="any" className="form-input k-price" value={it.price_each} placeholder={plain(r?.price)}
                               aria-label="Price per unit (leave empty to work it out)" title="Type a price to set it; clear it to work it out again"
                               onChange={(e) => setItem(it.key, { price_each: e.target.value })} />
                      </td>
                      <td className="calc num" data-label="Amount"><output>{r ? money(r.amount, result.currency) : '—'}</output></td>
                      <td className="calc num" data-label="Profit"><output>{r ? money(r.profit, result.currency) : '—'}</output>
                        <span className="k-sub">{r && r.profit_on_cost !== null ? `${r.profit_on_cost}%` : ''}</span></td>
                      <td className="col-x">
                        <button type="button" className="btn btn-ghost btn-xs k-toggle-lines" aria-expanded={open.has(it.key) && it.lines.length > 0}
                                title="Cost lines" aria-label={`Cost lines of item ${i + 1}`} onClick={() => toggleLines(it)}>
                          <Icon name="menu" /><span className="k-line-count">{it.lines.length || ''}</span>
                        </button>
                        <button type="button" className="btn btn-ghost btn-xs" aria-label={`Remove item ${i + 1}`} onClick={() => removeItem(it.key)}><Icon name="x" /></button>
                      </td>
                    </tr>
                    <tr className="k-lines-row" hidden={!(open.has(it.key) && it.lines.length)}>
                      <td className="k-lines-gap" />
                      <td colSpan={9} className="k-lines-cell">
                        <table className="items-editor k-lines">
                          <thead><tr><th className="long">Cost line</th><th className="c-make">Make / spec</th><th className="c-qty num">Qty</th><th className="c-unit">Unit</th>
                            <th className="c-ucost num">Unit cost</th><th className="c-markup num">Markup %</th><th className="c-lcost num">Cost</th><th className="col-x" /></tr></thead>
                          <tbody>
                            {it.lines.map((l, j) => {
                              if (filledLine(l)) filled += 1;
                              const cost = filledLine(l) ? lineCosts[filled]?.cost : undefined;
                              return (
                                <tr key={j} className="k-line">
                                  <td className="long" data-label="Cost line">
                                    <RateInput rates={data.rates} base={base} value={l.description} label="Cost line" placeholder="Material, machining, bought-out…"
                                               onType={(description) => setLine(it.key, j, { description })}
                                               onRate={(hit) => setLine(it.key, j, withRate(l, hit, ['make', 'unit', 'unit_cost', 'markup']))} />
                                  </td>
                                  <td className="short" data-label="Make / spec"><input type="text" className="form-input" value={l.make} aria-label="Make or specification"
                                                                                       onChange={(e) => setLine(it.key, j, { make: e.target.value })} /></td>
                                  <td className="short num" data-label="Qty"><input type="number" step="any" className="form-input" value={l.qty} placeholder="1" aria-label="Quantity"
                                                                                    onChange={(e) => setLine(it.key, j, { qty: e.target.value })} /></td>
                                  <td className="short" data-label="Unit"><input type="text" className="form-input" value={l.unit} aria-label="Unit"
                                                                                 onChange={(e) => setLine(it.key, j, { unit: e.target.value })} /></td>
                                  <td className="short num" data-label="Unit cost"><input type="number" step="any" className="form-input" value={l.unit_cost} aria-label="Unit cost"
                                                                                          onChange={(e) => setLine(it.key, j, { unit_cost: e.target.value })} /></td>
                                  <td className="short num" data-label="Markup %"><input type="number" step="any" className="form-input" value={l.markup} placeholder="0" aria-label="Markup percent"
                                                                                         onChange={(e) => setLine(it.key, j, { markup: e.target.value })} /></td>
                                  <td className="calc num" data-label="Cost"><output>{money(cost, base)}</output></td>
                                  <td className="col-x"><button type="button" className="btn btn-ghost btn-xs" aria-label="Remove cost line"
                                                                onClick={() => setItem(it.key, { lines: it.lines.filter((_, x) => x !== j) })}><Icon name="x" /></button></td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                        <button type="button" className="btn btn-ghost btn-sm" onClick={() => addLine(it.key)}><Icon name="plus" />Add cost line</button>
                      </td>
                    </tr>
                  </tbody>
                );
              })}
            </table>
          </div>
          <div className="items-foot k-foot">
            <div className="k-foot-actions">
              <button type="button" className="btn btn-ghost btn-sm" onClick={addItem}><Icon name="plus" />Add item</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDialog('copy')}><Icon name="file" />Copy from a costing</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDialog('import')}><Icon name="upload" />Import from Excel</button>
              {data.urls.purchase_order && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDialog('purchase')}><Icon name="filePlus" />Make a purchase order</button>
              )}
            </div>
            <span className="k-foot-totals">Costs <strong>{money(t.cost, cur)}</strong> · Profit <strong>{money(t.profit, cur)}</strong> · Quote total{' '}
              <strong>{money(t.price, cur)}</strong></span>
          </div>
        </section>

        <section className="card items-card k-shared-card">
          <div className="card-header">
            <h2 className="card-title">Shared costs</h2>
            <span className="text-tertiary">Design, freight, a reference station, an allowance for changes: spread over the items, so their prices carry them.</span>
          </div>
          <div className="items-wrap">
            <table className="items-editor k-shared" hidden={!shared.length}>
              <thead>
                <tr>
                  <th className="long">Shared cost</th><th className="c-how">How</th><th className="c-qty">Qty</th><th className="c-ucost">Cost</th><th className="c-markup">Markup %</th>
                  <th className="c-spread">Spread</th><th className="c-over">Over</th><th className="c-lcost num">Amount</th><th className="col-x"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {shared.map((s, j) => {
                  const k = filledShares.indexOf(j);
                  const picked = items.map((it, i) => (s.items.includes(it.key) ? i + 1 : 0)).filter(Boolean);
                  return (
                    <tr key={j} className="k-share" data-kind={s.kind}>
                      <td className="long" data-label="Shared cost">
                        <RateInput rates={data.rates} base={base} value={s.description} label="Shared cost" placeholder="Design, freight, reference station…"
                                   onType={(description) => setShare(j, { description })}
                                   onRate={(hit) => setShare(j, withRate(s, hit, ['unit_cost', 'markup']))} />
                      </td>
                      <td className="short" data-label="How">
                        <Dropdown value={s.kind} aria-label="An amount, or a % of the items' cost" onChange={(v) => setShare(j, { kind: v })}
                                  data={choices(data.options.shared_kinds)} />
                      </td>
                      <td className="short num" data-label="Qty"><input type="number" step="any" className="form-input k-amount-only" value={s.qty} placeholder="1" aria-label="Quantity"
                                                                        onChange={(e) => setShare(j, { qty: e.target.value })} /></td>
                      <td className="short num" data-label="Cost">
                        <input type="number" step="any" className="form-input k-amount-only" value={s.unit_cost} aria-label="Cost" onChange={(e) => setShare(j, { unit_cost: e.target.value })} />
                        <input type="number" step="any" className="form-input k-percent-only" value={s.percent} placeholder="%" aria-label="Percent of the items' cost"
                               onChange={(e) => setShare(j, { percent: e.target.value })} />
                      </td>
                      <td className="short num" data-label="Markup %"><input type="number" step="any" className="form-input k-amount-only" value={s.markup} placeholder="0" aria-label="Markup percent"
                                                                             onChange={(e) => setShare(j, { markup: e.target.value })} /></td>
                      <td className="short" data-label="Spread">
                        <Dropdown className="k-amount-only" value={s.spread} aria-label="How it's spread over the items" onChange={(v) => setShare(j, { spread: v })}
                                  data={choices(data.options.spreads)} />
                        <span className="k-percent-only k-fixed">by cost</span>
                      </td>
                      <td className="short" data-label="Over">
                        <details className="menu k-over">
                          <summary className="btn btn-secondary btn-sm"><span className="k-over-label">{overLabel(picked)}</span><Icon name="chevronDown" /></summary>
                          <div className="menu-items k-over-items">
                            {items.map((it, i) => (
                              <label key={it.key} className="menu-check">
                                <input type="checkbox" checked={s.items.includes(it.key)}
                                       onChange={(e) => setShare(j, { items: e.target.checked ? [...s.items, it.key] : s.items.filter((x) => x !== it.key) })} />
                                <span>{labels[i]}</span>
                              </label>
                            ))}
                          </div>
                        </details>
                      </td>
                      <td className="calc num" data-label="Amount"><output>{k >= 0 ? money(result.shared[k]?.amount, base) : '—'}</output></td>
                      <td className="col-x"><button type="button" className="btn btn-ghost btn-xs" aria-label="Remove shared cost"
                                                    onClick={() => setShared((all) => all.filter((_, x) => x !== j))}><Icon name="x" /></button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="items-foot k-foot">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => {
              setShared((all) => [...all, { ...BLANK_SHARED }]);
              focus.current = '.k-share:last-child input';
            }}><Icon name="plus" />Add shared cost</button>
            {t.shared ? <span className="k-foot-totals k-shared-only">Shared <strong>{money(t.shared, base)}</strong></span> : null}
          </div>
        </section>

        <div className="k-bottom">
          <section className="card">
            <div className="card-header"><h2 className="card-title">Quote</h2></div>
            <div className="card-body">
              {c.quote ? (
                <>
                  <p style={{ marginTop: 0 }}><a href={c.quote.url}>{c.quote.number}</a> · {c.quote.status}</p>
                  {c.quote.status === 'draft'
                    ? <button type="submit" name="action" value="update_quote" className="btn btn-secondary btn-block"><Icon name="refresh" />Update the quote's prices</button>
                    : <p className="form-text">The quote has gone out, so it stays as it is. To requote, start a new version.</p>}
                  <details className="fold"><summary>Make another quote</summary><MakeQuote data={data} primary={false} /></details>
                </>
              ) : <MakeQuote data={data} primary />}
            </div>
          </section>

          <section className="card">
            <div className="card-header"><h2 className="card-title">Versions</h2></div>
            {data.versions.length > 0 && (
              <ul className="pick-list">
                {data.versions.map((v) => (
                  <li key={v.url}><a href={v.url}>
                    <span className="pick-main"><span className="pick-title">Version {v.version}</span>
                      <span className="pick-sub">{money(v.total, v.currency)}{v.profit_on_cost !== null ? ` · ${v.profit_on_cost}% profit` : ''}{v.quote_number ? ` · ${v.quote_number}` : ''}</span></span>
                    <Icon name="chevronRight" /></a></li>
                ))}
              </ul>
            )}
            <div className="card-body">
              <button type="submit" form="k-new-version" className="btn btn-secondary btn-block"><Icon name="plus" />Start a new version from this</button>
              <p className="form-text">Save first: the new version copies what's saved.</p>
              <button type="submit" form="k-delete" className="btn btn-ghost btn-block"><Icon name="trash" />Delete this version</button>
            </div>
          </section>

          <section className="card">
            <div className="card-header"><h2 className="card-title">Notes for yourselves</h2></div>
            <div className="card-body">
              <label htmlFor="notes" className="sr-only">Notes</label>
              <textarea id="notes" name="notes" rows={4} className="form-textarea" defaultValue={c.notes} placeholder="Rates used, supplier quotes, assumptions…" />
            </div>
          </section>
        </div>
      </form>
      <form id="k-new-version" method="post" action={data.urls.new_version}>
        <input type="hidden" name="project_id" value={data.urls.project_id} /><input type="hidden" name="copy_of" value={c.id} />
      </form>
      <form id="k-delete" method="post" action={data.urls.delete} onSubmit={ask(`Delete costing version ${c.version}? This can't be undone.`)} />

      <CopyDialog open={dialog === 'copy'} onClose={() => setDialog(null)} library={data.urls.library} itemsUrl={data.urls.items} self={c.id}
                  onAdd={addItems} />
      <ImportDialog open={dialog === 'import'} onClose={() => setDialog(null)} url={data.urls.import} base={base} items={labels}
                    onAddItems={addItems} onAddLines={addLinesTo} />
      {data.urls.purchase_order && (
        <PurchaseDialog open={dialog === 'purchase'} onClose={() => setDialog(null)} url={data.urls.purchase_order}
                        items={data.sheet.items} unsaved={JSON.stringify(sheet) !== asSaved} />
      )}
    </>
  );
}

function MakeQuote({ data, primary }: { data: CostingData; primary: boolean }) {
  return (
    <>
      <div className="form-group">
        <label htmlFor="template_id" className="form-label">Template</label>
        <Dropdown id="template_id" name="template_id" defaultValue={data.templates[0]?.id}
                  data={data.templates.map((tpl) => ({ value: tpl.id, label: tpl.name }))} />
      </div>
      <button type="submit" name="action" value="quote" className={`btn btn-${primary ? 'primary' : 'secondary'} btn-block`}><Icon name="file" />Save and make the quote</button>
      <p className="form-text" style={{ marginBottom: 0 }}>A draft quotation with these items and prices; the costs stay here.</p>
    </>
  );
}

export default function CostingPage({ costingId }: { costingId: string }) {
  const { data, error } = useLoad<CostingData>(`/api/costings/${costingId}`, "Couldn't load the costing. Check your connection.");
  return data ? <CostingEditor data={data} /> : <Loading title="Costing" kind="page" error={error} heading />;
}
