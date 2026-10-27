"""Advances: received on a proforma, carried to its invoice on conversion, or applied to another invoice."""

import re
import uuid

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401


def _doc(org_id, doc_id):
    from db import db
    return next(d for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) if d['invoice_id'] == doc_id)


def test_advance_on_a_proforma_follows_it_to_the_invoice(client, gst_org):
    import projects
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Wipro Enterprises Pvt Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, f'HEC torquing station {uuid.uuid4().hex[:5]}')
    rows = [{'description': 'HEC torquing station', 'qty': 1, 'rate': 100000}]
    pi1, _ = _create(client, org_id, 'proforma', 'Proforma Invoice', customer, rows, tax_mode='none',
                     advance_percent='20', advance_basis='pre_tax', project_id=project_id)
    pi2, _ = _create(client, org_id, 'proforma', 'Proforma Invoice', customer, rows, tax_mode='none',
                     advance_percent='20', advance_basis='pre_tax', project_id=project_id)

    # Not on a draft; on a finalized PI it's an advance, and the PI stays as it is
    client.post(f'/invoices/{pi1}/payment', data={'amount': '20000'})
    assert float(_doc(org_id, pi1)['paid_amount']) == 0
    for pi in (pi1, pi2):
        assert client.post(f'/invoices/{pi}/finalize').status_code == 302
    page = client.get(f'/proformas/{pi1}').get_data(as_text=True)
    assert 'Record an advance' in page and 'value="20000.00"' in page          # the advance asked for
    client.post(f'/invoices/{pi1}/payment', data={'amount': '20000', 'method': 'NEFT / RTGS', 'reference_number': 'UTR1',
                                                  'payment_date': '2026-04-23'})
    client.post(f'/invoices/{pi2}/payment', data={'amount': '20000', 'reference_number': 'UTR2'})
    assert _doc(org_id, pi1)['status'] == 'sent' and float(_doc(org_id, pi1)['paid_amount']) == 20000
    page = client.get(f'/proformas/{pi1}').get_data(as_text=True)
    assert 'Advances received' in page and 'Advance received' in page and 'Advance still to come' not in page
    money = projects.project_money(projects.project_documents(project_id, org_id))
    assert money['advances'] == {'INR': 40000} and money['received'] == {}

    # Converting PI 1 takes its advance to the invoice
    response = client.post(f'/invoices/{pi1}/convert', data={'target': 'invoice'}, follow_redirects=False)
    invoice_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert float(_doc(org_id, invoice_id)['paid_amount']) == 20000 and float(_doc(org_id, pi1)['paid_amount']) == 0
    page = client.get(f'/proformas/{pi1}').get_data(as_text=True)
    assert 'Applied to' in page
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    assert _doc(org_id, invoice_id)['status'] == 'pending'                     # 20,000 of 1,00,000

    # PI 2's advance is offered to the invoice (same customer and project), and applied
    page = client.get(f'/invoices/{invoice_id}').get_data(as_text=True)
    assert 'Apply an advance' in page and 'Advance on PI' in page
    advance2 = next(a for a in db.execute_proc('sp_list_advances', (pi2,)))
    client.post(f'/invoices/{invoice_id}/advances', data={'payment_id': advance2['payment_id']})
    assert float(_doc(org_id, invoice_id)['paid_amount']) == 40000
    page = client.get(f'/invoices/{invoice_id}').get_data(as_text=True)
    assert page.count('Take off this invoice') == 2 and 'Apply an advance' not in page
    money = projects.project_money(projects.project_documents(project_id, org_id))
    assert money['advances'] == {} and money['received'] == {'INR': 40000} and money['due'] == {'INR': 60000}

    # The rest arrives: paid. Taking an advance off makes it pending again, and puts it back on PI 2
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '60000'})
    assert _doc(org_id, invoice_id)['status'] == 'paid'
    client.post(f"/invoices/{invoice_id}/advances/{advance2['payment_id']}/remove")
    assert _doc(org_id, invoice_id)['status'] == 'pending' and float(_doc(org_id, pi2)['paid_amount']) == 20000
    assert client.post(f"/invoices/{invoice_id}/advances/{advance2['payment_id']}/remove").status_code == 302   # not on it now

    # An advance can't go to another customer's invoice
    other = _customer(org_id, 'Precision Hydraulic Pvt Ltd', 'Tamil Nadu', 'India')
    stranger, _ = _create(client, org_id, 'invoice', 'Tax Invoice', other, rows, tax_mode='none')
    client.post(f'/invoices/{stranger}/advances', data={'payment_id': advance2['payment_id']})
    assert float(_doc(org_id, stranger)['paid_amount']) == 0 and float(_doc(org_id, pi2)['paid_amount']) == 20000

    # Deleting a draft invoice hands its advance back to the proforma
    response = client.post(f'/invoices/{pi2}/convert', data={'target': 'invoice'})
    draft = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert float(_doc(org_id, draft)['paid_amount']) == 20000
    db.execute_proc('sp_delete_invoice', (draft,), fetch=False)
    assert float(_doc(org_id, pi2)['paid_amount']) == 20000

    for doc_id in (stranger, invoice_id, pi2, pi1):
        db.execute_proc('sp_delete_invoice', (doc_id,), fetch=False)
