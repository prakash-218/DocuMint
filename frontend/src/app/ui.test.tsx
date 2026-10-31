import { render, screen } from '../test/render';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import { CustomerFormView } from '../islands/customers/CustomerForm';
import type { CustomerForm } from '../islands/customers/types';
import type { Boot } from './boot';
import { BootContext } from './Layout';
import { pageHref, Pager } from './ui';

describe('Pager', () => {
  it('links the other pages on this address, its other arguments kept', () => {
    expect(pageHref('/emails/', '?show=all&page=3', 4)).toBe('/emails/?show=all&page=4');
    expect(pageHref('/emails/', '?show=all&page=3', 1)).toBe('/emails/?show=all');
    render(
      <MemoryRouter initialEntries={['/emails/?show=all&page=6']}>
        <Pager page={{ page: 6, pages: 20, first: 126, last: 150, total: 492, numbers: [1, null, 4, 5, 6, 7, 8, null, 20], noun: 'threads' }} />
      </MemoryRouter>,
    );
    expect(screen.getByText('126–150 of 492 threads')).toBeInTheDocument();
    expect(screen.getByText('6')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Next page' })).toHaveAttribute('href', '/emails/?show=all&page=7');
    expect(screen.getAllByText('…')).toHaveLength(2);
  });

  it("isn't there for one page", () => {
    const { container } = render(
      <MemoryRouter><Pager page={{ page: 1, pages: 1, first: 1, last: 3, total: 3, numbers: [1], noun: '' }} /></MemoryRouter>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});

const FORM: CustomerForm = {
  title: 'New customer', name: null, action: '/customers/create', cancel: '/customers/', submit: 'Create customer',
  values: { name: '', parent_id: '', site_name: '', tax_id: '', email_domains: '', payment_days: '', street_address: '', city: '',
            state: '', zip_code: '', country: 'India' },
  site_count: 0, parents: [{ id: 'C-1', name: 'Gear Cutters Ltd' }], domains_help: '',
  payment_help: "How many days after the invoice date they pay. Empty: your usual terms (30 days).",
  custom: [{ key: 'vendor_code', label: 'Vendor code', value: '' }],
  gst_states: { '29': 'Karnataka', '33': 'Tamil Nadu' },
};

function drawn(boot: Partial<Boot>, path = '/customers/create', form = FORM) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <BootContext.Provider value={boot as Boot}><CustomerFormView data={form} /></BootContext.Provider>
    </MemoryRouter>,
  );
  return Object.fromEntries(new FormData(document.querySelector('form') as HTMLFormElement).entries());
}

describe('a form the server turned down', () => {
  it('starts again from what was typed, on the page that answered it', () => {
    const posted = { path: '/customers/create', values: { name: 'Spindle Works', payment_days: '400', parent_id: 'C-1', custom_vendor_code: 'V-9' } };
    expect(drawn({ posted })).toMatchObject({ name: 'Spindle Works', payment_days: '400', parent_id: 'C-1', custom_vendor_code: 'V-9', country: 'India' });
  });

  it('ignores it anywhere else', () => {
    const posted = { path: '/customers/C-1/edit', values: { name: 'Spindle Works' } };
    expect(drawn({ posted })).toMatchObject({ name: '', country: 'India' });
  });

  it("leaves out Site of when the customer has sites of its own", () => {
    const values = drawn({}, '/customers/C-1/edit', { ...FORM, site_count: 2 });
    expect(values).not.toHaveProperty('parent_id');
    expect(screen.getByText(/2 sites belong to this/)).toBeInTheDocument();
  });
});

describe("a customer's GSTIN", () => {
  it('says which state it is registered in, and fills in an empty State', async () => {
    drawn({});
    const gstin = screen.getByLabelText('GSTIN / Tax ID');
    await userEvent.type(gstin, '29ABCDE1234F1Z');
    expect(screen.queryByText(/Registered in/)).toBeNull();                         // not a whole GSTIN yet
    await userEvent.type(gstin, '5');
    expect(screen.getByText('Registered in Karnataka. Its state decides CGST + SGST or IGST.')).toBeInTheDocument();
    expect(screen.getByLabelText('State')).toHaveValue('Karnataka');
  });

  it('leaves a State that was typed', async () => {
    drawn({}, '/customers/create', { ...FORM, values: { ...FORM.values, state: 'TN' } });
    await userEvent.type(screen.getByLabelText('GSTIN / Tax ID'), '33ABCDE1234F1Z5');
    expect(screen.getByText(/Registered in Tamil Nadu/)).toBeInTheDocument();
    expect(screen.getByLabelText('State')).toHaveValue('TN');
  });
});
