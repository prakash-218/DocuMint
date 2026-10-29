import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { Icon } from '../../icons';
import { CustomerOptions } from './Editor';
import type { ProjectStep as ProjectData, TemplateLink, TemplateStep as TemplateData } from './types';

// The steps before a new document's editor, as the server pages drew them: the project it's for (one of the open
// ones, or a new one), then its template.

interface Option { id: string; no: string; title: string; customer: string; site: string; reference: string; fy: string }

/** Every word typed is found in the project's number, name, customer, site or reference. */
function matches(p: Option, query: string): boolean {
  const hay = [p.no, p.title, p.customer, p.site, p.reference, p.fy].join(' ').toLowerCase();
  return query.toLowerCase().split(/\s+/).filter(Boolean).every((w) => hay.includes(w));
}

export function ProjectStep({ data }: { data: ProjectData }) {
  const [options, setOptions] = useState<Option[] | null>(null);
  const [query, setQuery] = useState('');
  useEffect(() => {
    if (!data.has_open_projects) return;
    api.get<{ projects: Option[] }>(data.options).then((d) => setOptions(d.projects)).catch(() => setOptions([]));
  }, [data.options, data.has_open_projects]);
  const shown = useMemo(() => (options ?? []).filter((p) => matches(p, query)).slice(0, 12), [options, query]);
  const customer = new URLSearchParams(window.location.search).get('customer_id') ?? '';
  return (
    <>
      <PageHeader title={data.title} heading />
      <div className="panel-medium" style={{ maxWidth: 760 }}>
        <section className="card">
          <div className="card-header"><div><h2 className="card-title">Choose a project</h2></div></div>
          <div className="card-body">
            {!data.has_open_projects ? <p className="text-tertiary" style={{ margin: 0 }}>No open projects yet.</p> : (
              <div className="project-picker">
                <div className="pp-bar">
                  <div className="search-input pp-search">
                    <Icon name="search" />
                    <input type="search" className="form-input pp-query" placeholder="Search projects by name, number or customer" autoComplete="off"
                           aria-label="Search projects" value={query} onChange={(e) => setQuery(e.target.value)} />
                  </div>
                </div>
                <ul className="pp-list" aria-label="Projects">
                  {options === null ? <li className="pp-empty">Loading projects…</li>
                    : !shown.length ? <li className="pp-empty">No open project matches.</li>
                    : shown.map((p) => (
                      <li key={p.id} className="pp-option" style={{ padding: 0 }}>
                        <a href={data.open_url.replace('__ID__', p.id)} style={{ display: 'flex', flex: 1, padding: '8px 12px', color: 'inherit', textDecoration: 'none' }}>
                          <span className="pp-main"><span className="pp-title">{p.no} · {p.title}</span>
                            <span className="pp-sub">{[p.site ? `${p.customer} · ${p.site}` : p.customer, p.fy && `FY ${p.fy}`].filter(Boolean).join(' · ')}</span></span>
                        </a>
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </div>
        </section>
        <section className="card">
          <div className="card-header"><h2 className="card-title">New project</h2></div>
          <form method="post" action={data.new_project.action} className="card-body">
            <input type="hidden" name="next" value={data.new_project.next} />
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="np-customer" className="form-label">Customer</label>
                <select id="np-customer" name="customer_id" className="form-select" required defaultValue={customer}>
                  <option value="">Select a customer</option>
                  <CustomerOptions groups={data.new_project.customers} />
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="np-title" className="form-label">Project name</label>
                <input type="text" id="np-title" name="title" className="form-input" required maxLength={200} placeholder="Drill jig for bracket" />
              </div>
            </div>
            {data.new_project.add_customer && <p className="form-text"><a href={data.new_project.add_customer}>Add a customer</a> first.</p>}
            <button type="submit" className="btn btn-primary">Create project and continue</button>
          </form>
        </section>
      </div>
    </>
  );
}

function Links({ list }: { list: TemplateLink[] }) {
  return (
    <ul className="pick-list">
      {list.map((t) => (
        <li key={t.href}>
          <a href={t.href}>
            <span className="pick-main"><span className="pick-title">{t.name}</span><span className="pick-sub">{t.currency}</span></span>
            <Icon name="chevronRight" />
          </a>
        </li>
      ))}
    </ul>
  );
}

export function TemplateStep({ data }: { data: TemplateData }) {
  const p = data.project;
  return (
    <>
      <PageHeader title={data.title} heading
                  description={p && <><a href={p.url}>{p.label} · {p.title}</a> · {p.customer_name}</>} />
      <div className="panel-medium" style={{ maxWidth: 760 }}>
        {data.missing && <p className="error" role="alert">That template isn't there any more. Choose another.</p>}
        <section className="card">
          <div className="card-header"><h2 className="card-title">Choose a template</h2></div>
          {data.templates.length ? (
            <>
              <Links list={data.templates} />
              {data.others.length > 0 && (
                <details className="other-templates">
                  <summary>Other templates ({data.others.length}), made for other document types</summary>
                  <Links list={data.others} />
                </details>
              )}
            </>
          ) : (
            <div className="empty-state">
              <h3>No templates yet</h3>
              <p>Add the ready-made templates from Settings, or build your own.</p>
              <a href={data.templates_page} className="btn btn-primary">Templates</a>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
