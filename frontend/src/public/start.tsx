import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Public } from './Public';

/** Draw the page's form in #public from its boot data: {screen, props} (nav.public). */
export function start(el: HTMLElement) {
  const boot = JSON.parse(document.getElementById('boot')?.textContent || '{}');
  createRoot(el).render(
    <StrictMode>
      <Public screen={boot.screen ?? ''} props={boot.props ?? {}} />
    </StrictMode>,
  );
}
