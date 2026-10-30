import { useEffect, useState } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad, usePosted } from '../../app/ui';
import { Icon } from '../../icons';

// The template builder (GET /api/templates/new or /<id>/fields, template_view.builder): sections, their fields, the
// fields' formulas and which number is the document total. It posts what template_builder.sections_from_form reads to
// templates_bp.create_template or edit_template: section_count, s<i>_present / _name / _title / _type / _field_count,
// s<i>_f<j>_present / _name / _label / _type / _formula / _currency / _required, and total ("i:j"). A removed section
// or field isn't posted. When the save is turned down, the builder comes back with what was sent (usePosted).

interface Field {
  j: number;
  label: string;
  name: string;              // fixed once saved: formulas refer to it
  type: string;
  formula: string;
  currency: boolean;
  required: boolean;
}

interface Section {
  i: number;
  title: string;
  name: string;
  type: string;
  fields: Field[];
}

interface Data {
  title: string;
  creating: boolean;
  sub: string;
  action: string;
  cancel: string;
  in_use: string;
  sections: { title: string; name: string; type: string; fields: Omit<Field, 'j'>[] }[];
  total: string;
  field_types: [string, string][];
  section_types: [string, string][];
  currencies: string[];
  currency: string;
  choosable: [string, string][];
}

export const slug = (text: string) => text.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');

/** The sections as the server sent them, numbered 1… */
function numbered(sections: Data['sections']): Section[] {
  return sections.map((s, i) => ({ ...s, i: i + 1, fields: s.fields.map((f, j) => ({ ...f, j: j + 1 })) }));
}

/** The sections from a form the server turned down: s<i>_..., s<i>_f<j>_... as they were sent */
export function fromPosted(v: Record<string, string>): Section[] {
  const out: Section[] = [];
  const count = parseInt(v.section_count, 10) || 0;
  for (let i = 1; i <= count; i++) {
    if (!v[`s${i}_present`]) continue;
    const fields: Field[] = [];
    const fcount = parseInt(v[`s${i}_field_count`], 10) || 0;
    for (let j = 1; j <= fcount; j++) {
      const q = `s${i}_f${j}_`;
      if (!v[`${q}present`]) continue;
      fields.push({ j, label: v[`${q}label`] ?? '', name: v[`${q}name`] ?? '', type: v[`${q}type`] || 'string', formula: v[`${q}formula`] ?? '',
                    currency: !!v[`${q}currency`], required: !!v[`${q}required`] });
    }
    out.push({ i, title: v[`s${i}_title`] ?? '', name: v[`s${i}_name`] ?? '', type: v[`s${i}_type`] || 'line_item', fields });
  }
  return out;
}

const blankField = (j: number): Field => ({ j, label: '', name: '', type: 'string', formula: '', currency: false, required: false });

export function BuilderForm({ data }: { data: Data }) {
  const posted = usePosted();
  const [sections, setSections] = useState<Section[]>(() => (posted ? fromPosted(posted) : numbered(data.sections)));
  const [total, setTotal] = useState(posted?.total ?? data.total);
  const [focus, setFocus] = useState('');
  useEffect(() => {
    if (focus) (document.querySelector(focus) as HTMLElement | null)?.focus();
  }, [focus]);

  const setSection = (i: number, patch: Partial<Section>) => setSections((all) => all.map((s) => (s.i === i ? { ...s, ...patch } : s)));
  const setField = (i: number, j: number, patch: Partial<Field>) => setSections((all) => all.map((s) => (s.i !== i ? s
    : { ...s, fields: s.fields.map((f) => (f.j !== j ? f : { ...f, ...patch })) })));
  const nextField = (s: Section) => Math.max(0, ...s.fields.map((f) => f.j)) + 1;
  // Fields that exist on the server keep their numbers; field_count is the highest given out
  const [counts, setCounts] = useState<Record<number, number>>(() => Object.fromEntries(sections.map((s) => [s.i, nextField(s) - 1])));
  const [sectionCount, setSectionCount] = useState(() => Math.max(0, ...sections.map((s) => s.i)));

  function addField(s: Section) {
    const j = Math.max(counts[s.i] ?? 0, nextField(s) - 1) + 1;
    setCounts((c) => ({ ...c, [s.i]: j }));
    setSection(s.i, { fields: [...s.fields, blankField(j)] });
    setFocus(`[name="s${s.i}_f${j}_label"]`);
  }
  function addSection() {
    const i = sectionCount + 1;
    setSectionCount(i);
    setCounts((c) => ({ ...c, [i]: 1 }));
    setSections((all) => [...all, { i, title: '', name: '', type: 'line_item', fields: [blankField(1)] }]);
    setFocus(`[name="s${i}_title"]`);
  }

  // The document total: a number field in a fields section
  const choices = sections.filter((s) => s.type === 'normal').flatMap((s) => s.fields
    .filter((f) => f.type === 'number' && f.label.trim()).map((f) => [`${s.i}:${f.j}`, `${s.title || 'Section'} › ${f.label}`] as const));
  const chosen = choices.some(([v]) => v === total) ? total : choices.length ? choices[choices.length - 1][0] : '';

  return (
    <>
      <PageHeader title={data.title} heading description={data.sub || undefined}
                  actions={<>
                    <a href={data.cancel} className="btn btn-ghost"><span className="btn-label">Cancel</span><Icon name="x" className="show-mobile-icon" /></a>
                    <button type="submit" form="tplForm" className="btn btn-primary"><Icon name="check" /><span className="btn-label">Save</span></button>
                  </>} />
      <form id="tplForm" method="post" action={data.action}>
        {data.creating ? (
          <section className="card">
            <div className="card-body form-row">
              <div className="form-group">
                <label htmlFor="name" className="form-label">Name</label>
                <input type="text" id="name" name="name" className="form-input" required maxLength={100} placeholder="Quotation" defaultValue={posted?.name ?? ''} />
              </div>
              <div className="form-group">
                <label htmlFor="currency_code" className="form-label">Currency</label>
                <select id="currency_code" name="currency_code" className="form-select" defaultValue={posted?.currency_code ?? data.currency}>
                  {data.currencies.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <fieldset className="form-group used-for">
                <legend className="form-label">Used for</legend>
                {data.choosable.map(([key, plural]) => (
                  <label key={key} className="form-check"><input type="checkbox" name="used_for" value={key} className="form-checkbox" /> {plural}</label>
                ))}
              </fieldset>
            </div>
          </section>
        ) : data.in_use && <div className="alert alert-info"><span>{data.in_use}</span></div>}

        <input type="hidden" name="section_count" value={sectionCount} />
        <div className="stack">
          {sections.map((s) => (
            <section key={s.i} className="card builder-section">
              <input type="hidden" name={`s${s.i}_present`} value="1" />
              <input type="hidden" name={`s${s.i}_name`} value={s.name} />
              <input type="hidden" name={`s${s.i}_field_count`} value={Math.max(counts[s.i] ?? 0, nextField(s) - 1)} />
              <div className="card-header builder-head">
                <input type="text" name={`s${s.i}_title`} value={s.title} className="form-input section-title" placeholder="Section name" aria-label="Section name"
                       onChange={(e) => setSection(s.i, { title: e.target.value })} />
                <select name={`s${s.i}_type`} value={s.type} className="form-select section-type" aria-label="Section type"
                        onChange={(e) => setSection(s.i, { type: e.target.value })}>
                  {data.section_types.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
                </select>
                <button type="button" className="btn btn-ghost btn-xs" aria-label="Remove section"
                        onClick={() => setSections((all) => all.filter((x) => x.i !== s.i))}><Icon name="trash" /></button>
              </div>
              <div className="items-wrap">
                <table className="items-editor fields-editor">
                  <thead><tr><th className="long">Label</th><th>Type</th><th>Formula</th><th className="center">Money</th><th className="center">Required</th><th className="col-x" /></tr></thead>
                  <tbody>
                    {s.fields.map((f) => {
                      const q = `s${s.i}_f${f.j}_`;
                      const number = f.type === 'number';
                      return (
                        <tr key={f.j}>
                          <td className="long" data-label="Label">
                            <input type="hidden" name={`${q}present`} value="1" />
                            <input type="hidden" name={`${q}name`} value={f.name} />
                            <input type="text" name={`${q}label`} value={f.label} className="form-input field-label" placeholder="Label" aria-label="Label"
                                   onChange={(e) => setField(s.i, f.j, { label: e.target.value })} />
                            <code className="field-code">{f.name || slug(f.label)}</code>
                          </td>
                          <td data-label="Type">
                            <select name={`${q}type`} value={f.type} className="form-select field-type" aria-label="Type"
                                    onChange={(e) => setField(s.i, f.j, e.target.value === 'number' ? { type: e.target.value } : { type: e.target.value, currency: false, formula: '' })}>
                              {data.field_types.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
                            </select>
                          </td>
                          <td data-label="Formula" className="formula-cell">
                            <input type="text" name={`${q}formula`} value={f.formula} className="form-input field-formula" placeholder="—" aria-label="Formula"
                                   spellCheck={false} disabled={!number} onChange={(e) => setField(s.i, f.j, { formula: e.target.value })} />
                          </td>
                          <td data-label="Money" className="center">
                            <input type="checkbox" name={`${q}currency`} className="form-checkbox field-money" aria-label="Money" checked={f.currency}
                                   disabled={!number} onChange={(e) => setField(s.i, f.j, { currency: e.target.checked })} />
                          </td>
                          <td data-label="Required" className="center">
                            <input type="checkbox" name={`${q}required`} className="form-checkbox" aria-label="Required" checked={f.required}
                                   onChange={(e) => setField(s.i, f.j, { required: e.target.checked })} />
                          </td>
                          <td className="col-x"><button type="button" className="btn btn-ghost btn-xs" aria-label="Remove field"
                                                        onClick={() => setSection(s.i, { fields: s.fields.filter((x) => x.j !== f.j) })}><Icon name="x" /></button></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="items-foot"><button type="button" className="btn btn-ghost btn-sm" onClick={() => addField(s)}><Icon name="plus" />Add field</button></div>
            </section>
          ))}
        </div>
        <div className="builder-actions">
          <button type="button" className="btn btn-secondary" onClick={addSection}><Icon name="plus" />Add section</button>
        </div>

        <section className="card">
          <div className="card-body form-row">
            <div className="form-group">
              <label htmlFor="total" className="form-label">Document total</label>
              <select id="total" name="total" className="form-select" value={chosen} onChange={(e) => setTotal(e.target.value)}>
                {choices.length ? choices.map(([value, label]) => <option key={value} value={value}>{label}</option>)
                  : <option value="">Add a number field to a fields section</option>}
              </select>
            </div>
            <div className="form-group">
              <span className="form-label">Formulas</span>
              <p className="form-text" style={{ margin: '6px 0 0' }}><code>this.rate * this.qty</code> on a line · <code>SUM(items.amount)</code> for a column total</p>
            </div>
          </div>
        </section>
      </form>
    </>
  );
}

/** source: /api/templates/new or /api/templates/<id>/fields */
export default function Builder({ source, title }: { source: string; title: string }) {
  const { data, error } = useLoad<Data>(source, "Couldn't load the template. Check your connection.");
  return data ? <BuilderForm data={data} /> : <Loading title={title} kind="page" error={error} heading />;
}
