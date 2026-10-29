// Each app screen as its route draws it: the address's parts become the screen's props. Keys start a screen afresh
// for another record (one project to the next) or another list address, rather than reusing the last one's state.
import { lazy } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router';

const Home = lazy(() => import('../islands/home/Home'));
const ProjectsBoard = lazy(() => import('../islands/board/ProjectsBoard'));
const ProjectPage = lazy(() => import('../islands/project/ProjectPage'));
const DocumentList = lazy(() => import('../islands/documents/DocumentList'));
const CustomerPage = lazy(() => import('../islands/customer/CustomerPage'));
const DocumentPage = lazy(() => import('../islands/document/DocumentPage'));
const EditorPage = lazy(() => import('../islands/editor/EditorPage'));
const PackingPage = lazy(() => import('../islands/packing/PackingPage'));
const CustomerList = lazy(() => import('../islands/customers/CustomerList'));
const CustomerForm = lazy(() => import('../islands/customers/CustomerForm'));
const NewProject = lazy(() => import('../islands/project/NewProject'));
const Inbox = lazy(() => import('../islands/emails/Inbox'));
const Thread = lazy(() => import('../islands/emails/Thread'));
const Notifications = lazy(() => import('../islands/notifications/Notifications'));
const Settings = lazy(() => import('../islands/settings/Settings'));
const Profile = lazy(() => import('../islands/settings/Profile'));
const AuditLog = lazy(() => import('../islands/settings/AuditLog'));
const OrgForm = lazy(() => import('../islands/settings/OrgForm'));

export function HomeScreen() {
  return <Home />;
}

export function ProjectsScreen() {
  return <ProjectsBoard />;
}

export function ProjectScreen() {
  const { projectId = '' } = useParams();
  return <ProjectPage key={projectId} projectId={projectId} />;
}

/** /quotes/, /proformas/ or /invoices/; ?status= opens a tab and ?q= a search, as links from elsewhere ask */
export function ListScreen() {
  const location = useLocation();
  const [params] = useSearchParams();
  const group = location.pathname.split('/')[1];
  return <DocumentList key={location.pathname + location.search} group={group} tab={params.get('status') || 'all'}
                       query={(params.get('q') || '').trim()} />;
}

export function CustomerScreen() {
  const { customerId = '' } = useParams();
  return <CustomerPage key={customerId} customerId={customerId} />;
}

export function DocumentScreen() {
  const { invoiceId = '' } = useParams();
  return <DocumentPage key={invoiceId} invoiceId={invoiceId} />;
}

const KINDS: Record<string, string> = { quotes: 'quotation', proformas: 'proforma invoice', invoices: 'invoice' };

/** /quotes/create and the like: a new document's steps (?project_id=, ?template_id=), then its editor */
export function NewDocumentScreen() {
  const location = useLocation();
  const group = location.pathname.split('/')[1];
  return <EditorPage key={location.pathname + location.search} source={`/api/editor/new/${group}${location.search}`}
                     title={`New ${KINDS[group] ?? 'document'}`} />;
}

/** /quotes/<id>/edit (?correct=1 for a sent one) */
export function EditDocumentScreen() {
  const { invoiceId = '' } = useParams();
  const location = useLocation();
  return <EditorPage key={location.pathname + location.search} source={`/api/editor/${invoiceId}${location.search}`}
                     title={new URLSearchParams(location.search).get('correct') ? 'Correct' : 'Edit'} />;
}

/** /invoices/<id>/packing: its packing, box by box */
export function PackingScreen() {
  const { invoiceId = '' } = useParams();
  return <PackingPage key={invoiceId} invoiceId={invoiceId} />;
}

/** A list whose address's ?arguments are its filter, search and page: the screen starts afresh for each */
function useListKey() {
  const location = useLocation();
  return { key: location.pathname + location.search, search: location.search };
}

/** /customers/ (?q=, ?include_archived=true, ?page=) */
export function CustomersScreen() {
  const { key, search } = useListKey();
  return <CustomerList key={key} search={search} />;
}

/** /customers/create (?parent_id= adds a site) */
export function NewCustomerScreen() {
  const { key, search } = useListKey();
  return <CustomerForm key={key} source={`/api/customers/new${search}`} title="New customer" />;
}

/** /customers/<id>/edit */
export function EditCustomerScreen() {
  const { customerId = '' } = useParams();
  return <CustomerForm key={customerId} source={`/api/customers/${customerId}/form`} title="Edit customer" />;
}

/** /projects/new (?customer_id=) */
export function NewProjectScreen() {
  const { key, search } = useListKey();
  return <NewProject key={key} search={search} />;
}

/** /emails/ (?show=all, ?page=) */
export function InboxScreen() {
  const { key, search } = useListKey();
  return <Inbox key={key} search={search} />;
}

/** /emails/<thread id> */
export function ThreadScreen() {
  const { threadId = '' } = useParams();
  return <Thread key={threadId} threadId={threadId} />;
}

/** /notifications/ (?show=all, ?page=) */
export function NotificationsScreen() {
  const { key, search } = useListKey();
  return <Notifications key={key} search={search} />;
}

export function SettingsScreen() {
  return <Settings />;
}

export function ProfileScreen() {
  return <Profile />;
}

/** /settings/audit-log (?table_name=, ?page=) */
export function AuditLogScreen() {
  const { key, search } = useListKey();
  return <AuditLog key={key} search={search} />;
}

/** /settings/organizations/<id>/edit */
export function OrgScreen() {
  const { orgId = '' } = useParams();
  return <OrgForm key={orgId} orgId={orgId} />;
}
