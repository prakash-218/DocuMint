"""The new document page's logic: where a quotation, proforma or invoice is, and what to do next with it."""

from datetime import date

import document_view as D

TODAY = date(2026, 10, 20)
EDITOR = {'edit': True, 'sales': False}


def doc(doc_type, status, issue='2026-10-14', number='Q/001'):
    return {'invoice_id': 'D-1', 'doc_type': doc_type, 'status': status, 'issue_date': issue, 'doc_number': number,
            'currency_code': 'INR'}


def url(endpoint, **values):
    return f"/{endpoint}" + ''.join(f'/{k}={v}' for k, v in sorted(values.items()))


def look(d, summary=None, advance=0, open_advances=(), can=EDITOR, email=True, defaults=None):
    return D.next_step(d, summary or {'total': 10000}, advance, list(open_advances), can, url, defaults, email, TODAY)


def labels(nxt):
    return [a['label'] + ('*' if a['primary'] else '') for a in nxt['actions']]


def states(d, summary=None, advance=0):
    return [(s['key'], s['state'], s['sub']) for s in D.steps(d, summary or {'total': 10000}, advance, TODAY)]


def test_a_draft_is_finalized_or_edited():
    nxt = look(doc('quote', 'draft'))
    assert nxt['text'] == 'Quotation Q/001 is a draft.'
    assert labels(nxt) == ['Mark as sent*', 'Edit']
    assert nxt['actions'][0]['action'] == '/invoices_bp.finalize_invoice/invoice_id=D-1'
    assert labels(look(doc('invoice', 'draft', number='058'))) == ['Finalize*', 'Edit']
    assert states(doc('quote', 'draft'))[0] == ('written', 'now', 'Draft')


def test_a_sent_quotation_waits_then_is_followed_up():
    fresh = look(doc('quote', 'sent', issue='2026-10-14'))
    assert fresh['tone'] == 'wait' and fresh['sub'] == 'No answer for 6 days.'
    assert labels(fresh) == ['Mark accepted*', 'Send a follow-up', 'Mark declined', 'Make a revision']
    assert fresh['actions'][3] == {'label': 'Make a revision', 'kind': 'dialog', 'dialog': 'change-dialog', 'primary': False}

    old = look(doc('quote', 'sent', issue='2026-09-30'))
    assert old['tone'] == 'action' and old['sub'] == 'No answer for 20 days. Time to follow it up.'
    assert labels(old) == ['Mark accepted', 'Send a follow-up*', 'Mark declined', 'Make a revision']
    assert old['actions'][1]['kind'] == 'email' and old['actions'][1]['invoice_id'] == 'D-1'

    assert labels(look(doc('quote', 'sent'), email=False)) == ['Mark accepted*', 'Mark declined', 'Make a revision']  # no project
    assert states(doc('quote', 'sent'))[1:3] == [('sent', 'done', '14 Oct'), ('answer', 'now', 'Waiting · 6 days')]


def test_an_accepted_quotation_is_taken_forward():
    nxt = look(doc('quote', 'accepted'), defaults={'proforma': 'T-PRO', 'invoice': 'T-INV'})
    assert labels(nxt) == ['Raise proforma for the advance*', 'Invoice in full instead', 'Undo: not answered yet']
    assert nxt['actions'][0]['fields'] == {'target': 'proforma', 'template_id': 'T-PRO'}
    assert nxt['actions'][2]['fields'] == {'status': 'sent'}
    sales = look(doc('quote', 'accepted'), can={'edit': True, 'sales': True})
    assert labels(sales) == ['Undo: not answered yet'] and 'office' in sales['sub']
    assert states(doc('quote', 'accepted'))[2:] == [('answer', 'done', ''), ('forward', 'now', 'Proforma or invoice')]


def test_a_declined_quotation_can_be_revised():
    nxt = look(doc('quote', 'declined'))
    assert nxt['tone'] == 'late' and labels(nxt) == ['Make a revision*', 'Undo: not answered yet']
    assert states(doc('quote', 'declined'))[2] == ('answer', 'late', 'Declined')


def test_a_proforma_waits_for_its_advance_then_becomes_the_tax_invoice():
    summary = {'total': 100000, 'advance': {'percent': 40, 'amount': 40000}}
    waiting = look(doc('proforma', 'sent', number='PI/007'), summary)
    assert waiting['text'] == "Sent on 14 Oct. The advance of ₹40,000 hasn't arrived."
    assert labels(waiting) == ['Record the advance*', 'Email a reminder', 'Create tax invoice anyway', 'Make a revision']
    assert waiting['actions'][0]['href'] == '#payment'
    assert states(doc('proforma', 'sent'), summary)[2:] == [('advance', 'now', '₹40,000 asked'), ('forward', 'todo', '')]

    paid = look(doc('proforma', 'sent'), summary, advance=40000)
    assert paid['text'] == 'Advance of ₹40,000 received.' and labels(paid) == ['Create tax invoice*']
    assert states(doc('proforma', 'sent'), summary, 40000)[2:] == [('advance', 'done', '₹40,000'), ('forward', 'now', 'To raise')]

    done = look(doc('proforma', 'converted'), summary, advance=40000)
    assert done['tone'] == 'done' and done['actions'] == []
    assert states(doc('proforma', 'converted'), summary)[2:] == [('advance', 'skipped', 'No advance'), ('forward', 'done', '')]


def test_an_invoice_waits_for_payment_and_takes_advances_first():
    summary = {'total': 118000, 'paid': 18000, 'balance': 100000}
    nxt = look(doc('invoice', 'pending', number='058'), summary)
    assert nxt['text'] == '₹1,00,000 due.' and nxt['sub'] == '₹18,000 received so far. Sent on 14 Oct.'
    assert labels(nxt) == ['Record payment*', 'Email a reminder']
    assert states(doc('invoice', 'pending'), summary)[2] == ('paid', 'now', '₹18,000 of ₹1,18,000')

    advance = look(doc('invoice', 'pending'), summary, open_advances=[{'proforma_number': 'PI/007', 'amount': 40000}])
    assert labels(advance) == ['Apply the advance on PI/007*', 'Record payment', 'Email a reminder']
    assert advance['actions'][0]['href'] == '#advances'

    paid = look(doc('invoice', 'paid'), {'total': 118000, 'paid': 118000, 'balance': 0})
    assert paid['tone'] == 'done' and paid['actions'] == []
    assert states(doc('export_invoice', 'paid'), {'total': 118000, 'paid': 118000, 'balance': 0})[2] == ('paid', 'done', '')


def test_a_revised_version_points_to_the_newest_and_viewers_get_no_actions():
    revised = look(doc('quote', 'revised'))
    assert revised['tone'] == 'draft' and revised['actions'] == []
    assert states(doc('proforma', 'revised'))[2] == ('advance', 'skipped', 'Revised')
    assert look(doc('invoice', 'pending'), {'total': 10, 'balance': 10}, can={'edit': False, 'sales': False})['actions'] == []


def test_the_head_pill_and_money_strip_say_where_the_money_is():
    assert D.pill(doc('quote', 'sent'), {}) == {'text': 'Sent', 'tone': 'wait'}
    assert D.pill(doc('quote', 'declined'), {})['tone'] == 'late'
    assert D.pill(doc('proforma', 'sent'), {}, advance_received=0)['text'] == 'Advance asked'
    assert D.pill(doc('proforma', 'sent'), {}, advance_received=40000) == {'text': 'Advance received', 'tone': 'done'}
    assert D.pill(doc('invoice', 'pending'), {'balance': 100, 'paid': 18})['text'] == 'Part paid'
    assert D.pill(doc('invoice', 'paid'), {'balance': 0}) == {'text': 'Paid', 'tone': 'done'}

    assert D.money_strip(doc('quote', 'sent'), {'total': 100}, []) is None
    payments = [{'amount': 40000, 'advance_number': 'PI/007'}, {'amount': 30000, 'advance_number': None}]
    strip = D.money_strip(doc('invoice', 'pending'), {'total': 118000, 'balance': 48000, 'tax_lines': [1]}, payments)
    assert [(m['label'], m['value'], m['cap'], m.get('late', False)) for m in strip] == [
        ('Invoice total', 118000, 'incl. GST', False), ('Less advance', -40000, 'On proforma PI/007', False),
        ('Received since', 30000, '', False), ('Due', 48000, '', True)]
    strip = D.money_strip(doc('proforma', 'sent'), {'total': 100000, 'advance': {'percent': 40, 'amount': 40000}}, [], advance_received=10000)
    assert [(m['label'], m['value'], m['cap']) for m in strip] == [
        ('Proforma total', 100000, ''), ('Advance asked', 40000, '40% of the order'), ('Advance received', 10000, ''),
        ('Still to come', 30000, '')]


def test_beside_the_document_its_chain_who_gets_it_and_what_happened():
    docs = [{'invoice_id': 'I-1', 'doc_type': 'invoice', 'status': 'pending', 'total_amount': 500, 'paid_amount': 0, 'doc_number': '058'},
            {'invoice_id': 'Q-1', 'doc_type': 'quote', 'status': 'converted', 'total_amount': 500, 'paid_amount': 0, 'doc_number': 'Q/041',
             'versions': [{'invoice_id': 'Q-0'}]}]
    chain = D.chain(docs, 'Q-0', url)
    assert [(c['kind'], c['number'], c['pill']['text'], c['here']) for c in chain] == [
        ('Quotation', 'Q/041', 'Accepted', True), ('Tax Invoice', '058', 'Unpaid', False)]   # an earlier version is "here" too
    people = [{'name': 'A', 'project_gets': 'all'}, {'name': 'B', 'project_gets': 'billing'}, {'name': 'C', 'project_gets': 'none'}]
    assert [p['name'] for p in D.who_gets_it(doc('quote', 'sent'), people)] == ['A']
    assert [p['name'] for p in D.who_gets_it(doc('invoice', 'pending'), people)] == ['A', 'B']
    events = [{'kind': 'payment', 'title': 'Payment of ₹500 on 058', 'body': 'Axle Works', 'link': '/invoices/I-1', 'created_at': '2026-10-20'},
              {'kind': 'note', 'title': 'Called', 'body': 'Call back Monday', 'link': '/invoices/I-1'}, {'kind': 'note', 'title': 'Other', 'link': '/x'}]
    act = D.activity(events, 'I-1', ('Axle Works', None))
    assert [(a['title'], a['body'], a['tone']) for a in act] == [('Payment of ₹500 on 058', None, 't-pay'), ('Called', 'Call back Monday', 't-note')]
