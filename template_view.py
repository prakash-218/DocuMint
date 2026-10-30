"""
Templates for the React app (frontend/src/islands/templates/): the list of cards (GET /api/templates), a template's
page with its preview on sample values (GET /api/templates/<id>), its pages & printing (GET /api/templates/<id>/layout)
and the builder for a new one or its fields (GET /api/templates/new, /api/templates/<id>/fields). Their forms post to
the templates_bp routes as the server pages did, which save them.
"""

from typing import Callable, Dict, List, Optional

MANAGERS = ('owner', 'admin')
BADGES = {'paid': 'success', 'accepted': 'success', 'pending': 'warning', 'sent': 'info', 'declined': 'danger',
          'converted': 'secondary', 'revised': 'secondary', 'draft': 'secondary'}


def _number(value) -> str:
    """The pages' number filter: 1,250 or 1,250.50."""
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        return '0'
    return f'{int(num):,}' if num == int(num) else f'{num:,.2f}'


def _cell(v: Dict, cur: str) -> str:
    from money import format_money
    if v.get('data_type') == 'number':
        return format_money(v.get('val_number'), cur) if v.get('is_currency') else _number(v.get('val_number'))
    return v.get('val_string') or ''


def _kind(f: Dict, cur: str) -> str:
    if f.get('calculation_formula'):
        return 'calculated'
    if f.get('data_type') == 'number':
        return f'{cur} amount' if f.get('is_currency') else 'number'
    return {'date': 'date', 'boolean': 'yes / no'}.get(f.get('data_type'), 'text')


def cards(org_id, archived: bool, role: str, url: Callable) -> Dict:
    from documents import get_type
    from pagination import paginate
    from template_service import template_cards
    page = paginate(template_cards(org_id, archived), per_page=12)           # cards: a grid of 12
    manage = role in MANAGERS
    return {
        'title': 'Templates',
        'archived': archived,
        'toggle': {'href': url('templates_bp.list_templates', include_archived='false' if archived else 'true'),
                   'label': 'Hide archived' if archived else 'Show archived'},
        'new': url('templates_bp.create_template') if manage else None,
        'cards': [{'url': url('templates_bp.view_template', template_id=t['template_id']), 'name': t.get('name') or '',
                   'archived': bool(t.get('is_archived')), 'currency': t.get('currency_code') or '', 'version': t.get('version'),
                   'used_for': (', '.join(get_type(k).plural for k in t['used_for']).lower() if len(t['used_for']) < 3
                                else 'every document type'),
                   'sections': [{'title': s['title'], 'items': s['type'] == 'line_item', 'columns': s['columns']} for s in t['sections']],
                   'used': t['used']} for t in page.items],
        'page': page.json('templates'),
    }


def _pages(layout: Dict) -> List[Dict]:
    from documents import get_type
    out = []
    for pg in layout['pages']:
        sub = 'All document types' if not pg['doc_types'] else ', '.join(get_type(k).label for k in pg['doc_types'])
        sub += ' · ' + ('in the same PDF' if pg['with_document'] else 'separate PDF')
        if pg['copies']:
            sub += f" · {len(pg['copies'])} cop{'y' if len(pg['copies']) == 1 else 'ies'}"
        out.append({'title': pg['title'] or 'Main document', 'kind': pg['kind'], 'sub': sub})
    return out


def overview(org_id, template_id: str, role: str, url: Callable) -> Optional[Dict]:
    from app_helpers import invoice_is_overdue
    from documents import DOC_TYPES, display_number, get_type
    from template_service import template_overview
    t = template_overview(org_id, template_id)
    if not t:
        return None
    info, cur = t['info'], t['info'].get('currency_code') or 'INR'
    editable = not info.get('is_archived')
    total_id = (t['total_field'] or {}).get('field_id')
    preview = []
    for title, section in t['sections'].items():
        kind = 'Cost break-up' if section.get('breakup') else ('Line items' if section['type'] == 'line_item' else 'Fields')
        entry = {'title': title, 'kind': kind, 'items': section['type'] == 'line_item'}
        if section['type'] == 'line_item':
            first = section['line_item_rows'][0] if section.get('line_item_rows') else []
            entry['columns'] = [{'label': f.get('field_label') or '', 'required': bool(f.get('is_required')), 'kind': _kind(f, cur),
                                 'num': f.get('data_type') == 'number', 'calc': bool(f.get('calculation_formula'))} for f in first]
            entry['rows'] = [[_cell(v, cur) for v in row] for row in section['line_item_rows']]
        else:
            entry['fields'] = [{'label': v.get('field_label') or '', 'value': _cell(v, cur) if v.get('data_type') == 'number' else (v.get('val_string') or '—'),
                                'calc': bool(v.get('calculation_formula')), 'total': bool(total_id and v.get('field_id') == total_id)}
                               for v in section.get('fields') or []]
        preview.append(entry)
    documents = [{'number': display_number(d), 'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id']),
                  'kind': get_type(d.get('doc_type')).label, 'customer': d.get('customer_name') or '',
                  'status': {'text': 'Overdue', 'tone': 'danger'} if invoice_is_overdue(d)
                  else {'text': d.get('status') or 'draft', 'tone': BADGES.get(d.get('status') or 'draft', 'secondary')}}
                 for d in t['documents'][:6]]
    manage = role in MANAGERS
    return {
        'title': info.get('name') or '',
        'sub': f"Template · v{info['version']} · {cur} · {t['field_count']} fields",
        'archived': bool(info.get('is_archived')),
        'use': [{'label': f'New {dt.label.lower()}', 'href': url('invoices_bp.create_invoice', doc_type=key, template_id=template_id)}
                for key, dt in DOC_TYPES.items()] if editable and role in ('owner', 'admin', 'member') else [],
        'layout': url('templates_bp.edit_layout', template_id=template_id) if editable and manage else None,
        'edit': url('templates_bp.edit_template', template_id=template_id) if editable and manage else None,
        'broken': sum(1 for f in t['formulas'] if f['error']),
        'preview': preview,
        'breakups': bool(t['summary'].get('breakups')),
        'formulas': [{'label': f['label'], 'section': f['section'] or '', 'plain': f['plain'], 'formula': f['formula'],
                      'error': f['error'] or '', 'total': f['is_total']} for f in t['formulas']],
        'no_total': not t['total_field'],
        'pages': _pages(t['layout']),
        'documents': {'count': len(t['documents']), 'rows': documents},
        'versions': [{'version': v['version'], 'date': v.get('created_at')} for v in t['versions']],
        'archive': ({'action': url('templates_bp.unarchive_template' if info.get('is_archived') else 'templates_bp.archive_template',
                                   template_id=template_id), 'archived': bool(info.get('is_archived'))} if manage else None),
    }


def layout_page(org_id, template_id: str, info: Dict, url: Callable) -> Dict:
    """Pages & printing: which pages the template prints, their copies, columns and box fields."""
    from blueprints.templates_bp import _ticked_types
    from documents import CHOOSABLE, DOC_TYPES
    from invoice_service import get_template_fields
    from layout import PAGE_KINDS, load_layout, template_is_export
    layout = load_layout(template_id, org_id)
    item_fields, sections = [], []
    for f in get_template_fields(template_id, info.get('latest_version')):
        if f.get('section_type') == 'line_item' and 'break' not in (f.get('section_name') or '').lower():
            if f['field_name'] not in [x['name'] for x in item_fields]:
                item_fields.append({'name': f['field_name'], 'label': f.get('field_display_name') or f['field_name']})
        sec = {'name': (f.get('section_name') or '').lower(), 'label': f.get('section_display_name') or f.get('section_name')}
        if sec not in sections:
            sections.append(sec)
    return {
        'title': 'Pages & printing', 'name': info.get('name') or info.get('template_name') or '',
        'back': url('templates_bp.view_template', template_id=template_id),
        'action': url('templates_bp.edit_layout', template_id=template_id),
        'used_for': _ticked_types(info, layout), 'guessed': layout.get('used_for') is None,
        'export': 'auto' if layout.get('export') is None else ('yes' if layout['export'] else 'no'),
        'auto_export': template_is_export(template_id, org_id, {**layout, 'export': None}),
        'choosable': [[k, DOC_TYPES[k].plural] for k in CHOOSABLE],
        'doc_types': [[k, dt.label] for k, dt in DOC_TYPES.items()],
        'kinds': PAGE_KINDS,
        'pages': layout['pages'],
        'item_fields': item_fields,
        'sections': sections,
    }


def builder(org_id, template_id: Optional[str], info: Optional[Dict], sections: List[Dict], url: Callable, in_use: int = 0) -> Dict:
    """The builder: a new template (STARTER) or the latest version's fields. It posts s<i>_..., s<i>_f<j>_..., section_count
    and total (template_builder.sections_from_form)."""
    import template_builder as TB
    from document_service import get_org_profile
    from documents import CHOOSABLE, DOC_TYPES
    from money import SYMBOLS
    total = ''
    for i, sec in enumerate(sections, start=1):
        for j, f in enumerate(sec['fields'], start=1):
            if f.get('total'):
                total = f'{i}:{j}'
    creating = not template_id
    return {
        'title': 'New template' if creating else f"Edit {info.get('name') or ''}",
        'creating': creating,
        'sub': '' if creating else f"{info.get('currency_code')} · v{info['version']}",
        'action': url('templates_bp.create_template') if creating else url('templates_bp.edit_template', template_id=template_id),
        'cancel': url('templates_bp.list_templates') if creating else url('templates_bp.view_template', template_id=template_id),
        'in_use': (f"{in_use} document{' uses' if in_use == 1 else 's use'} v{info['version']}. Saving creates "
                   f"v{info['version'] + 1}; existing documents don't change.") if in_use else '',
        'sections': [{'title': s.get('title') or '', 'name': s.get('name') or '', 'type': s.get('type') or 'line_item',
                      'fields': [{'label': f.get('label') or '', 'name': f.get('name') or '', 'type': f.get('type') or 'string',
                                  'formula': f.get('formula') or '', 'currency': bool(f.get('currency')),
                                  'required': bool(f.get('required'))} for f in s['fields']]} for s in sections],
        'total': total,
        'field_types': [[k, v] for k, v in TB.FIELD_TYPES.items()],
        'section_types': [[k, v] for k, v in TB.SECTION_TYPES.items()],
        'currencies': list(SYMBOLS),
        'currency': get_org_profile(org_id)[1].get('default_currency') or 'INR',
        'choosable': [[k, DOC_TYPES[k].plural] for k in CHOOSABLE],
    }
