import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Skeleton } from './Skeleton';
import ProjectsBoard from './islands/board/ProjectsBoard';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Skeleton', () => {
  it('says it is loading, once, and hides the shapes from screen readers', () => {
    render(<Skeleton kind="list" label="Loading the projects…" />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-busy', 'true');
    expect(status).toHaveClass('ui', 'skeleton');
    expect(status).toHaveTextContent('Loading the projects…');
    expect(status.querySelector('[aria-hidden="true"] .rows .rr')).not.toBeNull();       // the list's rows
  });

  it('has a shape for every kind of screen', () => {
    for (const kind of ['list', 'page', 'home', 'doc', 'form'] as const) {
      const { container, unmount } = render(<Skeleton kind={kind} label="Loading" ui={kind !== 'form'} />);
      expect(container.querySelectorAll('.sk').length).toBeGreaterThan(4);
      unmount();
    }
  });

  it('is what a screen shows while its data is on the way', async () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));              // never answers
    render(<ProjectsBoard />);
    expect(await screen.findByRole('status')).toHaveTextContent('Loading the projects…');
  });
});
