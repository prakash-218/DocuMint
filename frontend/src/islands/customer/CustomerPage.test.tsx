import { fireEvent, pick, render, screen, waitFor, within } from '../../test/render';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomerPage from './CustomerPage';
import type { CustomerData } from './types';

const DATA: CustomerData = {
  customer: {
    id: 'C-1', name: 'Gear Cutters Ltd', site: null, parent: null, tax_id: '33AAACG1234B1Z5', email_domains: 'gearco.example',
    address: ['12 Industrial Estate', 'Ambattur, Tamil Nadu, 600058', 'India'], archived: false, custom: [{ label: 'Vendor code', value: 'V-2231' }],
    tax_note: 'Tamil Nadu, so CGST + SGST', payment_terms: '45 days',
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
      fiscal_year: '26-27', status: 'open', stage: 'paid', pill: { text: 'Part paid', tone: 'wait' }, stage_label: 'Invoiced', sub: '₹80,000 due', next: '₹80,000 due.',
      action: 'Record payment', tone: 'wait', currency: 'INR', quoted: 100000, due: 80000, last_activity: '2026-05-06', numbers: ['058'] },
    { id: 'P-2', label: 'PRJ-012', title: 'Old fixture', reference: '', url: '/projects/P-2/new', customer: { id: 'C-2', name: 'Gear Cutters Ltd', site: 'Hosur plant' },
      fiscal_year: '25-26', status: 'completed', stage: null, pill: { text: 'Paid', tone: 'done' }, stage_label: 'Paid', sub: '', next: '', action: null, tone: 'done',
      currency: 'INR', quoted: 9000, due: 0, last_activity: '2025-11-02', numbers: [] },
  ],
  documents: [
    { invoice_id: 'I-58', doc_type: 'invoice', kind: 'Tax Invoice', number: '058', status: 'pending', issue_date: '2026-04-12', currency: 'INR',
      total: 100000, paid: 20000, balance: 80000, url: '/invoices/I-58/new', pdf: '/invoices/I-58/pdf', versions: [], site: null, project_id: 'P-1' },
    { invoice_id: 'Q-41', doc_type: 'quote', kind: 'Quotation', number: 'Q/041', status: 'converted', issue_date: '2026-01-20', currency: 'INR',
      total: 100000, paid: 0, balance: null, url: '/quotes/Q-41/new', pdf: '/quotes/Q-41/pdf', versions: [], site: 'Hosur plant', project_id: 'P-1' },
  ],
  statuses: { open: 'Open', completed: 'Completed', cancelled: 'Cancelled' },
  files: [{ project: { id: 'P-1', title: 'Hob arbor set', label: 'PRJ-041', url: '/projects/P-1/new' },
            files: [{ id: 'A-1', name: 'arbor.pdf', kind: 'drawing', kind_label: 'Drawing', title: null, reference_no: null, date: '2026-01-10',
                      size: '2 KB', from_email: true, url: '/projects/files/A-1', delete: '/projects/files/A-1/delete',
                      customer_id: 'C-1', move: '/projects/files/A-1/link' }] }],
  files_count: 1,
  people: [{ contact_id: 'K-1', customer_id: 'C-1', name: 'Ravi Kumar', email: 'ravi@gearco.example', phone: null, role: 'Purchase',
             gets: 'all', initials: 'RK', at_parent: false }],
  usually: { all: 'Everything', billing: 'Invoices and payments', none: 'Nothing' },
  sites: [{ id: 'C-2', name: 'Hosur plant', tax_id: null, archived: false, documents: 3, url: '/customers/C-2/new' }],
  links: { new_project: '/projects/new?customer_id=C-1', new_quote: '/quotes/create?customer_id=C-1', edit: '/customers/C-1/edit',
           add_site: '/customers/create?parent_id=C-1', archive: '/customers/C-1/archive', statement_pdf: '/customers/C-1/statement.pdf',
           statement_email: { compose: '/api/customers/C-1/statement/compose', send: '/api/customers/C-1/statement/emails' } },
  upload: { action: '/projects/files', kinds: { drawing: 'Drawing', po: 'Purchase order', other: 'Other' } },
  portal: { email: null, login_url: 'https://portal.example/customer/login', create: '/customers/C-1/create-portal-account' },
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
  it('shows who they are and what they owe, then the open projects by the step each has reached', async () => {
    serve();
    render(<CustomerPage customerId="C-1" />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Gear Cutters Ltd');
    expect(screen.getByText('Tamil Nadu, so CGST + SGST')).toBeInTheDocument();
    expect(screen.getByLabelText('Due by how old the invoice is')).toHaveTextContent('31–60 days old: ₹80,000');
    expect(screen.getByText('Balance').closest('.balance')).toHaveTextContent('Balance₹70,000₹80,000 due on 1 invoice, less ₹10,000 advance held');
    const panel = screen.getByRole('tabpanel');
    expect(within(panel).getByRole('link', { name: 'New quotation' })).toHaveAttribute('href', '/quotes/create?customer_id=C-1');
    const row = within(panel).getByText('Hob arbor set').closest('a')!;
    expect(row).toHaveAttribute('href', '/projects/P-1/new');
    expect(within(row).getByText('Invoiced')).toHaveClass('tag', 'tone-wait');
    expect(within(panel).queryByText('Old fixture')).not.toBeInTheDocument();       // finished: behind a button
    fireEvent.click(within(panel).getByRole('button', { name: 'Show 1 finished project too' }));
    expect(within(panel).getByText('Old fixture')).toBeInTheDocument();
    expect(within(panel).getByRole('link', { name: /^Hosur plant/ })).toHaveAttribute('href', '/customers/C-2/new');
  });

  it('lists the documents by type, and the statement by financial year with what was brought forward', async () => {
    serve();
    render(<CustomerPage customerId="C-1" />);
    fireEvent.click(await screen.findByRole('tab', { name: /Documents/ }));
    expect(window.location.hash).toBe('#documents');
    const rows = () => within(screen.getByRole('tabpanel')).getAllByRole('link');
    expect(rows()).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', { name: /Quotations/ }));
    expect(rows()).toHaveLength(1);
    expect(rows()[0]).toHaveTextContent('Q/041');
    expect(within(rows()[0]).getByText('Accepted')).toHaveClass('tone-done');

    fireEvent.click(screen.getByRole('tab', { name: 'Statement' }));
    const table = within(screen.getByRole('tabpanel'));
    expect(table.getByText('Opening balance').closest('tr')).toHaveTextContent('-₹20,000');          // FY 26-27 first
    expect(table.queryByText('Advance on PI 007, applied to 058')).not.toBeInTheDocument();
    expect(table.getByText('Balance due').closest('tr')).toHaveTextContent('₹70,000');
    expect(table.getByRole('link', { name: /PDF/ })).toHaveAttribute('href', '/customers/C-1/statement.pdf?fy=26-27&currency=INR');
    await pick(table.getByLabelText('Financial year'), 'Every year');
    expect(table.getByText('Advance on PI 007, applied to 058')).toBeInTheDocument();
    expect(table.queryByText('Opening balance')).not.toBeInTheDocument();
    expect(table.getByRole('link', { name: /PDF/ })).toHaveAttribute('href', '/customers/C-1/statement.pdf?fy=all&currency=INR');
    expect(table.getByRole('button', { name: /Email/ })).toBeInTheDocument();      // opens the email form for this statement
  });

  it('keeps Sales to the customer and their quotations: no money, no statement', async () => {
    serve({ ...DATA, money: null, can: { ...DATA.can, sales: true } });
    render(<CustomerPage customerId="C-1" />);
    await screen.findByRole('tab', { name: /Overview/ });
    expect(screen.queryByRole('tab', { name: 'Statement' })).not.toBeInTheDocument();
    expect(screen.queryByText('Balance')).not.toBeInTheDocument();
  });

  it('adds, changes and removes contacts', async () => {
    const fetch = serve();
    render(<CustomerPage customerId="C-1" />);
    fireEvent.click(await screen.findByRole('tab', { name: /Contacts/ }));
    await pick('What Ravi Kumar usually gets', 'Invoices and payments');
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/customers/C-1/contacts/K-1', expect.objectContaining({ method: 'POST' })));
    const saves = () => fetch.mock.calls.filter((c) => c[0] === '/api/customers/C-1/contacts/K-1' && c[1]?.method === 'POST');
    expect(JSON.parse(String(saves()[0][1]!.body)).gets).toBe('billing');

    fireEvent.click(await screen.findByRole('button', { name: 'Edit Ravi Kumar' }));
    const form = screen.getByRole('form', { name: 'Edit Ravi Kumar' });
    fireEvent.change(within(form).getByLabelText('Role'), { target: { value: 'Accounts' } });
    fireEvent.click(within(form).getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(saves()).toHaveLength(2));
    expect(JSON.parse(String(saves()[1][1]!.body)).role).toBe('Accounts');

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    fireEvent.click(await screen.findByRole('button', { name: 'Remove Ravi Kumar' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/customers/C-1/contacts/K-1', expect.objectContaining({ method: 'DELETE' })));

    const add = screen.getByRole('form', { name: 'Add a contact' });
    fireEvent.change(within(add).getByLabelText('Name'), { target: { value: 'Meena' } });
    fireEvent.change(within(add).getByLabelText('Email'), { target: { value: 'meena@gearco.example' } });
    fireEvent.click(within(add).getByRole('button', { name: 'Add' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/customers/C-1/contacts', expect.objectContaining({ method: 'POST' })));
  });

  it('takes files for the customer, moves one into a project, gives a portal login and archives', async () => {
    serve();
    render(<CustomerPage customerId="C-1" />);
    fireEvent.click(await screen.findByRole('tab', { name: /Files/ }));
    const zone = screen.getByText(/here or/).closest('form')!;
    expect(zone).toHaveAttribute('data-dropzone');
    expect(zone.querySelector('input[name=customer_id]')).toHaveValue('C-1');
    fireEvent.click(screen.getByRole('button', { name: 'Drawing: change what arbor.pdf is' }));
    const move = screen.getByLabelText('In the project').closest('form')!;
    expect(move).toHaveAttribute('action', '/projects/files/A-1/link');
    expect(move.querySelector('input[name=project_id]')).toHaveValue('P-1');                 // the hidden input it posts
    expect(screen.getByRole('button', { name: 'Delete the file' }).closest('form')).toHaveAttribute('action', '/projects/files/A-1/delete');

    fireEvent.click(screen.getByRole('tab', { name: 'Overview' }));
    fireEvent.click(screen.getByRole('button', { name: 'Give them one' }));
    expect(screen.getByLabelText('Portal email').closest('form')).toHaveAttribute('action', '/customers/C-1/create-portal-account');
    expect(screen.getByRole('button', { name: 'Archive the customer' }).closest('form')).toHaveAttribute('action', '/customers/C-1/archive');
  });
});
