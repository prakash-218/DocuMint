// The app: its frame, and the screen for the address. A click on a link to another of its screens changes the
// screen without loading a page; a link to a server page (the editor, settings...) loads that page as before.
import { Suspense, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router';
import { Skeleton } from '../Skeleton';
import type { Boot } from './boot';
import { BootContext, Layout } from './Layout';
import { appRoute, ROUTES, type AppRoute } from './routes';

declare global {
  interface Window {
    dmNavigate?: (url: string) => void;     // static/js/palette.js opens results through this
  }
}

const firstUrl = typeof window === 'undefined' ? '' : window.location.pathname + window.location.search + window.location.hash;

/** Same-origin links to the app's screens open in the app; anything else (new tab, download, a server page) as usual. */
export function useAppLinks() {
  const navigate = useNavigate();
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as Element | null)?.closest?.('a');
      if (!a || !a.href || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
      const url = new URL(a.href, window.location.href);
      if (url.origin !== window.location.origin || !appRoute(url.pathname)) return;
      if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return;   // on this page
      e.preventDefault();
      navigate(url.pathname + url.search + url.hash);
    }
    document.addEventListener('click', onClick);
    window.dmNavigate = (href: string) => {
      const url = new URL(href, window.location.href);
      if (url.origin === window.location.origin && appRoute(url.pathname)) navigate(url.pathname + url.search + url.hash);
      else window.location.assign(href);
    };
    return () => {
      document.removeEventListener('click', onClick);
      delete window.dmNavigate;
    };
  }, [navigate]);
}

/** A server page reached inside the app: load it. If the app was sent for it, the app has no screen for it. */
function Elsewhere() {
  const location = useLocation();
  const url = location.pathname + location.search + location.hash;
  const served = url === firstUrl;
  useEffect(() => {
    if (!served) window.location.assign(url);
  }, [url, served]);
  return served ? <div className="ui"><p className="error" role="alert">There's nothing at this address.</p></div> : null;
}

function Screen({ route }: { route: AppRoute }) {
  const location = useLocation();
  if (!appRoute(location.pathname)) return <Elsewhere />;          // /projects/new and the like: server pages
  const Draw = route.screen;
  return (
    <Suspense fallback={<Skeleton kind={route.skeleton} label={`Loading ${route.label.toLowerCase()}…`} />}>
      <Draw />
    </Suspense>
  );
}

export function AppRoutes() {
  useAppLinks();
  return (
    <Routes>
      {ROUTES.map((r) => <Route key={r.path} path={r.path} element={<Screen route={r} />} />)}
      <Route path="*" element={<Elsewhere />} />
    </Routes>
  );
}

export function App({ boot }: { boot: Boot }) {
  return (
    <BrowserRouter>
      <BootContext.Provider value={boot}>
        <Layout boot={boot}>
          <AppRoutes />
        </Layout>
      </BootContext.Provider>
    </BrowserRouter>
  );
}
