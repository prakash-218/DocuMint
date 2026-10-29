import { PageHeader } from '../../app/PageHeader';
import { ask, Loading, useLoad } from '../../app/ui';
import { day } from '../../format';
import { Icon } from '../../icons';

// A template's page (GET /api/templates/<id>, template_view.overview): a preview with sample values, its formulas in
// words, the pages it prints, the documents that use it and its versions. Archiving posts to templates_bp.

interface Preview {
  title: string;
  kind: string;
  items: boolean;
  columns?: { label: string; required: boolean; kind: string; num: boolean; calc: boolean }[];
  rows?: string[][];
  fields?: { label: string; value: string; calc: boolean; total: boolean }[];
}

interface Data {
  title: string;
  sub: string;
  archived: boolean;
  use: { label: string; href: string }[];
  layout: string | null;
  edit: string | null;
  broken: number;
  preview: Preview[];
  breakups: boolean;
  formulas: { label: string; section: string; plain: string; formula: string; error: string; total: boolean }[];
  no_total: boolean;
  pages: { title: string; kind: string; sub: string }[];
  documents: { count: number; rows: { number: string; url: string; kind: string; customer: string; status: { text: string; tone: string } }[] };
  versions: { version: number; date: string | null }[];
  archive: { action: string; archived: boolean } | null;
}

function Section({ s }: { s: Preview }) {
  return (
    <section className="invoice-section">
      <h3 className="invoice-section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {s.title}<span className={`badge ${s.items ? 'badge-info' : 'badge-secondary'}`}>{s.kind}</span>
      </h3>
      {s.items ? (
        <div style={{ overflowX: 'auto' }}>
          <table className="invoice-items preview-table">
            <thead>
              <tr>
                <th style={{ width: 36 }}>#</th>
                {(s.columns ?? []).map((c, i) => (
                  <th key={i} className={[c.num && 'num', c.calc && 'calc'].filter(Boolean).join(' ') || undefined}>
                    {c.label}{c.required && <span className="req" title="Required">*</span>}
                    <span className="col-kind">{c.kind}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(s.rows ?? []).map((row, i) => (
                <tr key={i}>
                  <td className="text-tertiary">{i + 1}</td>
                  {row.map((v, j) => {
                    const c = s.columns?.[j];
                    return <td key={j} className={[c?.num && 'num', c?.calc && 'calc'].filter(Boolean).join(' ') || undefined}>{v}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="invoice-totals" style={{ marginLeft: 'auto' }}>
          {(s.fields ?? []).map((f, i) => (
            <div key={i} className={f.total ? 'grand' : undefined}>
              <span className={f.total ? undefined : 'label'}>{f.label}{f.total && <> <span className="badge badge-success" style={{ verticalAlign: 'middle' }}>Document total</span></>}</span>
              <span className={f.calc ? 'calc-text' : undefined}>{f.value}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function Overview({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title} heading description={data.sub}
                  actions={<>
                    {data.use.length > 0 && (
                      <details className="menu">
                        <summary className="btn btn-primary"><Icon name="plus" /><span className="btn-label">Use this template</span></summary>
                        <div className="menu-panel">
                          {data.use.map((u) => <a key={u.href} href={u.href}><Icon name="file" />{u.label}</a>)}
                        </div>
                      </details>
                    )}
                    {data.layout && <a href={data.layout} className="btn btn-secondary"><Icon name="file" /><span className="btn-label">Pages &amp; printing</span></a>}
                    {data.edit && <a href={data.edit} className="btn btn-secondary"><Icon name="pencil" /><span className="btn-label">Edit fields</span></a>}
                  </>} />
      {data.archived && <div className="alert alert-warning"><span>This template is archived. Existing documents still use it, but it can't be picked for new ones.</span></div>}
      {data.broken > 0 && <div className="alert alert-error"><span>{data.broken} formula{data.broken === 1 ? '' : 's'} won't calculate. See the Formulas panel.</span></div>}
      <div className="invoice-layout">
        <div>
          <article className="card">
            <div className="card-header"><div><h2 className="card-title">Preview</h2><p className="card-subtitle">With sample values</p></div></div>
            <div className="card-body">
              {data.preview.length ? data.preview.map((s) => <Section key={s.title} s={s} />)
                : <p className="text-tertiary">This template has no fields yet.</p>}
              {data.breakups && <p className="form-text" style={{ marginTop: 0 }}>Cost break-up lines explain an item's price and are never added to the total.</p>}
            </div>
          </article>
        </div>
        <aside>
          <div className="card">
            <div className="card-header"><h2 className="card-title">Formulas</h2></div>
            <div className="card-body">
              {data.formulas.length ? (
                <ul className="formula-list">
                  {data.formulas.map((f, i) => (
                    <li key={i}>
                      <div className="flex-between" style={{ flexWrap: 'nowrap', alignItems: 'baseline' }}>
                        <strong>{f.label}</strong><span className="text-tertiary" style={{ fontSize: 'var(--font-size-xs)' }}>{f.section}</span>
                      </div>
                      <div className="text-secondary">= {f.plain}</div>
                      <code>{f.formula}</code>
                      {f.error && <div className="badge badge-danger" style={{ marginTop: 4 }}>{f.error}</div>}
                      {f.total && <div className="badge badge-success" style={{ marginTop: 4 }}>Document total</div>}
                    </li>
                  ))}
                </ul>
              ) : <p className="text-tertiary" style={{ margin: 0 }}>No calculated fields.</p>}
              {data.no_total && <p className="form-text" style={{ color: 'var(--warning-ink)' }}>No document total selected. Choose one in Edit.</p>}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Pages</h2>
              {data.layout && <a href={data.layout} className="btn btn-ghost btn-xs">Edit</a>}
            </div>
            <div className="card-body">
              <ul className="timeline">
                {data.pages.map((p, i) => (
                  <li key={i} style={{ gridTemplateColumns: '28px 1fr' }}>
                    <span className="dot" style={{ background: 'var(--accent-soft)', color: 'var(--accent-ink)' }}>
                      <Icon name={p.kind === 'packing' ? 'package' : 'file'} size={14} /></span>
                    <div><div>{p.title}</div><div className="when">{p.sub}</div></div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Used by</h2>
              <span className="text-tertiary">{data.documents.count} document{data.documents.count === 1 ? '' : 's'}</span>
            </div>
            <div className="card-body">
              {data.documents.rows.length ? (
                <ul className="timeline">
                  {data.documents.rows.map((d) => (
                    <li key={d.url} style={{ gridTemplateColumns: '1fr auto' }}>
                      <div style={{ minWidth: 0 }}><a href={d.url}>{d.number}</a><div className="when">{d.kind} · {d.customer}</div></div>
                      <span><span className={`badge badge-${d.status.tone}`}>{d.status.text}</span></span>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-tertiary" style={{ margin: 0 }}>Not used yet.</p>}
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h2 className="card-title">Versions</h2></div>
            <div className="card-body">
              <dl className="summary-list">
                {data.versions.map((v, i) => (
                  <div key={v.version}><dt>v{v.version}{i === 0 && <> <span className="badge badge-success">Current</span></>}</dt>
                    <dd className="text-tertiary" style={{ fontWeight: 400 }}>{day(v.date)}</dd></div>
                ))}
              </dl>
              {data.archive && (
                <div className="btn-group" style={{ marginTop: 'var(--spacing-sm)' }}>
                  <form method="post" action={data.archive.action}
                        onSubmit={data.archive.archived ? undefined : ask(`Archive ${data.title}? It can't be used for new documents; existing ones are unaffected.`)}>
                    {data.archive.archived
                      ? <button type="submit" className="btn btn-secondary btn-sm">Unarchive</button>
                      : <button type="submit" className="btn btn-ghost btn-sm">Archive</button>}
                  </form>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}

export default function TemplatePage({ templateId }: { templateId: string }) {
  const { data, error } = useLoad<Data>(`/api/templates/${templateId}`, "Couldn't load the template. Check your connection.");
  return data ? <Overview data={data} /> : <Loading title="Template" kind="page" error={error} heading />;
}
