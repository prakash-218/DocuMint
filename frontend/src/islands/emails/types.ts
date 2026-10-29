// GET /api/emails and /api/emails/<thread_id> (email_view.py).
import type { Filter, PageInfo } from '../../app/ui';

export interface Inbox {
  title: string;
  accounts: string;          // the mailboxes, or that none are synced yet
  problems: string[];        // a mailbox's last error
  sync: string | null;       // owners and admins: Sync now
  filters: Filter[];
  threads: {
    id: string; url: string; subject: string; count: number; from: string; customer: string; project: string;
    files: number; snippet: string; when: string | null;
  }[];
  page: PageInfo;
  empty: string;
}

export interface Thread {
  title: string;
  count: number;
  customer: { id: string; name: string; url: string } | null;
  project: { id: string; label: string; title: string; url: string } | null;
  back: string;
  messages: {
    id: string; from_name: string; from_address: string; to: string; cc: string; sent_at: string | null; body: string;
    outgoing: boolean; files: { name: string; url: string; size: string }[];
  }[];
  link: { action: string; options: string; auto: string };
}

/** projects_bp.picker_options */
export interface ProjectOption {
  id: string;
  no: string;
  title: string;
  customer_id: string;
  fy: string;
  status: string;
}
