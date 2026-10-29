// The costing sheet as typed: numbers shown the way the inputs show them, blank rows, new item keys.
import type { Item, Line, Shared, StoredSheet } from './types';

/** A stored number as the inputs show it: up to 4 decimals, no trailing zeros */
export function num(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === '') return '';
  const n = Number(v);
  return Number.isFinite(n) ? String(+n.toFixed(4)) : String(v);
}

/** Money with paise, as costings show it: ₹1,23,450.50 */
export function money(v: number | null | undefined, cur: string): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—';
  try {
    return new Intl.NumberFormat(cur === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: cur }).format(v);
  } catch {
    return Number(v).toFixed(2);
  }
}


export function newKey(): string {
  const bytes = new Uint8Array(4);
  crypto.getRandomValues(bytes);
  return 'i' + Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export const BLANK_LINE: Line = { description: '', make: '', qty: '', unit: '', unit_cost: '', markup: '' };
export const BLANK_SHARED: Shared = { description: '', kind: 'amount', qty: '', unit_cost: '', markup: '', percent: '', spread: 'equal', items: [] };
export const blankItem = (): Item => ({ key: newKey(), name: '', description: '', qty: '', unit: '', cost_each: '', profit_percent: '',
                                        price_each: '', lines: [] });
const text = (v: unknown) => (v === null || v === undefined ? '' : String(v));

export function fromStored(sheet: StoredSheet): { items: Item[]; shared: Shared[] } {
  return {
    items: sheet.items.map((it) => ({
      key: it.key, name: it.name || '', description: it.description || '', qty: num(it.qty), unit: it.unit || '',
      cost_each: it.lines.length ? '' : num(it.cost_each), profit_percent: num(it.profit_percent), price_each: num(it.price_each),
      lines: it.lines.map((l) => ({ description: text(l.description), make: text(l.make), qty: num(l.qty), unit: text(l.unit),
                                    unit_cost: num(l.unit_cost), markup: num(l.markup) })),
    })),
    shared: sheet.shared.map((s) => ({ description: text(s.description), kind: text(s.kind) || 'amount', qty: num(s.qty),
                                       unit_cost: num(s.unit_cost), markup: num(s.markup), percent: num(s.percent),
                                       spread: text(s.spread) || 'equal', items: s.items || [] })),
  };
}
