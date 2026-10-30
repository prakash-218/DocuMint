"""
Discounts end to end against real PostgreSQL (same opt-in as test_app_db.py): a quotation with a discount on the whole
(an amount) and on a line (a percent), its totals, GST, PDF and page; a revision keeps them; converting keeps them, or
takes them into the prices so the proforma shows net prices and the same total.
"""

import re

from documents import load_json

import pytest

from tests.integration.test_documents_db import PROFILE, _create, _customer, _summary, _template, app, client, org_of  # noqa: F401
from tests.integration.test_app_db import login, pytestmark  # noqa: F401

OTHER_OWNER = 'emily.rodriguez@nexus.com'       # another organization's: its number series are its own


@pytest.fixture
def gst_org(client):
    """An owner logged in, their organization set up as a GST-registered business in Tamil Nadu, with the starter
    templates (as test_documents_db's gst_org, in an organization of its own)."""
    from db import db
    login(client, OTHER_OWNER)
    org_id = org_of(client)
    db.execute_proc('sp_update_organization', (org_id, None, '4 Test Road', 'Chennai', 'Tamil Nadu', '600050', 'India'), fetch=False)
    assert client.post('/settings/profile', data=PROFILE).status_code == 302
    if not any(t['name'] == 'Quotation' for t in db.execute_proc('sp_list_templates', (org_id, False)) or []):
        assert client.post('/settings/profile/starter-templates').status_code == 302
    return org_id

LINES = [{'description': 'Test stand frame', 'price': 250000, 'qty': 1}, {'description': 'Mounting plates', 'price': 30000, 'qty': 1},
         {'description': 'Locating pins', 'price': 2000, 'qty': 1}, {'description': 'Commissioning', 'price': 18000, 'qty': 1}]


def _section(org_id, template_name):
    from db import db
    fields = db.execute_proc('sp_get_template_fields', (_template(org_id, template_name)['template_id'],))
    return next(f['section_id'] for f in fields if f['section_type'] == 'line_item')


def test_discounts_on_a_quotation_and_what_converting_does(client, gst_org):
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Torque Rigs Pvt Ltd', 'Tamil Nadu', 'India')
    try:
        _check(client, org_id, customer)
    finally:
        # its documents go, so the next tests number theirs from the series they set
        for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) or []:
            if d.get('customer_id') == customer:
                db.execute_proc('sp_delete_invoice', (d['invoice_id'],), fetch=False)


def _check(client, org_id, customer):
    section = _section(org_id, 'Quotation')

    # ₹45,000 off ₹3,00,000, then GST on what's left
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, LINES, tax_mode='cgst_sgst', tax_rate='18', discount='45000')
    header, summary = _summary(quote_id)
    assert (summary['subtotal'], summary['discount']['amount'], summary['taxable'], summary['total']) == (300000, 45000, 255000, 300900)
    assert [line['amount'] for line in summary['tax_lines']] == [22950, 22950]
    assert float(header['total_amount']) == 300900                                     # what the lists and statements use
    page = client.get(f'/api/document/{quote_id}').get_json()
    assert 'Less: discount' in page['document_html'] and 'Sub total' in page['document_html']
    pdf = client.get(f'/quotes/{quote_id}/pdf')
    assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf'

    # 10% off one line: its amount is after the discount, and it prints a discount column
    lined_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, LINES, tax_mode='none',
                          **{f'line_discount_{section}_1': '10%'})
    _, lined = _summary(lined_id)
    assert (lined['subtotal'], lined['discount'], lined['total']) == (275000, None, 275000)          # 225000 + 50000
    assert 'Disc.' in client.get(f'/api/document/{lined_id}').get_json()['document_html']
    editor = client.get(f'/api/editor/{lined_id}').get_json()
    items = next(s for s in editor['sections'] if s['type'] == 'line_item')
    assert items['amount_field'] and items['rows'][0]['discount'] == '10%' and editor['discount'] == ''

    # A revision keeps both
    assert client.post(f'/quotes/{quote_id}/finalize').status_code == 302
    response = client.post(f'/quotes/{quote_id}/revise', data={})
    revision = re.search(r'/quotes/([0-9a-f-]{36})/edit', response.headers['Location']).group(1)      # straight into its editor
    assert revision != quote_id and _summary(revision)[1]['total'] == 300900

    # Converting: the same discount on the proforma...
    kept = _convert(client, quote_id, 'keep')
    header, summary = _summary(kept)
    assert load_json(header['details'])['discounts'] == {'document': '45000', 'lines': {}}
    assert (summary['discount']['amount'], summary['taxable'], summary['total']) == (45000, 255000, 300900)

    # ...or taken into its prices: net prices, no discount, the same total
    spread = _convert(client, quote_id, 'spread')
    header, summary = _summary(spread)
    assert 'discounts' not in load_json(header['details'])
    assert (summary['discount'], summary['subtotal'], summary['total']) == (None, 255000, 300900)
    from access import fetch_invoice
    prices = sorted(float(v['val_number']) for v in fetch_invoice(spread)[1] if v.get('field_name') == 'price')
    assert prices[-1] < 250000 and abs(sum(prices) - 255000) < 0.005

    # A line discount spreads into its own line's price
    _, summary = _summary(_convert(client, lined_id, 'spread'))
    assert (summary['discount'], summary['total']) == (None, 275000)


def _convert(client, quote_id, discount):
    """Convert the quotation into a proforma, keeping its discount or taking it into the prices: the proforma's id."""
    response = client.post(f'/quotes/{quote_id}/convert', data={'target': 'proforma', 'discount': discount})
    assert response.status_code == 302
    found = re.search(r'/proformas/([0-9a-f-]{36})/edit', response.headers['Location'])
    assert found, response.headers['Location']                       # into the new proforma's editor
    return found.group(1)
