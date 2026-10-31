import { act, render, screen, waitFor, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CostingEditor } from './CostingEditor';
import { importRows } from './Dialogs';
import type { CostingData, Result } from './types';

const RESULT: Result = {
  mode: 'build', profit_percent: 15, round_to: 0, currency: 'INR', needs_rate: false,
  items: [{ key: 'unit1', own_cost_each: 1000, shared_each: 250, price: 1437.5, amount: 1437.5, profit: 187.5, profit_on_cost: 15, manual_price: false, lines: [] },
          { key: 'tank1', own_cost_each: 400, shared_each: 0, price: 460, amount: 920, profit: 120, profit_on_cost: 15, manual_price: false,
            lines: [{ cost: 300 }, { cost: 100 }] }],
  shared: [{ amount: 250 }],
  totals: { cost: 2050, cost_base: 2050, shared: 250, price: 2357.5, profit: 307.5, profit_on_cost: 15, margin_of_price: 13 },
};

const DATA: CostingData = {
  title: 'Costing v2', tab: 'Costing v2 · Spline gauges',
  costing: { id: 'K-2', version: 2, title: 'Spline gauges', notes: '', customer: 'Gear Cutters Ltd',
             project: { label: 'PRJ-007', title: 'Spline gauges', url: '/projects/P-7' }, quote: null },
  sheet: {
    items: [{ key: 'unit1', name: 'Gauge', description: '', qty: 1, unit: 'no', cost_each: 1000, profit_percent: null, price_each: null, lines: [] },
            { key: 'tank1', name: 'Master', description: '', qty: 2, unit: '', cost_each: null, profit_percent: null, price_each: null,
              lines: [{ description: 'MS plate', make: 'Tata', qty: 3, unit: 'kg', unit_cost: 100, markup: null },
                      { description: 'Grinding', make: '', qty: null, unit: '', unit_cost: 100, markup: null }] }],
    shared: [{ description: 'Design', kind: 'amount', qty: null, unit_cost: 250, markup: null, percent: null, spread: 'equal', items: ['unit1'] }],
    exchange_rate: null,
  },
  settings: { mode: 'build', profit_percent: 15, target_total: null, round_to: 0, currency: 'INR' },
  result: RESULT, base: 'INR',
  options: { modes: [['build', 'Build up from costs'], ['target', 'Work back from a total']], rounding: [0, 10, 100], currencies: ['INR', 'USD'],
             spreads: [['equal', 'equally'], ['cost', 'by cost']], shared_kinds: [['amount', 'Amount'], ['percent', '% of cost']] },
  templates: [{ id: 'T-1', name: 'Quotation' }], versions: [],
  rates: [{ description: 'LM guide with block', make: 'Hiwin', unit: 'set', unit_cost: 34000, markup: 10 }],
  urls: { save: '/costings/K-2', preview: '/costings/K-2/preview', library: '/costings/library', items: '/costings/COSTING/items',
          import: '/costings/K-2/import', rates: '/costings/rates?back=K-2', new_version: '/costings/new', delete: '/costings/K-2/delete', project_id: 'P-7' },
};

const form = () => document.querySelector('form.k-form') as HTMLFormElement;
const sheet = () => JSON.parse(new FormData(form()).get('sheet_json') as string);

afterEach(() => vi.restoreAllMocks());

describe('the costing editor', () => {
  it('posts the sheet as typed, with the settings, and shows the worked-out numbers', () => {
    render(<CostingEditor data={DATA} />);
    expect(sheet().items.map((i: { key: string; qty: string; cost_each: string }) => [i.key, i.qty, i.cost_each]))
      .toEqual([['unit1', '1', '1000'], ['tank1', '2', '']]);                 // with cost lines, no typed cost
    expect(sheet().items[1].lines[0]).toEqual({ description: 'MS plate', make: 'Tata', qty: '3', unit: 'kg', unit_cost: '100', markup: '' });
    expect(sheet().shared[0].items).toEqual(['unit1']);
    expect(Object.fromEntries(new FormData(form()))).toMatchObject({ title: 'Spline gauges', mode: 'build', profit_percent: '15', round_to: '0', currency: 'INR' });
    expect(screen.getByText('+ ₹250.00 shared')).toBeInTheDocument();
    expect(screen.getAllByText('₹2,357.50').length).toBeGreaterThan(0);           // the quote total
    expect(document.querySelector('.k-over-label')).toHaveTextContent(/^Item 1$/);   // the shared cost is over item 1
  });

  it('works the numbers out again after a change, from the server', async () => {
    const after = { ...RESULT, totals: { ...RESULT.totals, price: 3795 } };
    const fetched = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(after), { status: 200 }));
    render(<CostingEditor data={DATA} />);
    expect(fetched).not.toHaveBeenCalled();                                     // the first numbers came with the page
    await userEvent.clear(screen.getAllByLabelText('Quantity')[0]);
    await userEvent.type(screen.getAllByLabelText('Quantity')[0], '2');
    const sent = () => {
      const [, init] = fetched.mock.calls.at(-1) ?? [];
      return init ? JSON.parse((init.body as FormData).get('sheet_json') as string).items[0].qty : null;
    };
    await waitFor(() => expect(sent()).toBe('2'));
    expect(fetched.mock.calls.at(-1)![0]).toBe('/costings/K-2/preview');
    await waitFor(() => expect(screen.getAllByText('₹3,795.00').length).toBeGreaterThan(0));
  });

  it('adds and removes items; a removed item drops out of the shared costs', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(RESULT), { status: 200 }));
    render(<CostingEditor data={DATA} />);
    await userEvent.click(screen.getByRole('button', { name: 'Add item' }));
    expect(sheet().items).toHaveLength(3);
    expect(document.activeElement).toHaveClass('k-name');
    await userEvent.click(screen.getByRole('button', { name: 'Remove item 1' }));
    expect(sheet().items.map((i: { key: string }) => i.key)).not.toContain('unit1');
    expect(sheet().shared[0].items).toEqual([]);
    expect(document.querySelector('.k-over-label')).toHaveTextContent(/^All items$/);
  });

  it('fills a cost line from the rates list', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(RESULT), { status: 200 }));
    render(<CostingEditor data={DATA} />);
    const lines = within(document.querySelector('[data-item="tank1"]') as HTMLElement);
    await userEvent.click(lines.getByRole('button', { name: 'Add cost line' }));
    const line = lines.getAllByLabelText('Cost line', { selector: 'input' }).at(-1)!;
    await userEvent.type(line, 'LM guide with block — Hiwin');
    act(() => line.blur());
    expect(sheet().items[1].lines[2]).toEqual({ description: 'LM guide with block', make: 'Hiwin', qty: '', unit: 'set', unit_cost: '34000', markup: '10' });
  });
});

describe('a purchase order of its lines', () => {
  it('opens the purchase order with the ticked lines', async () => {
    const url = '/purchase-orders/new?project_id=P-7&from_costing=K-2';
    render(<CostingEditor data={{ ...DATA, urls: { ...DATA.urls, purchase_order: url } }} />);
    await userEvent.click(screen.getByRole('button', { name: 'Make a purchase order' }));
    const dialog = document.getElementById('k-purchase') as HTMLElement;
    const open = within(dialog).getByText(/^Open the purchase order/).closest('a')!;
    expect(open).not.toHaveAttribute('href');                                   // nothing ticked yet
    await userEvent.click(within(dialog).getByRole('checkbox', { name: /MS plate/ }));
    expect(open).toHaveAttribute('href', `${url}&lines=${encodeURIComponent('tank1:0')}`);
    expect(open).toHaveTextContent('(1 line)');
    expect(dialog).not.toHaveTextContent('Save the costing first');              // nothing changed since it was saved
  });

  it('says unsaved changes are not included once something has changed', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(RESULT), { status: 200 }));
    render(<CostingEditor data={{ ...DATA, urls: { ...DATA.urls, purchase_order: '/purchase-orders/new' } }} />);
    await userEvent.type(screen.getAllByDisplayValue('MS plate')[0], ' 6mm');
    await userEvent.click(screen.getByRole('button', { name: 'Make a purchase order' }));
    expect(document.getElementById('k-purchase')).toHaveTextContent("Unsaved changes aren't included. Save the costing first.");
  });

  it('is not offered to those who may not make one', () => {
    render(<CostingEditor data={DATA} />);
    expect(screen.queryByRole('button', { name: 'Make a purchase order' })).toBeNull();
  });
});

describe('importing from a spreadsheet', () => {
  const sheet = {
    name: 'Costing', header_row: 2, columns: {},
    rows: [['Breakup'], [], ['S.No', 'Description', 'Specifications', 'Price', 'Qty', 'Total in Rs'],
           [1, 'Frame', 'MS', '1,200', 2, 2400], [2, '', 'Bolts M8', null, 10, 50], [3, 'Sub total', '', null, null, 2450],
           [4, 'Paint', '', null, null, null], []],
  };
  it('takes the rows with an item and an amount, and leaves out totals', () => {
    const got = importRows(sheet, 2, { name: 1, spec: 2, qty: 4, unit: -1, price: 3, amount: 5 });
    expect(got.rows).toEqual([{ name: 'Frame', spec: 'MS', qty: 2, unit: '', price: 1200 },
                              { name: 'Bolts M8', spec: '', qty: 10, unit: '', price: 5 }]);   // no price: the amount over the qty
    expect(got.skipped).toBe(2);                                                              // the sub total, and Paint with no amount
  });
});
