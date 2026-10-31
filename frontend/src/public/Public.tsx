import type { ComponentType } from 'react';

// The pages outside the app (nav.public): logging in, what to do without an account (DocuMint is invite-only), an
// invite's page, forgetting and setting a password, choosing an organization, and the customer portal's login.
// templates/public.html draws the frame and the page's messages; these draw the form in it from the boot data's props.
// Every form posts to the Flask route that drew it, which decides what comes next.

interface Org { id: string; name: string; domain: string; created?: string; status?: string }

type Props = Record<string, unknown>;
const s = (p: Props, k: string) => (p[k] as string) ?? '';

function Field({ name, label, type = 'text', help, ...rest }: {
  name: string; label: string; type?: string; help?: string; required?: boolean; autoFocus?: boolean; autoComplete?: string;
  placeholder?: string; defaultValue?: string; minLength?: number;
}) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      <input type={type} id={name} name={name} className="form-input" {...rest} />
      {help && <p className="form-text">{help}</p>}
    </div>
  );
}

function Address() {
  return (
    <>
      <Field name="street_address" label="Street address" />
      <div className="form-row">
        <Field name="city" label="City" />
        <Field name="state" label="State / province" />
      </div>
      <div className="form-row">
        <Field name="zip_code" label="PIN / ZIP code" />
        <Field name="country" label="Country" defaultValue="India" />
      </div>
    </>
  );
}

function Login({ p }: { p: Props }) {
  return (
    <>
      <h1>Welcome back</h1>
      <form method="post" action={s(p, 'action')}>
        <Field name="email" label="Email" type="email" autoComplete="email" required autoFocus />
        <Field name="password" label="Password" type="password" autoComplete="current-password" required />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Log in</button>
      </form>
      <p className="auth-footer">
        <a href={s(p, 'forgot')}>Forgot your password?</a><br />
        New here? <a href={s(p, 'register')}>DocuMint is invite-only</a><br />
        <span className="text-tertiary">Are you a customer? <a href={s(p, 'portal')}>Open the customer portal</a></span>
      </p>
    </>
  );
}

function SelectOrg({ p }: { p: Props }) {
  const orgs = (p.orgs as Org[]) ?? [];
  return (
    <>
      <h1>Choose an organization</h1>
      {orgs.length ? (
        <ul className="pick-list org-pick">
          {orgs.map((o) => (
            <li key={o.id}>
              <form method="post" action={s(p, 'action')}>
                <input type="hidden" name="org_id" value={o.id} />
                <button type="submit" className="k-pick-row">
                  <span className="pick-main"><span className="pick-title">{o.name}</span>
                    <span className="pick-sub">{o.domain}{o.status && o.status !== 'active' ? ` · ${o.status}` : ''}</span></span>
                </button>
              </form>
            </li>
          ))}
        </ul>
      ) : <p className="text-tertiary">You're not in an organization yet.</p>}
      <form method="post" action={s(p, 'logout')} className="auth-footer"><button type="submit" className="link-button">Log out</button></form>
    </>
  );
}

function InviteOnly({ p }: { p: Props }) {
  return (
    <>
      <h1>DocuMint is invite-only</h1>
      <p className="lead">Ask your company's owner or an admin to invite you.</p>
      <p className="auth-footer">
        Have an account? <a href={s(p, 'login')}>Log in</a><br />
        <a href={s(p, 'forgot')}>Forgot your password?</a>
      </p>
    </>
  );
}

const PROBLEMS: Record<string, string> = {
  missing: "This invite link doesn't work. Check that you opened the whole link, or ask for a new invite.",
  used: 'This invite was used already. If it was you, log in.',
  cancelled: 'This invite was cancelled. Ask whoever invited you for a new one.',
  expired: 'This invite has expired. Ask whoever invited you to send it again.',
};

function AcceptInvite({ p }: { p: Props }) {
  const problem = s(p, 'problem');
  if (problem) {
    return (
      <>
        <h1>Your invite</h1>
        <p className="lead">{PROBLEMS[problem] ?? PROBLEMS.missing}</p>
        <p className="auth-footer"><a href={s(p, 'login')}>Log in</a></p>
      </>
    );
  }
  const newOrg = !!p.new_org;
  const account = !!p.has_account;
  return (
    <>
      <h1>{newOrg ? 'Start your organization' : `Join ${s(p, 'org')}`}</h1>
      {!newOrg && (
        <p className="lead">{s(p, 'invited_by') ? `${s(p, 'invited_by')} invited you` : "You're invited"} as <strong>{s(p, 'role').toLowerCase()}</strong>.</p>
      )}
      <form method="post" action={s(p, 'action')}>
        <div className="form-group">
          <span className="form-label">Email</span>
          <div className="form-static">{s(p, 'email')}</div>
        </div>
        {account ? (
          <Field name="password" label="Your password" type="password" autoComplete="current-password" required autoFocus
                 help="This address has a DocuMint account already." />
        ) : (
          <>
            <Field name="password" label="Choose a password" type="password" autoComplete="new-password" minLength={8} required autoFocus
                   placeholder="At least 8 characters" />
            <Field name="confirm_password" label="The password again" type="password" autoComplete="new-password" minLength={8} required />
          </>
        )}
        {newOrg && (
          <>
            <Field name="org_name" label="Organization name" placeholder="Demo Engineering" required />
            <Address />
          </>
        )}
        <button type="submit" className="btn btn-primary btn-lg btn-block">{newOrg ? 'Start my organization' : 'Accept and join'}</button>
      </form>
      {account && <p className="auth-footer"><a href={s(p, 'forgot')}>Forgot your password?</a></p>}
    </>
  );
}

function Forgot({ p }: { p: Props }) {
  return (
    <>
      <h1>Forgot your password</h1>
      {p.sent ? (
        <>
          <p className="lead">If that address has a DocuMint account, a link to set a new password is on its way.</p>
          <p className="text-secondary">No email? Ask your organization's owner or an admin for a reset link.</p>
        </>
      ) : (
        <>
          <form method="post" action={s(p, 'action')}>
            <Field name="email" label="Email" type="email" autoComplete="email" required autoFocus />
            <button type="submit" className="btn btn-primary btn-lg btn-block">Email me a link</button>
          </form>
        </>
      )}
      <p className="auth-footer"><a href={s(p, 'login')}>Back to log in</a></p>
    </>
  );
}

function Reset({ p }: { p: Props }) {
  if (p.problem) {
    return (
      <>
        <h1>New password</h1>
        <p className="lead">This link doesn't work any more: it was used, or it's more than 2 hours old.</p>
        <p className="auth-footer"><a href={s(p, 'forgot')}>Get a new link</a></p>
      </>
    );
  }
  return (
    <>
      <h1>New password</h1>
      <p className="lead">For {s(p, 'email')}.</p>
      <form method="post" action={s(p, 'action')}>
        <Field name="password" label="New password" type="password" autoComplete="new-password" minLength={8} required autoFocus placeholder="At least 8 characters" />
        <Field name="confirm_password" label="The password again" type="password" autoComplete="new-password" minLength={8} required />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Set my password</button>
      </form>
    </>
  );
}

function PortalLogin({ p }: { p: Props }) {
  return (
    <>
      <h1>Customer portal</h1>
      <form method="post" action={s(p, 'action')}>
        <Field name="email" label="Email" type="email" autoComplete="email" required autoFocus />
        <Field name="password" label="Password" type="password" autoComplete="current-password" required />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Log in</button>
      </form>
      <p className="auth-footer text-tertiary">Don't have a login? Ask the business that invoices you to create one.<br />
        <a href={s(p, 'staff')}>Staff log in</a></p>
    </>
  );
}

const SCREENS: Record<string, ComponentType<{ p: Props }>> = {
  login: Login, invite_only: InviteOnly, accept_invite: AcceptInvite, forgot: Forgot, reset: Reset,
  select_org: SelectOrg, portal_login: PortalLogin,
};

export function Public({ screen, props }: { screen: string; props: Props }) {
  const Draw = SCREENS[screen];
  return Draw ? <Draw p={props} /> : <p className="error" role="alert">There's nothing at this address.</p>;
}
