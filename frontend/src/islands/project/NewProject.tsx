import { PageHeader } from '../../app/PageHeader';
import { Loading, useLoad } from '../../app/ui';
import { CustomerOptions } from '../editor/Editor';
import type { CustomerGroup } from '../editor/types';

// A new project (GET /api/new-project, project_view.new_project): who it's for, its name, the customer's reference,
// its financial year and notes. It posts to projects_bp.create_project, which opens the project.

interface Data {
  title: string;
  action: string;
  cancel: string;
  customers: CustomerGroup[];
  customer_id: string;
  years: string[];
}

export function NewProjectForm({ data }: { data: Data }) {
  return (
    <>
      <PageHeader title={data.title} heading />
      <form method="post" action={data.action} className="card panel-medium" style={{ maxWidth: 640 }}>
        <div className="card-body">
          <div className="form-group">
            <label htmlFor="customer_id" className="form-label">Customer *</label>
            <select id="customer_id" name="customer_id" className="form-select" required defaultValue={data.customer_id}>
              <option value="">Select a customer</option>
              <CustomerOptions groups={data.customers} />
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="title" className="form-label">Project name *</label>
            <input type="text" id="title" name="title" className="form-input" required maxLength={200} placeholder="Welding fixture for Line 3" />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="reference" className="form-label">Customer reference</label>
              <input type="text" id="reference" name="reference" className="form-input" maxLength={100} placeholder="Enquiry / RFQ no." />
            </div>
            <div className="form-group">
              <label htmlFor="fiscal_year" className="form-label">Financial year</label>
              <select id="fiscal_year" name="fiscal_year" className="form-select">
                {data.years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="notes" className="form-label">Notes</label>
            <textarea id="notes" name="notes" className="form-textarea" rows={3} />
          </div>
          <div className="form-actions" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
            <button type="submit" className="btn btn-primary">Create project</button>
            <a href={data.cancel} className="btn btn-secondary">Cancel</a>
          </div>
        </div>
      </form>
    </>
  );
}

export default function NewProject({ search }: { search: string }) {
  const { data, error } = useLoad<Data>(`/api/new-project${search}`, "Couldn't load the form. Check your connection.");
  return data ? <NewProjectForm data={data} /> : <Loading title="New project" kind="page" error={error} heading />;
}
