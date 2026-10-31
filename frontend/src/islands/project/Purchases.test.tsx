import { render, screen, within } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { Purchases } from './Purchases';
import type { Doc } from './types';

function po(id: string, over: Partial<Doc> = {}): Doc {
  return { invoice_id: id, doc_type: 'purchase_order', kind: 'Purchase Order', number: id, status: 'sent', issue_date: '2026-10-31',
           currency: 'INR', total: 100000, paid: 0, balance: null, url: `/purchase-orders/${id}`, pdf: '', versions: [],
           party: 'Clamp Works', ...over };
}

describe("a project's purchases", () => {
  it('lists its purchase orders, what was ordered and what is still to arrive', () => {
    render(<Purchases docs={[po('017'), po('018', { status: 'received', total: 40000 }), po('019', { status: 'cancelled', total: 5000 })]}
                      newUrl="/purchase-orders/create?doc_type=purchase_order&project_id=P-1" />);
    const card = screen.getByRole('region', { name: 'Purchases' });
    expect(card).toHaveTextContent('₹1,40,000 ordered · ₹1,00,000 still to arrive');     // the cancelled one isn't counted
    expect(within(card).getByRole('link', { name: '017' })).toHaveAttribute('href', '/purchase-orders/017');
    expect(within(card).getByText('Received')).toHaveClass('tone-done');
    expect(within(card).getByRole('link', { name: 'New purchase order' })).toHaveAttribute('href', expect.stringContaining('project_id=P-1'));
  });

  it('says what a purchase order is when there are none', () => {
    render(<Purchases docs={[]} newUrl="/purchase-orders/create" />);
    expect(screen.getByText(/Nothing bought for it yet/)).toBeInTheDocument();
  });
});
