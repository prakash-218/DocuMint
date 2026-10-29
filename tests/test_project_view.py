"""The new project page's logic: where the job is (from its documents), what to do next, and its timeline."""

import itertools
from datetime import date

import pytest

import project_view as V

TODAY = date(2026, 10, 20)
EDITOR = {'edit': True, 'sales': False}
_ids = itertools.count(1)


def doc(doc_type, status, total=1000, paid=0, issue='2026-10-14', number=None):
    n = next(_ids)
    return {'invoice_id': f'D-{n}', 'doc_type': doc_type, 'status': status, 'total_amount': total, 'paid_amount': paid,
            'issue_date': issue, 'doc_number': number or f'{doc_type[0].upper()}/{n:03}', 'currency_code': 'INR'}


def url(endpoint, **values):
    return f"/{endpoint}" + ''.join(f'/{k}={v}' for k, v in sorted(values.items()))


def look(docs, status='open', can=EDITOR):
    st = V.stage(docs, status, TODAY)
    nxt = V.next_step(docs, st, {'project_id': 'P-1', 'status': status}, can, url, TODAY)
    return st, nxt


def states(st):
    return [(s['key'], s['state'], s['sub']) for s in st['steps']]


def labels(nxt):
    return [a['label'] + ('*' if a['primary'] else '') for a in nxt['actions']]


def test_a_new_project_starts_with_a_quotation():
    st, nxt = look([])
    assert st['current'] == 'quoted' and states(st)[0] == ('quoted', 'now', 'No quotation yet')
    assert st['pill'] == {'text': 'New', 'tone': 'action'}
    assert nxt['text'] == 'No quotation yet.' and labels(nxt) == ['New quotation*', 'New invoice']
    assert labels(look([], can={'edit': True, 'sales': True})[1]) == ['New quotation*']


def test_a_draft_quotation_is_finished_first():
    q = doc('quote', 'draft')
    st, nxt = look([q])
    assert states(st)[0] == ('quoted', 'now', 'Draft')
    assert nxt['text'] == f"Quotation {q['doc_number']} is a draft." and labels(nxt) == ['Edit quotation*', 'Open']


def test_a_sent_quotation_waits_for_the_answer():
    q = doc('quote', 'sent', issue='2026-10-14')
    st, nxt = look([q])
    assert states(st)[:2] == [('quoted', 'done', '14 Oct'), ('accepted', 'now', 'Waiting · 6 days')]
    assert st['pill'] == {'text': 'Waiting for an answer', 'tone': 'wait'}
    assert nxt['text'] == f"Quotation {q['doc_number']} sent on 14 Oct." and nxt['sub'] == 'No answer for 6 days.'
    assert labels(nxt) == ['Mark accepted*', 'Send a follow-up', 'Mark declined', 'Make a revision']
    accept = nxt['actions'][0]
    assert accept['kind'] == 'post' and accept['action'] == f"/invoices_bp.set_status/invoice_id={q['invoice_id']}"
    assert accept['fields'] == {'status': 'accepted'}
    assert nxt['actions'][1] == {'label': 'Send a follow-up', 'kind': 'email', 'invoice_id': q['invoice_id'], 'primary': False}


def test_a_declined_quotation():
    st, nxt = look([doc('quote', 'declined')])
    assert states(st)[1] == ('accepted', 'late', 'Declined') and st['pill'] == {'text': 'Declined', 'tone': 'late'}
    assert nxt['tone'] == 'late' and labels(nxt) == ['Make a revision*', 'Cancel the project']


def test_once_accepted_the_advance_is_asked_for():
    q = doc('quote', 'accepted')
    st, nxt = look([q])
    assert states(st)[2] == ('advance', 'now', 'Not requested') and st['pill']['text'] == 'Accepted'
    assert labels(nxt) == ['Raise proforma for the advance*', 'Invoice in full instead']
    assert nxt['actions'][0]['fields'] == {'target': 'proforma'}
    sales = look([q], can={'edit': True, 'sales': True})[1]
    assert sales['actions'] == [] and 'office' in sales['sub']


def test_a_proforma_waits_for_the_advance():
    pi = doc('proforma', 'sent', issue='2026-10-16')
    st, nxt = look([doc('quote', 'converted'), pi])
    assert states(st)[2] == ('advance', 'now', 'Requested') and st['pill']['text'] == 'Waiting for advance'
    assert nxt['text'] == f"Proforma {pi['doc_number']} sent on 16 Oct." and nxt['sub'] == "The advance hasn't arrived (4 days)."
    assert nxt['actions'][0] == {'label': 'Record the advance', 'kind': 'link', 'primary': True,
                                 'href': f"/invoices_bp.view_invoice/invoice_id={pi['invoice_id']}#payment"}


def test_with_the_advance_in_the_invoice_is_raised():
    pi = doc('proforma', 'sent', total=400, paid=400)
    st, nxt = look([doc('quote', 'converted'), pi])
    assert states(st)[2:4] == [('advance', 'done', '₹400'), ('invoiced', 'now', 'To raise')]
    assert nxt['text'] == 'Advance of ₹400 received.' and labels(nxt) == ['Create tax invoice*']
    assert nxt['actions'][0]['action'] == f"/invoices_bp.convert/invoice_id={pi['invoice_id']}"


def test_the_advance_moves_onto_the_invoice_made_from_its_proforma():
    docs = [doc('quote', 'converted'), doc('proforma', 'converted', total=400, paid=0),
            doc('invoice', 'pending', total=1000, paid=400, number='058')]
    st, nxt = look(docs)
    assert states(st)[2:] == [('advance', 'done', 'On the invoice'), ('invoiced', 'done', '14 Oct'), ('paid', 'now', '₹600 due')]
    assert st['pill']['text'] == 'Part paid' and nxt['text'] == 'Tax invoice 058: ₹600 due.'


def test_an_invoice_without_an_advance():
    inv = doc('invoice', 'pending', total=100000, issue='2026-10-18', number='058')
    st, nxt = look([doc('quote', 'accepted'), inv])
    assert states(st)[2:] == [('advance', 'skipped', 'No advance'), ('invoiced', 'done', '18 Oct'), ('paid', 'now', '₹1,00,000 due')]
    assert st['pill'] == {'text': 'Waiting for payment', 'tone': 'wait'}
    assert nxt['text'] == 'Tax invoice 058: ₹1,00,000 due.' and labels(nxt) == ['Record payment*', 'Email a reminder']
    assert look([doc('quote', 'accepted'), doc('invoice', 'pending', total=1000, paid=300)])[0]['pill']['text'] == 'Part paid'


def test_a_draft_invoice_is_finished_first():
    st, nxt = look([doc('quote', 'accepted'), doc('invoice', 'draft')])
    assert states(st)[3] == ('invoiced', 'now', 'Draft') and labels(nxt) == ['Edit invoice*', 'Open']


def test_paid_in_full():
    docs = [doc('quote', 'converted'), doc('invoice', 'paid', total=1000, paid=1000)]
    st, nxt = look(docs)
    assert st['current'] is None and st['pill'] == {'text': 'Paid', 'tone': 'done'}
    assert [s['state'] for s in st['steps']] == ['done', 'done', 'skipped', 'done', 'done']
    assert nxt['text'] == 'Paid in full.' and labels(nxt) == ['Mark the project completed*']
    assert look(docs, status='completed')[1]['actions'] == []


def test_a_cancelled_project():
    st, nxt = look([doc('quote', 'sent')], status='cancelled')
    assert st['pill'] == {'text': 'Cancelled', 'tone': 'draft'} and 'now' not in [s['state'] for s in st['steps']]
    assert nxt['text'] == 'This project is cancelled.' and labels(nxt) == ['Reopen it*']


@pytest.mark.parametrize('docs', [[], [doc('quote', 'sent')], [doc('quote', 'accepted'), doc('invoice', 'pending')]])
def test_viewers_get_the_sentence_without_the_buttons(docs):
    assert look(docs, can={'edit': False, 'sales': False})[1]['actions'] == []


def test_earlier_revisions_dont_count():
    st, _ = look([doc('quote', 'revised'), doc('quote', 'sent')])
    assert st['current'] == 'accepted'


def test_the_timeline_shows_emails_in_place_of_their_events():
    events = [{'event_id': 'E1', 'kind': 'email_received', 'title': 'Email from Ravi', 'body': None, 'created_at': '2026-10-12T09:00:00',
               'actor_email': None, 'link': '/emails/T1'},
              {'event_id': 'E2', 'kind': 'document_sent', 'title': 'Quotation Q/1 finalized', 'body': 'Gear Cutters Ltd',
               'created_at': '2026-10-10T09:00:00', 'actor_email': 'meena@ourworks.example', 'link': '/quotes/Q1'},
              {'event_id': 'E3', 'kind': 'note', 'title': 'Note: Agreed 4.5% off', 'body': 'Agreed 4.5% off\nif delivered in 6 weeks',
               'created_at': '2026-10-13T09:00:00', 'actor_email': 'meena@ourworks.example', 'link': None}]
    messages = [{'message_id': 'M1', 'thread_id': 'T1', 'subject': 'Re: Quotation Q/1', 'thread_subject': 'Quotation Q/1',
                 'from_name': 'Ravi', 'from_address': 'ravi@gearco.example', 'to_addresses': '', 'sent_at': '2026-10-12T09:00:00',
                 'direction': 'in', 'snippet': 'Can you do   better\non price?', 'file_count': 1}]
    items = V.timeline(events, messages, True, ('Gear Cutters Ltd', None))
    assert [(i['type'], i['title']) for i in items] == [
        ('note', 'Agreed 4.5% off\nif delivered in 6 weeks'), ('email', 'Re: Quotation Q/1'), ('event', 'Quotation Q/1 finalized')]
    assert items[1]['body'] == 'Can you do better on price?' and items[1]['thread_id'] == 'T1' and items[1]['files'] == 1
    assert items[2]['body'] is None and items[2]['who'] == 'meena'          # just the customer's name: left out
    # without the mail, the email's event stays and the email doesn't show
    assert [i['title'] for i in V.timeline(events, messages, False)] == [
        'Agreed 4.5% off\nif delivered in 6 weeks', 'Email from Ravi', 'Quotation Q/1 finalized']
