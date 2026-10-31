"""
Document URLs by type: /quotes/<id>, /proformas/<id>, /invoices/<id> (tax and export).

Routes take a <doc_path> segment; url_for() fills it in from the document's type,
so templates keep writing url_for('invoices_bp.view_invoice', invoice_id=...).
Types are remembered from rows the request already loaded (any row with
invoice_id + doc_type), so building links rarely costs a query. A GET on the
wrong segment (old /invoices/<quote id> links) redirects to the right one.
"""

from flask import current_app, g, has_request_context, redirect, request, url_for

DOC_PATHS = {'quote': 'quotes', 'proforma': 'proformas', 'invoice': 'invoices', 'export_invoice': 'invoices',
             'purchase_order': 'purchase-orders'}
PATH_TYPES = {'quotes': 'quote', 'proformas': 'proforma', 'invoices': 'invoice', 'purchase-orders': 'purchase_order'}
SEGMENT = '<any(quotes, proformas, invoices, "purchase-orders"):doc_path>'
LIST_GROUPS = {'quote': 'quotes', 'proforma': 'proformas', 'invoices': 'invoices', 'purchase_order': 'purchase-orders',
               None: 'invoices'}


def path_for(doc_type) -> str:
    return DOC_PATHS.get(doc_type, 'invoices')


def _cache():
    if not hasattr(g, '_doc_types'):
        g._doc_types = {}
    return g._doc_types


def remember(results):
    """Row observer (see db.add_row_observer): note the type of every document row seen."""
    if not has_request_context() or not results:
        return
    cache = _cache()
    for item in results:
        rows = item if isinstance(item, list) else [item]
        for row in rows:
            if isinstance(row, dict) and row.get('invoice_id') and row.get('doc_type'):
                cache[str(row['invoice_id'])] = row['doc_type']


def doc_type_of(invoice_id):
    cache = _cache()
    key = str(invoice_id)
    if key not in cache:
        from db import db, DatabaseError
        try:
            row = db.execute_proc_single('sp_get_document_type', (key,))
        except DatabaseError:
            row = None
        cache[key] = (row or {}).get('doc_type') or 'invoice'
    return cache[key]


def _takes_path(endpoint) -> bool:
    known = current_app.extensions.setdefault('doc_path_endpoints', {})
    if endpoint not in known:
        known[endpoint] = any('doc_path' in r.arguments for r in current_app.url_map.iter_rules(endpoint))
    return known[endpoint]


def install(bp):
    """Wire a blueprint whose document routes contain SEGMENT."""

    @bp.url_value_preprocessor
    def _pop_path(endpoint, values):
        if values and 'doc_path' in values:
            g.doc_path = values.pop('doc_path')

    @bp.url_defaults
    def _add_path(endpoint, values):
        if 'doc_path' in values or not _takes_path(endpoint):
            return
        if values.get('invoice_id'):
            values['doc_path'] = path_for(doc_type_of(values['invoice_id']))
        elif 'type' in values:                       # list pages: type=quote / proforma / None
            values['doc_path'] = LIST_GROUPS.get(values.pop('type'), 'invoices')
        else:
            values['doc_path'] = path_for(values.get('doc_type'))

    @bp.before_request
    def _canonical():
        args = request.view_args or {}
        if request.method != 'GET' or not getattr(g, 'doc_path', None):
            return None
        if args.get('invoice_id'):
            right = path_for(doc_type_of(args['invoice_id']))
        elif request.args.get('type') in ('quote', 'proforma') and g.doc_path == 'invoices':
            right = LIST_GROUPS[request.args['type']]      # old /invoices/?type=quote links
        else:
            return None
        if right == g.doc_path:
            return None
        query = {k: v for k, v in request.args.items(multi=False) if k != 'type'}
        return redirect(url_for(request.endpoint, **args, **query, doc_path=right), code=301)
