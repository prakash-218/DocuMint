import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ProjectsBoard, { matches, type Projects, type Row } from './ProjectsBoard';

function row(id: string, title: string, over: Partial<Row> = {}): Row {
  return {
    id, label: `PRJ-0${id}`, title, reference: '', url: `/projects/${id}/new`,
    customer: { id: 'C-1', name: 'Gear Cutters Ltd', site: 'Hosur plant' }, fiscal_year: '26-27', status: 'open',
    stage: 'accepted', pill: { text: 'Waiting for an answer', tone: 'wait' }, stage_label: 'Quoted', sub: 'Waiting · 6 days', next: 'Quotation sent.',
    action: 'Mark accepted', tone: 'wait', currency: 'INR', quoted: 100000, due: 0, last_activity: '2026-10-20T10:00:00',
    numbers: [`Q/0${id}`], ...over,
  };
}

const DATA: Projects = {
  can: { edit: true, sales: false },
  projects: [
    row('41', 'Hob arbor set'),
    row('42', 'Spline gauges', { stage: 'advance', pill: { text: 'Accepted', tone: 'action' }, stage_label: 'Accepted', tone: 'action', action: 'Raise proforma for the advance',
                                 last_activity: '2026-10-18T10:00:00', customer: { id: 'C-2', name: 'Axle Works', site: null } }),
    row('43', 'Drill jig', { stage: 'paid', pill: { text: 'Waiting for payment', tone: 'wait' }, stage_label: 'Invoiced', due: 250000, action: 'Record payment',
                             last_activity: '2026-10-21T10:00:00', fiscal_year: '25-26' }),
    row('44', 'Press tool', { stage: null, pill: { text: 'Paid', tone: 'done' }, stage_label: 'Paid', action: 'Mark the project completed' }),
    row('45', 'Old fixture', { status: 'completed', stage: null, pill: { text: 'Paid', tone: 'done' }, stage_label: 'Paid' }),
  ],
  board: [{ key: 'quoted', label: 'Quoting' }, { key: 'accepted', label: 'Waiting for an answer' }, { key: 'advance', label: 'Advance' },
          { key: 'invoiced', label: 'To invoice' }, { key: 'paid', label: 'Waiting for payment' }],
  years: ['26-27', '25-26'],
  customers: [{ id: 'C-2', name: 'Axle Works' }, { id: 'C-1', name: 'Gear Cutters Ltd' }],
  new_project: '/projects/new',
};

function serve(data: Projects = DATA) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })));
}

const titles = () => [...document.querySelectorAll('.rr .c-title')].map((t) => t.textContent);

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ProjectsBoard', () => {
  it('lists the open projects with where each is, newest activity first', async () => {
    serve();
    render(<ProjectsBoard />);
    expect(await screen.findByRole('tab', { name: /^Open\s*4/ })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /^Completed\s*1/ })).toHaveTextContent('₹1,00,000');      // its count, and what was quoted
    expect(titles()).toEqual(['Drill jig', 'Hob arbor set', 'Press tool', 'Spline gauges']);
    const drill = screen.getByText('Drill jig').closest('a')!;
    expect(drill).toHaveAttribute('href', '/projects/43/new');
    expect(within(drill).getByText('Invoiced')).toHaveClass('tag', 'tone-wait');
    expect(within(drill).getByText('₹2,50,000')).toBeInTheDocument();
    expect(within(drill).getByText('Record payment')).toBeInTheDocument();
  });

  it('searches names, numbers and customers, and filters by customer and year', async () => {
    serve();
    render(<ProjectsBoard />);
    await userEvent.type(await screen.findByLabelText('Search projects'), 'q/042');
    expect(titles()).toEqual(['Spline gauges']);
    await userEvent.clear(screen.getByLabelText('Search projects'));
    await userEvent.selectOptions(screen.getByLabelText('Financial year'), '25-26');
    expect(titles()).toEqual(['Drill jig']);
    expect(matches(row('9', 'Ball pressing mandrel'), 'mandrel hosur')).toBe(true);
    expect(matches(row('9', 'Ball pressing mandrel'), 'mandrel elsewhere')).toBe(false);
  });

  it('shows open projects on a board by stage, needing action first, and remembers the choice', async () => {
    serve();
    render(<ProjectsBoard />);
    await userEvent.click(await screen.findByRole('button', { name: 'Board' }));
    const column = (name: string) => screen.getByRole('region', { name: new RegExp(`^${name}`) });
    expect(within(column('Advance')).getByText('Spline gauges')).toBeInTheDocument();
    expect(within(column('Waiting for payment')).getByText('Drill jig')).toBeInTheDocument();
    expect(screen.queryByText('Old fixture')).not.toBeInTheDocument();                          // completed: not on the board
    expect(screen.getByText(/1 paid project is off the board/)).toBeInTheDocument();
    expect(window.localStorage.getItem('documint.projectsView')).toBe('board');
  });

  it('gives Sales the quotation stages and no amounts due', async () => {
    serve({ ...DATA, can: { edit: true, sales: true }, projects: DATA.projects.map((r) => ({ ...r, due: null })) });
    render(<ProjectsBoard />);
    expect(await screen.findByText('Quoted', { selector: '.rh span' })).toBeInTheDocument();
    expect(screen.queryByText('Due', { selector: '.rh span' })).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /^Open\s*4$/ })).toBeInTheDocument();                         // no ₹ totals for Sales
    await userEvent.click(screen.getByRole('button', { name: 'Board' }));
    expect(screen.getAllByRole('region').map((r) => r.getAttribute('aria-labelledby'))).toEqual(['pb-col-quoted', 'pb-col-accepted']);
  });
});
