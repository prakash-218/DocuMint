// The screens the app draws itself, by address. Flask serves the app's page for exactly these (nav.spa); every
// other address is still a server page, which the app opens with an ordinary page load.
import type { ComponentType } from 'react';
import { matchRoutes } from 'react-router';
import type { SkeletonKind } from '../Skeleton';
import { AuditLogScreen, CostingScreen, CustomerScreen, CustomersScreen, DocumentScreen, EditCustomerScreen, EditDocumentScreen,
         EditTemplateScreen, HomeScreen, InboxScreen, ListScreen, NewCustomerScreen, NewDocumentScreen, NewProjectScreen,
         NewTemplateScreen, NotificationsScreen, OrgScreen, PackingScreen, PaymentsScreen, ProfileScreen, ProjectScreen, ProjectsScreen,
         RatesScreen, RoleScreen, RolesScreen, SettingsScreen, TemplateLayoutScreen, TemplateScreen, TemplatesScreen, ThreadScreen } from './screens';

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
  { path: '/proformas', screen: ListScreen, skeleton: 'list', label: 'Proformas' },
  { path: '/invoices', screen: ListScreen, skeleton: 'list', label: 'Invoices' },
  { path: '/payments', screen: PaymentsScreen, skeleton: 'list', label: 'Payments' },
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
  { path: '/customers', screen: CustomersScreen, skeleton: 'list', label: 'Customers' },
  { path: '/customers/create', screen: NewCustomerScreen, skeleton: 'page', label: 'New customer' },
  { path: '/customers/:customerId/edit', screen: EditCustomerScreen, skeleton: 'page', label: 'Edit customer', ids: ['customerId'] },
  { path: '/projects/new', screen: NewProjectScreen, skeleton: 'page', label: 'New project' },
  { path: '/emails', screen: InboxScreen, skeleton: 'list', label: 'Emails' },
  { path: '/emails/:threadId', screen: ThreadScreen, skeleton: 'page', label: 'Email', ids: ['threadId'] },
  { path: '/notifications', screen: NotificationsScreen, skeleton: 'list', label: 'Notifications' },
  { path: '/settings', screen: SettingsScreen, skeleton: 'page', label: 'Settings' },
  { path: '/settings/profile', screen: ProfileScreen, skeleton: 'page', label: 'Business profile' },
  { path: '/settings/audit-log', screen: AuditLogScreen, skeleton: 'list', label: 'Audit log' },
  { path: '/settings/organizations/:orgId/edit', screen: OrgScreen, skeleton: 'page', label: 'Name & address', ids: ['orgId'] },
  { path: '/settings/roles', screen: RolesScreen, skeleton: 'list', label: 'Roles' },
  { path: '/settings/roles/new', screen: RoleScreen, skeleton: 'page', label: 'New role' },
  { path: '/settings/roles/:roleId', screen: RoleScreen, skeleton: 'page', label: 'Role', ids: ['roleId'] },
  { path: '/costings/rates', screen: RatesScreen, skeleton: 'page', label: 'Rates list' },
  { path: '/costings/:costingId', screen: CostingScreen, skeleton: 'page', label: 'Costing', ids: ['costingId'] },
  { path: '/templates', screen: TemplatesScreen, skeleton: 'list', label: 'Templates' },
  { path: '/templates/create', screen: NewTemplateScreen, skeleton: 'page', label: 'New template' },
  { path: '/templates/:templateId', screen: TemplateScreen, skeleton: 'page', label: 'Template', ids: ['templateId'] },
  { path: '/templates/:templateId/layout', screen: TemplateLayoutScreen, skeleton: 'page', label: 'Pages & printing', ids: ['templateId'] },
  { path: '/templates/:templateId/edit', screen: EditTemplateScreen, skeleton: 'page', label: 'Edit template', ids: ['templateId'] },
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
