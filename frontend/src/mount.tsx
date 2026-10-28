import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { islands as registered, type Islands } from './islands';

/** Render each element's island with the props in its data-props, once. Unknown names are left alone. */
export async function mountAll(elements: Iterable<HTMLElement>, islands: Islands = registered): Promise<void> {
  for (const el of elements) {
    const load = islands[el.dataset.island ?? ''];
    if (!load || el.dataset.mounted) continue;
    el.dataset.mounted = 'true';
    let props: Record<string, unknown>;
    try {
      props = JSON.parse(el.dataset.props || '{}');
    } catch {
      console.error(`Island ${el.dataset.island}: data-props isn't JSON`);
      continue;
    }
    const { default: Island } = await load();
    createRoot(el).render(
      <StrictMode>
        <Island {...props} />
      </StrictMode>,
    );
  }
}
