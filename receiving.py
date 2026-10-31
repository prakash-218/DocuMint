"""
What arrived on a purchase order: each delivery (po_receipt) says how much of which of its lines came, so a part
delivery is counted line by line, and once every line's quantity has come the order is received.
"""

from typing import Dict, List, Optional

QTY_NAMES = ('qty', 'quantity', 'qty_nos', 'nos')
TEXT_NAMES = ('description', 'item', 'item_details', 'particulars', 'description_of_goods')


def _cell(row: List[Dict], names) -> Optional[Dict]:
    return next((c for c in row if (c.get('field_name') or '').lower() in names), None)


def ordered(sections: Dict) -> List[Dict]:
    """The order's lines (invoice_service.build_sections): [{line (its row number), description, qty, unit}]; a line
    without a quantity counts as one."""
    rows = [r for s in sections.values() if s.get('type') == 'line_item' and not s.get('breakup') for r in s.get('line_item_rows') or []]
    out = []
    for n, row in enumerate(rows, start=1):
        qty, text = _cell(row, QTY_NAMES), _cell(row, TEXT_NAMES) or next((c for c in row if c.get('data_type') == 'string'), None)
        unit = _cell(row, ('unit', 'uom', 'per'))
        out.append({'line': n, 'description': ((text or {}).get('val_string') or f'Line {n}').split('\n')[0],
                    'qty': float((qty or {}).get('val_number') or 1), 'unit': (unit or {}).get('val_string') or ''})
    return out


def progress(lines: List[Dict], receipts: List[Dict]) -> Dict:
    """{lines: [{..., received, left}], state: 'none' | 'part' | 'all', arrived: how many lines in full}."""
    got: Dict[int, float] = {}
    for r in receipts:
        for item in r.get('lines') or []:
            got[int(item['line'])] = got.get(int(item['line']), 0.0) + float(item.get('qty') or 0)
    out = [{**l, 'received': got.get(l['line'], 0.0), 'left': max(0.0, l['qty'] - got.get(l['line'], 0.0))} for l in lines]
    full = sum(1 for l in out if l['left'] <= 1e-9)
    state = 'all' if out and full == len(out) else 'part' if any(l['received'] for l in out) else 'none'
    return {'lines': out, 'state': state, 'arrived': full}


def from_form(form, lines: List[Dict]) -> List[Dict]:
    """The quantities a delivery's form says came (qty_<line>): [{line, qty}] for those above nothing. ValueError when one
    isn't a number, is below nothing, or is more than is still to come."""
    out = []
    for l in lines:
        raw = (form.get(f"qty_{l['line']}") or '').strip().replace(',', '')
        if not raw:
            continue
        try:
            qty = float(raw)
        except ValueError:
            raise ValueError(f"Line {l['line']}: “{raw}” isn't a quantity")
        if qty < 0:
            raise ValueError(f"Line {l['line']}: a quantity can't be below nothing")
        if qty - l['left'] > 1e-9:
            raise ValueError(f"Line {l['line']}: {qty:g} is more than the {l['left']:g} still to come")
        if qty:
            out.append({'line': l['line'], 'qty': qty})
    return out
