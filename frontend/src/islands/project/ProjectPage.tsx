import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { Skeleton } from '../../Skeleton';
import { PageHeader } from '../../app/PageHeader';
import { Composer } from '../EmailComposer';
import { NextStep, ProgressChips } from './Overview';
import { People, type ContactFields } from './People';
import { PartInvoiceCard } from './PartInvoice';
import { ProfitCard } from './Profit';
import { Costings, Details, Files, type DetailFields } from './Side';
import { Thread } from './Thread';
import type { Page } from './types';

// The project page, the Job hub: where the job stands on each count (quotation, advance, material, invoiced, paid),
// what to do next, everything on the job in one thread, and the people, files and details beside it.

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
    return (
      <>
        <PageHeader title="Project" crumbs={[{ label: 'Projects', href: '/projects/' }, { label: '…' }]} />
        {error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="page" label="Loading the project…" />}
      </>
    );
  }

  const { project } = page;
  return (
    <div className="ui">
      <PageHeader title={`${project.title} · ${project.label}`}
                  crumbs={[{ label: 'Projects', href: '/projects/' }, { label: `${project.label} ${project.title}` }]} />
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

      <ProgressChips items={page.progress} />
      <NextStep next={page.next} onEmail={(invoiceId) => setCompose({ invoiceId })}
                onStatus={(status) => void change(() => api.patch(base, { status }), `Project marked ${page.statuses[status]?.toLowerCase()}`)} />

      <div className="cols">
        <div className="col-main">
          <Thread page={page}
                  onNote={(text) => change(() => api.post(`${base}/notes`, { text }), 'Note added')}
                  onReply={(threadId) => setCompose({ threadId })}
                  onEmail={(invoiceId) => setCompose(invoiceId ? { invoiceId } : {})} />
        </div>
        <aside className="col-side" aria-label="People, files and details">
          {page.part && <PartInvoiceCard part={page.part} />}
          {page.profit && <ProfitCard profit={page.profit} costings={page.costings} />}
          <People page={page}
                  onGets={(contactId, gets) => void change(() => api.post(`${base}/people`, { contact_id: contactId, gets }), 'Saved')}
                  onSave={(fields: ContactFields) => change(() => api.post(`${base}/contacts`, fields),
                                                            fields.contact_id ? `${fields.name} saved` : `${fields.name || fields.email} added`)}
                  onIgnore={(value) => void change(() => api.post(`${base}/ignore`, { value }), "It won't be suggested again")} />
          <Files page={page} onSave={(fileId, kind, referenceNo) => change(() => api.patch(`/api/files/${fileId}`, { kind, reference_no: referenceNo }), 'File saved')} />
          {page.costings && <Costings costings={page.costings} projectId={project.id} links={page.links} />}
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
