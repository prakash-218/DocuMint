"""
A document's packing, box by box, for the React app (frontend/src/islands/packing/): GET /api/packing/<id> gives its
item lines, the boxes with what's in each, the per-box fields its template's packing page asks for, and what isn't packed
yet. The screen posts the same form the server page did to invoices_bp.packing, which saves it (boxes_from_form):
    box_count, box_<n>_present, box_<n>_<field key>, qty_<n>_<ordinal>, packing_list_no, marks.
"""

from typing import Callable, Dict


def _label(line: Dict) -> str:
    return (line['description'] or '').splitlines()[0] if line['description'] else f"Item {line['sl']}"


def build(header: Dict, values, pack_page: Dict, url: Callable) -> Dict:
    from documents import display_number, load_json
    from invoice_service import build_sections, item_lines, packing_summary
    sections = build_sections(header, values)
    lines = item_lines(sections)
    box_fields = pack_page['box_fields']
    details = load_json(header.get('details'))
    boxes = details.get('boxes') or [{'contents': []}]
    summary = packing_summary(header, sections, box_fields)
    number = display_number(header)
    invoice_id = header['invoice_id']
    return {
        'title': f'Packing for {number}',
        'number': number,
        'customer': header.get('customer_name') or '',
        'back': url('invoices_bp.view_invoice', invoice_id=invoice_id),
        'pdf': {'href': url('invoices_bp.export_pdf', invoice_id=invoice_id, page=pack_page['key']),
                'label': f"{pack_page.get('title') or 'Packing list'} PDF"},
        'action': url('invoices_bp.packing', invoice_id=invoice_id),
        'packing_list_no': details.get('packing_list_no') or '',
        'marks': details.get('marks') or '',
        'box_fields': [{'key': f['key'], 'label': f['label'], 'sum': bool(f.get('sum'))} for f in box_fields],
        'lines': [{'ordinal': l['ordinal'], 'sl': l['sl'], 'label': _label(l), 'hsn': l['hsn'], 'qty': l['qty'],
                   'unit': l['unit']} for l in lines],
        'boxes': [{'values': {f['key']: str(box.get(f['key']) or '') for f in box_fields},
                   'packed': {str(c['ordinal']): c['qty'] for c in (box.get('contents') or [])}} for box in boxes],
        'unpacked': [{'label': _label(l), 'qty': l['missing']} for l in summary['unpacked']],
        'over': [{'label': _label(l), 'qty': l['extra']} for l in summary['over']],
    }
