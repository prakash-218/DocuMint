"""Credit and debit notes in the money views, in the database: what Home, a project, a customer's statement, the
customer portal, the payments list and the CSVs make of an invoice once notes are issued against it (and a refund
paid back on a credit note)."""

import csv
import io
import re
import uuid

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.spa import editor, editor_form


def _invoice(client, org_id, qty, rate):
    """A sent tax invoice with GST at 18% for a customer of its own; (its id, its number, the customer, the project)."""
    import projects
    customer = _customer(org_id, f'Spline Works {uuid.uuid4().hex[:6]}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Gauge set')
    invoice_id, number = _create(client, org_id, 'invoice', 'Tax Invoice', customer, [{'description': 'Ring gauge', 'rate': rate, 'qty': qty}],
                                 tax_mode='cgst_sgst', tax_rate='18', project_id=project_id)
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    return invoice_id, number, customer, project_id


def _issued(client, invoice_id, kind, qty=None):
    """A note against the invoice (its first line's quantity set to qty), issued; its id."""
    response = client.post(f'/invoices/{invoice_id}/notes', data={'kind': kind})
    note_id = re.search(r'/(?:credit|debit)-notes/([0-9a-f-]{36})/edit', response.headers['Location']).group(1)
    if qty is not None:
        page = editor(client, response.headers['Location'])
        form = editor_form(page)
        items = next(s for s in page['sections'] if s['type'] == 'line_item')
        form[f"line_item_{items['id']}_1_field_{next(f for f in items['fields'] if f['name'] == 'qty')['id']}"] = str(qty)
        assert client.post(page['action'], data=form).status_code == 302
    assert client.post(f'/{kind}-notes/{note_id}/finalize').status_code == 302
    return note_id


def _number(note_id):
    from access import fetch_invoice
    return fetch_invoice(note_id)[0]['doc_number']


def test_home_and_the_project_count_what_is_left(app, client, gst_org):
    before = client.get('/api/home').get_json()['to_receive']['total'].get('INR', 0)
    invoice_id, number, _, project_id = _invoice(client, gst_org, qty=2, rate=50000)       # 1,18,000
    assert client.get('/api/home').get_json()['to_receive']['total'].get('INR', 0) == round(before + 118000, 2)
    note_id = _issued(client, invoice_id, 'credit', qty=1)                                  # 59,000 back
    home = client.get('/api/home').get_json()
    assert home['to_receive']['total'].get('INR', 0) == round(before + 59000, 2)

    page = client.get(f'/api/projects/{project_id}').get_json()
    assert (page['money'][0]['invoiced'], page['money'][0]['received'], page['money'][0]['due']) == (59000.0, 0.0, 59000.0)
    note = next(d for d in page['documents'] if d['invoice_id'] == note_id)
    assert (note['adjusts'], note['against'], note['status'], note['total']) == (-1, number, 'issued', 59000.0)
    assert page['stage']['current'] == 'paid' and page['next']['text'].endswith('₹59,000 due.')

    # the rest comes in: the project is paid
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '59000', 'method': 'NEFT / RTGS'})
    page = client.get(f'/api/projects/{project_id}').get_json()
    assert (page['money'][0]['invoiced'], page['money'][0]['received'], page['money'][0]['due']) == (59000.0, 59000.0, 0.0)
    assert page['stage']['current'] is None


def test_a_statement_with_a_credit_note_and_a_refund(app, client, gst_org):
    import statement
    from flask import url_for
    invoice_id, number, customer, _ = _invoice(client, gst_org, qty=2, rate=10000)          # 23,600
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '23600', 'method': 'NEFT / RTGS'})
    credit = _issued(client, invoice_id, 'credit', qty=1)                                   # 11,800 after it was paid
    client.post(f'/credit-notes/{credit}/refunds', data={'amount': '11800', 'refunded_on': '2026-11-03', 'reference': 'UTR 7731'})
    cn = _number(credit)

    money = client.get(f'/api/customers/{customer}').get_json()['money']
    account = money['statement'][0]
    lines = [(line['text'], line['owed'], line['paid']) for line in account['lines']]
    assert (f'Tax Invoice {number}', 23600.0, 0.0) in lines
    assert (f'Credit Note {cn} against {number}', 0.0, 11800.0) in lines
    assert (f'Refund on {cn}', 11800.0, 0.0) in lines
    assert account['lines'][-1]['balance'] == 0 and money['total'] == {}                   # nothing owed either way

    with app.test_request_context():
        data = statement.gather(gst_org, {'customer_id': customer, 'name': 'Spline Works'}, url_for, 'all', 'INR')
    assert [x['text'] for x in data['account']['lines']][-1].startswith('Refund on') and data['unpaid'] == []


def test_a_debit_note_on_the_statement_and_in_the_portal(app, client, gst_org):
    import portal_view
    from flask import url_for
    invoice_id, number, customer, _ = _invoice(client, gst_org, qty=1, rate=10000)          # 11,800
    debit = _issued(client, invoice_id, 'debit', qty=1)                                     # 11,800 more
    money = client.get(f'/api/customers/{customer}').get_json()['money']
    lines = [(line['text'], line['owed'], line['paid']) for line in money['statement'][0]['lines']]
    assert (f'Debit Note {_number(debit)} against {number}', 11800.0, 0.0) in lines
    assert money['total'] == {'INR': 23600.0}

    with app.test_request_context():
        portal = portal_view.documents(customer, url_for)
    rows = {r['id']: r for r in portal['rows']}
    assert rows[invoice_id]['balance'] == '₹23,600.00' and rows[debit]['balance'] is None and rows[debit]['due'] == '—'
    assert portal['stats']['outstanding'] == '₹23,600.00'


def test_a_credit_note_in_the_portal_and_the_lists(app, client, gst_org):
    import exports
    import payments_view
    import portal_view
    from app_helpers import invoice_is_overdue
    from db import db
    from flask import url_for
    invoice_id, number, customer, _ = _invoice(client, gst_org, qty=2, rate=10000)          # 23,600
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '23600', 'method': 'NEFT / RTGS'})
    credit = _issued(client, invoice_id, 'credit', qty=1)
    client.post(f'/credit-notes/{credit}/refunds', data={'amount': '11800', 'refunded_on': '2026-11-03', 'reference': 'UTR 7731'})
    cn = _number(credit)

    with app.test_request_context():
        portal = portal_view.documents(customer, url_for)
        refunds = db.execute_proc('sp_list_org_refunds', (gst_org, None)) or []
        docs = db.execute_proc('sp_list_invoices', (gst_org, None, 100000, 0)) or []
        listed = payments_view.build(db.execute_proc('sp_list_org_payments', (gst_org, None)) or [], docs, url_for, refunds)
    note_row = next(r for r in portal['rows'] if r['id'] == credit)
    assert note_row['total'] == '−₹11,800.00' and note_row['due'] == '—' and note_row['status']['text'] == 'issued'
    assert portal['stats']['outstanding'] == 'Nothing due' and portal['stats']['paid'] == '₹11,800.00'   # 23,600 in, 11,800 back

    refund = next(r for r in listed['rows'] if r['tab'] == 'refund' and r['document']['number'] == cn)
    assert (refund['amount'], refund['reference'], refund['note']) == (-11800.0, 'UTR 7731', f'Refund on {cn}, against {number}')
    assert 'refund' in [t['key'] for t in listed['tabs']]
    out = list(csv.reader(io.StringIO(exports.payments_csv([refund]).decode('utf-8-sig'))))
    assert out[1][4] == cn and out[1][-2:] == ['-11800.00', '-11800.00']

    from access import fetch_invoice
    from invoice_service import build_sections, invoice_summary
    items = []
    for doc_id in (invoice_id, credit):
        header, values = fetch_invoice(doc_id)
        row = next(d for d in docs if d['invoice_id'] == doc_id)
        items.append((row, header, invoice_summary(header, build_sections(header, values), [])))
    note = next(d for d in docs if d['invoice_id'] == credit)
    assert not invoice_is_overdue({**note, 'status': 'pending', 'due_date': '2020-01-01'})          # a note is never overdue
    assert invoice_is_overdue({**items[0][0], 'status': 'pending', 'due_date': '2020-01-01'})
    out = list(csv.reader(io.StringIO(exports.documents_csv(items).decode('utf-8-sig'))))
    assert out[0][-1] == 'Against invoice' and out[2][0] == cn and out[2][-1] == number and out[1][-1] == ''
