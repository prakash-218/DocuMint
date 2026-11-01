import type { NoteRow, Refunds } from './Notes';
import type { Receiving } from './Receiving';
// GET /api/document/<id> (document_page.py): everything a document's page shows.
import type { Page, Tone } from '../project/types';
import type { Head } from './DocumentNext';

export interface PdfMenu {
  seal: boolean;
  links: { label: string; icon: string; href: string }[];
  packing: string | null;
  delete: string | null;
}

export interface Change {
  number: string;
  short: string;
  correct: string;
  revise: { possible: boolean; number: string; note: string | null; action: string; current_template: string;
            templates: { id: string; name: string; same: boolean }[] } | null;
  reopen: { blocker: string | null; action: string };
}

export interface PaymentRow {
  id: string;
  date: string | null;
  amount: number;
  label: string;
  method: string | null;
  reference: string | null;
  credited: { amount: number; currency: string; rate: string | null } | null;
  applied: { number: string; url: string } | null;
  take_off: { action: string; confirm: string } | null;
}

export interface Payments {
  title: string;
  rows: PaymentRow[];
  empty: string;
  record_label: string | null;
  record: { action: string; advance: boolean; title: string; button: string; suggested: number | null; currency: string;
            base_currency: string; today: string; methods: string[] } | null;
  apply: { action: string; note: string; button: string;
           rows: { payment_id: string; amount: number; number: string; date: string | null; reference: string | null; checked: boolean }[] } | null;
}

export interface DocumentData {
  invoice_id: string;
  project_id: string | null;
  number: string;
  doc_type: string;
  status: string;
  currency: string;
  list: { label: string; url: string };
  head: Head;
  next: Page['next'];
  money: { label: string; value: number; cap: string; late?: boolean }[] | null;
  pdf: PdfMenu;
  /** A draft: its editor. */
  edit: string | null;
  /** Sent, and you may send it: the share dialog's data (api_bp.share). */
  share: string | null;
  change: Change | null;
  payments: Payments | null;
  /** A purchase order's: what's arrived (Receiving.tsx). */
  receiving?: Receiving | null;
  /** An invoice's credit and debit notes; a credit note's refunds (Notes.tsx). */
  notes?: { rows: NoteRow[] } | null;
  refunds?: Refunds | null;
  versions_html: string | null;
  document_html: string;
  chain: { kind: string; number: string; pill: { text: string; tone: Tone }; total: number; currency: string; url: string; here: boolean; paid: boolean }[];
  people: { list: { name: string; role: string | null; email: string | null; initials: string }[]; url: string | null; empty: string } | null;
  activity: { title: string; body: string | null; when: string | null; who: string | null; icon: string; tone: string }[];
  convert: { label: string; action: string; targets: { key: string; label: string; template: string }[]; templates: { id: string; name: string }[];
             discount: string | null } | null;     // its discounts in words, when it has any: keep them, or take them into the prices
  project: {
    project: { title: string; label: string; fy: string | null; reference: string | null; url: string } | null;
    others: { number: string; url: string; kind: string; versions: number }[];
    change: { action: string; options: string } | null;
  };
  files: Page['files'];
  upload: { action: string } | null;
}
