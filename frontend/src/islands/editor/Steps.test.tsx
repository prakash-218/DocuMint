import { render, screen } from '../../test/render';
import { describe, expect, it } from 'vitest';
import { ProjectStep } from './Steps';
import type { ProjectStep as ProjectData } from './types';

const STEP: ProjectData = {
  step: 'project', title: 'New purchase order', type: { key: 'purchase_order', label: 'Purchase Order' }, has_open_projects: false,
  options: '/projects/options?status=open', open_url: '/purchase-orders/create?project_id=__ID__',
  new_project: { action: '/projects/new', next: 'purchase_order', customers: [], add_customer: null },
};

describe("a new document's project", () => {
  it('lets a purchase order go on without one', () => {
    render(<ProjectStep data={{ ...STEP, no_project: '/purchase-orders/create?doc_type=purchase_order&project_id=none' }} />);
    expect(screen.getByRole('link', { name: 'Continue without a project' }))
      .toHaveAttribute('href', '/purchase-orders/create?doc_type=purchase_order&project_id=none');
  });

  it("doesn't let a sale", () => {
    render(<ProjectStep data={{ ...STEP, type: { key: 'quote', label: 'Quotation' }, no_project: null }} />);
    expect(screen.queryByRole('link', { name: 'Continue without a project' })).toBeNull();
  });
});
