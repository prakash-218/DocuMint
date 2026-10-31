"""
The new project page (frontend/src/islands/project/): where the job is, worked out from its documents and
payments, what to do next, and everything else the page shows, as one JSON (GET /api/projects/<id>).

The stage is never set by hand. Quoted, Accepted, Advance, Invoiced and Paid follow from the documents, so
the page shows where each job really is; only Cancelled (and Completed) stay the project's own status.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from documents import balance_of, display_number, get_type
from money import format_money

FOLLOW_UP_AFTER = 14        # days a quotation waits for an answer before the next step is to chase it
STEPS = (('quoted', 'Quoted'), ('accepted', 'Accepted'), ('advance', 'Advance'), ('invoiced', 'Invoiced'), ('paid', 'Paid'))
INVOICE_TYPES = ('invoice', 'export_invoice')
SENT_QUOTE = ('sent', 'accepted', 'declined', 'converted')


def _live(docs: List[Dict], *types) -> List[Dict]:
    return [d for d in docs if d.get('doc_type') in types and d.get('status') != 'revised']


def _day(value) -> str:
    d = to_date(value)
    return f'{d.day} {d:%b}' if d else ''


def _days_since(value, today: date) -> Optional[int]:
    d = to_date(value)
    return (today - d).days if d else None


def _money(amount, docs: List[Dict]) -> str:
    return format_money(amount, (docs[0].get('currency_code') if docs else None) or 'INR', decimals=False)


def facts(docs: List[Dict]) -> Dict:
    """What the documents say about the job (docs: the project's documents, revisions collapsed)."""
    quotes, proformas = _live(docs, 'quote'), _live(docs, 'proforma')
    all_invoices = _live(docs, *INVOICE_TYPES)
    invoices = [d for d in all_invoices if d.get('status') != 'draft']
    sent_proformas = [d for d in proformas if d.get('status') != 'draft']
    accepted_quote = next((d for d in reversed(quotes) if d.get('status') in ('accepted', 'converted')), None)
    sent_quotes = [d for d in quotes if d.get('status') in SENT_QUOTE]
    accepted = bool(accepted_quote or sent_proformas or invoices)
    due = sum(balance_of(d) for d in invoices)
    return {
        'quotes': quotes, 'quote': quotes[-1] if quotes else None, 'sent_quotes': sent_quotes,
        'accepted_quote': accepted_quote, 'accepted': accepted,
        'declined': bool(sent_quotes) and not accepted and all(d.get('status') == 'declined' for d in sent_quotes),
        'proformas': proformas, 'proforma': proformas[-1] if proformas else None, 'sent_proformas': sent_proformas,
        'advance_paid': [d for d in proformas if float(d.get('paid_amount') or 0) > 0],
        # turned into the tax invoice: its advance (if any) moved there with it (advances.carry_over)
        'proforma_invoiced': [d for d in proformas if d.get('status') == 'converted'],
        'all_invoices': all_invoices, 'invoices': invoices, 'due': due,
        'unpaid': [d for d in invoices if balance_of(d) > 0.005],
        'paid': bool(invoices) and due <= 0.005,
    }


def stage(docs: List[Dict], project_status: str = 'open', today: Optional[date] = None) -> Dict:
    """{'steps': [{key, label, state, sub}], 'current': key or None, 'pill': {text, tone}}.
    state: done, now, todo, skipped (no advance taken), late (declined)."""
    today = today or date.today()
    f = facts(docs)
    s = {key: {'key': key, 'label': label, 'state': 'todo', 'sub': ''} for key, label in STEPS}

    if f['sent_quotes'] or f['accepted']:
        s['quoted'].update(state='done', sub=_day((f['sent_quotes'] or [{}])[0].get('issue_date')))
    else:
        s['quoted'].update(state='now', sub='Draft' if f['quotes'] else 'No quotation yet')

    if f['accepted']:
        s['accepted'].update(state='done')
    elif f['declined']:
        s['accepted'].update(state='late', sub='Declined')
    elif f['sent_quotes']:
        waited = _days_since(f['quote'].get('issue_date'), today)
        s['accepted'].update(state='now', sub=f'Waiting · {waited} day{"" if waited == 1 else "s"}' if waited is not None else 'Waiting')

    if f['advance_paid']:
        s['advance'].update(state='done', sub=_money(sum(float(d['paid_amount']) for d in f['advance_paid']), f['advance_paid']))
    elif f['proforma_invoiced']:
        s['advance'].update(state='done', sub='On the invoice')
    elif f['all_invoices'] and not f['proformas']:
        s['advance'].update(state='skipped', sub='No advance')
    elif f['accepted']:
        s['advance'].update(state='now', sub='Requested' if f['sent_proformas'] else 'Draft' if f['proformas'] else 'Not requested')

    if f['invoices']:
        s['invoiced'].update(state='done', sub=_day(f['invoices'][0].get('issue_date')))
    elif s['advance']['state'] in ('done', 'skipped'):
        s['invoiced'].update(state='now', sub='Draft' if f['all_invoices'] else 'To raise')

    if f['paid']:
        s['paid'].update(state='done')
    elif f['invoices']:
        s['paid'].update(state='now', sub=f"{_money(f['due'], f['invoices'])} due")

    steps = list(s.values())
    current = next((x['key'] for x in steps if x['state'] in ('now', 'late')), None)
    if project_status == 'cancelled':
        for x in steps:
            if x['state'] in ('now', 'late'):
                x['state'] = 'todo'
        return {'steps': steps, 'current': None, 'pill': {'text': 'Cancelled', 'tone': 'draft'}}
    return {'steps': steps, 'current': current, 'pill': _pill(current, s, f)}


def stage_label(st: Dict, docs: List[Dict]) -> str:
    """The step a job has reached, as the prototypes' lists tag it: Quoted (sent, or still a draft), Accepted,
    Advance, Invoiced, Paid; New before any quotation."""
    reached = [x['label'] for x in st['steps'] if x['state'] == 'done']
    if st['current'] == 'advance' and any(d.get('doc_type') == 'proforma' and d.get('status') != 'draft' for d in docs):
        return 'Advance'                                  # asked for, waiting
    if reached:
        return reached[-1]
    return 'Quoted' if any(d.get('doc_type') == 'quote' for d in docs) else 'New'


def _pill(current, s, f) -> Dict:
    if current is None:
        return {'text': 'Paid', 'tone': 'done'}
    if current == 'quoted':
        return {'text': 'Quotation draft' if f['quotes'] else 'New', 'tone': 'action'}
    if current == 'accepted':
        return {'text': 'Declined', 'tone': 'late'} if s['accepted']['state'] == 'late' else {'text': 'Waiting for an answer', 'tone': 'wait'}
    if current == 'advance':
        return {'text': 'Waiting for advance', 'tone': 'wait'} if f['sent_proformas'] else {'text': 'Accepted', 'tone': 'action'}
    if current == 'invoiced':
        return {'text': 'To invoice', 'tone': 'action'}
    return {'text': 'Part paid' if any(float(d.get('paid_amount') or 0) > 0 for d in f['unpaid']) else 'Waiting for payment',
            'tone': 'wait'}


# ---------------------------------------------------------------- What to do next

def _link(label, href, primary=False):
    return {'label': label, 'kind': 'link', 'href': href, 'primary': primary}


def _post(label, action, fields=None, primary=False, confirm=None):
    return {'label': label, 'kind': 'post', 'action': action, 'fields': fields or {}, 'primary': primary, 'confirm': confirm}


def _email(label, invoice_id=None, primary=False):
    return {'label': label, 'kind': 'email', 'invoice_id': invoice_id, 'primary': primary}


def _status(label, status, primary=False):
    return {'label': label, 'kind': 'status', 'status': status, 'primary': primary}


def next_step(docs: List[Dict], st: Dict, project: Dict, can: Dict, url: Callable, today: Optional[date] = None) -> Dict:
    """{'tone', 'text', 'sub', 'actions': [...]}: the sentence for where the job is and every action that fits,
    the one that moves it on marked primary. url(endpoint, **values) builds links (flask.url_for)."""
    today = today or date.today()
    f = facts(docs)
    edit, sales = can.get('edit'), can.get('sales')
    no = lambda d: display_number(d) or 'draft'  # noqa: E731
    view = lambda d: url('invoices_bp.view_invoice', invoice_id=d['invoice_id'])  # noqa: E731
    edit_doc = lambda d, kind: _link(f'Edit {kind}', url('invoices_bp.edit_invoice', invoice_id=d['invoice_id']), True)  # noqa: E731
    convert = lambda label, source, target, primary=False: _post(  # noqa: E731
        label, url('invoices_bp.convert', invoice_id=source['invoice_id']), {'target': target}, primary)
    new_doc = lambda label, doc_type, primary=False: _link(  # noqa: E731
        label, url('invoices_bp.create_invoice', doc_type=doc_type, project_id=project['project_id']), primary)

    if project.get('status') == 'cancelled':
        return {'tone': 'draft', 'text': 'This project is cancelled.', 'sub': '',
                'actions': [_status('Reopen it', 'open', True)] if edit else []}

    current, q, pi = st['current'], f['quote'], f['proforma']
    out = {'tone': 'action', 'text': '', 'sub': '', 'actions': []}
    if current == 'quoted':
        if not q:
            out.update(text='No quotation yet.', sub='Start with a quotation, or upload one made earlier under Files.',
                       actions=[new_doc('New quotation', 'quote', True)] + ([] if sales else [new_doc('New invoice', 'invoice')]))
        else:
            out.update(text=f'Quotation {no(q)} is a draft.', sub='Finish it, then send it from here.',
                       actions=[edit_doc(q, 'quotation'), _link('Open', view(q))])
    elif current == 'accepted' and st['steps'][1]['state'] == 'late':
        out.update(tone='late', text=f'Quotation {no(q)} was declined.', sub='Revise it, or cancel the project.',
                   actions=[_post('Revise', url('invoices_bp.revise', invoice_id=q['invoice_id']), primary=True),
                            _status('Cancel the project', 'cancelled')])
    elif current == 'accepted':
        waited = _days_since(q.get('issue_date'), today)
        chase = waited is not None and waited > FOLLOW_UP_AFTER          # long enough without an answer to chase it
        out.update(tone='action' if chase else 'wait', text=f'Quotation {no(q)} sent on {_day(q.get("issue_date"))}.',
                   sub=(f'No answer for {waited} day{"" if waited == 1 else "s"}.' if waited is not None else '')
                   + (' Time to follow it up.' if chase else ''),
                   actions=[_post('Mark accepted', url('invoices_bp.set_status', invoice_id=q['invoice_id']), {'status': 'accepted'}, not chase),
                            _email('Send a follow-up', q['invoice_id'], chase),
                            _post('Mark declined', url('invoices_bp.set_status', invoice_id=q['invoice_id']), {'status': 'declined'},
                                  confirm=f'Mark {no(q)} declined?'),
                            _post('Revise', url('invoices_bp.revise', invoice_id=q['invoice_id']))])
    elif current == 'advance':
        source = f['accepted_quote'] or q
        if not pi:
            out.update(text=f'Quotation {no(source)} accepted.' if source else 'Accepted.',
                       sub='The office raises the proforma and the invoice.' if sales else
                       'Raise a proforma for the advance, or invoice it in full.',
                       actions=[] if sales or not source else [convert('Raise proforma for the advance', source, 'proforma', True),
                                                               convert('Invoice in full instead', source, 'invoice')])
        elif pi.get('status') == 'draft':
            out.update(text=f'Proforma {no(pi)} is a draft.', sub='Finish it, then send it from here.',
                       actions=[edit_doc(pi, 'proforma'), _link('Open', view(pi))])
        else:
            waited = _days_since(pi.get('issue_date'), today)
            out.update(tone='wait', text=f'Proforma {no(pi)} sent on {_day(pi.get("issue_date"))}.',
                       sub="The advance hasn't arrived" + (f' ({waited} day{"" if waited == 1 else "s"}).' if waited else '.'),
                       actions=[_link('Record the advance', view(pi) + '#payment', True), _email('Email a reminder', pi['invoice_id'])])
    elif current == 'invoiced':
        draft = next((d for d in f['all_invoices'] if d.get('status') == 'draft'), None)
        if draft:
            out.update(text=f'Tax invoice {no(draft)} is a draft.', sub='Finish it, then send it from here.',
                       actions=[edit_doc(draft, 'invoice'), _link('Open', view(draft))])
        else:
            source = pi or f['accepted_quote'] or q
            paid = f['advance_paid']
            out.update(text=f"Advance of {_money(sum(float(d['paid_amount']) for d in paid), paid)} received." if paid else 'Ready to invoice.',
                       sub='Raise the tax invoice; the advance comes off it.' if paid else 'Raise the tax invoice.',
                       actions=[] if sales or not source else [convert('Create tax invoice', source, 'invoice', True)])
    elif current == 'paid':
        unpaid = f['unpaid']
        first = unpaid[0] if unpaid else f['invoices'][0]
        out.update(tone='wait', text=(f'Tax invoice {no(first)}: ' if len(unpaid) == 1 else 'Invoices: ')
                   + f"{_money(f['due'], f['invoices'])} due.", sub='',
                   actions=[_link('Record payment', view(first) + '#payment', True), _email('Email a reminder', first['invoice_id'])])
    else:
        out.update(tone='done', text='Paid in full.', sub='Nothing left to do on this job.',
                   actions=[_status('Mark the project completed', 'completed', True)] if project.get('status') == 'open' else [])
    if not edit:
        out['actions'] = []
    return out


# ---------------------------------------------------------------- The rest of the page

def documents(docs: List[Dict], url: Callable) -> List[Dict]:
    out = []
    for d in docs:
        kind = get_type(d.get('doc_type'))
        out.append({'invoice_id': d['invoice_id'], 'doc_type': kind.key, 'kind': kind.label, 'number': display_number(d) or 'Draft',
                    'customer_id': d.get('customer_id'), 'site': d.get('customer_site'), 'project_id': d.get('project_id'),
                    'status': d.get('status') or 'draft', 'issue_date': d.get('issue_date'), 'currency': d.get('currency_code'),
                    'total': float(d.get('total_amount') or 0), 'paid': float(d.get('paid_amount') or 0),
                    'balance': balance_of(d) if kind.takes_payments else None, 'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id']),
                    'pdf': url('invoices_bp.export_pdf', invoice_id=d['invoice_id']),
                    'versions': [{'invoice_id': v['invoice_id'], 'number': display_number(v), 'issue_date': v.get('issue_date'),
                                  'total': float(v.get('total_amount') or 0),
                                  'url': url('invoices_bp.view_invoice', invoice_id=v['invoice_id'])} for v in d.get('versions') or []]})
    return out


def money(docs: List[Dict], files: List[Dict], quoted_only: bool = False) -> List[Dict]:
    """Per currency: quoted, invoiced, received (with advances held on proformas) and due."""
    import projects
    m = projects.project_money(docs, files)
    currencies = list(dict.fromkeys([*m['quoted'], *m['invoiced'], *m['received'], *m['advances']])) or ['INR']
    rows = []
    for c in currencies:
        row = {'currency': c, 'quoted': float(m['quoted'].get(c, 0))}
        if not quoted_only:
            row.update(invoiced=float(m['invoiced'].get(c, 0)), received=float(m['received'].get(c, 0)) + float(m['advances'].get(c, 0)),
                       advance_held=float(m['advances'].get(c, 0)), due=float(m['due'].get(c, 0)))
        rows.append(row)
    return rows


def file_row(f: Dict, url: Callable) -> Dict:
    """A file kept for the customer (attachment), as the project and customer pages list it."""
    import projects
    return {'id': f['attachment_id'], 'name': f.get('file_name'), 'kind': f.get('kind'),
            'kind_label': projects.DOCUMENT_KINDS.get(f.get('kind'), 'File'), 'title': f.get('title'),
            'reference_no': f.get('reference_no'), 'date': f.get('doc_date') or f.get('created_at'),
            'size': projects.human_size(f.get('file_size') or 0), 'from_email': bool(f.get('email_thread_id')),
            'url': url('projects_bp.download_file', attachment_id=f['attachment_id']),
            'delete': url('projects_bp.delete_file', attachment_id=f['attachment_id'])}


SALES_EVENTS = ('project_created', 'project_status', 'file_uploaded', 'note')


def build(org_id, project: Dict, perms, url: Callable, today: Optional[date] = None) -> Dict:
    """Everything the page shows, for someone with these permissions (permissions.granted(), or a built-in role's
    name): the documents they may read (quotations only, as Sales: no money beyond what was quoted), the mail if they
    read it, costings if they see them; viewers see it all but change nothing."""
    import contacts
    import costing
    import permissions
    import projects
    import revisions
    from db import db
    from document_service import get_org_profile
    project_id = project['project_id']
    sales, reads_mail = permissions.quotations_only(perms), permissions.can('emails.read', perms=perms)
    costings = permissions.can('costings.read', perms=perms)
    can = {'edit': permissions.can('projects.write', perms=perms), 'manage': costings, 'read_mail': reads_mail, 'sales': sales}
    readable = permissions.doc_types('read', perms)

    docs = revisions.collapse(projects.project_documents(project_id, org_id))
    files = projects.list_attachments(org_id, project_id=project_id)
    events = db.execute_proc('sp_list_project_events', (project_id, org_id, 100)) or []
    docs = [d for d in docs if d.get('doc_type') in readable]
    files = [f for f in files if permissions.file_kind_allowed(f.get('kind'), perms)]
    if sales:
        events = [e for e in events if e.get('kind') in SALES_EVENTS or '/quotes/' in (e.get('link') or '')]
    messages = db.execute_proc('sp_list_project_messages', (project_id, org_id, 100)) or [] if reads_mail else []

    st = stage(docs, project.get('status') or 'open', today)
    if sales:                                       # how far it went after the quotation isn't theirs to see
        st['steps'] = st['steps'][:2]
    people = contacts.for_project(org_id, project_id)
    found = contacts.project_suggestions(org_id, project, people, get_org_profile(org_id)[1].get('phone') or '') \
        if reads_mail else {'people': [], 'phones': []}
    po = projects.latest_purchase_order(org_id, project_id)
    addable = projects.unassigned_documents(org_id, project['customer_id']) if can['edit'] else []
    if sales:
        addable = [d for d in addable if d.get('doc_type') == 'quote']
    kinds = {k: v for k, v in projects.DOCUMENT_KINDS.items() if permissions.file_kind_allowed(k, perms)}
    return _plain({
        'project': {'id': project_id, 'label': projects.project_label(project), 'title': project['title'],
                    'reference': project.get('reference') or '', 'notes': project.get('notes') or '',
                    'fiscal_year': project.get('fiscal_year'), 'status': project.get('status') or 'open',
                    'created_at': project.get('created_at'),
                    'customer': {'id': project['customer_id'], 'name': project.get('customer_name'),
                                 'site': project.get('customer_site'),
                                 'url': url('customers_bp.view_customer', customer_id=project['customer_id'])},
                    'po': {'number': po.get('reference_no'), 'date': po.get('doc_date'), 'amount': po.get('amount'),
                           'currency': po.get('currency')} if po else None},
        'can': can,
        'stage': st,
        'next': next_step(docs, st, project, can, url, today),
        'money': money(docs, files, quoted_only=sales),
        'documents': documents(docs, url),
        'new_document': {t: url('invoices_bp.create_invoice', doc_type=t, project_id=project_id)
                         for t in (('quote',) if sales else ('quote', 'proforma', 'invoice'))},
        'timeline': timeline(events, messages, reads_mail, (project.get('customer_name'), project.get('customer_site'))),
        'people': [{'contact_id': p['contact_id'], 'customer_id': p['customer_id'], 'name': p['name'], 'email': p.get('email'),
                    'phone': p.get('phone'), 'role': p.get('role'), 'gets': p['project_gets'], 'usually': p['gets'],
                    'initials': p['initials'], 'at_parent': p['customer_id'] != project['customer_id']} for p in people],
        'found': {'people': [{'name': p['name'], 'email': p['email'], 'phone': p.get('phone'), 'seen': p['seen']}
                             for p in found['people']],
                  'phones': [{'contact_id': p['contact_id'], 'name': p['name'], 'phone': p['phone'], 'value': p['value'],
                              'replaces': p.get('replaces')} for p in found['phones']]},
        'gets': contacts.GETS, 'usually': contacts.USUALLY,
        'files': [file_row(f, url) for f in files],
        'upload': {'action': url('projects_bp.upload_file'), 'kinds': kinds} if can['edit'] else None,
        'costings': [{'id': k['costing_id'], 'title': k.get('title') or 'Costing', 'currency': k.get('currency'),
                      'cost': float(k.get('total_cost') or 0), 'price': float(k.get('total_price') or 0),
                      'profit_on_cost': k.get('profit_on_cost'), 'quote_number': k.get('quote_number'),
                      'url': url('costings_bp.edit', costing_id=k['costing_id'])}
                     for k in costing.list_for(org_id, project_id)] if costings else None,
        'addable': [{'invoice_id': d['invoice_id'], 'number': display_number(d), 'kind': get_type(d.get('doc_type')).label,
                     'total': float(d.get('total_amount') or 0), 'currency': d.get('currency_code') or 'INR'}
                    for d in revisions.collapse(addable) if d.get('status') != 'revised'],
        'links': {'documents': url('projects_bp.project_document', project_id=project_id) if can['edit'] else None,
                  'delete': url('projects_bp.delete_project', project_id=project_id) if permissions.can('projects.delete', perms=perms) else None,
                  'new_costing': url('costings_bp.create') if permissions.can('costings.write', perms=perms) else None,
                  'rates': url('costings_bp.rates') if costings else None},
        'years': sorted(set(projects.recent_fiscal_years(org_id)) | {project.get('fiscal_year')} - {None}, reverse=True),
        'statuses': projects.PROJECT_STATUSES,
    })


BOARD = (('quoted', 'Quoting'), ('accepted', 'Waiting for an answer'), ('advance', 'Advance'),
         ('invoiced', 'To invoice'), ('paid', 'Waiting for payment'))


def projects_list(org_id, perms, url: Callable, today: Optional[date] = None) -> Dict:
    """Every project with where it is and what's next, for the projects list and board: two queries (all the
    projects, all the documents) and the same stage logic as the project page."""
    import permissions
    import projects
    import revisions
    from db import db
    sales, readable = permissions.quotations_only(perms), permissions.doc_types('read', perms)
    can = {'edit': permissions.can('projects.write', perms=perms), 'sales': sales}
    by_project: Dict[str, List[Dict]] = {}
    for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or []:
        if d.get('project_id') and d.get('doc_type') in readable:
            by_project.setdefault(str(d['project_id']), []).append(d)
    order = {'quote': 0, 'proforma': 1, 'invoice': 2, 'export_invoice': 2}
    rows = []
    for p in projects.list_projects(org_id):
        docs = revisions.collapse(sorted(by_project.get(str(p['project_id']), []),
                                         key=lambda d: (order.get(d.get('doc_type'), 3), str(d.get('issue_date') or ''))))
        st = stage(docs, p.get('status') or 'open', today)
        nxt = next_step(docs, st, p, can, url, today)
        f = facts(docs)
        currency = (docs[0].get('currency_code') if docs else None) or 'INR'
        step = next((s for s in st['steps'] if s['key'] == st['current']), None)
        rows.append({
            'id': p['project_id'], 'label': projects.project_label(p), 'title': p['title'], 'reference': p.get('reference') or '',
            'url': url('projects_bp.view_project', project_id=p['project_id']),
            'customer': {'id': p['customer_id'], 'name': p.get('customer_name'), 'site': p.get('customer_site')},
            'fiscal_year': p.get('fiscal_year'), 'status': p.get('status') or 'open',
            'stage': st['current'] if not (sales and st['current'] not in ('quoted', 'accepted', None)) else 'accepted',
            'pill': st['pill'], 'sub': (step or {}).get('sub') or '',
            'stage_label': stage_label(st, docs),
            'next': nxt['text'], 'action': next((a['label'] for a in nxt['actions'] if a['primary']), None),
            'tone': nxt['tone'], 'currency': currency,
            'quoted': float((f['quote'] or {}).get('total_amount') or 0),
            'due': None if sales else f['due'],
            'advance': None if sales else sum(float(d.get('total_amount') or 0) for d in f['sent_proformas']
                                              if float(d.get('paid_amount') or 0) <= 0 and d.get('status') == 'sent'),
            'last_activity': max(filter(None, [str(p.get('updated_at') or ''), str(p.get('last_issue_date') or '')]), default=None),
            'numbers': [x for d in docs for x in [d.get('doc_number'), *[v.get('doc_number') for v in d.get('versions') or []]] if x],
        })
    years = sorted({r['fiscal_year'] for r in rows if r['fiscal_year']}, reverse=True)
    customers = sorted({(r['customer']['id'], r['customer']['name']) for r in rows}, key=lambda c: (c[1] or '').lower())
    return _plain({'can': can, 'projects': rows, 'board': [{'key': k, 'label': label} for k, label in BOARD],
                   'years': years, 'customers': [{'id': i, 'name': n} for i, n in customers],
                   'new_project': url('projects_bp.create_project') if can['edit'] else None})


def _plain(value):
    """Dates as ISO strings ('2026-10-24', '2026-10-24T09:30:00+00:00') and amounts as numbers, for the JSON."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


EMAIL_EVENTS = ('email_received', 'email_sent')


def timeline(events: List[Dict], messages: List[Dict], reads_mail: bool, customer_names=()) -> List[Dict]:
    """Activity, notes and (for those who read mail) the emails themselves, newest first. The emails stand
    in for the 'email received/sent' events when they're shown; an event's body that only names the
    project's customer (documents' events carry it) is left out."""
    items, names = [], {n for n in customer_names if n}
    for e in events:
        if reads_mail and e.get('kind') in EMAIL_EVENTS:
            continue
        note = e.get('kind') == 'note'
        body = None if note or e.get('body') in names else e.get('body')
        items.append({'id': f"e-{e['event_id']}", 'type': 'note' if note else 'event', 'kind': e.get('kind'),
                      'title': e.get('body') if note else e.get('title'), 'body': body,
                      'when': e.get('created_at'), 'who': (e.get('actor_email') or '').split('@')[0] or None, 'link': e.get('link')})
    for m in messages if reads_mail else []:
        out = m.get('direction') == 'out'
        items.append({'id': f"m-{m['message_id']}", 'type': 'email', 'kind': 'email_sent' if out else 'email_received',
                      'title': m.get('subject') or m.get('thread_subject') or '(no subject)',
                      'body': ' '.join((m.get('snippet') or '').split())[:240] or None, 'when': m.get('sent_at'),
                      'who': (f"to {m.get('to_addresses')}" if out else (m.get('from_name') or m.get('from_address'))),
                      'thread_id': m.get('thread_id'), 'files': m.get('file_count') or 0, 'direction': m.get('direction'),
                      'link': f"/emails/{m['thread_id']}"})
    items.sort(key=lambda i: str(i['when'] or ''), reverse=True)
    return items


def new_project(org_id, customer_id: Optional[str], url: Callable) -> Dict:
    """The new project form (frontend/src/islands/project/NewProject.tsx); it posts to projects_bp.create_project."""
    import projects
    from db import db
    from editor_page import _customers
    return {'title': 'New project', 'action': url('projects_bp.create_project'), 'cancel': url('projects_bp.list_projects'),
            'customers': _customers(db.execute_proc('sp_list_customers', (org_id, False)) or []),
            'customer_id': customer_id or '', 'years': projects.recent_fiscal_years(org_id)}
