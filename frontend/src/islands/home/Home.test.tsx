import userEvent from '@testing-library/user-event';
import { fireEvent, render, screen, within } from '../../test/render';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Home, { totals, type HomeData } from './Home';

const DATA: HomeData = {
  hello: { name: 'Ravi', today: '2026-10-28', fy: '26-27', greeting: 'Good morning' },
  work: {
    bar: [
      { key: 'answer', label: 'Quotes awaiting an answer', total: { INR: 1454940 }, count: 3, columns: ['accepted'] },
      { key: 'bill', label: 'Accepted, to bill', total: {}, count: 0, columns: ['advance', 'invoiced'] },
      { key: 'advance', label: 'Advances asked', total: { INR: 198240 }, count: 1, columns: ['advance'] },
      { key: 'unpaid', label: 'Unpaid invoices', total: { INR: 2200000 }, count: 3, columns: ['paid'], late: { INR: 60000 } },
      { key: 'received', label: 'Received in October', total: {}, count: null, columns: [], url: '/payments/' },
    ],
    columns: [
      { key: 'quoted', label: 'Quoting', count: 1, total: { INR: 90000 }, cards: [
        { id: 'P-44', label: 'PRJ-044', title: 'Locating pins', url: '/projects/P-44', customer: { name: 'Axle Works', site: null },
          tone: 'action', next: 'Quotation Q/044 is a draft.', action: 'Edit quotation',
          move: { kind: 'link', label: 'Edit quotation', href: '/invoices/Q-44/edit', primary: true }, days: 2, late: null, amount: 90000, currency: 'INR' }] },
      { key: 'accepted', label: 'Waiting for an answer', count: 1, total: { INR: 495600 }, cards: [
        { id: 'P-41', label: 'PRJ-041', title: 'Hob arbor set', url: '/projects/P-41', customer: { name: 'Gear Cutters Ltd', site: 'Hosur plant' },
          tone: 'action', next: 'Quotation Q/041 sent on 9 Oct.', action: 'Send a follow-up',
          move: { kind: 'post', label: 'Mark accepted', action: '/invoices/Q-41/status', fields: { status: 'accepted' }, primary: false, confirm: null },
          days: 19, late: null, amount: 495600, currency: 'INR' }] },
      { key: 'advance', label: 'Advance', count: 0, total: {}, cards: [] },
      { key: 'invoiced', label: 'To invoice', count: 0, total: {}, cards: [] },
      { key: 'paid', label: 'Waiting for payment', count: 1, total: { INR: 60000 }, cards: [
        { id: 'P-30', label: 'PRJ-030', title: 'Drill jig', url: '/projects/P-30', customer: { name: 'Axle Works', site: null },
          tone: 'wait', next: 'Tax invoice 058: ₹60,000 due.', action: 'Record payment',
          move: { kind: 'link', label: 'Record payment', href: '/invoices/I-58#payment', primary: true }, days: 40, late: 12, amount: 60000, currency: 'INR' }] },
    ],
  },
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
    expect(within(receive).getByText(/Advances requested on proformas:/)).toHaveTextContent('₹1,98,240 (1 project).');
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
    expect(screen.getByRole('list', { name: 'By how late each invoice is' })).toHaveTextContent('1–30 days late₹12,00,0003 invoices');
  });

  it('shows the money bar over the pipeline, each tile picking out its columns', async () => {
    serve();
    render(<Home />);
    const bar = await screen.findByRole('group', { name: 'Money' });
    expect(within(bar).getByRole('button', { name: /Quotes awaiting an answer/ })).toHaveTextContent('₹14,54,9403 jobs');
    expect(within(bar).getByRole('button', { name: /Unpaid invoices/ })).toHaveTextContent('₹22,00,000₹60,000 late');
    expect(within(bar).getByRole('button', { name: /Advances asked/ })).toHaveTextContent('₹1,98,2401 job');
    expect(within(bar).getByRole('link', { name: /Received in October/ })).toHaveAttribute('href', '/payments/');
    const col = (name: string) => screen.getByRole('heading', { name: new RegExp(`^${name}`) }).closest('section')!;
    expect(col('Waiting for an answer')).toHaveTextContent('Waiting for an answer1₹4,95,600');

    const tile = within(bar).getByRole('button', { name: /Quotes awaiting an answer/ });
    await userEvent.click(tile);
    expect(tile).toHaveAttribute('aria-pressed', 'true');
    expect(col('Waiting for an answer')).not.toHaveClass('dim');
    expect(col('Quoting')).toHaveClass('dim');
    await userEvent.click(tile);
    expect(col('Quoting')).not.toHaveClass('dim');
  });

  it('shows each job with how long it has sat there, and how late its invoice is', async () => {
    serve();
    render(<Home />);
    const waiting = await screen.findByRole('article', { name: 'Hob arbor set, Hosur plant' });
    expect(within(waiting).getByText('19 days here')).toHaveClass('tone-late');
    expect(within(waiting).getByRole('link', { name: 'Hob arbor set' })).toHaveAttribute('href', '/projects/P-41');
    expect(within(screen.getByRole('article', { name: 'Locating pins, Axle Works' })).getByText('2 days')).toHaveClass('tone-done');
    const paying = screen.getByRole('article', { name: 'Drill jig, Axle Works' });
    expect(within(paying).getByText('12 days late')).toHaveClass('tone-late');
    expect(within(paying).queryByRole('button')).toBeNull();                 // nothing after the last column
    expect(paying).toHaveTextContent('Next: Record payment');
  });

  it('offers the step that moves a job on when it is dropped on the next column, and its project anywhere else', async () => {
    serve();
    render(<Home />);
    const card = await screen.findByRole('article', { name: 'Hob arbor set, Hosur plant' });
    const col = (name: string) => screen.getByRole('heading', { name: new RegExp(`^${name}`) }).closest('section')!;
    const drag = (to: HTMLElement) => {
      const dataTransfer = { effectAllowed: '', setData: () => undefined };
      fireEvent.dragStart(card, { dataTransfer });
      fireEvent.dragOver(to, { dataTransfer });
      fireEvent.drop(to, { dataTransfer });
    };

    drag(col('Advance'));
    let dialog = screen.getByRole('dialog');
    expect(within(dialog).getByRole('heading', { name: 'Mark accepted' })).toBeInTheDocument();
    const form = within(dialog).getByRole('button', { name: 'Mark accepted' }).closest('form')!;
    expect(form).toHaveAttribute('action', '/invoices/Q-41/status');
    expect(form.querySelector('input[name="status"]')).toHaveValue('accepted');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('dialog')).toBeNull();

    drag(col('Waiting for payment'));
    dialog = screen.getByRole('dialog');
    expect(within(dialog).getByRole('link', { name: 'Open the project' })).toHaveAttribute('href', '/projects/P-41');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Close' }));

    card.focus();
    await userEvent.keyboard('{ArrowRight}');
    expect(within(screen.getByRole('dialog')).getByRole('button', { name: 'Mark accepted' })).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancel' }));

    await userEvent.click(within(card).getByRole('button', { name: 'Next: Mark accepted' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('PRJ-041 · Hosur plant · ₹4,95,600');
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
