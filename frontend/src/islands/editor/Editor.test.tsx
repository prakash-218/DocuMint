import { optionsOf, pick, render, screen, waitFor } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluate, lineCells, parseDiscount, takeOff, totals } from './calc';
import { HeaderSlots } from '../../app/PageHeader';
import { Editor } from './Editor';
import type { EditorData, Section } from './types';

const ITEMS: Section = {
  id: 'S-1', type: 'line_item', title: 'Items', name: 'items', amount_field: 'F-a', fields: [
    { id: 'F-d', name: 'description', label: 'Description', data_type: 'string', formula: null, money: false, required: true, long: true },
    { id: 'F-q', name: 'qty', label: 'Qty', data_type: 'number', formula: null, money: false, required: false, long: false },
    { id: 'F-r', name: 'rate', label: 'Rate', data_type: 'number', formula: null, money: true, required: false, long: false },
    { id: 'F-a', name: 'amount', label: 'Amount', data_type: 'number', formula: 'this.qty * this.rate', money: true, required: false, long: false },
  ],
  rows: [{ row: 3, values: { 'F-d': 'Spline gauge', 'F-q': '2', 'F-r': '1000' } }],
};
const TOTALS: Section = {
  id: 'S-2', type: 'normal', title: 'Totals', name: 'totals', fields: [
    { id: 'F-f', name: 'freight', label: 'Freight', data_type: 'number', formula: null, money: true, required: false, long: false },
    { id: 'F-t', name: 'total', label: 'Total', data_type: 'number', formula: 'SUM(items.amount) + freight', money: true, required: false, long: false },
  ],
  values: { 'F-f': '500' },
};

const DATA: EditorData = {
  step: 'editor', title: 'New quotation', correcting: false, editing: false,
  type: { key: 'quote', label: 'Quotation', sent_word: 'sent', takes_payments: false, proforma: false, due_label: 'Valid until' },
  project: { id: 'P-1', label: 'PRJ-001', title: 'Spline gauges', url: '/projects/P-1', customer_id: 'C-1', customer_name: 'Gear Cutters Ltd' },
  template_name: 'Quotation', change_template: '/quotes/create?doc_type=quote&project_id=P-1',
  action: '/quotes/create?doc_type=quote', preview: '/api/editor/new/quotes/preview', cancel: '/projects/P-1', submit: 'Create', submit_side: 'Create quotation',
  hidden: { doc_type: 'quote', suggested_number: 'TF/Q/031', template_id: 'T-1', project_id: 'P-1' },
  customer: { fixed: null, groups: [{ label: 'Gear Cutters Ltd', options: [{ id: 'C-1', label: 'Gear Cutters Ltd' }, { id: 'C-2', label: 'Hosur plant' }] },
                                    { label: null, options: [{ id: 'C-9', label: 'Axle Works' }] }] },
  number: { value: 'TF/Q/031', required: false }, issue_date: '2026-10-29', due_date: '',
  sections: [ITEMS, TOTALS], discount: '',
  details: { fields: [{ key: 'subject', label: 'Subject', kind: 'text', placeholder: '', group: '' },
                      { key: 'incoterms', label: 'Incoterms', kind: 'text', placeholder: 'FOB Chennai', group: 'export' }],
             values: { subject: 'Spline gauges' }, groups: [{ key: 'export', label: 'Export terms', fields: ['incoterms'], open: false }] },
  settings: { currencies: ['INR', 'USD'], currency: 'INR', tax_modes: [['none', 'No tax'], ['cgst_sgst', 'CGST + SGST (same state)'], ['igst', 'IGST (other state)']],
              tax_mode: 'none', tax_rate: '18', advance_percent: '', advance_basis: 'pre_tax' },
  tax_hints: { 'C-1': { mode: 'cgst_sgst', note: 'Tamil Nadu GSTIN, so CGST + SGST' },
               'C-9': { mode: 'igst', note: 'Karnataka GSTIN, another state, so IGST' } },
};

const form = () => document.getElementById('docForm') as HTMLFormElement;
const posted = () => Object.fromEntries(new FormData(form()).entries());

describe('the live amounts', () => {
  it('works out only arithmetic', () => {
    expect(evaluate('(2) * (1000)')).toBe(2000);
    expect(evaluate('alert(1)')).toBeNaN();
  });

  it('works out a line, then the totals from the lines and the other fields', () => {
    expect(lineCells(ITEMS, { 'F-q': '3', 'F-r': '250' })).toEqual({ 'F-a': 750 });
    const t = totals([ITEMS, TOTALS], { 'S-1': [{ row: 1, values: { 'F-q': '2', 'F-r': '1000' } }, { row: 2, values: { 'F-q': '1', 'F-r': '300' } }] },
                     { 'F-f': '500' }, 'cgst_sgst', '18');
    expect(t.fields).toEqual([{ id: 'F-t', label: 'Total', value: 2800 }]);
    expect([t.tax, t.grand, t.taxLabel]).toEqual([504, 3304, 'GST 18%']);
  });
});

describe('discounts', () => {
  it('reads an amount or a percent, and nothing else', () => {
    expect(['10%', '12.5 %', '5,000', '₹5000', 'Rs. 5000', '', '0'].map(parseDiscount)).toEqual([
      { kind: 'percent', value: 10 }, { kind: 'percent', value: 12.5 }, { kind: 'amount', value: 5000 }, { kind: 'amount', value: 5000 },
      { kind: 'amount', value: 5000 }, null, null]);
    expect(['10x', '150%', 'abc'].map(parseDiscount)).toEqual(['invalid', 'invalid', 'invalid']);
    expect([takeOff(300000, { kind: 'amount', value: 45000 }), takeOff(1000, { kind: 'percent', value: 12.5 }),
            takeOff(100, { kind: 'amount', value: 500 })]).toEqual([45000, 125, 100]);    // never more than there is
  });

  it("takes a line's discount off its amount, and the document's off the total before tax", () => {
    expect(lineCells(ITEMS, { 'F-q': '3', 'F-r': '1000' }, '10%')).toEqual({ 'F-a': 2700 });
    const t = totals([ITEMS, TOTALS], { 'S-1': [{ row: 1, values: { 'F-q': '2', 'F-r': '1000' }, discount: '500' },
                                                 { row: 2, values: { 'F-q': '1', 'F-r': '300' } }] },
                     { 'F-f': '500' }, 'cgst_sgst', '18', '10%');
    expect([t.total, t.discount, t.taxable, t.tax, t.grand, t.discountLabel]).toEqual([2300, 230, 2070, 372.6, 2442.6, 'Discount (10%)']);
  });
});

describe('Editor', () => {
  it('posts the form the server reads: its lines by row and field, the details and the settings', () => {
    render(<Editor data={DATA} />);
    const values = posted();
    expect(form()).toHaveAttribute('action', '/quotes/create?doc_type=quote');
    expect(values).toMatchObject({ doc_type: 'quote', suggested_number: 'TF/Q/031', template_id: 'T-1', project_id: 'P-1', doc_number: 'TF/Q/031',
                                   'line_item_S-1_3_field_F-d': 'Spline gauge', 'line_item_S-1_3_field_F-q': '2', 'line_item_S-1_3_field_F-a': '',
                                   'field_F-f': '500', 'field_F-t': '', detail_subject: 'Spline gauges', detail_incoterms: '',
                                   currency: 'INR', tax_mode: 'none', tax_rate: '18' });
    expect(screen.getByText('₹2,000.00')).toHaveClass('calc');                     // the line's amount
    expect(screen.getByText('Total').nextElementSibling).toHaveTextContent('₹2,500.00');
  });

  it('adds and removes lines, numbering new ones after the highest, and the totals follow', async () => {
    render(<Editor data={DATA} />);
    await userEvent.click(screen.getByRole('button', { name: 'Add line' }));
    expect(screen.getAllByLabelText('Description')[1]).toHaveFocus();
    await userEvent.type(screen.getAllByLabelText('Qty')[1], '1');
    await userEvent.type(screen.getAllByLabelText('Rate')[1], '300');
    expect(posted()['line_item_S-1_4_field_F-r']).toBe('300');
    expect(screen.getByText('Total').nextElementSibling).toHaveTextContent('₹2,800.00');
    await userEvent.click(screen.getByRole('button', { name: 'Remove line 1' }));
    expect(Object.keys(posted()).filter((k) => k.startsWith('line_item_S-1_3_'))).toEqual([]);
    expect(screen.getByText('Total').nextElementSibling).toHaveTextContent('₹800.00');
    await userEvent.click(screen.getByRole('button', { name: 'Remove line 1' }));      // the last line empties, it stays
    expect(screen.getAllByLabelText('Qty')).toHaveLength(1);
    expect(screen.getAllByLabelText('Qty')[0]).toHaveValue(null);
  });

  it('takes the tax the customer usually gets, and shows GST on the total', async () => {
    render(<Editor data={DATA} />);
    expect(screen.queryByText('GST 18%')).not.toBeInTheDocument();
    await pick(screen.getByLabelText('Customer'), 'Gear Cutters Ltd');
    expect(screen.getByLabelText('Tax')).toHaveValue('CGST + SGST (same state)');
    expect(screen.getByText('CGST 9% + SGST 9%')).toBeInTheDocument();
    expect(screen.getByText('Tamil Nadu GSTIN, so CGST + SGST.')).toBeInTheDocument();          // and why
    expect(screen.getByText('GST 18%').nextElementSibling).toHaveTextContent('₹450.00');
    expect(await optionsOf(screen.getByLabelText('Customer'))).toEqual(['Gear Cutters Ltd', 'Hosur plant', 'Axle Works']);
    expect(document.querySelector('[class*="groupLabel"]')).toHaveTextContent('Gear Cutters Ltd');          // its sites, under it
    await pick(screen.getByLabelText('Customer'), 'Axle Works');
    expect(screen.getByLabelText('Tax')).toHaveValue('IGST (other state)');
    expect(screen.getByText('Karnataka GSTIN, another state, so IGST.')).toBeInTheDocument();
    await pick(screen.getByLabelText('Tax'), 'No tax');                                     // changed by hand: what it would be
    expect(screen.getByText('Suggested: Karnataka GSTIN, another state, so IGST.')).toBeInTheDocument();
  });

  it("says why for a draft's customer, which can't be changed here", () => {
    render(<Editor data={{ ...DATA, customer: { fixed: { id: null, name: 'Axle Works' }, groups: [] },
                           settings: { ...DATA.settings, tax_mode: 'igst' },
                           tax_hint: { mode: 'igst', note: 'Karnataka GSTIN, another state, so IGST' } }} />);
    expect(screen.getByText('Karnataka GSTIN, another state, so IGST.')).toBeInTheDocument();
  });

  it('takes a discount on a line and on the whole, posts them, and shows them in the totals', async () => {
    render(<Editor data={DATA} />);
    expect(screen.queryByLabelText('Discount on line 1')).toBeNull();               // until a line is discounted
    await userEvent.click(screen.getByRole('button', { name: 'Discount a line' }));
    await userEvent.type(screen.getByLabelText('Discount on line 1'), '10%');
    expect(screen.getByText('₹1,800.00')).toHaveClass('calc');                     // 2 × 1,000 less 10%
    await userEvent.type(screen.getByLabelText('Discount on the total'), '300');
    expect(posted()).toMatchObject({ 'line_discount_S-1_3': '10%', discount: '300' });
    expect(screen.getByText('Sub total').nextElementSibling).toHaveTextContent('₹2,300.00');
    expect(screen.getByText('Discount', { selector: 'dt' }).nextElementSibling).toHaveTextContent('-₹300.00');
    expect(screen.getAllByText('Total').at(-1)!.parentElement!.nextElementSibling).toHaveTextContent('₹2,000.00');
    await userEvent.clear(screen.getByLabelText('Discount on the total'));
    await userEvent.type(screen.getByLabelText('Discount on the total'), 'ten');
    expect(screen.getByLabelText('Discount on the total')).toBeInvalid();             // the form won't go
  });

  it('opens with the discounts a document has', () => {
    render(<Editor data={{ ...DATA, discount: '5%', sections: [{ ...ITEMS, rows: [{ ...ITEMS.rows![0], discount: '250' }] }, TOTALS] }} />);
    expect(screen.getByLabelText('Discount on line 1')).toHaveValue('250');
    expect(screen.getByLabelText('Discount on the total')).toHaveValue('5%');
    expect(screen.getByText('Discount (5%)').nextElementSibling).toHaveTextContent('-₹112.50');
  });

  it('says it is correcting a sent document, and keeps it from being renumbered by accident', () => {
    render(<Editor data={{ ...DATA, correcting: true, editing: true, title: 'Correct TF/INV/007', submit: 'Save the correction',
                           type: { ...DATA.type, label: 'Tax Invoice', key: 'invoice', sent_word: 'finalized', takes_payments: true },
                           customer: { fixed: { id: null, name: 'Gear Cutters Ltd' }, groups: [] },
                           hidden: { doc_type: 'invoice', suggested_number: '', correct: '1' }, number: { value: 'TF/INV/007', required: true } }} />);
    expect(screen.getByText("You're correcting a tax invoice that was finalized.")).toBeInTheDocument();
    expect(screen.getByLabelText('Number')).toBeRequired();
    expect(posted()).toMatchObject({ correct: '1', doc_number: 'TF/INV/007' });
    expect(posted()).not.toHaveProperty('customer_id');
  });
});

describe('the preview beside the editor', () => {
  const DRAWN = { html: '<article class="card invoice-doc"><h1>Q/001</h1><p>Hob arbor</p></article>', total: 1180,
                  email: { subject: 'Quotation Q/001 · Spline gauges (PRJ-001)', body: 'Dear Sir/Madam,\n\nPlease find attached our quotation Q/001.' },
                  whatsapp: 'Dear …,\n\nPlease find our quotation Q/001: ₹1,180 incl. GST.' };
  afterEach(() => { vi.restoreAllMocks(); try { localStorage.removeItem('dm-editor-preview'); } catch { /* none */ } });
  // the app's header, where the editor puts its buttons (PageHeader)
  const withHeader = () => {
    const actions = document.createElement('div'); document.body.append(actions);
    return <HeaderSlots.Provider value={{ crumbs: null, actions }}><Editor data={DATA} /></HeaderSlots.Provider>;
  };

  it('draws what is typed, as its page, email and message, and remembers to sit beside it', async () => {
    const fetched = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(DRAWN), { status: 200 }));
    const first = render(withHeader());
    expect(screen.queryByRole('region', { name: 'Preview' })).toBeNull();               // off until picked
    await userEvent.click(screen.getByRole('button', { name: 'Preview beside' }));
    expect(await screen.findByText('Hob arbor')).toBeInTheDocument();
    const [url, init] = fetched.mock.calls[0];
    expect(url).toBe('/api/editor/new/quotes/preview');
    expect(JSON.parse(String((init as RequestInit).body)).fields).toMatchObject({ doc_type: 'quote', 'line_item_S-1_3_field_F-q': '2' });

    await userEvent.click(screen.getByRole('tab', { name: 'Email' }));
    expect(screen.getByText('Quotation Q/001 · Spline gauges (PRJ-001)')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('tab', { name: 'WhatsApp' }));
    expect(screen.getByText(/Please find our quotation Q\/001/)).toBeInTheDocument();

    const before = fetched.mock.calls.length;
    await userEvent.type(screen.getAllByLabelText('Qty')[0], '5');
    await waitFor(() => expect(fetched.mock.calls.length).toBeGreaterThan(before));   // drawn again
    expect(JSON.parse(String((fetched.mock.calls.at(-1)![1] as RequestInit).body)).fields['line_item_S-1_3_field_F-q']).toBe('25');

    first.unmount();
    render(withHeader());                                                               // the next document opens with it beside
    expect(screen.getByRole('region', { name: 'Preview' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Preview beside' })).toHaveAttribute('aria-pressed', 'true');
  });
});
