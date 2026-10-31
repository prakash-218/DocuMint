import { PageHeader } from '../../app/PageHeader';
import { EmptyState, Filters, Loading, Pager, useLoad } from '../../app/ui';
import { when } from '../../format';
import { Icon } from '../../icons';
import type { Inbox as Data } from './types';

// The emails synced from the mailboxes, newest thread first: the ones not in a project yet, or all of them.

function InboxView({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title} heading description={data.accounts}
                  actions={data.sync && (
                    <form method="post" action={data.sync}>
                      <button type="submit" className="btn btn-secondary"><Icon name="refresh" /><span className="btn-label">Sync now</span></button>
                    </form>
                  )} />
      {data.problems.map((p) => <div key={p} className="alert alert-warning"><span>{p}</span></div>)}
      <Filters filters={data.filters} />
      <div className="card">
        {data.threads.length ? (
          <>
            <ul className="pick-list thread-list">
              {data.threads.map((t) => (
                <li key={t.id}>
                  <a href={t.url}>
                    <span className="pick-main">
                      <span className="pick-title">{t.subject}{t.count > 1 && <span className="text-tertiary"> ({t.count})</span>}</span>
                      <span className="pick-sub">
                        {t.from}{t.customer && ` · ${t.customer}`}{t.project && ` · ${t.project}`}
                        {t.files > 0 && <> · <Icon name="paperclip" size={12} className="inline-icon" />{t.files}</>}
                      </span>
                      {t.snippet && <span className="thread-snippet">{t.snippet}</span>}
                    </span>
                    <span className="text-tertiary thread-when">{when(t.when)}</span>
                  </a>
                </li>
              ))}
            </ul>
            <Pager page={data.page} />
          </>
        ) : <EmptyState icon="mail" title={data.empty} />}
      </div>
    </>
  );
}

export default function Inbox({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/emails${search}`, "Couldn't load the emails. Check your connection.");
  return data ? <InboxView data={data} /> : <Loading title="Emails" kind="list" error={error} heading />;
}
