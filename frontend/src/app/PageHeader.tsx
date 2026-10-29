// A screen's part of the header: its breadcrumbs and buttons, drawn into the app's header (Layout), and the tab's
// title. Outside the app (a screen on its own, as in the tests) it draws nothing.
import { createContext, useContext, useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

export interface Crumb {
  label: string;
  href?: string;
}

export const HeaderSlots = createContext<{ crumbs: HTMLElement | null; actions: HTMLElement | null } | null>(null);

export function Crumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      {crumbs.map((c, i) => (
        <span key={`${i}-${c.label}`} style={{ display: 'contents' }}>
          {i > 0 && <span aria-hidden="true">/</span>}
          {c.href && i < crumbs.length - 1 ? <a href={c.href}>{c.label}</a> : <b>{c.label}</b>}
        </span>
      ))}
    </nav>
  );
}

export function PageHeader({ title, crumbs, actions }: { title: string; crumbs?: Crumb[]; actions?: ReactNode }) {
  const slots = useContext(HeaderSlots);
  useEffect(() => {
    document.title = `${title} · DocuMint`;
  }, [title]);
  return (
    <>
      {slots?.crumbs && createPortal(<Crumbs crumbs={crumbs ?? [{ label: title }]} />, slots.crumbs)}
      {slots?.actions && actions ? createPortal(actions, slots.actions) : null}
    </>
  );
}
