// GET /api/customers (customer_view.listing) and the customer form, /api/customers/new or /<id>/form (customer_view.form).
import type { Filter, PageInfo } from '../../app/ui';

export interface CustomerRow {
  id: string;
  url: string;
  name: string;
  sub: string;              // where they are, how many sites, archived
  tax_id: string;
  documents: number;
  archived: boolean;
  site: boolean;
}

export interface CustomerList {
  title: string;
  query: string;
  archived: boolean;
  any: boolean;
  new: string | null;
  filters: Filter[];
  groups: { customer: CustomerRow; sites: CustomerRow[] }[];
  page: PageInfo;
}

export interface CustomerForm {
  title: string;
  name: string | null;      // editing: the customer's name, for the tab
  action: string;
  cancel: string;
  submit: string;
  values: Record<string, string>;
  site_count: number;       // its sites: then it can't be a site itself
  parents: { id: string; name: string }[];
  domains_help: string;
  payment_help: string;
  custom: { key: string; label: string; value: string }[];
}
