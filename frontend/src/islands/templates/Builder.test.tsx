import { render, screen } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import type { Boot } from '../../app/boot';
import { BootContext } from '../../app/Layout';
import { BuilderForm, fromPosted } from './Builder';
import { LayoutForm } from './PagesPrinting';

type BuilderData = Parameters<typeof BuilderForm>[0]['data'];

const DATA: BuilderData = {
  title: 'Edit Quotation', creating: false, sub: 'INR · v1', action: '/templates/T-1/edit', cancel: '/templates/T-1',
  in_use: '4 documents use v1. Saving creates v2; existing documents don\'t change.',
  sections: [{ title: 'Items', name: 'items', type: 'line_item', fields: [
    { label: 'Description', name: 'description', type: 'string', formula: '', currency: false, required: true },
    { label: 'Rate', name: 'rate', type: 'number', formula: '', currency: true, required: false },
    { label: 'Amount', name: 'amount', type: 'number', formula: 'this.rate * this.qty', currency: true, required: false }] },
  { title: 'Totals', name: 'totals', type: 'normal', fields: [
    { label: 'Total', name: 'total', type: 'number', formula: 'SUM(items.amount)', currency: true, required: false }] }],
  total: '2:1',
  field_types: [['string', 'Text'], ['number', 'Number']], section_types: [['line_item', 'Line items (a table)'], ['normal', 'Fields (totals, notes...)']],
  currencies: ['INR', 'USD'], currency: 'INR', choosable: [['quote', 'Quotations'], ['invoice', 'Invoices']],
};

function drawn(data: BuilderData, boot: Partial<Boot> = {}) {
  render(<MemoryRouter initialEntries={['/templates/T-1/edit']}>
    <BootContext.Provider value={boot as Boot}><BuilderForm data={data} /></BootContext.Provider>
  </MemoryRouter>);
}
const posted = () => Object.fromEntries(new FormData(document.getElementById('tplForm') as HTMLFormElement));

describe('the template builder', () => {
  it('posts the sections and fields as template_builder reads them', () => {
    drawn(DATA);
    expect(posted()).toMatchObject({ section_count: '2', s1_present: '1', s1_name: 'items', s1_field_count: '3', s1_f2_label: 'Rate',
                                     s1_f2_currency: 'on', s1_f3_formula: 'this.rate * this.qty', s1_f1_required: 'on', total: '2:1' });
    expect(posted()).not.toHaveProperty('s1_f1_formula');                   // text fields have no formula
    expect(screen.getByText(/4 documents use v1/)).toBeInTheDocument();
  });

  it('adds a field after the highest number and drops a removed one', async () => {
    drawn(DATA);
    const items = screen.getAllByRole('button', { name: 'Add field' })[0];
    await userEvent.click(items);
    await userEvent.type(document.activeElement as HTMLElement, 'Grade');
    expect(posted()).toMatchObject({ s1_field_count: '4', s1_f4_label: 'Grade', s1_f4_type: 'string' });
    expect(screen.getByText('grade')).toHaveClass('field-code');            // the name formulas will use
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove field' })[1]);
    expect(posted()).not.toHaveProperty('s1_f2_present');
    expect(posted()).toMatchObject({ s1_field_count: '4' });
  });

  it('offers the number fields of a fields section as the document total', async () => {
    drawn(DATA);
    const total = screen.getByLabelText('Document total');
    expect(total).toHaveValue('Totals › Total');
    await userEvent.click(total);
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual(['Totals › Total']);
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove section' })[1]);
    expect(total).toHaveValue('');
    expect(total).toHaveAttribute('placeholder', 'Add a number field to a fields section');
  });

  it('comes back with what was sent when the save is turned down', () => {
    const values = { section_count: '2', s1_present: '1', s1_title: 'Lines', s1_name: '', s1_type: 'line_item', s1_field_count: '2',
                     s1_f2_present: '1', s1_f2_label: 'Qty', s1_f2_type: 'number', s2_title: 'Gone', name: 'Spline quote', total: '' };
    expect(fromPosted(values)).toEqual([{ i: 1, title: 'Lines', name: '', type: 'line_item',
                                          fields: [{ j: 2, label: 'Qty', name: '', type: 'number', formula: '', currency: false, required: false }] }]);
    drawn({ ...DATA, creating: true }, { posted: { path: '/templates/T-1/edit', values } });
    expect(posted()).toMatchObject({ name: 'Spline quote', s1_title: 'Lines', s1_f2_label: 'Qty', s1_field_count: '2' });
  });
});

describe('pages & printing', () => {
  it('leaves a removed page out, and numbers new box details after the last', async () => {
    render(<LayoutForm data={{
      title: 'Pages & printing', name: 'Tax Invoice', back: '/templates/T-1', action: '/templates/T-1/layout', used_for: ['invoice'], guessed: false,
      export: 'auto', auto_export: false, choosable: [['invoice', 'Invoices']], doc_types: [['invoice', 'Tax Invoice']],
      kinds: { document: 'Main document', packing: 'Packing list', annexure: 'Annexure (extra page)' },
      pages: [{ key: 'document', kind: 'document', title: '', doc_types: [], with_document: true, copies: ['Original'], columns: [] },
              { key: 'packing', kind: 'packing', title: 'Shipping list', doc_types: ['invoice'], with_document: false, copies: [], columns: [],
                box_fields: [{ key: 'pallet_no', label: 'Pallet no.', sum: false }] },
              { key: 'annexure', kind: 'annexure', title: 'Terms', doc_types: [], with_document: true, copies: [], columns: [], sections: [] }],
      item_fields: [{ name: 'qty', label: 'Qty' }], sections: [{ name: 'items', label: 'Items' }],
    }} />);
    const form = () => new FormData(document.querySelector('form') as HTMLFormElement);
    expect(Object.fromEntries(form())).toMatchObject({ page_count: '3', page_1_copies: 'Original', page_2_box_label_1: 'Pallet no.', page_2_box_key_1: 'pallet_no' });
    expect(form().getAll('used_for')).toEqual(['invoice']);
    await userEvent.click(screen.getByRole('button', { name: 'Add box detail' }));
    expect(form().has('page_2_box_label_3')).toBe(true);
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove page' })[1]);
    expect(form().has('page_3_present')).toBe(false);
    expect(Object.fromEntries(form())).toMatchObject({ page_count: '2' });
  });
});
