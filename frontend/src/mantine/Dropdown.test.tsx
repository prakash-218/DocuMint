import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { field, pick, render, screen } from '../test/render';
import { choices, Dropdown } from './Dropdown';

const posted = (form: HTMLFormElement) => Object.fromEntries(new FormData(form).entries());

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Dropdown', () => {
  it('posts what is picked with its form, "" too', async () => {
    render(
      <form aria-label="Filters">
        <label htmlFor="d-year">Financial year</label>
        <Dropdown id="d-year" name="fy" defaultValue="26-27"
                  data={[{ value: '', label: 'Every year' }, ...choices([['26-27', 'FY 26-27'], ['25-26', 'FY 25-26']])]} />
      </form>,
    );
    const form = screen.getByRole('form', { name: 'Filters' }) as HTMLFormElement;
    expect(screen.getByLabelText('Financial year')).toHaveValue('FY 26-27');
    expect(posted(form)).toEqual({ fy: '26-27' });
    await pick(screen.getByLabelText('Financial year'), 'Every year');
    expect(posted(form)).toEqual({ fy: '' });
    expect(screen.getByLabelText('Financial year')).toHaveValue('Every year');
  });

  it('stops its form while nothing is picked, when it must be', async () => {
    render(
      <form aria-label="Move">
        <label htmlFor="d-project">Put it in</label>
        <Dropdown id="d-project" name="project_id" required placeholder="Choose a project"
                  data={[{ value: 'P-1', label: 'PRJ-001 · Spline gauges', sub: 'FY 26-27' }]} />
      </form>,
    );
    const form = screen.getByRole('form', { name: 'Move' }) as HTMLFormElement;
    expect(screen.getByLabelText('Put it in')).toHaveAttribute('placeholder', 'Choose a project');
    expect(form.checkValidity()).toBe(false);
    await pick(screen.getByLabelText('Put it in'), /Spline gauges/);
    expect(form.checkValidity()).toBe(true);
    expect(posted(form)).toEqual({ project_id: 'P-1' });
  });

  it('can post its form as soon as something is picked', async () => {
    const submitted = vi.spyOn(HTMLFormElement.prototype, 'requestSubmit').mockImplementation(() => undefined);
    render(
      <form aria-label="Team">
        <Dropdown aria-label="Role" name="role" size="xs" defaultValue="member" submitOnChange
                  data={choices([['viewer', 'Viewer'], ['member', 'Member']])} />
      </form>,
    );
    await pick('Role', 'Viewer');
    await vi.waitFor(() => expect(submitted).toHaveBeenCalledTimes(1));
    expect(posted(screen.getByRole('form', { name: 'Team' }) as HTMLFormElement)).toEqual({ role: 'viewer' });
  });

  it('shows a second line and a colour dot when a choice has them', async () => {
    const change = vi.fn();
    render(<Dropdown aria-label="Status" value="open" onChange={change}
                     data={[{ value: 'open', label: 'Open', dot: 'var(--mint)' }, { value: 'cancelled', label: 'Cancelled', sub: 'Kept, but off the board' }]} />);
    await userEvent.click(field('Status'));
    expect(await screen.findByRole('option', { name: /Cancelled/ })).toHaveTextContent('Kept, but off the board');
    await userEvent.click(screen.getByRole('option', { name: /Cancelled/ }));
    expect(change).toHaveBeenCalledWith('cancelled');
  });
});
