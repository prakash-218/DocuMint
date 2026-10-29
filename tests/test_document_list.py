"""The quotation, proforma and invoice lists: each document's state in a word and what it means today, and the rows."""

import itertools
from datetime import date

import pytest

import document_list as L

TODAY = date(2026, 10, 20)
_ids = itertools.count(1)


def doc(doc_type, status, total=1000, paid=0, issue='2026-10-14', due=None, **kw):
    n = next(_ids)
    return {'invoice_id': f'D-{n}', 'doc_type': doc_type, 'status': status, 'total_amount': total, 'paid_amount': paid,
            'issue_date': issue, 'due_date': due, 'doc_number': f'TF/{n:03}', 'currency_code': 'INR',
            'customer_id': 'C-1', 'customer_name': 'Gear Cutters Ltd', 'customer_site': 'Hosur plant', **kw}


def url(endpoint, **values):
    return f"/{endpoint}" + ''.join(f'/{k}={v}' for k, v in sorted(values.items()))


@pytest.mark.parametrize('subject, short', [
    ('Quotation for the Axle final assembly for G8', 'Axle final assembly for G8'),
    ('quotation for spline gauges', 'Spline gauges'),
    ('Proforma invoice for the hob arbors', 'Hob arbors'),
    ('Hob arbor set (3 nos)', 'Hob arbor set (3 nos)'),
    (None, ''),
])
def test_the_subject_without_what_every_one_starts_with(subject, short):
    assert L.short_subject(subject) == short


@pytest.mark.parametrize('d, tab, tag, note', [
    (doc('quote', 'draft'), 'draft', ('Draft', 'draft'), ''),
    (doc('quote', 'sent', issue='2026-10-15'), 'sent', ('Sent', 'wait'), 'Sent 5 days ago'),
    (doc('quote', 'sent', issue='2026-10-20'), 'sent', ('Sent', 'wait'), 'Sent today'),
    (doc('quote', 'sent', issue='2026-10-01'), 'sent', ('Sent', 'action'), 'No answer · 19 days'),    # time to chase it
    (doc('quote', 'accepted'), 'accepted', ('Accepted', 'done'), ''),
    (doc('quote', 'declined'), 'declined', ('Declined', 'late'), ''),
    (doc('quote', 'converted'), 'converted', ('Converted', 'done'), ''),
    (doc('proforma', 'sent'), 'sent', ('Advance asked', 'wait'), ''),
    (doc('proforma', 'sent', paid=400), 'sent', ('Advance received', 'done'), ''),
    (doc('proforma', 'converted'), 'converted', ('Invoiced', 'done'), ''),
    (doc('invoice', 'pending'), 'pending', ('Unpaid', 'wait'), ''),
    (doc('invoice', 'pending', due='2026-10-30'), 'pending', ('Unpaid', 'wait'), 'Due in 10 days'),
    (doc('invoice', 'pending', paid=300, due='2026-10-20'), 'pending', ('Part paid', 'wait'), 'Due today'),
    (doc('invoice', 'pending', due='2026-10-08'), 'overdue', ('Overdue', 'late'), '12 days late'),
    (doc('invoice', 'paid', paid=1000), 'paid', ('Paid', 'done'), ''),
    (doc('export_invoice', 'pending', paid=1000), 'paid', ('Paid', 'done'), ''),                     # all in: paid
])
def test_where_each_document_stands(d, tab, tag, note):
    got = L.state(d, TODAY)
    assert (got['tab'], (got['tag']['text'], got['tag']['tone']), got['note']) == (tab, tag, note)


def test_payment_terms_make_an_invoice_due():
    theirs = doc('invoice', 'pending', issue='2026-09-01', payment_days=30)               # due 1 Oct
    assert L.state(theirs, TODAY)['note'] == '19 days late' and L.state(theirs, TODAY)['tab'] == 'overdue'
    usual = doc('invoice', 'pending', issue='2026-10-14')
    assert L.state(usual, TODAY)['note'] == '' and L.state(usual, TODAY, usual_days=30)['note'] == 'Due in 24 days'
    [row] = L.rows([usual], url, TODAY, usual_days=30)
    assert row['until'] == date(2026, 11, 13)                                               # the list's Due column
    quote = doc('quote', 'sent', payment_days=30, due='2026-11-13')
    assert L.rows([quote], url, TODAY)[0]['until'] == '2026-11-13'                          # a quotation: valid until


def test_a_list_has_its_own_kind_and_a_revised_document_once():
    original = doc('quote', 'revised', issue='2026-10-01')
    revision = doc('quote', 'sent', issue='2026-10-10', source_invoice_id=original['invoice_id'], doc_number='TF/001R1',
                   subject='Quotation for the spline gauges', buyer_order_no='PO 4500 0188', project_id='P-7', project_no=7,
                   project_title='Spline gauges')
    invoice, export = doc('invoice', 'pending', due='2026-10-01'), doc('export_invoice', 'draft')
    every = [revision, original, invoice, export]

    quotes = L.build('quotes', every, url, can_create=True, today=TODAY)
    [row] = quotes['rows']
    assert row['number'] == 'TF/001R1' and row['subject'] == 'Spline gauges' and row['tab'] == 'sent'
    assert row['versions'] == [{'number': original['doc_number'], 'url': f"/invoices_bp.view_invoice/invoice_id={original['invoice_id']}"}]
    assert row['search'] == ['PO 4500 0188', original['doc_number']]         # a search for the PO or the old number finds it
    assert row['project'] == {'label': 'PRJ-007', 'title': 'Spline gauges', 'url': '/projects_bp.view_project/project_id=P-7'}
    assert row['customer'] == {'id': 'C-1', 'name': 'Gear Cutters Ltd', 'site': 'Hosur plant'} and row['balance'] is None
    assert [t['key'] for t in quotes['tabs']] == ['all', 'draft', 'sent', 'accepted', 'declined', 'converted']
    assert quotes['new_url'] == '/invoices_bp.create_invoice/doc_type=quote' and quotes['until'] == 'Valid until'

    invoices = L.build('invoices', every, url, can_create=False, today=TODAY)
    assert [(r['id'], r['tab'], r['balance'], r['note']) for r in invoices['rows']] == [
        (invoice['invoice_id'], 'overdue', 1000, '19 days late'), (export['invoice_id'], 'draft', None, '')]
    assert invoices['new_url'] is None and invoices['until'] == 'Due' and invoices['rows'][0]['until'] == '2026-10-01'
    assert L.build('proformas', every, url, can_create=True, today=TODAY)['rows'] == []
