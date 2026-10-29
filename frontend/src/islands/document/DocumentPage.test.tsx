import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import DocumentPage, { Pdf } from './DocumentPage';
import type { DocumentData } from './types';

const DOC: DocumentData = {
  invoice_id: 'D-7', project_id: 'P-7', number: 'TF/INV/007', doc_type: 'invoice', status: 'pending', currency: 'USD',
  list: { label: 'Invoices', url: '/invoices/' },
  head: { number: 'TF/INV/007', kind: 'Tax Invoice', pill: { text: 'Unpaid', tone: 'wait' },
          customer: { name: 'Hydro Parts Inc', url: '/customers/C-2' }, project: { label: 'PRJ-007', title: 'Clamp set', url: '/projects/P-7' } },
  next: { tone: 'action', text: '$300 due.', sub: 'Sent on 2 Oct.', actions: [{ kind: 'link', label: 'Record payment', href: '#payment', primary: true }] },
  money: [{ label: 'Invoice total', value: 300, cap: '' }, { label: 'Due', value: 300, cap: '', late: true }],
  pdf: { seal: true, links: [{ label: 'All copies', icon: 'file-down', href: '/invoices/D-7/pdf' },
                             { label: 'Original only', icon: 'file', href: '/invoices/D-7/pdf?copies=1' }],
         packing: '/invoices/D-7/packing', delete: null },
  change: { number: 'TF/INV/007', short: 'invoice', takes_payments: true, proforma: false, sent_word: 'finalized', undo: 'Finalize', again: 'finalize',
            correct: '/invoices/D-7/edit?correct=1', revise: null, reopen: { blocker: 'Payments are recorded on it.', action: '/invoices/D-7/reopen' } },
  payments: {
    title: 'Payments', empty: 'No payments recorded yet.', record_label: 'Record payment',
    rows: [{ id: 'PAY-1', date: '2026-10-20', amount: 100, label: 'Advance, against proforma TF/PI/004', method: 'SWIFT (foreign remittance)',
             reference: 'UTR9', credited: { amount: 8333, currency: 'INR', rate: '83.33' }, applied: null,
             take_off: { action: '/invoices/D-7/advances/PAY-1/remove', confirm: 'Take this advance off TF/INV/007? It goes back to TF/PI/004.' } }],
    record: { action: '/invoices/D-7/payment', advance: false, title: 'Record a payment', button: 'Record payment', suggested: 200,
              currency: 'USD', base_currency: 'INR', today: '2026-10-29', methods: ['Bank transfer', 'SWIFT (foreign remittance)'] },
    apply: { action: '/invoices/D-7/advances', note: "Received on Hydro Parts Inc's proformas and not on an invoice yet.", button: 'Apply to TF/INV/007',
             rows: [{ payment_id: 'PAY-2', amount: 50, number: 'TF/PI/005', date: '2026-10-01', reference: null, checked: true }] },
  },
  versions_html: null,
  document_html: '<article class="card invoice-doc"><h2 class="invoice-doc-title">TF/INV/007</h2><p>Clamp, 3 × $100</p></article>',
  chain: [{ kind: 'Proforma Invoice', number: 'TF/PI/004', pill: { text: 'Converted', tone: 'done' }, total: 100, currency: 'USD', url: '/proformas/D-4', here: false, paid: true },
          { kind: 'Tax Invoice', number: 'TF/INV/007', pill: { text: 'Unpaid', tone: 'wait' }, total: 300, currency: 'USD', url: '/invoices/D-7', here: true, paid: false }],
  people: { list: [{ name: 'Ravi Kumar', role: 'Accounts', email: 'ravi@hydro.example', initials: 'RK' }], url: '/projects/P-7', empty: '' },
  activity: [{ title: 'Payment of $100 recorded', body: null, when: '2026-10-20T10:00:00Z', who: 'meera', icon: 'indian-rupee', tone: 't-pay' }],
  convert: null,
  project: { project: { title: 'Clamp set', label: 'PRJ-007', fy: '26-27', reference: null, url: '/projects/P-7' },
             others: [{ number: 'TF/PI/004', url: '/proformas/D-4', kind: 'Proforma Invoice', versions: 0 }],
             change: { action: '/projects/for-document/D-7', options: '/projects/options?customer_id=C-2&exact=1' } },
  files: [],
  upload: { action: '/projects/files' },
};

function serve(doc: DocumentData = DOC) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const body = url.startsWith('/projects/options')
      ? { projects: [{ id: 'P-7', no: 'PRJ-007', title: 'Clamp set', fy: '26-27', status: 'open' },
                     { id: 'P-9', no: 'PRJ-009', title: 'Spare clamps', fy: '26-27', status: 'open' }] }
      : doc;
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe('DocumentPage', () => {
  it('shows where it is, its payments and the document the server drew', async () => {
    serve();
    render(<DocumentPage invoiceId="D-7" />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('TF/INV/007');
    expect(screen.getByText('$300 due.')).toBeInTheDocument();
    expect(document.querySelector('.invoice-doc')).toHaveTextContent('Clamp, 3 × $100');
    const payments = screen.getByRole('region', { name: 'Payments' });
    expect(within(payments).getByText(/Advance, against proforma TF\/PI\/004/)).toHaveTextContent('SWIFT (foreign remittance)');
    expect(within(payments).getByText(/Credited ₹/)).toHaveTextContent('Credited ₹8,333 @ 83.33');
    const chain = screen.getByRole('region', { name: 'Documents' });
    expect(within(chain).getByRole('link', { name: 'TF/PI/004' })).toHaveAttribute('href', '/proformas/D-4');
    expect(within(chain).queryByRole('link', { name: 'TF/INV/007' })).not.toBeInTheDocument();      // the one you're on
    expect(screen.getByText('Ravi Kumar')).toBeInTheDocument();
    expect(screen.getByText('Payment of $100 recorded')).toBeInTheDocument();
  });

  it('records a payment with the balance filled in, and says the rate the bank gave', async () => {
    serve();
    render(<DocumentPage invoiceId="D-7" />);
    const form = (await screen.findByRole('button', { name: 'Record payment', hidden: true })).closest('form')!;
    expect(form).toHaveAttribute('action', '/invoices/D-7/payment');
    expect(within(form).getByLabelText('Amount (USD)')).toHaveValue(200);
    await userEvent.type(within(form).getByLabelText(/Credited to your bank \(INR\)/), '16666');
    expect(within(form).getByText('Exchange rate: 1 USD = 83.33 INR')).toBeInTheDocument();
    const apply = screen.getByRole('button', { name: 'Apply to TF/INV/007' }).closest('form')!;
    expect(within(apply).getByRole('checkbox')).toBeChecked();
  });

  it('asks before taking an advance off, and sends nothing when told no', async () => {
    serve();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<DocumentPage invoiceId="D-7" />);
    const form = (await screen.findByRole('button', { name: 'Take off this invoice' })).closest('form')!;
    const sent = vi.fn((e: Event) => e.preventDefault());
    form.addEventListener('submit', sent);
    await userEvent.click(within(form).getByRole('button'));
    expect(confirm).toHaveBeenCalledWith('Take this advance off TF/INV/007? It goes back to TF/PI/004.');
    expect(sent.mock.calls[0][0].defaultPrevented).toBe(true);
    confirm.mockRestore();
  });

  it('prints without the seal once that is unticked, and remembers it', async () => {
    render(<Pdf pdf={DOC.pdf} />);                     // in the app's header; on its own here
    const hrefs = () => screen.getAllByRole('link', { hidden: true }).map((a) => a.getAttribute('href'));
    expect(hrefs()).toEqual(['/invoices/D-7/pdf', '/invoices/D-7/pdf?copies=1', '/invoices/D-7/packing']);
    await userEvent.click(screen.getByRole('checkbox', { name: 'Print with seal', hidden: true }));
    expect(hrefs()).toEqual(['/invoices/D-7/pdf?seal=0', '/invoices/D-7/pdf?copies=1&seal=0', '/invoices/D-7/packing']);
    expect(window.localStorage.getItem('documint.pdfSeal')).toBe('off');
  });

  it('moves the document to another of the customer\'s projects', async () => {
    serve();
    render(<DocumentPage invoiceId="D-7" />);
    await userEvent.click(await screen.findByText('Move to another project'));
    const select = await screen.findByLabelText('Move it to');
    expect(within(select).getAllByRole('option').map((o) => o.textContent)).toEqual(['Choose a project', 'PRJ-009 · Spare clamps · FY 26-27']);
    expect(select.closest('form')).toHaveAttribute('action', '/projects/for-document/D-7');
    expect(screen.getByRole('button', { name: 'Remove from the project' })).toHaveAttribute('value', '');
  });

  it('offers to change a sent document, and says why it can\'t go back to draft', async () => {
    serve();
    render(<DocumentPage invoiceId="D-7" />);
    const dialog = (await screen.findByText('Correct this invoice')).closest('dialog')!;
    expect(dialog).toHaveAttribute('id', 'change-dialog');
    expect(within(dialog).getByRole('link', { name: 'Correct it', hidden: true })).toHaveAttribute('href', '/invoices/D-7/edit?correct=1');
    expect(within(dialog).getByText(/Not possible: payments are recorded on it/)).toBeInTheDocument();
    expect(within(dialog).queryByText('Make a revision')).not.toBeInTheDocument();
  });
});
