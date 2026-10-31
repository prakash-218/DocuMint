import { render, screen } from '../test/render';
import { describe, expect, it } from 'vitest';
import { Public } from './Public';

const posted = () => {
  const forms = Array.from(document.querySelectorAll('form'));
  return forms.map((f) => ({ method: f.method, action: f.getAttribute('action'), fields: Object.fromEntries(new FormData(f)) }));
};

describe('the pages outside the app', () => {
  it('logs in with an email and password, and says how to get in without an account', () => {
    render(<Public screen="login" props={{ action: '/auth/login', register: '/auth/register', forgot: '/auth/forgot', portal: '/customer/login' }} />);
    expect(posted()).toEqual([{ method: 'post', action: '/auth/login', fields: { email: '', password: '' } }]);
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('link', { name: 'Forgot your password?' })).toHaveAttribute('href', '/auth/forgot');
    expect(screen.getByRole('link', { name: 'DocuMint is invite-only' })).toHaveAttribute('href', '/auth/register');
    expect(screen.getByRole('link', { name: 'Open the customer portal' })).toHaveAttribute('href', '/customer/login');
  });

  it('has no sign-up form: it says to ask for an invite, Gmail too', () => {
    render(<Public screen="invite_only" props={{ login: '/auth/login', forgot: '/auth/forgot' }} />);
    expect(posted()).toEqual([]);
    expect(screen.getByText(/ask its owner or an admin to invite you/)).toHaveTextContent('Gmail too');
  });

  it('accepts an invite with a new password', () => {
    render(<Public screen="accept_invite" props={{ email: 'ravi@gmail.com', org: 'Gear Cutters', role: 'Member', invited_by: 'owner@gearcutters.example',
                                                    new_org: false, has_account: false, action: '/auth/invite/T', problem: '', login: '/auth/login' }} />);
    expect(screen.getByRole('heading', { name: 'Join Gear Cutters' })).toBeInTheDocument();
    expect(screen.getByText(/owner@gearcutters.example invited you as/)).toHaveTextContent('member');
    expect(screen.getByText('ravi@gmail.com')).toBeInTheDocument();                       // the address is the invite's, not typed
    expect(posted()).toEqual([{ method: 'post', action: '/auth/invite/T', fields: { password: '', confirm_password: '' } }]);
    expect(screen.getByLabelText('Choose a password')).toHaveAttribute('minlength', '8');
  });

  it('asks an existing account only for its password, and an invite to start one for the organization too', () => {
    const { unmount } = render(<Public screen="accept_invite" props={{ email: 'ravi@gmail.com', org: 'Gear Cutters', role: 'Admin', new_org: false,
                                                                       has_account: true, action: '/auth/invite/T', problem: '', forgot: '/auth/forgot' }} />);
    expect(posted()[0].fields).toEqual({ password: '' });
    expect(screen.getByRole('link', { name: 'Forgot your password?' })).toBeInTheDocument();
    unmount();
    render(<Public screen="accept_invite" props={{ email: 'ravi@gmail.com', org: '', role: 'Owner', new_org: true, has_account: false,
                                                   action: '/auth/invite/T', problem: '' }} />);
    expect(screen.getByRole('heading', { name: 'Start your organization' })).toBeInTheDocument();
    expect(posted()[0].fields).toMatchObject({ org_name: '', password: '', confirm_password: '', country: 'India' });
  });

  it('says what is wrong with an invite that can\'t be used', () => {
    render(<Public screen="accept_invite" props={{ problem: 'expired', login: '/auth/login' }} />);
    expect(screen.getByText(/This invite has expired/)).toBeInTheDocument();
    expect(posted()).toEqual([]);
  });

  it('asks for the address to email a reset link to, then says what to do if none comes', () => {
    const { unmount } = render(<Public screen="forgot" props={{ action: '/auth/forgot', sent: false, login: '/auth/login' }} />);
    expect(posted()).toEqual([{ method: 'post', action: '/auth/forgot', fields: { email: '' } }]);
    unmount();
    render(<Public screen="forgot" props={{ action: '/auth/forgot', sent: true, login: '/auth/login' }} />);
    expect(screen.getByText(/can make you a reset link from Settings/)).toBeInTheDocument();
  });

  it('sets a new password from a reset link', () => {
    render(<Public screen="reset" props={{ email: 'ravi@gmail.com', action: '/auth/reset/T', problem: false }} />);
    expect(screen.getByText('For ravi@gmail.com.')).toBeInTheDocument();
    expect(posted()).toEqual([{ method: 'post', action: '/auth/reset/T', fields: { password: '', confirm_password: '' } }]);
  });
});
