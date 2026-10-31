import { render, screen, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Settings from './Settings';

const LINK = 'https://app.example/auth/invite/Zx9_long-random-token-of-forty-three-chars0';
const DATA = {
  title: 'Settings', links: [], team: '/settings/members/approve', roles: [['admin', 'Admin'], ['member', 'Member'], ['viewer', 'Viewer']],
  requests: [], switch: '/settings/select-org',
  members: [{ user_id: 'U-1', email: 'owner@gearcutters.example', role: 'owner', role_label: 'Owner', status: 'active', you: true, manage: false, reset: null },
            { user_id: 'U-2', email: 'ravi@gmail.com', role: 'member', role_label: 'Member', status: 'active', you: false, manage: true,
              reset: '/api/settings/members/U-2/reset' }],
  invite: '/api/settings/invites',
  invites: [{ id: 'I-1', email: 'divya@yahoo.com', role_label: 'Viewer', sent: '2026-10-30', expires: '2026-11-06', expired: false, by: 'owner@gearcutters.example',
              again: '/api/settings/invites/I-1/again', cancel: '/api/settings/invites/I-1' }],
  orgs: [{ id: 'O-1', name: 'Gear Cutters', domain: '', role: 'Owner', current: true }],
};

function serve() {
  const fetch = vi.fn(async (path: string, init?: RequestInit) => {
    const body = path === '/api/settings' ? DATA
      : path === '/api/settings/invites' ? { link: LINK, emailed: false, to: JSON.parse(String(init?.body)).email }
        : path.endsWith('/reset') ? { link: 'https://app.example/auth/reset/R', emailed: true, to: 'ravi@gmail.com' }
          : { link: LINK, emailed: true, to: 'divya@yahoo.com' };
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

afterEach(() => vi.unstubAllGlobals());

describe('the team on the settings page', () => {
  it('invites an address with a role, and shows the link to send when it could not be emailed', async () => {
    const fetch = serve();
    render(<Settings />);
    await userEvent.type(await screen.findByLabelText('Email'), 'arun@gmail.com');
    await userEvent.click(screen.getByRole('button', { name: 'Invite' }));
    const posted = fetch.mock.calls.find(([path]) => path === '/api/settings/invites')!;
    expect(JSON.parse(String(posted[1]?.body))).toEqual({ email: 'arun@gmail.com', role: 'member' });
    const sent = await screen.findByRole('status');
    expect(sent).toHaveTextContent("The invite for arun@gmail.com wasn't emailed");
    expect(within(sent).getByLabelText('The link')).toHaveValue(LINK);
    expect(within(sent).getByRole('link', { name: 'WhatsApp' }).getAttribute('href')).toContain(encodeURIComponent(LINK));
  });

  it('lists invites not used yet, to send again; and makes a member a link to set a new password', async () => {
    serve();
    render(<Settings />);
    const pending = await screen.findByRole('list', { name: 'Invites not used yet' });
    expect(pending).toHaveTextContent('divya@yahoo.com');
    await userEvent.click(within(pending).getByRole('button', { name: 'Send again' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Emailed the invite to divya@yahoo.com');
    await userEvent.click(screen.getByRole('button', { name: 'Password link' }));
    expect(await screen.findByText(/Emailed the link to set a new password to/)).toHaveTextContent('ravi@gmail.com');
    expect(screen.queryByRole('link', { name: 'Join' })).toBeNull();                       // no more joining by domain
  });
});
