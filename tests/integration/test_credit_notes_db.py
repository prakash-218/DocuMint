"""Credit and debit notes against a sent tax invoice, in the database: made with the invoice's lines, numbered in their
own series, issued, and counted on the invoice (its due and paid / pending); a credit note is never more than is left
to credit; cancelling it counts it no more; a credit note on a paid invoice can record a refund; and an invoice with
notes issued against it can't go back to draft or be deleted."""

import re

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.spa import document, editor, editor_form


def _invoice(client, org_id, qty=2, rate=50000):
    customer = _customer(org_id, 'Gear Cutters Ltd', 'Tamil Nadu', 'India')
    invoice_id, number = _create(client, org_id, 'invoice', 'Tax Invoice', customer, [{'description': 'Hob arbor', 'rate': rate, 'qty': qty}],
                                 tax_mode='cgst_sgst', tax_rate='18')
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    return invoice_id, number


def _note(client, invoice_id, kind, qty=None):
    """A note against the invoice, its first line's quantity changed to qty, saved; its id."""
    response = client.post(f'/invoices/{invoice_id}/notes', data={'kind': kind})
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    note_id = re.search(r'/(?:credit|debit)-notes/([0-9a-f-]{36})/edit', response.headers['Location']).group(1)
    if qty is not None:
        page = editor(client, response.headers['Location'])
        form = editor_form(page)
        items = next(s for s in page['sections'] if s['type'] == 'line_item')
        qty_field = next(f for f in items['fields'] if f['name'] == 'qty')
        form[f"line_item_{items['id']}_1_field_{qty_field['id']}"] = str(qty)
        assert client.post(page['action'], data=form).status_code == 302
    return note_id


def _money(invoice_id):
    from access import fetch_invoice
    from documents import balance_of, credit_of
    header, _ = fetch_invoice(invoice_id)
    return header['status'], round(balance_of(header), 2), round(credit_of(header), 2)


def test_a_credit_note_takes_off_what_an_invoice_is_owed(app, client, gst_org):
    from access import fetch_invoice
    invoice_id, number = _invoice(client, gst_org)                   # 2 x 50,000 + 18% = 1,18,000
    note_id = _note(client, invoice_id, 'credit', qty=1)            # one came back: 59,000
    note, _ = fetch_invoice(note_id)
    assert (note['doc_type'], note['status'], note['source_invoice_id'], note['source_number']) == ('credit_note', 'draft', invoice_id, number)
    assert re.fullmatch(r'CN/\d{3}/\d\d-\d\d', note['doc_number']) and note['tax_mode'] == 'cgst_sgst' and float(note['total_amount']) == 59000
    assert _money(invoice_id) == ('pending', 118000, 0)              # a draft counts for nothing

    assert client.post(f'/credit-notes/{note_id}/finalize').status_code == 302
    assert fetch_invoice(note_id)[0]['status'] == 'issued'
    assert _money(invoice_id) == ('pending', 59000, 0)
    page = document(client, f'/invoices/{invoice_id}')
    assert page['status'] == 'pending'

    # the rest credited too: the invoice is settled, with nothing received
    second = _note(client, invoice_id, 'credit')                    # all its lines again: 1,18,000, more than is left
    client.post(f'/credit-notes/{second}/finalize')
    assert fetch_invoice(second)[0]['status'] == 'draft'            # refused
    second_page = editor(client, f'/credit-notes/{second}/edit')
    form = editor_form(second_page)
    items = next(s for s in second_page['sections'] if s['type'] == 'line_item')
    form[f"line_item_{items['id']}_1_field_{next(f for f in items['fields'] if f['name'] == 'qty')['id']}"] = '1'
    client.post(second_page['action'], data=form)
    assert client.post(f'/credit-notes/{second}/finalize').status_code == 302
    assert _money(invoice_id) == ('paid', 0, 0)

    # cancelling one counts it no more
    assert client.post(f'/credit-notes/{second}/status', data={'status': 'cancelled'}).status_code == 302
    assert _money(invoice_id) == ('pending', 59000, 0)

    # an invoice with notes issued against it stays as it is
    client.post(f'/invoices/{invoice_id}/reopen')
    client.post(f'/invoices/{invoice_id}/delete')
    assert fetch_invoice(invoice_id)[0]['status'] == 'pending'


def test_a_debit_note_adds_to_it(app, client, gst_org):
    invoice_id, _ = _invoice(client, gst_org, qty=1, rate=10000)    # 11,800
    note_id = _note(client, invoice_id, 'debit')                    # its line again: 11,800 more
    from access import fetch_invoice
    assert re.fullmatch(r'DN/\d{3}/\d\d-\d\d', fetch_invoice(note_id)[0]['doc_number'])
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '11800', 'method': 'NEFT / RTGS'})
    assert _money(invoice_id) == ('paid', 0, 0)
    client.post(f'/debit-notes/{note_id}/finalize')
    assert _money(invoice_id) == ('pending', 11800, 0)               # owed again
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '11800', 'method': 'NEFT / RTGS'})
    assert _money(invoice_id) == ('paid', 0, 0)


def test_a_refund_on_a_paid_invoice(app, client, gst_org):
    from access import fetch_invoice
    from db import db
    invoice_id, _ = _invoice(client, gst_org, qty=2, rate=10000)    # 23,600, paid in full
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '23600', 'method': 'NEFT / RTGS'})
    note_id = _note(client, invoice_id, 'credit', qty=1)            # 11,800 credited after it was paid
    client.post(f'/credit-notes/{note_id}/finalize')
    assert _money(invoice_id) == ('paid', 0, 11800)                  # owed back
    client.post(f'/credit-notes/{note_id}/refunds', data={'amount': '12000', 'refunded_on': '2026-11-02', 'reference': 'UTR 4411'})
    assert not db.execute_proc('sp_list_note_refunds', (note_id, gst_org))     # more than they're owed back
    client.post(f'/credit-notes/{note_id}/refunds', data={'amount': '11800', 'refunded_on': '2026-11-02', 'reference': 'UTR 4411'})
    refunds = db.execute_proc('sp_list_note_refunds', (note_id, gst_org))
    assert [(float(r['amount']), r['reference']) for r in refunds] == [(11800.0, 'UTR 4411')]
    assert _money(invoice_id) == ('paid', 0, 0)
    assert fetch_invoice(note_id)[0]['refunded_amount'] == 11800
    client.post(f'/credit-notes/{note_id}/status', data={'status': 'cancelled'})
    assert fetch_invoice(note_id)[0]['status'] == 'issued'          # not with a refund on it
    client.post(f"/credit-notes/{note_id}/refunds/{refunds[0]['refund_id']}/delete")
    assert _money(invoice_id) == ('paid', 0, 11800)


def test_who_makes_them(app, client, gst_org):
    from tests.integration.test_app_db import OWNER, VIEWER, login
    from tests.integration.test_sales_role_db import _set_role
    invoice_id, _ = _invoice(client, gst_org)
    _set_role(client, VIEWER, 'viewer')
    login(client, VIEWER)
    try:
        response = client.post(f'/invoices/{invoice_id}/notes', data={'kind': 'credit'})
        assert '/edit' not in (response.headers.get('Location') or '')
    finally:
        login(client, OWNER)
