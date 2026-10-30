import { pick, render, screen, waitFor, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import ProjectPage from './ProjectPage';
import type { Page } from './types';

const PAGE: Page = {
  project: {
    id: 'P-1', label: 'PRJ-041', title: 'Hob arbor set', reference: '', notes: '', fiscal_year: '26-27', status: 'open',
    created_at: '2026-10-08T09:00:00', customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: 'Hosur plant', url: '/customers/C-1' },
    po: null,
  },
  can: { edit: true, manage: true, read_mail: true, sales: false },
  stage: {
    steps: [{ key: 'quoted', label: 'Quoted', state: 'done', sub: '14 Oct' }, { key: 'accepted', label: 'Accepted', state: 'now', sub: 'Waiting · 6 days' },
            { key: 'advance', label: 'Advance', state: 'todo', sub: '' }, { key: 'invoiced', label: 'Invoiced', state: 'todo', sub: '' },
            { key: 'paid', label: 'Paid', state: 'todo', sub: '' }],
    current: 'accepted', pill: { text: 'Waiting for an answer', tone: 'wait' },
  },
  next: {
    tone: 'wait', text: 'Quotation Q/041 sent on 14 Oct.', sub: 'No answer for 6 days.',
    actions: [{ kind: 'post', label: 'Mark accepted', action: '/quotes/Q-1/status', fields: { status: 'accepted' }, primary: true, confirm: null },
              { kind: 'email', label: 'Send a follow-up', invoice_id: 'Q-1', primary: false }],
  },
  money: [{ currency: 'INR', quoted: 495600, invoiced: 0, received: 0, advance_held: 0, due: 0 }],
  documents: [{ invoice_id: 'Q-1', doc_type: 'quote', kind: 'Quotation', number: 'Q/041', status: 'sent', issue_date: '2026-10-14',
                currency: 'INR', total: 495600, paid: 0, balance: null, url: '/quotes/Q-1', pdf: '/quotes/Q-1/pdf',
                versions: [{ invoice_id: 'Q-0', number: 'Q/041 (original)', issue_date: '2026-10-10', total: 519200, url: '/quotes/Q-0' }] }],
  new_document: { quote: '/quotes/create?project_id=P-1', proforma: '/proformas/create?project_id=P-1', invoice: '/invoices/create?project_id=P-1' },
  timeline: [{ id: 'e-1', type: 'note', kind: 'note', title: 'Agreed 4.5% off', body: null, when: '2026-10-13T09:00:00', who: 'meena', link: null },
             { id: 'm-1', type: 'email', kind: 'email_received', title: 'Re: Quotation Q/041', body: 'Can you do better?', when: '2026-10-12T09:00:00',
               who: 'Ravi', link: '/emails/T-1', thread_id: 'T-1', files: 0, direction: 'in' }],
  people: [{ contact_id: 'K-1', customer_id: 'C-1', name: 'Ravi Kumar', email: 'ravi@gearco.example', phone: null, role: 'Purchase',
             gets: 'all', usually: 'all', initials: 'RK', at_parent: false }],
  found: { people: [{ name: 'Meera Iyer', email: 'meera@gearco.example', phone: null, seen: 'Copied on an email, 21 Oct' }], phones: [] },
  gets: { all: 'Gets everything', billing: 'Proformas and invoices only', none: 'Not on this project' },
  usually: { all: 'Everything', billing: 'Proformas and invoices', none: 'Only when picked on a project' },
  files: [], upload: { action: '/projects/files', kinds: { drawing: 'Drawing', po: 'Purchase order' } },
  costings: [], years: ['26-27', '25-26'], statuses: { open: 'Open', completed: 'Completed', cancelled: 'Cancelled' },
};

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function serve(page: Page = PAGE, answer: (path: string, init?: RequestInit) => Response | undefined = () => undefined) {
  const fetch = vi.fn(async (path: string, init?: RequestInit) => answer(path, init) ?? (init?.method && init.method !== 'GET'
    ? json(200, { ok: true }) : json(200, page)));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

const sent = (fetch: ReturnType<typeof serve>, method: string) =>
  fetch.mock.calls.filter(([, init]) => init?.method === method).map(([path, init]) => [path, JSON.parse(String(init?.body))]);

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ProjectPage', () => {
  it('shows where the job is, what to do next and the money', async () => {
    serve();
    render(<ProjectPage projectId="P-1" />);
    expect(await screen.findByText('Waiting for an answer')).toBeInTheDocument();
    const tracker = screen.getByRole('list', { name: 'Where the job is' });
    expect(within(tracker).getAllByRole('listitem').map((li) => li.textContent)).toEqual(
      ['Quoted14 Oct', 'AcceptedWaiting · 6 days', 'Advance', 'Invoiced', 'Paid']);
    expect(within(tracker).getByText('Accepted').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Quotation Q/041 sent on 14 Oct.')).toBeInTheDocument();
    const accept = screen.getByRole('button', { name: 'Mark accepted' });
    const form = accept.closest('form')!;
    expect(form).toHaveAttribute('action', '/quotes/Q-1/status');
    expect(form.querySelector('input[name=status]')).toHaveValue('accepted');
    expect(screen.getByText('₹4,95,600', { selector: '.money b' })).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Earlier versions' })).toHaveTextContent('Original · Q/041 (original)');
    expect(screen.getByText('Proforma for the advance').closest('.slot')).toHaveClass('later');   // not the next step yet
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Hob arbor set');
  });

  it('adds a note and shows the page as it is now', async () => {
    const fetch = serve();
    render(<ProjectPage projectId="P-1" />);
    await userEvent.type(await screen.findByLabelText('Add a note'), 'Called Ravi: PO next week');
    await userEvent.click(screen.getByRole('button', { name: 'Add note' }));
    await waitFor(() => expect(sent(fetch, 'POST')).toEqual([['/api/projects/P-1/notes', { text: 'Called Ravi: PO next week' }]]));
    const reads = () => fetch.mock.calls.filter(([p, i]) => p === '/api/projects/P-1' && (!i?.method || i.method === 'GET'));
    await waitFor(() => expect(reads()).toHaveLength(2));                         // loaded again after the note
  });

  it('changes what a contact gets, and adds someone found in the emails', async () => {
    const fetch = serve();
    render(<ProjectPage projectId="P-1" />);
    await screen.findByLabelText('What Ravi Kumar gets on this project', { selector: 'input' });
    await pick('What Ravi Kumar gets on this project', 'Proformas and invoices only');
    await userEvent.click(screen.getByRole('button', { name: 'Add to Hosur plant' }));
    expect(screen.getByLabelText('Email')).toHaveValue('meera@gearco.example');
    await userEvent.type(screen.getByLabelText(/^Role/), 'Quality');
    await userEvent.click(screen.getByRole('button', { name: 'Add contact' }));
    await waitFor(() => expect(sent(fetch, 'POST')).toEqual([
      ['/api/projects/P-1/people', { contact_id: 'K-1', gets: 'billing' }],
      ['/api/projects/P-1/contacts', { name: 'Meera Iyer', email: 'meera@gearco.example', phone: '', role: 'Quality', gets: 'all' }],
    ]));
  });

  it('opens the email form for a document', async () => {
    const fetch = serve(PAGE, (path) => (path.includes('/compose') ? json(200, {
      from: 'desk@ourworks.example', from_name: 'Our Works', can_send: true, why_not: null, people: [], found: [], to: [], cc: [],
      threads: [], thread_id: null, subject: 'Quotation Q/041', new_subject: 'Quotation Q/041', body: 'Dear Sir/Madam,', documents: [], attach: [],
    }) : undefined));
    render(<ProjectPage projectId="P-1" />);
    await userEvent.click(await screen.findByRole('button', { name: 'Send a follow-up' }));
    expect(await screen.findByDisplayValue('Quotation Q/041')).toBeInTheDocument();
    expect(fetch.mock.calls.some(([p]) => p === '/api/projects/P-1/compose?invoice_id=Q-1')).toBe(true);
  });

  it('edits the details, and shows why when the server says no', async () => {
    const fetch = serve(PAGE, (_path, init) => (init?.method === 'PATCH' ? json(400, { error: 'Give the project a name.' }) : undefined));
    render(<ProjectPage projectId="P-1" />);
    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }));
    await pick(screen.getByLabelText('Status'), 'Cancelled');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Give the project a name.');
    expect(sent(fetch, 'PATCH')[0]).toEqual(['/api/projects/P-1',
      { title: 'Hob arbor set', reference: '', fiscal_year: '26-27', status: 'cancelled', notes: '' }]);
    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();         // the form stays open
  });

  it('filters the timeline', async () => {
    serve();
    render(<ProjectPage projectId="P-1" />);
    await userEvent.click(await screen.findByRole('button', { name: 'Notes' }));
    expect(screen.getByText('Agreed 4.5% off')).toBeInTheDocument();
    expect(screen.queryByText('Re: Quotation Q/041')).not.toBeInTheDocument();
  });

  it('gives Sales the quotation, without the money after it or the mailbox', async () => {
    serve({ ...PAGE, can: { edit: true, manage: false, read_mail: false, sales: true }, stage: { ...PAGE.stage, steps: PAGE.stage.steps.slice(0, 2) },
            money: [{ currency: 'INR', quoted: 495600 }], found: { people: [], phones: [] }, timeline: [PAGE.timeline[0]], costings: null });
    render(<ProjectPage projectId="P-1" />);
    expect(within(await screen.findByRole('list', { name: 'Where the job is' })).getAllByRole('listitem')).toHaveLength(2);
    expect(screen.queryByText('Invoiced', { selector: '.pp-money-label' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Emails' })).not.toBeInTheDocument();
    expect(screen.queryByText("Found in this project's emails")).not.toBeInTheDocument();
    expect(screen.queryByText('Proforma for the advance')).not.toBeInTheDocument();
  });

  it('takes files dropped or chosen, and says what one is with its number', async () => {
    const files: Page['files'] = [{ id: 'F-1', name: 'scan 0041.pdf', kind: 'other', kind_label: 'Other', title: 'scan 0041.pdf', reference_no: null,
                                    date: '2026-10-20', size: '12 KB', from_email: false, url: '/projects/files/F-1', delete: '/projects/files/F-1/delete' }];
    const fetch = serve({ ...PAGE, files });
    render(<ProjectPage projectId="P-1" />);
    const zone = (await screen.findByText(/Drop files here or/)).closest('form')!;
    expect(zone).toHaveAttribute('data-dropzone');
    expect(zone).toHaveAttribute('action', '/projects/files');
    expect(zone.querySelector('input[type=file]')).toHaveAttribute('multiple');
    expect(zone.querySelector('input[name=project_id]')).toHaveValue('P-1');
    expect(screen.getByText('choose files')).toHaveAttribute('for', zone.querySelector('input[type=file]')!.id);

    await userEvent.click(screen.getByRole('button', { name: 'Other: change what scan 0041.pdf is' }));
    const form = screen.getByRole('form', { name: 'What scan 0041.pdf is' });
    await pick(within(form).getByLabelText('What it is'), 'Purchase order');
    await userEvent.type(within(form).getByLabelText(/Number/), '4500 0188');
    await userEvent.click(within(form).getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(sent(fetch, 'PATCH')).toEqual([['/api/files/F-1', { kind: 'po', reference_no: '4500 0188' }]]));
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Delete the file' })).not.toBeInTheDocument());   // closed after saving
  });

  it('adds a document of theirs to the project, takes one out, starts a costing and deletes the project', async () => {
    serve({ ...PAGE, costings: [],
            addable: [{ invoice_id: 'Q-9', number: 'Q/039', kind: 'Quotation', total: 5000, currency: 'INR' }],
            links: { documents: '/projects/P-1/documents', delete: '/projects/P-1/delete', new_costing: '/costings/new', rates: '/costings/rates' } });
    render(<ProjectPage projectId="P-1" />);
    const add = (await screen.findByLabelText("Add one of their documents that's in no project")).closest('form')!;
    expect(add).toHaveAttribute('action', '/projects/P-1/documents');
    await userEvent.click(within(add).getByLabelText("Add one of their documents that's in no project"));
    expect(await screen.findByRole('option', { name: /Q\/039 · Quotation/ })).toHaveTextContent('₹5,000');
    const out = screen.getAllByRole('button', { name: 'Take out of the project' })[0].closest('form')!;
    expect(out).toHaveAttribute('action', '/projects/P-1/documents');
    expect(out.querySelector('input[name=action]')).toHaveValue('remove');
    const costing = screen.getByRole('button', { name: 'New costing' }).closest('form')!;
    expect(costing).toHaveAttribute('action', '/costings/new');
    expect(costing.querySelector('input[name=project_id]')).toHaveValue('P-1');
    expect(screen.getByRole('link', { name: 'Rates list' })).toHaveAttribute('href', '/costings/rates');
    expect(screen.getByRole('button', { name: 'Delete the project' }).closest('form')).toHaveAttribute('action', '/projects/P-1/delete');
  });
});
