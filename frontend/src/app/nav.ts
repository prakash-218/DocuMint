// The sidebar's active link, worked out as nav.active() does on the server: the link whose prefix is the
// longest one the path starts with (/settings/audit-log is Audit log, not Settings).
import type { IconName } from '../icons';
import type { NavSection } from './boot';

export function activeKey(sections: NavSection[], path: string): string | null {
  let best: string | null = null;
  let length = -1;
  for (const section of sections) {
    for (const item of section.items) {
      const prefix = item.prefix;
      const on = path === prefix || path.startsWith(`${prefix.replace(/\/$/, '')}/`);
      if (on && prefix.length > length) {
        best = item.key;
        length = prefix.length;
      }
    }
  }
  return best;
}

// The sidebar's Lucide names, as icons.tsx has them
const ICONS: Record<string, IconName> = {
  house: 'house', 'layout-dashboard': 'layoutDashboard', bell: 'bell', briefcase: 'briefcase', mail: 'mail',
  'file-pen-line': 'filePenLine', 'file-clock': 'fileClock', 'file-text': 'fileText', users: 'users',
  'layout-template': 'layoutTemplate', list: 'list', settings: 'settings', history: 'history', plus: 'plus',
};

export function lucide(name: string): IconName {
  return ICONS[name] ?? 'file';
}
