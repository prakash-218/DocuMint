"""The editor's live preview, in the database: the form as typed, drawn as the document's page shows it (and as its PDF,
email and WhatsApp message), for a new document and one being edited, with nothing saved."""

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, _template, app, client, gst_org  # noqa: F401
from tests.spa import editor, editor_form


def _with_line(page, **cells):
    """The editor's form with its first line item's cells set by field name (description, qty, rate)."""
    form = editor_form(page)
    items = next(s for s in page['sections'] if s['type'] == 'line_item')
    for f in items['fields']:
        if f['name'] in cells:
            form[f"line_item_{items['id']}_1_field_{f['id']}"] = str(cells[f['name']])
    return form


def _count(org_id):
    from db import db
    return len(db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [])


def test_a_new_invoice_as_typed(app, client, gst_org):
    import projects
    customer = _customer(gst_org, 'Gear Cutters Ltd', 'Tamil Nadu', 'India')
    project = projects.create_project(gst_org, customer, 'Hob arbors')
    template = _template(gst_org, 'Tax Invoice')
    page = editor(client, f"/invoices/create?doc_type=invoice&template_id={template['template_id']}&project_id={project}")
    assert page['preview'].endswith('/api/editor/new/invoices/preview')
    form = {**_with_line(page, description='Hob arbor', qty=2, rate=10000), 'customer_id': customer, 'tax_mode': 'cgst_sgst', 'tax_rate': '18'}
    before = _count(gst_org)

    got = client.post(page['preview'], json={'fields': form}).get_json()
    assert got['total'] == 23600 and 'Hob arbor' in got['html'] and 'Gear Cutters Ltd' in got['html'] and 'CGST' in got['html']
    assert got['email']['subject'].startswith('Tax Invoice ') and ' · Hob arbors (PRJ-' in got['email']['subject']
    assert got['whatsapp'].startswith('Dear …,') and '₹23,600' in got['whatsapp']

    pdf = client.post(page['preview'] + '?as=pdf', json={'fields': form})
    assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf' and pdf.data[:4] == b'%PDF'
    assert _count(gst_org) == before                                    # a preview saves nothing


def test_a_draft_being_edited(app, client, gst_org):
    from access import fetch_invoice
    customer = _customer(gst_org, 'Gear Cutters Ltd', 'Tamil Nadu', 'India')
    invoice_id, _ = _create(client, gst_org, 'invoice', 'Tax Invoice', customer, [{'description': 'Drill jig', 'rate': 5000, 'qty': 1}],
                            tax_mode='cgst_sgst', tax_rate='18')
    page = editor(client, f'/invoices/{invoice_id}/edit')
    assert page['preview'].endswith(f'/api/editor/{invoice_id}/preview')
    got = client.post(page['preview'], json={'fields': _with_line(page, qty=3)}).get_json()
    assert got['total'] == 17700 and 'Drill jig' in got['html']
    assert float(fetch_invoice(invoice_id)[0]['total_amount']) == 5900       # still as saved


def test_only_those_who_write_it_see_a_preview(app, client, gst_org):
    from tests.integration.test_sales_role_db import _set_role
    customer = _customer(gst_org, 'Gear Cutters Ltd', 'Tamil Nadu', 'India')
    invoice_id, _ = _create(client, gst_org, 'invoice', 'Tax Invoice', customer, [{'description': 'Drill jig', 'rate': 5000, 'qty': 1}])
    _set_role(client, VIEWER, 'viewer')
    login(client, VIEWER)
    try:
        assert client.post(f'/api/editor/{invoice_id}/preview', json={'fields': {}}).status_code in (302, 403)
    finally:
        login(client, OWNER)
