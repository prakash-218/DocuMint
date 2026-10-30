import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RoleForm, RolesView, toggle } from './Roles';

type Editor = Parameters<typeof RoleForm>[0]['data'];
type Listing = Parameters<typeof RolesView>[0]['data'];

const QUOTES = [
  { name: 'quotes.read', label: 'See quotations', needs: [], yours: true },
  { name: 'quotes.write', label: 'Make, edit and send quotations', needs: ['quotes.read'], yours: true },
];
const INVOICES = [{ name: 'invoices.write', label: 'Make, edit and finalize invoices', needs: ['invoices.read'], yours: false }];

const EDITOR: Editor = {
  title: 'New role',
  role: { id: null, name: '', description: '', permissions: [], members: 0 },
  catalog: [{ key: 'quotes', label: 'Quotations', permissions: QUOTES }, { key: 'invoices', label: 'Invoices', permissions: INVOICES }],
  editable: true,
  save: '/api/settings/roles',
  method: 'POST',
  delete: null,
  back: '/settings/roles',
};

function Landed() {
  const state = useLocation().state as { notice?: string } | null;
  return <p>Back on the roles: {state?.notice}</p>;
}

function editor(data: Editor) {
  render(
    <MemoryRouter initialEntries={['/settings/roles/new']}>
      <Routes>
        <Route path="/settings/roles/new" element={<RoleForm data={data} />} />
        <Route path="/settings/roles" element={<Landed />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('a role of your own', () => {
  it('ticks what a permission needs, and unticks what needs it', () => {
    const all = [...QUOTES, ...INVOICES];
    const on = toggle(new Set(), QUOTES[1], true, all);
    expect([...on].sort()).toEqual(['quotes.read', 'quotes.write']);
    expect([...toggle(on, QUOTES[0], false, all)]).toEqual([]);
  });

  it('is saved through the API, and only with what your own role can give', async () => {
    const fetched = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ id: 'R-1' }), { status: 201 }));
    editor(EDITOR);
    expect(screen.getByRole('checkbox', { name: 'Make, edit and finalize invoices' })).toBeDisabled();
    await userEvent.type(screen.getByLabelText('Name *'), 'Estimator');
    await userEvent.click(screen.getByRole('checkbox', { name: 'Make, edit and send quotations' }));
    expect(screen.getByRole('checkbox', { name: 'See quotations' })).toBeChecked();
    await userEvent.click(screen.getByRole('button', { name: 'Make role' }));
    const [url, init] = fetched.mock.calls[0];
    expect(url).toBe('/api/settings/roles');
    expect(init?.method).toBe('POST');
    expect(JSON.parse(String(init?.body))).toEqual({ name: 'Estimator', description: '', permissions: ['quotes.read', 'quotes.write'] });
    expect(await screen.findByText('Back on the roles: Estimator saved')).toBeInTheDocument();
  });

  it('says why it was not saved', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ error: 'There is already a role called Estimator.' }), { status: 409 }));
    editor({ ...EDITOR, role: { ...EDITOR.role, name: 'Estimator' } });
    await userEvent.click(screen.getByRole('button', { name: 'Make role' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('There is already a role called Estimator.');
  });

  it('is only shown, not changed, when it has more than your role', () => {
    editor({ ...EDITOR, title: 'Accounts', editable: false, method: 'PATCH', save: '/api/settings/roles/R-9',
             role: { id: 'R-9', name: 'Accounts', description: '', permissions: ['quotes.read'], members: 2 } });
    expect(screen.getByText(/more than your own role does/)).toBeInTheDocument();
    expect(screen.getByLabelText('Name *')).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: 'See quotations' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Save' })).toBeNull();
    expect(screen.getByText(/2 people have this role/)).toBeInTheDocument();
  });

  it('can be deleted after asking', async () => {
    const fetched = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    editor({ ...EDITOR, method: 'PATCH', save: '/api/settings/roles/R-1', delete: '/api/settings/roles/R-1',
             role: { id: 'R-1', name: 'Estimator', description: '', permissions: [], members: 0 } });
    await userEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(fetched.mock.calls[0][1]?.method).toBe('DELETE');
    expect(await screen.findByText('Back on the roles: Estimator deleted')).toBeInTheDocument();
  });
});

describe('the roles page', () => {
  const LISTING: Listing = {
    title: 'Roles',
    built_in: [{ key: 'owner', name: 'Owner', summary: 'Everything', members: 1, permissions: 33, copy: null },
               { key: 'member', name: 'Member', summary: 'Every document', members: 3, permissions: 16, copy: '/settings/roles/new?from=member' }],
    custom: [{ id: 'R-1', name: 'Estimator', description: 'Prices jobs', members: 1, permissions: 4, url: '/settings/roles/R-1', editable: true }],
    new: '/settings/roles/new',
    back: '/settings/',
  };

  it('lists your roles and the built-in ones, which can be copied', () => {
    render(<MemoryRouter><RolesView data={LISTING} /></MemoryRouter>);
    expect(screen.getByRole('link', { name: /Estimator/ })).toHaveAttribute('href', '/settings/roles/R-1');
    expect(screen.getByText('Prices jobs · 4 permissions · 1 person')).toBeInTheDocument();
    const builtIn = screen.getByRole('heading', { name: 'Built-in roles' }).closest('section') as HTMLElement;
    expect(within(builtIn).getAllByRole('link', { name: 'Copy' })).toHaveLength(1);         // not the owner
  });

  it('says how to start when there are none of your own', () => {
    render(<MemoryRouter><RolesView data={{ ...LISTING, custom: [] }} /></MemoryRouter>);
    expect(screen.getByText(/No roles of your own yet/)).toBeInTheDocument();
  });
});
