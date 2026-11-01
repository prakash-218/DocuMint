"""
The customer portal's two screens for its React app (frontend/src/portal/): the documents a customer has (GET
/customer/api/documents) and one document (GET /customer/api/documents/<id>), drawn with the same _document.html and
_summary.html the portal always used. Customers see only their own sent documents (sp_get_customer_invoices).
"""

from typing import Callable, Dict, List

from flask import current_app, render_template_string

BADGES = {'paid': 'success', 'accepted': 'success', 'pending': 'warning', 'sent': 'info', 'declined': 'danger',
          'converted': 'secondary', 'revised': 'secondary', 'draft': 'secondary', 'issued': 'info', 'cancelled': 'secondary'}


def _filter(name):
    return current_app.jinja_env.filters[name]


def documents(customer_id, url: Callable) -> Dict:
    from app_helpers import invoice_is_overdue
    from db import db
    from documents import balance_of, display_number, get_type, sum_by_currency
    from pagination import paginate
    invoices = db.execute_proc('sp_get_customer_invoices', (customer_id,)) or []
    if not isinstance(invoices, list):
        invoices = [invoices]
    # a credit or debit note only once it's issued; it's counted on its invoice (balance_of), never owed itself
    invoices = [i for i in invoices if not get_type(i.get('doc_type')).adjusts or i.get('status') == 'issued']
    payable = [i for i in invoices if get_type(i.get('doc_type')).takes_payments and i.get('status') == 'pending']
    outstanding = sum_by_currency(payable, balance_of)
    paid = sum_by_currency(invoices, lambda i: float(i.get('paid_amount') or 0) - float(i.get('refunded_amount') or 0))
    page = paginate(invoices)
    currency, day = _filter('currency'), _filter('date')
    rows: List[Dict] = []
    for i in page.items:
        cur = i.get('currency_code')
        note = bool(get_type(i.get('doc_type')).adjusts)
        balance = balance_of(i)
        owed = i.get('doc_type') in ('invoice', 'export_invoice') and i.get('status') != 'paid' and balance
        status = {'text': 'Overdue', 'tone': 'danger'} if invoice_is_overdue(i) else \
            {'text': i.get('status') or 'draft', 'tone': BADGES.get(i.get('status') or 'draft', 'secondary')}
        rows.append({'id': str(i['invoice_id']), 'url': url('customer_portal_bp.view_invoice', invoice_id=i['invoice_id']),
                     'pdf': url('customer_portal_bp.export_pdf', invoice_id=i['invoice_id']), 'number': display_number(i),
                     'kind': get_type(i.get('doc_type')).label, 'date': day(i.get('issue_date')) or '—',
                     'due': '—' if note else day(i.get('due_date')) or '—', 'status': status,
                     'total': ('−' if get_type(i.get('doc_type')).adjusts < 0 else '') + currency(i.get('total_amount'), cur),
                     'balance': currency(balance, cur) if owed else None})
    totals = _filter('money_totals')
    return {
        'title': 'My documents',
        'stats': {'outstanding': totals(outstanding) if outstanding else 'Nothing due',
                  'overdue': sum(1 for i in payable if invoice_is_overdue(i)),
                  'paid': totals(paid) if paid else '—'},
        'rows': rows,
        'page': page.json(),
    }


def document(header: Dict, values, url: Callable) -> Dict:
    from db import db
    from documents import display_number
    from invoice_service import build_sections, invoice_summary, with_discount_column
    sections = build_sections(header, values)
    payments = db.execute_proc('sp_get_invoice_payments', (header['invoice_id'],)) or []
    ctx = {'invoice': header, 'sections_data': sections, 'payments': payments,
           'summary': invoice_summary(header, sections, payments)}
    return {
        'title': display_number(header),
        'from': header.get('organization_name') or '',
        'back': url('customer_portal_bp.dashboard'),
        'pdf': url('customer_portal_bp.export_pdf', invoice_id=header['invoice_id']),
        'document_html': render_template_string('{% include "invoices/_document.html" %}',
                                                **{**ctx, 'sections_data': with_discount_column(sections)}),
        'summary_html': render_template_string('{% include "invoices/_summary.html" %}', **ctx),
    }
