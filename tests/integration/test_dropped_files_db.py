"""
Files dropped on the new pages against real PostgreSQL (same opt-in as test_app_db.py): several at once, each one's
kind from its name, then what it is and its number said afterwards (a PO's number goes onto the project's drafts).
"""

import io
import uuid

from documents import load_json
from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role

PDF = b'%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n'


def test_dropped_files_then_say_what_they_are(client, gst_org):
    import projects
    from access import fetch_invoice
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, f'Axle Works {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Spline gauges')
    proforma_id, proforma_no = _create(client, org_id, 'proforma', 'Proforma Invoice', customer,
                                       [{'description': 'Spline gauge', 'qty': 1, 'rate': 1000}], tax_mode='none', project_id=project_id)

    # Two files dropped at once, no kind given: each one's from its name, and its own name as its title
    page = f'http://localhost/projects/{project_id}/new'
    response = client.post('/projects/files', data={'project_id': project_id, 'file': [(io.BytesIO(PDF), 'Drg HA-220 rev B.pdf'),
                                                                                      (io.BytesIO(PDF), 'scan 0041.pdf')]},
                           content_type='multipart/form-data', headers={'Referer': page})
    assert response.status_code == 302 and response.headers['Location'].endswith(f'/projects/{project_id}/new')
    files = {f['file_name']: f for f in projects.list_attachments(org_id, project_id=project_id)}
    assert {n: (f['kind'], f['title']) for n, f in files.items()} == {
        'Drg HA-220 rev B.pdf': ('drawing', 'Drg HA-220 rev B.pdf'), 'scan 0041.pdf': ('other', 'scan 0041.pdf')}
    rows = client.get(f'/api/projects/{project_id}').get_json()['files']
    assert all(r['delete'].endswith('/delete') for r in rows)

    # The scan was their PO: saying so, with its number, fills the draft proforma's buyer's order no.
    scan = files['scan 0041.pdf']['attachment_id']
    response = client.patch(f'/api/files/{scan}', json={'kind': 'po', 'reference_no': '4500 0188'})
    assert response.status_code == 200 and response.get_json()['filled'] == [proforma_no]
    assert load_json(fetch_invoice(proforma_id)[0].get('details'))['buyer_order_no'] == '4500 0188'
    [po] = [f for f in projects.list_attachments(org_id, project_id=project_id) if f['attachment_id'] == scan]
    assert (po['kind'], po['reference_no'], po['title']) == ('po', '4500 0188', 'scan 0041.pdf')

    assert client.patch(f'/api/files/{scan}', json={'kind': 'nonsense'}).status_code == 400
    assert client.patch(f'/api/files/{uuid.uuid4()}', json={'kind': 'po'}).status_code == 404
    assert client.patch(f'/api/files/{scan}', data={'kind': 'po'}).status_code == 415             # JSON only
    assert 'data-dropzone' in client.get(f'/proformas/{proforma_id}/new').get_data(as_text=True)

    # Nothing chosen: said so, nothing stored
    client.post('/projects/files', data={'project_id': project_id}, content_type='multipart/form-data', headers={'Referer': page})
    assert len(projects.list_attachments(org_id, project_id=project_id)) == 2

    # Viewers can't; Sales don't see our earlier invoices, so can't make a file one or change one
    our_invoice = files['Drg HA-220 rev B.pdf']['attachment_id']
    assert client.patch(f'/api/files/{our_invoice}', json={'kind': 'our_invoice'}).status_code == 200
    try:
        login(client, VIEWER)
        assert client.patch(f'/api/files/{scan}', json={'kind': 'drawing'}).status_code == 403
        login(client, OWNER)
        _set_role(client, VIEWER, 'sales')
        login(client, VIEWER)
        assert client.patch(f'/api/files/{our_invoice}', json={'kind': 'drawing'}).status_code == 404
        assert client.patch(f'/api/files/{scan}', json={'kind': 'our_invoice'}).status_code == 403
        assert client.patch(f'/api/files/{scan}', json={'kind': 'po', 'reference_no': '4500 0189'}).status_code == 200
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
