import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Portal, type PortalBoot } from './Portal';

/** Draw the portal over the frame and grey shapes the server put in #portal (nav.portal). */
export function start(el: HTMLElement) {
  const boot = JSON.parse(document.getElementById('boot')?.textContent || '{}') as PortalBoot;
  createRoot(el).render(
    <StrictMode>
      <Portal boot={boot} />
    </StrictMode>,
  );
}
