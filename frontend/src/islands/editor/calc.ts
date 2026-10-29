// The editor's live amounts, as static/js/editor.js worked them out: a line's calculated cells from its own fields
// (this.qty * this.rate), the totals from the lines and the other fields (SUM(items.amount), other fields' names),
// then GST. Only that arithmetic: anything else shows "—" and is worked out by the server on save.
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

/** One line's calculated cells (field id -> value), each formula seeing the cells worked out before it. */
export function lineCells(section: Section, values: Record<string, Value>): Record<string, number> {
  const named: Record<string, number> = {};
  for (const f of section.fields) if (!f.formula) named[f.name] = num(values[f.id]);
  const out: Record<string, number> = {};
  for (const f of section.fields) {
    if (!f.formula) continue;
    const expr = f.formula.replace(/this\.(\w+)/g, (_, k: string) => (k in named ? `(${named[k]})` : 'NaN'));
    const v = evaluate(expr);
    out[f.id] = v;
    named[f.name] = Number.isFinite(v) ? v : 0;
  }
  return out;
}

export interface Totals {
  fields: { id: string; label: string; value: number }[];    // the template's calculated totals, in order
  total: number;                                            // the last of them (before tax)
  tax: number;
  taxed: boolean;
  taxLabel: string;
  grand: number;
}

export function totals(sections: Section[], rows: Record<string, { row: number; values: Record<string, Value> }[]>,
                       normals: Record<string, Value>, taxMode: string, taxRate: string): Totals {
  const sums: Record<string, number> = {};
  for (const s of sections) {
    if (s.type !== 'line_item') continue;
    for (const r of rows[s.id] ?? []) {
      const cells = lineCells(s, r.values);
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
  const tax = taxed && Number.isFinite(total) ? (total * rate) / 100 : 0;
  return { fields, total, tax, taxed, taxLabel: `${taxMode === 'igst' ? 'IGST' : 'GST'} ${rate}%`,
           grand: Number.isFinite(total) ? total + tax : NaN };
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
