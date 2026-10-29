// Pieces the list and form screens share, drawn with the server pages' classes (main.css): a page of results
// (pagination.Page.json), the filter above a list, an empty list, a screen loading its JSON, a form the server didn't
// save starting again from what was typed (nav.spa(posted=True)), and asking before a form is sent.
import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useLocation } from 'react-router';
import { api, ApiError } from '../api';
import { Icon, type IconName } from '../icons';
import { Skeleton, type SkeletonKind } from '../Skeleton';
import { useBoot } from './Layout';
import { PageHeader } from './PageHeader';

export interface PageInfo {
  page: number;
  pages: number;
  first: number;
  last: number;
  total: number;
  numbers: (number | null)[];      // null: a gap (1 … 4 5 [6] 7 8 … 20)
  noun: string;
}

export interface Filter {
  label: string;
  href: string;
  active: boolean;
}

/** This address with ?page=n, its other arguments kept (pagination.page_url) */
export function pageHref(pathname: string, search: string, n: number): string {
  const params = new URLSearchParams(search);
  params.delete('page');
  if (n > 1) params.set('page', String(n));
  const query = params.toString();
  return pathname + (query ? `?${query}` : '');
}

export function Pager({ page }: { page: PageInfo }) {
  const location = useLocation();
  if (page.pages <= 1) return null;
  const href = (n: number) => pageHref(location.pathname, location.search, n);
  return (
    <nav className="pager" aria-label="Pages">
      <span className="pager-count">{page.first}–{page.last} of {page.total}{page.noun ? ` ${page.noun}` : ''}</span>
      <span className="pager-links">
        {page.page > 1 ? <a href={href(page.page - 1)} rel="prev" aria-label="Previous page"><Icon name="chevronLeft" /></a>
          : <span className="disabled" aria-hidden="true"><Icon name="chevronLeft" /></span>}
        {page.numbers.map((n, i) => (n === null ? <span key={`gap-${i}`} className="gap">…</span>
          : n === page.page ? <span key={n} className="current" aria-current="page">{n}</span>
            : <a key={n} href={href(n)}>{n}</a>))}
        {page.page < page.pages ? <a href={href(page.page + 1)} rel="next" aria-label="Next page"><Icon name="chevronRight" /></a>
          : <span className="disabled" aria-hidden="true"><Icon name="chevronRight" /></span>}
      </span>
    </nav>
  );
}

/** Active / All and the like, above a list; children (a search box) go beside it */
export function Filters({ filters, children }: { filters: Filter[]; children?: ReactNode }) {
  return (
    <div className="list-header">
      <nav className="segmented" aria-label="Filter">
        {filters.map((f) => <a key={f.label} href={f.href} className={f.active ? 'active' : undefined}>{f.label}</a>)}
      </nav>
      {children}
    </div>
  );
}

export function EmptyState({ icon, title, text, action }: {
  icon: IconName; title: string; text?: string; action?: { href: string; label: string } | null;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon"><Icon name={icon} /></span>
      <h3>{title}</h3>
      {text && <p>{text}</p>}
      {action && <a href={action.href} className="btn btn-primary"><Icon name="plus" />{action.label}</a>}
    </div>
  );
}

/** A screen's JSON from the API; failed: what to say when it can't be reached */
export function useLoad<T>(path: string, failed: string): { data: T | null; error: string } {
  const [state, setState] = useState<{ path: string; data: T | null; error: string }>({ path, data: null, error: '' });
  useEffect(() => {
    let current = true;
    api.get<T>(path).then((data) => current && setState({ path, data, error: '' }))
      .catch((e) => current && setState({ path, data: null, error: e instanceof ApiError ? e.message : failed }));
    return () => {
      current = false;
    };
  }, [path, failed]);
  return state.path === path ? state : { data: null, error: '' };
}

/** The screen's title and grey shapes until its JSON is here, or why it didn't come */
export function Loading({ title, kind, error, heading = false }: { title: string; kind: SkeletonKind; error: string; heading?: boolean }) {
  return (
    <>
      <PageHeader title={title} heading={heading} />
      {error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind={kind} label={`Loading ${title.toLowerCase()}…`} />}
    </>
  );
}

/** What was typed into the form the server just turned down, on the page that answered it; null once the app has
 *  moved on (react-router keys the first page it loaded 'default'). */
export function usePosted(): Record<string, string> | null {
  const posted = useBoot()?.posted;
  const location = useLocation();
  return posted && posted.path === location.pathname && location.key === 'default' ? posted.values : null;
}

/** onSubmit for a form that asks first */
export const ask = (message: string) => (e: FormEvent) => {
  if (!window.confirm(message)) e.preventDefault();
};
