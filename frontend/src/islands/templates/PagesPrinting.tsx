import { Dropdown } from '../../mantine/Dropdown';
import { useState } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { Icon } from '../../icons';

// Pages & printing (GET /api/templates/<id>/layout, template_view.layout_page): which document types the template is
// offered for, whether it's for exports, and the pages it prints with their copies, columns, box details and contents.
// It posts layout.layout_from_form's fields (page_<n>_..., page_<n>_box_<field>_<m>) to templates_bp.edit_layout; a
// removed page or box row isn't posted, so it's dropped. "Add packing list" / "Add annexure page" save and add one.

interface Page {
  key: string;
  kind: string;
  title: string;
  doc_types: string[];
  with_document: boolean;
  copies: string[];
  columns: string[];
  box_fields?: { key: string; label: string; sum: boolean }[];
  sections?: string[];
  include_notes?: boolean;
  include_terms?: boolean;
}

interface Data {
  title: string;
  name: string;
  back: string;
  action: string;
  used_for: string[];
  guessed: boolean;
  export: string;
  auto_export: boolean;
  choosable: [string, string][];
  doc_types: [string, string][];
  kinds: Record<string, string>;
  pages: Page[];
  item_fields: { name: string; label: string }[];
  sections: { name: string; label: string }[];
}

function Checks({ name, options, ticked }: { name: string; options: [string, string][]; ticked: string[] }) {
  return (
    <div className="check-row">
      {options.map(([value, label]) => (
        <label key={value} className="form-check">
          <input type="checkbox" name={name} value={value} className="form-checkbox" defaultChecked={ticked.includes(value)} /> {label}
        </label>
      ))}
    </div>
  );
}

function BoxFields({ p, fields }: { p: string; fields: { key: string; label: string; sum: boolean }[] }) {
  const [rows, setRows] = useState(() => [...fields, { key: '', label: '', sum: false }].map((f, i) => ({ ...f, m: i + 1 })));
  return (
    <div className="form-group">
      <label className="form-label">Box details</label>
      <table className="table box-table">
        <thead><tr><th>Label</th><th className="center" style={{ width: 110 }}>Total at end</th><th style={{ width: 40 }} /></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.m}>
              <td><input type="hidden" name={`${p}box_key_${r.m}`} value={r.key} />
                <input type="text" name={`${p}box_label_${r.m}`} defaultValue={r.label} className="form-input" placeholder="Pallet no." aria-label="Box detail" /></td>
              <td className="center"><input type="checkbox" name={`${p}box_sum_${r.m}`} className="form-checkbox" defaultChecked={r.sum} aria-label="Total at end" /></td>
              <td><button type="button" className="btn btn-ghost btn-xs" aria-label="Remove" onClick={() => setRows((all) => all.filter((x) => x.m !== r.m))}>×</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: 'var(--spacing-sm)' }}
              onClick={() => setRows((all) => [...all, { key: '', label: '', sum: false, m: Math.max(0, ...all.map((x) => x.m)) + 1 }])}>
        <Icon name="plus" />Add box detail</button>
    </div>
  );
}

export function LayoutForm({ data }: { data: Data }) {
  const [pages, setPages] = useState(() => data.pages.map((pg, i) => ({ ...pg, n: i + 1 })));
  return (
    <>
      <PageHeader title={data.title} heading description={data.name}
                  actions={<a href={data.back} className="btn btn-secondary"><Icon name="arrowLeft" /><span className="btn-label">Back to template</span></a>} />
      <form method="post" action={data.action} className="panel-medium layout-editor" style={{ maxWidth: 880 }}>
        <input type="hidden" name="page_count" value={Math.max(0, ...pages.map((p) => p.n))} />
        <section className="card">
          <div className="card-body">
            <fieldset className="form-group used-for">
              <legend className="form-label">Used for</legend>
              {data.choosable.map(([key, plural]) => (
                <label key={key} className="form-check"><input type="checkbox" name="used_for" value={key} className="form-checkbox"
                                                               defaultChecked={data.used_for.includes(key)} /> {plural}</label>
              ))}
              {data.guessed && <p className="form-text">Guessed from its name.</p>}
            </fieldset>
            <label htmlFor="export" className="form-label">Used for exports</label>
            <Dropdown id="export" name="export" style={{ maxWidth: 520 }} defaultValue={data.export}
                      data={[{ value: 'auto', label: 'Automatic', sub: data.auto_export ? 'Yes: a foreign currency, or "export" in the name' : 'No: the home currency' },
                             { value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} />
          </div>
        </section>

        {pages.map((pg) => {
          const p = `page_${pg.n}_`;
          return (
            <section key={pg.n} className="card layout-page">
              <input type="hidden" name={`${p}present`} value="1" />
              <input type="hidden" name={`${p}key`} value={pg.key} />
              <input type="hidden" name={`${p}kind`} value={pg.kind} />
              <div className="card-header">
                <div>
                  <h2 className="card-title"><Icon name={pg.kind === 'packing' ? 'package' : 'file'} /> {pg.title || data.kinds[pg.kind]}</h2>
                  <p className="card-subtitle">{data.kinds[pg.kind]}</p>
                </div>
                {pg.kind !== 'document' && (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPages((all) => all.filter((x) => x.n !== pg.n))}>
                    <Icon name="trash" />Remove page</button>
                )}
              </div>
              <div className="card-body">
                {pg.kind !== 'document' && (
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label" htmlFor={`${p}title`}>Page title</label>
                      <input type="text" id={`${p}title`} name={`${p}title`} className="form-input" defaultValue={pg.title} maxLength={60} />
                    </div>
                    <div className="form-group">
                      <span className="form-label">How it prints</span>
                      <label className="form-check"><input type="checkbox" name={`${p}with_document`} className="form-checkbox" defaultChecked={pg.with_document} /> In the same PDF, after the main document</label>
                    </div>
                  </div>
                )}
                <div className="form-group">
                  <span className="form-label">Document types</span>
                  <Checks name={`${p}doc_types`} options={data.doc_types} ticked={pg.doc_types} />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor={`${p}copies`}>Copies</label>
                  <textarea id={`${p}copies`} name={`${p}copies`} className="form-input" rows={3} style={{ minHeight: 84 }}
                            placeholder={'Original for Recipient\nDuplicate for Transporter'} defaultValue={pg.copies.join('\n')} />
                  <p className="form-text">Up to 5.</p>
                </div>
                {(pg.kind === 'document' || pg.kind === 'packing') && data.item_fields.length > 0 && (
                  <div className="form-group">
                    <span className="form-label">Item columns</span>
                    <Checks name={`${p}columns`} options={data.item_fields.map((f) => [f.name, f.label])} ticked={pg.columns} />
                  </div>
                )}
                {pg.kind === 'packing' && <BoxFields p={p} fields={pg.box_fields ?? []} />}
                {pg.kind === 'annexure' && (
                  <div className="form-group">
                    <span className="form-label">Contents</span>
                    <div className="check-row">
                      {data.sections.map((s) => (
                        <label key={s.name} className="form-check"><input type="checkbox" name={`${p}sections`} value={s.name} className="form-checkbox"
                                                                           defaultChecked={(pg.sections ?? []).includes(s.name)} /> {s.label}</label>
                      ))}
                      <label className="form-check"><input type="checkbox" name={`${p}include_notes`} className="form-checkbox" defaultChecked={pg.include_notes} /> Notes</label>
                      <label className="form-check"><input type="checkbox" name={`${p}include_terms`} className="form-checkbox" defaultChecked={pg.include_terms} /> Terms &amp; conditions</label>
                    </div>
                  </div>
                )}
              </div>
            </section>
          );
        })}

        <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
            <button type="submit" name="add_page" value="packing" className="btn btn-secondary"><Icon name="package" />Add packing list</button>
            <button type="submit" name="add_page" value="annexure" className="btn btn-secondary"><Icon name="plus" />Add annexure page</button>
          </div>
          <button type="submit" className="btn btn-primary"><Icon name="check" />Save</button>
        </div>
      </form>
    </>
  );
}

export default function PagesPrinting({ templateId }: { templateId: string }) {
  const { data, error } = useLoad<Data>(`/api/templates/${templateId}/layout`, "Couldn't load the page settings. Check your connection.");
  return data ? <LayoutForm data={data} /> : <Loading title="Pages & printing" kind="page" error={error} heading />;
}
