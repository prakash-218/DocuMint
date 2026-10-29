import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomerPage from './CustomerPage';
import type { CustomerData } from './types';

const DATA: CustomerData = {
  customer: {
    id: 'C-1', name: 'Gear Cutters Ltd', site: null, parent: null, tax_id: '33AAACG1234B1Z5', email_domains: 'gearco.example',
    address: ['12 Industrial Estate', 'Ambattur, Tamil Nadu, 600058', 'India'], archived: false, custom: [{ label: 'Vendor code', value: 'V-2231' }],
    classic_url: '/customers/C-1',
  },
  can: { edit: true, edit_customer: true, manage: true, sales: false },
  money: {
    total: { INR: 80000 }, count: 1,
    ages: [{ label: '0–30 days', count: 0, total: {} }, { label: '31–60 days', count: 1, total: { INR: 80000 } },
           { label: '61–90 days', count: 0, total: {} }, { label: 'Over 90 days', count: 0, total: {} }],
    customers: [{ id: 'C-1', name: 'Gear Cutters Ltd', count: 1, total: { INR: 50000 } },
                { id: 'C-2', name: 'Gear Cutters Ltd · Hosur plant', count: 1, total: { INR: 30000 } }],
    advances: { count: 0, total: {} }, advance_held: { INR: 10000 },
    statement: [{
      currency: 'INR', owed: 100000, paid: 30000, balance: 70000,
      lines: [
        { date: '2026-02-15', fy: '25-26', text: 'Advance on PI 007, applied to 058', sub: 'NEFT / RTGS', owed: 0, paid: 20000, balance: -20000, url: '/invoices/I-58/new' },
        { date: '2026-04-12', fy: '26-27', text: 'Tax Invoice 058', sub: '', owed: 100000, paid: 0, balance: 80000, url: '/invoices/I-58/new' },
        { date: '2026-05-06', fy: '26-27', text: 'Advance on PI 009', sub: '', owed: 0, paid: 10000, balance: 70000, url: '/proformas/P-9/new' },
      ],
    }],
  },
  projects: [
    { id: 'P-1', label: 'PRJ-041', title: 'Hob arbor set', reference: '', url: '/projects/P-1/new', customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: null },
      fiscal_year: '26-27', status: 'open', stage: 'paid', pill: { text: 'Part paid', tone: 'wait' }, sub: '', next: '₹80,000 due.',
      action: 'Record payment', tone: 'wait', currency: 'INR', quoted: 100000, due: 80000, last_activity: '2026-05-06', numbers: ['058'] },
    { id: 'P-2', label: 'PRJ-012', title: 'Old fixture', reference: '', url: '/projects/P-2/new', customer: { id: 'C-2', name: 'Gear Cutters Ltd', site: 'Hosur plant' },
      fiscal_year: '25-26', status: 'completed', stage: null, pill: { text: 'Paid', tone: 'done' }, sub: '', next: '', action: null, tone: 'done',
      currency: 'INR', quoted: 9000, due: 0, last_activity: '2025-11-02', numbers: [] },
  ],
  documents: [
    { invoice_id: 'I-58', doc_type: 'invoice', kind: 'Tax Invoice', number: '058', status: 'pending', issue_date: '2026-04-12', currency: 'INR',
      total: 100000, paid: 20000, balance: 80000, url: '/invoices/I-58/new', pdf: '/invoices/I-58/pdf', versions: [], site: null },
    { invoice_id: 'Q-41', doc_type: 'quote', kind: 'Quotation', number: 'Q/041', status: 'converted', issue_date: '2026-01-20', currency: 'INR',
      total: 100000, paid: 0, balance: null, url: '/quotes/Q-41/new', pdf: '/quotes/Q-41/pdf', versions: [], site: 'Hosur plant' },
  ],
  statuses: { open: 'Open', completed: 'Completed', cancelled: 'Cancelled' },
  files: [{ project: { id: 'P-1', title: 'Hob arbor set', label: 'PRJ-041', url: '/projects/P-1/new' },
            files: [{ id: 'A-1', name: 'arbor.pdf', kind: 'drawing', kind_label: 'Drawing', title: null, reference_no: null, date: '2026-01-10',
                      size: '2 KB', from_email: true, url: '/projects/files/A-1' }] }],
  files_count: 1,
  people: [{ contact_id: 'K-1', customer_id: 'C-1', name: 'Ravi Kumar', email: 'ravi@gearco.example', phone: null, role: 'Purchase',
             gets: 'all', initials: 'RK', at_parent: false }],
  usually: { all: 'Everything', billing: 'Invoices and payments', none: 'Nothing' },
  sites: [{ id: 'C-2', name: 'Hosur plant', tax_id: null, archived: false, documents: 3, url: '/customers/C-2/new' }],
  links: { new_project: '/projects/new?customer_id=C-1', edit: '/customers/C-1/edit', add_site: '/customers/create?parent_id=C-1' },
};

function serve(data: CustomerData = DATA) {
  const fetch = vi.fn(async (_path: string, init?: RequestInit) => new Response(
    JSON.stringify(init?.method && init.method !== 'GET' ? { ok: true } : data), { status: 200, headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState(null, '', '/');
});

describe('CustomerPage', () => {
  it('shows what they owe, how old it is and by site, then the open projects', async () => {
    serve();
    render(<CustomerPage customerId="C-1" />);
    expect((await screen.findByText('Due on invoices')).parentElement).toHaveTextContent('Due on invoices₹80,000on 1 invoice');
    expect(screen.getByText('Advance held').parentElement).toHaveTextContent('Advance held₹10,000');
    const ages = screen.getByRole('list', { name: "How old what's due is" });
    expect(within(ages).getAllByRole('listitem')[1]).toHaveClass('has-due');
    expect(screen.getByRole('list', { name: 'Due by site' })).toHaveTextContent('Gear Cutters Ltd · Hosur plant₹30,000');
    const panel = screen.getByRole('tabpanel');
    expect(within(panel).getByRole('link', { name: /Hob arbor set/ })).toHaveAttribute('href', '/projects/P-1/new');
    expect(within(panel).queryByText('Old fixture')).not.toBeInTheDocument();       // finished: behind a button
    fireEvent.click(within(panel).getByRole('button', { name: 'Show 1 finished project' }));
    expect(within(panel).getByText('Old fixture')).toBeInTheDocument();
  });

  it('lists the documents by type, and the statement by financial year with what was brought forward', async () => {
    serve();
    render(<CustomerPage customerId="C-1" />);
    fireEvent.click(await screen.findByRole('tab', { name: /Documents/ }));
    expect(window.location.hash).toBe('#documents');
    expect(within(screen.getByRole('tabpanel')).getAllByRole('row')).toHaveLength(3);
    fireEvent.click(screen.getByRole('button', { name: /Quotations/ }));
    const rows = within(screen.getByRole('tabpanel')).getAllByRole('row');
    expect(rows).toHaveLength(2);
    expect(rows[1]).toHaveTextContent('Q/041');
    expect(rows[1]).toHaveTextContent('Accepted');

    fireEvent.click(screen.getByRole('tab', { name: 'Statement' }));
    const table = within(screen.getByRole('tabpanel'));
    expect(table.getByText('Balance now').closest('tr')).toHaveTextContent('₹70,000');
    fireEvent.change(table.getByLabelText('Financial year'), { target: { value: '26-27' } });
    expect(table.getByText('Brought forward').closest('tr')).toHaveTextContent('-₹20,000');
    expect(table.queryByText('Advance on PI 007, applied to 058')).not.toBeInTheDocument();
    expect(table.getByText('Balance at the end of FY 26-27').closest('tr')).toHaveTextContent('₹1,00,000₹10,000₹70,000');
  });

  it('keeps Sales to the customer and their quotations: no money, no statement', async () => {
    serve({ ...DATA, money: null, can: { ...DATA.can, sales: true } });
    render(<CustomerPage customerId="C-1" />);
    await screen.findByRole('tab', { name: /Projects/ });
    expect(screen.queryByRole('tab', { name: 'Statement' })).not.toBeInTheDocument();
    expect(screen.queryByText('Due on invoices')).not.toBeInTheDocument();
  });

  it('adds, changes and removes contacts', async () => {
    const fetch = serve();
    render(<CustomerPage customerId="C-1" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Edit Ravi Kumar' }));
    fireEvent.change(screen.getByLabelText(/Role/), { target: { value: 'Accounts' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/customers/C-1/contacts/K-1', expect.objectContaining({ method: 'POST' })));
    expect(JSON.parse(String(fetch.mock.calls.find((c) => c[0] === '/api/customers/C-1/contacts/K-1')![1]!.body)).role).toBe('Accounts');

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    fireEvent.click(await screen.findByRole('button', { name: 'Remove Ravi Kumar' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/customers/C-1/contacts/K-1', expect.objectContaining({ method: 'DELETE' })));
  });
});
