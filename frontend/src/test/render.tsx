// Testing Library's render, inside Mantine's provider as the app is (src/mantine/Mantine.tsx): for screens with
// Mantine's dropdowns and pickers.
import type { ReactElement, ReactNode } from 'react';
import { render as base, screen, within, type RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Mantine } from '../mantine/Mantine';

export * from '@testing-library/react';

export function render(ui: ReactElement, options?: RenderOptions) {
  return base(ui, { wrapper: ({ children }: { children: ReactNode }) => <Mantine testing>{children}</Mantine>, ...options });
}

/** A dropdown's field by its label: Mantine labels its list too, so only the input */
export const field = (label: string | RegExp) => screen.getByLabelText(label, { selector: 'input' });

/** Pick a choice in a Dropdown (src/mantine/Dropdown.tsx) or Mantine select (its field, or the field's label): open it,
 *  click the choice by its words */
export async function pick(target: HTMLElement | string | RegExp, choice: string | RegExp) {
  const input = target instanceof HTMLElement ? target : field(target);
  await userEvent.click(input);
  const list = input.getAttribute('aria-controls') && document.getElementById(input.getAttribute('aria-controls')!);
  await userEvent.click(await (list ? within(list) : screen).findByRole('option', { name: choice }));
}

/** The words of a dropdown's choices, opening it to see them */
export async function optionsOf(input: HTMLElement): Promise<string[]> {
  await userEvent.click(input);
  const list = document.getElementById(input.getAttribute('aria-controls') ?? '');
  return (list ? within(list) : screen).getAllByRole('option').map((o) => o.textContent ?? '');
}
