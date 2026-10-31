import { render, screen, within } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { ReceivingCard, type Receiving } from './Receiving';

const PART: Receiving = {
  lines: [{ line: 1, description: 'Hydraulic jack, 5 ton', qty: 4, unit: 'nos', received: 3, left: 1 },
          { line: 2, description: 'Base plate', qty: 2, unit: '', received: 2, left: 0 }],
  state: 'part',
  deliveries: [{ id: 'R-1', date: '2026-11-02', challan: 'DC-31', note: 'One short', by: 'owner@example.com',
                 lines: [{ description: 'Hydraulic jack, 5 ton', qty: 3, unit: 'nos' }, { description: 'Base plate', qty: 2, unit: '' }],
                 delete: '/purchase-orders/PO-1/receipts/R-1/delete' }],
  record: { action: '/purchase-orders/PO-1/receipts', today: '2026-11-05' },
};

const fields = () => Object.fromEntries(new FormData(document.querySelector('form.recv-form') as HTMLFormElement));

describe('what arrived on a purchase order', () => {
  it('shows each line ordered, arrived and still to come, and each delivery', () => {
    render(<ReceivingCard receiving={PART} />);
    const card = screen.getByRole('region', { name: 'What arrived' });
    expect(card).toHaveTextContent('1 of 2 lines in full');
    const jack = within(card.querySelector('table.recv-table') as HTMLElement).getByText('1. Hydraulic jack, 5 ton').closest('tr')!;
    expect(jack).toHaveTextContent('4 nos3 nos1 nos');
    expect(within(card).getByRole('list', { name: 'Deliveries' })).toHaveTextContent('Challan DC-31');
  });

  it('records the next delivery, each line starting at what is still to come', () => {
    render(<ReceivingCard receiving={PART} />);
    expect(fields()).toEqual({ received_on: '2026-11-05', challan_no: '', qty_1: '1', note: '' });     // only what's still to come
    expect(screen.getByLabelText('1. Hydraulic jack, 5 ton')).toHaveAttribute('max', '1');
  });

  it('offers no form once everything has arrived', () => {
    render(<ReceivingCard receiving={{ ...PART, state: 'all', record: null }} />);
    expect(screen.getByText('Everything has arrived')).toBeInTheDocument();
    expect(document.querySelector('form.recv-form')).toBeNull();
  });
});
