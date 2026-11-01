"""
Invoicing part of a quotation against real PostgreSQL (same opt-in as test_app_db.py): a tax invoice for 60% of it,
made from its proforma, every price at 60% and marked so, its discount taken into the prices, and the advance going
with it only where it fits; never past what's left; then the rest by amount.
"""

import re
import uuid

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, _summary, app, client, gst_org  # noqa: F401
from tests.integration.test_project_page_db import _page, _run


def _made(response):
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return re.search(r'/invoices/([0-9a-f-]{36})', response.headers['Location']).group(1)


def _lines(invoice_id):
    from access import fetch_invoice
    _, values = fetch_invoice(invoice_id)
    return sorted(v['val_string'] for v in values if (v.get('val_string') or '').startswith(('Guarding', 'Doors')))


def _advance_on(invoice_id):
    from db import db
    return sum(float(p['amount']) for p in db.execute_proc('sp_get_invoice_payments', (invoice_id,)) or [])


def test_a_tax_invoice_for_part_of_the_quotation(app, client, gst_org):
    import projects
    tag = uuid.uuid4().hex[:6]
    customer = _customer(gst_org, f'Press Makers {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(gst_org, customer, 'Press guarding')
    # ₹50,000 of lines, 10% off: ₹45,000 before GST, ₹53,100 with it
    quote_id, quote_no = _create(client, gst_org, 'quote', 'Quotation', customer,
                                 [{'description': 'Guarding frame', 'price': 30000, 'qty': 1}, {'description': 'Doors', 'price': 10000, 'qty': 2}],
                                 tax_mode='cgst_sgst', tax_rate='18', discount='10%', project_id=project_id)
    client.post(f'/quotes/{quote_id}/finalize')
    page = _page(client, project_id)
    assert page['part'] is None                                                # not accepted yet
    _run(client, page['next']['actions'][0])                                   # accepted
    proforma_id = re.search(r'([0-9a-f-]{36})', _run(client, _page(client, project_id)['next']['actions'][0])).group(1)
    client.post(f'/proformas/{proforma_id}/finalize')
    for amount in ('20000', '15000'):                                          # the advance, in two payments
        assert client.post(f'/proformas/{proforma_id}/payment', data={'amount': amount, 'method': 'bank_transfer'}).status_code == 302

    part = _page(client, project_id)['part']
    assert (part['source']['kind'], part['quote'], part['base'], part['invoiced'], part['advances']) == \
        ('Proforma Invoice', quote_no, 45000.0, 0.0, [20000.0, 15000.0])
    assert part['tax'] == {'mode': 'cgst_sgst', 'rate': 18.0}

    first = _made(client.post(part['action'], data={'target': 'invoice', 'part_percent': '60'}))
    header, summary = _summary(first)
    assert (summary['taxable'], summary['total'], summary['discount']) == (27000.0, 31860.0, None)   # the discount is in the prices
    assert _lines(first) == [f'Doors (60% of {quote_no})', f'Guarding frame (60% of {quote_no})']
    assert _advance_on(first) == 20000.0                                       # the ₹15,000 too wouldn't fit in ₹31,860
    client.post(f'/invoices/{first}/finalize')

    part = _page(client, project_id)['part']
    assert (part['invoiced'], part['advances']) == (27000.0, [15000.0])
    over = client.post(part['action'], data={'target': 'invoice', 'part_percent': '50'})     # more than the 40% left
    assert over.status_code == 302 and f'/projects/{project_id}' in over.headers['Location']
    assert len([d for d in _page(client, project_id)['documents'] if d['doc_type'] == 'invoice']) == 1

    second = _made(client.post(part['action'], data={'target': 'invoice', 'part_amount': '18,000'}))   # the rest, by amount
    header, summary = _summary(second)
    assert (summary['taxable'], summary['total']) == (18000.0, 21240.0)
    assert _lines(second) == [f'Doors (40% of {quote_no})', f'Guarding frame (40% of {quote_no})']
    assert _advance_on(second) == 15000.0
    client.post(f'/invoices/{second}/finalize')
    page = _page(client, project_id)
    assert page['part'] is None                                                # all of it invoiced
    invoiced = next(c for c in page['progress'] if c['key'] == 'invoiced')
    assert (invoiced['text'], invoiced['tone']) == ('100% · ₹53,100', 'done')
