import { Dropdown, choices, type Choice, type ChoiceGroup } from '../../mantine/Dropdown';
import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Icon } from '../../icons';
import { amount, lineCells, parseDiscount, totals } from './calc';
import type { CustomerGroup, EditorData, Field, Section, Value } from './types';

// A document in the editor, as the server page drew it: customer, number and dates; the template's line items (add
// and remove lines, amounts worked out as you type) and other fields; the document's details; and beside them the
// totals and the currency, tax, discount and advance. It posts the same form the server page did (editor_page.py
// says what). A line's discount, and the document's, are an amount (5000) or a percent (10%).

type Rows = Record<string, { row: number; values: Record<string, Value>; discount?: string }[]>;

/** A discount as typed; the browser won't send the form while it isn't an amount or a percent (calc.parseDiscount) */
function DiscountInput({ id, name, label, value, onChange, placeholder }: {
  id?: string; name: string; label?: string; value: string; onChange: (v: string) => void; placeholder: string;
}) {
  const invalid = parseDiscount(value) === 'invalid';
  return (
    <input type="text" inputMode="decimal" id={id} name={name} value={value} aria-label={label} placeholder={placeholder} autoComplete="off"
           className={`form-input discount-input${invalid ? ' is-invalid' : ''}`} aria-invalid={invalid || undefined}
           title="An amount, like 5000, or a percent, like 10%"
           ref={(el) => el?.setCustomValidity(invalid ? 'Type an amount, like 5000, or a percent, like 10%.' : '')}
           onChange={(e) => onChange(e.target.value)} />
  );
}

function colClass(f: Field): string {
  if (f.formula) return 'calc num';
  if (f.long) return 'long';
  return f.data_type === 'number' ? 'short num' : 'short';
}

function grow(el: HTMLTextAreaElement | null) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight}px`;
}

/** The customers to pick from, a parent company's sites grouped under it */
export function customerChoices(groups: CustomerGroup[]): (Choice | ChoiceGroup)[] {
  return groups.flatMap((g): (Choice | ChoiceGroup)[] => {
    const items = g.options.map((o) => ({ value: o.id, label: o.label }));
    return g.label ? [{ group: g.label, items }] : items;
  });
}

function Cell({ section, field: f, row, value, calc, currency, onChange }: {
  section: Section; field: Field; row: number; value: Value | undefined; calc: number | undefined; currency: string;
  onChange: (v: Value) => void;
}) {
  const name = `line_item_${section.id}_${row}_field_${f.id}`;
  let input;
  if (f.formula) {
    const shown = calc === undefined || !Number.isFinite(calc) ? '—' : f.money ? amount(calc, currency) : String(+calc.toFixed(4));
    input = <><input type="hidden" name={name} value="" /><output className="calc">{shown}</output></>;
  } else if (f.data_type === 'number') {
    input = <input type="number" step="any" name={name} value={String(value ?? '')} className="form-input" aria-label={f.label}
                   required={f.required} onChange={(e) => onChange(e.target.value)} />;
  } else if (f.data_type === 'date') {
    input = <input type="date" name={name} value={String(value ?? '')} className="form-input" aria-label={f.label} onChange={(e) => onChange(e.target.value)} />;
  } else if (f.data_type === 'boolean') {
    input = <input type="checkbox" name={name} value="true" className="form-checkbox" aria-label={f.label} checked={value === true}
                   onChange={(e) => onChange(e.target.checked)} />;
  } else if (f.long) {
    input = <textarea name={name} rows={1} className="form-textarea line-text" aria-label={f.label} required={f.required} value={String(value ?? '')}
                      ref={grow} onChange={(e) => { grow(e.target); onChange(e.target.value); }} />;
  } else {
    input = <input type="text" name={name} value={String(value ?? '')} className="form-input" aria-label={f.label} required={f.required}
                   onChange={(e) => onChange(e.target.value)} />;
  }
  return <td data-label={f.label} className={colClass(f)}>{input}</td>;
}

function ItemsCard({ section, rows, currency, setRows }: {
  section: Section; rows: Rows[string]; currency: string; setRows: (next: Rows[string]) => void;
}) {
  const focusRow = useRef<number | null>(null);
  const body = useRef<HTMLTableSectionElement>(null);
  const [discounting, setDiscounting] = useState(false);
  const canDiscount = !!section.amount_field;
  const withDiscount = canDiscount && (discounting || rows.some((r) => r.discount));
  useEffect(() => {
    if (focusRow.current === null) return;
    const tr = body.current?.querySelector(`tr[data-row="${focusRow.current}"]`);
    (tr?.querySelector('textarea, input:not([type=hidden])') as HTMLElement | null)?.focus();
    focusRow.current = null;
  });
  const add = () => {
    const next = Math.max(0, ...rows.map((r) => r.row)) + 1;
    focusRow.current = next;
    setRows([...rows, { row: next, values: {} }]);
  };
  const remove = (row: number) => {
    if (rows.length > 1) setRows(rows.filter((r) => r.row !== row));
    else setRows([{ row, values: {} }]);                    // the last line is emptied, not removed
  };
  return (
    <section className="card items-card">
      <div className="card-header"><h2 className="card-title">{section.title}</h2></div>
      <div className="items-wrap">
        <table className="items-editor">
          <thead>
            <tr>
              <th className="col-no">#</th>
              {section.fields.map((f) => (
                <Fragment key={f.id}>
                  {withDiscount && f.id === section.amount_field && <th className="short col-discount">Discount</th>}
                  <th className={colClass(f)}>{f.label}</th>
                </Fragment>
              ))}
              <th className="col-x"><span className="sr-only">Remove</span></th>
            </tr>
          </thead>
          <tbody ref={body}>
            {rows.map((r, i) => {
              const cells = lineCells(section, r.values, r.discount);
              return (
                <tr key={r.row} data-row={r.row}>
                  <td className="col-no" data-label="#"><span className="row-no">{i + 1}</span></td>
                  {section.fields.map((f) => (
                    <Fragment key={f.id}>
                      {withDiscount && f.id === section.amount_field && (            // before the amount it comes off, as printed
                        <td className="short col-discount" data-label="Discount">
                          <DiscountInput name={`line_discount_${section.id}_${r.row}`} label={`Discount on line ${i + 1}`} value={r.discount ?? ''}
                                         placeholder="—" onChange={(v) => setRows(rows.map((x) => (x.row === r.row ? { ...x, discount: v } : x)))} />
                        </td>
                      )}
                      <Cell section={section} field={f} row={r.row} value={r.values[f.id]} calc={cells[f.id]} currency={currency}
                            onChange={(v) => setRows(rows.map((x) => (x.row === r.row ? { ...x, values: { ...x.values, [f.id]: v } } : x)))} />
                    </Fragment>
                  ))}
                  <td className="col-x">
                    <button type="button" className="btn btn-ghost btn-xs remove-row" aria-label={`Remove line ${i + 1}`} onClick={() => remove(r.row)}>
                      <Icon name="x" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="items-foot">
        <button type="button" className="btn btn-ghost btn-sm add-row" onClick={add}><Icon name="plus" />Add line</button>
        {canDiscount && !withDiscount && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDiscounting(true)}>Discount a line</button>
        )}
      </div>
    </section>
  );
}

function NormalCard({ section, values, setValue }: { section: Section; values: Record<string, Value>; setValue: (id: string, v: Value) => void }) {
  const inputs = section.fields.filter((f) => !f.formula);
  return (
    <>
      {section.fields.filter((f) => f.formula).map((f) => <input key={f.id} type="hidden" name={`field_${f.id}`} value="" />)}
      {inputs.length > 0 && (
        <section className="card">
          <div className="card-header"><h2 className="card-title">{section.title}</h2></div>
          <div className="card-body form-row">
            {inputs.map((f) => (
              <div key={f.id} className="form-group">
                <label htmlFor={`field_${f.id}`} className="form-label">{f.label}{f.required ? ' *' : ''}</label>
                {f.data_type === 'boolean' ? (
                  <input type="checkbox" id={`field_${f.id}`} name={`field_${f.id}`} value="true" className="form-checkbox" checked={values[f.id] === true}
                         onChange={(e) => setValue(f.id, e.target.checked)} />
                ) : (
                  <input type={f.data_type === 'number' ? 'number' : f.data_type === 'date' ? 'date' : 'text'} step={f.data_type === 'number' ? 'any' : undefined}
                         id={`field_${f.id}`} name={`field_${f.id}`} value={String(values[f.id] ?? '')} className="form-input" required={f.required}
                         onChange={(e) => setValue(f.id, e.target.value)} />
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function Details({ details }: { details: EditorData['details'] }) {
  const input = (key: string) => {
    const f = details.fields.find((x) => x.key === key)!;
    const value = details.values[f.key] ?? '';
    return (
      <div key={f.key} className="form-group">
        <label htmlFor={`detail_${f.key}`} className="form-label">{f.label}</label>
        {f.kind === 'textarea' ? (
          <textarea id={`detail_${f.key}`} name={`detail_${f.key}`} className="form-textarea" rows={f.key === 'terms' ? 5 : 3}
                    placeholder={f.placeholder} defaultValue={value} />
        ) : (
          <input type={f.kind === 'date' ? 'date' : 'text'} id={`detail_${f.key}`} name={`detail_${f.key}`} className="form-input"
                 defaultValue={value} placeholder={f.placeholder} />
        )}
      </div>
    );
  };
  const layout = (keys: string[]) => {
    const kind = (k: string) => details.fields.find((f) => f.key === k)!.kind;
    const short = keys.filter((k) => kind(k) !== 'textarea');
    return <>{short.length > 0 && <div className="form-row">{short.map(input)}</div>}{keys.filter((k) => kind(k) === 'textarea').map(input)}</>;
  };
  const plain = details.fields.filter((f) => !f.group).map((f) => f.key);
  if (!plain.length && !details.groups.length) return null;
  return (
    <section className="card">
      <div className="card-header"><h2 className="card-title">Details</h2></div>
      <div className="card-body">
        {layout(plain)}
        {details.groups.map((g) => (
          <details key={g.key} className="fold" open={g.open}>
            <summary>{g.label}</summary>
            {layout(g.fields)}
          </details>
        ))}
      </div>
    </section>
  );
}

export function Editor({ data }: { data: EditorData }) {
  const s = data.settings;
  const [rows, setAllRows] = useState<Rows>(() => Object.fromEntries(data.sections.filter((x) => x.type === 'line_item').map((x) => [x.id, x.rows ?? []])));
  const [normals, setNormals] = useState<Record<string, Value>>(() => Object.assign({}, ...data.sections.filter((x) => x.type !== 'line_item').map((x) => x.values ?? {})));
  const [currency, setCurrency] = useState(s.currency);
  const [taxMode, setTaxMode] = useState(s.tax_mode);
  const [customerId, setCustomerId] = useState('');                  // picked here; a fixed one has its tax_hint
  const hint = customerId ? data.tax_hints[customerId] : data.tax_hint ?? undefined;
  const [taxRate, setTaxRate] = useState(s.tax_rate);
  const [discount, setDiscount] = useState(data.discount ?? '');
  const sum = useMemo(() => totals(data.sections, rows, normals, taxMode, taxRate, discount),
                      [data.sections, rows, normals, taxMode, taxRate, discount]);
  const discounted = sum.discount > 0;
  const taxed = taxMode === 'cgst_sgst' || taxMode === 'igst';
  const rate = parseFloat(taxRate) || 0;
  const t = data.type;

  return (
    <>
      <PageHeader title={data.title} heading
                  description={<>
                    {data.project && <><a href={data.project.url}>{data.project.label} · {data.project.title}</a> · </>}
                    {data.template_name}
                    {data.change_template && <> · <a href={data.change_template}>Change</a></>}
                  </>}
                  actions={<>
                    <a href={data.cancel} className="btn btn-ghost"><span className="btn-label">Cancel</span><Icon name="x" className="show-mobile-icon" /></a>
                    <button type="submit" form="docForm" className="btn btn-primary"><Icon name="check" /><span className="btn-label">{data.submit}</span></button>
                  </>} />
      <form id="docForm" method="post" action={data.action}>
        {Object.entries(data.hidden).map(([k, v]) => <input key={k} type="hidden" name={k} value={v} />)}
        {data.correcting && (
          <div className="alert alert-warning">
            <span>You're correcting a {t.label.toLowerCase()} that was {t.sent_word}. It keeps its number and
              status{t.takes_payments ? '; if the total changes, paid / pending follows the payments recorded' : ''}. The correction is
              recorded in the audit log. Download the PDF again afterwards and send the corrected one.</span>
          </div>
        )}
        <div className="invoice-layout editor-layout">
          <div className="stack">
            <section className="card">
              <div className="card-body">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="customer_id" className="form-label">Customer</label>
                    {data.customer.fixed ? (
                      <>
                        {data.customer.fixed.id && <input type="hidden" id="customer_id" name="customer_id" value={data.customer.fixed.id} />}
                        <div className="form-static">{data.customer.fixed.name}</div>
                      </>
                    ) : (
                      <Dropdown id="customer_id" name="customer_id" required placeholder="Select a customer" searchable
                                data={customerChoices(data.customer.groups)}
                                onChange={(v) => { setCustomerId(v); if (data.tax_hints[v]) setTaxMode(data.tax_hints[v].mode); }} />
                    )}
                  </div>
                  <div className="form-group">
                    <label htmlFor="doc_number" className="form-label">Number</label>
                    <input type="text" id="doc_number" name="doc_number" className="form-input" defaultValue={data.number.value} required={data.number.required} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="issue_date" className="form-label">Date</label>
                    <input type="date" id="issue_date" name="issue_date" className="form-input" defaultValue={data.issue_date} />
                  </div>
                  <div className="form-group">
                    <label htmlFor="due_date" className="form-label">{t.due_label}</label>
                    <input type="date" id="due_date" name="due_date" className="form-input" defaultValue={data.due_date} />
                  </div>
                </div>
              </div>
            </section>

            {data.sections.filter((x) => x.type === 'line_item').map((x) => (
              <ItemsCard key={x.id} section={x} rows={rows[x.id] ?? []} currency={currency}
                         setRows={(next) => setAllRows((all) => ({ ...all, [x.id]: next }))} />
            ))}
            {data.sections.filter((x) => x.type !== 'line_item').map((x) => (
              <NormalCard key={x.id} section={x} values={normals} setValue={(id, v) => setNormals((all) => ({ ...all, [id]: v }))} />
            ))}
            <Details details={data.details} />
          </div>

          <aside>
            <div className="card">
              <div className="card-header"><h2 className="card-title">Summary</h2></div>
              <div className="card-body">
                <dl className="kv editor-summary">
                  {sum.fields.map((f, i) => (
                    <span key={f.id} style={{ display: 'contents' }}>
                      <dt>{discounted && i === sum.fields.length - 1 ? 'Sub total' : f.label}</dt><dd><output>{amount(f.value, currency)}</output></dd>
                    </span>
                  ))}
                  {discounted && <><dt className="discount-line">{sum.discountLabel}</dt><dd className="discount-line"><output>-{amount(sum.discount, currency)}</output></dd></>}
                  {discounted && taxed && <><dt>Taxable value</dt><dd><output>{amount(sum.taxable, currency)}</output></dd></>}
                  {taxed && <><dt className="tax-line">{sum.taxLabel}</dt><dd className="tax-line"><output>{amount(sum.tax, currency)}</output></dd></>}
                  {(taxed || discounted || !sum.fields.length) && (
                    <><dt className="grand"><strong>Total</strong></dt><dd className="grand"><strong><output>{amount(sum.grand, currency)}</output></strong></dd></>
                  )}
                </dl>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <div className="form-group">
                  <label htmlFor="currency" className="form-label">Currency</label>
                  <Dropdown id="currency" name="currency" value={currency} onChange={setCurrency} data={choices(s.currencies)} />
                </div>
                <div className="form-group">
                  <label htmlFor="discount" className="form-label">Discount on the total</label>
                  <DiscountInput id="discount" name="discount" value={discount} onChange={setDiscount} placeholder="None" />
                  <p className="form-text">An amount (5000) or a percent (10%), taken off before tax.</p>
                </div>
                <div className="form-group">
                  <label htmlFor="tax_mode" className="form-label">Tax</label>
                  <Dropdown id="tax_mode" name="tax_mode" value={taxMode} onChange={setTaxMode} data={choices(s.tax_modes)} />
                  {hint?.note && <p className="form-text">{hint.mode === taxMode ? `${hint.note}.` : `Suggested: ${hint.note}.`}</p>}
                </div>
                <div className="form-group" style={taxed ? undefined : { display: 'none' }}>
                  <label htmlFor="tax_rate" className="form-label">GST rate (%)</label>
                  <input type="number" step="0.01" min="0" max="100" id="tax_rate" name="tax_rate" className="form-input" value={taxRate}
                         onChange={(e) => setTaxRate(e.target.value)} />
                  <p className="form-text">{taxMode === 'cgst_sgst' ? `CGST ${rate / 2}% + SGST ${rate / 2}%` : ''}</p>
                </div>
                {t.proforma && (
                  <>
                    <div className="form-group">
                      <label htmlFor="advance_percent" className="form-label">Advance (%)</label>
                      <input type="number" step="0.01" min="0" max="100" id="advance_percent" name="advance_percent" className="form-input"
                             defaultValue={s.advance_percent} placeholder="None" />
                    </div>
                    <div className="form-group">
                      <label htmlFor="advance_basis" className="form-label">Advance on</label>
                      <Dropdown id="advance_basis" name="advance_basis" defaultValue={s.advance_basis}
                                data={[{ value: 'pre_tax', label: 'Value before tax' }, { value: 'total', label: 'Total with tax' }]} />
                    </div>
                  </>
                )}
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-block">{data.submit_side}</button>
          </aside>
        </div>
      </form>
    </>
  );
}
