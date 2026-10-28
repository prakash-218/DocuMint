import { screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { mountAll } from './mount';

function Greeting({ name }: { name: string }) {
  return <p>Hello {name}</p>;
}

const islands = { greeting: async () => ({ default: Greeting }) };

function element(html: string): HTMLElement {
  const host = document.createElement('div');
  host.innerHTML = html;
  document.body.append(host);
  return host.firstElementChild as HTMLElement;
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('mountAll', () => {
  it('renders an island with the props from its data-props', async () => {
    const el = element(`<div data-island="greeting" data-props='{"name": "Gear Cutters"}'></div>`);
    await mountAll([el], islands);
    await waitFor(() => expect(screen.getByText('Hello Gear Cutters')).toBeInTheDocument());
    expect(el.dataset.mounted).toBe('true');
  });

  it('leaves unknown islands, bad props and ones already mounted alone', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    const unknown = element('<div data-island="nothing-here"></div>');
    const broken = element(`<div data-island="greeting" data-props="{not json"></div>`);
    const done = element(`<div data-island="greeting" data-mounted="true" data-props='{"name": "x"}'></div>`);
    await mountAll([unknown, broken, done], islands);
    expect(unknown.innerHTML).toBe('');
    expect(broken.innerHTML).toBe('');
    expect(done.innerHTML).toBe('');
    expect(error).toHaveBeenCalledWith("Island greeting: data-props isn't JSON");
  });
});
