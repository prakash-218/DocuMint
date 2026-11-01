"""Credit and debit notes on the app's screens, in the database: the invoice's page (making one, its notes, its money
strip with them, what's to refund), the note's own page (its steps, next step and pill, and a credit note's refunds),
the Invoices list's tabs, the note in the editor, and the search."""

import re

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import app, client, gst_org  # noqa: F401
from tests.integration.test_credit_notes_db import _invoice, _note
from tests.spa import document, editor


def _actions(page):
    return {a['label']: a for a in page['next']['actions']}


def _steps(note_id):
    """The note's tracker steps (document_view.steps), from what's saved."""
    from access import fetch_invoice
    from document_view import steps
    header, _ = fetch_invoice(note_id)
    return steps(header, {})


def test_an_invoice_and_its_credit_note(app, client, gst_org):
    invoice_id, number = _invoice(client, gst_org)                       # 1,18,000
    page = document(client, f'/invoices/{invoice_id}')
    made = _actions(page)
    assert made['Credit note']['fields'] == {'kind': 'credit'} and made['Debit note']['fields'] == {'kind': 'debit'}
    assert not made['Credit note']['primary'] and made['Credit note']['action'].endswith(f'/invoices/{invoice_id}/notes')
    assert page['notes'] is None and page['refunds'] is None

    note_id = _note(client, invoice_id, 'credit', qty=1)                # 59,000
    draft_editor = editor(client, f'/credit-notes/{note_id}/edit')
    assert re.match(r'Edit CN/\d{3}/', draft_editor['title']) and draft_editor['customer']['fixed']['name'] == 'Gear Cutters Ltd'
    assert draft_editor['against']['number'] == number and draft_editor['against']['url'].endswith(f'/invoices/{invoice_id}')
    assert draft_editor['type']['due_label'] is None and [f['key'] for f in draft_editor['details']['fields']] == ['reason']

    draft = document(client, f'/credit-notes/{note_id}')
    assert (draft['head']['kind'], draft['head']['pill']['text']) == ('Credit Note', 'Draft')
    assert draft['next']['actions'][0]['label'] == 'Issue' and draft['next']['actions'][0]['primary']
    assert draft['list']['url'] == '/invoices/?status=credit_note'
    assert draft['payments'] is None and draft['convert'] is None and draft['money'] is None and draft['refunds'] is None
    assert 'Against invoice' in draft['document_html'] and number in draft['document_html']

    client.post(f'/credit-notes/{note_id}/finalize')
    issued = document(client, f'/credit-notes/{note_id}')
    assert issued['head']['pill'] == {'text': 'Issued', 'tone': 'done'}
    assert issued['next']['text'].endswith(f', against {number}.')
    assert {f'Open {number}', 'Cancel the credit note'} <= set(_actions(issued))
    assert issued['refunds'] is None                                        # nothing paid, so nothing to refund

    page = document(client, f'/invoices/{invoice_id}')
    assert [(n['number'], n['pill']['text'], n['amount']) for n in page['notes']['rows']] == [(issued['number'], 'Issued', -59000.0)]
    assert [(m['label'], m['value']) for m in page['money']] == [('Invoice total', 118000.0), ('Credit notes', -59000.0),
                                                                 ('Received', 0.0), ('Due', 59000.0)]
    assert page['next']['text'] == '₹59,000 due.'
    assert next(d for d in page['chain'] if d['number'] == issued['number'])['total'] == -59000.0

    # the Invoices list: the note under its own tab, not under All
    listing = client.get('/api/documents/invoices').get_json()
    assert {t['key']: t.get('alone', False) for t in listing['tabs']}['credit_note'] is True
    row = next(r for r in listing['rows'] if r['id'] == note_id)
    assert (row['tab'], row['note'], row['total'], row['balance'], row['url']) == \
        ('credit_note', f'Against {number}', -59000.0, None, f'/credit-notes/{note_id}')
    assert next(r for r in listing['rows'] if r['id'] == invoice_id)['balance'] == 59000.0

    # cancelled: counted no more, and it can be issued again
    client.post(f'/credit-notes/{note_id}/status', data={'status': 'cancelled'})
    cancelled = document(client, f'/credit-notes/{note_id}')
    assert (cancelled['head']['pill']['text'], cancelled['next']['text']) == ('Cancelled', 'Cancelled.')
    assert 'Issue it again' in _actions(cancelled)
    assert [s['state'] for s in _steps(note_id)] == ['done', 'late']
    assert document(client, f'/invoices/{invoice_id}')['next']['text'] == '₹1,18,000 due.'

    # found by its number
    items = client.get('/search/items').get_json()['items']
    found = next(i for i in items if i.get('url') == f'/credit-notes/{note_id}')
    assert found['code'].startswith('CN ') and 'Credit Note' in found['sub']


def test_a_refund_from_the_credit_note(app, client, gst_org):
    invoice_id, number = _invoice(client, gst_org, qty=2, rate=10000)    # 23,600, paid in full
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '23600', 'method': 'NEFT / RTGS'})
    note_id = _note(client, invoice_id, 'credit', qty=1)                # 11,800
    client.post(f'/credit-notes/{note_id}/finalize')

    page = document(client, f'/invoices/{invoice_id}')
    assert page['next']['text'] == '₹11,800 to refund.' and page['head']['pill']['text'] == 'To refund'
    assert page['money'][-1] == {'label': 'To refund', 'value': 11800.0, 'cap': ''}

    note = document(client, f'/credit-notes/{note_id}')
    assert note['refunds']['owed'] == 11800.0 and note['refunds']['record']['suggested'] == 11800.0
    assert note['next']['actions'][0] == {'label': 'Record a refund', 'kind': 'link', 'href': '#refunds', 'primary': True}
    assert note['next']['sub'] == f'₹11,800 to refund on {number}.'

    client.post(note['refunds']['record']['action'], data={'amount': '11800', 'refunded_on': '2026-11-02', 'reference': 'UTR 4411'})
    note = document(client, f'/credit-notes/{note_id}')
    assert [(r['amount'], r['reference']) for r in note['refunds']['rows']] == [(11800.0, 'UTR 4411')]
    assert note['refunds']['owed'] == 0 and note['refunds']['record'] is None
    assert not any(a['label'] == 'Record a refund' for a in note['next']['actions'])
    page = document(client, f'/invoices/{invoice_id}')
    assert page['next']['text'] == 'Paid in full.' and page['money'][-1]['label'] == 'Due'


def test_a_debit_note_and_the_share_message(app, client, gst_org):
    invoice_id, number = _invoice(client, gst_org, qty=1, rate=10000)    # 11,800
    note_id = _note(client, invoice_id, 'debit')
    client.post(f'/debit-notes/{note_id}/finalize')
    page = document(client, f'/invoices/{invoice_id}')
    assert [(m['label'], m['value']) for m in page['money']][1] == ('Debit notes', 11800.0)
    share = client.get(document(client, f'/debit-notes/{note_id}')['share']).get_json()
    assert re.search(rf'our debit note DN/\d{{3}}/\S+ against invoice {re.escape(number)}: ₹11,800 incl\. GST\.', share['body'])
    assert 'UPI' not in share['body']
