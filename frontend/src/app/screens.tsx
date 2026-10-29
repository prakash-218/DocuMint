// Each app screen as its route draws it: the address's parts become the screen's props. Keys start a screen afresh
// for another record (one project to the next) or another list address, rather than reusing the last one's state.
import { lazy } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router';

const Home = lazy(() => import('../islands/home/Home'));
const ProjectsBoard = lazy(() => import('../islands/board/ProjectsBoard'));
const ProjectPage = lazy(() => import('../islands/project/ProjectPage'));
const DocumentList = lazy(() => import('../islands/documents/DocumentList'));
const CustomerPage = lazy(() => import('../islands/customer/CustomerPage'));

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
