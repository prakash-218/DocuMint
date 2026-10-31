"""
Template print layout: the pages a template prints, and custom fields.

A layout (stored per template in template_layout) says what the template is for and lists the pages it prints:

    'used_for': ['quote'],                 # document types it's for (CHOOSABLE); [] = any; missing = guess from the name
    'export': None,                        # True / False, or None to decide by currency and name

    {'key': 'packing', 'kind': 'packing', 'title': 'Packing List',
     'doc_types': ['export_invoice'],      # empty = every document type
     'with_document': False,               # True: printed in the same PDF after the main page
     'copies': [],                         # e.g. ['Original Copy', 'Duplicate Copy']; empty = type default
     'columns': ['description', 'hsn_sac', 'qty'],   # line-item fields shown; empty = all
     'box_fields': [{'key': 'dimensions', 'label': 'Dimensions', 'sum': False}, ...],  # packing only
     'sections': ['breakup'], 'include_notes': True, 'include_terms': True}            # annexure only

Kinds: 'document' (the invoice/quote itself; always first, can't be removed),
'packing' (box-by-box packing list), 'annexure' (chosen sections / notes / terms).

Custom fields live in the business profile:
    custom_fields:   [{'key', 'label', 'value', 'print'}]   - about your organization
    customer_fields: [{'key', 'label', 'print'}]            - definitions; values on each customer
"""

import json
import re
from copy import deepcopy
from typing import Dict, List, Optional

from documents import CHOOSABLE, DOC_TYPES, load_json

PAGE_KINDS = {
    'document': 'Main document',
    'packing': 'Packing list',
    'annexure': 'Annexure (extra page)',
}

DEFAULT_BOX_FIELDS = [
    {'key': 'dimensions', 'label': 'Dimensions', 'sum': False},
    {'key': 'net_weight', 'label': 'Net Wt (kg)', 'sum': True},
    {'key': 'gross_weight', 'label': 'Gross Wt (kg)', 'sum': True},
]

DEFAULT_PAGES = [
    {'key': 'document', 'kind': 'document', 'title': '', 'doc_types': [], 'with_document': True,
     'copies': [], 'columns': []},
    {'key': 'packing', 'kind': 'packing', 'title': 'Packing List', 'doc_types': ['export_invoice'],
     'with_document': False, 'copies': [], 'columns': [], 'box_fields': DEFAULT_BOX_FIELDS},
]


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', (text or '').strip().lower()).strip('_')[:40]


def _clean_list(values, allowed=None) -> List[str]:
    out = []
    for v in values or []:
        v = str(v).strip()
        if v and (allowed is None or v in allowed) and v not in out:
            out.append(v)
    return out


def normalize(layout) -> Dict:
    """Validate a layout from the database or a form; always returns a usable layout."""
    data = load_json(layout) if not isinstance(layout, dict) else layout
    export = data.get('export') if isinstance(data.get('export'), bool) else None   # None = decide automatically
    used_for = _clean_list(data['used_for'], CHOOSABLE) if isinstance(data.get('used_for'), list) else None
    pages_in = data.get('pages') if isinstance(data.get('pages'), list) else None
    if not pages_in:
        return {'pages': deepcopy(DEFAULT_PAGES), 'export': export, 'used_for': used_for}

    pages, keys = [], set()
    for raw in pages_in:
        if not isinstance(raw, dict):
            continue
        kind = raw.get('kind') if raw.get('kind') in PAGE_KINDS else 'annexure'
        key = 'document' if kind == 'document' else (slug(raw.get('key') or raw.get('title') or kind) or kind)
        if key in keys:
            if kind == 'document':
                continue
            key = f'{key}_{len(pages) + 1}'
        keys.add(key)
        page = {
            'key': key, 'kind': kind,
            'title': str(raw.get('title') or '').strip()[:60],
            'doc_types': _clean_list(raw.get('doc_types'), DOC_TYPES),
            'with_document': True if kind == 'document' else bool(raw.get('with_document')),
            'copies': _clean_list(raw.get('copies'))[:5],
            'columns': _clean_list(raw.get('columns')),
        }
        if kind == 'packing':
            fields = []
            for f in raw.get('box_fields') or []:
                label = str((f or {}).get('label') or '').strip()[:40]
                if label:
                    fields.append({'key': (f.get('key') or slug(label))[:40] or slug(label),
                                   'label': label, 'sum': bool(f.get('sum'))})
            page['box_fields'] = fields or deepcopy(DEFAULT_BOX_FIELDS)
        if kind == 'annexure':
            page['sections'] = _clean_list(raw.get('sections'))
            page['include_notes'] = bool(raw.get('include_notes'))
            page['include_terms'] = bool(raw.get('include_terms'))
        pages.append(page)

    if not any(p['kind'] == 'document' for p in pages):
        pages.insert(0, deepcopy(DEFAULT_PAGES[0]))
    pages.sort(key=lambda p: p['kind'] != 'document')   # main document always first
    return {'pages': pages, 'export': export, 'used_for': used_for}


def load_layout(template_id, org_id) -> Dict:
    from db import db, DatabaseError
    try:
        row = db.execute_proc_single('sp_get_template_layout', (template_id, org_id))
    except DatabaseError:
        row = None
    return normalize(row.get('layout') if row else None)


def save_layout(template_id, org_id, layout: Dict):
    from db import db
    db.execute_proc('sp_save_template_layout', (template_id, org_id, json.dumps(normalize(layout))), fetch=False)


def template_is_export(template_id, org_id, layout: Optional[Dict] = None) -> bool:
    """Is this an export template? Its Pages & printing setting, else: a foreign currency
    or "export" in the name."""
    from db import db, DatabaseError
    layout = layout if layout is not None else load_layout(template_id, org_id)
    if layout.get('export') is not None:
        return layout['export']
    try:
        info = next((t for t in db.execute_proc('sp_list_templates', (org_id, True)) or []
                     if t.get('template_id') == template_id), None)
    except DatabaseError:
        info = None
    if not info:
        return False
    from document_service import get_org_profile
    home = get_org_profile(org_id)[1].get('default_currency') or 'INR'
    return (info.get('currency_code') or home) != home or 'export' in (info.get('name') or '').lower()


# A template's name says what it's for, when its settings don't: 'Proforma Invoice', 'Quotation with split up'
NAME_HINTS = {'quote': ('quot', 'offer'), 'proforma': ('proforma', 'pro forma', 'pro-forma'), 'invoice': ('invoice', 'bill'),
              'purchase_order': ('purchase', 'po ')}
# A template that doesn't say what it's for is for sales: a purchase order's template says so (or its name does)
SALES_CHOOSABLE = tuple(t for t in CHOOSABLE if t != 'purchase_order')


def template_types(name: Optional[str], layout: Dict) -> List[str]:
    """The document types a template is for (quote / proforma / invoice): its setting, else guessed from its name;
    every type when neither says."""
    if layout.get('used_for') is not None:
        return layout['used_for'] or list(SALES_CHOOSABLE)
    name = (name or '').lower() + ' '
    guessed = [t for t, hints in NAME_HINTS.items() if any(h in name for h in hints)]
    if 'proforma' in guessed and 'invoice' in guessed:        # "Proforma Invoice"
        guessed.remove('invoice')
    return guessed or list(SALES_CHOOSABLE)


def types_by_template(org_id, templates: List[Dict]) -> Dict[str, List[str]]:
    """template_id -> template_types, for a list of templates (one query)."""
    from db import db, DatabaseError
    try:
        layouts = {r['template_id']: r['layout'] for r in db.execute_proc('sp_list_template_layouts', (org_id,)) or []}
    except DatabaseError:
        layouts = {}
    return {t['template_id']: template_types(t.get('name') or t.get('template_name'), normalize(layouts.get(t['template_id'])))
            for t in templates}


def pages_for(layout: Dict, doc_type: str) -> List[Dict]:
    """The layout's pages that apply to this document type, main document first."""
    return [p for p in normalize(layout)['pages'] if not p['doc_types'] or doc_type in p['doc_types']]


def page(layout: Dict, doc_type: str, key: str) -> Optional[Dict]:
    return next((p for p in pages_for(layout, doc_type) if p['key'] == key), None)


def packing_page(layout: Dict, doc_type: str) -> Optional[Dict]:
    return next((p for p in pages_for(layout, doc_type) if p['kind'] == 'packing'), None)


# ---------------------------------------------------------------- Custom fields

def custom_field_defs(profile: Dict, level: str) -> List[Dict]:
    """level 'org' -> profile.custom_fields, 'customer' -> profile.customer_fields"""
    raw = profile.get('custom_fields' if level == 'org' else 'customer_fields') or []
    return [f for f in raw if isinstance(f, dict) and f.get('key') and f.get('label')]


def defs_from_form(form, prefix: str, with_value: bool) -> List[Dict]:
    """Repeatable rows <prefix>_label_N / _value_N / _print_N (and _key_N to keep keys stable)."""
    out, seen = [], set()
    labels = sorted((k for k in form.keys() if k.startswith(f'{prefix}_label_')), key=lambda k: int(k.rsplit('_', 1)[1]))
    for name in labels:
        n = name.rsplit('_', 1)[1]
        label = (form.get(name) or '').strip()[:60]
        if not label:
            continue
        key = (form.get(f'{prefix}_key_{n}') or '').strip() or slug(label)
        if key in seen:
            key = f'{key}_{n}'
        seen.add(key)
        row = {'key': key, 'label': label, 'print': bool(form.get(f'{prefix}_print_{n}'))}
        if with_value:
            row['value'] = (form.get(f'{prefix}_value_{n}') or '').strip()[:200]
        out.append(row)
    return out


def printed_org_fields(profile: Dict) -> List[Dict]:
    return [f for f in custom_field_defs(profile, 'org') if f.get('print') and f.get('value')]


def printed_customer_fields(profile: Dict, customer_custom) -> List[Dict]:
    values = load_json(customer_custom)
    return [{'label': f['label'], 'value': values[f['key']]}
            for f in custom_field_defs(profile, 'customer') if f.get('print') and values.get(f['key'])]


# ---------------------------------------------------------------- Layout editor form

def layout_from_form(form) -> Dict:
    """Parse the Pages & printing editor (page_<i>_*, box fields page_<i>_box_*_<j>)."""
    pages = []
    try:
        count = min(int(form.get('page_count') or 0), 30)
    except ValueError:
        count = 0
    export = {'yes': True, 'no': False}.get(form.get('export'))
    used_for = form.getlist('used_for') if hasattr(form, 'getlist') else form.get('used_for') or []
    for i in range(1, count + 1):
        if not form.get(f'page_{i}_present'):
            continue
        p = f'page_{i}_'
        page = {
            'key': form.get(p + 'key') or '',
            'kind': form.get(p + 'kind') or 'annexure',
            'title': form.get(p + 'title') or '',
            'doc_types': form.getlist(p + 'doc_types') if hasattr(form, 'getlist') else form.get(p + 'doc_types') or [],
            'with_document': bool(form.get(p + 'with_document')),
            'copies': [c.strip() for c in (form.get(p + 'copies') or '').splitlines() if c.strip()],
            'columns': form.getlist(p + 'columns') if hasattr(form, 'getlist') else form.get(p + 'columns') or [],
            'sections': form.getlist(p + 'sections') if hasattr(form, 'getlist') else form.get(p + 'sections') or [],
            'include_notes': bool(form.get(p + 'include_notes')),
            'include_terms': bool(form.get(p + 'include_terms')),
        }
        box_fields = []
        labels = sorted((k for k in form.keys() if k.startswith(p + 'box_label_')), key=lambda k: int(k.rsplit('_', 1)[1]))
        for name in labels:
            j = name.rsplit('_', 1)[1]
            label = (form.get(name) or '').strip()
            if label:
                box_fields.append({'key': (form.get(f'{p}box_key_{j}') or '').strip() or slug(label),
                                   'label': label, 'sum': bool(form.get(f'{p}box_sum_{j}'))})
        page['box_fields'] = box_fields
        pages.append(page)
    return normalize({'pages': pages, 'export': export, 'used_for': used_for})


def new_page(kind: str) -> Dict:
    if kind == 'packing':
        return {'key': 'packing', 'kind': 'packing', 'title': 'Packing List', 'doc_types': ['export_invoice'],
                'with_document': False, 'copies': [], 'columns': [], 'box_fields': deepcopy(DEFAULT_BOX_FIELDS)}
    return {'key': 'annexure', 'kind': 'annexure', 'title': 'Annexure', 'doc_types': [], 'with_document': True,
            'copies': [], 'columns': [], 'sections': [], 'include_notes': False, 'include_terms': False}
