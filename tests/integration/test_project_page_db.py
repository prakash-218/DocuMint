"""
The new project page against real PostgreSQL (same opt-in as test_app_db.py): a job from quotation to paid,
as GET /api/projects/<id> reports it at each step, and the page's own changes (notes, people, details).
"""

import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role


def _page(client, project_id):
    response = client.get(f'/api/projects/{project_id}')
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return response.get_json()


def _where(page):
    return page['stage']['current'], [a['label'] for a in page['next']['actions'] if a['primary']]


def _run(client, action):
    """Do what a 'post' action on the page does: its form, to its address."""
    response = client.post(action['action'], data=action['fields'])
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return response.headers['Location']


def test_a_job_from_quotation_to_paid(client, gst_org):
    import projects
    from db import db
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Hob arbor set')
    assert client.get(f'/projects/{project_id}/new').status_code == 200
    assert _where(_page(client, project_id)) == ('quoted', ['New quotation'])

    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Hob arbor', 'price': 10000, 'qty': 1}],
                          tax_mode='none', project_id=project_id)
    assert _where(_page(client, project_id)) == ('quoted', ['Edit quotation'])
    client.post(f'/quotes/{quote_id}/finalize')
    page = _page(client, project_id)
    assert _where(page) == ('accepted', ['Mark accepted'])
    assert page['money'][0]['quoted'] == 10000 and page['documents'][0]['status'] == 'sent'

    _run(client, page['next']['actions'][0])                                   # the customer said yes
    page = _page(client, project_id)
    assert _where(page) == ('advance', ['Raise proforma for the advance'])
    edit = _run(client, page['next']['actions'][0])                            # proforma from the quotation
    proforma_id = re.search(r'([0-9a-f-]{36})', edit).group(1)
    assert _where(_page(client, project_id)) == ('advance', ['Edit proforma'])
    client.post(f'/proformas/{proforma_id}/finalize')
    assert _where(_page(client, project_id)) == ('advance', ['Record the advance'])
    assert client.post(f'/proformas/{proforma_id}/payment', data={'amount': '4000', 'method': 'bank_transfer'}).status_code == 302

    page = _page(client, project_id)
    steps = {s['key']: s for s in page['stage']['steps']}
    assert steps['advance']['state'] == 'done' and _where(page) == ('invoiced', ['Create tax invoice'])
    assert page['money'][0]['received'] == 4000 and page['money'][0]['advance_held'] == 4000
    edit = _run(client, page['next']['actions'][0])                            # the tax invoice, advance carried
    invoice_id = re.search(r'([0-9a-f-]{36})', edit).group(1)
    client.post(f'/invoices/{invoice_id}/finalize')
    page = _page(client, project_id)
    assert _where(page) == ('paid', ['Record payment']) and page['stage']['pill']['text'] == 'Part paid'
    invoice = next(d for d in page['documents'] if d['invoice_id'] == invoice_id)
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': str(invoice['balance']), 'method': 'bank_transfer'})

    page = _page(client, project_id)
    assert page['stage']['current'] is None and page['stage']['pill']['text'] == 'Paid'
    assert [a['label'] for a in page['next']['actions']] == ['Mark the project completed']

    # The page's own changes: complete it, a note, the details, a contact and what they get
    assert client.patch(f'/api/projects/{project_id}', json={'status': 'completed'}).status_code == 200
    assert client.post(f'/api/projects/{project_id}/notes', json={'text': 'Delivered 3 sets.\nDC 118 signed.'}).status_code == 201
    response = client.patch(f'/api/projects/{project_id}', json={'title': 'Hob arbor set (3 nos)', 'reference': 'PO 4500 0188'})
    assert response.status_code == 200
    assert client.patch(f'/api/projects/{project_id}', json={'title': ' '}).get_json() == {'error': 'Give the project a name.'}
    response = client.post(f'/api/projects/{project_id}/contacts', json={'name': 'Ravi Kumar', 'email': f'ravi@gearco{tag}.example'})
    contact_id = response.get_json()['contact_id']
    assert client.post(f'/api/projects/{project_id}/people', json={'contact_id': contact_id, 'gets': 'billing'}).status_code == 200
    page = _page(client, project_id)
    assert page['project']['status'] == 'completed' and page['project']['title'] == 'Hob arbor set (3 nos)'
    assert page['project']['reference'] == 'PO 4500 0188'
    assert page['next']['actions'] == [] and page['timeline'][0]['type'] == 'note'
    assert page['timeline'][0]['title'] == 'Delivered 3 sets.\nDC 118 signed.'
    assert [(p['name'], p['gets'], p['usually']) for p in page['people']] == [('Ravi Kumar', 'billing', 'all')]
    assert page['costings'] == [] and page['can']['manage']

    # Sales see the quotation and no further; viewers see it all and change nothing
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        page = _page(client, project_id)
        assert [s['key'] for s in page['stage']['steps']] == ['quoted', 'accepted']
        assert {d['doc_type'] for d in page['documents']} == {'quote'} and set(page['money'][0]) == {'currency', 'quoted'}
        assert page['costings'] is None and not page['found']['people']
        assert not any(i['kind'] in ('payment', 'document_converted') for i in page['timeline'])
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
        login(client, VIEWER)
        page = _page(client, project_id)
        assert not page['can']['edit'] and page['upload'] is None and page['next']['actions'] == []
        assert client.post(f'/api/projects/{project_id}/notes', json={'text': 'x'}).status_code == 403
        assert client.patch(f'/api/projects/{project_id}', json={'status': 'open'}).status_code == 403
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')

    # Another organization's project isn't there
    assert client.get(f'/api/projects/{uuid.uuid4()}').status_code == 404
    assert db.execute_proc_single('sp_get_project', (project_id, str(uuid.uuid4()))) is None
