// What the app starts with, from the page Flask sends (nav.boot, in <script id="boot">): who's signed in, the
// sidebar for their role, the links it needs, and the messages the last page left (flash).
import type { Me } from '../api';

export interface NavItem {
  key: string;
  label: string;
  icon: string;          // a Lucide name, as the server pages use: 'layout-dashboard'
  href: string;
  prefix: string;        // the addresses it's for: the longest prefix of the path wins
  also?: string[];       // other prefixes it's for: Invoices also lights up for /credit-notes/ and /debit-notes/
  badge: number;
}

export interface NavSection {
  title: string | null;
  items: NavItem[];
}

export interface NewItem {
  label: string;
  icon: string;
  href: string;
  divider?: boolean;
}

export interface Boot {
  me: Me;
  sidebar: NavSection[];
  orgs: { id: string; name: string }[];        // only when there's more than one to switch between
  links: { home: string; logout: string; select_org: string; search: string; new: NewItem[] };
  flashes: { category: string; text: string }[];
  posted?: { path: string; values: Record<string, string> } | null;   // a form that didn't save (nav.spa(posted=True))
}

export function readBoot(doc: Document = document): Boot {
  const el = doc.getElementById('boot');
  return JSON.parse(el?.textContent || '{}') as Boot;
}
