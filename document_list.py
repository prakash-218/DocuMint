"""
The quotation, proforma and invoice lists (the React screen in frontend/src/islands/documents/), as the prototype
draws them: one row per document (a revised one once, as its latest version) with where it stands in a word and a
short note under it, and the tabs that filter them.
"""

import re
from datetime import date
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from document_view import FOLLOW_UP_AFTER, pill
from documents import balance_of, display_number, get_type
from payment_terms import due_on
import revisions

GROUPS = {
    'quotes': {'title': 'Quotations', 'types': ('quote',), 'new_type': 'quote', 'until': 'Valid until',
               'tabs': [('all', 'All'), ('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'),
                        ('declined', 'Declined'), ('converted', 'Converted')]},
    'proformas': {'title': 'Proforma invoices', 'types': ('proforma',), 'new_type': 'proforma', 'until': None,
                  'tabs': [('all', 'All'), ('draft', 'Draft'), ('sent', 'Sent'), ('converted', 'Invoiced')]},
    'invoices': {'title': 'Invoices', 'types': ('invoice', 'export_invoice'), 'new_type': 'invoice', 'until': 'Due',
                 'tabs': [('all', 'All'), ('draft', 'Draft'), ('pending', 'Unpaid'), ('overdue', 'Overdue'), ('paid', 'Paid')]},
}


def _days(n: int) -> str:
    return f'{n} day{"" if n == 1 else "s"}'


_ABOUT = re.compile(r'^\s*(quotation|offer|proforma(\s+invoice)?|(tax\s+)?invoice)\s+for\s+(the\s+)?', re.I)


def short_subject(subject: Optional[str]) -> str:
    """The subject without the 'Quotation for the' every one starts with: 'Axle final assembly for G8'."""
    text = _ABOUT.sub('', subject or '').strip()
    return text[:1].upper() + text[1:]


def state(doc: Dict, today: date, usual_days: Optional[int] = None) -> Dict:
    """{tab, tag {text, tone}, note}: the tab it's under, its state in a word and, under it, what that means today.
    An invoice is due on its own due date, else after the customer's payment terms (or usual_days, the usual ones)."""
    kind = get_type(doc.get('doc_type'))
    status = doc.get('status') or 'draft'
    paid, balance = float(doc.get('paid_amount') or 0), balance_of(doc)
    tag = pill(doc, {'balance': balance, 'paid': paid}, advance_received=paid if kind.key == 'proforma' else 0)
    issued = to_date(doc.get('issue_date'))
    if status in ('draft', 'revised'):
        return {'tab': 'draft', 'tag': tag, 'note': ''}
    if kind.key == 'quote':
        if status == 'sent' and issued:
            waited = (today - issued).days
            if waited > FOLLOW_UP_AFTER:
                return {'tab': 'sent', 'tag': {'text': 'Sent', 'tone': 'action'}, 'note': f'No answer · {_days(waited)}'}
            return {'tab': 'sent', 'tag': tag, 'note': 'Sent today' if waited <= 0 else f'Sent {_days(waited)} ago'}
        if status == 'converted':
            return {'tab': 'converted', 'tag': {'text': 'Converted', 'tone': 'done'}, 'note': ''}
        return {'tab': status if status in ('sent', 'accepted', 'declined') else 'accepted', 'tag': tag, 'note': ''}
    if kind.key == 'proforma':
        return {'tab': 'converted' if status == 'converted' else 'sent', 'tag': tag, 'note': ''}
    if status == 'paid' or balance <= 0.005:
        return {'tab': 'paid', 'tag': {'text': 'Paid', 'tone': 'done'}, 'note': ''}
    due = due_on(doc, usual_days)
    if due and due < today:
        return {'tab': 'overdue', 'tag': {'text': 'Overdue', 'tone': 'late'}, 'note': f'{_days((today - due).days)} late'}
    note = '' if not due else 'Due today' if due == today else f'Due in {_days((due - today).days)}'
    return {'tab': 'pending', 'tag': tag, 'note': note}


def rows(docs: List[Dict], url: Callable, today: Optional[date] = None, usual_days: Optional[int] = None) -> List[Dict]:
    """The list's rows, newest first as the documents come; docs are one group's, revisions already collapsed."""
    import projects
    today = today or date.today()
    out = []
    for d in docs:
        kind = get_type(d.get('doc_type'))
        versions = d.get('versions') or []
        project = {'label': projects.project_label(d), 'title': d.get('project_title') or '',
                   'url': url('projects_bp.view_project', project_id=d['project_id'])} if d.get('project_id') else None
        out.append({
            'id': d['invoice_id'], 'number': display_number(d) or 'Draft', 'kind': kind.label, 'subject': short_subject(d.get('subject')),
            'project': project, 'customer': {'id': d.get('customer_id'), 'name': d.get('customer_name') or '', 'site': d.get('customer_site')},
            'date': d.get('issue_date'),
            'until': due_on(d, usual_days) if kind.takes_payments else d.get('due_date') if kind.key == 'quote' else None,
            **state(d, today, usual_days),
            'currency': d.get('currency_code') or 'INR', 'total': float(d.get('total_amount') or 0),
            'balance': balance_of(d) if kind.takes_payments and (d.get('status') or 'draft') not in ('draft', 'paid') else None,
            'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id']),
            'pdf': url('invoices_bp.export_pdf', invoice_id=d['invoice_id']),
            'versions': [{'number': display_number(v), 'url': url('invoices_bp.view_invoice', invoice_id=v['invoice_id'])} for v in versions],
            'search': [n for n in (d.get('buyer_order_no'), *(display_number(v) for v in versions)) if n],
        })
    return out


def build(group: str, docs: List[Dict], url: Callable, can_create: bool, today: Optional[date] = None,
          usual_days: Optional[int] = None) -> Dict:
    """Everything the list screen draws for /quotes/, /proformas/ or /invoices/."""
    import project_view
    info = GROUPS[group]
    mine = [d for d in docs if (d.get('doc_type') or 'invoice') in info['types']]
    if group != 'invoices':
        mine = revisions.collapse(mine)
    return project_view._plain({'group': group, 'title': info['title'], 'until': info['until'],
            'tabs': [{'key': k, 'label': label} for k, label in info['tabs']],
            'rows': rows(mine, url, today, usual_days),
            'new_url': url('invoices_bp.create_invoice', doc_type=info['new_type']) if can_create else None,
            'new_label': f"New {get_type(info['new_type']).short.lower()}"})
