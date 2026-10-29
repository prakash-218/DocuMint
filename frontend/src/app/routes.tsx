// The screens the app draws itself, by address. Flask serves the app's page for exactly these (nav.spa); every
// other address is still a server page, which the app opens with an ordinary page load.
import type { ComponentType } from 'react';
import { matchRoutes } from 'react-router';
import type { SkeletonKind } from '../Skeleton';
import { CustomerScreen, DocumentScreen, EditDocumentScreen, HomeScreen, ListScreen, NewDocumentScreen, PackingScreen,
         ProjectScreen, ProjectsScreen } from './screens';

export interface AppRoute {
  path: string;
  screen: ComponentType;
  skeleton: SkeletonKind;
  label: string;
  ids?: string[];        // params that must be record ids (UUIDs): /projects/new is a server page, not a project
}

export const ROUTES: AppRoute[] = [
  { path: '/dashboard', screen: HomeScreen, skeleton: 'home', label: 'Home' },
  { path: '/projects', screen: ProjectsScreen, skeleton: 'list', label: 'Projects' },
  { path: '/projects/:projectId', screen: ProjectScreen, skeleton: 'page', label: 'Project', ids: ['projectId'] },
  { path: '/quotes', screen: ListScreen, skeleton: 'list', label: 'Quotations' },
  { path: '/proformas', screen: ListScreen, skeleton: 'list', label: 'Proforma invoices' },
  { path: '/invoices', screen: ListScreen, skeleton: 'list', label: 'Invoices' },
  { path: '/customers/:customerId', screen: CustomerScreen, skeleton: 'page', label: 'Customer', ids: ['customerId'] },
  { path: '/quotes/:invoiceId', screen: DocumentScreen, skeleton: 'doc', label: 'Quotation', ids: ['invoiceId'] },
  { path: '/proformas/:invoiceId', screen: DocumentScreen, skeleton: 'doc', label: 'Proforma', ids: ['invoiceId'] },
  { path: '/invoices/:invoiceId', screen: DocumentScreen, skeleton: 'doc', label: 'Invoice', ids: ['invoiceId'] },
  { path: '/quotes/create', screen: NewDocumentScreen, skeleton: 'page', label: 'New quotation' },
  { path: '/proformas/create', screen: NewDocumentScreen, skeleton: 'page', label: 'New proforma' },
  { path: '/invoices/create', screen: NewDocumentScreen, skeleton: 'page', label: 'New invoice' },
  { path: '/quotes/:invoiceId/edit', screen: EditDocumentScreen, skeleton: 'page', label: 'Editor', ids: ['invoiceId'] },
  { path: '/proformas/:invoiceId/edit', screen: EditDocumentScreen, skeleton: 'page', label: 'Editor', ids: ['invoiceId'] },
  { path: '/invoices/:invoiceId/edit', screen: EditDocumentScreen, skeleton: 'page', label: 'Editor', ids: ['invoiceId'] },
  { path: '/quotes/:invoiceId/packing', screen: PackingScreen, skeleton: 'page', label: 'Packing', ids: ['invoiceId'] },
  { path: '/proformas/:invoiceId/packing', screen: PackingScreen, skeleton: 'page', label: 'Packing', ids: ['invoiceId'] },
  { path: '/invoices/:invoiceId/packing', screen: PackingScreen, skeleton: 'page', label: 'Packing', ids: ['invoiceId'] },
];

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const OBJECTS = ROUTES.map((r) => ({ path: r.path }));

/** The app's screen for this path, or null when it's a server page. */
export function appRoute(pathname: string): AppRoute | null {
  const found = matchRoutes(OBJECTS, pathname);
  const last = found?.[found.length - 1];
  if (!last) return null;
  const r = ROUTES[OBJECTS.indexOf(last.route)];
  return (r.ids ?? []).every((id) => UUID.test(last.params[id] ?? '')) ? r : null;
}
