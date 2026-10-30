import { Dropdown } from '../../mantine/Dropdown';
import { useEffect } from 'react';
import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad, usePosted } from '../../app/ui';
import type { CustomerForm as Data } from './types';

// A customer's details, new (?parent_id= adds a site of that customer) or to edit. It posts the server page's form to
// customers_bp.create_customer or edit_customer; when that doesn't save (no name, odd payment terms), the app comes
// back with what was typed.

function Text({ name, label, value, help, ...rest }: {
  name: string; label: string; value: string; help?: string; placeholder?: string; maxLength?: number; required?: boolean; autoFocus?: boolean;
}) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      <input type="text" id={name} name={name} className="form-input" defaultValue={value} {...rest} />
      {help && <p className="form-text">{help}</p>}
    </div>
  );
}

export function CustomerFormView({ data }: { data: Data }) {
  const posted = usePosted();
  const v = (key: string) => posted?.[key] ?? data.values[key] ?? '';
  useEffect(() => {
    if (data.name) document.title = `Edit ${data.name} · DocuMint`;
  }, [data.name]);
  return (
    <>
      <PageHeader title={data.title} heading />
      <form method="post" action={data.action} className="panel-medium">
        <section className="card">
          <div className="card-body">
            <Text name="name" label="Name" value={v('name')} help="The legal name printed on documents." required autoFocus />
            {data.site_count ? (
              <p className="form-text">{data.site_count} site{data.site_count === 1 ? '' : 's'} belong{data.site_count === 1 ? 's' : ''} to this
                customer, so it can't be a site itself.</p>
            ) : (
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="parent_id" className="form-label">Site of</label>
                  <Dropdown id="parent_id" name="parent_id" defaultValue={v('parent_id')}
                            data={[{ value: '', label: 'A customer of its own' }, ...data.parents.map((p) => ({ value: p.id, label: p.name }))]} />
                  <p className="form-text">A plant, branch, division or sister company of another customer.</p>
                </div>
                <Text name="site_name" label="Site name" value={v('site_name')} maxLength={100} placeholder="Gears Division, Madurai plant"
                      help="Tells it apart from the other sites. Defaults to the city." />
              </div>
            )}
            <div className="form-row">
              <Text name="tax_id" label="GSTIN / Tax ID" value={v('tax_id')} />
              <Text name="email_domains" label="Email domains" value={v('email_domains')} placeholder="hydroparts.com, hydroparts.us"
                    help={data.domains_help} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="payment_days" className="form-label">Payment terms (days)</label>
                <input type="number" id="payment_days" name="payment_days" className="form-input" min={0} max={365} step={1} inputMode="numeric"
                       defaultValue={v('payment_days')} placeholder="30" />
                <p className="form-text">{data.payment_help}</p>
              </div>
            </div>
            <Text name="street_address" label="Address" value={v('street_address')} />
            <div className="form-row">
              <Text name="city" label="City" value={v('city')} />
              <Text name="state" label="State" value={v('state')} />
            </div>
            <div className="form-row">
              <Text name="zip_code" label="PIN / ZIP code" value={v('zip_code')} />
              <Text name="country" label="Country" value={v('country')} />
            </div>
            {data.custom.length > 0 && (
              <div className="form-row">
                {data.custom.map((f) => <Text key={f.key} name={`custom_${f.key}`} label={f.label} value={posted?.[`custom_${f.key}`] ?? f.value} />)}
              </div>
            )}
          </div>
        </section>
        <div className="form-actions">
          <button type="submit" className="btn btn-primary">{data.submit}</button>
          <a href={data.cancel} className="btn btn-ghost">Cancel</a>
        </div>
      </form>
    </>
  );
}

/** source: /api/customers/new?parent_id= or /api/customers/<id>/form */
export default function CustomerForm({ source, title }: { source: string; title: string }) {
  const { data, error } = useLoad<Data>(source, "Couldn't load the form. Check your connection.");
  return data ? <CustomerFormView data={data} /> : <Loading title={title} kind="page" error={error} heading />;
}
