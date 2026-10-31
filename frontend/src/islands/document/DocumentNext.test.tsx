import { fireEvent, render, screen } from '../../test/render';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import type { Compose } from '../EmailComposer';
import DocumentNext from './DocumentNext';

const COMPOSE: Compose = {
  from: 'desk@ourworks.example', from_name: 'Our Works', can_send: true, why_not: null,
  people: [{ name: 'Ravi Kumar', email: 'ravi@gearco.example', role: 'Purchase', gets: 'all' }], found: [],
  to: ['ravi@gearco.example'], cc: [], threads: [], thread_id: null,
  subject: 'Quotation Q/041 · Spline gauges', new_subject: 'Quotation Q/041 · Spline gauges', body: 'Dear Ravi Kumar,',
  documents: [{ invoice_id: 'Q-1', doc_type: 'quote', label: 'Quotation Q/041', why_not: null }], attach: ['Q-1'],
};

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const STEPS = [
  { key: 'written', label: 'Written', state: 'done' as const, sub: '' },
  { key: 'sent', label: 'Sent', state: 'done' as const, sub: '14 Oct' },
  { key: 'answer', label: 'Accepted', state: 'now' as const, sub: 'Waiting · 20 days' },
  { key: 'forward', label: 'Taken forward', state: 'todo' as const, sub: '' },
];

const NEXT = {
  tone: 'action' as const, text: 'Sent on 14 Oct.', sub: 'No answer for 20 days. Time to follow it up.',
  actions: [
    { kind: 'post' as const, label: 'Mark accepted', action: '/quotes/Q-1/status', fields: { status: 'accepted' }, primary: false, confirm: null },
    { kind: 'email' as const, label: 'Send a follow-up', invoice_id: 'Q-1', primary: true },
    { kind: 'dialog' as const, label: 'Revise', dialog: 'change-dialog', primary: false },
  ],
};

describe('DocumentNext', () => {
  it('shows where the document is and what to do, the main action coloured', () => {
    render(<DocumentNext next={NEXT} steps={STEPS} invoiceId="Q-1" projectId="P-1" />);
    expect(screen.getByRole('list', { name: 'Where the job is' }).children).toHaveLength(4);
    expect(screen.getByText('Waiting · 20 days').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Sent on 14 Oct.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send a follow-up' })).toHaveClass('btn-primary');
    const accept = screen.getByRole('button', { name: 'Mark accepted' }).closest('form')!;
    expect(accept).toHaveAttribute('action', '/quotes/Q-1/status');
    expect(accept.querySelector('input[name="status"]')).toHaveValue('accepted');
  });

  it('opens the page\'s change dialog, and the email form for the document', async () => {
    render(<DocumentNext next={NEXT} steps={STEPS} invoiceId="Q-1" projectId="P-1" />);
    expect(screen.getByRole('button', { name: 'Revise' })).toHaveAttribute('data-open-dialog', 'change-dialog');
    const fetch = vi.fn(async () => new Response(JSON.stringify(COMPOSE), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetch);
    fireEvent.click(screen.getByRole('button', { name: 'Send a follow-up' }));
    expect(await screen.findByDisplayValue('Quotation Q/041 · Spline gauges')).toBeInTheDocument();
    expect(String(fetch.mock.calls[0])).toContain('/api/projects/P-1/compose?invoice_id=Q-1');
  });
});
