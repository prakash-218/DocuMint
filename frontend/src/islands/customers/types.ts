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
  /** customers, or suppliers (the same companies: one can be both) */
  kind: 'customer' | 'supplier';
  new_label: string;
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
  /** What an empty payment terms field means for them, as its placeholder: '30 days (your usual)' */
  payment_empty: string;
  custom: { key: string; label: string; value: string }[];
  /** A GSTIN's first two digits → the state it's registered in ('33' → Tamil Nadu). */
  gst_states: Record<string, string>;
  /** A company says whether it's a customer, a supplier or both; a site is what its company is. */
  kinds: boolean;
}
