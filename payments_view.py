"""
The payments list (the React screen in frontend/src/islands/payments/): every payment received, newest first, each
once on the document it counts on now, with how it came (method and bank reference) and, for one in a foreign
currency, the rupees the bank credited. An advance shows on its proforma until it's applied, then on the invoice it
went to, with the proforma it came in on. The tabs split advances from payments against invoices. Money paid back on
a credit note (refunds: sp_list_org_refunds) is a row of its own, as a negative amount, under Refunds.
"""

import re
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from documents import display_number, get_type

TABS = [('all', 'All'), ('advance', 'Advances'), ('invoice', 'Against invoices'), ('refund', 'Refunds')]


def _day(value) -> str:
    """'2026-10-28': the day it came, as the statements and the document page take it (app_helpers.to_date)."""
    found = to_date(value)
    return found.isoformat() if found else ''


def _method(text) -> str:
    """How it came, in words: older payments kept a key ('bank_transfer'), newer ones the form's label."""
    text = (text or '').strip()
    return text.replace('_', ' ').capitalize() if re.fullmatch(r'[a-z_]+', text) else text


def rows(payments: List[Dict], docs: List[Dict], url: Callable, refunds: Optional[List[Dict]] = None) -> List[Dict]:
    """One row per payment, and one per refund (newest first, with the payments); docs (sp_list_invoices) give each
    its project and the customer's site."""
    import projects
    by_id = {str(d['invoice_id']): d for d in docs}

    def project_of(doc):
        return {'label': projects.project_label(doc), 'title': doc.get('project_title') or '',
                'url': url('projects_bp.view_project', project_id=doc['project_id'])} if doc.get('project_id') else None
    out = []
    for p in payments:
        doc = by_id.get(str(p['invoice_id'])) or {}
        currency = p.get('currency_code') or 'INR'
        credited = p.get('received_amount') if p.get('received_currency') and p.get('received_currency') != currency else None
        project = project_of(doc)
        advance = bool(p.get('advance_of'))
        out.append({
            'id': str(p['payment_id']), 'date': _day(p.get('payment_date')),
            'amount': float(p.get('amount') or 0), 'currency': currency,
            'credited': {'amount': float(credited), 'currency': p['received_currency']} if credited is not None else None,
            'method': _method(p.get('method')), 'reference': p.get('reference_number') or '',
            'tab': 'advance' if advance else 'invoice',
            # an applied advance names the proforma it came in on
            'note': (f"Advance on {p['advance_number']}" if p.get('advance_number') else 'Advance') if advance else '',
            'document': {'number': display_number(p), 'kind': get_type(p.get('doc_type')).label,
                         'url': url('invoices_bp.view_invoice', invoice_id=p['invoice_id'])},
            'customer': {'id': str(p.get('customer_id') or ''), 'name': p.get('customer_name') or '', 'site': doc.get('customer_site')},
            'project': project,
        })
    for r in refunds or []:
        doc = by_id.get(str(r['invoice_id'])) or {}
        out.append({
            'id': f"refund-{r['refund_id']}", 'date': _day(r.get('refunded_on')),
            'amount': -float(r.get('amount') or 0), 'currency': r.get('currency_code') or 'INR', 'credited': None,
            'method': 'Refund', 'reference': r.get('reference') or '', 'tab': 'refund',
            'note': f"Refund on {display_number(r)}" + (f", against {r['source_number']}" if r.get('source_number') else ''),
            'document': {'number': display_number(r), 'kind': get_type(r.get('doc_type')).label,
                         'url': url('invoices_bp.view_invoice', invoice_id=r['invoice_id'])},
            'customer': {'id': str(r.get('customer_id') or ''), 'name': r.get('customer_name') or '', 'site': doc.get('customer_site')},
            'project': project_of(doc),
        })
    return sorted(out, key=lambda x: x['date'], reverse=True) if refunds else out


def build(payments: List[Dict], docs: List[Dict], url: Callable, refunds: Optional[List[Dict]] = None) -> Dict:
    """Everything the payments screen draws. The Refunds tab only when there are any."""
    import project_view
    tabs = [(k, label) for k, label in TABS if k != 'refund' or refunds]
    return project_view._plain({'title': 'Payments', 'tabs': [{'key': k, 'label': label} for k, label in tabs],
                                'rows': rows(payments, docs, url, refunds), 'export': url('payments_bp.export_csv')})
