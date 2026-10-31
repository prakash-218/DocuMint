import { Dropdown, choices } from '../../mantine/Dropdown';
import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { ask, Loading, useLoad } from '../../app/ui';
import { day } from '../../format';
import { Icon } from '../../icons';

// The settings page (GET /api/settings, settings_view.index): its links, and for those who manage the team its invites
// (DocuMint is invite-only: invites.py), any old requests to join, and the team; for everyone the organizations they're in. The team's forms post to settings_bp.approve_member
// (a role is a built-in one's name or a custom one's id: roles they may give), switching posts to settings_bp.select_org.

interface Data {
  title: string;
  links: { title: string; sub: string; href: string }[];
  team: string;
  roles: [string, string][];          // [value, label]: the roles they may give
  requests: { user_id: string; email: string; asked: string | null }[];
  members: { user_id: string; email: string; role: string; role_label: string; status: string; you: boolean; manage: boolean;
             reset: string | null }[];
  /** Inviting someone (api_bp.invite_create), for those who manage the team. */
  invite: string | null;
  invites: Invite[];
  orgs: { id: string; name: string; domain: string; role: string; current: boolean }[];
  switch: string;
}

export interface Invite { id: string; email: string; role_label: string; sent: string | null; expires: string | null; expired: boolean;
                          by: string; again: string; cancel: string }

/** What came back from inviting or a reset link: the link (shown once), and whether it went by email. */
interface Sent { link: string; emailed: boolean; to: string; what: 'invite' | 'reset' }

const title = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function Requests({ data }: { data: Data }) {
  return (
    <section className="card">
      <div className="card-header"><h2 className="card-title">Requests to join</h2><span className="badge badge-warning">{data.requests.length}</span></div>
      <ul className="member-list">
        {data.requests.map((r) => (
          <li key={r.user_id}>
            <div className="pick-main"><span className="pick-title">{r.email}</span><span className="pick-sub">Asked {day(r.asked)}</span></div>
            <div className="member-actions">
              <form id={`approve-form-${r.user_id}`} action={data.team} method="post">
                <input type="hidden" name="user_id" value={r.user_id} />
                <label className="sr-only" htmlFor={`role-${r.user_id}`}>Role</label>
                <Dropdown id={`role-${r.user_id}`} name="role" size="xs" data={choices(data.roles)}
                          defaultValue={data.roles.some(([value]) => value === 'member') ? 'member' : data.roles[0]?.[0]} />
              </form>
              <button type="submit" form={`approve-form-${r.user_id}`} name="action" value="approve" className="btn btn-primary btn-sm">Approve</button>
              <form action={data.team} method="post" onSubmit={ask(`Reject ${r.email}?`)}>
                <input type="hidden" name="user_id" value={r.user_id} />
                <button type="submit" name="action" value="reject" className="btn btn-ghost btn-sm">Reject</button>
              </form>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** The link just made: emailed or not, to copy or send on WhatsApp. It isn't shown again. */
function SentLink({ sent, onDone }: { sent: Sent; onDone: () => void }) {
  const [copied, setCopied] = useState(false);
  const what = sent.what === 'invite' ? 'invite' : 'link to set a new password';
  const text = sent.what === 'invite' ? `You're invited to our DocuMint. Open this link to set your password: ${sent.link}`
    : `Here's a link to set a new DocuMint password (it works once, for 2 hours): ${sent.link}`;
  return (
    <div className="sent-link" role="status">
      <p>{sent.emailed ? <>Emailed the {what} to <strong>{sent.to}</strong>.</>
        : <>The {what} for <strong>{sent.to}</strong> wasn't emailed: this organization has no mailbox to send from.</>}</p>
      <div className="sent-link-row">
        <input className="form-input mono" readOnly value={sent.link} aria-label="The link" onFocus={(e) => e.target.select()} />
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => {
          navigator.clipboard?.writeText(sent.link).then(() => setCopied(true), () => undefined);
        }}>{copied ? 'Copied' : 'Copy'}</button>
        <a className="btn btn-secondary btn-sm" href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer">WhatsApp</a>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onDone}>Done</button>
      </div>
    </div>
  );
}

function Invites({ data, sent, onSent }: { data: Data; sent: Sent | null; onSent: (s: Sent | null) => void }) {
  const [invites, setInvites] = useState(data.invites);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const refresh = () => api.get<Data>('/api/settings').then((d) => setInvites(d.invites)).catch(() => undefined);

  async function run(go: () => Promise<Sent | null>) {
    setError('');
    setBusy(true);
    try {
      const done = await go();
      if (done) onSent(done);
      await refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't work. Check your connection.");
    } finally {
      setBusy(false);
    }
  }

  function invite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const values = Object.fromEntries(new FormData(form)) as Record<string, string>;
    void run(async () => {
      const r = await api.post<Omit<Sent, 'what'>>(data.invite!, { email: values.email, role: values.role });
      form.reset();
      return { ...r, what: 'invite' };
    });
  }

  return (
    <section className="card">
      <div className="card-header"><h2 className="card-title">Invite someone</h2></div>
      <div className="card-body stack">
        <form className="invite-form" onSubmit={invite}>
          <div className="form-group">
            <label htmlFor="invite-email" className="form-label">Email</label>
            <input id="invite-email" name="email" type="email" className="form-input" required placeholder="name@company.com" />
          </div>
          <div className="form-group">
            <label htmlFor="invite-role" className="form-label">Role</label>
            <Dropdown id="invite-role" name="role" data={choices(data.roles)}
                      defaultValue={data.roles.some(([value]) => value === 'member') ? 'member' : data.roles[0]?.[0]} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy}><Icon name="userPlus" />Invite</button>
        </form>
        {error && <p className="error" role="alert">{error}</p>}
        {sent && <SentLink sent={sent} onDone={() => onSent(null)} />}
        {invites.length > 0 && (
          <ul className="member-list" aria-label="Invites not used yet">
            {invites.map((i) => (
              <li key={i.id}>
                <div className="pick-main">
                  <span className="pick-title">{i.email}</span>
                  <span className="pick-sub">{i.role_label} · {i.expired ? 'Expired' : `Invited ${day(i.sent)}, until ${day(i.expires)}`}{i.by && ` · by ${i.by}`}</span>
                </div>
                <div className="member-actions">
                  <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                          onClick={() => void run(async () => ({ ...await api.post<Omit<Sent, 'what'>>(i.again, {}), what: 'invite' }))}>Send again</button>
                  <button type="button" className="btn btn-ghost btn-sm" disabled={busy}
                          onClick={() => { if (window.confirm(`Cancel the invite for ${i.email}?`)) void run(async () => { await api.del(i.cancel); return null; }); }}>Cancel</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function Team({ data, onSent }: { data: Data; onSent: (s: Sent) => void }) {
  const [error, setError] = useState('');
  async function reset(m: Data['members'][number]) {
    setError('');
    try {
      onSent({ ...await api.post<Omit<Sent, 'what'>>(m.reset!, {}), what: 'reset' });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't work. Check your connection.");
    }
  }
  return (
    <section className="card">
      <div className="card-header"><h2 className="card-title">Team</h2></div>
      {error && <p className="error" role="alert" style={{ margin: 'var(--spacing-md)' }}>{error}</p>}
      <ul className="member-list">
        {data.members.map((m) => (
          <li key={m.user_id}>
            <div className="pick-main">
              <span className="pick-title">{m.email}{m.you && <span className="text-tertiary"> (you)</span>}</span>
              <span className="pick-sub">{m.role_label}{m.status !== 'active' && ` · ${title(m.status)}`}</span>
            </div>
            {m.manage && (
              <div className="member-actions">
                <form action={data.team} method="post">
                  <input type="hidden" name="user_id" value={m.user_id} />
                  <input type="hidden" name="action" value="change_role" />
                  <label className="sr-only" htmlFor={`mrole-${m.user_id}`}>Role</label>
                  <Dropdown id={`mrole-${m.user_id}`} name="role" size="xs" defaultValue={m.role} submitOnChange data={choices(data.roles)} />
                </form>
                {m.reset && (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => void reset(m)}>Password link</button>
                )}
                <form action={data.team} method="post" onSubmit={m.status === 'active' ? ask(`Deactivate ${m.email}?`) : undefined}>
                  <input type="hidden" name="user_id" value={m.user_id} />
                  {m.status === 'active'
                    ? <button type="submit" name="action" value="deactivate" className="btn btn-ghost btn-sm">Deactivate</button>
                    : <button type="submit" name="action" value="reactivate" className="btn btn-secondary btn-sm">Reactivate</button>}
                </form>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function SettingsView({ data }: { data: Data }) {
  const [sent, setSent] = useState<Sent | null>(null);
  return (
    <>
      <PageHeader title={data.title} />
      <div className="panel-medium stack" style={{ maxWidth: 880 }}>
        {data.links.length > 0 && (
          <section className="card">
            <ul className="pick-list">
              {data.links.map((l) => (
                <li key={l.href}>
                  <a href={l.href}>
                    <span className="pick-main"><span className="pick-title">{l.title}</span>{l.sub && <span className="pick-sub">{l.sub}</span>}</span>
                    <Icon name="chevronRight" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
        {data.invite && <Invites data={data} sent={sent} onSent={setSent} />}
        {data.requests.length > 0 && <Requests data={data} />}
        {data.members.length > 0 && <Team data={data} onSent={setSent} />}
        <section className="card">
          <div className="card-header"><h2 className="card-title">Organizations</h2></div>
          <ul className="member-list">
            {data.orgs.map((o) => (
              <li key={o.id}>
                <div className="pick-main">
                  <span className="pick-title">{o.name}{o.current && <> <span className="badge badge-info">Current</span></>}</span>
                  <span className="pick-sub">{[o.domain, o.role].filter(Boolean).join(' · ')}</span>
                </div>
                {!o.current && (
                  <form method="post" action={data.switch}>
                    <input type="hidden" name="org_id" value={o.id} />
                    <button type="submit" className="btn btn-secondary btn-sm">Switch</button>
                  </form>
                )}
              </li>
            ))}
            {!data.orgs.length && <li><span className="text-tertiary">Not a member of any organization yet.</span></li>}
          </ul>
        </section>
      </div>
    </>
  );
}

export default function Settings() {
  const { data, error } = useLoad<Data>('/api/settings', "Couldn't load the settings. Check your connection.");
  return data ? <SettingsView data={data} /> : <Loading title="Settings" kind="page" error={error} />;
}
