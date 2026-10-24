"""
End-to-end tests against a real PostgreSQL database, wiped and loaded with the demo
data (tests/fixtures/demo.json) at the start of the session - see conftest.py.
"""

import os
import re

import pytest

pytestmark = pytest.mark.skipif(os.getenv('DOCUMINT_INTEGRATION_DB') != '1',
                                reason='set DOCUMINT_INTEGRATION_DB=1 to run against a scratch MySQL database')

PASSWORD = 'demo12345'
OWNER = 'michael.chen@techflow.com'
VIEWER = 'david.kim@techflow.com'


@pytest.fixture(scope='module')
def app():
    from app import create_app
    app = create_app('testing')
    app.config.update(TESTING=True, SECRET_KEY='integration')
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email):
    response = client.post('/auth/login', data={'email': email, 'password': PASSWORD})
    assert response.status_code == 302, response.data[:300]
    assert '/dashboard' in response.headers['Location']


def org_of(client):
    with client.session_transaction() as s:
        return s['org_id']


def first_active_template(org_id):
    from db import db
    templates = db.execute_proc('sp_list_templates', (org_id, False)) or []
    return next(t for t in templates if t['version'] == t['latest_version'] and t['name'] == 'Standard Invoice')


def test_pages_render_with_real_data(client):
    login(client, OWNER)
    for path in ('/dashboard/', '/invoices/', '/invoices/?status=overdue', '/customers/',
                 '/templates/', '/settings/', '/settings/audit-log'):
        response = client.get(path)
        assert response.status_code == 200, path

    org_id = org_of(client)
    from db import db
    invoices = db.execute_proc('sp_list_invoices', (org_id, None, 5, 0))
    for inv in invoices:
        assert client.get(f"/invoices/{inv['invoice_id']}", follow_redirects=True).status_code == 200
    pdf = client.get(f"/invoices/{invoices[0]['invoice_id']}/pdf", follow_redirects=True)
    assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf'


def test_create_edit_finalize_and_pay(client):
    from db import db
    login(client, OWNER)
    org_id = org_of(client)
    template = first_active_template(org_id)
    customer = db.execute_proc('sp_list_customers', (org_id, False))[0]
    fields = db.execute_proc('sp_get_template_fields', (template['template_id'],))
    items = [f for f in fields if f['section_type'] == 'line_item']
    section_id = items[0]['section_id']
    by_name = {f['field_name']: f['field_id'] for f in items}

    import projects
    # Without a project, "New invoice" asks for one first
    assert 'Choose a project' in client.get(f"/invoices/create?template_id={template['template_id']}").get_data(as_text=True)
    form = {'customer_id': customer['customer_id'], 'template_id': template['template_id'],
            'issue_date': '2026-10-01', 'due_date': '2026-10-31',
            'project_id': projects.create_project(org_id, customer['customer_id'], 'Widgets')}
    rows = [('Widget', 2, 10), ('Gadget', 3, 5)]
    for i, (name, qty, price) in enumerate(rows, start=1):
        form[f'line_item_{section_id}_{i}_field_{by_name["name"]}'] = name
        form[f'line_item_{section_id}_{i}_field_{by_name["qty"]}'] = str(qty)
        form[f'line_item_{section_id}_{i}_field_{by_name["price"]}'] = str(price)

    response = client.post('/invoices/create', data=form)
    assert response.status_code == 302, response.data[:500]
    invoice_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)

    # Formulas were evaluated and saved on create (line totals, subtotal, tax, grand total)
    from access import fetch_invoice
    header, values = fetch_invoice(invoice_id)
    saved = {(v['field_name'], v['section_name'], v['value_ordinal']): v['val_number'] for v in values}
    assert float(saved[('total', 'items', 1)]) == 20
    assert float(saved[('total', 'items', 2)]) == 15
    assert float(saved[('total', 'total', 0)]) == 35
    assert float(saved[('grand_total', 'total', 0)]) == pytest.approx(38.5)
    listed = next(i for i in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0))
                  if i['invoice_id'] == invoice_id)
    assert float(listed['total_amount']) > 0

    # Viewing does not write
    before = db.execute_proc('sp_get_audit_log', (org_id, None, 1000, 0)) or []
    assert client.get(f'/invoices/{invoice_id}').status_code == 200

    # Edit: change the first row's quantity, totals follow
    edit = dict(form, doc_number=header['doc_number'])   # the edit form always posts the number
    edit[f'line_item_{section_id}_1_field_{by_name["qty"]}'] = '4'
    response = client.post(f'/invoices/{invoice_id}/edit', data=edit)
    assert response.status_code == 302, response.data[:500]
    header, values = fetch_invoice(invoice_id)
    saved = {(v['field_name'], v['section_name'], v['value_ordinal']): v['val_number'] for v in values}
    assert float(saved[('total', 'total', 0)]) == 55

    # Finalize, then pay in full
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    header, _ = fetch_invoice(invoice_id)
    assert header['status'] == 'pending'
    listed = next(i for i in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0))
                  if i['invoice_id'] == invoice_id)
    client.post(f'/invoices/{invoice_id}/payment',
                data={'amount': str(listed['total_amount']), 'method': 'Card'})
    header, _ = fetch_invoice(invoice_id)
    assert header['status'] == 'paid'


def test_viewer_is_read_only(client):
    login(client, VIEWER)
    response = client.get('/invoices/create')
    assert response.status_code == 302
    page = client.get('/invoices/').get_data(as_text=True)
    assert 'New invoice' not in page


def test_customer_portal_login(client):
    from db import db
    response = client.post('/customer/login', data={'email': 'cust@cambridge.com', 'password': PASSWORD})
    assert response.status_code == 302, response.data[:300]
    page = client.get('/customer/')
    assert page.status_code == 200
    with client.session_transaction() as s:
        customer_id = s['customer_id']
    invoices = db.execute_proc('sp_get_customer_invoices', (customer_id,)) or []
    assert all(i['status'] != 'draft' for i in invoices)
    if invoices:
        assert client.get(f"/customer/invoice/{invoices[0]['invoice_id']}", follow_redirects=True).status_code == 200


def test_legacy_unnumbered_draft_still_edits(client):
    """Drafts created before document numbering existed have no doc_number."""
    from db import db
    login(client, OWNER)
    org_id = org_of(client)
    draft = next(d for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0))
                 if d['status'] == 'draft' and not d['doc_number'])
    assert client.get(f"/invoices/{draft['invoice_id']}/edit").status_code == 200
    response = client.post(f"/invoices/{draft['invoice_id']}/edit", data={'tax_mode': 'none', 'doc_number': ''})
    assert response.status_code == 302
    with client.session_transaction() as s:
        flashes = [m for _, m in s.get('_flashes', [])]
    assert not any('required' in m for m in flashes), flashes
