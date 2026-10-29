"""
The Sales role end to end against real PostgreSQL (same opt-in as test_app_db.py): an owner makes a teammate
Sales; they add a customer, a project and a quotation, send it, and never reach invoices.
"""

import re

from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401


def _set_role(client, email, role):
    from db import db
    user = db.execute_proc_single('sp_get_user_by_email', (email,))
    response = client.post('/settings/members/approve', data={'user_id': user['user_id'], 'action': 'change_role', 'role': role})
    assert response.status_code == 302


def test_sales_work_on_quotations_only(client, gst_org):
    import projects
    org_id = gst_org
    # The owner's work for a customer: a quotation and an invoice in one project
    customer = _customer(org_id, 'Gear Cutters Ltd', 'Tamil Nadu', 'India')
    project = projects.create_project(org_id, customer, 'Hob arbor set')
    quote_id, quote_no = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Hob arbor', 'price': 9000, 'qty': 1}],
                                 tax_mode='none', project_id=project)
    invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                                     [{'description': 'Hob arbor', 'rate': 9000, 'qty': 1}], project_id=project)
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        assert client.get('/dashboard/').headers['Location'].endswith('/projects/')

        # They add a customer, start a project and a quotation, and send it
        response = client.post('/customers/create', data={'name': 'Spindle Works', 'city': 'Coimbatore', 'state': 'Tamil Nadu', 'country': 'India'})
        new_customer = re.search(r'/customers/([0-9a-f-]{36})', response.headers['Location']).group(1)
        response = client.post('/projects/new', data={'customer_id': new_customer, 'title': 'Collet chuck'})
        assert response.status_code == 302
        own_quote, _ = _create(client, org_id, 'quote', 'Quotation', new_customer, [{'description': 'Collet chuck', 'price': 4200, 'qty': 2}],
                               tax_mode='none', project_id=projects.list_projects(org_id, new_customer)[0]['project_id'])
        assert client.post(f'/quotes/{own_quote}/finalize').status_code == 302
        from access import fetch_invoice
        assert fetch_invoice(own_quote)[0]['status'] == 'sent'

        # The owner's project and customer show them the quotation, not the invoice or what's owed
        page = client.get(f'/projects/{project}/classic').get_data(as_text=True)
        assert f'/quotes/{quote_id}' in page and f'/invoices/{invoice_id}' not in page and 'Still due' not in page
        page = client.get(f'/customers/{customer}/classic').get_data(as_text=True)
        assert quote_no in page and f'/invoices/{invoice_id}' not in page and 'Outstanding' not in page
        items = client.get('/search/items').get_json()['items']
        assert any(i['url'] == f'/quotes/{quote_id}' for i in items) and not any(invoice_id in i['url'] for i in items)

        # ...and never the invoice itself, nor a quotation turned into one
        for response in (client.get(f'/invoices/{invoice_id}'), client.get(f'/invoices/{invoice_id}/pdf'),
                         client.post(f'/quotes/{quote_id}/convert', data={'target': 'invoice'}), client.get('/emails/')):
            assert response.headers['Location'].endswith('/projects/')
        assert not [d for d in projects.project_documents(project, org_id) if d['doc_type'] == 'invoice' and d['invoice_id'] != invoice_id]
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
