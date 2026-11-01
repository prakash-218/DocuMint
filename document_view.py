"""
A document's page (document_page.py, drawn by the React app): what to do next with a quotation, proforma, tax
invoice, purchase order or credit / debit note, from its type and status, with every action that fits; the one that
moves it on is marked primary.
Actions are links, forms to the existing routes (invoices_bp), the change dialog, or the email form.
"""

import math
from datetime import date
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from documents import display_number, get_type, load_json
from money import format_money
from payment_terms import due_on

FOLLOW_UP_AFTER = 14


def _post(label, action, fields=None, primary=False, confirm=None):
    return {'label': label, 'kind': 'post', 'action': action, 'fields': fields or {}, 'primary': primary, 'confirm': confirm}


def _link(label, href, primary=False):
    return {'label': label, 'kind': 'link', 'href': href, 'primary': primary}


def _dialog(label, dialog, primary=False):
    return {'label': label, 'kind': 'dialog', 'dialog': dialog, 'primary': primary}


def _email(label, invoice_id, primary=False):
    return {'label': label, 'kind': 'email', 'invoice_id': invoice_id, 'primary': primary}


def _day(value) -> str:
    d = to_date(value)
    return f'{d.day} {d:%b}' if d else ''


STEPS = {'quote': [('written', 'Written'), ('sent', 'Sent'), ('answer', 'Accepted'), ('forward', 'Taken forward')],
         'proforma': [('written', 'Written'), ('sent', 'Sent'), ('advance', 'Advance'), ('forward', 'Tax invoice')],
         'invoice': [('written', 'Written'), ('sent', 'Finalized'), ('paid', 'Paid')],
         'purchase_order': [('written', 'Written'), ('sent', 'Sent'), ('confirmed', 'Confirmed'), ('received', 'Received')],
         'note': [('written', 'Written'), ('sent', 'Issued')]}


def steps(doc: Dict, summary: Dict, advance_received: float = 0, today: Optional[date] = None) -> List[Dict]:
    """Where this document is, as the project page's tracker draws it: [{key, label, state, sub}], state done, now
    (what it waits for), todo, skipped or late (declined)."""
    today = today or date.today()
    kind = get_type(doc.get('doc_type'))
    status = doc.get('status') or 'draft'
    currency = doc.get('currency_code') or 'INR'
    money = lambda v: format_money(v, currency, decimals=False)  # noqa: E731
    key = 'note' if kind.adjusts else kind.key if kind.key in STEPS else 'invoice'
    s = {k: {'key': k, 'label': label, 'state': 'todo', 'sub': ''} for k, label in STEPS[key]}
    if status == 'draft':
        s['written'].update(state='now', sub='Draft')
        return list(s.values())
    s['written']['state'] = 'done'
    s['sent'].update(state='done', sub=_day(doc.get('issue_date')))
    later = list(s)[2:]
    if key == 'note':
        if status == 'cancelled':
            s['sent'].update(state='late', sub='Cancelled')
    elif status == 'revised':
        s[later[0]].update(state='skipped', sub='Revised')
    elif key == 'purchase_order':
        if status == 'cancelled':
            s['confirmed'].update(state='late', sub='Cancelled')
        else:
            s['confirmed'].update(state='done' if status in ('confirmed', 'received') else 'now',
                                  sub='' if status in ('confirmed', 'received') else 'Waiting for the supplier')
            s['received'].update(state='done' if status == 'received' else 'now' if status == 'confirmed' else 'todo',
                                 sub=('Expected: ' + (load_json(doc.get('details')).get('delivery') or '')).rstrip(': ')
                                 if status == 'confirmed' else '')
    elif key == 'quote':
        if status == 'sent':
            issued = to_date(doc.get('issue_date'))
            waited = (today - issued).days if issued else None
            s['answer'].update(state='now', sub=f'Waiting · {waited} day{"" if waited == 1 else "s"}' if waited is not None else 'Waiting')
        elif status == 'declined':
            s['answer'].update(state='late', sub='Declined')
        else:
            s['answer']['state'] = 'done'
            s['forward'].update(state='done' if status == 'converted' else 'now', sub='' if status == 'converted' else 'Proforma or invoice')
    elif key == 'proforma':
        due = (summary.get('advance') or {}).get('amount') or summary.get('total') or 0
        if advance_received:
            s['advance'].update(state='done', sub=money(advance_received))
        elif status == 'converted':
            s['advance'].update(state='skipped', sub='No advance')
        else:
            s['advance'].update(state='now', sub=f'{money(due)} asked')
        s['forward'].update(state='done' if status == 'converted' else 'now' if advance_received else 'todo',
                            sub='To raise' if advance_received and status != 'converted' else '')
    else:
        balance, paid = summary.get('balance') or 0, summary.get('paid') or 0
        if status == 'paid' or balance <= 0.005:
            s['paid']['state'] = 'done'
        else:
            s['paid'].update(state='now', sub=f'{money(paid)} of {money(summary.get("total") or 0)}' if paid else f'{money(balance)} due')
    return list(s.values())


def next_step(doc: Dict, summary: Dict, advance_received: float, open_advances: List[Dict], can: Dict, url: Callable,
              convert_defaults: Optional[Dict] = None, can_email: bool = False, today: Optional[date] = None,
              usual_days: Optional[int] = None, received: Optional[Dict] = None) -> Dict:
    """{'tone', 'text', 'sub', 'actions'} for one document. can: {'edit', 'sales'}; can_email: it's in a project
    (the email form goes by the project); usual_days: the organization's usual payment terms (payment_terms.py)."""
    today = today or date.today()
    kind = get_type(doc.get('doc_type'))
    status = doc.get('status') or 'draft'
    number = display_number(doc)
    currency = doc.get('currency_code') or 'INR'
    money = lambda v: format_money(v, currency, decimals=False)  # noqa: E731
    doc_id = doc['invoice_id']
    sent_on = _day(doc.get('issue_date'))
    edit, sales = can.get('edit'), can.get('sales')
    email = (lambda label, primary=False: [_email(label, doc_id, primary)] if can_email else [])  # noqa: E731
    convert = lambda label, target, primary=False: _post(  # noqa: E731
        label, url('invoices_bp.convert', invoice_id=doc_id),
        {'target': target, **({'template_id': convert_defaults[target]} if (convert_defaults or {}).get(target) else {})}, primary)
    status_to = lambda label, value, primary=False, confirm=None: _post(  # noqa: E731
        label, url('invoices_bp.set_status', invoice_id=doc_id), {'status': value}, primary, confirm)
    out = {'tone': 'action', 'text': '', 'sub': '', 'actions': []}

    if status == 'draft':
        finish = {'sent': 'Mark as sent', 'issued': 'Issue'}.get(kind.sent_status, 'Finalize')
        out.update(text=f'{kind.label} {number} is a draft.',
                   actions=[_post(finish, url('invoices_bp.finalize_invoice', invoice_id=doc_id), primary=True,
                                  confirm=f'{finish} {number}? It can\'t be edited afterwards.'),
                            _link('Edit', url('invoices_bp.edit_invoice', invoice_id=doc_id))])
    elif status == 'revised':
        out.update(tone='draft', text=f'{number} was revised.')
    elif kind.adjusts:                                    # a credit or debit note, against its invoice
        against = doc.get('source_number') or 'its invoice'
        invoice = ([_link(f'Open {against}', url('invoices_bp.view_invoice', invoice_id=doc['source_invoice_id']))]
                   if doc.get('source_invoice_id') else [])
        if status == 'cancelled':
            out.update(tone='draft', text='Cancelled.', sub=f'Against {against}.',
                       actions=[status_to('Issue it again', 'issued'), *invoice])
        else:
            out.update(tone='done', text=f'Issued on {sent_on}, against {against}.' if sent_on else f'Issued, against {against}.',
                       actions=[*invoice, *email('Email the customer'),
                                status_to(f'Cancel the {kind.short.lower()}', 'cancelled',
                                          confirm=f'Cancel {number}? It stops counting on {against}.')])
    elif kind.purchase:
        supplier = doc.get('customer_name') or 'the supplier'
        lines = (received or {}).get('lines') or []
        part = (received or {}).get('state') == 'part'
        so_far = f"{received['arrived']} of {len(lines)} line{'' if len(lines) == 1 else 's'} arrived in full." if part else ''
        record = _link('Record what arrived', '#receiving')
        if status == 'sent':
            out.update(tone='wait', text=f'Sent to {supplier}' + (f' on {sent_on}.' if sent_on else '.'),
                       actions=[status_to('Mark confirmed', 'confirmed', True), record, *email('Email the supplier'),
                                status_to('Cancel the order', 'cancelled', confirm=f'Cancel {number}?')])
        elif status == 'confirmed':
            delivery = load_json(doc.get('details')).get('delivery')
            out.update(tone='wait', text=so_far or f'{supplier} confirmed it.',
                       sub='The rest is still to come.' if part else f'Delivery: {delivery}.' if delivery else '',
                       actions=[{**record, 'primary': True}, *email('Email the supplier'),
                                status_to('Mark it all received', 'received'),
                                status_to('Cancel the order', 'cancelled', confirm=f'Cancel {number}?')])
        elif status == 'received':
            out.update(tone='done', text='Received.', sub='Everything on it has arrived.',
                       actions=[] if (received or {}).get('state') == 'all' else [status_to('Undo: not received yet', 'confirmed')])
        else:                                             # cancelled
            out.update(tone='draft', text='Cancelled.', sub='', actions=[status_to('Undo: back to sent', 'sent')])
    elif kind.key == 'quote':
        if status == 'sent':
            waited = (today - to_date(doc['issue_date'])).days if to_date(doc.get('issue_date')) else None
            chase = waited is not None and waited > FOLLOW_UP_AFTER
            out.update(tone='action' if chase else 'wait', text=f'Sent on {sent_on}.' if sent_on else 'Sent.',
                       sub=f'No answer for {waited} day{"" if waited == 1 else "s"}.' if waited is not None else '',
                       actions=[status_to('Mark accepted', 'accepted', not chase), *email('Send a follow-up', chase),
                                status_to('Mark declined', 'declined', confirm=f'Mark {number} declined?'),
                                _dialog('Revise', 'change-dialog')])
        elif status == 'accepted':
            out.update(text='Accepted.',
                       actions=([] if sales else [convert('Raise proforma for the advance', 'proforma', True),
                                                  convert('Invoice in full instead', 'invoice')])
                       + [status_to('Undo: not answered yet', 'sent')])
        elif status == 'declined':
            out.update(tone='late', text='Declined.',
                       actions=[_dialog('Revise', 'change-dialog', True), status_to('Undo: not answered yet', 'sent')])
        else:                                             # converted
            out.update(tone='done', text='Accepted and taken forward.')
    elif kind.key == 'proforma':
        due = (summary.get('advance') or {}).get('amount') or summary.get('total') or 0
        if status == 'converted':
            out.update(tone='done', text='Turned into the tax invoice.',
                       sub=f'Its advance of {money(advance_received)} went with it.' if advance_received else '')
        elif advance_received:
            out.update(text=f'Advance of {money(advance_received)} received.',
                       actions=[] if sales else [convert('Create tax invoice', 'invoice', True)])
        else:
            out.update(tone='wait', text=f'Sent on {sent_on}. The advance of {money(due)} hasn\'t arrived.' if sent_on
                       else f"The advance of {money(due)} hasn't arrived.", sub='',
                       actions=[_link('Record the advance', '#payment', True), *email('Email a reminder'),
                                *([] if sales else [convert('Create tax invoice anyway', 'invoice')]),
                                _dialog('Revise', 'change-dialog')])
    else:                                                 # tax / export invoice
        balance = summary.get('balance') or 0
        back = summary.get('in_favour') or 0
        if back > 0.005:
            out.update(tone='action', text=f'{money(back)} to refund.', sub='')
        elif status == 'paid' or balance <= 0.005:
            credited_only = (summary.get('credited') or 0) > 0.005 and (summary.get('paid') or 0) <= 0.005
            out.update(tone='done', text='Credited in full.' if credited_only else 'Paid in full.', sub='')
        else:
            paid = summary.get('paid') or 0
            due = due_on(doc, usual_days)
            late = (today - due).days if due else 0
            when = (f'{late} day{"" if late == 1 else "s"} late: it was due on {_day(due)}. ' if late > 0
                    else 'Due today. ' if due == today else f'Due on {_day(due)}. ' if due else '')
            out.update(tone='late' if late > 0 else 'wait', text=f'{money(balance)} due.',
                       sub=when + (f'{money(paid)} received so far. ' if paid else '') + (f'Sent on {sent_on}.' if sent_on else ''),
                       actions=([_link(f'Apply the advance on {open_advances[0].get("proforma_number")}', '#advances', True)]
                                if open_advances else [])
                       + [_link('Record payment', '#payment', not open_advances), *email('Email a reminder')])
    if not edit:
        out['actions'] = []
    return out


def pill(doc: Dict, summary: Dict, advance_received: float = 0) -> Dict:
    """The document's state in a word or two, in its tone (as the prototype's pills): Sent, Accepted, Unpaid, Paid..."""
    kind = get_type(doc.get('doc_type'))
    status = doc.get('status') or 'draft'
    if status == 'draft':
        return {'text': 'Draft', 'tone': 'draft'}
    if status == 'revised':
        return {'text': 'Revised', 'tone': 'draft'}
    if kind.adjusts:
        return {'text': 'Cancelled', 'tone': 'draft'} if status == 'cancelled' else {'text': 'Issued', 'tone': 'done'}
    if kind.purchase:
        return {'sent': {'text': 'Sent', 'tone': 'wait'}, 'confirmed': {'text': 'Confirmed', 'tone': 'wait'},
                'received': {'text': 'Received', 'tone': 'done'}, 'cancelled': {'text': 'Cancelled', 'tone': 'draft'}
                }.get(status, {'text': 'Sent', 'tone': 'wait'})
    if kind.key == 'quote':
        return {'sent': {'text': 'Sent', 'tone': 'wait'}, 'accepted': {'text': 'Accepted', 'tone': 'done'},
                'declined': {'text': 'Declined', 'tone': 'late'}}.get(status, {'text': 'Accepted', 'tone': 'done'})
    if kind.key == 'proforma':
        if status == 'converted':
            return {'text': 'Invoiced', 'tone': 'done'}
        return {'text': 'Advance received', 'tone': 'done'} if advance_received else {'text': 'Advance asked', 'tone': 'wait'}
    if (summary.get('in_favour') or 0) > 0.005:
        return {'text': 'To refund', 'tone': 'action'}
    if status == 'paid' or (summary.get('balance') or 0) <= 0.005:
        return {'text': 'Paid', 'tone': 'done'}
    return {'text': 'Part paid', 'tone': 'wait'} if (summary.get('paid') or 0) > 0 else {'text': 'Unpaid', 'tone': 'wait'}


def money_strip(doc: Dict, summary: Dict, payments: List[Dict], advance_received: float = 0,
                notes: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
    """The four amounts under the next step: for an invoice its total, the advance taken off it, what came in since,
    and what's due; for a proforma its total, the advance asked, received and still to come. None for a quotation, a
    purchase order or a credit / debit note. notes: an invoice's credit and debit notes (only issued ones count); with
    some, the four are its total, the notes, what was received (its advance too) and what's due, or to refund."""
    kind = get_type(doc.get('doc_type'))
    total = float(summary.get('total') or 0)
    if kind.key == 'quote' or kind.purchase or kind.adjusts or (doc.get('status') or 'draft') == 'draft':
        return None
    if kind.key == 'proforma':
        advance = summary.get('advance') or {}
        asked = float(advance.get('amount') or total)
        return [{'label': 'Proforma total', 'value': total, 'cap': 'incl. GST' if summary.get('tax_lines') else ''},
                {'label': 'Advance asked', 'value': asked, 'cap': f"{advance['percent']:g}% of the order" if advance.get('percent') else 'The whole proforma'},
                {'label': 'Advance received', 'value': advance_received, 'cap': 'Nothing yet' if not advance_received else ''},
                {'label': 'Still to come', 'value': max(0.0, asked - advance_received), 'cap': '' if asked - advance_received > 0.005 else 'All in',
                 'late': asked - advance_received > 0.005}]
    advance_in = sum(float(p.get('amount') or 0) for p in payments if p.get('advance_number'))
    since = sum(float(p.get('amount') or 0) for p in payments if not p.get('advance_number'))
    balance = float(summary.get('balance') or 0)
    advance_of = next((p.get('advance_number') for p in payments if p.get('advance_number')), None)
    issued = [n for n in notes or [] if n.get('status') == 'issued']
    if issued:
        credit = [n for n in issued if n.get('doc_type') == 'credit_note']
        debit = [n for n in issued if n.get('doc_type') == 'debit_note']
        net = sum(float(n.get('total_amount') or 0) for n in debit) - sum(float(n.get('total_amount') or 0) for n in credit)
        back = float(summary.get('in_favour') or 0)
        return [{'label': 'Invoice total', 'value': total, 'cap': 'incl. GST' if summary.get('tax_lines') else ''},
                {'label': 'Credit notes' if not debit else 'Debit notes' if not credit else 'Credit and debit notes',
                 'value': net, 'cap': ', '.join(display_number(n) for n in issued)},
                {'label': 'Received', 'value': since + advance_in,
                 'cap': f'Incl. advance on proforma {advance_of}' if advance_of else '' if since else 'Nothing yet'},
                {'label': 'To refund', 'value': back, 'cap': ''} if back > 0.005 else
                {'label': 'Due', 'value': balance, 'cap': 'Nothing due' if balance <= 0.005 else '', 'late': balance > 0.005}]
    return [{'label': 'Invoice total', 'value': total, 'cap': 'incl. GST' if summary.get('tax_lines') else ''},
            {'label': 'Less advance', 'value': -advance_in, 'cap': f'On proforma {advance_of}' if advance_of else 'No advance'},
            {'label': 'Received since', 'value': since, 'cap': '' if since else 'Nothing yet'},
            {'label': 'Due', 'value': balance, 'cap': 'Nothing due' if balance <= 0.005 else '', 'late': balance > 0.005}]


def made_from(here_id, project_docs: List[Dict]) -> List[Dict]:
    """The documents made from a quotation (from any of its versions): its proformas, and the tax invoices made from it
    or from them. When it's the project's only quotation, that's every other document in the project: documents made
    before converting kept the link (source_invoice_id), but imported or uploaded ones don't have it.
    project_docs: the project's, revisions collapsed (each with its earlier 'versions')."""
    every = [x for d in project_docs for x in (d, *(d.get('versions') or []))]
    ids = {str(x['invoice_id']) for d in project_docs for x in (d, *(d.get('versions') or []))
           if any(str(y['invoice_id']) == str(here_id) for y in (d, *(d.get('versions') or [])))} or {str(here_id)}
    quotes = [d for d in project_docs if d.get('doc_type') == 'quote']
    if len(quotes) == 1 and str(quotes[0]['invoice_id']) in ids:
        return [d for d in every if d.get('doc_type') != 'quote']
    made, grew = [], True
    while grew:
        grew = False
        for d in every:
            if str(d['invoice_id']) not in ids and str(d.get('source_invoice_id') or '') in ids and d.get('doc_type') != 'quote':
                ids.add(str(d['invoice_id']))
                made.append(d)
                grew = True
    return made


def quote_strip(doc: Dict, summary: Dict, invoiced: List[Dict]) -> Optional[List[Dict]]:
    """Under an accepted quotation's next step: what it quoted, how much of it is invoiced ("Invoiced ₹X of ₹Y") and
    what's still to invoice, all before GST, since a quotation usually states GST in its terms rather than adding it.
    invoiced: [{'taxable', 'currency', 'note'}] for the tax invoices made from it (made_from), drafts left out, and their
    issued credit notes (taxable negative) and debit notes (note: True)."""
    if (doc.get('status') or 'draft') not in ('accepted', 'converted'):
        return None
    currency = doc.get('currency_code') or 'INR'
    money = lambda v: format_money(v, currency, decimals=False)  # noqa: E731
    quoted = float(summary['taxable'] if summary.get('taxable') is not None else summary.get('total') or 0)
    mine = [i for i in invoiced if (i.get('currency') or 'INR') == currency]
    done = sum(float(i['taxable'] or 0) for i in mine)
    left = quoted - done
    bills = len([i for i in mine if not i.get('note')])
    on = f'on {bills} tax invoice{"" if bills == 1 else "s"}'
    return [{'label': 'Quoted', 'value': quoted, 'cap': 'Before GST'},
            {'label': 'Invoiced', 'value': done,
             # rounded down: 99.6% isn't "100%" while something's still to invoice
             'cap': (f'{math.floor(done / quoted * 100 + 1e-9)}% of it, {on}' if quoted else on.capitalize()) if mine else 'Nothing yet'},
            {'label': 'Still to invoice', 'value': max(0.0, left),
             'cap': f'{money(-left)} more than quoted' if left < -0.5 else 'All invoiced' if left <= 0.5 else 'Before GST'}]


def chain(project_docs: List[Dict], here_id, url: Callable) -> List[Dict]:
    """The project's documents, quotation to tax invoice, for the side of a document's page."""
    from documents import balance_of, credit_of
    order = {'quote': 0, 'proforma': 1, 'invoice': 2, 'export_invoice': 2, 'credit_note': 3, 'debit_note': 3}
    out = []
    sales = [d for d in project_docs if not get_type(d.get('doc_type')).purchase]
    for d in sorted(sales, key=lambda d: (order.get(d.get('doc_type'), 3), str(d.get('issue_date') or ''))):
        kind = get_type(d.get('doc_type'))
        paid = float(d.get('paid_amount') or 0)
        summary = {'balance': balance_of(d) if kind.takes_payments else 0, 'paid': paid,
                   'in_favour': credit_of(d) if kind.takes_payments else 0}
        out.append({'kind': kind.label, 'number': display_number(d), 'pill': pill(d, summary, paid if kind.key == 'proforma' else 0),
                    'total': float(d.get('total_amount') or 0) * (-1 if kind.adjusts < 0 else 1), 'currency': d.get('currency_code') or 'INR',
                    'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id']),
                    'here': str(d['invoice_id']) == str(here_id) or any(str(v.get('invoice_id')) == str(here_id) for v in d.get('versions') or []),
                    'paid': kind.takes_payments and summary['balance'] <= 0.005 or (kind.key == 'proforma' and paid > 0)})
    return out


def who_gets_it(doc: Dict, people: List[Dict]) -> List[Dict]:
    """The project's contacts who get this kind of document: quotations go to those who get everything, proformas
    and invoices also to those who get the billing."""
    if get_type(doc.get('doc_type')).purchase:            # people are the supplier's contacts (contacts.for_supplier)
        return list(people)
    wanted = ('all',) if doc.get('doc_type') == 'quote' else ('all', 'billing')
    return [p for p in people if (p.get('project_gets') or p.get('gets')) in wanted]


EVENT_ICONS = {'payment': ('indian-rupee', 't-pay'), 'email_sent': ('send', 't-email'), 'email_received': ('mail', 't-email'),
               'note': ('sticky-note', 't-note')}


def activity(events: List[Dict], doc_id, customer_names=()) -> List[Dict]:
    """What happened to this document (its events in the project), newest first. A body that only names the
    customer (the page says who already) is left out."""
    mine = [e for e in events if str(doc_id) in (e.get('link') or '')]
    names = {(n or '').strip().lower() for n in customer_names if n}
    return [{'title': e.get('title'), 'body': None if (e.get('body') or '').strip().lower() in names else e.get('body'), 'when': e.get('created_at'),
             'who': (e.get('actor_email') or '').split('@')[0] or None,
             'icon': EVENT_ICONS.get(e.get('kind'), ('file-text', 't-doc'))[0],
             'tone': EVENT_ICONS.get(e.get('kind'), ('file-text', 't-doc'))[1]} for e in mine]
