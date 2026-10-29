import { PageHeader } from '../../app/PageHeader';
import { EmptyState, Filters, Loading, Pager, useLoad, type Filter, type PageInfo } from '../../app/ui';
import { when } from '../../format';
import { Icon, type IconName } from '../../icons';

// What happened on projects (GET /api/notifications, notifications_view.build): unread, or all. Opening one goes
// through notifications_bp.open_notification, which marks it read and goes where it points.

interface Data {
  title: string;
  unread_only: boolean;
  mark_read: string | null;
  filters: Filter[];
  items: { id: string; url: string; title: string; sub: string; kind: string; unread: boolean; when: string | null }[];
  page: PageInfo;
  empty: string;
}

/** The kind's icon, from the few the app draws (the server pages' event_icon has more) */
export function eventIcon(kind: string): IconName {
  if (kind === 'payment') return 'rupee';
  if (kind === 'file_uploaded') return 'paperclip';
  if (kind === 'email_sent') return 'send';
  if (kind === 'email_received') return 'mail';
  if (kind === 'note') return 'note';
  if (kind === 'project_created') return 'briefcase';
  if (kind === 'document_corrected') return 'pencil';
  if (kind.startsWith('quote_') || kind.startsWith('document_')) return 'file';
  return kind === 'project_status' ? 'flag' : 'bell';
}

function List({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title}
                  actions={data.mark_read && (
                    <form method="post" action={data.mark_read}>
                      <button type="submit" className="btn btn-secondary"><Icon name="checkCheck" /><span className="btn-label">Mark all read</span></button>
                    </form>
                  )} />
      <Filters filters={data.filters} />
      <div className="card">
        {data.items.length ? (
          <>
            <ul className="member-list audit-list">
              {data.items.map((n) => (
                <li key={n.id} className={n.unread ? 'is-unread' : undefined}>
                  <span className="file-icon"><Icon name={eventIcon(n.kind)} /></span>
                  <div className="pick-main" style={{ flex: 1 }}>
                    <a href={n.url} className="pick-title">{n.title}</a>
                    <span className="pick-sub">{n.sub}</span>
                  </div>
                  <time className="text-tertiary audit-when" dateTime={n.when ?? undefined}>{when(n.when)}</time>
                </li>
              ))}
            </ul>
            <Pager page={data.page} />
          </>
        ) : <EmptyState icon="bell" title={data.empty} />}
      </div>
    </>
  );
}

export default function Notifications({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/notifications${search}`, "Couldn't load the notifications. Check your connection.");
  return data ? <List data={data} /> : <Loading title="Notifications" kind="list" error={error} />;
}
