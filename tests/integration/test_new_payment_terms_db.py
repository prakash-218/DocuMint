"""
Payment terms against real PostgreSQL (same opt-in as test_app_db.py): set on a company in its form, used by its
site, the organization's usual ones for everyone else, and an invoice that goes overdue because of them, as the
invoices list, Home, the customer page and the invoice's page say. Nothing is written on the invoice.
"""

import re
import uuid
from datetime import date, timedelta

from tests.integration.test_app_db import login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, app, client, gst_org  # noqa: F401
from tests.integration.test_sites_db import _created_id


def test_terms_make_an_invoice_overdue_everywhere(client, gst_org):
    import projects
    from document_service import get_org_profile, save_org_profile
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    name = f'Spindle Works {tag}'

    # Terms are whole days, 0 to 365
    refused = client.post('/customers/create', data={'name': name, 'payment_days': '400'})
    assert refused.status_code == 200 and 'Payment terms are a number of days, 0 to 365.' in refused.get_data(as_text=True)
    company = _created_id(client.post('/customers/create', data={'name': name, 'city': 'Coimbatore', 'country': 'India',
                                                                 'payment_days': '30'}))
    site = _created_id(client.post('/customers/create', data={'name': name, 'parent_id': company, 'site_name': 'Hosur plant',
                                                              'city': 'Hosur', 'country': 'India', 'payment_days': ''}))
    assert 'value="30"' in client.get(f'/customers/{company}/edit').get_data(as_text=True)
    assert client.get(f'/api/customers/{company}').get_json()['customer']['payment_terms'] == '30 days'
    assert client.get(f'/api/customers/{site}').get_json()['customer']['payment_terms'] == f'30 days, as {name}'

    # An invoice to the site 40 days ago is 10 days late: on the list, on Home and on its page
    project_id = projects.create_project(org_id, site, 'Spindle repair')
    issued = date.today() - timedelta(days=40)
    invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', site, [{'description': 'Spindle repair', 'rate': 50000, 'qty': 1}],
                            project_id=project_id, issue_date=issued.isoformat())
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    row = next(r for r in client.get('/api/documents/invoices').get_json()['rows'] if r['id'] == invoice_id)
    assert (row['tab'], row['note'], row['until']) == ('overdue', '10 days late', (issued + timedelta(days=30)).isoformat())
    home = client.get('/api/home').get_json()
    overdue = next(g for g in home['attention'] if g['key'] == 'overdue')
    late = [int(re.search(r'(\d+) days? late', i['sub']).group(1)) for i in overdue['items']]
    assert late == sorted(late, reverse=True)                                     # the most late first
    assert any(i['url'] == f'/invoices/{invoice_id}' and '10 days late' in i['sub'] for i in overdue['items']) or late[-1] >= 10
    assert overdue['more_url'] == '/invoices/?status=overdue'
    page = client.get(f'/invoices/{invoice_id}').get_data(as_text=True)
    assert '10 days late: it was due on' in page
    from access import fetch_invoice
    assert fetch_invoice(invoice_id)[0]['due_date'] is None                       # nothing written on the invoice

    # Without terms of their own, the organization's usual ones; "on receipt" is 0
    loner = _created_id(client.post('/customers/create', data={'name': f'Axle Works {tag}', 'country': 'India'}))
    assert client.get(f'/api/customers/{loner}').get_json()['customer']['payment_terms'] == ''
    profile = get_org_profile(org_id)[1]
    try:
        save_org_profile(org_id, {**profile, 'payment_days': 0})
        assert client.get(f'/api/customers/{loner}').get_json()['customer']['payment_terms'] == 'On receipt (your usual terms)'
        assert f'your usual terms (On receipt)' in client.get(f'/customers/{loner}/edit').get_data(as_text=True)
    finally:
        save_org_profile(org_id, profile)
