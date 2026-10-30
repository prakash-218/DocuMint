import { useState } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { Icon } from '../../icons';
import { money, num } from './sheet';
import type { Rate } from './types';

// The usual rates (material per kg, machining, bought-outs with their markup), in the business's currency. A costing's
// cost lines offer them as they're typed. It posts rates_json (every row as typed) to costings_bp.rates, which keeps
// one per description and make; under it, cost lines from the costings that aren't in the list yet, to add.

interface Data {
  title: string;
  base: string;
  action: string;
  back: { url: string; version: number } | null;
  rates: Rate[];
  suggestions: (Rate & { used: number })[];
}

type Row = Record<'description' | 'make' | 'unit' | 'unit_cost' | 'markup' | 'notes', string> & { id: number };

let next = 0;
const row = (r: Partial<Rate> = {}): Row => ({
  id: ++next, description: r.description ?? '', make: r.make ?? '', unit: r.unit ?? '', unit_cost: num(r.unit_cost),
  markup: num(r.markup), notes: r.notes ?? '',
});

const COLS: { key: keyof Omit<Row, 'id'>; label: string; cls: string; type?: string; max?: number; hint?: string }[] = [
  { key: 'description', label: 'Description', cls: 'long', max: 300, hint: 'MS raw material, fabrication, LM guide…' },
  { key: 'make', label: 'Make or specification', cls: 'short', max: 120 },
  { key: 'unit', label: 'Unit', cls: 'short', max: 20, hint: 'kg' },
  { key: 'unit_cost', label: 'Unit cost', cls: 'short num', type: 'number' },
  { key: 'markup', label: 'Markup percent', cls: 'short num', type: 'number', hint: '0' },
  { key: 'notes', label: 'Notes', cls: 'short', max: 300, hint: 'Supplier, date…' },
];

export function RatesList({ data }: { data: Data }) {
  const [rows, setRows] = useState<Row[]>(() => (data.rates.length ? data.rates.map(row) : [row()]));
  const [offered, setOffered] = useState(data.suggestions);
  const change = (id: number, key: keyof Row, value: string) => setRows((all) => all.map((r) => (r.id === id ? { ...r, [key]: value } : r)));
  const posted = JSON.stringify(rows.map(({ id: _id, ...r }) => r));
  return (
    <>
      <PageHeader title={data.title} heading
                  description={<>Your usual costs, in {data.base}. A costing's cost lines offer them as you type.{' '}
                    <span className="text-tertiary">Only owners and admins see this.</span></>}
                  actions={data.back && <a href={data.back.url} className="btn btn-secondary"><Icon name="arrowLeft" />
                    <span className="btn-label">Back to costing v{data.back.version}</span></a>} />
      <form method="post" action={data.action} className="mb-lg">
        <input type="hidden" name="rates_json" value={posted} />
        <section className="card items-card">
          <div className="card-header"><h2 className="card-title">Rates</h2><span className="text-tertiary">{data.rates.length} saved</span></div>
          <div className="items-wrap">
            <table className="items-editor k-rates-table">
              <thead>
                <tr><th className="long">Description</th><th className="c-make">Make / spec</th><th className="c-unit">Unit</th><th className="c-ucost num">Unit cost</th>
                  <th className="c-markup num">Markup %</th><th className="c-notes">Notes</th><th className="col-x"><span className="sr-only">Actions</span></th></tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="k-rate">
                    {COLS.map((c) => (
                      <td key={c.key} className={c.cls}>
                        <input type={c.type ?? 'text'} step={c.type ? 'any' : undefined} maxLength={c.max} className="form-input" value={r[c.key]}
                               placeholder={c.hint} aria-label={c.label} onChange={(e) => change(r.id, c.key, e.target.value)} />
                      </td>
                    ))}
                    <td className="col-x"><button type="button" className="btn btn-ghost btn-xs" aria-label="Remove rate"
                                                  onClick={() => setRows((all) => all.filter((x) => x.id !== r.id))}><Icon name="x" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="items-foot k-foot">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setRows((all) => [...all, row()])}><Icon name="plus" />Add rate</button>
            <button type="submit" className="btn btn-primary"><Icon name="check" />Save rates</button>
          </div>
        </section>
      </form>

      {offered.length > 0 && (
        <section className="card items-card">
          <div className="card-header"><h2 className="card-title">From your costings</h2>
            <span className="text-tertiary">Cost lines you've used that aren't in the list yet, with the rate they had last. Add the ones you use often, then save.</span></div>
          <div className="items-wrap">
            <table className="items-editor k-rates-table k-suggest">
              <thead>
                <tr><th className="long">Description</th><th className="c-make">Make / spec</th><th className="c-unit">Unit</th><th className="c-ucost num">Unit cost</th>
                  <th className="c-markup num">Markup %</th><th className="c-notes k-used">Used</th><th className="col-x"><span className="sr-only">Add</span></th></tr>
              </thead>
              <tbody>
                {offered.map((s, i) => (
                  <tr key={`${s.description}|${s.make}`}>
                    <td className="long" data-label="Description">{s.description}</td>
                    <td className="short" data-label="Make / spec">{s.make}</td>
                    <td className="short" data-label="Unit">{s.unit}</td>
                    <td className="short num" data-label="Unit cost">{money(s.unit_cost, data.base)}</td>
                    <td className="short num" data-label="Markup %">{num(s.markup)}</td>
                    <td className="short k-used" data-label="Used">{s.used} {s.used === 1 ? 'time' : 'times'}</td>
                    <td className="col-x">
                      <button type="button" className="btn btn-ghost btn-xs" aria-label={`Add ${s.description} to the rates`}
                              onClick={() => {
                                setRows((all) => [...all, row(s)]);
                                setOffered((all) => all.filter((_, j) => j !== i));
                              }}><Icon name="plus" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}

export default function RatesPage({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/costings/rates${search}`, "Couldn't load the rates. Check your connection.");
  return data ? <RatesList data={data} /> : <Loading title="Rates list" kind="page" error={error} heading />;
}
