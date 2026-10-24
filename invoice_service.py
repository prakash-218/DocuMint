"""
Invoice calculation and display helpers shared by the staff and customer views.

- recalculate_invoice() evaluates formulas and saves the results. Call it after
  an invoice's input values change (create / edit).
- build_sections() shapes an invoice for display. It computes formulas on the
  fly but never writes, so it is safe on GET requests and for read-only roles.
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from flask import render_template, make_response

from calculations import calculate
from db import db, DatabaseError

logger = logging.getLogger(__name__)

VALUE_COLUMNS = ('val_string', 'val_number', 'val_date', 'val_boolean')
RATE_FIELD_NAMES = ('gst_rate', 'tax', 'tax_rate', 'gst')


def get_template_fields(template_id, version=None) -> List[Dict]:
    """Fields for a specific template version (the latest if version is None)."""
    if not template_id:
        return []
    try:
        if version:
            fields = db.execute_proc('sp_get_template_fields_by_version', (template_id, version))
        else:
            fields = db.execute_proc('sp_get_template_fields', (template_id,))
    except DatabaseError:
        logger.exception("Could not load fields for template %s v%s", template_id, version)
        return []
    return fields or []


def _invoice_fields(header: Dict) -> List[Dict]:
    return get_template_fields(header.get('template_id'), header.get('template_version'))


def recalculate_invoice(invoice_id, header: Dict, values: List[Dict]) -> Dict[Tuple[str, int], float]:
    """Evaluate every formula on the invoice, persist the results and refresh its total."""
    results = calculate(_invoice_fields(header), values)
    stored = {(v.get('field_id'), v.get('value_ordinal') or 0): v.get('val_number') for v in values}

    for (field_id, ordinal), result in results.items():
        current = stored.get((field_id, ordinal))
        if current is not None and abs(float(current) - result) < 1e-6:
            continue
        db.execute_proc('sp_save_invoice_value',
                        (invoice_id, field_id, None, result, None, None, ordinal),
                        fetch=False)

    db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)
    # The procedure above only knows template fields; the stored total is the
    # document's grand total, including any GST added by its tax settings.
    summary = invoice_summary(header, build_sections(header, values), [])
    db.execute_proc('sp_set_invoice_total', (invoice_id, round(summary['total'], 2)), fetch=False)
    return results


def build_sections(header: Dict, values: List[Dict]) -> Dict[str, Dict]:
    """
    Group an invoice's values into ordered sections for the templates:

        {section_title: {
            'type': 'normal' | 'line_item',
            'fields': [value, ...],                      # normal sections
            'line_item_headers': [label, ...],           # line-item sections
            'line_item_rows': [[value, ...], ...],       # aligned with the headers
        }}

    Every template field appears, even if the invoice has no value for it yet,
    and formula fields show freshly calculated results (flagged 'calculated').
    """
    fields = _invoice_fields(header)
    if not fields:
        # Template version missing: fall back to the metadata carried on the values
        fields = [v for v in values if v.get('field_id')]

    by_field = {}
    for f in fields:
        by_field.setdefault(f['field_id'], f)
    ordered = sorted(by_field.values(), key=lambda f: (f.get('section_ordinal') or 0, f.get('field_ordinal') or 0))

    stored = {}
    for v in values:
        if v.get('field_id'):
            stored[(v['field_id'], v.get('value_ordinal') or 0)] = v

    calculated = calculate(fields, values)

    def cell(f, ordinal):
        base = stored.get((f['field_id'], ordinal), {})
        cell = {
            'field_id': f['field_id'],
            'field_name': f.get('field_name') or f.get('name'),
            'field_label': f.get('field_display_name') or f.get('label') or f.get('field_label') or f.get('field_name'),
            'data_type': f.get('data_type') or 'string',
            'is_currency': bool(f.get('is_currency')),
            'is_required': bool(f.get('is_required')),
            'calculation_formula': f.get('calculation_formula'),
            'value_ordinal': ordinal,
            **{col: base.get(col) for col in VALUE_COLUMNS},
        }
        if (f['field_id'], ordinal) in calculated:
            cell['val_number'] = calculated[(f['field_id'], ordinal)]
            cell['calculated'] = True
        if (cell['data_type'] == 'string' and not cell['val_string']
                and (cell['field_name'] or '').lower() in RATE_FIELD_NAMES):
            # "GST Rate" / "Tax" columns show the document's rate unless typed in
            rate = float(header.get('tax_rate') or 0) if header.get('tax_mode') in ('cgst_sgst', 'igst') else 0.0
            cell['val_string'] = f'{rate:g}%'
            cell['derived'] = True
        return cell

    sections: Dict[str, Dict] = {}
    section_fields: Dict[str, List[Dict]] = {}
    for f in ordered:
        title = f.get('section_display_name') or f.get('section_title') or f.get('section_name') or 'Untitled Section'
        if title not in sections:
            name = (f.get('section_name') or title).lower()
            sections[title] = {'type': f.get('section_type') or 'normal', 'fields': [], 'name': name,
                               'breakup': is_breakup_section(name, title),
                               'line_item_headers': [], 'line_item_rows': []}
            section_fields[title] = []
        section_fields[title].append(f)

    for title, section in sections.items():
        flist = section_fields[title]
        if section['type'] == 'line_item':
            ids = {f['field_id'] for f in flist}
            ordinals = sorted({o for (fid, o) in stored if fid in ids})
            section['line_item_headers'] = [cell(f, 0)['field_label'] for f in flist]
            section['line_item_rows'] = [[cell(f, o) for f in flist] for o in ordinals]
        else:
            section['fields'] = [cell(f, 0) for f in flist]

    return sections


def is_breakup_section(name: str, title: str = '') -> bool:
    """Cost break-up sections explain an item's price; they never add to the total."""
    text = f'{name} {title}'.lower().replace('-', '').replace(' ', '')
    return 'breakup' in text or 'splitup' in text


def main_items(sections: Dict[str, Dict]) -> Optional[Dict]:
    """The document's main line-item section (not a cost break-up)."""
    return next((sec for sec in sections.values() if sec['type'] == 'line_item' and not sec.get('breakup')), None)


def _named(row, names):
    return next((c for c in row if (c.get('field_name') or '').lower() in names), None)


def item_lines(sections: Dict[str, Dict]) -> List[Dict]:
    """Main line items as {ordinal, sl, description, hsn, qty, unit, amount} for packing and break-ups."""
    section = main_items(sections)
    lines = []
    for sl, row in enumerate(section['line_item_rows'] if section else [], start=1):
        text = next((c for c in row if c['data_type'] == 'string' and (c.get('val_string') or '').strip()
                     and (c.get('field_name') or '').lower() not in ('per', 'unit', 'uom')
                     and 'hsn' not in (c.get('field_name') or '').lower()
                     and (c.get('field_name') or '').lower() not in RATE_FIELD_NAMES), None)
        qty = _named(row, ('qty', 'quantity'))
        unit = _named(row, ('per', 'unit', 'uom'))
        hsn = next((c for c in row if 'hsn' in (c.get('field_name') or '').lower()), None)
        amount = _line_amount_cell(row)
        lines.append({
            'ordinal': row[0]['value_ordinal'] if row else sl, 'sl': sl,
            'description': text['val_string'] if text else '',
            'hsn': (hsn.get('val_string') or '') if hsn else '',
            'qty': float(qty['val_number'] or 0) if qty and qty.get('val_number') is not None else 0.0,
            'unit': (unit.get('val_string') or '') if unit else '',
            'amount': float(amount['val_number'] or 0) if amount and amount.get('val_number') is not None else 0.0,
            'row': row,
        })
    return lines


def _weight(value) -> Optional[float]:
    try:
        return float(str(value).lower().replace('kg', '').replace(',', '').strip()) if value not in (None, '') else None
    except ValueError:
        return None


def packing_summary(header: Dict, sections: Dict[str, Dict], box_fields: Optional[List[Dict]] = None) -> Dict:
    """
    Box-by-box packing for an export invoice, from details.boxes:
        [{'dimensions': '60x40x30 cm', 'net_weight': '18', 'pallet_no': 'P1', ...,
          'contents': [{'ordinal': 1, 'qty': 10}, ...]}, ...]
    box_fields (from the template's packing page) say which per-box values exist and
    which are added up. Returns boxes with their item lines, totals, and anything
    left unpacked or over-packed.
    """
    from documents import load_json
    from layout import DEFAULT_BOX_FIELDS
    box_fields = box_fields or DEFAULT_BOX_FIELDS
    details = load_json(header.get('details'))
    lines = {l['ordinal']: l for l in item_lines(sections)}
    packed: Dict[int, float] = {}
    boxes = []
    for i, box in enumerate(details.get('boxes') or [], start=1):
        contents = []
        for entry in box.get('contents') or []:
            line = lines.get(int(entry.get('ordinal', -1)))
            qty = float(entry.get('qty') or 0)
            if not line or qty <= 0:
                continue
            packed[line['ordinal']] = packed.get(line['ordinal'], 0.0) + qty
            contents.append({**line, 'qty': qty})
        values = {f['key']: (box.get(f['key']) or '') for f in box_fields}
        boxes.append({'no': i, 'contents': contents, 'values': values,
                      'dimensions': box.get('dimensions') or '',
                      'net_weight': _weight(box.get('net_weight')), 'gross_weight': _weight(box.get('gross_weight'))})

    totals = {}
    for f in box_fields:
        if f.get('sum'):
            numbers = [_weight(b['values'].get(f['key'])) for b in boxes]
            numbers = [n for n in numbers if n is not None]
            totals[f['key']] = sum(numbers) if numbers else None

    unpacked = [{**l, 'missing': l['qty'] - packed.get(o, 0.0)} for o, l in lines.items() if packed.get(o, 0.0) < l['qty']]
    over = [{**l, 'extra': packed[o] - l['qty']} for o, l in lines.items() if packed.get(o, 0.0) > l['qty']]
    nets = [b['net_weight'] for b in boxes if b['net_weight'] is not None]
    grosses = [b['gross_weight'] for b in boxes if b['gross_weight'] is not None]
    return {
        'boxes': boxes,
        'box_fields': box_fields,
        'totals': totals,
        'count': len(boxes),
        'total_qty': sum(packed.values()),
        'net_weight': sum(nets) if nets else None,
        'gross_weight': sum(grosses) if grosses else None,
        'unpacked': unpacked if boxes else [],
        'over': over,
    }


def breakup_check(sections: Dict[str, Dict]) -> List[Dict]:
    """For each main item that has a cost break-up: the break-up lines, their sum and whether it matches."""
    lines = {l['sl']: l for l in item_lines(sections)}
    groups: Dict[int, List[Dict]] = {}
    for sec in sections.values():
        if not sec.get('breakup'):
            continue
        for row in sec['line_item_rows']:
            ref = _named(row, ('item', 'item_no', 'for_item', 'line'))
            amount = _line_amount_cell(row) or _named(row, ('amount', 'cost', 'price'))
            text = next((c for c in row if c['data_type'] == 'string' and (c.get('val_string') or '').strip()), None)
            item_no = int(ref['val_number']) if ref and ref.get('val_number') else 1
            part = {'description': text['val_string'] if text else '',
                    'amount': float(amount['val_number'] or 0) if amount and amount.get('val_number') is not None else 0.0}
            if part['description'].strip() or part['amount']:
                groups.setdefault(item_no, []).append(part)
    out = []
    for item_no in sorted(groups):
        parts = groups[item_no]
        total = sum(p['amount'] for p in parts)
        line = lines.get(item_no)
        out.append({'item_no': item_no, 'item': line, 'parts': parts, 'total': total,
                    'matches': line is not None and abs(total - line['amount']) < 0.01})
    return out


TOTAL_NAMES = ('total', 'grand_total', 'invoice_total', 'amount')


def _invoice_total(header: Dict, sections: Dict[str, Dict]) -> float:
    """Pick the invoice total the same way sp_update_invoice_total does."""
    cells = [c for s in sections.values() if s['type'] == 'normal' for c in s['fields']
             if c['data_type'] == 'number']
    number = lambda c: float(c.get('val_number') or 0)

    try:
        row = db.execute_proc_single('sp_get_template_total_field',
                                     (header.get('template_id'), header.get('template_version')))
        total_field_id = row.get('total_field_id') if row else None
    except DatabaseError:
        total_field_id = None
    if total_field_id:
        return sum(number(c) for c in cells if c['field_id'] == total_field_id)

    key = lambda c: (c['field_label'] or '').strip().replace(' ', '_').lower()
    for name in TOTAL_NAMES:
        match = next((c for c in cells if key(c) == name), None)
        if match:
            return number(match)

    total = sum(number(c) for c in cells
                if 'sum' in (c.get('calculation_formula') or '').lower() or 'total' in key(c))
    return total or sum(number(c) for c in cells)


class PdfUnavailable(Exception):
    """xhtml2pdf isn't installed"""


FONT_CANDIDATES = {
    # DejaVu ships in the Docker image (fonts-dejavu-core); Arial covers Windows dev machines.
    # Both include the rupee sign, which PDF's built-in Helvetica doesn't.
    'regular': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf',
                '/Library/Fonts/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'],
    'bold': ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf',
             '/Library/Fonts/Arial Bold.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'],
    'mono': ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 'C:/Windows/Fonts/courbd.ttf',
             '/System/Library/Fonts/Supplemental/Courier New Bold.ttf'],
}


_registered_fonts: Optional[Dict[str, Optional[str]]] = None


def pdf_fonts() -> Dict[str, Optional[str]]:
    """Register a Unicode TTF with ReportLab (once) and return the CSS font names to use.

    Fonts are registered directly rather than via CSS @font-face, which in xhtml2pdf
    goes through a temp file that can't be reopened on Windows."""
    global _registered_fonts
    if _registered_fonts is not None:
        return _registered_fonts
    import os
    found = {kind: next((p for p in paths if os.path.exists(p)), None) for kind, paths in FONT_CANDIDATES.items()}
    names: Dict[str, Optional[str]] = {'regular': None, 'mono': None}
    try:
        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xhtml2pdf.default import DEFAULT_FONT

        if found['regular']:
            pdfmetrics.registerFont(TTFont('DocFont', found['regular']))
            pdfmetrics.registerFont(TTFont('DocFont-Bold', found['bold'] or found['regular']))
            for bold, italic, face in ((0, 0, 'DocFont'), (1, 0, 'DocFont-Bold'), (0, 1, 'DocFont'), (1, 1, 'DocFont-Bold')):
                addMapping('DocFont', bold, italic, face)
            DEFAULT_FONT['docfont'] = 'DocFont'
            names['regular'] = 'DocFont'
        if found['mono']:
            pdfmetrics.registerFont(TTFont('DocMono', found['mono']))
            for bold in (0, 1):
                for italic in (0, 1):
                    addMapping('DocMono', bold, italic, 'DocMono')
            DEFAULT_FONT['docmono'] = 'DocMono'
            names['mono'] = 'DocMono'
    except Exception:
        logger.exception("Could not register PDF fonts; falling back to Helvetica (no rupee sign)")
    _registered_fonts = names
    return names


COPY_LABELS = ('Original Copy', 'Duplicate Copy', 'Transporter Copy')


def _pdf_bytes(html: str) -> bytes:
    from xhtml2pdf import pisa
    buffer = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), buffer, encoding='utf-8')
    if pdf.err:
        raise RuntimeError('xhtml2pdf reported %s error(s)' % pdf.err)
    return buffer.getvalue()


def _merge(parts: List[bytes]) -> bytes:
    if len(parts) == 1:
        return parts[0]
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    for part in parts:
        for pg in PdfReader(BytesIO(part)).pages:
            writer.add_page(pg)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def render_invoice_pdf(header: Dict, values: List[Dict], copies: Optional[int] = None,
                       packing: bool = False, page_key: Optional[str] = None):
    """Render a document to a PDF response (shared by staff and customer portal).

    Prints the pages the template's layout defines for this document type: the
    main document plus every page marked "print with document", or just page_key.
    Quotations use the letter layout; other types the boxed grid. Tax and export
    invoices print Original/Duplicate/Transporter copies unless the page (or
    copies=1) says otherwise.
    """
    try:
        import xhtml2pdf  # noqa: F401
    except ImportError:
        raise PdfUnavailable()
    from documents import display_number, get_type, load_json
    from layout import load_layout, page as find_page, pages_for, packing_page, printed_customer_fields, printed_org_fields

    doc_type = get_type(header.get('doc_type'))
    layout = load_layout(header.get('template_id'), header.get('org_id'))
    if packing and not page_key:
        page_key = (packing_page(layout, doc_type.key) or {}).get('key')
    if page_key:
        selected = [find_page(layout, doc_type.key, page_key)]
        if not selected[0]:
            raise LookupError(f'No page {page_key!r} for this document')
    else:
        selected = [p for p in pages_for(layout, doc_type.key) if p['with_document']]

    sections = build_sections(header, values)
    payments = db.execute_proc('sp_get_invoice_payments', (header['invoice_id'],)) or []
    summary = invoice_summary(header, sections, payments)
    profile = load_json(header.get('organization_profile'))
    pack_page = packing_page(layout, doc_type.key)
    common = dict(invoice=header, sections_data=sections, payments=payments, summary=summary, profile=profile,
                  fonts=pdf_fonts(), current_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                  org_fields=printed_org_fields(profile),
                  customer_fields=printed_customer_fields(profile, header.get('customer_custom')),
                  pack=packing_summary(header, sections, (pack_page or {}).get('box_fields')) if pack_page else None)

    parts = []
    for pg in selected:
        if pg['kind'] == 'document':
            if pg['copies']:
                labels = pg['copies'][:copies] if copies else pg['copies']
            elif doc_type.takes_payments:
                labels = COPY_LABELS[:max(1, min(int(copies or len(COPY_LABELS)), len(COPY_LABELS)))]
            else:
                labels = ['']
            template = 'pdf/quote.html' if doc_type.key == 'quote' else 'pdf/grid.html'
            parts.append(_pdf_bytes(render_template(template, page=pg, copies=labels, packing=False, **common)))
        elif pg['kind'] == 'packing':
            parts.append(_pdf_bytes(render_template('pdf/grid.html', page=pg, copies=pg['copies'] or [''],
                                                    packing=True, **common)))
        else:
            parts.append(_pdf_bytes(render_template('pdf/annexure.html', page=pg, copies=pg['copies'] or [''], **common)))

    filename = ''.join(c if c.isalnum() or c in '-_' else '_' for c in display_number(header)).strip('_')
    prefix = slug_title(selected[0]['title']) if page_key and selected[0]['title'] else doc_type.short
    response = make_response(_merge(parts))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{prefix}_{filename}.pdf"'
    return response


def slug_title(title: str) -> str:
    return ''.join(c if c.isalnum() else '_' for c in title).strip('_') or 'Page'


AMOUNT_NAMES = ('amount', 'total', 'line_total', 'value', 'total_amount')


def _line_amount_cell(row):
    """The cell holding a line item's amount: a column named like an amount, else the last calculated number."""
    numbers = [c for c in row if c['data_type'] == 'number']
    named = next((c for c in numbers if (c.get('field_name') or '').lower() in AMOUNT_NAMES), None)
    if named:
        return named
    calculated = [c for c in numbers if c.get('calculation_formula')]
    return calculated[-1] if calculated else None


def _hsn_summary(sections: Dict[str, Dict], tax_mode: str, rate: float) -> List[Dict]:
    """Taxable value and tax grouped by HSN/SAC code, for the GST summary table."""
    groups: Dict[str, float] = {}
    for section in sections.values():
        if section['type'] != 'line_item' or section.get('breakup'):
            continue
        for row in section['line_item_rows']:
            hsn = next((c for c in row if 'hsn' in (c.get('field_name') or '').lower()
                        or 'hsn' in (c.get('field_label') or '').lower()), None)
            amount = _line_amount_cell(row)
            if not hsn or not amount:
                continue
            code = (hsn.get('val_string') or (str(int(hsn['val_number'])) if hsn.get('val_number') else '')).strip()
            if code:
                groups[code] = groups.get(code, 0.0) + float(amount.get('val_number') or 0)
    rows = []
    for code, taxable in groups.items():
        tax = taxable * rate / 100 if tax_mode in ('cgst_sgst', 'igst') else 0.0
        rows.append({'hsn': code, 'taxable': taxable, 'rate': rate, 'tax': tax,
                     'half_rate': rate / 2, 'half_tax': tax / 2})
    return rows


def invoice_summary(header: Dict, sections: Dict[str, Dict], payments: List[Dict]) -> Dict:
    """
    Money summary of a document:

        taxable       value before document-level tax (the template's total field)
        tax_lines     [{'label': 'CGST', 'rate': 9, 'amount': ...}, ...]
        total         grand total = taxable + tax
        advance       {'percent', 'basis', 'amount'} when an advance is requested
        payable_now   advance amount if there is one, else the total
        paid/balance  from recorded payments
        words         payable_now in words, in the document's currency
        hsn           HSN/SAC-wise summary rows (GST documents)
    """
    from money import amount_in_words

    currency = header.get('currency_code') or 'USD'
    taxable = _invoice_total(header, sections)
    tax_mode = header.get('tax_mode') or 'none'
    rate = float(header.get('tax_rate') or 0)

    tax_lines = []
    if tax_mode == 'cgst_sgst' and rate:
        half = round(taxable * rate / 200, 2)
        tax_lines = [{'label': 'CGST', 'rate': rate / 2, 'amount': half},
                     {'label': 'SGST', 'rate': rate / 2, 'amount': half}]
    elif tax_mode == 'igst' and rate:
        tax_lines = [{'label': 'IGST', 'rate': rate, 'amount': round(taxable * rate / 100, 2)}]
    tax_total = sum(line['amount'] for line in tax_lines)
    total = round(taxable + tax_total, 2)

    advance = None
    percent = float(header.get('advance_percent') or 0)
    if percent:
        basis = header.get('advance_basis') or 'pre_tax'
        base = taxable if basis == 'pre_tax' else total
        advance = {'percent': percent, 'basis': basis, 'amount': round(base * percent / 100, 2)}
    payable_now = advance['amount'] if advance else total

    paid = sum(float(p.get('amount') or 0) for p in payments or [])
    return {
        'currency': currency,
        'taxable': taxable,
        'tax_mode': tax_mode,
        'tax_lines': tax_lines,
        'tax_total': tax_total,
        'total': total,
        'advance': advance,
        'payable_now': payable_now,
        'paid': paid,
        'balance': max(total - paid, 0.0),
        'words': amount_in_words(payable_now, currency),
        'tax_words': amount_in_words(tax_total, currency) if tax_total else None,
        'hsn': _hsn_summary(sections, tax_mode, rate) if tax_mode in ('cgst_sgst', 'igst', 'lut') else [],
        'breakups': breakup_check(sections),
    }
