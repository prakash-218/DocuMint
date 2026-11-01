import { render, screen, within } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { NotesCard, RefundsCard, type Refunds } from './Notes';

const REFUNDS: Refunds = {
  rows: [{ id: 'R-1', date: '2026-11-02', amount: 5000, reference: 'UTR 4411', by: 'owner@example.com',
           delete: '/credit-notes/CN-1/refunds/R-1/delete' }],
  owed: 6800, against: 'INV-040', currency: 'INR',
  record: { action: '/credit-notes/CN-1/refunds', today: '2026-11-05', suggested: 6800 },
};

const fields = () => Object.fromEntries(new FormData(document.querySelector('#refunds form:not([style])') as HTMLFormElement));

describe("an invoice's notes", () => {
  it('lists each note, its state, and its amount, a credit note taken off', () => {
    render(<NotesCard currency="INR" notes={[
      { id: 'CN-1', number: 'CN/001/26-27', kind: 'Credit Note', date: '2026-11-01', pill: { text: 'Issued', tone: 'done' },
        reason: 'Goods returned', amount: -11800, url: '/credit-notes/CN-1' },
      { id: 'DN-1', number: 'DN/001/26-27', kind: 'Debit Note', date: '2026-11-03', pill: { text: 'Draft', tone: 'draft' },
        reason: '', amount: 2360, url: '/debit-notes/DN-1' }]} />);
    const list = screen.getByRole('list', { name: 'Notes' });
    const credit = within(list).getByRole('link', { name: 'CN/001/26-27' }).closest('li')!;
    expect(credit).toHaveTextContent('Issued');
    expect(credit).toHaveTextContent('Credit Note · 1 Nov · Goods returned');
    expect(credit).toHaveTextContent('−₹11,800');
    expect(within(list).getByRole('link', { name: 'DN/001/26-27' }).closest('li')).toHaveTextContent('₹2,360');
  });
});

describe("a credit note's refunds", () => {
  it('shows what was paid back and what is still to refund, the next one starting at that', () => {
    render(<RefundsCard refunds={REFUNDS} />);
    const card = screen.getByRole('region', { name: 'Refunds' });
    expect(card).toHaveTextContent('₹6,800 to refund on INV-040');
    expect(within(card).getByRole('list', { name: 'Refunded' })).toHaveTextContent('2 Nov · UTR 4411 · owner@example.com');
    expect(fields()).toEqual({ amount: '6800.00', refunded_on: '2026-11-05', reference: '' });
    expect(screen.getByLabelText('Amount (INR)')).toHaveAttribute('max', '6800');
  });

  it('offers no form once nothing is owed back', () => {
    render(<RefundsCard refunds={{ ...REFUNDS, owed: 0, record: null }} />);
    expect(screen.getByText('Nothing to refund')).toBeInTheDocument();
    expect(screen.queryByText('Record a refund')).toBeNull();
  });
});
