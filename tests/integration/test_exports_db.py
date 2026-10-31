"""
Several documents at once against real PostgreSQL (same opt-in as test_app_db.py): a CSV of chosen invoices with
their GST, their PDFs in a ZIP, the payments as a CSV, and only the list's own kinds going in.
"""

import csv
import io
import zipfile

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role


def _rows(response):
    assert response.status_code == 200 and response.headers['Content-Type'].startswith('text/csv')
    assert response.headers['Content-Disposition'].startswith('attachment; filename=')
    return list(csv.DictReader(io.StringIO(response.get_data().decode('utf-8-sig'))))


def test_chosen_invoices_as_a_csv_and_a_zip(client, gst_org):
    customer = _customer(gst_org, 'Hob Arbor Works Pvt Ltd', 'Tamil Nadu', 'India')
    first, n1 = _create(client, gst_org, 'invoice', 'Tax Invoice', customer, [{'description': 'Arbor', 'rate': 10000, 'qty': 2}],
                        tax_mode='cgst_sgst', tax_rate='18')
    second, n2 = _create(client, gst_org, 'invoice', 'Tax Invoice', customer, [{'description': 'Collar', 'rate': 500, 'qty': 1}],
                         tax_mode='cgst_sgst', tax_rate='18')
    quote, _ = _create(client, gst_org, 'quote', 'Quotation', customer, [{'description': 'Arbor', 'price': 10000, 'qty': 1}], tax_mode='none')
    client.post(f'/invoices/{first}/finalize')
    client.post(f'/invoices/{first}/payment', data={'amount': '5000', 'method': 'UPI', 'payment_date': '2026-10-20', 'reference_number': 'UTR 77'})

    rows = _rows(client.post('/invoices/export.csv', data={'ids': [first, second, quote]}))
    assert sorted(r['Number'] for r in rows) == sorted([n1, n2])                       # the quotation isn't an invoice
    one = next(r for r in rows if r['Number'] == n1)
    assert (one['Taxable value'], one['CGST'], one['SGST'], one['IGST'], one['Total']) == ('20000.00', '1800.00', '1800.00', '', '23600.00')
    assert (one['Received'], one['Due'], one['GSTIN'], one['State']) == ('5000.00', '18600.00', '33AAACT2761Q1Z1', 'Tamil Nadu')

    pdfs = client.post('/invoices/export.zip', data={'ids': [first, second]})
    assert pdfs.status_code == 200 and pdfs.headers['Content-Type'] == 'application/zip'
    names = zipfile.ZipFile(io.BytesIO(pdfs.get_data())).namelist()
    assert len(names) == 2 and all(n.endswith('.pdf') for n in names)
    assert client.post('/invoices/export.zip', data={}).status_code == 302              # nothing chosen: back to the list

    paid = _rows(client.post('/payments/export.csv', data={}))
    mine = next(r for r in paid if r['Reference'] == 'UTR 77')
    assert (mine['Document'], mine['Method'], mine['Amount'], mine['Credited (INR)']) == (n1, 'UPI', '5000.00', '5000.00')


def test_who_may_export(client, gst_org):
    customer = _customer(gst_org, 'Hob Arbor Works Pvt Ltd', 'Tamil Nadu', 'India')
    invoice, _ = _create(client, gst_org, 'invoice', 'Tax Invoice', customer, [{'description': 'Arbor', 'rate': 100, 'qty': 1}])
    quote, _ = _create(client, gst_org, 'quote', 'Quotation', customer, [{'description': 'Arbor', 'price': 100, 'qty': 1}], tax_mode='none')
    login(client, VIEWER)
    try:
        assert len(_rows(client.post('/invoices/export.csv', data={'ids': [invoice]}))) == 1      # reading is enough
        login(client, OWNER)
        _set_role(client, VIEWER, 'sales')
        login(client, VIEWER)
        assert client.post('/invoices/export.csv', data={'ids': [invoice]}).status_code in (302, 403)
        assert client.post('/payments/export.csv', data={}).status_code in (302, 403)
        assert len(_rows(client.post('/quotes/export.csv', data={'ids': [quote, invoice]}))) == 1   # their quotations only
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
