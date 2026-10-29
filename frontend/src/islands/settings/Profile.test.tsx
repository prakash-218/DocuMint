import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { ProfileForm } from './Profile';

type Data = Parameters<typeof ProfileForm>[0]['data'];

const DATA: Data = {
  title: 'Business profile',
  org: { name: 'Gear Cutters Ltd', address: 'Hosur, India', edit: '/settings/organizations/O-1/edit' },
  action: '/settings/profile',
  values: { gstin: '33ABCDE1234F1Z5', default_currency: 'INR', default_gst_rate: '18', fy_start_month: '4', advance_basis: 'pre_tax',
            payment_days: '30', letterhead_style: 'left', letterhead_color: '#2b3138', letterhead_accent: '#2b3138', team_addresses: '' },
  checks: { separate_export_series: false, logo_has_name: true },
  currencies: ['INR', 'USD'],
  months: [['1', 'January'], ['4', 'April']],
  series: [{ key: 'invoice', label: 'Tax Invoice', format: 'GC/{num:03}/{fy}', next: 12, shared: false, preview: 'GC/012/26-27' },
           { key: 'export_invoice', label: 'Export Invoice', format: '', next: null, shared: true, preview: 'GC/012/26-27' }],
  custom_fields: [{ key: 'msme', label: 'MSME No.', value: 'UDYAM-TN-02-0000001', print: true }],
  customer_fields: [],
  images: { logo: null, logo_small: 'data:image/png;base64,iVBORw0KGgo=', stamp: null, signature: null },
  starter: '/settings/profile/starter-templates',
};

const posted = () => new FormData(screen.getByRole('button', { name: 'Save profile' }).closest('form') as HTMLFormElement);

describe('the business profile', () => {
  it('posts what is saved now, the way the server reads it', () => {
    render(<ProfileForm data={DATA} />);
    const form = posted();
    expect(Object.fromEntries(form.entries())).toMatchObject({
      gstin: '33ABCDE1234F1Z5', fy_start_month: '4', letterhead_style: 'left', logo_has_name: 'on', format_invoice: 'GC/{num:03}/{fy}',
      next_invoice: '12', orgcf_key_1: 'msme', orgcf_label_1: 'MSME No.', orgcf_value_1: 'UDYAM-TN-02-0000001', orgcf_print_1: 'on',
      orgcf_label_2: '', custcf_label_1: '' });
    expect(form.has('next_export_invoice')).toBe(false);                        // shares the tax invoice series
    expect(form.has('separate_export_series')).toBe(false);
    expect(screen.getByAltText('Logo for invoices (optional)')).toBeInTheDocument();
  });

  it('adds and removes custom fields; a removed one is not sent, so it is dropped', async () => {
    render(<ProfileForm data={DATA} />);
    const [org] = document.querySelectorAll('.cf-table');
    await userEvent.click(screen.getAllByRole('button', { name: 'Add field' })[0]);
    expect(within(org as HTMLElement).getAllByLabelText('Label').map((i) => i.getAttribute('name'))).toEqual(['orgcf_label_1', 'orgcf_label_2', 'orgcf_label_3']);
    await userEvent.click(within(org as HTMLElement).getAllByRole('button', { name: 'Remove' })[0]);
    expect(posted().has('orgcf_label_1')).toBe(false);
    expect(posted().has('orgcf_label_3')).toBe(true);
  });
});
