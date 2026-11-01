import { act, render, screen, waitFor, within } from '../test/render';
import { MemoryRouter } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from './App';
import type { Boot } from './boot';
import { BootContext, Layout } from './Layout';
import { activeKey } from './nav';
import { appRoute } from './routes';

const PROJECT = '6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f';
const CUSTOMER = '0a1b2c3d-4e5f-4a6b-8c9d-0e1f2a3b4c5d';

const BOOT: Boot = {
  me: { email: 'ravi@gearco.example', role: 'owner', role_label: 'Owner', org: { id: 'O-1', name: 'Gear Cutters Ltd' }, permissions: ['projects.read'],
        can: { edit: true, edit_customers: true, manage: true, read_mail: true, quotations_only: false } },
  sidebar: [
    { title: null, items: [
      { key: 'home', label: 'Dashboard', icon: 'layout-dashboard', href: '/dashboard/', prefix: '/dashboard', badge: 0 },
      { key: 'notifications', label: 'Notifications', icon: 'bell', href: '/notifications/', prefix: '/notifications', badge: 3 },
      { key: 'projects', label: 'Projects', icon: 'briefcase', href: '/projects/', prefix: '/projects', badge: 0 },
      { key: 'quote', label: 'Quotations', icon: 'file-pen-line', href: '/quotes/', prefix: '/quotes', badge: 0 },
    ] },
    { title: 'Organization', items: [
      { key: 'settings', label: 'Settings', icon: 'settings', href: '/settings/', prefix: '/settings', badge: 0 },
      { key: 'audit', label: 'Audit log', icon: 'history', href: '/settings/audit-log', prefix: '/settings/audit-log', badge: 0 },
    ] },
  ],
  orgs: [],
  links: { home: '/dashboard/', logout: '/auth/logout', select_org: '/settings/select-org', search: '/search/items',
           new: [{ label: 'Quotation', icon: 'file-pen-line', href: '/quotes/create?doc_type=quote' },
                 { label: 'Project', icon: 'briefcase', href: '/projects/new', divider: true }] },
  flashes: [{ category: 'success', text: 'Project deleted.' }],
};

function app(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <BootContext.Provider value={BOOT}>
        <Layout boot={BOOT}><AppRoutes /></Layout>
      </BootContext.Provider>
    </MemoryRouter>,
  );
}

/** Every API call answers with this (or never, for a screen's own data the test doesn't need). */
function serve(data: unknown = null) {
  vi.stubGlobal('fetch', vi.fn(() => (data === null ? new Promise(() => {})
    : Promise.resolve(new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })))));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('which addresses are the app\'s', () => {
  it('knows its screens, and leaves the server pages beside them alone', () => {
    expect(appRoute('/dashboard/')?.label).toBe('Home');
    expect(appRoute('/projects/')?.label).toBe('Projects');
    expect(appRoute(`/projects/${PROJECT}`)?.label).toBe('Project');
    expect(appRoute('/quotes/')?.label).toBe('Quotations');
    expect(appRoute(`/customers/${CUSTOMER}`)?.label).toBe('Customer');
    expect(appRoute(`/quotes/${PROJECT}`)?.label).toBe('Quotation');
    expect(appRoute(`/invoices/${PROJECT}`)?.label).toBe('Invoice');
    expect(appRoute('/quotes/create')?.label).toBe('New quotation');
    expect(appRoute(`/quotes/${PROJECT}/edit`)?.label).toBe('Editor');
    expect(appRoute(`/invoices/${PROJECT}/packing`)?.label).toBe('Packing');
    expect(appRoute('/projects/new')?.label).toBe('New project');
    expect(appRoute('/customers/')?.label).toBe('Customers');
    expect(appRoute('/customers/create')?.label).toBe('New customer');
    expect(appRoute(`/customers/${CUSTOMER}/edit`)?.label).toBe('Edit customer');
    expect(appRoute(`/emails/${PROJECT}`)?.label).toBe('Email');
    expect(appRoute('/settings/audit-log')?.label).toBe('Audit log');
    expect(appRoute('/templates/')?.label).toBe('Templates');
    expect(appRoute(`/templates/${PROJECT}/layout`)?.label).toBe('Pages & printing');
    expect(appRoute('/costings/rates')?.label).toBe('Rates list');
    expect(appRoute(`/costings/${PROJECT}`)?.label).toBe('Costing');
    for (const server of ['/projects/options', '/quotes/import', '/invoices/x/packing', `/invoices/${PROJECT}/pdf`,
                          `/projects/${PROJECT}/edit`, `/emails/files/${PROJECT}`, `/notifications/${PROJECT}/open`,
                          '/settings/select-org', '/costings/library', `/costings/${PROJECT}/items`]) {
      expect(appRoute(server), server).toBeNull();
    }
  });

  it('lights the link with the longest prefix, as the server does', () => {
    expect(activeKey(BOOT.sidebar, '/settings/audit-log')).toBe('audit');
    expect(activeKey(BOOT.sidebar, '/settings/profile')).toBe('settings');
    expect(activeKey(BOOT.sidebar, `/projects/${PROJECT}`)).toBe('projects');
    expect(activeKey(BOOT.sidebar, '/quotesx')).toBeNull();
    expect(activeKey(BOOT.sidebar, '/costings/K-1')).toBeNull();
    const notes = [{ title: 'Sales', items: [{ key: 'invoices', label: 'Invoices', icon: 'file-text', href: '/invoices/', prefix: '/invoices',
                                                badge: 0, also: ['/credit-notes', '/debit-notes'] }] }];
    expect(activeKey(notes, '/credit-notes/N-1')).toBe('invoices');               // a note is listed in Invoices
    expect(appRoute(`/credit-notes/${PROJECT}`)?.label).toBe('Credit note');
    expect(appRoute(`/debit-notes/${PROJECT}/edit`)?.label).toBe('Editor');
  });
});

describe('the app', () => {
  it('draws the frame: the sidebar for the role, the screen\'s header, and the last page\'s message', async () => {
    serve();
    app('/projects/');
    const nav = screen.getByRole('navigation', { name: 'Main' });
    expect(within(nav).getByRole('link', { name: 'Projects' })).toHaveAttribute('aria-current', 'page');
    expect(within(nav).getByRole('link', { name: /Notifications/ })).toHaveTextContent('3');
    expect(screen.getByText('Organization')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search' })).toHaveAttribute('data-palette-open');
    expect(screen.getByText('Project deleted.')).toHaveClass('alert', 'alert-success');
    // the first screen loads its code: with every test file running at once that can take longer than a second
    expect(await screen.findByRole('navigation', { name: 'Breadcrumb' }, { timeout: 8000 })).toHaveTextContent('Projects');
    await waitFor(() => expect(document.title).toBe('Projects · DocuMint'));
    expect(document.querySelector('form[method="POST"][action="/auth/logout"]')).toBeTruthy();
  });

  it('opens another of its screens without loading a page, and leaves the message behind', async () => {
    serve();
    app('/projects/');
    await screen.findByRole('navigation', { name: 'Breadcrumb' });
    const link = document.createElement('a');
    link.href = `/customers/${CUSTOMER}`;
    link.textContent = 'Gear Cutters';
    document.querySelector('.main-content')!.appendChild(link);
    let prevented = false;
    document.addEventListener('click', (e) => { prevented = e.defaultPrevented; }, { once: true });
    await act(async () => { link.click(); });
    expect(prevented).toBe(true);
    expect(await screen.findByRole('link', { name: 'Customers' })).toHaveAttribute('href', '/customers/');
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Customers/…');
    await waitFor(() => expect(screen.queryByText('Project deleted.')).not.toBeInTheDocument());
    link.remove();
  });

  it('lets a link to a server page, a new tab or a download load as usual', async () => {
    serve();
    app('/projects/');
    await screen.findByRole('navigation', { name: 'Breadcrumb' });
    for (const [href, extra] of [['/settings/select-org', {}], [`/projects/${PROJECT}`, { target: '_blank' }], [`/projects/${PROJECT}`, { download: '' }]] as const) {
      const link = document.createElement('a');
      link.href = href;
      Object.entries(extra).forEach(([k, v]) => link.setAttribute(k, v));
      document.querySelector('.main-content')!.appendChild(link);
      let prevented = true;
      const look = (e: Event) => { prevented = e.defaultPrevented; e.preventDefault(); };     // jsdom can't load pages
      document.addEventListener('click', look);
      await act(async () => { link.click(); });
      document.removeEventListener('click', look);
      expect(prevented, `${href} ${JSON.stringify(extra)}`).toBe(false);
      link.remove();
    }
  });

  it('opens the tab and search a link to a list asks for', async () => {
    const row = (id: string, tab: string) => ({
      id, number: id, kind: 'Tax Invoice', subject: 'Spline gauge', project: null, customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: null },
      date: '2026-10-14', until: null, tab, tag: { text: tab, tone: 'wait' }, note: '', currency: 'INR', total: 100, balance: 100,
      url: `/invoices/${id}`, pdf: `/invoices/${id}/pdf`, versions: [], search: [] });
    serve({ group: 'invoices', title: 'Invoices', until: 'Due', new_url: null, new_label: 'New invoice',
            tabs: [{ key: 'all', label: 'All' }, { key: 'pending', label: 'Unpaid' }, { key: 'overdue', label: 'Overdue' }],
            rows: [row('058', 'overdue'), row('057', 'pending'), row('051', 'overdue')] });
    app('/invoices/?status=overdue&q=058');
    expect(await screen.findByRole('tab', { name: /^Overdue/ })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('searchbox')).toHaveValue('058');
    expect([...document.querySelectorAll('.rr .c-title')].map((t) => t.textContent)).toEqual(['058']);
    await waitFor(() => expect(document.title).toBe('Invoices · DocuMint'));
  });

  it('puts the Home screen\'s New menu in the header', async () => {
    serve();
    app('/dashboard/');
    const menu = (await screen.findByText('New')).closest('details')!;
    expect(within(menu).getByRole('link', { name: 'Quotation' })).toHaveAttribute('href', '/quotes/create?doc_type=quote');
    expect(within(menu).getByRole('link', { name: 'Project' })).toHaveAttribute('href', '/projects/new');
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Home');
  });
});
