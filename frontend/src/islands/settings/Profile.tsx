import { Dropdown, choices } from '../../mantine/Dropdown';
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

function Text({ name, label, value, placeholder }: { name: string; label: string; value: string; placeholder?: string }) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      <input type="text" id={name} name={name} className="form-input" defaultValue={value} placeholder={placeholder} />
    </div>
  );
}

function Image({ name, label, src }: { name: string; label: string; src: string | null }) {
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
              <Text name="gstin" label="GSTIN" value={v.gstin} placeholder="33ABCDE1234F1Z5" />
              <Text name="pan" label="PAN" value={v.pan} placeholder="ABCDE1234F" />
              <Text name="state_code" label="State code" value={v.state_code} placeholder="33" />
            </div>
            <div className="form-row">
              <Text name="iec_code" label="IEC code" value={v.iec_code} />
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
              <Text name="bank_swift" label="SWIFT code" value={v.bank_swift} />
            </div>
            <Text name="upi_id" label="UPI ID" value={v.upi_id} placeholder="yourname@okhdfcbank" />
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Documents</h2></div>
          <div className="card-body">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="default_currency" className="form-label">Main currency</label>
                <Dropdown id="default_currency" name="default_currency" defaultValue={v.default_currency} data={choices(data.currencies)} />
              </div>
              <div className="form-group">
                <label htmlFor="default_gst_rate" className="form-label">Default GST rate (%)</label>
                <input type="number" step="0.01" id="default_gst_rate" name="default_gst_rate" className="form-input" defaultValue={v.default_gst_rate} />
              </div>
              <div className="form-group">
                <label htmlFor="fy_start_month" className="form-label">Financial year starts</label>
                <Dropdown id="fy_start_month" name="fy_start_month" defaultValue={v.fy_start_month} data={choices(data.months)} />
              </div>
              <div className="form-group">
                <label htmlFor="advance_basis" className="form-label">Proforma advance usually on</label>
                <Dropdown id="advance_basis" name="advance_basis" defaultValue={v.advance_basis}
                          data={[{ value: 'pre_tax', label: 'Value before tax' }, { value: 'total', label: 'Total including tax' }]} />
              </div>
              <div className="form-group">
                <label htmlFor="payment_days" className="form-label">Usual payment terms (days)</label>
                <input type="number" id="payment_days" name="payment_days" className="form-input" min={0} max={365} step={1} inputMode="numeric"
                       defaultValue={v.payment_days} placeholder="30" />
              </div>
            </div>

            <h3 style={{ margin: 'var(--spacing-md) 0 var(--spacing-md)' }}>Numbering</h3>
            <label style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 'var(--spacing-md)', fontSize: 'var(--font-size-sm)' }}>
              <input type="checkbox" name="separate_export_series" className="form-checkbox" defaultChecked={data.checks.separate_export_series} />
              Number export invoices separately
            </label>
            <div className="table-container" style={{ boxShadow: 'none' }}>
              <table className="table">
                <thead><tr><th>Document</th><th>Format</th><th>Next number</th><th>Preview</th></tr></thead>
                <tbody>
                  {data.series.map((s) => (
                    <tr key={s.key}>
                      <td>{s.label}</td>
                      <td><input type="text" name={`format_${s.key}`} defaultValue={s.format} className="form-input" style={{ minWidth: 160 }}
                                 placeholder="{num:03}/{fy}" aria-label={`${s.label} format`} /></td>
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
            <h2 className="card-title">Custom fields</h2>
          </div>
          <div className="card-body">
            <h3 style={{ margin: '0 0 var(--spacing-sm)' }}>About your organization</h3>
            <FieldRows prefix="orgcf" rows={data.custom_fields} withValue labelHint="MSME No." valueHint="UDYAM-TN-00-0000000" />
            <h3 style={{ margin: 'var(--spacing-xl) 0 var(--spacing-sm)' }}>On every customer</h3>
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
              <label htmlFor="quote_terms" className="form-label">Terms &amp; conditions</label>
              <textarea id="quote_terms" name="quote_terms" className="form-textarea" rows={5} defaultValue={v.quote_terms}
                        placeholder={'Taxes: 18% GST\nOffer validity – 30 days'} />
            </div>
            <div className="form-group">
              <label htmlFor="quote_closing" className="form-label">Closing paragraph</label>
              <textarea id="quote_closing" name="quote_closing" className="form-textarea" rows={3} defaultValue={v.quote_closing} />
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title">Letterhead</h2></div>
          <div className="card-body">
            <fieldset className="letterhead-style">
              <legend className="form-label">Quotation letterhead</legend>
              <label className="form-check"><input type="radio" name="letterhead_style" value="centred" defaultChecked={v.letterhead_style !== 'left'} /> Centred</label>
              <label className="form-check"><input type="radio" name="letterhead_style" value="left" defaultChecked={v.letterhead_style === 'left'} /> Logo on the left, address opposite</label>
            </fieldset>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="letterhead_color" className="form-label">Colour</label>
                <input type="color" id="letterhead_color" name="letterhead_color" defaultValue={v.letterhead_color} className="form-input color-input" />
              </div>
              <div className="form-group">
                <label htmlFor="letterhead_accent" className="form-label">Accent</label>
                <input type="color" id="letterhead_accent" name="letterhead_accent" defaultValue={v.letterhead_accent} className="form-input color-input" />
              </div>
            </div>
            <div className="form-row">
              <Image name="logo" label="Logo" src={data.images.logo} />
              <Image name="logo_small" label="Logo for invoices (optional)" src={data.images.logo_small} />
            </div>
            <label className="form-check">
              <input type="checkbox" name="logo_has_name" className="form-checkbox" defaultChecked={data.checks.logo_has_name} />{' '}
              The logo already shows the company's name
            </label>
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
              <Text name="signatory_name" label="Signed by" value={v.signatory_name} placeholder="A. Kumar" />
            </div>
          </div>
        </section>

        <div className="flex-between" style={{ marginBottom: 'var(--spacing-2xl)' }}>
          <button type="submit" className="btn btn-primary btn-lg">Save profile</button>
        </div>
      </form>

      <section className="card panel-medium" style={{ maxWidth: 880 }}>
        <div className="card-header">
          <h2 className="card-title">Starter templates</h2>
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
