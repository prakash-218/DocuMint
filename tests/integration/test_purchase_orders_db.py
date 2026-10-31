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
    assert [a['label'] for a in document(client, f'/purchase-orders/{po}')['next']['actions']][0] == 'Record what arrived'

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


def test_what_arrived_line_by_line(app, client, gst_org):
    import projects
    from db import db
    tag = uuid.uuid4().hex[:6]
    customer = _customer(gst_org, f'Axle Works {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(gst_org, customer, 'Test rig')
    supplier = _supplier(client, f'Fastener House {tag}')
    po = _make_po(client, gst_org, project_id, supplier)                    # one line: 4 hydraulic jacks
    assert document(client, f'/purchase-orders/{po}')['receiving'] is None    # a draft: nothing to receive yet
    client.post(f'/purchase-orders/{po}/finalize')
    page = document(client, f'/purchase-orders/{po}')
    r = page['receiving']
    assert [(l['description'], l['qty'], l['left']) for l in r['lines']] == [('Hydraulic jack, 5 ton', 4.0, 4.0)] and r['record']
    assert 'Record what arrived' in [a['label'] for a in page['next']['actions']]

    back = client.post(f'/purchase-orders/{po}/receipts', data={'received_on': '2026-11-02', 'challan_no': 'DC-31', 'qty_1': '5'})
    assert back.status_code == 302 and db.execute_proc('sp_list_po_receipts', (po, gst_org)) in (None, [])   # more than ordered
    client.post(f'/purchase-orders/{po}/receipts', data={'received_on': '2026-11-02', 'challan_no': 'DC-31', 'qty_1': '3'})
    page = document(client, f'/purchase-orders/{po}')
    assert (page['status'], page['receiving']['state'], page['receiving']['lines'][0]['left']) == ('confirmed', 'part', 1.0)
    assert page['next']['actions'][0]['label'] == 'Record what arrived'
    client.post(f'/purchase-orders/{po}/receipts', data={'received_on': '2026-11-05', 'challan_no': 'DC-38', 'qty_1': '1'})
    page = document(client, f'/purchase-orders/{po}')
    assert (page['status'], page['receiving']['state'], page['receiving']['record']) == ('received', 'all', None)   # by itself
    assert [d['challan'] for d in page['receiving']['deliveries']] == ['DC-31', 'DC-38']

    client.post(page['receiving']['deliveries'][1]['delete'])                     # the second was a mistake
    page = document(client, f'/purchase-orders/{po}')
    assert (page['status'], page['receiving']['state']) == ('confirmed', 'part')
    rows = client.get('/api/documents/purchase-orders').get_json()['rows']
    assert next(x for x in rows if x['id'] == po)['tab'] == 'open'


def test_a_purchase_order_of_a_costings_lines(app, client, gst_org):
    import projects
    from tests.integration.test_costing_db import _form, _new_costing
    tag = uuid.uuid4().hex[:6]
    customer = _customer(gst_org, f'Press Makers {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(gst_org, customer, 'Test press')
    sheet = {'items': [{'name': 'Test press', 'qty': 2, 'lines': [
        {'description': 'Hydraulic cylinder', 'make': 'Test Make', 'qty': 3, 'unit': 'nos', 'unit_cost': 4200},
        {'description': 'Base plate', 'qty': 1, 'unit_cost': 900},
        {'description': 'Paint', 'qty': 4, 'unit': 'l', 'unit_cost': 350}]}]}
    costing_id = _new_costing(client, project_id)
    assert client.post(f'/costings/{costing_id}', data=_form(sheet)).status_code == 302
    url = client.get(f'/api/costings/{costing_id}').get_json()['urls']['purchase_order']
    assert f'from_costing={costing_id}' in url and f'project_id={project_id}' in url
    key = client.get(f'/api/costings/{costing_id}').get_json()['sheet']['items'][0]['key']

    page = editor(client, f'{url}&lines={key}:0,{key}:2')
    if page.get('step') == 'template':                           # the template's link carries the lines along
        href = next(t['href'] for t in page['templates'] if 'Purchase Order' in t['name'])
        assert 'from_costing=' in href and 'lines=' in href
        page = editor(client, href)
    table = next(s for s in page['sections'] if s['type'] == 'line_item')
    by_name = {f['name']: f['id'] for f in table['fields']}
    rows = [(r['values'][by_name['description']], r['values'][by_name['qty']], r['values'][by_name['unit']], r['values'][by_name['rate']])
            for r in table['rows']]
    assert rows == [('Hydraulic cylinder (Test Make)', '6', 'nos', '4200'), ('Paint', '8', 'l', '350')]   # × 2 presses
    assert page['customer']['label'] == 'Supplier'                                       # still picked in the editor
    other = projects.create_project(gst_org, customer, 'Another job')
    stray = editor(client, url.replace(project_id, other) + f'&lines={key}:0')
    if stray.get('step') == 'template':
        stray = editor(client, next(t['href'] for t in stray['templates'] if 'Purchase Order' in t['name']))
    table = next(s for s in stray['sections'] if s['type'] == 'line_item')
    assert all(not v for r in table['rows'] for v in r['values'].values())               # another project's costing: nothing
