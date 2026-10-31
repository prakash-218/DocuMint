// GET /api/editor/new/<group> and /api/editor/<id> (editor_page.py): a new document's step, or the editor.

export interface Field {
  id: string;
  name: string;              // what formulas call it: this.qty, SUM(items.amount)
  label: string;
  data_type: 'string' | 'number' | 'date' | 'boolean';
  formula: string | null;    // worked out, never typed
  money: boolean;
  required: boolean;
  long: boolean;             // the item's description: a growing text box
}

export type Value = string | boolean;

export interface Section {
  id: string;
  type: 'line_item' | 'normal';
  title: string;
  name: string;              // the section's name in formulas (lower case)
  fields: Field[];
  amount_field?: string | null;  // a line's amount, which its discount comes off (null: lines can't be discounted)
  rows?: { row: number; values: Record<string, Value>; discount?: string }[];
  values?: Record<string, Value>;
}

export interface CustomerGroup {
  label: string | null;
  options: { id: string; label: string }[];
}

export interface ProjectRef {
  id: string;
  label: string;
  title: string;
  url: string;
  customer_id: string;
  customer_name: string | null;
}

export interface EditorData {
  step: 'editor';
  title: string;
  correcting: boolean;
  editing: boolean;
  type: { key: string; label: string; sent_word: string; takes_payments: boolean; proforma: boolean; due_label: string };
  project: ProjectRef | null;
  template_name: string;
  change_template: string | null;
  action: string;
  cancel: string;
  submit: string;
  submit_side: string;
  hidden: Record<string, string>;
  /** Who it's to: label Customer, or Supplier for a purchase order (add: a new supplier, when there's none). */
  customer: { fixed: { id: string | null; name: string | null } | null; groups: CustomerGroup[]; label?: string; add?: string | null };
  number: { value: string; required: boolean };
  issue_date: string;
  due_date: string;
  sections: Section[];
  discount: string;          // on the whole document, as typed: '10%', '5000', ''
  details: {
    fields: { key: string; label: string; kind: 'text' | 'date' | 'textarea'; placeholder: string; group: string }[];
    values: Record<string, string>;
    groups: { key: string; label: string; fields: string[]; open: boolean }[];
  };
  settings: { currencies: string[]; currency: string; tax_modes: [string, string][]; tax_mode: string; tax_rate: string;
              advance_percent: string; advance_basis: 'pre_tax' | 'total' };
  /** customer_id → the tax its GSTIN or state suggests, and why: 'Karnataka GSTIN, another state, so IGST'. */
  tax_hints: Record<string, { mode: string; note: string }>;
  /** The same for a customer that can't be changed here: a draft's, or its project's. */
  tax_hint?: { mode: string; note: string } | null;
}

export interface ProjectStep {
  step: 'project';
  title: string;
  type: { key: string; label: string };
  has_open_projects: boolean;
  options: string;
  open_url: string;           // with __ID__ for the project
  new_project: { action: string; next: string; customers: CustomerGroup[]; add_customer: string | null };
}

export interface TemplateLink {
  name: string;
  currency: string | null;
  href: string;
}

export interface TemplateStep {
  step: 'template';
  title: string;
  type: { key: string; label: string };
  missing: boolean;
  project: ProjectRef | null;
  templates: TemplateLink[];
  others: TemplateLink[];
  templates_page: string;
}

export type EditorResponse = EditorData | ProjectStep | TemplateStep;
