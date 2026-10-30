import type { ComponentType } from 'react';

// The pages outside the app (nav.public): logging in, registering (email, then a password and an organization, or
// joining one), choosing, making or joining an organization, and the customer portal's login. templates/public.html
// draws the frame and the page's messages; these draw the form in it from the boot data's props. Every form posts to
// the same Flask route as before, which decides what comes next.

interface Link { href: string; label: string }
interface Org { id: string; name: string; domain: string; created?: string; status?: string }

type Props = Record<string, unknown>;
const s = (p: Props, k: string) => (p[k] as string) ?? '';

function Hidden({ values }: { values: Record<string, string> }) {
  return <>{Object.entries(values).filter(([, v]) => v).map(([k, v]) => <input key={k} type="hidden" name={k} value={v} />)}</>;
}

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

function OrgChoices({ orgs, sub }: { orgs: Org[]; sub: (o: Org) => string }) {
  return (
    <div className="org-choices">
      {orgs.map((o) => (
        <label key={o.id} className="org-choice">
          <input type="radio" name="org_id" value={o.id} required />
          <span><strong>{o.name}</strong><span className="text-tertiary">{sub(o)}</span></span>
        </label>
      ))}
    </div>
  );
}

function Login({ p }: { p: Props }) {
  return (
    <>
      <h1>Welcome back</h1>
      <p className="lead">Log in to your DocuMint workspace.</p>
      <form method="post" action={s(p, 'action')}>
        <Field name="email" label="Email" type="email" autoComplete="email" required autoFocus />
        <Field name="password" label="Password" type="password" autoComplete="current-password" required />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Log in</button>
      </form>
      <p className="auth-footer">
        New to DocuMint? <a href={s(p, 'register')}>Create an account</a><br />
        <span className="text-tertiary">Are you a customer? <a href={s(p, 'portal')}>Open the customer portal</a></span>
      </p>
    </>
  );
}

function Register({ p }: { p: Props }) {
  return (
    <>
      <h1>Create an account</h1>
      <p className="lead">Step 1 of 2: your work email. We'll find your company's organization from it.</p>
      <form method="post" action={s(p, 'action')}>
        <Field name="email" label="Email" type="email" autoComplete="email" placeholder="you@company.com" required autoFocus />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Continue</button>
      </form>
      <p className="auth-footer">Already have an account? <a href={s(p, 'login')}>Log in</a></p>
    </>
  );
}

function Verify({ p }: { p: Props }) {
  return (
    <>
      <h1>Verify your account</h1>
      <p className="lead">An account with <strong>{s(p, 'email')}</strong> already exists. Enter its password to join an organization or create one.</p>
      <form method="post" action={s(p, 'action')}>
        <Hidden values={{ email: s(p, 'email'), domain: s(p, 'domain') }} />
        <Field name="password" label="Password" type="password" autoComplete="current-password" required autoFocus />
        <button type="submit" className="btn btn-primary btn-lg btn-block">Verify and continue</button>
      </form>
      <p className="auth-footer"><a href={s(p, 'register')}>Back to email</a> · <a href={s(p, 'login')}>Log in instead</a></p>
    </>
  );
}

function ChooseOrg({ p }: { p: Props }) {
  const orgs = (p.orgs as Org[]) ?? [];
  const hidden = { email: s(p, 'email'), domain: s(p, 'domain') };
  return (
    <>
      <h1>Choose your organization</h1>
      <p className="lead">{p.existing_user ? '' : 'Step 2 of 3: '}Join your company's organization, or create a new one. Signed up as <strong>{s(p, 'email')}</strong>.</p>
      {orgs.length > 0 && (
        <form method="post" action={s(p, 'action')}>
          <Hidden values={hidden} />
          <p className="form-text">{orgs.length === 1 ? 'An organization uses' : `${orgs.length} organizations use`} {s(p, 'domain')}. An owner approves you before you get in.</p>
          <OrgChoices orgs={orgs} sub={(o) => o.domain} />
          <button type="submit" name="action" value="join" className="btn btn-primary btn-lg btn-block">Join the selected organization</button>
        </form>
      )}
      <form method="post" action={s(p, 'action')} style={{ marginTop: 'var(--spacing-lg)' }}>
        <Hidden values={{ ...hidden, action: 'create' }} />
        {!orgs.length && <p className="form-text">No organization uses {s(p, 'domain')} yet.</p>}
        <button type="submit" className={`btn ${orgs.length ? 'btn-secondary' : 'btn-primary'} btn-lg btn-block`}>Create a new organization</button>
      </form>
      <p className="auth-footer"><a href={s(p, 'register')}>Back to email</a> · You can join or create more later, in Settings.</p>
    </>
  );
}

function RegisterOrg({ p }: { p: Props }) {
  const org = p.org as Org | null;
  const joining = !!s(p, 'org_id');
  const back = p.back as Link;
  return (
    <>
      <h1>{p.existing_user ? (joining ? 'Join the organization' : 'Create your organization') : 'Complete your registration'}</h1>
      <p className="lead">{p.existing_user ? '' : `Step 2 of 2: a password${joining ? '' : ' and your organization'}. `}Signed up as <strong>{s(p, 'email')}</strong>.</p>
      {org && <div className="alert alert-info"><span>You're joining <strong>{org.name}</strong> ({org.domain}). An owner approves you before you get in.</span></div>}
      <form method="post" action={s(p, 'action')}>
        <Hidden values={{ email: s(p, 'email'), domain: s(p, 'domain'), org_id: s(p, 'org_id'), existing_user: p.existing_user ? 'true' : '' }} />
        {!p.existing_user && (
          <>
            <Field name="password" label="Password" type="password" autoComplete="new-password" minLength={8} required help="At least 8 characters." />
            <Field name="confirm_password" label="Confirm password" type="password" autoComplete="new-password" required />
          </>
        )}
        {!joining && (
          <>
            <Field name="org_name" label="Organization name" required />
            <Field name="org_domain" label="Organization domain" placeholder="example.com" defaultValue={s(p, 'domain')} required
                   help="People with emails at this domain can find it and ask to join." />
            <Address />
          </>
        )}
        <button type="submit" className="btn btn-primary btn-lg btn-block">
          {joining ? (p.existing_user ? 'Ask to join' : 'Create account and ask to join') : (p.existing_user ? 'Create organization' : 'Create account')}
        </button>
      </form>
      <p className="auth-footer"><a href={back.href}>{back.label}</a></p>
    </>
  );
}

function SelectOrg({ p }: { p: Props }) {
  const orgs = (p.orgs as Org[]) ?? [];
  return (
    <>
      <h1>Choose an organization</h1>
      <p className="lead">The organization to work in. You can switch any time from the sidebar.</p>
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

function CreateOrg({ p }: { p: Props }) {
  return (
    <>
      <h1>Create an organization</h1>
      <p className="lead">Its own customers, templates and documents. You'll be its owner.</p>
      <form method="post" action={s(p, 'action')}>
        <Field name="org_name" label="Organization name" placeholder="Acme Engineering" required autoFocus />
        <Field name="org_domain" label="Domain" placeholder="acme.com" required help="People with emails at this domain can find it and ask to join." />
        <Address />
        <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <button type="submit" className="btn btn-primary">Create organization</button>
          <a href={s(p, 'cancel')} className="btn btn-secondary">Cancel</a>
        </div>
      </form>
    </>
  );
}

function JoinOrg({ p }: { p: Props }) {
  const orgs = (p.orgs as Org[]) ?? [];
  const domain = s(p, 'domain');
  const mine = s(p, 'user_domain');
  return (
    <>
      <h1>Join an organization</h1>
      <p className="lead">Find your company's organization by its domain{mine ? <>: yours is <strong>{mine}</strong></> : ''}. An owner approves you before you get in.</p>
      <form method="get" action={s(p, 'action')}>
        <Field name="domain" label="Domain" placeholder={mine || 'acme.com'} defaultValue={domain || mine} required autoFocus
               help={mine ? `You can join organizations at ${mine}.` : 'You can join organizations at your email\'s domain.'} />
        <button type="submit" className="btn btn-secondary">Search</button>
      </form>
      {domain && (orgs.length ? (
        <form method="post" action={s(p, 'action')} style={{ marginTop: 'var(--spacing-lg)' }}>
          <input type="hidden" name="domain" value={domain} />
          <OrgChoices orgs={orgs} sub={(o) => o.domain} />
          <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
            <button type="submit" className="btn btn-primary">Ask to join</button>
            <a href={s(p, 'cancel')} className="btn btn-secondary">Cancel</a>
          </div>
        </form>
      ) : (
        <p className="form-text" style={{ marginTop: 'var(--spacing-lg)' }}>No organization uses {domain}. <a href={s(p, 'create')}>Create one</a> instead.</p>
      ))}
    </>
  );
}

function PortalLogin({ p }: { p: Props }) {
  return (
    <>
      <h1>Customer portal</h1>
      <p className="lead">View and download the invoices your suppliers have sent you.</p>
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
  login: Login, register: Register, verify: Verify, choose_org: ChooseOrg, register_org: RegisterOrg,
  select_org: SelectOrg, create_org: CreateOrg, join_org: JoinOrg, portal_login: PortalLogin,
};

export function Public({ screen, props }: { screen: string; props: Props }) {
  const Draw = SCREENS[screen];
  return Draw ? <Draw p={props} /> : <p className="error" role="alert">There's nothing at this address.</p>;
}
