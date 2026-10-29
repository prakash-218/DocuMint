import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad, usePosted } from '../../app/ui';

// The organization's name and address (GET /api/settings/organizations/<id>, settings_view.organization), printed
// on documents. It posts to settings_bp.edit_organization; without a name it comes back with what was typed.

interface Data {
  title: string;
  action: string;
  cancel: string;
  domain: string;
  values: Record<string, string>;
}

function Field({ name, label, value, placeholder }: { name: string; label: string; value: string; placeholder?: string }) {
  return (
    <div className="form-group">
      <label htmlFor={name} className="form-label">{label}</label>
      <input type="text" id={name} name={name} className="form-input" defaultValue={value} placeholder={placeholder} />
    </div>
  );
}

export function OrgFormView({ data }: { data: Data }) {
  const posted = usePosted();
  const v = (key: string) => posted?.[key] ?? data.values[key] ?? '';
  return (
    <>
      <PageHeader title={data.title} heading description="Changes appear on documents made from now on." />
      <form method="post" action={data.action} className="card panel-medium" style={{ maxWidth: 600 }}>
        <div className="card-body">
          <div className="form-group">
            <label htmlFor="name" className="form-label">Organization name *</label>
            <input type="text" id="name" name="name" className="form-input" required defaultValue={v('name')} autoFocus />
          </div>
          <div className="form-group">
            <label htmlFor="domain" className="form-label">Domain</label>
            <input type="text" id="domain" className="form-input" value={data.domain} disabled />
            <p className="form-text">The domain can't be changed.</p>
          </div>
          <h3 style={{ margin: 'var(--spacing-lg) 0 var(--spacing-xs)' }}>Address</h3>
          <p className="form-text" style={{ margin: '0 0 var(--spacing-md)' }}>Printed on your documents.</p>
          <Field name="street_address" label="Street address" value={v('street_address')} placeholder="123 Main Street" />
          <div className="form-row">
            <Field name="city" label="City" value={v('city')} />
            <Field name="state" label="State / province" value={v('state')} />
          </div>
          <div className="form-row">
            <Field name="zip_code" label="PIN / ZIP code" value={v('zip_code')} />
            <Field name="country" label="Country" value={v('country')} />
          </div>
          <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
            <button type="submit" className="btn btn-primary">Save</button>
            <a href={data.cancel} className="btn btn-secondary">Cancel</a>
          </div>
        </div>
      </form>
    </>
  );
}

export default function OrgForm({ orgId }: { orgId: string }) {
  const { data, error } = useLoad<Data>(`/api/settings/organizations/${orgId}`, "Couldn't load the form. Check your connection.");
  return data ? <OrgFormView data={data} /> : <Loading title="Name & address" kind="page" error={error} heading />;
}
