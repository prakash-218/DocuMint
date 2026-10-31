import { render, screen, within } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { BootContext } from '../../app/Layout';
import type { Boot } from '../../app/boot';
import Help from './Help';

const boot = (permissions: string[]) => ({ me: { permissions } }) as unknown as Boot;
const topics = () => within(screen.getByRole('navigation', { name: 'Help topics' })).getAllByRole('link').map((a) => a.textContent);

describe('help', () => {
  it('has a section for each area their role can use, and a link to it', () => {
    render(<BootContext.Provider value={boot(['projects.read', 'quotes.read', 'quotes.write', 'customers.read'])}><Help /></BootContext.Provider>);
    expect(topics()).toEqual(['Projects', 'Quotations', 'Revise, correct or undo', 'Making a document', 'Email and sharing',
                              'Customers and suppliers']);
    expect(screen.getByRole('link', { name: 'Quotations' })).toHaveAttribute('href', '#quotations');
    expect(screen.queryByRole('heading', { name: 'Costing and rates' })).toBeNull();        // Sales don't read about costings
  });

  it('shows the costing and team sections to owners', () => {
    render(<BootContext.Provider value={boot(['costings.read', 'team.manage'])}><Help /></BootContext.Provider>);
    expect(topics()).toEqual(['Costing and rates', 'Team and roles']);
    expect(screen.getByRole('region', { name: 'Team and roles' })).toHaveTextContent('An invite link works once, for 7 days');
  });
});
