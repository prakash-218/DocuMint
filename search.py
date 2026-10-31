"""
The Ctrl+K search: every page, document, project, customer and template a person can go to, as one list
that the browser searches as they type (static/js/palette.js, with the project picker's forgiving matching).

Each item: kind, title and sub (what is shown), url, icon, and what the search looks at: code (numbers
such as 'TF/Q/029/26-27' or 'PRJ-047', found by '29' or 'q29' too), name (counts most) and also. date
puts recent things first among equal matches; old ones (revised, cancelled...) go last.
"""

import logging
from typing import Dict, List

from flask import current_app, url_for

from customers import label as customer_label
from db import DatabaseError, db
from documents import display_number, get_type
from layout import types_by_template
from money import format_money
import app_helpers
import permissions
import projects

logger = logging.getLogger(__name__)

# (title, endpoint, url arguments, icon, other words people may type). Each is listed for those whose permissions let
# them open it (permissions.allows).
PAGES = [
    ('Home', 'dashboard_bp.index', {}, 'house', 'dashboard overview needs attention to receive'),
    ('Notifications', 'notifications_bp.index', {}, 'bell', 'activity alerts'),
    ('Projects', 'projects_bp.list_projects', {}, 'briefcase', 'jobs'),
    ('Emails', 'emails_bp.inbox', {}, 'mail', 'inbox mail'),
    ('Quotations', 'invoices_bp.list_invoices', {'type': 'quote'}, 'file-pen-line', 'quotes'),
    ('Proformas', 'invoices_bp.list_invoices', {'type': 'proforma'}, 'file-clock', 'pi proforma invoices advance'),
    ('Invoices', 'invoices_bp.list_invoices', {}, 'file-text', 'tax export bills'),
    ('Payments', 'payments_bp.index', {}, 'wallet', 'received receipts bank utr reference advances'),
    ('Customers', 'customers_bp.list_customers', {}, 'users', 'clients buyers'),
    ('Suppliers', 'suppliers_bp.list_suppliers', {}, 'truck', 'vendors bought-out purchases'),
    ('Templates', 'templates_bp.list_templates', {}, 'layout-template', 'formats'),
    ('Rates', 'costings_bp.rates', {}, 'list', 'rates list costing prices materials machining'),
    ('Settings', 'settings_bp.index', {}, 'settings', 'business profile bank seal signature numbering team'),
    ('Roles', 'settings_bp.roles', {}, 'shield', 'permissions access custom roles team'),
    ('Audit log', 'settings_bp.audit_log', {}, 'history', 'history changes'),
]
ACTIONS = [
    ('New quotation', 'invoices_bp.create_invoice', {'doc_type': 'quote'}, 'plus', 'create quote'),
    ('New proforma invoice', 'invoices_bp.create_invoice', {'doc_type': 'proforma'}, 'plus', 'create pi'),
    ('New invoice', 'invoices_bp.create_invoice', {'doc_type': 'invoice'}, 'plus', 'create tax'),
    ('New project', 'projects_bp.create_project', {}, 'plus', 'create job'),
    ('New customer', 'customers_bp.create_customer', {}, 'plus', 'create client'),
    ('New template', 'templates_bp.create_template', {}, 'plus', 'create format'),
]

# Put before a document's number for the search, so 'pi 9' finds proforma 009 and 'inv 38' invoice 038
SHORT = {'quote': 'Q', 'proforma': 'PI', 'invoice': 'INV', 'export_invoice': 'EXP'}

# Badge colours, as the document lists show them (_macros.status_badge)
BADGES = {'paid': 'success', 'accepted': 'success', 'pending': 'warning', 'sent': 'info', 'declined': 'danger'}
OLD = ('revised', 'converted', 'cancelled', 'completed')


def _day(value) -> str:
    return current_app.jinja_env.filters['date'](value) if value else ''


def _sub(*parts) -> str:
    return ' · '.join(str(p) for p in parts if p)


def _links(rows, kind) -> List[Dict]:
    return [{'kind': kind, 'title': title, 'url': url_for(endpoint, **args), 'icon': icon, 'name': title, 'also': also}
            for title, endpoint, args, icon, also in rows]


def _project(p) -> Dict:
    status = p.get('status') or 'open'
    docs = p.get('document_count') or 0
    return {'kind': 'project', 'title': p.get('title') or '', 'icon': 'briefcase',
            'url': url_for('projects_bp.view_project', project_id=p['project_id']),
            'sub': _sub('Project', projects.project_label(p), customer_label(p),
                        p.get('fiscal_year') and 'FY ' + p['fiscal_year'],
                        docs and f"{docs} document{'' if docs == 1 else 's'}"),
            'code': projects.project_label(p), 'name': p.get('title') or '',
            'also': _sub(p.get('customer_name'), p.get('customer_site'), p.get('reference'), p.get('fiscal_year')),
            'date': str(p.get('last_issue_date') or p.get('created_at') or '')[:10],
            'badge': status if status != 'open' else '', 'old': status in OLD}


def _customer(c) -> Dict:
    count = c.get('invoice_count') or 0
    return {'kind': 'customer', 'title': customer_label(c), 'icon': 'building-2',
            'url': url_for('customers_bp.view_customer', customer_id=c['customer_id']),
            'sub': _sub('Customer', c.get('parent_name') and 'Site of ' + c['parent_name'], c.get('city'),
                        count and f"{count} document{'' if count == 1 else 's'}"),
            'name': _sub(c.get('name'), c.get('site')), 'also': _sub(c.get('parent_name'), c.get('city'), c.get('tax_id'))}


def _document(d) -> Dict:
    info = get_type(d.get('doc_type'))
    status = 'overdue' if app_helpers.invoice_is_overdue(d) else (d.get('status') or 'draft')
    return {'kind': 'document', 'title': display_number(d), 'icon': info.icon,
            'url': url_for('invoices_bp.view_invoice', invoice_id=d['invoice_id']),
            'sub': _sub(info.label, customer_label(d), d.get('subject'), _day(d.get('issue_date')),
                        d.get('total_amount') and format_money(d['total_amount'], d.get('currency_code'))),
            'code': _sub(SHORT.get(d.get('doc_type')), display_number(d)), 'name': d.get('subject') or '',
            'also': _sub(info.label, info.short, d.get('customer_name'), d.get('customer_site'), d.get('buyer_order_no'),
                         d.get('project_title')),
            'date': str(d.get('issue_date') or '')[:10],
            'badge': status, 'tone': 'danger' if status == 'overdue' else BADGES.get(status, 'secondary'),
            'old': status in OLD}


def _templates(org_id) -> List[Dict]:
    rows = [t for t in db.execute_proc('sp_list_templates', (org_id, False)) or []
            if t.get('version') == t.get('latest_version')]
    types = types_by_template(org_id, rows)
    return [{'kind': 'template', 'title': t.get('name') or '', 'icon': 'layout-template',
             'url': url_for('templates_bp.view_template', template_id=t['template_id']),
             'sub': _sub('Template', t.get('currency_code'),
                         'For ' + ', '.join(get_type(k).plural.lower() for k in types.get(t['template_id']) or [])),
             'name': t.get('name') or '', 'also': 'template'}
            for t in rows]


def _opens(row, perms) -> bool:
    title, endpoint, args, icon, also = row
    doc_type = args.get('doc_type') or args.get('type') or ('invoice' if endpoint.startswith('invoices_bp.') else None)
    return permissions.allows(endpoint, doc_type, perms)


def palette_items(org_id, perms) -> List[Dict]:
    """Everything the Ctrl+K search can find for someone with these permissions (permissions.granted(), or a built-in
    role's name): the pages and actions they may open, and the projects, customers, documents and templates they read."""
    perms = permissions.of(perms)
    allowed = [r for r in PAGES + ACTIONS if _opens(r, perms)]
    items = _links([r for r in allowed if r in PAGES], 'page') + _links([r for r in allowed if r in ACTIONS], 'action')
    readable = permissions.doc_types('read', perms)
    try:
        if permissions.can('projects.read', perms=perms):
            items += [_project(p) for p in projects.list_projects(org_id)]
        if permissions.can('customers.read', perms=perms):
            items += [_customer(c) for c in db.execute_proc('sp_list_customers', (org_id, False)) or []]
        items += [_document(d) for d in db.execute_proc('sp_list_search_documents', (org_id,)) or []
                  if d.get('doc_type') in readable]
        items += _templates(org_id) if permissions.can('templates.read', perms=perms) else []
    except DatabaseError:
        logger.exception('Could not list everything for the search')
    return items
