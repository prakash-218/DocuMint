"""
Suppliers against real PostgreSQL (same opt-in as test_app_db.py): a company is a customer, a supplier or both; each
list shows its own; a site is what its company is; and every company there was stays a customer.
"""

import uuid

from tests.integration.test_app_db import OWNER, app, client, login, org_of, pytestmark  # noqa: F401
from tests.spa import boot_of


def _names(client, kind=''):
    rows = client.get(f'/api/customers{"?kind=" + kind if kind else ""}').get_json()
    return {r['name'] for g in rows['groups'] for r in [g['customer'], *g['sites']]}, rows


def _created(response):
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return response.headers['Location'].rstrip('/').split('/')[-1]


def test_a_company_is_a_customer_a_supplier_or_both(client):
    login(client, OWNER)
    tag = uuid.uuid4().hex[:6]
    form = boot_of(client.get('/customers/create?kind=supplier').get_data(as_text=True))
    assert form is not None
    fresh = client.get('/api/customers/new?kind=supplier').get_json()
    assert (fresh['title'], fresh['values']['is_supplier'], fresh['values']['is_customer'], fresh['kinds']) == ('New supplier', '1', '', True)

    filters = f'Filter Works {tag}'
    _created(client.post('/customers/create', data={'name': filters, 'is_supplier': '1', 'country': 'India'}))
    both = f'Gear Cutters {tag}'
    both_id = _created(client.post('/customers/create', data={'name': both, 'is_customer': '1', 'is_supplier': '1', 'country': 'India'}))
    plain = f'Axle Works {tag}'
    _created(client.post('/customers/create', data={'name': plain, 'country': 'India'}))     # an old form: a customer

    suppliers, data = _names(client, 'supplier')
    customers, _ = _names(client)
    assert (data['title'], data['new_label']) == ('Suppliers', 'New supplier')
    assert {filters, both} <= suppliers and plain not in suppliers
    assert {both, plain} <= customers and filters not in customers

    site = _created(client.post('/customers/create', data={'name': both, 'parent_id': both_id, 'site_name': 'Hosur plant',
                                                           'country': 'India'}))
    assert client.get(f'/api/customers/{site}/form').get_json()['kinds'] is False                   # a site follows its company
    assert 'Hosur plant' in _names(client, 'supplier')[0]

    page = client.get(f'/api/customers/{both_id}').get_json()['customer']
    assert page['kinds'] == {'customer': True, 'supplier': True} and page['list']['label'] == 'Customers'
    client.post(f'/customers/{both_id}/edit', data={'name': both, 'is_supplier': '1', 'country': 'India'})   # no longer a customer
    page = client.get(f'/api/customers/{both_id}').get_json()['customer']
    assert page['kinds'] == {'customer': False, 'supplier': True} and page['list'] == {'label': 'Suppliers', 'href': '/suppliers/'}
    assert both not in _names(client)[0]
    assert client.get('/suppliers/').status_code == 200


def test_companies_there_were_stay_customers(client):
    from db import db
    login(client, OWNER)
    rows = db.execute_proc('sp_list_customers', (org_of(client), True)) or []
    old = [r for r in rows if 'Filter Works' not in r['name'] and 'Gear Cutters' not in r['name']]
    assert old and all(r['is_customer'] for r in old)
