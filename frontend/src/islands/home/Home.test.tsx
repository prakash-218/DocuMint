import { render, screen, within } from '../../test/render';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Home, { totals, type HomeData } from './Home';

const DATA: HomeData = {
  hello: { name: 'Ravi', today: '2026-10-28', fy: '26-27', greeting: 'Good morning' },
  open_quotes: { count: 3, total: { INR: 1454940 } },
  attention: [
    { key: 'follow_up', title: 'Quotations with no answer for over two weeks', label: '2 quotations with no answer after 14 days',
      names: 'Hob arbor set · Programming charges', count: 2, total: { INR: 595600, USD: 1200 },
      items: [{ title: 'Hob arbor set', sub: 'Hosur plant · PRJ-041 · Waiting · 19 days', amount: 495600, currency: 'INR',
                url: '/projects/P-41/new', action: 'Send a follow-up' }], more: 1 },
    { key: 'paid_open', title: 'Paid in full, still open', label: '1 project paid in full, still open', names: 'Old fixture', count: 1, total: { INR: 90000 },
      items: [{ title: 'Old fixture', sub: 'Axle Works · PRJ-002', amount: 90000, currency: 'INR', url: '/projects/P-2/new',
                action: 'Mark the project completed' }], more: 0 },
  ],
  unfiled_emails: { count: 4, url: '/emails/' },
  to_receive: {
    total: { INR: 2200000 }, count: 3, aged_by: 'date', overdue: { count: 0, total: {} },
    ages: [{ label: '0–30 days', count: 1, total: { INR: 1000000 } }, { label: '31–60 days', count: 0, total: {} },
           { label: '61–90 days', count: 2, total: { INR: 1200000 } }, { label: 'Over 90 days', count: 0, total: {} }],
    customers: [{ id: 'C-1', name: 'Gear Cutters Ltd · Hosur plant', count: 2, total: { INR: 2000000 } }],
    advances: { count: 1, total: { INR: 198240 } },
  },
  month: { label: 'October', invoiced: { INR: 477994 }, received: {} },
  recent: [{ id: 'E-1', kind: 'payment', title: 'Payment of ₹1,50,000.00 on 058', when: '2026-10-20T10:00:00', link: '/invoices/I-58',
             who: 'ravi', project: 'Hob arbor set', project_url: '/projects/P-41/new' }],
  links: { projects: '/projects/board' },
};

function serve(data: HomeData | null = DATA, status = 200) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(data ?? { error: 'Your role is Sales: projects, quotations and customers only' }),
                                                          { status, headers: { 'Content-Type': 'application/json' } })));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Home', () => {
  it('greets, and lists what needs doing one row a kind, each opening to its projects', async () => {
    serve();
    render(<Home />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(/^Good (morning|afternoon|evening), Ravi$/);
    expect(screen.getByText('Over 90 days old').closest('.stat')).not.toHaveClass('late');        // nothing that old
    const followUps = screen.getByText('2 quotations with no answer after 14 days').closest('details')!;
    expect(followUps).not.toHaveAttribute('open');
    expect(within(followUps).getByText('Hob arbor set · Programming charges')).toBeInTheDocument();
    expect(within(followUps).getByText('₹5,95,600 + $1,200')).toBeInTheDocument();
    expect(followUps.querySelector('.ai')).toHaveClass('tone-action');
    const link = within(followUps).getByRole('link', { name: /Hob arbor set/ });
    expect(link).toHaveAttribute('href', '/projects/P-41/new');
    expect(link).toHaveTextContent('Send a follow-up →');
    expect(within(followUps).getByRole('link', { name: 'and 1 more on the projects list' })).toHaveAttribute('href', '/projects/board');
    expect(screen.getByRole('link', { name: /4 emails not filed to a project/ })).toHaveAttribute('href', '/emails/');
  });

  it('shows the money to come in, by how old the invoices are', async () => {
    serve();
    render(<Home />);
    const receive = (await screen.findByRole('heading', { name: 'To receive' })).closest('section')!;
    expect(within(receive).getAllByText('₹22,00,000')[0]).toBeInTheDocument();
    const ages = within(receive).getByRole('list', { name: 'By how long ago each invoice was sent' });
    expect(within(ages).getAllByRole('listitem').map((li) => li.textContent)).toEqual(
      ['0–30 days₹10,00,0001 invoice', '31–60 days—0 invoices', '61–90 days₹12,00,0002 invoices', 'Over 90 days—0 invoices']);
    expect(receive.querySelectorAll('.agebar span')).toHaveLength(2);                                 // a coloured part for each age with money
    expect(within(receive).getByText(/Advances requested on proformas:/)).toHaveTextContent('₹1,98,240 (1 project). They count once paid.');
    expect(within(receive).getByText('Gear Cutters Ltd · Hosur plant')).toBeInTheDocument();
  });

  it('with payment terms: what is overdue first, and the money by how late it is', async () => {
    const overdue = {
      key: 'overdue', title: 'Invoices past their due date', label: '1 invoice past its due date', names: 'Tax Invoice 058', count: 1,
      total: { INR: 60000 }, more: 2, more_url: '/invoices/?status=overdue', more_label: 'on the invoices list',
      items: [{ title: 'Tax Invoice 058', sub: 'Hosur plant · 12 days late', amount: 60000, currency: 'INR', url: '/invoices/I-58', action: 'Send a reminder' }],
    };
    serve({
      ...DATA, attention: [overdue, ...DATA.attention],
      to_receive: { ...DATA.to_receive, aged_by: 'due', overdue: { count: 3, total: { INR: 1200000 } },
                    ages: [{ label: 'Not due yet', count: 1, total: { INR: 1000000 } }, { label: '1–30 days late', count: 3, total: { INR: 1200000 } },
                           { label: '31–60 days late', count: 0, total: {} }, { label: 'Over 60 days late', count: 0, total: {} }] },
    });
    render(<Home />);
    const late = (await screen.findByText('1 invoice past its due date')).closest('details')!;
    expect(late.querySelector('.ai')).toHaveClass('tone-late');
    expect(within(late).getByRole('link', { name: /Tax Invoice 058/ })).toHaveTextContent('Send a reminder →');
    expect(within(late).getByRole('link', { name: 'and 2 more on the invoices list' })).toHaveAttribute('href', '/invoices/?status=overdue');
    expect(screen.getByText('Overdue').closest('.stat')).toHaveClass('late');
    expect(screen.getByText('Overdue').closest('.stat')).toHaveTextContent('₹12,00,000');
    expect(screen.queryByText('Over 90 days old')).toBeNull();
    expect(screen.getByRole('list', { name: 'By how late each invoice is' })).toHaveTextContent('1–30 days late₹12,00,0003 invoices');
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
