"""
What the classic project and customer pages could do, from the new ones, against real PostgreSQL (same opt-in as
test_app_db.py): adding a customer's document to a project and taking it out, deleting a project, files dropped for
a customer and moved into a project, the portal login, archiving, editing; each form coming back to the new page.
"""

import io
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role

PDF = b'%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n'


def _post(client, path, data, page, **kw):
    response = client.post(path, data=data, headers={'Referer': f'http://localhost{page}'}, **kw)
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return response.headers['Location']


def test_documents_go_in_and_out_of_a_project_and_a_project_goes(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, f'Axle Works {tag}', 'Tamil Nadu', 'India')
    first = projects.create_project(org_id, customer, 'Spline gauges')
    second = projects.create_project(org_id, customer, 'Hob arbor set')
    quote_id, quote_no = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Gauge', 'price': 1000, 'qty': 1}],
                                 tax_mode='none', project_id=first)
    page = client.get(f'/api/projects/{first}').get_json()
    assert page['links']['documents'] == f'/projects/{first}/documents' and page['links']['delete'] == f'/projects/{first}/delete'
    assert page['links']['new_costing'] and page['links']['rates'] and page['addable'] == []

    # Taken out of the first project, it's offered to the second, and added there; both come back to the new page
    assert _post(client, page['links']['documents'], {'invoice_id': quote_id, 'action': 'remove'}, f'/projects/{first}') \
        .endswith(f'/projects/{first}')
    offered = client.get(f'/api/projects/{second}').get_json()['addable']
    assert [(d['invoice_id'], d['number'], d['kind']) for d in offered] == [(quote_id, quote_no, 'Quotation')]
    assert _post(client, f'/projects/{second}/documents', {'invoice_id': quote_id}, f'/projects/{second}').endswith(f'/projects/{second}')
    assert projects.project_of(quote_id, org_id) == second
    assert client.get(f'/api/projects/{second}').get_json()['addable'] == []

    # Deleting the first, from its new page, goes to the new list; from the classic page, to the classic list
    assert _post(client, f'/projects/{first}/delete', {}, f'/projects/{first}').endswith('/projects/')
    assert projects.get_project(first, org_id) is None
    assert _post(client, f'/projects/{second}/delete', {}, f'/projects/{second}/classic').endswith('/projects/classic')
    assert projects.project_of(quote_id, org_id) is None                                  # the document is kept

    try:                                                                                   # viewers: nothing to change
        login(client, VIEWER)
        third = projects.create_project(org_id, customer, 'Collet chuck')
        page = client.get(f'/api/projects/{third}').get_json()
        assert page['links'] == {'documents': None, 'delete': None, 'new_costing': None, 'rates': None} and page['addable'] == []
    finally:
        login(client, OWNER)


def test_customer_files_portal_archive_and_edit_from_the_new_page(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Drill jig')
    page = f'/customers/{customer}'
    data = client.get(f'/api/customers/{customer}').get_json()
    assert data['upload']['action'] == '/projects/files' and 'po' in data['upload']['kinds']
    assert data['portal'] == {'email': None, 'login_url': data['portal']['login_url'], 'create': f'/customers/{customer}/create-portal-account'}
    assert data['links']['archive'] == f'/customers/{customer}/archive'

    # A file dropped for the customer goes in no project, then is moved into one, back on the new page
    assert _post(client, '/projects/files', {'customer_id': customer, 'file': (io.BytesIO(PDF), 'PO 4500 0188.pdf')}, page,
                 content_type='multipart/form-data').endswith(page)
    [group] = client.get(f'/api/customers/{customer}').get_json()['files']
    [row] = group['files']
    assert group['project'] is None and row['kind'] == 'po' and row['customer_id'] == customer and row['move'].endswith('/link')
    assert _post(client, row['move'], {'project_id': project_id}, page).endswith(page)
    assert [f['project_id'] for f in projects.list_attachments(org_id, customer_id=customer)] == [project_id]

    # The portal login, given from the new page
    assert _post(client, f'/customers/{customer}/create-portal-account', {'email': f'buyer@gear{tag}.example', 'password': 'long enough 1'},
                 page).endswith(page)
    assert client.get(f'/api/customers/{customer}').get_json()['portal']['email'] == f'buyer@gear{tag}.example'

    # Archived and restored, back on the new page; edited from it, saved back to it
    assert _post(client, f'/customers/{customer}/archive', {}, page).endswith(page)
    data = client.get(f'/api/customers/{customer}').get_json()
    assert data['customer']['archived'] and data['links']['archive'] == f'/customers/{customer}/unarchive' and data['upload'] is None
    assert _post(client, f'/customers/{customer}/unarchive', {}, page).endswith(page)
    edit = data['links']['edit']
    assert edit == f'/customers/{customer}/edit'
    form = client.get(edit).get_data(as_text=True)
    assert f'action="/customers/{customer}/edit"' in form and f'href="/customers/{customer}"' in form   # cancel goes back too
    assert _post(client, edit, {'name': f'Gear Cutters {tag}', 'city': 'Hosur', 'country': 'India', 'state': 'Tamil Nadu', 'parent_id': ''},
                 f'/customers/{customer}/edit').endswith(page)

    # Sales: no portal, no archiving; viewers: no uploads
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        data = client.get(f'/api/customers/{customer}').get_json()
        assert data['portal'] is None and data['links']['archive'] is None and data['upload'] is not None
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
        login(client, VIEWER)
        assert client.get(f'/api/customers/{customer}').get_json()['upload'] is None
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
