"""
Purchase orders against real PostgreSQL (same opt-in as test_app_db.py): one for a project, to a supplier who isn't
the project's customer; its starter template made the first time; its steps from sent to received; its list, PDF,
message and people; and none of it counted as a sale.
"""

import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _customer, app, client, gst_org  # noqa: F401
from tests.spa import document, editor


def _supplier(client, name):
    response = client.post('/customers/create', data={'name': name, 'is_supplier': '1', 'tax_id': '27AAACT0000T1Z5', 'city': 'Pune',
                                                      'state': 'Maharashtra', 'country': 'India'})
    assert response.status_code == 302
    return response.headers['Location'].rstrip('/').split('/')[-1]


def _make_po(client, org_id, project_id, supplier):
    from db import db
    page = editor(client, f'/purchase-orders/create?project_id={project_id}')
    if page.get('step') == 'template':                                   # the first one makes its template
        link = next(t['href'] for t in page['templates'] if 'Purchase Order' in t['name'])
        page = editor(client, link)
    assert page['step'] == 'editor' and page['customer']['label'] == 'Supplier' and page['customer']['fixed'] is None
    assert [o['id'] for g in page['customer']['groups'] for o in g['options']] == [supplier] or \
        supplier in [o['id'] for g in page['customer']['groups'] for o in g['options']]
    assert page['details']['values'] == {'order_type': 'Bought-out', 'delivery': 'Immediate', 'payment_terms': 'Against delivery'}
    # its GST: the supplier's GSTIN (Maharashtra) is another state from ours (Tamil Nadu)
    assert page['tax_hints'][supplier] == {'mode': 'igst', 'note': 'Maharashtra GSTIN, another state, so IGST'}
    template_id = page['hidden']['template_id']
    fields = db.execute_proc('sp_get_template_fields', (template_id,))
    items = {f['field_name']: f for f in fields if f['section_type'] == 'line_item'}
    section = next(iter(items.values()))['section_id']
    form = {'doc_type': 'purchase_order', 'template_id': template_id, 'customer_id': supplier, 'project_id': project_id,
            'issue_date': '2026-10-31', 'doc_number': page['hidden']['suggested_number'], 'suggested_number': page['hidden']['suggested_number'],
            'detail_order_type': 'Bought-out', 'detail_delivery': 'Immediate', 'detail_payment_terms': 'Against delivery', 'discount': '5%',
            'tax_mode': 'igst', 'tax_rate': '18',
            f'line_item_{section}_1_field_{items["description"]["field_id"]}': 'Hydraulic jack, 5 ton',
            f'line_item_{section}_1_field_{items["qty"]["field_id"]}': '4',
            f'line_item_{section}_1_field_{items["rate"]["field_id"]}': '9500'}
    response = client.post('/purchase-orders/create', data=form)
    assert response.status_code == 302, response.get_data(as_text=True)[:400]
    return re.search(r'/purchase-orders/([0-9a-f-]{36})', response.headers['Location']).group(1)


def test_a_purchase_order_for_a_project_to_a_supplier(app, client, gst_org):
    import projects
    tag = uuid.uuid4().hex[:6]
    customer = _customer(gst_org, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(gst_org, customer, 'Hob arbor set')
    supplier = _supplier(client, f'Clamp Works {tag}')
    po = _make_po(client, gst_org, project_id, supplier)

    props = document(client, f'/purchase-orders/{po}')
    assert props['head']['kind'] == 'Purchase Order' and props['money'] is None
    assert props['list'] == {'label': 'Purchase orders', 'url': '/purchase-orders/'}
    assert client.post(f'/purchase-orders/{po}/finalize').status_code == 302
    props = document(client, f'/purchase-orders/{po}')
    assert props['head']['pill'] == {'text': 'Sent', 'tone': 'wait'}
    labels = [a['label'] for a in props['next']['actions']]
    assert labels[0] == 'Mark confirmed' and 'Cancel the order' in labels
    assert client.post(f'/purchase-orders/{po}/status', data={'status': 'confirmed'}).status_code == 302
    assert [a['label'] for a in document(client, f'/purchase-orders/{po}')['next']['actions']][0] == 'Mark received'

    rows = client.get('/api/documents/purchase-orders').get_json()['rows']
    row = next(r for r in rows if r['id'] == po)
    # 4 × ₹9,500 = ₹38,000, less 5% is ₹36,100, plus 18% IGST
    assert (row['tab'], row['tag']['text'], row['total'], row['customer']['name']) == ('open', 'Confirmed', 42598.0, f'Clamp Works {tag}')

    page = client.get(f'/api/projects/{project_id}').get_json()
    assert [d['invoice_id'] for d in page['purchases']] == [po] and page['purchases'][0]['party'] == f'Clamp Works {tag}'
    assert po not in [d['invoice_id'] for d in page['documents']]                       # not one of the sales
    assert page['stage']['current'] == 'quoted' and page['new_document']['purchase_order']
    assert all(m.get('invoiced', 0) == 0 for m in page['money'])

    pdf = client.get(f'/purchase-orders/{po}/pdf')
    assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf'
    share = client.get(f'/api/document/{po}/share').get_json()
    assert 'Please find our purchase order' in share['body'] and '₹42,598 incl. GST' in share['body'] and share['pay'] is None
    supplier_page = client.get(f'/api/customers/{supplier}').get_json()
    assert po in [d['invoice_id'] for d in supplier_page['documents']]

    home = client.get('/api/home').get_json()
    assert po not in str(home['attention']) and po not in str(home['to_receive'])       # not a sale, nor a draft to send
    assert any(po in (a.get('link') or '') for a in home['recent'])                     # what happened to it shows


def test_who_sees_purchase_orders(app, client, gst_org):
    from tests.integration.test_sales_role_db import _set_role
    login(client, VIEWER)
    try:
        assert client.get('/api/documents/purchase-orders').status_code == 200           # viewers read them
        assert client.post('/purchase-orders/create', data={}).status_code in (302, 403)
        login(client, OWNER)
        _set_role(client, VIEWER, 'sales')
        login(client, VIEWER)
        assert client.get('/api/documents/purchase-orders').status_code == 403           # Sales: quotations only
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
