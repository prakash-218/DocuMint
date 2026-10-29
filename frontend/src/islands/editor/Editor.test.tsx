import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { evaluate, lineCells, totals } from './calc';
import { Editor } from './Editor';
import type { EditorData, Section } from './types';

const ITEMS: Section = {
  id: 'S-1', type: 'line_item', title: 'Items', name: 'items', fields: [
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
  action: '/quotes/create?doc_type=quote', cancel: '/projects/P-1', submit: 'Create', submit_side: 'Create quotation',
  hidden: { doc_type: 'quote', suggested_number: 'TF/Q/031', template_id: 'T-1', project_id: 'P-1' },
  customer: { fixed: null, groups: [{ label: 'Gear Cutters Ltd', options: [{ id: 'C-1', label: 'Gear Cutters Ltd' }, { id: 'C-2', label: 'Hosur plant' }] },
                                    { label: null, options: [{ id: 'C-9', label: 'Axle Works' }] }] },
  number: { value: 'TF/Q/031', required: false }, issue_date: '2026-10-29', due_date: '',
  sections: [ITEMS, TOTALS],
  details: { fields: [{ key: 'subject', label: 'Subject', kind: 'text', placeholder: '', group: '' },
                      { key: 'incoterms', label: 'Incoterms', kind: 'text', placeholder: 'FOB Chennai', group: 'export' }],
             values: { subject: 'Spline gauges' }, groups: [{ key: 'export', label: 'Export terms', fields: ['incoterms'], open: false }] },
  settings: { currencies: ['INR', 'USD'], currency: 'INR', tax_modes: [['none', 'No tax'], ['cgst_sgst', 'CGST + SGST (same state)'], ['igst', 'IGST (other state)']],
              tax_mode: 'none', tax_rate: '18', advance_percent: '', advance_basis: 'pre_tax' },
  tax_hints: { 'C-1': 'cgst_sgst', 'C-9': 'igst' },
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
    await userEvent.selectOptions(screen.getByLabelText('Customer'), 'C-1');
    expect(screen.getByLabelText('Tax')).toHaveValue('cgst_sgst');
    expect(screen.getByText('CGST 9% + SGST 9%')).toBeInTheDocument();
    expect(screen.getByText('GST 18%').nextElementSibling).toHaveTextContent('₹450.00');
    const sites = within(screen.getByLabelText('Customer')).getByRole('group', { name: 'Gear Cutters Ltd' });
    expect(within(sites).getAllByRole('option').map((o) => o.textContent)).toEqual(['Gear Cutters Ltd', 'Hosur plant']);
  });

  it('says what correcting a sent document means, and keeps it from being renumbered by accident', () => {
    render(<Editor data={{ ...DATA, correcting: true, editing: true, title: 'Correct TF/INV/007', submit: 'Save the correction',
                           type: { ...DATA.type, label: 'Tax Invoice', key: 'invoice', sent_word: 'finalized', takes_payments: true },
                           customer: { fixed: { id: null, name: 'Gear Cutters Ltd' }, groups: [] },
                           hidden: { doc_type: 'invoice', suggested_number: '', correct: '1' }, number: { value: 'TF/INV/007', required: true } }} />);
    expect(screen.getByText(/You're correcting a tax invoice that was finalized/)).toHaveTextContent('paid / pending follows the payments');
    expect(screen.getByLabelText('Number')).toBeRequired();
    expect(posted()).toMatchObject({ correct: '1', doc_number: 'TF/INV/007' });
    expect(posted()).not.toHaveProperty('customer_id');
  });
});
