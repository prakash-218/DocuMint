import { render, screen } from '../test/render';
import { describe, expect, it } from 'vitest';
import { Public } from './Public';

const posted = () => {
  const forms = Array.from(document.querySelectorAll('form'));
  return forms.map((f) => ({ method: f.method, action: f.getAttribute('action'), fields: Object.fromEntries(new FormData(f)) }));
};

describe('the pages outside the app', () => {
  it('logs in with an email and password, to the same route as before', () => {
    render(<Public screen="login" props={{ action: '/auth/login', register: '/auth/register', portal: '/customer/login' }} />);
    expect(posted()).toEqual([{ method: 'post', action: '/auth/login', fields: { email: '', password: '' } }]);
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('link', { name: 'Open the customer portal' })).toHaveAttribute('href', '/customer/login');
  });

  it("asks a verified account only for the organization, and keeps it verified", () => {
    render(<Public screen="register_org" props={{ email: 'ravi@gearcutters.example', domain: 'gearcutters.example', org_id: '', org: null,
                                                   existing_user: true, action: '/auth/register/org?existing_user=true',
                                                   back: { href: '/auth/register', label: 'Back to email' } }} />);
    expect(screen.queryByLabelText('Password')).not.toBeInTheDocument();
    expect(posted()[0].fields).toMatchObject({ email: 'ravi@gearcutters.example', existing_user: 'true', org_domain: 'gearcutters.example',
                                               country: 'India' });
    expect(posted()[0].fields).not.toHaveProperty('org_id');
  });

  it('joins an organization: the passwords and a choice of who to join', () => {
    render(<Public screen="register_org" props={{ email: 'ravi@gearcutters.example', domain: 'gearcutters.example', org_id: 'O-1',
                                                   org: { name: 'Gear Cutters', domain: 'gearcutters.example' }, existing_user: false,
                                                   action: '/auth/register/org?org_id=O-1', back: { href: '/auth/register/select-org', label: 'Back' } }} />);
    expect(screen.getByText(/You're joining/)).toHaveTextContent('Gear Cutters');
    expect(screen.getByLabelText('Password')).toHaveAttribute('minlength', '8');
    expect(screen.queryByLabelText('Organization name')).not.toBeInTheDocument();
    expect(posted()[0].fields).toMatchObject({ org_id: 'O-1', password: '', confirm_password: '' });
  });

  it('offers the organizations at the email\'s domain, or making a new one', () => {
    render(<Public screen="choose_org" props={{ email: 'ravi@gearcutters.example', domain: 'gearcutters.example', existing_user: false,
                                                 orgs: [{ id: 'O-1', name: 'Gear Cutters', domain: 'gearcutters.example' }],
                                                 action: '/auth/register/select-org?email=x', register: '/auth/register' }} />);
    expect(screen.getByRole('radio', { name: /Gear Cutters/ })).toBeRequired();
    expect(posted().map((f) => f.fields.action ?? '')).toEqual(['', 'create']);
    expect(screen.getByRole('button', { name: 'Join the selected organization' })).toHaveAttribute('value', 'join');
  });

  it('searches for an organization to join with a plain address, and asks to join one it found', () => {
    render(<Public screen="join_org" props={{ action: '/settings/organizations/join', domain: 'gearcutters.example', user_domain: 'gearcutters.example',
                                               orgs: [{ id: 'O-1', name: 'Gear Cutters', domain: 'gearcutters.example' }],
                                               cancel: '/settings/', create: '/settings/organizations/create' }} />);
    const [search, join] = posted();
    expect(search).toMatchObject({ method: 'get', fields: { domain: 'gearcutters.example' } });
    expect(join).toMatchObject({ method: 'post', fields: { domain: 'gearcutters.example' } });
  });
});
