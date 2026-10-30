import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { api, ApiError } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { Icon } from '../../icons';

// The roles (GET /api/settings/roles, roles_view.listing): the built-in ones and the organization's own. A role of its
// own is a set of permissions, edited by area (GET /api/settings/roles/<id> or /new, roles_view.editor) and saved
// through the API. Nobody gives a permission their own role doesn't have: those boxes can't be ticked.

interface Listing {
  title: string;
  built_in: { key: string; name: string; summary: string; members: number; permissions: number; copy: string | null }[];
  custom: { id: string; name: string; description: string; members: number; permissions: number; url: string; editable: boolean }[];
  new: string;
  back: string;
}

interface Permission {
  name: string;
  label: string;
  needs: string[];
  yours: boolean;
}

interface Editor {
  title: string;
  role: { id: string | null; name: string; description: string; permissions: string[]; members: number };
  catalog: { key: string; label: string; permissions: Permission[] }[];
  editable: boolean;
  save: string;
  method: 'POST' | 'PATCH';
  delete: string | null;
  back: string;
}

const people = (n: number) => (n === 1 ? '1 person' : `${n} people`);
const CRUMBS = [{ label: 'Settings', href: '/settings/' }];

export function RolesView({ data }: { data: Listing }) {
  const notice = (useLocation().state as { notice?: string } | null)?.notice;
  return (
    <>
      <PageHeader title={data.title} crumbs={[...CRUMBS, { label: 'Roles' }]}
                  actions={<a href={data.new} className="btn btn-primary btn-sm"><Icon name="plus" />New role</a>} />
      <div className="panel-medium stack" style={{ maxWidth: 880 }}>
        {notice && <div className="alert alert-success" role="status">{notice}</div>}
        <section className="card">
          <div className="card-header"><h2 className="card-title">Your roles</h2></div>
          {data.custom.length ? (
            <ul className="pick-list">
              {data.custom.map((r) => (
                <li key={r.id}>
                  <a href={r.url}>
                    <span className="pick-main">
                      <span className="pick-title">{r.name}</span>
                      <span className="pick-sub">{r.description ? `${r.description} · ` : ''}{r.permissions} permissions · {people(r.members)}</span>
                    </span>
                    <Icon name="chevronRight" />
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <div className="card-body">
              <p className="text-tertiary">No roles of your own yet. Make one from scratch, or copy a built-in role below and change it.</p>
            </div>
          )}
        </section>
        <section className="card">
          <div className="card-header"><h2 className="card-title">Built-in roles</h2></div>
          <ul className="member-list">
            {data.built_in.map((r) => (
              <li key={r.key}>
                <div className="pick-main">
                  <span className="pick-title">{r.name}</span>
                  <span className="pick-sub">{r.summary}. {people(r.members)}.</span>
                </div>
                {r.copy && <a href={r.copy} className="btn btn-ghost btn-sm">Copy</a>}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}

export function Roles() {
  const { data, error } = useLoad<Listing>('/api/settings/roles', "Couldn't load the roles. Check your connection.");
  return data ? <RolesView data={data} /> : <Loading title="Roles" kind="list" error={error} />;
}

/** Ticking a permission ticks what it needs; unticking one unticks what needs it */
export function toggle(chosen: Set<string>, perm: Permission, on: boolean, all: Permission[]): Set<string> {
  const next = new Set(chosen);
  if (on) {
    next.add(perm.name);
    perm.needs.forEach((n) => next.add(n));
  } else {
    next.delete(perm.name);
    all.filter((p) => p.needs.includes(perm.name)).forEach((p) => next.delete(p.name));
  }
  return next;
}

export function RoleForm({ data }: { data: Editor }) {
  const navigate = useNavigate();
  const [name, setName] = useState(data.role.name);
  const [description, setDescription] = useState(data.role.description);
  const [chosen, setChosen] = useState(() => new Set(data.role.permissions));
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const all = data.catalog.flatMap((a) => a.permissions);
  const locked = !data.editable;

  async function run(work: () => Promise<unknown>, notice: string) {
    setBusy(true);
    try {
      await work();
      navigate(data.back, { state: { notice } });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong. Nothing was changed.');
      setBusy(false);
    }
  }

  function save(e: FormEvent) {
    e.preventDefault();
    const body = { name, description, permissions: [...chosen].sort() };
    void run(() => (data.method === 'PATCH' ? api.patch(data.save, body) : api.post(data.save, body)), `${name.trim()} saved`);
  }

  function remove() {
    if (data.delete && window.confirm(`Delete the role ${data.role.name}?`)) {
      void run(() => api.del(data.delete!), `${data.role.name} deleted`);
    }
  }

  return (
    <>
      <PageHeader title={data.title} crumbs={[...CRUMBS, { label: 'Roles', href: data.back }, { label: data.role.id ? data.role.name : 'New role' }]} />
      <form className="card panel-medium" style={{ maxWidth: 880 }} onSubmit={save}>
        <div className="card-body">
          {locked && <div className="alert alert-warning">This role has more than your own role does, so you can't change it.</div>}
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="role-name" className="form-label">Name *</label>
              <input id="role-name" className="form-input" required maxLength={60} value={name} disabled={locked}
                     onChange={(e) => setName(e.target.value)} autoFocus={!data.role.id} />
            </div>
            <div className="form-group">
              <label htmlFor="role-description" className="form-label">What it's for</label>
              <input id="role-description" className="form-input" maxLength={255} value={description} disabled={locked}
                     placeholder="Prices jobs and sends quotations" onChange={(e) => setDescription(e.target.value)} />
            </div>
          </div>
          {data.role.id && <p className="form-text">{people(data.role.members)} {data.role.members === 1 ? 'has' : 'have'} this role. Changes apply to them at once.</p>}
          <h3 className="perm-heading">What it lets someone do</h3>
          <div className="perm-areas">
            {data.catalog.map((area) => (
              <fieldset key={area.key} className="perm-area">
                <legend>{area.label}</legend>
                {area.permissions.map((p) => (
                  <label key={p.name} className={`form-check${p.yours ? '' : ' unavailable'}`}
                         title={p.yours ? undefined : "Your role doesn't have this, so you can't give it"}>
                    <input type="checkbox" className="form-checkbox" checked={chosen.has(p.name)} disabled={locked || !p.yours}
                           onChange={(e) => setChosen(toggle(chosen, p, e.target.checked, all))} />
                    <span>{p.label}</span>
                  </label>
                ))}
              </fieldset>
            ))}
          </div>
          {!locked && (
            <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <button type="submit" className="btn btn-primary" disabled={busy}>{data.role.id ? 'Save' : 'Make role'}</button>
              <a href={data.back} className="btn btn-secondary">Cancel</a>
              {data.delete && (
                <button type="button" className="btn btn-ghost" style={{ marginLeft: 'auto' }} disabled={busy} onClick={remove}>
                  <Icon name="trash" />Delete
                </button>
              )}
            </div>
          )}
        </div>
      </form>
    </>
  );
}

/** /settings/roles/new (?from=member) and /settings/roles/<id> */
export function RoleEditor({ roleId, search }: { roleId: string | null; search: string }) {
  const path = roleId ? `/api/settings/roles/${roleId}` : `/api/settings/roles/new${search}`;
  const { data, error } = useLoad<Editor>(path, "Couldn't load the role. Check your connection.");
  return data ? <RoleForm data={data} /> : <Loading title="Role" kind="page" error={error} />;
}

export default Roles;
