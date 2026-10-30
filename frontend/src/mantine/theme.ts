// Mantine (https://mantine.dev), the app's dropdowns and pickers, in DocuMint's look: its violet accent, warm greys
// and IBM Plex (static/css/variables.css). Surfaces, text and borders are the app's own CSS variables, so they follow
// its light and dark themes.
import { createTheme, type CSSVariablesResolver, type MantineColorsTuple } from '@mantine/core';

const docu: MantineColorsTuple = ['#f3f1fd', '#e4e0fa', '#c9c1f5', '#ada1ef', '#9085e9', '#7868df', '#6250d6', '#5141c2', '#4a3aa7', '#3a2d86'];
// Light: surface-page, surface-2, surface-3, line-1, line-2, neutral, ink-3, ink-2, …, ink-1
const gray: MantineColorsTuple = ['#f6f6f3', '#f2f1ed', '#e9e8e3', '#e6e5df', '#d4d3cc', '#a3a29b', '#6f6d68', '#52514e', '#2e2e2b', '#0b0b0b'];
// Dark: ink-1 … surface-page
const dark: MantineColorsTuple = ['#f0efec', '#c3c2b7', '#9a988f', '#6f6d68', '#3d3d39', '#2e2e2b', '#232321', '#1a1a19', '#141413', '#0f0f0e'];

const FONT = "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";

/** Dropdowns, popovers and tooltips: the app's dialog shadow and corners, a quick pop open */
const DROPDOWN = { shadow: 'md', radius: 'md', transitionProps: { transition: 'pop', duration: 120 } } as const;

export const theme = createTheme({
  primaryColor: 'docu',
  primaryShade: { light: 6, dark: 4 },
  colors: { docu, gray, dark },
  fontFamily: FONT,
  fontFamilyMonospace: "'IBM Plex Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace",
  headings: { fontFamily: FONT, fontWeight: '600' },
  defaultRadius: 'sm',
  radius: { xs: '4px', sm: '6px', md: '10px', lg: '14px', xl: '20px' },
  fontSizes: { xs: '12px', sm: '14px', md: '15px', lg: '18px', xl: '20px' },
  focusRing: 'auto',
  cursorType: 'pointer',
  components: {
    Combobox: { defaultProps: DROPDOWN },
    Popover: { defaultProps: { shadow: 'md', radius: 'md' } },
    Select: { defaultProps: { comboboxProps: DROPDOWN } },
  },
});

export const resolver: CSSVariablesResolver = () => {
  const app = {
    '--mantine-color-body': 'var(--surface-1)',
    '--mantine-color-text': 'var(--ink-1)',
    '--mantine-color-dimmed': 'var(--ink-3)',
    '--mantine-color-default': 'var(--surface-1)',
    '--mantine-color-default-hover': 'var(--surface-2)',
    '--mantine-color-default-border': 'var(--line-2)',
    '--mantine-color-placeholder': 'var(--ink-3)',
  };
  return { variables: {}, light: app, dark: app };
};

/** The app's theme: the one picked with its toggle (data-theme on <html>), else the system's */
export function colorScheme(): 'light' | 'dark' {
  const chosen = document.documentElement.getAttribute('data-theme');
  if (chosen === 'light' || chosen === 'dark') return chosen;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
