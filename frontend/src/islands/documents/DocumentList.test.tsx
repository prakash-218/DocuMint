import { pick, render, screen, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import DocumentList, { fiscalYear, matches, type DocList, type DocRow } from './DocumentList';

function row(id: string, number: string, over: Partial<DocRow> = {}): DocRow {
  return {
    id, number, kind: 'Tax Invoice', subject: '', project: { label: `PRJ-0${id}`, title: 'Hob arbor set', url: `/projects/P-${id}` },
    customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: 'Hosur plant' }, date: '2026-10-14', until: null, tab: 'pending',
    tag: { text: 'Unpaid', tone: 'wait' }, note: '', currency: 'INR', total: 100000, balance: 100000,
    url: `/invoices/D-${id}`, pdf: `/invoices/D-${id}/pdf`, versions: [], search: [], ...over,
  };
}

const INVOICES: DocList = {
  group: 'invoices', title: 'Invoices', until: 'Due',
  tabs: [{ key: 'all', label: 'All' }, { key: 'draft', label: 'Draft' }, { key: 'pending', label: 'Unpaid' },
         { key: 'overdue', label: 'Overdue' }, { key: 'paid', label: 'Paid' }],
  rows: [
    row('58', '058', { until: '2026-10-08', tab: 'overdue', tag: { text: 'Overdue', tone: 'late' }, note: '12 days late', balance: 60000 }),
    row('57', '057', { until: '2026-11-13', note: 'Due in 24 days', search: ['PO 4500 0188'] }),
    row('56', '056', { tab: 'paid', tag: { text: 'Paid', tone: 'done' }, balance: null, date: '2026-03-30',
                       customer: { id: 'C-2', name: 'Axle Works', site: null } }),
  ],
  new_url: '/invoices/create?doc_type=invoice', new_label: 'New invoice',
};

function serve(data: DocList) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })));
}

const numbers = () => [...document.querySelectorAll('.rr .c-title')].map((t) => t.textContent);

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState(null, '', '/');
});

describe('DocumentList', () => {
  it('tabs say how many and how much: what is still due for unpaid and overdue ones', async () => {
    serve(INVOICES);
    render(<DocumentList group="invoices" />);
    expect(await screen.findByRole('tab', { name: /^All\s*3/ })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /^All/ })).toHaveTextContent('₹3,00,000');
    expect(screen.getByRole('tab', { name: /^Unpaid\s*1/ })).toHaveTextContent('₹1,00,000');
    expect(screen.getByRole('tab', { name: /^Overdue\s*1/ })).toHaveTextContent('₹60,000');       // the balance, not the total
    const late = screen.getByText('058').closest('a')!;
    expect(late).toHaveAttribute('href', '/invoices/D-58');
    expect(within(late).getByText('Overdue')).toHaveClass('tag', 'tone-late');
    expect(within(late).getByText('12 days late')).toHaveClass('late');
    expect(late.querySelector('.c-main .c-sub')).toHaveTextContent('Hob arbor set · PRJ-058');      // no subject: the project's name
    expect(screen.getByRole('link', { name: /New invoice/ })).toHaveAttribute('href', '/invoices/create?doc_type=invoice');
  });

  it('opens the tab a link asks for, and keeps the tab and search in the address', async () => {
    serve(INVOICES);
    render(<DocumentList group="invoices" tab="overdue" />);
    expect(await screen.findByRole('tab', { name: /^Overdue/ })).toHaveAttribute('aria-selected', 'true');
    expect(numbers()).toEqual(['058']);
    await userEvent.click(screen.getByRole('tab', { name: /^All/ }));
    await userEvent.type(screen.getByLabelText('Search invoices'), '4500 0188');
    expect(numbers()).toEqual(['057']);                                                               // found by its PO
    expect(window.location.search).toBe('?q=4500+0188');
  });

  it('filters by customer and financial year, and has no due column when nothing has a date', async () => {
    serve({ ...INVOICES, rows: INVOICES.rows.map((r) => ({ ...r, until: null })) });
    render(<DocumentList group="invoices" />);
    await screen.findByRole('tab', { name: /^All/ });
    expect(screen.queryByText('Due', { selector: '.rh span' })).toBeNull();
    await pick(screen.getByLabelText('Financial year'), 'FY 25-26');
    expect(numbers()).toEqual(['056']);
    await pick(screen.getByLabelText('Financial year'), 'All years');
    await pick(screen.getByLabelText('Customer'), /Gear Cutters/);
    expect(numbers()).toEqual(['058', '057']);
  });

  it('says so when nothing matches', async () => {
    serve(INVOICES);
    render(<DocumentList group="invoices" query="nothing like this" />);
    expect(await screen.findByText(/Nothing matches/)).toBeInTheDocument();
  });
});

describe('matching and years', () => {
  it('finds a document by any word of its number, subject, customer, project or earlier numbers', () => {
    const r = row('41', 'TF/Q/041R1/26-27', { subject: 'Spline gauges', search: ['TF/Q/041/26-27'] });
    expect(matches(r, 'spline hosur')).toBe(true);
    expect(matches(r, 'tf/q/041/26-27')).toBe(true);
    expect(matches(r, 'prj-041')).toBe(true);
    expect(matches(r, 'axle')).toBe(false);
  });

  it('puts April to March in one financial year', () => {
    expect(fiscalYear('2026-04-01')).toBe('26-27');
    expect(fiscalYear('2027-03-31')).toBe('26-27');
    expect(fiscalYear('2026-03-31')).toBe('25-26');
    expect(fiscalYear('2099-12-01')).toBe('99-00');
    expect(fiscalYear(null)).toBe('');
  });
});
