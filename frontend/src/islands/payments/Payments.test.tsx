import { pick, render, screen, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Payments, { matches, type PaymentList, type PaymentRow } from './Payments';

function row(id: string, over: Partial<PaymentRow> = {}): PaymentRow {
  return {
    id, date: '2026-10-28', amount: 40000, currency: 'INR', credited: null, method: 'NEFT / RTGS', reference: `UTR 6302 ${id}`,
    tab: 'invoice', note: '', document: { number: `TF/INV/0${id}/26-27`, kind: 'Tax Invoice', url: `/invoices/D-${id}` },
    customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: 'Hosur plant' },
    project: { label: `PRJ-0${id}`, title: 'Hob arbor set', url: `/projects/P-${id}` }, ...over,
  };
}

const DATA: PaymentList = {
  title: 'Payments',
  tabs: [{ key: 'all', label: 'All' }, { key: 'advance', label: 'Advances' }, { key: 'invoice', label: 'Against invoices' }],
  export: '/payments/export.csv',
  rows: [
    row('58'),
    row('12', { tab: 'advance', note: 'Advance on TF/PI/012/26-27', amount: 20000, method: 'UPI', reference: '',
                document: { number: 'TF/INV/057/26-27', kind: 'Tax Invoice', url: '/invoices/D-57' } }),
    row('03', { currency: 'USD', amount: 1200, credited: { amount: 99840, currency: 'INR' }, date: '2026-03-15',
                customer: { id: 'C-2', name: 'Hydro Parts Inc', site: null }, project: null }),
  ],
};

function serve(data: PaymentList) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })));
}

const shown = () => [...document.querySelectorAll('.rr')].map((r) => r.children[2].querySelector('.mono')?.textContent);

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState(null, '', '/');
});

describe('Payments', () => {
  it('lists every payment with its document, how it came, and how much each tab adds up to', async () => {
    serve(DATA);
    render(<Payments />);
    expect(await screen.findByRole('tab', { name: /^All\s*3/ })).toHaveTextContent('₹60,000 + $1,200');
    expect(screen.getByRole('tab', { name: /^Advances\s*1/ })).toHaveTextContent('₹20,000');
    const advance = screen.getByText('Advance on TF/PI/012/26-27').closest('a')!;
    expect(advance).toHaveAttribute('href', '/invoices/D-57');
    expect(within(advance).getByText('UPI')).toBeInTheDocument();
    const foreign = screen.getByText('Hydro Parts Inc', { selector: '.c-title' }).closest('a')!;
    expect(within(foreign).getByText('₹99,840 credited')).toBeInTheDocument();
    expect(within(foreign).getByText('15 Mar 2026')).toBeInTheDocument();
    expect(within(screen.getByText('TF/INV/058/26-27').closest('a')!).getByText('UTR 6302 58')).toBeInTheDocument();
  });

  it('finds a payment by its bank reference, and keeps the tab, search and year in the address', async () => {
    serve(DATA);
    render(<Payments tab="invoice" />);
    expect(await screen.findByRole('tab', { name: /^Against invoices/ })).toHaveAttribute('aria-selected', 'true');
    await userEvent.type(screen.getByLabelText('Search payments'), '6302 58');
    expect(shown()).toEqual(['TF/INV/058/26-27']);
    await pick(screen.getByLabelText('Financial year'), 'FY 25-26');
    expect(screen.getByText(/Nothing matches/)).toBeInTheDocument();
    expect(window.location.search).toBe('?tab=invoice&q=6302+58&fy=25-26');
  });

  it('says how to get a first one', async () => {
    serve({ ...DATA, rows: [] });
    render(<Payments />);
    expect(await screen.findByText(/No payments yet/)).toBeInTheDocument();
  });

  it('matches every word typed', () => {
    expect(matches(DATA.rows[0], 'gear hob')).toBe(true);
    expect(matches(DATA.rows[1], 'upi pi/012')).toBe(true);
    expect(matches(DATA.rows[2], 'hydro hob')).toBe(false);
  });
});
