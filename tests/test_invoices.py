import pytest

from tests.fakedb import ORG_A, ORG_B
from tests.spa import document


def test_view_computes_without_writing(client, login_as, fake_db):
    login_as('U-A', ORG_A)
    assert client.get('/invoices/INV-A').status_code == 200                 # the app's page
    page = document(client, '/invoices/INV-A')['document_html']
    assert fake_db.written() == []
    # stale stored values (999) are replaced by fresh results: 2*10 + 3*5 = 35, +10% tax
    assert '999' not in page
    assert '$38.50' in page


def test_viewer_role_can_view_without_writing(client, login_as, fake_db):
    fake_db.members['U-A'][0]['role'] = 'viewer'
    login_as('U-A', ORG_A)
    assert client.get('/invoices/INV-A').status_code == 200
    assert fake_db.written() == []


def test_recalculate_saves_fresh_results(fake_db):
    from invoice_service import recalculate_invoice

    header = fake_db.invoices['INV-A']
    values = fake_db._values_for('INV-A')
    results = recalculate_invoice('INV-A', header, values)
    assert results[('F-LINE', 1)] == 20
    assert results[('F-LINE', 2)] == 15
    assert fake_db.values[('INV-A', 'F-TOTAL', 0)] == 35
    assert fake_db.values[('INV-A', 'F-GRAND', 0)] == pytest.approx(38.5)
    # Inputs are left alone; only formula cells and the total are written
    saved = {args[1] for proc, args in fake_db.calls if proc == 'sp_save_invoice_value'}
    assert saved <= {'F-LINE', 'F-TOTAL', 'F-TAX', 'F-GRAND'}
    procs = [c[0] for c in fake_db.calls]
    assert procs.index('sp_update_invoice_total') < procs.index('sp_set_invoice_total')
    assert fake_db.calls[-1] == ('sp_set_invoice_total', ('INV-A', 38.5))


def test_build_sections_shape(app, fake_db):
    from invoice_service import build_sections, invoice_summary

    with app.app_context():
        header = fake_db.invoices['INV-A']
        sections = build_sections(header, fake_db._values_for('INV-A'))
        assert list(sections) == ['Items', 'Total']
        items = sections['Items']
        assert items['line_item_headers'] == ['Name', 'Qty', 'Price', 'Total']
        assert [[c['val_number'] for c in row] for row in items['line_item_rows']] == [
            [None, 2, 10, 20], [None, 3, 5, 15]]
        summary = invoice_summary(header, sections, fake_db.payments['INV-A'])
        assert (summary['total'], summary['paid'], summary['balance']) == (pytest.approx(38.5), 10, pytest.approx(28.5))
        assert summary['tax_lines'] == [] and summary['advance'] is None


def test_customer_cannot_see_drafts(client, fake_db):
    fake_db.invoices['INV-A']['status'] = 'draft'
    with client.session_transaction() as s:
        s.update(customer_user_id='CU', customer_id='C-A', customer_email='c@a.com', customer_name='Acme')
    response = client.get('/customer/invoices/INV-A')
    assert response.status_code == 302


def test_customer_sees_own_finalized_invoice(client, fake_db):
    with client.session_transaction() as s:
        s.update(customer_user_id='CU', customer_id='C-A', customer_email='c@a.com', customer_name='Acme')
    response = client.get('/customer/invoices/INV-A')
    assert response.status_code == 200
    assert b'$38.50' in response.data
    assert fake_db.written() == []


def _gst_header(fake_db, **settings):
    return {**fake_db.invoices['INV-A'], 'currency_code': 'INR', **settings}


def test_gst_intra_state_with_pre_tax_advance(app, fake_db):
    """Mirrors proforma 006: 18% GST split CGST/SGST, 50% advance on the pre-tax value."""
    from invoice_service import build_sections, invoice_summary

    # Point the template total at the pre-tax subtotal, as GST templates do
    fake_db.total_field = 'F-TOTAL'
    header = _gst_header(fake_db, tax_mode='cgst_sgst', tax_rate=18, advance_percent=50, advance_basis='pre_tax')
    with app.app_context():
        s = invoice_summary(header, build_sections(header, fake_db._values_for('INV-A')), [])
    assert s['taxable'] == 35
    assert s['tax_lines'] == [{'label': 'CGST', 'rate': 9, 'amount': 3.15}, {'label': 'SGST', 'rate': 9, 'amount': 3.15}]
    assert s['total'] == pytest.approx(41.3)
    assert s['advance'] == {'percent': 50, 'basis': 'pre_tax', 'amount': 17.5}
    assert s['payable_now'] == 17.5
    assert s['words'] == 'INR Seventeen Rupees and Fifty Paise Only'


def test_advance_on_total_and_igst(app, fake_db):
    from invoice_service import build_sections, invoice_summary

    fake_db.total_field = 'F-TOTAL'
    header = _gst_header(fake_db, tax_mode='igst', tax_rate=18, advance_percent=50, advance_basis='total')
    with app.app_context():
        s = invoice_summary(header, build_sections(header, fake_db._values_for('INV-A')), [])
    assert s['tax_lines'] == [{'label': 'IGST', 'rate': 18, 'amount': 6.3}]
    assert s['advance']['amount'] == pytest.approx(20.65)


def test_lut_export_has_no_tax(app, fake_db):
    from invoice_service import build_sections, invoice_summary

    fake_db.total_field = 'F-TOTAL'
    header = {**fake_db.invoices['INV-A'], 'tax_mode': 'lut', 'tax_rate': 18}
    with app.app_context():
        s = invoice_summary(header, build_sections(header, fake_db._values_for('INV-A')), [])
    assert s['tax_lines'] == [] and s['total'] == 35
    assert s['words'] == 'USD Thirty Five Dollars Only'
