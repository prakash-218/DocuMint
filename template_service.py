"""
Read-side helpers for the template pages: a calculated preview with sample
values, formulas in plain words, versions and where a template is used.
"""

import re
from typing import Dict, List, Optional

from calculations import FUNCTION_NAMES, normalize_name, validate_formula
from db import db, DatabaseError
from invoice_service import (RATE_FIELD_NAMES, build_sections, get_template_fields, invoice_summary,
                             is_breakup_section)

SAMPLE_TEXT = {
    'description': ['Machined bracket', 'Installation & commissioning'],
    'name': ['Machined bracket', 'Installation & commissioning'],
    'hsn_sac': ['8466', '998719'], 'hsn': ['8466', '998719'],
    'per': ['no.', 'no.'], 'unit': ['no.', 'set'], 'item_code': ['AT-1001', ''],
}
QTY_NAMES = ('qty', 'quantity', 'nos', 'units')


def _sample_number(field, row: int) -> float:
    name = (field.get('field_name') or '').lower()
    if name in QTY_NAMES:
        return (4, 1)[row % 2]
    if name in ('item_no', 'item'):
        return 1
    if field.get('is_currency'):
        return (1250, 8000)[row % 2]
    return (10, 5)[row % 2]


def sample_values(fields: List[Dict], rows: int = 2) -> List[Dict]:
    """Plausible input values for every non-formula field, so the preview can calculate."""
    values = []
    for f in fields:
        if f.get('calculation_formula') or (f.get('field_name') or '').lower() in RATE_FIELD_NAMES:
            continue   # calculated / filled from the document's GST rate
        line_item = f.get('section_type') == 'line_item'
        breakup = is_breakup_section((f.get('section_name') or ''), f.get('section_title') or '')
        for row in range(1, (rows + 1 if line_item else 2)):
            name = (f.get('field_name') or '').lower()
            v = {**f, 'value_ordinal': row if line_item else 0,
                 'val_string': None, 'val_number': None, 'val_date': None, 'val_boolean': None}
            if f.get('data_type') == 'number':
                v['val_number'] = {1: 3000, 2: 2000}[row] if breakup and name == 'amount' else _sample_number(f, row - 1)
            elif f.get('data_type') == 'date':
                v['val_date'] = '2026-04-01'
            elif f.get('data_type') == 'boolean':
                v['val_boolean'] = 1
            elif breakup:
                v['val_string'] = ('Material', 'Machining')[(row - 1) % 2]
            else:
                samples = SAMPLE_TEXT.get(name)
                v['val_string'] = samples[(row - 1) % 2] if samples else (f.get('field_display_name') or name).title()
            values.append(v)
    return values


def humanize_formula(formula: str, fields: List[Dict]) -> str:
    """'SUM(items.amount) * 0.1' -> 'Sum of Items › Amount × 0.1'"""
    if not formula:
        return ''
    labels = {}
    sections = {}
    for f in fields:
        labels[normalize_name(f.get('field_name'))] = f.get('field_display_name') or f.get('field_name')
        sections[normalize_name(f.get('section_name'))] = f.get('section_display_name') or f.get('section_name')

    words = {'SUM': 'sum of', 'AVG': 'average of', 'COUNT': 'number of', 'MIN': 'lowest of', 'MAX': 'highest of',
             'ROUND': 'round', 'ABS': 'absolute value of', 'GET': ''}

    def token(m):
        if m.group(1):                                     # this.field
            return f"this row's {labels.get(m.group(1).lower(), m.group(1))}"
        if m.group(2):                                     # section.field
            return f"{sections.get(m.group(2).lower(), m.group(2))} › {labels.get(m.group(3).lower(), m.group(3))}"
        if m.group(4):                                     # FUNCTION(
            return words.get(m.group(4).upper(), m.group(4)) + ' '
        name = m.group(5)                                  # bare field (or section) name
        return labels.get(name.lower()) or sections.get(name.lower(), name)

    text = re.sub(r'(?i)\bthis\.([A-Za-z_]\w*)|\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)|\b([A-Za-z_]\w*)\s*(?=\()|\b([A-Za-z_]\w*)\b',
                  token, formula)
    # 'sum of (Items › Amount)' -> 'sum of Items › Amount' when there's a single argument
    text = re.sub(r'(of|round|value of) \(([^(),]*)\)', r'\1 \2', text)
    return text.replace('*', '×').replace('/', '÷').replace('  ', ' ').strip()


def template_versions(org_id, template_id) -> List[Dict]:
    rows = [t for t in db.execute_proc('sp_list_templates', (org_id, True)) or [] if t.get('template_id') == template_id]
    return sorted(rows, key=lambda t: t.get('version') or 0, reverse=True)


def template_overview(org_id, template_id) -> Optional[Dict]:
    versions = template_versions(org_id, template_id)
    if not versions:
        return None
    latest = versions[0]
    fields = get_template_fields(template_id, latest['version'])

    total_field_id = None
    try:
        row = db.execute_proc_single('sp_get_template_total_field', (template_id, latest['version']))
        total_field_id = row.get('total_field_id') if row else None
    except DatabaseError:
        pass

    has_rate_column = any((f.get('field_name') or '').lower() in RATE_FIELD_NAMES for f in fields)
    preview_header = {'invoice_id': 'preview', 'template_id': template_id, 'template_version': latest['version'],
                      'currency_code': latest.get('currency_code'), 'doc_type': 'invoice',
                      'tax_mode': 'cgst_sgst' if has_rate_column else 'none', 'tax_rate': 18 if has_rate_column else 0}
    sample = sample_values(fields)
    sections = build_sections(preview_header, sample)
    summary = invoice_summary(preview_header, sections, [])

    formulas = []
    for f in fields:
        if f.get('calculation_formula'):
            formulas.append({
                'label': f.get('field_display_name') or f.get('field_name'),
                'section': f.get('section_display_name') or f.get('section_name'),
                'formula': f['calculation_formula'],
                'plain': humanize_formula(f['calculation_formula'], fields),
                'error': validate_formula(f['calculation_formula'], fields, f.get('section_name') or ''),
                'is_total': f['field_id'] == total_field_id,
            })

    documents = [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) or []
                 if d.get('template_id') == template_id]
    total_field = next((f for f in fields if f['field_id'] == total_field_id), None)
    from layout import load_layout
    return {
        'layout': load_layout(template_id, org_id),
        'info': latest,
        'versions': versions,
        'fields': fields,
        'sections': sections,
        'summary': summary,
        'formulas': formulas,
        'total_field': total_field,
        'documents': documents,
        'field_count': len(fields),
    }


def template_cards(org_id, include_archived: bool) -> List[Dict]:
    """One card per template (latest version), with its columns and how often it's used."""
    rows = db.execute_proc('sp_list_templates', (org_id, include_archived)) or []
    latest: Dict[str, Dict] = {}
    for t in rows:
        if t.get('version') == t.get('latest_version'):
            latest[t['template_id']] = t
    usage: Dict[str, int] = {}
    for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) or []:
        usage[d.get('template_id')] = usage.get(d.get('template_id'), 0) + 1
    cards = []
    for t in latest.values():
        fields = get_template_fields(t['template_id'], t['version'])
        sections = []
        for f in fields:
            title = f.get('section_display_name') or f.get('section_name')
            if not sections or sections[-1]['title'] != title:
                sections.append({'title': title, 'type': f.get('section_type'), 'columns': []})
            sections[-1]['columns'].append(f.get('field_display_name') or f.get('field_name'))
        cards.append({**t, 'sections': sections, 'used': usage.get(t['template_id'], 0)})
    return sorted(cards, key=lambda c: (bool(c.get('is_archived')), -c['used'], c.get('name') or ''))
