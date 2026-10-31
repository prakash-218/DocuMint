"""The payments list (payments_view.py): every payment once, on the document it counts on now, with how it came."""
from tests.fakedb import ORG_A


def url(endpoint, **kw):
    return f"{endpoint}:{','.join(f'{k}={v}' for k, v in sorted(kw.items()))}"


PAYMENTS = [
    # an advance still on its proforma, by UPI
    {'payment_id': 'P-1', 'invoice_id': 'PI-1', 'amount': 40000, 'payment_date': '2026-10-28 00:00:00+05:30', 'method': 'UPI',
     'reference_number': '6302 1145 0098', 'advance_of': 'PI-1', 'advance_number': None, 'doc_type': 'proforma',
     'doc_number': 'TF/PI/012/26-27', 'customer_id': 'C-1', 'customer_name': 'Gear Cutters Ltd', 'currency_code': 'INR'},
    # an advance applied to the invoice: it shows there, naming the proforma it came in on
    {'payment_id': 'P-2', 'invoice_id': 'INV-1', 'amount': 25000, 'payment_date': '2026-09-02', 'method': 'bank_transfer',
     'reference_number': None, 'advance_of': 'PI-0', 'advance_number': 'TF/PI/009/26-27', 'doc_type': 'invoice',
     'doc_number': 'TF/INV/058/26-27', 'customer_id': 'C-1', 'customer_name': 'Gear Cutters Ltd', 'currency_code': 'INR'},
    # a foreign payment: the rupees the bank credited go with it
    {'payment_id': 'P-3', 'invoice_id': 'EX-1', 'amount': 1200, 'payment_date': '2026-08-15', 'method': 'SWIFT (foreign remittance)',
     'reference_number': 'FX-55', 'advance_of': None, 'received_amount': 99840, 'received_currency': 'INR', 'doc_type': 'export_invoice',
     'doc_number': 'TF/EX/003/26-27', 'customer_id': 'C-2', 'customer_name': 'Hydro Parts Inc', 'currency_code': 'USD'},
]
DOCS = [{'invoice_id': 'INV-1', 'project_id': 'PR-7', 'project_no': 7, 'project_title': 'Hob arbor set', 'fiscal_year': '26-27',
         'customer_site': 'Hosur plant'}]


def test_each_payment_with_its_document_and_how_it_came():
    import payments_view
    data = payments_view.build(PAYMENTS, DOCS, url)
    assert [t['key'] for t in data['tabs']] == ['all', 'advance', 'invoice']
    held, applied, foreign = data['rows']
    assert (held['tab'], held['note'], held['date'], held['method'], held['reference']) == \
        ('advance', 'Advance', '2026-10-28', 'UPI', '6302 1145 0098')
    assert held['document'] == {'number': 'TF/PI/012/26-27', 'kind': 'Proforma Invoice', 'url': 'invoices_bp.view_invoice:invoice_id=PI-1'}
    assert held['project'] is None and held['credited'] is None
    assert (applied['tab'], applied['note'], applied['reference'], applied['method']) ==         ('advance', 'Advance on TF/PI/009/26-27', '', 'Bank transfer')                     # an older payment's key, in words
    assert applied['customer'] == {'id': 'C-1', 'name': 'Gear Cutters Ltd', 'site': 'Hosur plant'}
    assert applied['project'] == {'label': 'PRJ-007', 'title': 'Hob arbor set', 'url': 'projects_bp.view_project:project_id=PR-7'}
    assert (foreign['tab'], foreign['currency'], foreign['credited']) == ('invoice', 'USD', {'amount': 99840.0, 'currency': 'INR'})


def test_the_page_and_its_data_are_for_those_who_see_invoices(client, login_as, fake_db):
    login_as('U-A', ORG_A, 'alice@a.com')
    assert client.get('/payments/').status_code == 200
    data = client.get('/api/payments').get_json()
    assert data['title'] == 'Payments' and [(r['amount'], r['method'], r['reference']) for r in data['rows']] == [(10.0, 'Card', 'R1')]
    fake_db.members['U-A'][0]['role'] = 'sales'                   # quotations only: no money
    assert client.get('/api/payments').status_code == 403
