import { render, screen } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Packing } from './PackingPage';
import type { PackingData } from './types';

const DATA: PackingData = {
  title: 'Packing for TF/EX/012', number: 'TF/EX/012', customer: 'Hydro Parts Inc', back: '/invoices/D-1',
  pdf: { href: '/invoices/D-1/pdf?page=packing', label: 'Packing list PDF' }, action: '/invoices/D-1/packing',
  packing_list_no: 'PL 900', marks: '',
  box_fields: [{ key: 'dimensions', label: 'Dimensions', sum: false }, { key: 'net_weight', label: 'Net Wt (kg)', sum: true }],
  lines: [{ ordinal: 7, sl: 1, label: 'Toggle clamp', hsn: '8205', qty: 10, unit: 'nos' },
          { ordinal: 9, sl: 2, label: 'Name plate', hsn: '', qty: 50, unit: 'nos' }],
  boxes: [{ values: { dimensions: '60 x 40 x 30 cm', net_weight: '18' }, packed: { 7: 10, 9: 40 } }],
  unpacked: [{ label: 'Name plate', qty: 10 }], over: [],
};

const posted = () => Object.fromEntries(new FormData(document.getElementById('packingForm') as HTMLFormElement).entries());

describe('Packing', () => {
  it('posts the boxes as the server reads them, and says what is not packed yet', () => {
    render(<Packing data={DATA} />);
    expect(posted()).toMatchObject({ box_count: '1', box_1_present: '1', box_1_dimensions: '60 x 40 x 30 cm', box_1_net_weight: '18',
                                     qty_1_7: '10', qty_1_9: '40', packing_list_no: 'PL 900', marks: '' });
    expect(screen.getByText('Name plate: 10 not packed yet')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove box 1' })).toBeDisabled();       // one box always stays
  });

  it('adds boxes after the highest, removes them, and puts the rest in the last one', async () => {
    render(<Packing data={DATA} />);
    await userEvent.click(screen.getByRole('button', { name: 'Add box' }));
    await userEvent.type(screen.getByLabelText('Box 2: Toggle clamp'), '3');
    expect(screen.getAllByText('over by 3')).toHaveLength(1);
    await userEvent.click(screen.getByRole('button', { name: 'Remove box 1' }));
    expect(posted()).toMatchObject({ box_count: '2', box_2_present: '1', qty_2_7: '3' });
    expect(posted()).not.toHaveProperty('box_1_present');                              // removed: not posted, so not saved
    await userEvent.click(screen.getByRole('button', { name: 'Put the rest in the last box' }));
    expect(posted()).toMatchObject({ qty_2_7: '10', qty_2_9: '50' });
    expect(screen.getAllByText('✓')).toHaveLength(2);
  });
});
