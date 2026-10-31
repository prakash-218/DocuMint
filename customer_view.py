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
                          'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id'])})
    for p in payments:
        lines.append({'date': to_date(p.get('payment_date')), 'order': 1, 'currency': p.get('currency_code') or 'INR',
                      'text': _payment_text(p), 'sub': ' · '.join(filter(None, [p.get('method'), p.get('reference_number')])),
                      'owed': 0.0, 'paid': float(p.get('amount') or 0),
                      'url': url('invoices_bp.view_invoice', invoice_id=p['invoice_id'])})
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
        g['files'].append({**file_row(f, url), 'customer_id': str(f.get('customer_id')),
                           'move': url('projects_bp.link_file', attachment_id=f['attachment_id'])})
    latest = sorted(groups.values(), key=lambda g: max(str(x['date'] or '') for x in g['files']), reverse=True)
    return sorted(latest, key=lambda g: g['project'] is None)


def build(org_id, customer: Dict, perms, url: Callable, today: Optional[date] = None) -> Dict:
    """Everything the page shows, for someone with these permissions (permissions.granted(), or a built-in role's
    name): the documents they may read, what's owed if they see invoices (Sales see quotations only, and nothing owed);
    viewers see it all and change nothing."""
    import contacts
    import home_view
    import permissions
    import project_view
    import projects
    import revisions
    from db import db
    from document_service import get_org_profile
    from documents import fy_start_month, load_json, tax_note, tax_suggestion
    from layout import custom_field_defs
    today = today or date.today()
    profile = get_org_profile(org_id)[1]
    sales = permissions.quotations_only(perms)
    can = {'edit': permissions.can('projects.write', perms=perms), 'edit_customer': permissions.can('customers.write', perms=perms),
           'manage': permissions.can('customers.manage', perms=perms), 'sales': sales}
    readable, owed = permissions.doc_types('read', perms), permissions.can('invoices.read', perms=perms)
    customer_id = str(customer['customer_id'])
    sites = [] if customer.get('parent_id') else db.execute_proc('sp_list_customer_sites', (org_id, customer_id)) or []
    family = [customer_id] + [str(s['customer_id']) for s in sites]

    all_docs = [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [] if str(d.get('customer_id')) in family]
    files = [f for cid in family for f in projects.list_attachments(org_id, customer_id=cid)]
    all_docs = [d for d in all_docs if d.get('doc_type') in readable]
    files = [f for f in files if permissions.file_kind_allowed(f.get('kind'), perms)]
    docs = revisions.collapse(all_docs)
    rows = [r for r in project_view.projects_list(org_id, perms, url, today)['projects'] if str(r['customer']['id']) in family]
    rows.sort(key=lambda r: str(r['last_activity'] or ''), reverse=True)
    rows.sort(key=lambda r: r['status'] != 'open')                    # open ones first, latest first

    money = None
    if owed:
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
    tax = tax_note(tax_suggestion('invoice', org, customer))             # 'Karnataka GSTIN, another state, so IGST'
    portal = (db.execute_proc('sp_get_customer_users', (customer_id,)) or [None])[0] if can['manage'] else None
    kinds = {k: v for k, v in projects.DOCUMENT_KINDS.items() if permissions.file_kind_allowed(k, perms)}
    people = contacts.for_customer(org_id, customer)
    values = load_json(customer.get('custom'))
    custom = [{'label': f['label'], 'value': values[f['key']]} for f in custom_field_defs(profile, 'customer') if values.get(f['key'])]
    from payment_terms import describe, usual_days
    own, usual = customer.get('payment_days'), usual_days(profile)
    parent_days = customer.get('parent_payment_days') if customer.get('parent_id') else None
    terms = (describe(own) if own is not None else f"{describe(parent_days)}, as {customer.get('parent_name')}" if parent_days is not None
             else f'{describe(usual)} (your usual terms)' if usual is not None else '')
    return project_view._plain({
        'customer': {
            'id': customer_id, 'name': customer['name'], 'site': customer.get('site') if customer.get('parent_id') else None,
            'parent': {'id': str(customer['parent_id']), 'name': customer.get('parent_name'),
                       'url': url('customers_bp.view_customer', customer_id=customer['parent_id'])} if customer.get('parent_id') else None,
            'tax_id': customer.get('tax_id'), 'email_domains': customer.get('email_domains'),
            'address': [x for x in [customer.get('street_address'),
                                    ', '.join(filter(None, [customer.get('city'), customer.get('state'), customer.get('zip_code')])),
                                    customer.get('country')] if x],
            'archived': bool(customer.get('is_archived')), 'custom': custom, 'tax_note': tax, 'payment_terms': terms,
        },
        'can': can,
        'money': money,
        'projects': rows,
        'documents': project_view.documents(docs, url),
        'statuses': projects.PROJECT_STATUSES,
        'files': file_groups(files, {str(r['id']): r for r in rows}, url),
        'files_count': len(files),
        'upload': {'action': url('projects_bp.upload_file'), 'kinds': kinds} if can['edit'] and not customer.get('is_archived') else None,
        'portal': {'email': portal.get('email') if portal else None, 'login_url': url('customer_portal_bp.login', _external=True),
                   'create': None if portal else url('customers_bp.create_portal_account', customer_id=customer_id)} if can['manage'] else None,
        'people': [{'contact_id': p['contact_id'], 'customer_id': p['customer_id'], 'name': p['name'], 'email': p.get('email'),
                    'phone': p.get('phone'), 'role': p.get('role'), 'gets': p['gets'], 'initials': p['initials'],
                    'at_parent': str(p['customer_id']) != customer_id} for p in people],
        'usually': contacts.USUALLY,
        'sites': [{'id': str(s['customer_id']), 'name': s.get('site') or s['name'], 'tax_id': s.get('tax_id'),
                   'archived': bool(s.get('is_archived')), 'documents': s.get('invoice_count') or 0,
                   'url': url('customers_bp.view_customer', customer_id=s['customer_id'])} for s in sites],
        'links': {
            'new_project': url('projects_bp.create_project', customer_id=customer_id) if can['edit'] and not customer.get('is_archived') else None,
            'new_quote': url('invoices_bp.create_invoice', doc_type='quote', customer_id=customer_id)
            if can['edit'] and not customer.get('is_archived') else None,
            'edit': url('customers_bp.edit_customer', customer_id=customer_id) if can['edit_customer'] else None,
            'add_site': url('customers_bp.create_customer', parent_id=customer_id)
            if can['manage'] and not customer.get('parent_id') and not customer.get('is_archived') else None,
            'archive': url('customers_bp.unarchive_customer' if customer.get('is_archived') else 'customers_bp.archive_customer',
                           customer_id=customer_id) if can['manage'] else None,
            # The statement as a PDF (?fy=, ?currency=), and emailing it (the email form's own addresses)
            'statement_pdf': url('customers_bp.statement_pdf', customer_id=customer_id) if owed else None,
            'statement_email': {'compose': url('api_bp.statement_compose', customer_id=customer_id),
                                'send': url('api_bp.send_statement', customer_id=customer_id)} if owed and permissions.can('emails.send', perms=perms) else None,
        },
    })


# ---------------------------------------------------------------- The list and the form

def _row(c: Dict, parent: Optional[Dict], url: Callable, site_count: int = 0) -> Dict:
    import customers
    if parent:
        name = c.get('site') or c.get('name') or ''
        place = ', '.join(x for x in (c.get('city'), c.get('country')) if x) or '—'
        sub = (f"{c['name']} · " if c.get('site') and c.get('name') != parent.get('name') else '') + place
    else:
        name = customers.label(c)
        sub = ', '.join(x for x in (c.get('city'), c.get('country')) if x) or '—'
        if site_count:
            sub += f" · {site_count} site{'' if site_count == 1 else 's'}"
    if c.get('is_archived'):
        sub += ' · Archived'
    return {'id': str(c['customer_id']), 'url': url('customers_bp.view_customer', customer_id=c['customer_id']),
            'name': name, 'sub': sub, 'tax_id': c.get('tax_id') or '', 'documents': c.get('invoice_count') or 0,
            'archived': bool(c.get('is_archived')), 'site': bool(parent)}


def listing(org_id, query: str, archived: bool, perms, url: Callable) -> Dict:
    """The customers list (frontend/src/islands/customers/): a page of whole groups, so a site stays with its customer;
    the search (customers.search) keeps a matching site's parent and a matching parent's sites."""
    import customers
    import permissions
    from db import db
    from pagination import paginate
    rows = customers.search(db.execute_proc('sp_list_customers', (org_id, archived)) or [], query)
    page = paginate(customers.group(rows))
    q = query or None
    return {
        'title': 'Customers', 'query': query, 'archived': archived, 'any': bool(rows),
        'new': url('customers_bp.create_customer') if permissions.can('customers.write', perms=perms) else None,
        'filters': [{'label': 'Active', 'href': url('customers_bp.list_customers', q=q), 'active': not archived},
                    {'label': 'All', 'href': url('customers_bp.list_customers', include_archived='true', q=q), 'active': archived}],
        'groups': [{'customer': _row(g['customer'], None, url, len(g['sites'])),
                    'sites': [_row(s, g['customer'], url) for s in g['sites']]} for g in page.items],
        'page': page.json(),
    }


FORM_FIELDS = ('name', 'parent_id', 'site_name', 'tax_id', 'email_domains', 'payment_days', 'street_address', 'city',
               'state', 'zip_code', 'country')


def form(org_id, customer: Optional[Dict], defaults: Dict, url: Callable) -> Dict:
    """A customer's form, new (defaults: an "Add site" starts from its parent's details) or to edit. It posts the
    server page's fields to customers_bp.create_customer or edit_customer, which save them."""
    from blueprints.customers_bp import _form_context
    from documents import GST_STATES, load_json
    ctx = _form_context(org_id, customer, defaults)
    c = customer or defaults or {}
    values = {k: '' if c.get(k) is None else str(c.get(k)) for k in FORM_FIELDS}
    values['country'] = values['country'] or 'India'
    if c.get('parent_id') and c.get('parent_payment_days') is not None:
        empty = f"Empty: {c.get('parent_name')}'s {c['parent_payment_days']} days."
    elif ctx['usual_terms']:
        empty = f"Empty: your usual terms ({ctx['usual_terms']})."
    else:
        empty = 'Empty: no due date unless the invoice has one.'
    custom = load_json(customer.get('custom')) if customer else {}
    customer_id = str(customer['customer_id']) if customer else None
    return {
        'title': 'Edit customer' if customer else 'New customer',
        'name': customer.get('name') if customer else None,
        'action': url('customers_bp.edit_customer', customer_id=customer_id) if customer else url('customers_bp.create_customer'),
        'cancel': url('customers_bp.view_customer', customer_id=customer_id) if customer else url('customers_bp.list_customers'),
        'submit': 'Save' if customer else 'Create customer',
        'values': values,
        'site_count': ctx['site_count'],
        'parents': [{'id': str(p['customer_id']), 'name': p['name']} for p in ctx['parents']],
        'domains_help': (f"{c.get('parent_name')} has {c['parent_email_domains']}; add only this site's own domains."
                         if c.get('parent_email_domains') else ''),
        'payment_help': ("How many days after the invoice date they pay; 0 is on receipt. It sets when their invoices "
                         f"count as overdue, and isn't printed. {empty}"),
        'custom': [{'key': f['key'], 'label': f['label'], 'value': custom.get(f['key'], '')} for f in ctx['custom_defs']],
        'gst_states': GST_STATES,                     # a GSTIN's first two digits: the state it's registered in
    }
