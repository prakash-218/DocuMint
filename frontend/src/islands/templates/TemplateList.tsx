import { PageHeader } from '../../app/PageHeader';
import { EmptyState, Loading, Pager, useLoad, type PageInfo } from '../../app/ui';
import { Icon } from '../../icons';

// The templates as cards (GET /api/templates, template_view.cards), the most used first: what they're for, their
// columns and how many documents use them. ?include_archived=true shows the archived ones too.

interface Data {
  title: string;
  archived: boolean;
  toggle: { href: string; label: string };
  new: string | null;
  cards: { url: string; name: string; archived: boolean; currency: string; version: number; used_for: string;
           sections: { title: string; items: boolean; columns: string[] }[]; used: number }[];
  page: PageInfo;
}

function Cards({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title}
                  actions={<>
                    <a href={data.toggle.href} className="btn btn-ghost"><span className="btn-label">{data.toggle.label}</span></a>
                    {data.new && <a href={data.new} className="btn btn-primary"><Icon name="plus" /><span className="btn-label">New template</span></a>}
                  </>} />
      {data.cards.length ? (
        <>
          <div className="template-grid">
            {data.cards.map((t) => (
              <a key={t.url} className={`card template-card${t.archived ? ' archived' : ''}`} href={t.url}>
                <div className="flex-between" style={{ flexWrap: 'nowrap', alignItems: 'flex-start' }}>
                  <h3>{t.name}</h3>
                  <span className={`badge ${t.archived ? 'badge-warning' : 'badge-secondary'}`}>{t.archived ? 'Archived' : t.currency}</span>
                </div>
                <p className="template-used-for">For {t.used_for}</p>
                {t.sections.length ? t.sections.map((s) => (
                  <div key={s.title}>
                    <div className="text-tertiary" style={{ fontSize: 'var(--font-size-xs)', marginBottom: 4 }}>{s.title}{s.items ? ' · line items' : ''}</div>
                    <div className="template-columns">{s.columns.map((c, i) => <span key={i}>{c}</span>)}</div>
                  </div>
                )) : <p className="text-tertiary" style={{ margin: 0 }}>No fields yet</p>}
                <div className="meta">
                  <span>v{t.version}</span>
                  <span>{t.used ? `Used by ${t.used} document${t.used === 1 ? '' : 's'}` : 'Not used yet'}</span>
                </div>
              </a>
            ))}
          </div>
          <Pager page={data.page} />
        </>
      ) : (
        <div className="card">
          <EmptyState icon="file" title="No templates yet"
                      action={data.new ? { href: data.new, label: 'New template' } : null} />
        </div>
      )}
    </>
  );
}

export default function TemplateList({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/templates${search}`, "Couldn't load the templates. Check your connection.");
  return data ? <Cards data={data} /> : <Loading title="Templates" kind="list" error={error} />;
}
