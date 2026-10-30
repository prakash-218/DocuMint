// The editor's live amounts, as static/js/editor.js worked them out: a line's calculated cells from its own fields
// (this.qty * this.rate), less the line's discount, the totals from the lines and the other fields (SUM(items.amount),
// other fields' names), less the document's discount, then GST. Only that arithmetic: anything else shows "—" and is
// worked out by the server on save, by the same rules (calculations.py, discounts.py).
import type { Section, Value } from './types';

export function evaluate(expr: string): number {
  if (!/^[\d.\s+\-*/()eE]+$/.test(expr)) return NaN;
  try {
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    return Function(`"use strict"; return (${expr});`)() as number;
  } catch {
    return NaN;
  }
}

const num = (v: Value | undefined) => {
  const n = typeof v === 'string' ? parseFloat(v) : NaN;
  return Number.isNaN(n) ? 0 : n;
};

/** A discount as typed: an amount ("5000", "₹5,000") or a percent ("10%"). null for none, 'invalid' for anything else. */
export type Discount = { kind: 'percent' | 'amount'; value: number } | null;

export function parseDiscount(typed: string | undefined): Discount | 'invalid' {
  const raw = (typed ?? '').trim();
  if (!raw) return null;
  const m = /^(?:rs\.?|inr|usd|eur|gbp|aud|cad|sgd|aed|[₹$€£])?\s*(\d[\d,]*(?:\.\d+)?|\.\d+)\s*(%?)$/i.exec(raw);
  if (!m) return 'invalid';
  const value = parseFloat(m[1].replace(/,/g, ''));
  if (m[2] === '%' && value > 100) return 'invalid';
  return value ? { kind: m[2] === '%' ? 'percent' : 'amount', value } : null;
}

/** What a discount takes off base: never more than base, never below nothing (discounts.off). */
export function takeOff(base: number, d: Discount | 'invalid'): number {
  if (!d || d === 'invalid' || !(base > 0)) return 0;
  const taken = d.kind === 'percent' ? (base * d.value) / 100 : d.value;
  return Math.round(Math.min(Math.max(taken, 0), base) * 100) / 100;
}

/** One line's calculated cells (field id -> value), each formula seeing the cells worked out before it; the line's
 *  discount comes off its amount (section.amount_field). */
export function lineCells(section: Section, values: Record<string, Value>, discount?: string): Record<string, number> {
  const named: Record<string, number> = {};
  for (const f of section.fields) if (!f.formula) named[f.name] = num(values[f.id]);
  const out: Record<string, number> = {};
  for (const f of section.fields) {
    if (!f.formula) continue;
    const expr = f.formula.replace(/this\.(\w+)/g, (_, k: string) => (k in named ? `(${named[k]})` : 'NaN'));
    let v = evaluate(expr);
    if (discount && f.id === section.amount_field && Number.isFinite(v)) v = Math.round((v - takeOff(v, parseDiscount(discount))) * 100) / 100;
    out[f.id] = v;
    named[f.name] = Number.isFinite(v) ? v : 0;
  }
  return out;
}

export interface Totals {
  fields: { id: string; label: string; value: number }[];    // the template's calculated totals, in order
  total: number;                                            // the last of them: the subtotal
  discount: number;                                         // the document's discount off it
  discountLabel: string;                                    // 'Discount (10%)'
  taxable: number;                                          // total less the discount
  tax: number;
  taxed: boolean;
  taxLabel: string;
  grand: number;
}

export function totals(sections: Section[], rows: Record<string, { row: number; values: Record<string, Value>; discount?: string }[]>,
                       normals: Record<string, Value>, taxMode: string, taxRate: string, documentDiscount = ''): Totals {
  const sums: Record<string, number> = {};
  for (const s of sections) {
    if (s.type !== 'line_item') continue;
    for (const r of rows[s.id] ?? []) {
      const cells = lineCells(s, r.values, r.discount);
      for (const f of s.fields) {
        const v = f.formula ? (Number.isFinite(cells[f.id]) ? cells[f.id] : 0) : num(r.values[f.id]);
        sums[`${s.name}.${f.name}`] = (sums[`${s.name}.${f.name}`] ?? 0) + v;
      }
    }
  }
  const named: Record<string, number> = {};
  for (const s of sections) {
    if (s.type === 'line_item') continue;
    for (const f of s.fields) if (!f.formula) named[f.name] = num(normals[f.id]);
  }
  const fields: Totals['fields'] = [];
  let total = NaN;
  for (const s of sections) {
    if (s.type === 'line_item') continue;
    for (const f of s.fields) {
      if (!f.formula) continue;
      const expr = f.formula
        .replace(/SUM\(\s*(\w+)\.(\w+)\s*\)/gi, (_, sec: string, fld: string) => `(${sums[`${sec.toLowerCase()}.${fld}`] ?? 0})`)
        .replace(/\b([A-Za-z_]\w*)\b/g, (m: string, k: string) => (k in named ? `(${named[k]})` : m));
      const v = evaluate(expr);
      if (Number.isFinite(v)) named[f.name] = v;
      fields.push({ id: f.id, label: f.label, value: v });
      total = v;
    }
  }
  const rate = parseFloat(taxRate) || 0;
  const taxed = taxMode === 'cgst_sgst' || taxMode === 'igst';
  const d = parseDiscount(documentDiscount);
  const discount = Number.isFinite(total) ? takeOff(total, d) : 0;
  const taxable = Number.isFinite(total) ? Math.round((total - discount) * 100) / 100 : NaN;
  const tax = taxed && Number.isFinite(taxable) ? (taxable * rate) / 100 : 0;
  return { fields, total, discount, taxable, tax, taxed, taxLabel: `${taxMode === 'igst' ? 'IGST' : 'GST'} ${rate}%`,
           discountLabel: d && d !== 'invalid' && d.kind === 'percent' ? `Discount (${d.value}%)` : 'Discount',
           grand: Number.isFinite(taxable) ? taxable + tax : NaN };
}

/** Money as the editor showed it: two decimals, lakh grouping in rupees; "—" when it can't be worked out. */
export function amount(v: number, currency: string): string {
  if (!Number.isFinite(v)) return '—';
  const code = currency || 'INR';
  try {
    return new Intl.NumberFormat(code === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: code }).format(v);
  } catch {
    return v.toFixed(2);
  }
}
