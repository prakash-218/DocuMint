"""
The new customer page (frontend/src/islands/customer/): what they owe and how old it is, their projects and where
each one is, their documents, their statement of account, their files by project, and their contacts and details.
A customer with sites (plants, branches billed separately) shows the sites' too.
"""

from datetime import date
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from documents import display_number, fiscal_year, get_type

INVOICE_TYPES = ('invoice', 'export_invoice')


def _payment_text(p: Dict) -> str:
    if p.get('doc_type') == 'proforma':
        return f"Advance on {p.get('doc_number') or 'a proforma'}"
    if p.get('advance_number'):
        return f"Advance on {p['advance_number']}, applied to {p.get('doc_number') or 'a draft invoice'}"
    return f"Payment on {p.get('doc_number') or 'a draft invoice'}"


def statement(docs: List[Dict], payments: List[Dict], url: Callable, start_month: int = 4, sites: bool = False) -> List[Dict]:
    """Their account per currency, oldest first, with the balance after each line: every finalized tax invoice
    (owed) and every payment (paid). Quotations and proformas aren't owed, so they aren't in it; an advance is,
    from the day it came in, as money received (sp_list_customer_payments counts each payment once). sites: the
    customer has sites, so each invoice says whose it is."""
    lines = []
    for d in docs:
        if d.get('doc_type') in INVOICE_TYPES and d.get('status') in ('pending', 'paid'):
            lines.append({'date': to_date(d.get('issue_date')), 'order': 0, 'currency': d.get('currency_code') or 'INR',
                          'text': f"{get_type(d['doc_type']).label} {display_number(d)}", 'sub': d.get('customer_site') or '' if sites else '',
                          'owed': float(d.get('total_amount') or 0), 'paid': 0.0,
                          'url': url('invoices_bp.view_invoice_new', invoice_id=d['invoice_id'])})
    for p in payments:
        lines.append({'date': to_date(p.get('payment_date')), 'order': 1, 'currency': p.get('currency_code') or 'INR',
                      'text': _payment_text(p), 'sub': ' · '.join(filter(None, [p.get('method'), p.get('reference_number')])),
                      'owed': 0.0, 'paid': float(p.get('amount') or 0),
                      'url': url('invoices_bp.view_invoice_new', invoice_id=p['invoice_id'])})
    lines.sort(key=lambda x: (x['date'] or date.min, x['order']))
    accounts: Dict[str, Dict] = {}
    for x in lines:
        a = accounts.setdefault(x['currency'], {'currency': x['currency'], 'owed': 0.0, 'paid': 0.0, 'balance': 0.0, 'lines': []})
        a['owed'] += x['owed']
        a['paid'] += x['paid']
        a['balance'] = round(a['balance'] + x['owed'] - x['paid'], 2)
        a['lines'].append({'date': x['date'], 'fy': fiscal_year(x['date'], start_month) if x['date'] else None,
                           'text': x['text'], 'sub': x['sub'], 'owed': x['owed'], 'paid': x['paid'], 'balance': a['balance'],
                           'url': x['url']})
    for a in accounts.values():
        a['owed'], a['paid'] = round(a['owed'], 2), round(a['paid'], 2)
    return sorted(accounts.values(), key=lambda a: -len(a['lines']))


def file_groups(files: List[Dict], projects_by_id: Dict[str, Dict], url: Callable) -> List[Dict]:
    """Files by the project they're kept in (newest project first), then the ones in no project."""
    from project_view import file_row
    from projects import project_label
    groups: Dict[str, Dict] = {}
    for f in files:
        key = str(f.get('project_id') or '')
        p = projects_by_id.get(key)
        g = groups.setdefault(key, {'project': {'id': key, 'title': p['title'], 'label': p['label'], 'url': p['url']} if p
                                    else ({'id': key, 'title': project_label(f) or 'Project', 'label': '', 'url': None} if key else None),
                                    'files': []})
        g['files'].append(file_row(f, url))
    latest = sorted(groups.values(), key=lambda g: max(str(x['date'] or '') for x in g['files']), reverse=True)
    return sorted(latest, key=lambda g: g['project'] is None)


def build(org_id, customer: Dict, role: str, url: Callable, today: Optional[date] = None) -> Dict:
    """Everything the page shows, for this role: Sales see quotations only, and nothing they owe; viewers see it
    all and change nothing."""
    import contacts
    import home_view
    import project_view
    import projects
    import revisions
    from auth import CUSTOMER_EDITORS, EDITORS, MANAGERS, SALES
    from db import db
    from document_service import get_org_profile
    from documents import fy_start_month, load_json, suggest_tax_mode
    from layout import custom_field_defs
    today = today or date.today()
    profile = get_org_profile(org_id)[1]
    sales = role == SALES
    can = {'edit': role in EDITORS, 'edit_customer': role in CUSTOMER_EDITORS, 'manage': role in MANAGERS, 'sales': sales}
    customer_id = str(customer['customer_id'])
    sites = [] if customer.get('parent_id') else db.execute_proc('sp_list_customer_sites', (org_id, customer_id)) or []
    family = [customer_id] + [str(s['customer_id']) for s in sites]

    all_docs = [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [] if str(d.get('customer_id')) in family]
    files = [f for cid in family for f in projects.list_attachments(org_id, customer_id=cid)]
    if sales:
        all_docs = [d for d in all_docs if d.get('doc_type') == 'quote']
        files = [f for f in files if f.get('kind') not in projects.NOT_QUOTATIONS]
    docs = revisions.collapse(all_docs)
    rows = [r for r in project_view.projects_list(org_id, role, url, today)['projects'] if str(r['customer']['id']) in family]
    rows.sort(key=lambda r: str(r['last_activity'] or ''), reverse=True)
    rows.sort(key=lambda r: r['status'] != 'open')                    # open ones first, latest first

    money = None
    if not sales:
        invoices = [d for d in docs if d.get('doc_type') in INVOICE_TYPES]
        payments = db.execute_proc('sp_list_customer_payments', (org_id, family)) or []
        held: Dict[str, float] = {}
        for p in payments:
            if p.get('doc_type') == 'proforma':
                cur = p.get('currency_code') or 'INR'
                held[cur] = round(held.get(cur, 0) + float(p.get('amount') or 0), 2)
        owed = home_view.to_receive(invoices, [r for r in rows if r.get('advance')], today)
        money = {**owed, 'advance_held': held,
                 'statement': statement(docs, payments, url, fy_start_month(profile), sites=bool(sites))}
        if not sites:
            money.pop('customers')

    org = get_org_profile(org_id)[0] or {}
    state = customer.get('state') or ''
    tax_note = {'cgst_sgst': f'{state}, so CGST + SGST' if state else 'CGST + SGST', 'igst': f'{state}, so IGST' if state else 'IGST',
                'lut': 'Export, under LUT'}.get(suggest_tax_mode('invoice', org, customer), '')
    people = contacts.for_customer(org_id, customer)
    values = load_json(customer.get('custom'))
    custom = [{'label': f['label'], 'value': values[f['key']]} for f in custom_field_defs(profile, 'customer') if values.get(f['key'])]
    return project_view._plain({
        'customer': {
            'id': customer_id, 'name': customer['name'], 'site': customer.get('site') if customer.get('parent_id') else None,
            'parent': {'id': str(customer['parent_id']), 'name': customer.get('parent_name'),
                       'url': url('customers_bp.view_customer_new', customer_id=customer['parent_id'])} if customer.get('parent_id') else None,
            'tax_id': customer.get('tax_id'), 'email_domains': customer.get('email_domains'),
            'address': [x for x in [customer.get('street_address'),
                                    ', '.join(filter(None, [customer.get('city'), customer.get('state'), customer.get('zip_code')])),
                                    customer.get('country')] if x],
            'archived': bool(customer.get('is_archived')), 'custom': custom, 'tax_note': tax_note,
            'classic_url': url('customers_bp.view_customer', customer_id=customer_id),
        },
        'can': can,
        'money': money,
        'projects': rows,
        'documents': project_view.documents(docs, url),
        'statuses': projects.PROJECT_STATUSES,
        'files': file_groups(files, {str(r['id']): r for r in rows}, url),
        'files_count': len(files),
        'people': [{'contact_id': p['contact_id'], 'customer_id': p['customer_id'], 'name': p['name'], 'email': p.get('email'),
                    'phone': p.get('phone'), 'role': p.get('role'), 'gets': p['gets'], 'initials': p['initials'],
                    'at_parent': str(p['customer_id']) != customer_id} for p in people],
        'usually': contacts.USUALLY,
        'sites': [{'id': str(s['customer_id']), 'name': s.get('site') or s['name'], 'tax_id': s.get('tax_id'),
                   'archived': bool(s.get('is_archived')), 'documents': s.get('invoice_count') or 0,
                   'url': url('customers_bp.view_customer_new', customer_id=s['customer_id'])} for s in sites],
        'links': {
            'new_project': url('projects_bp.create_project', customer_id=customer_id) if can['edit'] and not customer.get('is_archived') else None,
            'new_quote': url('invoices_bp.create_invoice', doc_type='quote', customer_id=customer_id)
            if can['edit'] and not customer.get('is_archived') else None,
            'edit': url('customers_bp.edit_customer', customer_id=customer_id) if can['edit_customer'] else None,
            'add_site': url('customers_bp.create_customer', parent_id=customer_id)
            if can['manage'] and not customer.get('parent_id') and not customer.get('is_archived') else None,
        },
    })
