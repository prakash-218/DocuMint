import { render, screen, within } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { Documents } from './Documents';
import type { Doc } from './types';

function doc(id: string, over: Partial<Doc> = {}): Doc {
  return { invoice_id: id, doc_type: 'invoice', kind: 'Tax Invoice', number: id, status: 'pending', issue_date: '2026-10-20',
           currency: 'INR', total: 118000, paid: 0, balance: 59000, url: `/invoices/${id}`, pdf: '', versions: [], ...over };
}

const NOTE = doc('CN/001/26-27', { doc_type: 'credit_note', kind: 'Credit Note', status: 'issued', issue_date: '2026-10-28', total: 59000,
                                    balance: null, adjusts: -1, against: '040', url: '/credit-notes/N-1' });

describe("a project's credit and debit notes", () => {
  it('come after the invoice, with their sign and the invoice they are against', () => {
    render(<Documents docs={[doc('040'), NOTE]} newDocument={{}} canEdit={false} sales={false} onEmail={() => {}} />);
    const card = screen.getByRole('region', { name: 'Documents' });
    const items = within(card).getAllByRole('listitem').filter((li) => li.classList.contains('is-doc'));
    expect(items.map((li) => within(li).getByRole('link', { name: /040|CN\// }).textContent)).toEqual(['040', 'CN/001/26-27']);
    expect(items[1]).toHaveTextContent('−₹59,000');
    expect(items[1]).toHaveTextContent('issued 28 Oct · against 040');
    expect(within(items[1]).getByText('Issued')).toHaveClass('tone-done');
  });

  it("aren't shown to Sales", () => {
    render(<Documents docs={[doc('Q-1', { doc_type: 'quote', kind: 'Quotation', status: 'sent', balance: null }), NOTE]}
                      newDocument={{}} canEdit={false} sales onEmail={() => {}} />);
    expect(screen.queryByText('CN/001/26-27')).toBeNull();
  });
});
