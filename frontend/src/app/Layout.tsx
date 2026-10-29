// The app's frame, drawn as base.html draws the server pages' (the same classes, so main.css styles both): the
// sidebar for this role, the header with the screen's breadcrumbs and buttons (PageHeader), and the messages the
// last page left. On a phone the sidebar slides in from the menu button.
import { createContext, Fragment, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useLocation } from 'react-router';
import { Icon } from '../icons';
import type { Boot, NewItem } from './boot';
import { activeKey, lucide } from './nav';
import { HeaderSlots } from './PageHeader';

export const BootContext = createContext<Boot | null>(null);

export function useBoot(): Boot | null {
  return useContext(BootContext);
}

const MAC = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme') || (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const next = current === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  try {
    localStorage.setItem('dm-theme', next);
  } catch {
    // private mode: the choice lasts until the page closes
  }
}

/** Switch organization: the same form the server pages post. */
function switchOrg(action: string, orgId: string) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = action;
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = 'org_id';
  input.value = orgId;
  form.appendChild(input);
  document.body.appendChild(form);
  form.submit();
}

function Sidebar({ boot, open, path }: { boot: Boot; open: boolean; path: string }) {
  const on = activeKey(boot.sidebar, path);
  const { me } = boot;
  return (
    <aside className={`sidebar${open ? ' open' : ''}`} id="app-sidebar">
      <div className="sidebar-header">
        <a href={boot.links.home} className="sidebar-logo">
          <span className="logo-icon"><img src="/static/img/documint-icon.svg" alt="" /></span>
          <span className="logo-text">DocuMint</span>
        </a>
      </div>
      <nav aria-label="Main">
        {boot.sidebar.map((section, i) => (
          <div className="nav-section" key={section.title ?? i}>
            {section.title && <div className="nav-section-title">{section.title}</div>}
            <ul className="sidebar-nav">
              {section.items.map((item) => (
                <li className="sidebar-nav-item" key={item.key}>
                  <a href={item.href} className={`sidebar-nav-link${item.key === on ? ' active' : ''}`}
                     aria-current={item.key === on ? 'page' : undefined}>
                    <Icon name={lucide(item.icon)} size={18} className="lucide nav-icon" /><span>{item.label}</span>
                    {item.badge > 0 && <span className="nav-badge" aria-label={`${item.badge} unread`}>{item.badge < 100 ? item.badge : '99+'}</span>}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        {boot.orgs.length > 1 && (
          <div className="org-switcher">
            <label htmlFor="orgSelect" className="sr-only">Organization</label>
            <select id="orgSelect" className="form-select" value={me.org.id} onChange={(e) => switchOrg(boot.links.select_org, e.target.value)}>
              {boot.orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </div>
        )}
        <div className="flex-between" style={{ flexWrap: 'nowrap' }}>
          <div className="user-chip">
            <span className="avatar" aria-hidden="true">{(me.email || '?').slice(0, 2)}</span>
            <span className="user-chip-text">
              <strong title={me.email}>{me.email}</strong>
              <span>{me.org.name}{me.role ? ` · ${me.role}` : ''}</span>
            </span>
          </div>
          <div className="footer-actions">
            <button type="button" className="icon-btn theme-toggle" onClick={toggleTheme} title="Dark mode" aria-label="Toggle dark mode">
              <Icon name="sun" size={18} className="lucide icon-sun" /><Icon name="moon" size={18} className="lucide icon-moon" />
            </button>
            <form method="POST" action={boot.links.logout}>
              <button type="submit" className="icon-btn" title="Log out" aria-label="Log out"><Icon name="logOut" size={18} className="lucide" /></button>
            </form>
          </div>
        </div>
      </div>
    </aside>
  );
}

/** The header's "New" menu: a quotation, proforma or invoice, or a project. */
export function NewMenu({ items }: { items: NewItem[] }) {
  if (!items.length) return null;
  return (
    <details className="menu">
      <summary className="btn btn-primary"><Icon name="plus" /><span className="btn-label">New</span><Icon name="chevronDown" className="hide-mobile" /></summary>
      <div className="menu-items">
        {items.map((item) => (
          <Fragment key={item.href}>
            {item.divider && <hr />}
            <a href={item.href}><Icon name={lucide(item.icon)} />{item.label}</a>
          </Fragment>
        ))}
      </div>
    </details>
  );
}

/** Scroll to the element a #hash names once the screen has drawn it (its data may still be loading). */
function revealHash(hash: string) {
  let tries = 0;
  const look = () => {
    const el = document.getElementById(decodeURIComponent(hash.slice(1)));
    if (el) el.scrollIntoView();
    else if (tries++ < 40) window.setTimeout(look, 50);
  };
  look();
}

export function Layout({ boot, children }: { boot: Boot; children: ReactNode }) {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [flashes, setFlashes] = useState(boot.flashes);
  const [crumbs, setCrumbs] = useState<HTMLElement | null>(null);
  const [actions, setActions] = useState<HTMLElement | null>(null);
  const first = useRef(location.key);

  useEffect(() => {                          // another screen: a fresh header, no old messages, at the top
    setOpen(false);
    if (location.key === first.current) return;
    setFlashes([]);
    if (location.hash) revealHash(location.hash);
    else window.scrollTo(0, 0);
  }, [location.key, location.hash]);

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    const resize = () => { if (window.innerWidth > 768) setOpen(false); };
    document.addEventListener('keydown', key);
    window.addEventListener('resize', resize);
    return () => {
      document.removeEventListener('keydown', key);
      window.removeEventListener('resize', resize);
    };
  }, [open]);

  return (
    <div className="app-container">
      <Sidebar boot={boot} open={open} path={location.pathname} />
      <div className={`sidebar-overlay${open ? ' active' : ''}`} onClick={() => setOpen(false)} />
      <main className="main-content">
        <header className="header">
          <div className="header-content">
            <div className="header-title-section">
              <button className="mobile-menu-btn" type="button" onClick={() => setOpen(true)} aria-label="Open menu"
                      aria-controls="app-sidebar" aria-expanded={open}>
                <Icon name="menu" size={18} className="lucide" />
              </button>
              <div style={{ minWidth: 0 }} ref={setCrumbs} />
            </div>
            <div className="header-actions">
              {boot.me.role && (
                <button type="button" className="btn btn-ghost search-trigger" data-palette-open title="Search everything" aria-label="Search"
                        aria-haspopup="dialog">
                  <Icon name="search" /><span className="btn-label">Search</span><kbd className="kbd hide-mobile">{MAC ? '⌘ K' : 'Ctrl K'}</kbd>
                </button>
              )}
              <span ref={setActions} style={{ display: 'contents' }} />
            </div>
          </div>
        </header>
        {flashes.length > 0 && (
          <div className="page-alerts" role="status">
            {flashes.map((f, i) => <div key={i} className={`alert alert-${f.category}`}>{f.text}</div>)}
          </div>
        )}
        <HeaderSlots.Provider value={{ crumbs, actions }}>{children}</HeaderSlots.Provider>
      </main>
    </div>
  );
}
