import { useEffect, useState, type MouseEvent as ClickEvent, type ReactNode } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate, useParams } from 'react-router';
import { toggleTheme } from '../app/Layout';
import { EmptyState, Pager, useLoad, type PageInfo } from '../app/ui';
import { Icon } from '../icons';
import { Skeleton } from '../Skeleton';

// The customer portal (nav.portal): a customer's documents and one document, over GET /customer/api/documents and
// /customer/api/documents/<id> (portal_view.py). Its own small app: the portal's sidebar, no staff screens. A document
// is the same server HTML the portal always showed (_document.html, _summary.html).

export interface PortalBoot {
  customer: { name: string; email: string };
  links: { dashboard: string; logout: string };
  flashes: { category: string; text: string }[];
}

interface Documents {
  title: string;
  stats: { outstanding: string; overdue: number; paid: string };
  rows: { id: string; url: string; pdf: string; number: string; kind: string; date: string; due: string;
          status: { text: string; tone: string }; total: string; balance: string | null }[];
  page: PageInfo;
}

interface Document {
  title: string;
  from: string;
  back: string;
  pdf: string;
  document_html: string;
  summary_html: string;
}

function Frame({ boot, title, description, actions, children }: {
  boot: PortalBoot; title: string; description?: string; actions?: ReactNode; children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [flashes, setFlashes] = useState(boot.flashes);
  const location = useLocation();
  const first = useState(location.key)[0];
  useEffect(() => {
    document.title = `${title} · DocuMint`;
  }, [title]);
  useEffect(() => {
    setOpen(false);
    if (location.key !== first) {
      setFlashes([]);
      window.scrollTo(0, 0);
    }
  }, [location.key, first]);
  return (
    <div className="app-container">
      <aside className={`sidebar${open ? ' open' : ''}`} id="portal-sidebar">
        <div className="sidebar-header">
          <a href={boot.links.dashboard} className="sidebar-logo">
            <span className="logo-icon"><img src="/static/img/documint-icon.svg" alt="" /></span>
            <span className="logo-text">Billing portal</span>
          </a>
        </div>
        <nav aria-label="Portal">
          <ul className="sidebar-nav">
            <li className="sidebar-nav-item">
              <a href={boot.links.dashboard} className="sidebar-nav-link active"><Icon name="receipt" size={18} className="lucide nav-icon" /><span>My documents</span></a>
            </li>
          </ul>
        </nav>
        <div className="sidebar-footer">
          <div className="flex-between" style={{ flexWrap: 'nowrap' }}>
            <div className="user-chip">
              <span className="avatar" aria-hidden="true">{(boot.customer.name || '?').slice(0, 2)}</span>
              <span className="user-chip-text"><strong>{boot.customer.name}</strong><span style={{ textTransform: 'none' }}>{boot.customer.email}</span></span>
            </div>
            <div className="footer-actions">
              <button type="button" className="icon-btn theme-toggle" onClick={toggleTheme} title="Dark mode" aria-label="Toggle dark mode">
                <Icon name="sun" size={18} className="lucide icon-sun" /><Icon name="moon" size={18} className="lucide icon-moon" />
              </button>
              <form method="post" action={boot.links.logout}>
                <button type="submit" className="icon-btn" title="Log out" aria-label="Log out"><Icon name="logOut" size={18} className="lucide" /></button>
              </form>
            </div>
          </div>
        </div>
      </aside>
      <div className={`sidebar-overlay${open ? ' active' : ''}`} onClick={() => setOpen(false)} />
      <main className="main-content">
        <header className="header">
          <div className="header-content">
            <div className="header-title-section">
              <button className="mobile-menu-btn" type="button" onClick={() => setOpen(true)} aria-label="Open menu" aria-controls="portal-sidebar"
                      aria-expanded={open}><Icon name="menu" size={18} className="lucide" /></button>
              <div style={{ minWidth: 0 }}>
                <h1 className="header-title">{title}</h1>
                {description && <p className="header-description">{description}</p>}
              </div>
            </div>
            <div className="header-actions">{actions}</div>
          </div>
        </header>
        {flashes.length > 0 && (
          <div className="page-alerts" role="status">
            {flashes.map((f, i) => <div key={i} className={`alert alert-${f.category}`}>{f.text}</div>)}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}

function openRow(e: ClickEvent<HTMLTableRowElement>) {
  if (!(e.target as Element).closest('a, button')) e.currentTarget.querySelector<HTMLAnchorElement>('a.cell-primary')?.click();
}

function DocumentsScreen({ boot }: { boot: PortalBoot }) {
  const location = useLocation();
  const { data, error } = useLoad<Documents>(`/customer/api/documents${location.search}`, "Couldn't load your documents. Check your connection.");
  if (!data) {
    return <Frame boot={boot} title="My documents">{error ? <div className="ui"><p className="error" role="alert">{error}</p></div>
      : <Skeleton kind="list" label="Loading your documents…" />}</Frame>;
  }
  return (
    <Frame boot={boot} title={data.title}>
      <div className="stats-grid">
        <div className="stat-card"><div className="stat-label">Outstanding</div><div className="stat-value">{data.stats.outstanding}</div></div>
        <div className={`stat-card${data.stats.overdue ? ' stat-alert' : ''}`}><div className="stat-label">Overdue invoices</div><div className="stat-value">{data.stats.overdue}</div></div>
        <div className="stat-card"><div className="stat-label">Paid to date</div><div className="stat-value">{data.stats.paid}</div></div>
      </div>
      <div className="card">
        {data.rows.length ? (
          <>
            <div className="table-container" style={{ border: 0, boxShadow: 'none' }}>
              <table className="table">
                <thead>
                  <tr><th>Document</th><th className="hide-mobile">Date</th><th className="hide-mobile">Due</th><th>Status</th>
                    <th className="num">Total</th><th className="num hide-mobile">Balance</th><th><span className="sr-only">Actions</span></th></tr>
                </thead>
                <tbody>
                  {data.rows.map((d) => (
                    <tr key={d.id} onClick={openRow} style={{ cursor: 'pointer' }}>
                      <td><a href={d.url} className="cell-primary" style={{ color: 'inherit' }}>{d.number}</a><span className="cell-secondary">{d.kind}</span></td>
                      <td className="num hide-mobile">{d.date}</td>
                      <td className="num hide-mobile">{d.due}</td>
                      <td><span className={`badge badge-${d.status.tone}`}>{d.status.text}</span></td>
                      <td className="num">{d.total}</td>
                      <td className="num hide-mobile">{d.balance ?? <span className="text-tertiary">—</span>}</td>
                      <td><div className="table-actions"><a href={d.pdf} className="btn btn-ghost btn-xs" target="_blank" rel="noopener" title="Download PDF"
                                                                 aria-label={`Download ${d.number} as a PDF`}><Icon name="download" /></a></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pager page={data.page} />
          </>
        ) : <EmptyState icon="receipt" title="No documents yet" />}
      </div>
    </Frame>
  );
}

function DocumentScreen({ boot }: { boot: PortalBoot }) {
  const { invoiceId = '' } = useParams();
  const { data, error } = useLoad<Document>(`/customer/api/documents/${invoiceId}`, "Couldn't load the document. Check your connection.");
  useEffect(() => {
    if (data) (window as { lucide?: { createIcons: () => void } }).lucide?.createIcons();
  }, [data]);
  if (!data) {
    return <Frame boot={boot} title="Document">{error ? <div className="ui"><p className="error" role="alert">{error}</p></div>
      : <Skeleton kind="doc" label="Loading the document…" />}</Frame>;
  }
  return (
    <Frame boot={boot} title={data.title} description={data.from ? `From ${data.from}` : undefined}
           actions={<>
             <a href={data.back} className="btn btn-ghost"><Icon name="arrowLeft" /><span className="btn-label">All documents</span></a>
             <a href={data.pdf} className="btn btn-primary" target="_blank" rel="noopener"><Icon name="download" /><span className="btn-label">Download PDF</span></a>
           </>}>
      <div className="invoice-layout">
        <div dangerouslySetInnerHTML={{ __html: data.document_html }} />
        <aside dangerouslySetInnerHTML={{ __html: data.summary_html }} />
      </div>
    </Frame>
  );
}

/** Links to the portal's own screens open in it; the PDFs and everything else load as usual. */
function usePortalLinks() {
  const navigate = useNavigate();
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as Element | null)?.closest?.('a');
      if (!a || !a.href || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
      const url = new URL(a.href, window.location.href);
      if (url.origin !== window.location.origin || !isPortalScreen(url.pathname)) return;
      e.preventDefault();
      navigate(url.pathname + url.search);
    }
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, [navigate]);
}

const DOCUMENT = /^\/customer\/(quotes|proformas|invoices)\/[0-9a-f-]{36}\/?$/i;

/** The portal's screens: /customer/ (its documents) and /customer/<quotes|proformas|invoices>/<id> */
export function isPortalScreen(path: string): boolean {
  return path === '/customer' || path === '/customer/' || DOCUMENT.test(path);
}

function Screens({ boot }: { boot: PortalBoot }) {
  usePortalLinks();
  const location = useLocation();
  return (
    <Routes>
      <Route path="/customer" element={<DocumentsScreen key={location.search} boot={boot} />} />
      <Route path="/customer/:group/:invoiceId" element={<DocumentScreen key={location.pathname} boot={boot} />} />
      <Route path="*" element={<Frame boot={boot} title="Not found"><div className="ui"><p className="error" role="alert">There's nothing at this address.</p></div></Frame>} />
    </Routes>
  );
}

export function Portal({ boot }: { boot: PortalBoot }) {
  return <BrowserRouter><Screens boot={boot} /></BrowserRouter>;
}
