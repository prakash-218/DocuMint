import { render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Home, { totals, type HomeData } from './Home';

const DATA: HomeData = {
  attention: [
    { key: 'follow_up', title: 'Quotations with no answer for over two weeks', count: 2, total: { INR: 595600, USD: 1200 },
      items: [{ title: 'Hob arbor set', sub: 'Hosur plant · PRJ-041 · Waiting · 19 days', amount: 495600, currency: 'INR',
                url: '/projects/P-41/new', action: 'Send a follow-up' }], more: 1 },
    { key: 'paid_open', title: 'Paid in full, still open', count: 1, total: { INR: 90000 },
      items: [{ title: 'Old fixture', sub: 'Axle Works · PRJ-002', amount: 90000, currency: 'INR', url: '/projects/P-2/new',
                action: 'Mark the project completed' }], more: 0 },
  ],
  unfiled_emails: { count: 4, url: '/emails/' },
  to_receive: {
    total: { INR: 2200000 }, count: 3,
    ages: [{ label: '0–30 days', count: 1, total: { INR: 1000000 } }, { label: '31–60 days', count: 0, total: {} },
           { label: '61–90 days', count: 2, total: { INR: 1200000 } }, { label: 'Over 90 days', count: 0, total: {} }],
    customers: [{ id: 'C-1', name: 'Gear Cutters Ltd · Hosur plant', count: 2, total: { INR: 2000000 } }],
    advances: { count: 1, total: { INR: 198240 } },
  },
  month: { label: 'October', invoiced: { INR: 477994 }, received: {} },
  recent: [{ id: 'E-1', kind: 'payment', title: 'Payment of ₹1,50,000.00 on 058', when: '2026-10-20T10:00:00', link: '/invoices/I-58',
             who: 'ravi', project: 'Hob arbor set', project_url: '/projects/P-41/new' }],
  links: { projects: '/projects/board', classic: '/dashboard/' },
};

function serve(data: HomeData | null = DATA, status = 200) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(data ?? { error: 'Your role is Sales: projects, quotations and customers only' }),
                                                          { status, headers: { 'Content-Type': 'application/json' } })));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Home', () => {
  it('lists what needs doing under each heading, with the way to do it', async () => {
    serve();
    render(<Home />);
    const followUps = (await screen.findByText('Quotations with no answer for over two weeks')).closest('details')!;
    expect(followUps).toHaveAttribute('open');
    expect(within(followUps).getByText('₹5,95,600 + $1,200')).toBeInTheDocument();
    const link = within(followUps).getByRole('link', { name: /Hob arbor set/ });
    expect(link).toHaveAttribute('href', '/projects/P-41/new');
    expect(link).toHaveTextContent('Send a follow-up →');
    expect(within(followUps).getByRole('link', { name: 'and 1 more on the projects board' })).toHaveAttribute('href', '/projects/board');
    expect(screen.getByText('Paid in full, still open').closest('details')).not.toHaveAttribute('open');   // folded: least urgent
    expect(screen.getByRole('link', { name: /Emails not filed to a project\s*4/ })).toHaveAttribute('href', '/emails/');
  });

  it('shows the money to come in, by how old the invoices are', async () => {
    serve();
    render(<Home />);
    const receive = (await screen.findByRole('heading', { name: 'To receive' })).closest('section')!;
    expect(within(receive).getByText('₹22,00,000')).toBeInTheDocument();
    expect(within(receive).getAllByRole('listitem').slice(0, 4).map((li) => li.textContent)).toEqual(
      ['0–30 days₹10,00,0001', '31–60 days—', '61–90 days₹12,00,0002', 'Over 90 days—']);
    expect(within(receive).getByText(/Plus ₹1,98,240 in advances asked for on 1 project\./)).toBeInTheDocument();
    expect(within(receive).getByText('Gear Cutters Ltd · Hosur plant')).toBeInTheDocument();
    const month = screen.getByRole('heading', { name: 'October' }).closest('section')!;
    expect(within(month).getByText('₹4,77,994')).toBeInTheDocument();
    expect(within(month).getByText('₹0')).toBeInTheDocument();
  });

  it("says why when it can't load", async () => {
    serve(null, 403);
    render(<Home />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Your role is Sales');
  });

  it('adds totals in each currency, biggest first', () => {
    expect(totals({ USD: 500, INR: 100000 })).toBe('₹1,00,000 + $500');
    expect(totals({})).toBe('₹0');
  });
});
