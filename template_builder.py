"""
Template builder: the create / edit form for a template's sections and fields.

The form describes the whole template (sections s1..sN, fields s<i>_f<j>), and
saving rebuilds the version from it. A version that documents already use is
never changed: saving makes the next version and documents keep theirs.
Field *names* (used in formulas, e.g. this.qty) stay fixed once created; only
labels change, so renaming "Qty" to "Quantity" doesn't break a formula.
"""

import re
from typing import Dict, List, Optional, Tuple

from db import db, DatabaseError

FIELD_TYPES = {'string': 'Text', 'number': 'Number', 'date': 'Date', 'boolean': 'Yes / No'}
SECTION_TYPES = {'line_item': 'Line items (a table)', 'normal': 'Fields (totals, notes...)'}

# What a new template starts with
STARTER = [
    {'title': 'Items', 'type': 'line_item', 'fields': [
        {'label': 'Description', 'name': 'description', 'type': 'string'},
        {'label': 'Qty', 'name': 'qty', 'type': 'number'},
        {'label': 'Rate', 'name': 'rate', 'type': 'number', 'currency': True},
        {'label': 'Amount', 'name': 'amount', 'type': 'number', 'currency': True, 'formula': 'this.rate * this.qty'},
    ]},
    {'title': 'Totals', 'type': 'normal', 'fields': [
        {'label': 'Total', 'name': 'total', 'type': 'number', 'currency': True, 'formula': 'SUM(items.amount)', 'total': True},
    ]},
]


class TemplateError(ValueError):
    pass


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', (text or '').strip().lower()).strip('_')[:60]


def sections_for_editor(template_id, version) -> List[Dict]:
    """The template's sections as the builder shows them (with the current total marked)."""
    from invoice_service import get_template_fields
    fields = get_template_fields(template_id, version)
    try:
        total_id = (db.execute_proc_single('sp_get_template_total_field', (template_id, version)) or {}).get('total_field_id')
    except DatabaseError:
        total_id = None
    sections: Dict[str, Dict] = {}
    for f in sorted(fields, key=lambda f: (f.get('section_ordinal') or 0, f.get('field_ordinal') or 0)):
        s = sections.setdefault(f['section_id'], {
            'title': f.get('section_display_name') or f.get('section_name'),
            'name': f.get('section_name'), 'type': f.get('section_type') or 'normal', 'fields': []})
        s['fields'].append({
            'label': f.get('field_display_name') or f.get('field_name'), 'name': f.get('field_name'),
            'type': f.get('data_type') or 'string', 'currency': bool(f.get('is_currency')),
            'required': bool(f.get('is_required')), 'formula': f.get('calculation_formula') or '',
            'total': f.get('field_id') == total_id})
    return list(sections.values())


def sections_from_form(form) -> Tuple[List[Dict], Optional[Tuple[int, int]]]:
    """Parse the builder. Returns (sections, (section index, field index) of the document total)."""
    try:
        count = min(int(form.get('section_count') or 0), 30)
    except ValueError:
        count = 0
    sections, used_section_names = [], set()
    total_key = (form.get('total') or '').split(':')
    total = None
    for i in range(1, count + 1):
        p = f's{i}_'
        title = (form.get(p + 'title') or '').strip()[:100]
        if not form.get(p + 'present') or not title:
            continue
        name = slug(form.get(p + 'name') or title) or f'section_{i}'
        while name in used_section_names:
            name += '_2'
        used_section_names.add(name)
        stype = form.get(p + 'type') if form.get(p + 'type') in SECTION_TYPES else 'normal'
        try:
            fcount = min(int(form.get(p + 'field_count') or 0), 40)
        except ValueError:
            fcount = 0
        fields, used = [], set()
        for j in range(1, fcount + 1):
            q = f'{p}f{j}_'
            label = (form.get(q + 'label') or '').strip()[:100]
            if not form.get(q + 'present') or not label:
                continue
            fname = slug(form.get(q + 'name') or label) or f'field_{j}'
            while fname in used:
                fname += '_2'
            used.add(fname)
            ftype = form.get(q + 'type') if form.get(q + 'type') in FIELD_TYPES else 'string'
            formula = (form.get(q + 'formula') or '').strip()[:500]
            fields.append({'label': label, 'name': fname, 'type': ftype,
                           'currency': ftype == 'number' and bool(form.get(q + 'currency')),
                           'required': bool(form.get(q + 'required')) and not formula,
                           'formula': formula if ftype == 'number' else ''})
            if total_key == [str(i), str(j)] and ftype == 'number' and stype == 'normal':
                total = (len(sections), len(fields) - 1)
        if fields:
            sections.append({'title': title, 'name': name, 'type': stype, 'fields': fields})
    return sections, total


def _latest(org_id, template_id) -> Optional[Dict]:
    for t in db.execute_proc('sp_list_templates', (org_id, True)) or []:
        if t.get('template_id') == template_id and t.get('version') == t.get('latest_version'):
            return t
    return None


def version_in_use(org_id, template_id, version) -> int:
    row = db.execute_proc_single('sp_check_template_version_has_invoices', (template_id, version, org_id))
    return int((row or {}).get('invoice_count') or 0)


def _write(template_id, version, sections, total):
    total_field_id = None
    for s_ord, s in enumerate(sections, start=1):
        sec = db.execute_proc_single('sp_create_section', (template_id, version, s['name'], s['title'], s_ord, s['type'], None))
        for f_ord, f in enumerate(s['fields'], start=1):
            row = db.execute_proc_single('sp_add_template_field', (
                sec['section_id'], f['name'], f['label'], f['type'], int(f['required']), int(f['currency']),
                f_ord, f['formula'] or None, None))
            if total == (s_ord - 1, f_ord - 1):
                total_field_id = row['field_id']
    db.execute_proc('sp_set_template_total_field', (template_id, version, total_field_id), fetch=False)


def save(org_id, form, template_id: Optional[str] = None) -> Tuple[str, Optional[int]]:
    """Create (template_id None) or update a template from the builder form.
    Returns (template_id, new version number if one had to be made, else None)."""
    sections, total = sections_from_form(form)
    if not sections:
        raise TemplateError('Add at least one section with a field')
    if total is None:
        # Default: the last calculated number in a fields section
        for si in range(len(sections) - 1, -1, -1):
            s = sections[si]
            if s['type'] == 'normal':
                nums = [fi for fi, f in enumerate(s['fields']) if f['type'] == 'number']
                if nums:
                    total = (si, nums[-1])
                    break

    if not template_id:
        name = (form.get('name') or '').strip()[:100]
        if not name:
            raise TemplateError('Give the template a name')
        currency = (form.get('currency_code') or 'INR').upper()[:3]
        row = db.execute_proc_single('sp_create_template', (org_id, name, currency, None, None))
        _write(row['template_id'], row.get('version') or 1, sections, total)
        return row['template_id'], None

    info = _latest(org_id, template_id)
    if not info:
        raise TemplateError('Template not found')
    version, new_version = info['version'], None
    if version_in_use(org_id, template_id, version):
        row = db.execute_proc_single('sp_create_template_version', (template_id, org_id, None))
        version = new_version = row.get('new_version')
    # Rebuild this (unused) version from the form
    from invoice_service import get_template_fields
    for section_id in {f['section_id'] for f in get_template_fields(template_id, version)}:
        db.execute_proc('sp_delete_section', (section_id,), fetch=False)
    _write(template_id, version, sections, total)
    return template_id, new_version
