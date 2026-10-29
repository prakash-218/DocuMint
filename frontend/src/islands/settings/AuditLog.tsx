import { PageHeader } from '../../app/PageHeader';
import { EmptyState, Filters, Loading, Pager, useLoad, type Filter, type PageInfo } from '../../app/ui';
import { Icon, type IconName } from '../../icons';

// Who changed what (GET /api/settings/audit-log, settings_view.audit), newest first, one kind of change at a time.

interface Data {
  title: string;
  filters: Filter[];
  entries: { icon: string; title: string; detail: string; sub: string; url: string | null; at: string }[];
  page: PageInfo;
}

/** app_helpers.describe_audit's icon, from the few the app draws */
const ICONS: Record<string, IconName> = { banknote: 'rupee', 'user-cog': 'users', users: 'users', history: 'history' };

function Log({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title} />
      <Filters filters={data.filters} />
      <div className="card">
        {data.entries.length ? (
          <>
            <ul className="member-list audit-list">
              {data.entries.map((e, i) => (
                <li key={i}>
                  <span className="file-icon"><Icon name={ICONS[e.icon] ?? 'file'} /></span>
                  <div className="pick-main" style={{ flex: 1 }}>
                    <span className="pick-title">
                      {e.url ? <a href={e.url}>{e.title}</a> : e.title}
                      {e.detail && <span className="text-secondary"> · {e.detail}</span>}
                    </span>
                    {e.sub && <span className="pick-sub">{e.sub}</span>}
                  </div>
                  <span className="text-tertiary audit-when">{e.at}</span>
                </li>
              ))}
            </ul>
            <Pager page={data.page} />
          </>
        ) : <EmptyState icon="history" title="Nothing here yet" />}
      </div>
    </>
  );
}

export default function AuditLog({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/settings/audit-log${search}`, "Couldn't load the audit log. Check your connection.");
  return data ? <Log data={data} /> : <Loading title="Audit log" kind="list" error={error} />;
}
