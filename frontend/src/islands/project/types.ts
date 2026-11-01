// GET /api/projects/<id> (project_view.build)

export type Tone = 'action' | 'wait' | 'late' | 'done' | 'draft';
export type StepState = 'done' | 'now' | 'todo' | 'skipped' | 'late';

export interface Step {
  key: string;
  label: string;
  state: StepState;
  sub: string;
}

export type Action =
  | { kind: 'link'; label: string; href: string; primary: boolean }
  | { kind: 'post'; label: string; action: string; fields: Record<string, string>; primary: boolean; confirm: string | null }
  | { kind: 'email'; label: string; invoice_id: string | null; primary: boolean }
  | { kind: 'status'; label: string; status: string; primary: boolean }
  | { kind: 'dialog'; label: string; dialog: string; primary: boolean };

export interface Doc {
  invoice_id: string;
  doc_type: 'quote' | 'proforma' | 'invoice' | 'export_invoice' | 'purchase_order' | 'credit_note' | 'debit_note';
  /** Who it's to: the customer, or a purchase order's supplier. */
  party?: string | null;
  /** A note against an invoice: -1 a credit note (takes its total off), 1 a debit note; 0 otherwise. */
  adjusts?: number;
  /** A note's invoice number. */
  against?: string | null;
  /** Money paid back on a credit note. */
  refunded?: number;
  site?: string | null;
  kind: string;
  number: string;
  status: string;
  issue_date: string | null;
  currency: string | null;
  total: number;
  paid: number;
  balance: number | null;
  url: string;
  pdf: string;
  versions: { invoice_id: string; number: string; issue_date: string | null; total: number; url: string }[];
}

/** Where the job stands on one count, apart from the others (project_view.statuses). */
export interface Progress {
  key: 'quotation' | 'advance' | 'material' | 'invoiced' | 'paid';
  label: string;
  text: string;
  sub: string;
  /** How far along, 0 to 1. */
  bar: number;
  /** none: not taken on this job; todo: not reached yet. */
  tone: 'done' | 'now' | 'late' | 'todo' | 'none';
}

/** A document in the thread (project_view.thread): the document itself is in documents or purchases. */
export interface DocEntry {
  id: string;
  type: 'document';
  kind: Doc['doc_type'];
  invoice_id: string;
  purchase: boolean;
  when: string | null;
  /** What happened to it, newest first. */
  history: { title: string; when: string | null; who: string | null }[];
}

export type ThreadItem = TimelineItem | DocEntry;

export interface TimelineItem {
  id: string;
  type: 'event' | 'note' | 'email';
  kind: string;
  title: string;
  body: string | null;
  when: string | null;
  who: string | null;
  link: string | null;
  thread_id?: string;
  files?: number;
  direction?: 'in' | 'out';
}

export interface Person {
  contact_id: string;
  customer_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  role: string | null;
  gets: 'all' | 'billing' | 'none';
  usually: 'all' | 'billing' | 'none';
  initials: string;
  at_parent: boolean;
}

export interface FileRow {
  id: string;
  name: string;
  kind: string;
  kind_label: string;
  title: string | null;
  reference_no: string | null;
  date: string | null;
  size: string;
  from_email: boolean;
  url: string;
  /** Where its delete form posts. */
  delete?: string;
}

export interface MoneyRow {
  currency: string;
  quoted: number;
  invoiced?: number;
  received?: number;
  advance_held?: number;
  due?: number;
}

export interface Page {
  project: {
    id: string;
    label: string;
    title: string;
    reference: string;
    notes: string;
    fiscal_year: string;
    status: 'open' | 'completed' | 'cancelled';
    created_at: string | null;
    customer: { id: string; name: string; site: string | null; url: string };
    po: { number: string; date: string | null; amount: number | null; currency: string | null } | null;
  };
  can: { edit: boolean; manage: boolean; read_mail: boolean; sales: boolean };
  stage: { steps: Step[]; current: string | null; pill: { text: string; tone: Tone } };
  /** Quotation, advance, material, invoiced, paid; Sales get the quotation only. */
  progress: Progress[];
  next: { tone: Tone; text: string; sub: string; actions: Action[] };
  money: MoneyRow[];
  documents: Doc[];
  /** What's bought for it: purchase orders to suppliers. */
  purchases?: Doc[];
  new_document: Partial<Record<'quote' | 'proforma' | 'invoice' | 'purchase_order', string>>;
  /** Everything on the job, newest first: documents (with their history), payments, emails, notes, the rest. */
  timeline: ThreadItem[];
  people: Person[];
  found: {
    people: { name: string; email: string; phone: string | null; seen: string }[];
    phones: { contact_id: string; name: string; phone: string; value: string; replaces: string | null }[];
  };
  gets: Record<string, string>;
  usually: Record<string, string>;
  files: FileRow[];
  upload: { action: string; kinds: Record<string, string> } | null;
  costings: { id: string; title: string; currency: string | null; cost: number; price: number;
              profit_on_cost: number | null; quote_number: string | null; url: string }[] | null;
  /** The customer's documents in no project, to add to this one. */
  addable?: { invoice_id: string; number: string; kind: string; total: number; currency: string }[];
  links?: { documents: string | null; delete: string | null; new_costing: string | null; rates: string | null };
  years: string[];
  statuses: Record<string, string>;
}
