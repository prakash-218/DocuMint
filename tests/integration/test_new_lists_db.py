"""
The quotation, proforma and invoice lists against real PostgreSQL (same opt-in as test_app_db.py): each list's rows
from GET /api/documents/<group>, a link from elsewhere opening a tab, and Sales on quotations only.
"""

import html
import json
import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role


def _rows(client, group):
    response = client.get(f'/api/documents/{group}')
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return {r['id']: r for r in response.get_json()['rows']}


def test_each_list_with_where_its_documents_stand(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    customer = _customer(org_id, f'Spline Works {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Spline gauges')
    quote_id, quote_no = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Spline gauge', 'price': 20000, 'qty': 1}],
                                 project_id=project_id, detail_subject='Quotation for the spline gauges')
    invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer, [{'description': 'Spline gauge', 'rate': 20000, 'qty': 1}],
                            project_id=project_id)
    client.post(f'/invoices/{quote_id}/finalize')

    quote = _rows(client, 'quotes')[quote_id]
    assert (quote['number'], quote['subject'], quote['tab'], quote['tag']['text']) == (quote_no, 'Spline gauges', 'sent', 'Sent')
    assert quote['project']['title'] == 'Spline gauges' and quote['url'] == f'/quotes/{quote_id}' and quote['note'] == 'Sent today'
    assert invoice_id not in _rows(client, 'quotes') and quote_id not in _rows(client, 'invoices')
    invoice = _rows(client, 'invoices')[invoice_id]
    assert (invoice['tab'], invoice['tag']['text'], invoice['balance']) == ('draft', 'Draft', None)

    # A link from elsewhere (Home) opens its tab
    page = client.get('/invoices/?status=overdue&q=spline').get_data(as_text=True)
    props = json.loads(html.unescape(re.search(r'data-island="document-list" data-props="([^"]*)"', page).group(1)))
    assert props == {'group': 'invoices', 'tab': 'overdue', 'query': 'spline'}

    # Sales: the quotations list, not the others
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        assert quote_id in _rows(client, 'quotes')
        assert client.get('/api/documents/invoices').status_code == 403 and client.get('/api/documents/proformas').status_code == 403
        assert client.get('/invoices/').status_code == 302 and client.get('/quotes/').status_code == 200
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
