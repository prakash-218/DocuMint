// Mantine for the app: its provider, following the app's light/dark theme, and the styles of the components the app
// uses. Not Mantine's baseline.css: it restyles <body>, which main.css draws.
import '@mantine/core/styles/default-css-variables.css';
import '@mantine/core/styles/global.css';
import '@mantine/core/styles/UnstyledButton.css';
import '@mantine/core/styles/VisuallyHidden.css';
import '@mantine/core/styles/Paper.css';
import '@mantine/core/styles/Popover.css';
import '@mantine/core/styles/CloseButton.css';
import '@mantine/core/styles/Group.css';
import '@mantine/core/styles/Loader.css';
import '@mantine/core/styles/Input.css';
import '@mantine/core/styles/InlineInput.css';
import '@mantine/core/styles/ScrollArea.css';
import '@mantine/core/styles/Combobox.css';
import '@mantine/core/styles/Pill.css';
import '@mantine/core/styles/PillsInput.css';
import '@mantine/core/styles/Avatar.css';
import '@mantine/core/styles/Tooltip.css';
import '@mantine/core/styles/Text.css';
import '@mantine/core/styles/Mark.css';
import './mantine.css';
import { useEffect, useState, type ReactNode } from 'react';
import { MantineProvider } from '@mantine/core';
import { colorScheme, resolver, theme } from './theme';

/** env 'test': no transitions or portals (src/test/render.tsx) */
export function Mantine({ children, env }: { children: ReactNode; env?: 'test' }) {
  const [scheme, setScheme] = useState(colorScheme);
  useEffect(() => {
    const update = () => setScheme(colorScheme());
    const observer = new MutationObserver(update);              // the app's theme toggle
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    media?.addEventListener('change', update);
    return () => {
      observer.disconnect();
      media?.removeEventListener('change', update);
    };
  }, []);
  return <MantineProvider theme={theme} cssVariablesResolver={resolver} forceColorScheme={scheme} env={env}>{children}</MantineProvider>;
}

/** For dropdowns in a <dialog>: drawn inside it (the top layer, above the page), placed fixed to the window so the
 *  dialog's scrolling body doesn't cut them off */
export const IN_DIALOG = { withinPortal: false, floatingStrategy: 'fixed' } as const;
