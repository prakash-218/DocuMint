"""
The new customer page against real PostgreSQL (same opt-in as test_app_db.py): a company and its site, an advance
and the invoice it went to, as GET /api/customers/<id> reports them, and the page's own changes (contacts).
"""

import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role
from tests.integration.test_sites_db import _created_id


def _page(client, customer_id):
    response = client.get(f'/api/customers/{customer_id}')
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return response.get_json()


def _lines(page):
    [account] = page['money']['statement']
    return [(line['text'], line['owed'], line['paid'], line['balance']) for line in account['lines']]


def test_a_company_and_its_site_on_the_new_page(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    name = f'Axle Works {tag}'
    parent = _created_id(client.post('/customers/create', data={'name': name, 'tax_id': '33AAACA1234B1Z5', 'city': 'Chennai',
                                                                'country': 'India', 'parent_id': ''}))
    site = _created_id(client.post('/customers/create', data={'name': name, 'parent_id': parent, 'site_name': 'Hosur plant',
                                                              'city': 'Hosur', 'country': 'India'}))
    project_id = projects.create_project(org_id, site, 'Spline gauges')
    rows = [{'description': 'Spline gauge', 'qty': 1, 'rate': 100000}]
    pi, pi_no = _create(client, org_id, 'proforma', 'Proforma Invoice', site, rows, tax_mode='none', advance_percent='20',
                        advance_basis='pre_tax', project_id=project_id)
    client.post(f'/invoices/{pi}/finalize')
    client.post(f'/invoices/{pi}/payment', data={'amount': '20000', 'method': 'NEFT / RTGS', 'reference_number': 'UTR 1',
                                                 'payment_date': '2026-04-23'})

    # The company: its site, the site's project and proforma, and the advance held (nothing owed yet)
    assert client.get(f'/customers/{parent}').status_code == 200
    page = _page(client, parent)
    assert [(s['name'], s['url']) for s in page['sites']] == [('Hosur plant', f'/customers/{site}')]
    assert [p['title'] for p in page['projects']] == ['Spline gauges'] and page['projects'][0]['url'] == f'/projects/{project_id}'
    assert [(d['number'], d['site']) for d in page['documents']] == [(pi_no, 'Hosur plant')]
    assert page['money']['count'] == 0 and page['money']['advance_held'] == {'INR': 20000}
    assert _lines(page) == [(f'Advance on {pi_no}', 0, 20000, -20000)]
    assert page['links']['add_site'] and page['links']['new_project'] == f'/projects/new?customer_id={parent}'

    # The proforma becomes the invoice, its advance with it: owed 80,000, the advance on the invoice's line
    response = client.post(f'/invoices/{pi}/convert', data={'target': 'invoice'})
    invoice_id = re.search(r'/invoices/([0-9a-f-]{36})', response.headers['Location']).group(1)
    client.post(f'/invoices/{invoice_id}/finalize')
    page = _page(client, site)
    assert page['customer']['parent'] == {'id': parent, 'name': name, 'url': f'/customers/{parent}'}
    assert page['sites'] == [] and page['links']['add_site'] is None
    assert page['money']['count'] == 1 and page['money']['total'] == {'INR': 80000} and page['money']['advance_held'] == {}
    assert page['money']['ages'][0]['total'] == {'INR': 80000} and 'customers' not in page['money']
    number = next(d['number'] for d in page['documents'] if d['invoice_id'] == invoice_id)
    assert _lines(page) == [(f'Advance on {pi_no}, applied to {number}', 0, 20000, -20000),
                            (f'Tax Invoice {number}', 100000, 0, 80000)]
    assert _lines(_page(client, parent)) == _lines(page)                       # the company's account has its site's

    # Contacts: the company's show on the site's page; added, changed and removed from the page
    response = client.post(f'/api/customers/{parent}/contacts', json={'name': 'Ravi Kumar', 'email': f'ravi@axle{tag}.example', 'gets': 'all'})
    assert response.status_code == 201
    contact_id = response.get_json()['contact_id']
    people = _page(client, site)['people']
    assert [(p['name'], p['at_parent'], p['customer_id']) for p in people] == [('Ravi Kumar', True, parent)]
    response = client.post(f'/api/customers/{parent}/contacts/{contact_id}',
                           json={'name': 'Ravi Kumar', 'email': f'ravi@axle{tag}.example', 'role': 'Purchase', 'gets': 'billing'})
    assert response.status_code == 200
    assert [(p['role'], p['gets']) for p in _page(client, parent)['people']] == [('Purchase', 'billing')]
    response = client.post(f'/api/customers/{parent}/contacts', json={'name': 'Ravi again', 'email': f'RAVI@axle{tag}.example'})
    assert response.status_code == 400 and 'already a contact' in response.get_json()['error']
    assert client.post(f'/api/customers/{parent}/contacts', data={'name': 'x'}).status_code == 415     # JSON only
    assert client.delete(f'/api/customers/{site}/contacts/{contact_id}', json={}).status_code == 404   # not the site's
    assert client.delete(f'/api/customers/{parent}/contacts/{contact_id}', json={}).status_code == 200
    assert _page(client, parent)['people'] == []

    # Sales see the customer, not what they owe; viewers change nothing
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        assert client.get(f'/customers/{site}').status_code == 200
        page = _page(client, site)
        assert page['money'] is None and page['documents'] == [] and page['can']['sales']
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
        login(client, VIEWER)
        page = _page(client, site)
        assert not page['can']['edit'] and page['links'] == {'new_project': None, 'new_quote': None, 'edit': None, 'add_site': None, 'archive': None}
        assert client.post(f'/api/customers/{site}/contacts', json={'name': 'x', 'email': 'x@x.example'}).status_code == 403
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')

    assert client.get(f'/api/customers/{uuid.uuid4()}').status_code == 404
    assert client.get('/api/customers/not-an-id').status_code == 404
    assert client.get(f'/customers/{uuid.uuid4()}').status_code == 302
