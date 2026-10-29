import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import EmailComposer, { type Compose } from './EmailComposer';

const CONTEXT: Compose = {
  from: 'desk@ourworks.example', from_name: 'Our Works', can_send: true, why_not: null,
  people: [{ name: 'Ravi Kumar', email: 'ravi@gearco.example', role: 'Purchase', gets: 'all' },
           { name: 'Divya', email: 'accounts@gearco.example', role: 'Accounts', gets: 'billing' }],
  found: [{ name: 'Meera Iyer', email: 'meera@gearco.example' }],
  to: ['ravi@gearco.example'], cc: [],
  threads: [{ thread_id: 'T-1', subject: 'PO for hob arbors' }], thread_id: null,
  subject: 'Quotation Q/041 · Hob arbor set (PRJ-041)', new_subject: 'Quotation Q/041 · Hob arbor set (PRJ-041)',
  body: 'Dear Ravi Kumar,\n\nPlease find attached our quotation Q/041.\n\nRegards,\nOur Works',
  documents: [{ invoice_id: 'Q-1', doc_type: 'quote', label: 'Quotation Q/041', why_not: null },
              { invoice_id: 'I-1', doc_type: 'invoice', label: 'Tax Invoice 058', why_not: 'Finalize it first' }],
  attach: ['Q-1'],
};

function serve(compose: Compose, send: Response = json(201, { thread_id: 'T-9', to: ['ravi@gearco.example'], cc: [],
                                                                     attached: ['Quotation Q/041'], saved_to: 'Sent' })) {
  const fetch = vi.fn(async (path: string, _init?: RequestInit) => (path.includes('/compose') ? json(200, compose) : send));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

beforeAll(() => {
  // jsdom has <dialog> but not its modal methods
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function openForm() {
  render(<EmailComposer projectId="P-1" invoiceId="Q-1" />);
  await userEvent.click(screen.getByRole('button', { name: 'Email' }));
  await screen.findByDisplayValue('Quotation Q/041 · Hob arbor set (PRJ-041)');
}

describe('EmailComposer', () => {
  it('starts with the project people, the subject, the message and the document attached', async () => {
    const fetch = serve(CONTEXT);
    await openForm();
    expect(fetch.mock.calls[0][0]).toBe('/api/projects/P-1/compose?invoice_id=Q-1');
    expect(screen.getByText('Ravi Kumar · ravi@gearco.example')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /Quotation Q\/041/ })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /Tax Invoice 058/ })).toBeDisabled();
    expect(screen.getByText(/Finalize it first/)).toBeInTheDocument();
  });

  it('adds typed addresses, refuses ones that are not, and sends what is on the form', async () => {
    const fetch = serve(CONTEXT);
    await openForm();
    const cc = screen.getByLabelText('Cc');
    await userEvent.type(cc, 'not an address{Enter}');
    expect(screen.getByRole('alert')).toHaveTextContent('"not" isn\'t an email address.');
    await userEvent.clear(cc);
    await userEvent.type(cc, 'Meera@GearCo.example{Enter}');
    expect(screen.getByText('Meera Iyer · meera@gearco.example')).toBeInTheDocument();     // known from the emails
    await userEvent.selectOptions(screen.getByLabelText('Thread'), 'T-1');
    expect(screen.getByLabelText('Subject')).toHaveValue('Re: PO for hob arbors');
    await userEvent.click(screen.getByRole('button', { name: 'Send' }));

    await screen.findByText('Sent to Ravi Kumar');
    const [path, init] = fetch.mock.calls[1];
    expect(path).toBe('/api/projects/P-1/emails');
    expect(JSON.parse(String(init?.body))).toEqual({
      to: ['ravi@gearco.example'], cc: ['meera@gearco.example'], subject: 'Re: PO for hob arbors',
      body: CONTEXT.body, thread_id: 'T-1', invoice_ids: ['Q-1'],
    });
    expect(screen.getByText(/A copy is in the mailbox's Sent folder/)).toBeInTheDocument();
  });

  it("shows the server's reason when it can't send", async () => {
    serve(CONTEXT, json(502, { error: "Couldn't reach the mail server (TimeoutError). Nothing was sent." }));
    await openForm();
    await userEvent.click(screen.getByRole('button', { name: 'Send' }));
    expect(await screen.findByRole('alert')).toHaveTextContent("Couldn't reach the mail server");
    expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled();
  });

  it('says so, and keeps Send off, while sending is not set up', async () => {
    serve({ ...CONTEXT, from: null, can_send: false, why_not: "Sending email isn't set up yet." });
    await openForm();
    expect(screen.getByText("Sending email isn't set up yet.")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled());
  });

  it('needs someone in To', async () => {
    serve({ ...CONTEXT, to: [] });
    await openForm();
    await userEvent.click(screen.getByRole('button', { name: 'Send' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Add at least one person in To.');
  });
});
