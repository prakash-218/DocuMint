"""
Costings for the React app (frontend/src/islands/costing/): a costing in its editor (GET /api/costings/<id>) and the
rates list (GET /api/costings/rates). The editor works its numbers out on the server as it's edited (costings_bp.preview,
the same costing.py that saves) and posts the server page's form to costings_bp.save; the rates list posts
rates_json to costings_bp.rates. Owners and admins only: costs and margins never reach anyone else.
"""

from typing import Callable, Dict, Optional


def editor(org_id, row: Dict, base: str, url: Callable) -> Dict:
    import costing as K
    import permissions
    from blueprints.costings_bp import _quote_templates
    from money import SYMBOLS
    from projects import project_label
    costing_id = str(row['costing_id'])
    others = [c for c in K.list_for(org_id, row['project_id']) if str(c['costing_id']) != costing_id]
    quote = None
    if row.get('quote_id'):
        quote = {'url': url('invoices_bp.view_invoice', invoice_id=row['quote_id']), 'number': row.get('quote_number') or 'The quote',
                 'status': row.get('quote_status') or 'draft'}
    return {
        'title': f"Costing v{row['version']}",
        'tab': f"Costing v{row['version']} · {row.get('title') or ''}",
        'costing': {'id': costing_id, 'version': row['version'], 'title': row.get('title') or '', 'notes': row.get('notes') or '',
                    'project': {'label': project_label(row), 'title': row.get('project_title') or '',
                                'url': url('projects_bp.view_project', project_id=row['project_id'])},
                    'customer': row.get('customer_name') or '', 'quote': quote},
        'sheet': row['sheet'],                       # as stored (costing.clean_sheet): what the inputs start from
        'settings': {**K.settings_from(row), 'target_total': K.number(row.get('target_total'))},
        'result': K.result_of(row),                  # every worked-out number, as costings_bp.preview returns them
        'base': base,
        'options': {'modes': [[k, v] for k, v in K.MODES.items()], 'rounding': list(K.ROUNDING), 'currencies': sorted(SYMBOLS),
                    'spreads': [[k, v] for k, v in K.SPREADS.items()], 'shared_kinds': [[k, v] for k, v in K.SHARED_KINDS.items()]},
        'templates': [{'id': str(t['template_id']), 'name': t.get('name') or ''} for t in _quote_templates(org_id, row['currency'])],
        'versions': [{'url': url('costings_bp.edit', costing_id=v['costing_id']), 'version': v['version'],
                      'total': K.number(v.get('total_price'), 0), 'currency': v.get('currency') or base,
                      'profit_on_cost': v.get('profit_on_cost'), 'quote_number': v.get('quote_number') or ''} for v in others],
        'rates': K.rates(org_id),
        'urls': {'save': url('costings_bp.save', costing_id=costing_id), 'preview': url('costings_bp.preview', costing_id=costing_id),
                 'library': url('costings_bp.library'), 'items': url('costings_bp.items', costing_id='COSTING'),
                 'import': url('costings_bp.read_spreadsheet', costing_id=costing_id),
                 'rates': url('costings_bp.rates', back=costing_id), 'new_version': url('costings_bp.create'),
                 'delete': url('costings_bp.delete', costing_id=costing_id), 'project_id': str(row['project_id']),
                 # buying some of its lines: a purchase order of them (editor_page.new_page's from_costing)
                 'purchase_order': url('invoices_bp.create_invoice', doc_type='purchase_order', project_id=row['project_id'],
                                       from_costing=costing_id) if permissions.can_doc('write', 'purchase_order') else None},
    }


def rates_page(org_id, back: Optional[Dict], base: str, url: Callable) -> Dict:
    import costing as K
    known = K.rates(org_id)
    return {
        'title': 'Rates list',
        'base': base,
        'action': url('costings_bp.rates', back=str(back['costing_id']) if back else None),
        'back': {'url': url('costings_bp.edit', costing_id=back['costing_id']), 'version': back['version']} if back else None,
        'rates': known,
        'suggestions': K.rate_suggestions(org_id, known),
    }
