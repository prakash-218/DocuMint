"""
Projects and customer documents against real PostgreSQL (same opt-in as test_app_db.py).
"""

import re

from tests.integration.test_documents_db import (_create, _customer, _template, app, client,  # noqa: F401
                                                    gst_org)
from tests.integration.test_app_db import VIEWER, login, pytestmark  # noqa: F401

PDF = b'%PDF-1.4\n% customer purchase order\n'


def _new_id(response):
    return re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)


def test_quote_to_invoice_builds_a_project_with_the_po(client, gst_org):
    import io
    import projects
    from access import fetch_invoice
    from documents import load_json
    from document_service import get_org_profile, set_next_number
    org_id = gst_org
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 900)
    customer = _customer(org_id, 'Sundram Fasteners Ltd', 'Tamil Nadu', 'India')
    # A quotation starts from a project: "New quotation" asks for one first
    assert 'Choose a project' in client.get('/quotes/create').get_data(as_text=True)
    response = client.post('/projects/new', data={'customer_id': customer, 'title': 'Drill jig for bracket', 'next': 'quote'})
    new_project = re.search(r'project_id=([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert '/quotes/create' in response.headers['Location']
    form = client.get(f'/quotes/create?project_id={new_project}&template_id={_template(org_id, "Quotation")["template_id"]}')
    assert 'value="Drill jig for bracket"' in form.get_data(as_text=True)          # subject from the project
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer,
                          [{'description': 'Drill jig', 'price': 40000, 'qty': 1}],
                          tax_mode='none', detail_subject='Drill jig for bracket', project_id=new_project)
    page = client.get(f'/quotes/{quote_id}').get_data(as_text=True)
    assert 'Drill jig for bracket' in page and 'PRJ-' in page
    client.post(f'/invoices/{quote_id}/finalize')
    # ...and can't be saved without one
    no_project = client.post('/quotes/create', data={'doc_type': 'quote', 'customer_id': customer,
                                                 'template_id': _template(org_id, 'Quotation')['template_id']})
    assert no_project.headers['Location'].endswith('/quotes/create?doc_type=quote')

    # Converting keeps the proforma in the quotation's project
    proforma_id = _new_id(client.post(f'/invoices/{quote_id}/convert', data={
        'target': 'proforma', 'template_id': _template(org_id, 'Proforma Invoice')['template_id']}))
    project_id = projects.project_of(quote_id, org_id)
    assert project_id and projects.project_of(proforma_id, org_id) == project_id
    project = projects.get_project(project_id, org_id)
    assert project['title'] == 'Drill jig for bracket' and project['customer_id'] == customer

    # Their PO, uploaded to the project, fills the draft proforma's buyer's order no. / date
    response = client.post('/projects/files', data={
        'project_id': project_id, 'kind': 'po', 'reference_no': '4500012345', 'doc_date': '2026-10-20', 'amount': '40,000',
        'file': (io.BytesIO(PDF), 'PO 4500012345.pdf')}, content_type='multipart/form-data',
        headers={'Referer': f'http://localhost/projects/{project_id}'})
    assert response.status_code == 302
    details = load_json(fetch_invoice(proforma_id)[0].get('details'))
    assert details['buyer_order_no'] == '4500012345' and details['buyer_order_date'] == '2026-10-20'
    [po] = projects.list_attachments(org_id, project_id=project_id)
    assert po['kind'] == 'po' and po['title'] == 'Purchase order' and float(po['amount']) == 40000

    # The file opens inline as a PDF, never sniffed
    download = client.get(f'/projects/files/{po["attachment_id"]}')
    assert download.status_code == 200 and download.data == PDF
    assert download.mimetype == 'application/pdf' and download.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'attachment' in client.get(f'/projects/files/{po["attachment_id"]}?download=1').headers['Content-Disposition']

    # Proforma -> invoice: still in the project; the project page shows all three and the PO
    client.post(f'/invoices/{proforma_id}/finalize')
    invoice_id = _new_id(client.post(f'/invoices/{proforma_id}/convert', data={
        'target': 'invoice', 'template_id': _template(org_id, 'Tax Invoice')['template_id']}))
    assert projects.project_of(invoice_id, org_id) == project_id
    assert load_json(fetch_invoice(invoice_id)[0].get('details'))['buyer_order_no'] == '4500012345'
    project_page = client.get(f'/projects/{project_id}').get_data(as_text=True)
    assert all(n in project_page for n in ('Drill jig for bracket', 'PO 4500012345', 'Quotations', 'Proforma invoices'))
    assert len(projects.project_documents(project_id, org_id)) == 3
    assert 'Drill jig for bracket' in client.get('/projects/').get_data(as_text=True)
    assert 'PO 4500012345.pdf' in client.get(f'/customers/{customer}').get_data(as_text=True)

    # A new document made from the project page belongs to it and starts with the PO number
    template_id = _template(org_id, 'Tax Invoice')['template_id']
    create = client.get(f'/invoices/create?doc_type=invoice&template_id={template_id}&project_id={project_id}').get_data(as_text=True)
    assert 'value="4500012345"' in create and 'Sundram Fasteners' in create and 'Select a customer' not in create
    extra_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                          [{'description': 'Spare bush', 'rate': 500, 'qty': 2}], project_id=project_id)
    assert projects.project_of(extra_id, org_id) == project_id

    # Taking a document out, and deleting the project, keep the documents and files
    client.post(f'/projects/{project_id}/documents', data={'invoice_id': extra_id, 'action': 'remove'})
    assert projects.project_of(extra_id, org_id) is None
    assert client.post(f'/projects/{project_id}/delete').status_code == 302
    assert projects.get_project(project_id, org_id) is None and projects.project_of(invoice_id, org_id) is None
    assert projects.list_attachments(org_id, customer_id=customer)[0]['project_id'] is None

    # "Group them into projects" puts the linked documents back together
    assert projects.ungrouped_families(org_id) >= 1
    client.post('/projects/group-linked')
    regrouped = projects.project_of(quote_id, org_id)
    assert regrouped and projects.project_of(proforma_id, org_id) == regrouped == projects.project_of(invoice_id, org_id)


def test_files_are_checked_and_scoped(client, gst_org):
    import io
    import projects
    org_id = gst_org
    customer = _customer(org_id, 'Sundram Fasteners Ltd', 'Tamil Nadu', 'India')
    bad = client.post('/projects/files', data={'customer_id': customer, 'kind': 'drawing',
                                           'file': (io.BytesIO(b'<script>alert(1)</script>'), 'drawing.html')},
                      content_type='multipart/form-data', follow_redirects=True)
    assert "isn&#39;t supported" in bad.get_data(as_text=True)
    ok = client.post('/projects/files', data={'customer_id': customer, 'kind': 'drawing', 'title': 'Bracket GA',
                                          'file': (io.BytesIO(b'AC1032 dwg'), 'bracket.dwg')},
                     content_type='multipart/form-data')
    assert ok.status_code == 302
    drawing = next(f for f in projects.list_attachments(org_id, customer_id=customer) if f['title'] == 'Bracket GA')
    assert 'attachment' in client.get(f'/projects/files/{drawing["attachment_id"]}').headers['Content-Disposition']
    assert client.get('/projects/files/00000000-0000-0000-0000-000000000000').status_code == 404

    # Viewers can read but not upload or delete
    login(client, VIEWER)
    assert client.get(f'/projects/files/{drawing["attachment_id"]}').status_code == 200
    client.post(f'/projects/files/{drawing["attachment_id"]}/delete')
    assert projects.get_attachment(drawing['attachment_id'], org_id)


def test_ongoing_project_with_earlier_documents(client, gst_org):
    """Work started before DocuMint: a project holding the quote and proforma made earlier, as files."""
    import io
    import projects
    from tests.integration.test_documents_db import _template
    org_id = gst_org
    customer = _customer(org_id, 'Lucas TVS Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Assembly fixture (ongoing)')
    for kind, number, amount in (('our_quote', 'KKR/Q/011/26-27', '85,000'), ('our_proforma', 'PI 004(26-27)', '1,00,300')):
        response = client.post('/projects/files', data={'project_id': project_id, 'kind': kind, 'reference_no': number,
                                                    'doc_date': '2026-06-01', 'amount': amount,
                                                    'file': (io.BytesIO(PDF), f'{number}.pdf')},
                               content_type='multipart/form-data', headers={'Referer': f'http://localhost/projects/{project_id}'})
        assert response.status_code == 302
    page = client.get(f'/projects/{project_id}').get_data(as_text=True)
    assert 'KKR/Q/011/26-27' in page and 'PI 004(26-27)' in page and 'Uploaded' in page
    assert '₹85,000.00' in page                                   # the earlier quote counts as quoted
    stages = projects.project_stages([], projects.list_attachments(org_id, project_id=project_id))
    assert [len(s['uploads']) for s in stages] == [1, 1, 0]

    # The invoice is made in DocuMint, in the same project
    from tests.integration.test_documents_db import _create
    invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                            [{'description': 'Assembly fixture', 'rate': 85000, 'qty': 1}], project_id=project_id)
    assert projects.project_of(invoice_id, org_id) == project_id
    # ...and can't be made without one
    response = client.post('/invoices/create', data={'doc_type': 'invoice', 'customer_id': customer,
                                                     'template_id': _template(org_id, 'Tax Invoice')['template_id']})
    assert '/invoices/create' in response.headers['Location']


def test_project_year_the_picker_and_finding_projects(client, gst_org):
    """A project has a financial year (this one when started, or its earliest document's); the picker gets a
    customer's projects as JSON; the projects page searches loosely and filters by year."""
    import projects
    org_id = gst_org
    customer = _customer(org_id, 'Wheels India Limited', 'Tamil Nadu', 'India')
    other = _customer(org_id, 'Venus Traders', 'Tamil Nadu', 'India')
    this_year = projects.current_fiscal_year(org_id)
    tool = projects.create_project(org_id, customer, 'Drop set for SRB 65 dia tool')
    spindle = projects.create_project(org_id, customer, 'Spindle repair', fiscal_year='25-26')
    projects.create_project(org_id, other, 'Drop set for a press')
    assert projects.get_project(tool, org_id)['fiscal_year'] == this_year

    # The year is set when starting a project, and can be changed (anything not a year is ignored)
    response = client.post('/projects/new', data={'customer_id': customer, 'title': 'Gauge set', 'fiscal_year': '24-25'})
    gauges = re.search(r'/projects/([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert projects.get_project(gauges, org_id)['fiscal_year'] == '24-25'
    edit = {'title': 'Spindle repair', 'reference': '', 'status': 'open', 'notes': ''}
    client.post(f'/projects/{spindle}/edit', data={**edit, 'fiscal_year': '26-27'})
    assert projects.get_project(spindle, org_id)['fiscal_year'] == '26-27'
    client.post(f'/projects/{spindle}/edit', data={**edit, 'fiscal_year': 'next year'})
    assert projects.get_project(spindle, org_id)['fiscal_year'] == '26-27'
    assert 'FY 26-27' in client.get(f'/projects/{spindle}').get_data(as_text=True)

    # The picker's list: the customer's own projects, with their years
    data = client.get(f'/projects/options?customer_id={customer}&exact=1').get_json()
    assert {(p['title'], p['fy']) for p in data['projects']} == {
        ('Drop set for SRB 65 dia tool', this_year), ('Spindle repair', '26-27'), ('Gauge set', '24-25')}
    assert data['this_year'] == this_year and all(p['no'].startswith('PRJ-') for p in data['projects'])
    everyone = client.get('/projects/options').get_json()['projects']
    assert 'Drop set for a press' in {p['title'] for p in everyone}

    # The projects page: a loose search, and a year
    page = client.get('/projects/?status=all&q=drop+st+srb').get_data(as_text=True)
    assert 'Drop set for SRB 65 dia tool' in page and 'Drop set for a press' not in page
    page = client.get(f'/projects/?status=all&customer_id={customer}&fy=24-25').get_data(as_text=True)
    assert 'Gauge set' in page and 'Spindle repair' not in page and '<option value="24-25" selected>' in page

    # A document's page offers the picker, fed by its customer's projects
    invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                            [{'description': 'Drop set', 'rate': 15000, 'qty': 1}], project_id=tool)
    page = client.get(f'/invoices/{invoice_id}').get_data(as_text=True)
    assert 'data-project-picker' in page and f'customer_id={customer}' in page and 'Move to another project' in page
    client.post(f'/projects/for-document/{invoice_id}', data={'project_id': spindle})
    assert projects.project_of(invoice_id, org_id) == spindle
