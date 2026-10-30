// Testing Library's render, inside Mantine's provider as the app is (src/mantine/Mantine.tsx): for screens with
// Mantine's dropdowns and pickers.
import type { ReactElement, ReactNode } from 'react';
import { render as base, type RenderOptions } from '@testing-library/react';
import { Mantine } from '../mantine/Mantine';

export * from '@testing-library/react';

export function render(ui: ReactElement, options?: RenderOptions) {
  return base(ui, { wrapper: ({ children }: { children: ReactNode }) => <Mantine env="test">{children}</Mantine>, ...options });
}
