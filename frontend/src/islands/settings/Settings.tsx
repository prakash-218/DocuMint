import { PageHeader } from '../../app/PageHeader';
import { ask, Loading, useLoad } from '../../app/ui';
import { day } from '../../format';
import { Icon } from '../../icons';

// The settings page (GET /api/settings, settings_view.index): for owners and admins its links, the requests to join
// and the team; for everyone the organizations they're in. The team's forms post to settings_bp.approve_member,
// switching posts to settings_bp.select_org.

interface Data {
  title: string;
  links: { title: string; sub: string; href: string }[];
  team: string;
  roles: [string, string][];
  requests: { user_id: string; email: string; asked: string | null }[];
  members: { user_id: string; email: string; role: string; status: string; you: boolean }[];
  orgs: { id: string; name: string; domain: string; role: string; current: boolean }[];
  switch: string;
  join: string;
  create: string;
}

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
                <select id={`role-${r.user_id}`} name="role" className="form-select form-select-sm" defaultValue="member">
                  {data.roles.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
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

function Team({ data }: { data: Data }) {
  return (
    <section className="card">
      <div className="card-header"><h2 className="card-title">Team</h2></div>
      <ul className="member-list">
        {data.members.map((m) => (
          <li key={m.user_id}>
            <div className="pick-main">
              <span className="pick-title">{m.email}{m.you && <span className="text-tertiary"> (you)</span>}</span>
              <span className="pick-sub">{title(m.role)}{m.status !== 'active' && ` · ${title(m.status)}`}</span>
            </div>
            {!m.you && (
              <div className="member-actions">
                <form action={data.team} method="post">
                  <input type="hidden" name="user_id" value={m.user_id} />
                  <input type="hidden" name="action" value="change_role" />
                  <label className="sr-only" htmlFor={`mrole-${m.user_id}`}>Role</label>
                  <select id={`mrole-${m.user_id}`} name="role" className="form-select form-select-sm" defaultValue={m.role}
                          onChange={(e) => e.currentTarget.form?.requestSubmit()}>
                    {data.roles.map(([value]) => <option key={value} value={value}>{title(value)}</option>)}
                  </select>
                </form>
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
                    <span className="pick-main"><span className="pick-title">{l.title}</span><span className="pick-sub">{l.sub}</span></span>
                    <Icon name="chevronRight" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
        {data.requests.length > 0 && <Requests data={data} />}
        {data.members.length > 0 && <Team data={data} />}
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Organizations</h2>
            <div className="btn-group">
              <a href={data.join} className="btn btn-ghost btn-sm">Join</a>
              <a href={data.create} className="btn btn-secondary btn-sm"><Icon name="plus" />New</a>
            </div>
          </div>
          <ul className="member-list">
            {data.orgs.map((o) => (
              <li key={o.id}>
                <div className="pick-main">
                  <span className="pick-title">{o.name}{o.current && <> <span className="badge badge-info">Current</span></>}</span>
                  <span className="pick-sub">{o.domain} · {title(o.role)}</span>
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
