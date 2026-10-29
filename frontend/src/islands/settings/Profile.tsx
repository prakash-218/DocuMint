import { useState } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { Icon } from '../../icons';

// The business profile (GET /api/settings/profile, settings_view.profile): registrations, bank details, document
// defaults and numbering, custom fields, quotation defaults, the letterhead, the stamp and signature. It posts the
// server page's form, with its images, to settings_bp.business_profile. Custom fields are repeatable rows
// <prefix>_label_N / _value_N / _print_N / _key_N (layout.defs_from_form); a removed row isn't posted, so it's dropped.

interface FieldRow {
  key: string;
  label: string;
  print: boolean;
  value?: string;
}

interface Data {
  title: string;
  org: { name: string; address: string; edit: string };
  action: string;
  values: Record<string, string>;
  checks: { separate_export_series: boolean; logo_has_name: boolean };
  currencies: string[];
  months: [string, string][];
  series: { key: string; label: string; format: string; next: number | null; shared: boolean; preview: string }[];
  custom_fields: FieldRow[];
  customer_fields: FieldRow[];
  images: Record<string, string | null>;
  starter: string;
}

function Text({ name, label, value, placeholder, help }: { name: string; label: string; value: string; placeholder?: string; help?: string }) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      <input type="text" id={name} name={name} className="form-input" defaultValue={value} placeholder={placeholder} />
      {help && <p className="form-text">{help}</p>}
    </div>
  );
}

function Image({ name, label, src, help }: { name: string; label: string; src: string | null; help?: string }) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      {src && (
        <>
          <img src={src} alt={label} style={{ maxHeight: 72, maxWidth: '100%', display: 'block', marginBottom: 'var(--spacing-sm)',
                                              background: '#fff', borderRadius: 'var(--radius-sm)', padding: 4 }} />
          <label style={{ fontSize: 'var(--font-size-xs)' }}><input type="checkbox" name={`remove_${name}`} className="form-checkbox" /> Remove</label>
        </>
      )}
      <input type="file" id={name} name={name} accept="image/png,image/jpeg" className="form-input" style={{ paddingTop: 6 }} />
      {help && <p className="form-text">{help}</p>}
    </div>
  );
}

/** Custom fields: a row each, and an empty one to add to; "Add field" adds another, × takes one away */
function FieldRows({ prefix, rows: first, withValue, labelHint, valueHint }: {
  prefix: string; rows: FieldRow[]; withValue: boolean; labelHint: string; valueHint?: string;
}) {
  const [rows, setRows] = useState(() => [...first, { key: '', label: '', print: true }].map((r, i) => ({ ...r, n: i + 1 })));
  const add = () => setRows((all) => [...all, { key: '', label: '', print: true, n: Math.max(0, ...all.map((r) => r.n)) + 1 }]);
  return (
    <>
      <table className="table cf-table">
        <thead>
          <tr><th>Label</th>{withValue && <th>Value</th>}<th className="center" style={{ width: 70 }}>Print</th><th style={{ width: 40 }} /></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.n}>
              <td>
                <input type="hidden" name={`${prefix}_key_${r.n}`} value={r.key} />
                <input type="text" name={`${prefix}_label_${r.n}`} defaultValue={r.label} className="form-input" placeholder={labelHint}
                       aria-label="Label" />
              </td>
              {withValue && (
                <td><input type="text" name={`${prefix}_value_${r.n}`} defaultValue={r.value ?? ''} className="form-input" placeholder={valueHint}
                           aria-label="Value" /></td>
              )}
              <td className="center">
                <input type="checkbox" name={`${prefix}_print_${r.n}`} className="form-checkbox" defaultChecked={r.print || !r.label} aria-label="Print" />
              </td>
              <td>
                <button type="button" className="btn btn-ghost btn-xs" aria-label="Remove"
                        onClick={() => setRows((all) => all.filter((x) => x.n !== r.n))}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: 'var(--spacing-sm)' }} onClick={add}>
        <Icon name="plus" />Add field
      </button>
    </>
  );
}

export function ProfileForm({ data }: { data: Data }) {
  const v = data.values;
  return (
    <>
      <PageHeader title={data.title} />
      <form method="post" action={data.action} encType="multipart/form-data" className="panel-medium" style={{ maxWidth: 880 }}>
        <section className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">{data.org.name}</h2>
              <p className="card-subtitle">{data.org.address} · <a href={data.org.edit}>Edit name &amp; address</a></p>
            </div>
          </div>
          <div className="card-body">
            <div className="form-row">
              <Text name="gstin" label="GSTIN" value={v.gstin} placeholder="33ABCDE1234F1Z5"
                    help="With a GSTIN set, new documents pick CGST+SGST, IGST or LUT automatically." />
              <Text name="pan" label="PAN" value={v.pan} />
              <Text name="state_code" label="State code" value={v.state_code} placeholder="33" />
            </div>
            <div className="form-row">
              <Text name="iec_code" label="IEC code" value={v.iec_code} help="Import Export Code, printed on export invoices" />
              <Text name="lut_number" label="LUT number" value={v.lut_number} />
              <Text name="ad_code" label="Authorised dealer code" value={v.ad_code} />
            </div>
            <div className="form-row">
              <Text name="phone" label="Phone" value={v.phone} />
              <Text name="email" label="Email" value={v.email} />
              <Text name="website" label="Website" value={v.website} />
            </div>
            <div className="form-group">
              <label htmlFor="team_addresses" className="form-label">Your team's other email addresses</label>
              <textarea id="team_addresses" name="team_addresses" className="form-textarea" rows={2} defaultValue={v.team_addresses}
                        placeholder="ravi.home@gmail.com, office.desk@yahoo.com" />
              <p className="form-text">Personal addresses your people also write from. They count as yours: never suggested as a customer's contact.</p>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Bank details</h2></div>
          <div className="card-body">
            <div className="form-row">
              <Text name="bank_name" label="Bank name" value={v.bank_name} />
              <Text name="bank_account" label="Account number" value={v.bank_account} />
              <Text name="bank_ifsc" label="IFSC code" value={v.bank_ifsc} />
            </div>
            <div className="form-row">
              <Text name="bank_branch" label="Branch" value={v.bank_branch} />
              <Text name="bank_swift" label="SWIFT code" value={v.bank_swift} help="For payments from abroad" />
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Documents</h2></div>
          <div className="card-body">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="default_currency" className="form-label">Main currency</label>
                <select id="default_currency" name="default_currency" className="form-select" defaultValue={v.default_currency}>
                  {data.currencies.map((c) => <option key={c}>{c}</option>)}
                </select>
                <p className="form-text">Dashboard totals are shown in this currency.</p>
              </div>
              <div className="form-group">
                <label htmlFor="default_gst_rate" className="form-label">Default GST rate (%)</label>
                <input type="number" step="0.01" id="default_gst_rate" name="default_gst_rate" className="form-input" defaultValue={v.default_gst_rate} />
              </div>
              <div className="form-group">
                <label htmlFor="fy_start_month" className="form-label">Financial year starts</label>
                <select id="fy_start_month" name="fy_start_month" className="form-select" defaultValue={v.fy_start_month}>
                  {data.months.map(([n, name]) => <option key={n} value={n}>{name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="advance_basis" className="form-label">Proforma advance usually on</label>
                <select id="advance_basis" name="advance_basis" className="form-select" defaultValue={v.advance_basis}>
                  <option value="pre_tax">Value before tax</option>
                  <option value="total">Total including tax</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="payment_days" className="form-label">Usual payment terms (days)</label>
                <input type="number" id="payment_days" name="payment_days" className="form-input" min={0} max={365} step={1} inputMode="numeric"
                       defaultValue={v.payment_days} placeholder="30" />
                <p className="form-text">Days after the invoice date customers pay, unless a customer has their own. Sets when invoices count as overdue; not printed.</p>
              </div>
            </div>

            <h3 style={{ margin: 'var(--spacing-md) 0 var(--spacing-sm)' }}>Numbering</h3>
            <p className="form-text" style={{ margin: '0 0 var(--spacing-md)' }}>
              Tokens: <span className="kbd">{'{num}'}</span> or <span className="kbd">{'{num:03}'}</span> for zero-padding,{' '}
              <span className="kbd">{'{fy}'}</span> financial year (26-27), <span className="kbd">{'{yyyy}'}</span>.
              Each type restarts at 1 every financial year. Set "next" to continue an existing series.
            </p>
            <label style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 'var(--spacing-md)', fontSize: 'var(--font-size-sm)' }}>
              <input type="checkbox" name="separate_export_series" className="form-checkbox" defaultChecked={data.checks.separate_export_series} />
              Number export invoices separately (by default they continue the tax-invoice series)
            </label>
            <div className="table-container" style={{ boxShadow: 'none' }}>
              <table className="table">
                <thead><tr><th>Document</th><th>Format</th><th>Next number</th><th>Preview</th></tr></thead>
                <tbody>
                  {data.series.map((s) => (
                    <tr key={s.key}>
                      <td>{s.label}</td>
                      <td><input type="text" name={`format_${s.key}`} defaultValue={s.format} className="form-input" style={{ minWidth: 160 }}
                                 aria-label={`${s.label} format`} /></td>
                      <td>
                        {s.shared ? <span className="text-tertiary">Shares the Tax Invoice series</span>
                          : <input type="number" min={1} name={`next_${s.key}`} defaultValue={s.next ?? ''} className="form-input" style={{ width: 90 }}
                                   aria-label={`${s.label} next number`} />}
                      </td>
                      <td className="item-id" style={{ fontSize: 'var(--font-size-sm)' }}>{s.preview}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Custom fields</h2>
              <p className="card-subtitle">Anything else you need on your documents. Ticked fields are printed.</p>
            </div>
          </div>
          <div className="card-body">
            <h3 style={{ margin: '0 0 var(--spacing-xs)' }}>About your organization</h3>
            <p className="form-text" style={{ margin: '0 0 var(--spacing-sm)' }}>e.g. MSME / Udyam no., CIN, vendor registration no. Printed under your address.</p>
            <FieldRows prefix="orgcf" rows={data.custom_fields} withValue labelHint="MSME No." valueHint="UDYAM-TN-00-0000000" />
            <h3 style={{ margin: 'var(--spacing-xl) 0 var(--spacing-xs)' }}>On every customer</h3>
            <p className="form-text" style={{ margin: '0 0 var(--spacing-sm)' }}>e.g. Vendor code, Plant, PAN, EIN. Each customer gets these fields; ticked ones print in the consignee block.</p>
            <FieldRows prefix="custcf" rows={data.customer_fields} withValue={false} labelHint="Vendor code" />
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Quotation defaults</h2></div>
          <div className="card-body">
            <div className="form-group">
              <label htmlFor="quote_intro" className="form-label">Opening paragraph</label>
              <textarea id="quote_intro" name="quote_intro" className="form-textarea" rows={3} defaultValue={v.quote_intro}
                        placeholder="We thankfully acknowledge the receipt of your above enquiry…" />
            </div>
            <div className="form-group">
              <label htmlFor="quote_terms" className="form-label">Terms &amp; conditions (one per line)</label>
              <textarea id="quote_terms" name="quote_terms" className="form-textarea" rows={5} defaultValue={v.quote_terms}
                        placeholder={'Taxes: 18% GST\nOffer validity – 30 days'} />
            </div>
            <div className="form-group">
              <label htmlFor="quote_closing" className="form-label">Closing paragraph</label>
              <textarea id="quote_closing" name="quote_closing" className="form-textarea" rows={3} defaultValue={v.quote_closing} />
            </div>
            <p className="form-text">Leave empty to use DocuMint's defaults. Every new quotation starts with these; you can edit them per quote.</p>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Letterhead</h2></div>
          <div className="card-body">
            <fieldset className="letterhead-style">
              <legend className="form-label">Quotation letterhead</legend>
              <label className="form-check"><input type="radio" name="letterhead_style" value="centred" defaultChecked={v.letterhead_style !== 'left'} /> Centred: logo, name and address in the middle</label>
              <label className="form-check"><input type="radio" name="letterhead_style" value="left" defaultChecked={v.letterhead_style === 'left'} /> Logo on the left, address opposite</label>
            </fieldset>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="letterhead_color" className="form-label">Colour</label>
                <input type="color" id="letterhead_color" name="letterhead_color" defaultValue={v.letterhead_color} className="form-input color-input" />
                <p className="form-text">The name, the address and the line under them.</p>
              </div>
              <div className="form-group">
                <label htmlFor="letterhead_accent" className="form-label">Accent</label>
                <input type="color" id="letterhead_accent" name="letterhead_accent" defaultValue={v.letterhead_accent} className="form-input color-input" />
                <p className="form-text">The bar under a centred letterhead, or where the line starts under the logo.</p>
              </div>
            </div>
            <div className="form-row">
              <Image name="logo" label="Logo" src={data.images.logo} help="Printed at the top of quotations, invoices and proformas." />
              <Image name="logo_small" label="Logo for invoices (optional)" src={data.images.logo_small}
                     help="A smaller version for invoices and proformas, which print the name as text beside it." />
            </div>
            <label className="form-check">
              <input type="checkbox" name="logo_has_name" className="form-checkbox" defaultChecked={data.checks.logo_has_name} />{' '}
              The logo already says the company's name, so quotations print it in place of the typed name
            </label>
            <p className="form-text">PNG or JPEG, up to 300 KB, with a transparent background.</p>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Stamp &amp; signature</h2></div>
          <div className="card-body">
            <div className="form-row">
              <Image name="stamp" label="Company stamp" src={data.images.stamp} />
              <Image name="signature" label="Signature" src={data.images.signature} />
            </div>
            <div className="form-row">
              <Text name="signatory_name" label="Signed by" value={v.signatory_name} placeholder="A. Kumar" help="Name printed under the signature on quotations" />
            </div>
            <p className="form-text">PNG or JPEG, up to 300 KB. A PNG with a transparent background looks best for stamps and signatures.</p>
          </div>
        </section>

        <div className="flex-between" style={{ marginBottom: 'var(--spacing-2xl)' }}>
          <button type="submit" className="btn btn-primary btn-lg">Save profile</button>
        </div>
      </form>

      <section className="card panel-medium" style={{ maxWidth: 880 }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Starter templates</h2>
            <p className="card-subtitle">Quotation, export quotation, proforma, tax and export invoice. Existing templates are kept.</p>
          </div>
          <form method="post" action={data.starter}>
            <button type="submit" className="btn btn-secondary"><Icon name="plus" />Add starter templates</button>
          </form>
        </div>
      </section>
    </>
  );
}

export default function Profile() {
  const { data, error } = useLoad<Data>('/api/settings/profile', "Couldn't load the business profile. Check your connection.");
  return data ? <ProfileForm data={data} /> : <Loading title="Business profile" kind="page" error={error} />;
}
