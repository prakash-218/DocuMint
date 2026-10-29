import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { Composer } from '../EmailComposer';
import { Documents } from './Documents';
import { MoneyStrip, NextStep, Tracker } from './Overview';
import { People, type ContactFields } from './People';
import { Costings, Details, Files, type DetailFields } from './Side';
import { Timeline } from './Timeline';
import type { Page } from './types';

// The new project page: where the job is (worked out from its documents), what to do next, the money, the
// documents from quotation to payment, one timeline, and the people, files and details beside them.

export default function ProjectPage({ projectId }: { projectId: string }) {
  const [page, setPage] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [compose, setCompose] = useState<{ invoiceId?: string | null; threadId?: string | null } | null>(null);
  const base = `/api/projects/${projectId}`;

  const load = useCallback(async () => {
    try {
      setPage(await api.get<Page>(base));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't load the project. Check your connection.");
    }
  }, [base]);

  useEffect(() => {
    void load();
  }, [load]);

  /** Make a change, then show the page as it is now. False (and the reason shown) when it didn't work. */
  async function change(run: () => Promise<unknown>, done: string): Promise<boolean> {
    try {
      await run();
      setError('');
      setNotice(done);
      await load();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong. Nothing was changed.');
      return false;
    }
  }

  if (!page) {
    return <div className="ui">{error ? <p className="error" role="alert">{error}</p> : <p className="loading">Loading the project…</p>}</div>;
  }

  const { can, project } = page;
  return (
    <div className="ui">
      {error && (
        <div className="error" role="alert">
          <span>{error}</span>
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setError('')}>Dismiss</button>
        </div>
      )}

      <header className="head">
        <div>
          <h1>{project.title}</h1>
          <div className="meta">
            <span className="mono">{project.label}</span>
            <a href={project.customer.url}>{project.customer.name}{project.customer.site ? ` · ${project.customer.site}` : ''}</a>
            <span>FY {project.fiscal_year}</span>
            {project.reference && <span>Ref. {project.reference}</span>}
            {project.status !== 'open' && <span>{page.statuses[project.status]}</span>}
          </div>
        </div>
        <div className="head-right"><span className={`pill tone-${page.stage.pill.tone}`}>{page.stage.pill.text}</span></div>
      </header>

      <Tracker steps={page.stage.steps} />
      <NextStep next={page.next} onEmail={(invoiceId) => setCompose({ invoiceId })}
                onStatus={(status) => void change(() => api.patch(base, { status }), `Project marked ${page.statuses[status]?.toLowerCase()}`)} />
      <MoneyStrip rows={page.money} quotedOnly={can.sales} />

      <div className="cols">
        <div className="col-main">
          <Documents docs={page.documents} newDocument={page.new_document} canEdit={can.edit} sales={can.sales} current={page.stage.current}
                     onEmail={(invoiceId) => setCompose({ invoiceId })} />
          <Timeline items={page.timeline} canEdit={can.edit} readMail={can.read_mail}
                    onNote={(text) => change(() => api.post(`${base}/notes`, { text }), 'Note added')}
                    onReply={(threadId) => setCompose({ threadId })}
                    onEmail={can.edit ? () => setCompose({}) : undefined} />
        </div>
        <aside className="col-side" aria-label="People, files and details">
          <People page={page}
                  onGets={(contactId, gets) => void change(() => api.post(`${base}/people`, { contact_id: contactId, gets }), 'Saved')}
                  onSave={(fields: ContactFields) => change(() => api.post(`${base}/contacts`, fields),
                                                            fields.contact_id ? `${fields.name} saved` : `${fields.name || fields.email} added`)}
                  onIgnore={(value) => void change(() => api.post(`${base}/ignore`, { value }), "It won't be suggested again")} />
          <Files page={page} />
          {page.costings && <Costings costings={page.costings} />}
          <Details page={page} onSave={(fields: DetailFields) => change(() => api.patch(base, fields), 'Project saved')} />
        </aside>
      </div>

      {compose && (
        <Composer projectId={projectId} invoiceId={compose.invoiceId} threadId={compose.threadId}
                  onClose={(sent) => {
                    setCompose(null);
                    if (sent) {
                      setNotice('Email sent');
                      void load();
                    }
                  }} />
      )}
      <p className="sr-only" role="status" aria-live="polite">{notice}</p>
    </div>
  );
}
