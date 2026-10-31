"""
Sharing a document against real PostgreSQL (same opt-in as test_app_db.py): its private link made once, its page and
PDF opened without signing in (a link preview doesn't count as opening it), the UPI QR code once there's a UPI ID,
and the link turned off.
"""

import re

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import PROFILE, _create, _customer, app, client, gst_org  # noqa: F401


def _invoice(client, org_id):
    customer = _customer(org_id, 'Spline Gauges Pvt Ltd', 'Tamil Nadu', 'India')
    invoice_id, number = _create(client, org_id, 'invoice', 'Tax Invoice', customer, [{'description': 'Spline gauge', 'rate': 10000, 'qty': 1}],
                                 tax_mode='cgst_sgst', tax_rate='18')
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    return invoice_id, number


def test_a_link_opens_the_document_until_it_is_turned_off(app, client, gst_org):
    invoice_id, number = _invoice(client, gst_org)
    api = f'/api/document/{invoice_id}/share'
    assert client.get(f'/api/document/{invoice_id}').get_json()['share'] == api
    first = client.get(api).get_json()
    assert first['link'] is None and '[link]' in first['body'] and number in first['body']     # looking makes no link
    assert first['pay'] is None and first['upi_missing'] is True                               # no UPI ID yet

    made = client.post(api, json={}).get_json()
    url = made['link']['url']
    token = url.rsplit('/', 1)[1]
    assert re.fullmatch(r'http://localhost/s/[A-Za-z0-9_-]{43}', url) and url in made['body']
    assert client.post(api, json={}).get_json()['link']['url'] == url                         # one link a document

    public = app.test_client()                                                                 # nobody signed in
    preview = public.get(f'/s/{token}', headers={'User-Agent': 'WhatsApp/2.23.20.0 A'})
    assert preview.status_code == 200 and preview.headers['X-Robots-Tag'] == 'noindex, nofollow'
    page = public.get(f'/s/{token}').get_data(as_text=True)
    assert number in page and '₹11,800.00' in page and 'Pay ₹' not in page                     # no UPI ID: no QR
    assert client.get(api).get_json()['link']['opens'] == 1                                    # the preview didn't count
    pdf = public.get(f'/s/{token}/pdf?download=1')
    assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf'
    assert pdf.headers['Content-Disposition'].startswith('attachment;')

    # a UPI ID: the QR code for what's due, on the dialog, the page and the PDF's page
    assert client.post('/settings/profile', data={**PROFILE, 'upi_id': 'not a upi id'}).status_code == 302
    assert client.get(api).get_json()['pay'] is None                                           # refused, not saved
    assert client.post('/settings/profile', data={**PROFILE, 'upi_id': 'testflow@okaxis'}).status_code == 302
    pay = client.get(api).get_json()['pay']
    assert pay['amount'] == 11800 and pay['link'] == f'upi://pay?pa=testflow@okaxis&pn=TechFlow%20USA&am=11800.00&cu=INR&tn={number}'
    assert pay['qr'].startswith('data:image/png;base64,')
    assert 'Pay ₹11,800.00 by UPI' in public.get(f'/s/{token}').get_data(as_text=True)

    off = client.delete(api, json={}).get_json()
    assert off['link'] is None
    gone = public.get(f'/s/{token}')
    assert gone.status_code == 404 and "This link isn't working" in gone.get_data(as_text=True)
    assert public.get(f'/s/{token}/pdf').status_code == 404
    again = client.post(api, json={}).get_json()['link']['url']
    assert again != url                                                                        # a new link, a new token
    client.post('/settings/profile', data=PROFILE)


def test_only_those_who_may_send_it_share_it(app, client, gst_org):
    invoice_id, _ = _invoice(client, gst_org)
    login(client, VIEWER)
    try:
        assert client.get(f'/api/document/{invoice_id}').get_json()['share'] is None
        assert client.post(f'/api/document/{invoice_id}/share', json={}).status_code == 403
    finally:
        login(client, OWNER)
    assert app.test_client().get('/s/not-a-real-token-but-long-enough-0123456789').status_code == 404
