"""Every page renders (no template errors) for each kind of visitor."""

import pytest

from tests.fakedb import ORG_A


STAFF_PAGES = [
    '/dashboard/',
    '/invoices/',
    '/invoices/?status=overdue',
    '/invoices/?q=acme',
    '/invoices/create',
    '/invoices/create?template_id=T-A',
    '/invoices/INV-A',
    '/customers/',
    '/customers/create',
    '/customers/C-A',
    '/customers/C-A/edit',
    '/templates/',
    '/templates/create',
    '/templates/T-A',
    '/settings/',
    '/settings/select-org',
    '/settings/organizations/create',
    '/settings/organizations/join',
    '/settings/audit-log',
    f'/settings/organizations/{ORG_A}/edit',
]

PUBLIC_PAGES = ['/', '/auth/login', '/auth/register', '/customer/login', '/does-not-exist']


@pytest.mark.parametrize('path', STAFF_PAGES)
def test_staff_pages_render(client, login_as, path):
    login_as('U-A', ORG_A, 'alice@a.com')
    response = client.get(path)
    assert response.status_code == 200, response.data[:500]
    assert b'DocuMint' in response.data


def test_draft_invoice_edit_page_renders(client, login_as, fake_db):
    fake_db.invoices['INV-A']['status'] = 'draft'
    login_as('U-A', ORG_A, 'alice@a.com')
    assert client.get('/invoices/INV-A/edit').status_code == 200
    assert client.get('/templates/T-A/edit').status_code == 200


def test_logo_and_tab_icons(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    html = client.get('/dashboard/').get_data(as_text=True)
    assert 'img/documint-icon.svg' in html and 'img/favicon.svg' in html and 'img/apple-touch-icon.png' in html
    assert '>DM</span>' not in html
    for name in ('documint-icon.svg', 'documint-mark.svg', 'favicon.svg', 'favicon-32.png', 'apple-touch-icon.png'):
        assert client.get(f'/static/img/{name}').status_code == 200, name
    assert 'img/documint-icon.svg' in client.get('/auth/login').get_data(as_text=True)


@pytest.mark.parametrize('path', PUBLIC_PAGES)
def test_public_pages_render(client, path):
    response = client.get(path)
    assert response.status_code in (200, 404)
    assert b'DocuMint' in response.data
    assert b'</html>' in response.data


def test_customer_portal_pages_render(client):
    with client.session_transaction() as s:
        s.update(customer_user_id='CU', customer_id='C-A', customer_email='c@a.com', customer_name='Acme')
    for path in ('/customer/', '/customer/invoices/INV-A'):
        response = client.get(path)
        assert response.status_code == 200, path
        assert b'Billing portal' in response.data


@pytest.mark.parametrize('doc_type', ['quote', 'proforma', 'invoice', 'export_invoice'])
def test_pdf_templates_render(app, fake_db, doc_type):
    from flask import render_template
    from invoice_service import build_sections, invoice_summary, pdf_fonts

    header = {**fake_db.invoices['INV-A'], 'doc_type': doc_type, 'doc_number': 'X/001',
              'tax_mode': 'cgst_sgst', 'tax_rate': 18, 'currency_code': 'INR',
              'advance_percent': 50 if doc_type == 'proforma' else None,
              'details': '{"buyer_order_no": "PO-77", "subject": "Tools", "terms": "Taxes: 18% GST"}',
              'organization_profile': '{"gstin": "33ABCDE1234F1Z5", "pan": "ABCDE1234F", "bank_name": "HDFC"}'}
    with app.test_request_context():
        sections = build_sections(header, fake_db._values_for('INV-A'))
        html = render_template('pdf/quote.html' if doc_type == 'quote' else 'pdf/grid.html',
                               invoice=header, sections_data=sections, payments=[], fonts=pdf_fonts(),
                               profile={'gstin': '33ABCDE1234F1Z5', 'pan': 'ABCDE1234F', 'bank_name': 'HDFC'},
                               copy='Original Copy' if doc_type == 'invoice' else '', header_height=150,
                               summary=invoice_summary(header, sections, []))
    assert 'X/001' in html
    assert '₹' in html
    assert '-pdf-frame-content: ' + ('letterhead' if doc_type == 'quote' else 'dochead') in html
    if doc_type != 'quote':
        assert 'PO-77' in html and '33ABCDE1234F1Z5' in html and 'CGST' in html
    if doc_type == 'proforma':
        assert 'Against Proforma invoice' in html
    if doc_type == 'invoice':
        assert html.count('Authorised Signatory') == 1 and 'Original Copy' in html     # one copy per render


def test_long_quote_repeats_letterhead_and_keeps_sign_off_together(app, fake_db):
    """A quote that runs past a page: the letterhead tops every page, the pages are numbered, and the
    seal / signature never go over without the closing ("Thanks & regards")."""
    import io
    from flask import render_template
    from pypdf import PdfReader
    import invoice_service
    from invoice_service import build_sections, invoice_summary, pdf_fonts

    header = {**fake_db.invoices['INV-A'], 'doc_type': 'quote', 'doc_number': 'KKR/Q/016/26-27', 'currency_code': 'INR',
              'organization_name': 'Letterhead Works', 'details': '{"subject": "Fixtures", "closing": "We hope you will find our offer suitable."}'}
    stamp = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    with app.test_request_context():
        sections = build_sections(header, fake_db._values_for('INV-A'))
        items = next(s for s in sections.values() if s['type'] == 'line_item')
        items['line_item_rows'] = items['line_item_rows'] * 45
        common = dict(invoice=header, sections_data=sections, payments=[], fonts=pdf_fonts(), page={},
                      profile={'stamp': stamp, 'signature': stamp, 'signatory_name': 'Signatory Name'},
                      summary=invoice_summary(header, sections, []))
        height = invoice_service._flow_height(render_template('pdf/quote.html', measure_header=True, **common))
        pdf = invoice_service._document_pdf('pdf/quote.html', number_if_long=True, **common)
    pages = [p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages]
    assert 40 < height < 120 and len(pages) > 1
    for n, text in enumerate(pages, 1):
        assert 'LETTERHEAD WORKS' in text and f'Page {n} of {len(pages)}' in text
    signed = [t for t in pages if 'Signatory Name' in t]
    assert len(signed) == 1 and 'Thanks & regards' in signed[0] and 'We hope you will find' in signed[0]


def test_dashboard_numbers(client, login_as, fake_db):
    from datetime import date, timedelta
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    fake_db.invoices['INV-A']['issue_date'] = today.isoformat()
    fake_db.invoices['INV-B'] = {**fake_db.invoices['INV-A'], 'invoice_id': 'INV-B', 'status': 'paid',
                                 'issue_date': last_month.isoformat(), 'total_amount': 20, 'paid_amount': 20}
    # Quotes never count as revenue
    fake_db.invoices['Q-1'] = {**fake_db.invoices['INV-A'], 'invoice_id': 'Q-1', 'doc_type': 'quote',
                               'status': 'sent', 'issue_date': today.isoformat(), 'total_amount': 5000}
    login_as('U-A', ORG_A, 'alice@a.com')
    html = client.get('/dashboard/').get_data(as_text=True)
    assert '$28.50' in html        # outstanding = 38.50 total - 10 paid
    assert '+92.5% vs last month' in html
    assert 'Open quotes' in html and '$5,000.00' in html
