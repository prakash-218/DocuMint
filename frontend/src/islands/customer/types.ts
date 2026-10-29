// GET /api/customers/<id> (customer_view.build)
import type { Row } from '../board/ProjectsBoard';
import type { Doc, FileRow } from '../project/types';

export type Totals = Record<string, number>;

export interface StatementLine {
  date: string | null;
  fy: string | null;
  text: string;
  sub: string;
  owed: number;
  paid: number;
  balance: number;
  url: string;
}

export interface Account {
  currency: string;
  owed: number;
  paid: number;
  balance: number;
  lines: StatementLine[];
}

export interface Money {
  total: Totals;
  count: number;
  ages: { label: string; count: number; total: Totals }[];
  /** Only for a customer with sites: what each owes. */
  customers?: { id: string; name: string; count: number; total: Totals }[];
  advances: { count: number; total: Totals };
  advance_held: Totals;
  statement: Account[];
}

export interface Contact {
  contact_id: string;
  customer_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  role: string | null;
  gets: 'all' | 'billing' | 'none';
  initials: string;
  at_parent: boolean;
}

export interface FileGroup {
  project: { id: string; title: string; label: string; url: string | null } | null;
  /** Each file also says whose it is (a company's page lists its sites' too) and where moving it posts. */
  files: (FileRow & { customer_id?: string; move?: string })[];
}

export interface CustomerData {
  customer: {
    id: string;
    name: string;
    site: string | null;
    parent: { id: string; name: string; url: string } | null;
    tax_id: string | null;
    email_domains: string | null;
    address: string[];
    archived: boolean;
    custom: { label: string; value: string }[];
    /** How GST applies to them: 'Tamil Nadu, so CGST + SGST'. */
    tax_note: string;
    /** When they pay: '30 days', '45 days, as their parent company', '30 days (your usual terms)'; '' when not set. */
    payment_terms: string;
    classic_url: string;
  };
  can: { edit: boolean; edit_customer: boolean; manage: boolean; sales: boolean };
  /** null for Sales: what a customer owes isn't theirs to see. */
  money: Money | null;
  projects: Row[];
  documents: (Doc & { site: string | null; project_id: string | null })[];
  statuses: Record<string, string>;
  files: FileGroup[];
  files_count: number;
  people: Contact[];
  usually: Record<string, string>;
  sites: { id: string; name: string; tax_id: string | null; archived: boolean; documents: number; url: string }[];
  links: {
    new_project: string | null; new_quote: string | null; edit: string | null; add_site: string | null; archive?: string | null;
    /** The statement as a PDF (add ?fy=26-27 or all, &currency=). */
    statement_pdf?: string | null;
    /** Emailing the statement: where the email form loads from and sends to. */
    statement_email?: { compose: string; send: string } | null;
  };
  upload?: { action: string; kinds: Record<string, string> } | null;
  /** Owners and admins: the customer portal login, or where giving one posts. */
  portal?: { email: string | null; login_url: string; create: string | null } | null;
}
