import type { ComponentType } from 'react';

// The React screens a page can hold, by the name in its data-island attribute. Each loads on its own,
// only on the pages that have it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Island = ComponentType<any>;
export type Islands = Record<string, () => Promise<{ default: Island }>>;

export const islands: Islands = {
  'email-composer': () => import('./islands/EmailComposer'),
  'project-page': () => import('./islands/project/ProjectPage'),
  'projects-board': () => import('./islands/board/ProjectsBoard'),
  'home': () => import('./islands/home/Home'),
  'document-next': () => import('./islands/document/DocumentNext'),
  'customer-page': () => import('./islands/customer/CustomerPage'),
};
