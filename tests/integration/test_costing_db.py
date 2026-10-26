"""Costings: work the prices out, make the quote from them, keep the quote in step; owners and admins only."""

import json
import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _customer, app, client, gst_org  # noqa: F401

MEMBER = 'sarah.martinez@techflow.com'
SHEET = {'items': [
    {'name': 'HEC torqueing station', 'description': 'With reference station', 'qty': 1, 'lines': [
        {'description': 'Raw material MS', 'qty': 900, 'unit': 'kg', 'unit_cost': 85},
        {'description': 'LM guide with block', 'make': 'Hiwin', 'qty': 2, 'unit_cost': 34000, 'markup': 10}]},
    {'name': 'Commissioning support', 'qty': 1, 'unit': 'lot', 'cost_each': 40000},
]}


def _new_costing(client, project_id, **extra):
    response = client.post('/costings/new', data={'project_id': project_id, **extra})
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return re.search(r'/costings/([0-9a-f-]{36})', response.headers['Location']).group(1)


def _form(sheet, **settings):
    return {'title': 'Assembly machine', 'mode': 'build', 'profit_percent': '15', 'round_to': '1000',
            'currency': 'INR', 'sheet_json': json.dumps(sheet), **settings}


def test_costing_to_quote(client, gst_org):
    import costing
    import projects
    from access import get_org_invoice
    from documents import load_json
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Acme Tools Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, f'Assembly machine {uuid.uuid4().hex[:5]}')
    costing_id = _new_costing(client, project_id)

    # Live numbers while editing; nothing is saved by a preview
    preview = client.post(f'/costings/{costing_id}/preview', data=_form(SHEET)).get_json()
    assert preview['totals']['cost'] == 191300 and preview['totals']['price'] == 220000    # 1,74,000 + 46,000
    assert costing.get(costing_id, org_id)['sheet'] == {'items': []}

    response = client.post(f'/costings/{costing_id}', data=_form(SHEET, action='save'), follow_redirects=True)
    page = response.get_data(as_text=True)
    assert 'Costing saved' in page and 'HEC torqueing station' in page and 'Hiwin' in page
    saved = costing.get(costing_id, org_id)
    assert (float(saved['total_cost']), float(saved['total_price'])) == (191300, 220000)
    assert f'/costings/{costing_id}' in client.get(f'/projects/{project_id}').get_data(as_text=True)

    # Make the quote: items and selling prices, never the costs
    template_id = next(t['template_id'] for t in db.execute_proc('sp_list_templates', (org_id, False)) if t['name'] == 'Quotation')
    response = client.post(f'/costings/{costing_id}', data=_form(SHEET, action='quote', template_id=template_id))
    quote_id = re.search(r'/quotes/([0-9a-f-]{36})', response.headers['Location']).group(1)
    header, values = get_org_invoice(quote_id, org_id)
    assert header['doc_type'] == 'quote' and header['status'] == 'draft' and header['project_id'] == project_id
    assert float(header['total_amount']) == 220000
    assert load_json(header['details'])['subject'] == 'Assembly machine'
    texts = {v.get('val_string') for v in values if v.get('val_string')}
    assert 'HEC torqueing station\nWith reference station' in texts and 'lot' in texts
    assert not any('Hiwin' in t or 'Raw material' in t for t in texts)
    assert costing.get(costing_id, org_id)['quote_id'] == quote_id

    # Rework the prices; the draft quote follows
    cheaper = _form(SHEET, profit_percent='10', action='update_quote')
    response = client.post(f'/costings/{costing_id}', data=cheaper)
    assert f'/quotes/{quote_id}' in response.headers['Location']
    header, values = get_org_invoice(quote_id, org_id)
    assert float(header['total_amount']) == 210000                              # 1,66,000 + 44,000
    assert len({v['value_ordinal'] for v in values if v.get('value_ordinal')}) == 2   # no leftover rows

    # Once the quote is sent it stays put: requote from a new version
    client.post(f'/invoices/{quote_id}/finalize')
    response = client.post(f'/costings/{costing_id}', data=cheaper, follow_redirects=True)
    assert 'stays as it is' in response.get_data(as_text=True)
    assert float(get_org_invoice(quote_id, org_id)[0]['total_amount']) == 210000
    v2 = _new_costing(client, project_id, copy_of=costing_id)
    copy = costing.get(v2, org_id)
    assert copy['version'] == 2 and copy['quote_id'] is None and len(copy['sheet']['items']) == 2

    # Work back from what the customer will pay
    back = client.post(f'/costings/{v2}/preview', data=_form(copy['sheet'], mode='target', target_total='2,50,000',
                                                             round_to='0')).get_json()
    assert back['totals']['price'] == 250000 and back['totals']['budget'] == round(250000 / 1.15, 2)

    client.post(f'/costings/{v2}/delete')
    assert costing.get(v2, org_id) is None

    # Members and viewers never see costings
    for email in (MEMBER, VIEWER):
        login(client, email)
        assert client.get(f'/costings/{costing_id}').status_code == 403
        assert client.post(f'/costings/{costing_id}/preview', data=_form(SHEET)).status_code == 403
        assert 'Costings' not in client.get(f'/projects/{project_id}').get_data(as_text=True)
    login(client, OWNER)

    # The quote took the next quote number; give it back for the document tests that expect it
    db.execute_proc('sp_delete_invoice', (quote_id,), fetch=False)
    assert costing.get(costing_id, org_id)['quote_id'] is None                  # the costing lets go of it


def test_numbers_already_typed_in_are_skipped(client, gst_org):
    """A document numbered by hand doesn't move the series on; the next number handed out skips it."""
    import costing
    import projects
    from access import get_org_invoice
    from db import db
    from document_service import get_org_profile, preview_number
    org_id = gst_org
    _, profile = get_org_profile(org_id)
    customer = _customer(org_id, 'Acme Tools Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, f'Numbering {uuid.uuid4().hex[:5]}')
    template_id = next(t['template_id'] for t in db.execute_proc('sp_list_templates', (org_id, False)) if t['name'] == 'Quotation')

    upcoming = preview_number(org_id, 'quote', profile)                         # TF/Q/027/26-27
    blocker = db.execute_proc('sp_create_invoice', (org_id, customer, template_id, None, None))[0]['invoice_id']
    db.execute_proc('sp_init_document', (blocker, org_id, 'quote', upcoming, None, None), fetch=False)   # typed in
    try:
        assert preview_number(org_id, 'quote', profile) != upcoming                 # the form suggests the next free one
        costing_id = _new_costing(client, project_id)
        response = client.post(f'/costings/{costing_id}', data=_form(SHEET, action='quote', template_id=template_id))
        quote_id = re.search(r'/quotes/([0-9a-f-]{36})', response.headers['Location']).group(1)
        number = get_org_invoice(quote_id, org_id)[0]['doc_number']
        assert number != upcoming and number.startswith('TF/Q/')
        db.execute_proc('sp_delete_invoice', (quote_id,), fetch=False)
    finally:
        db.execute_proc('sp_delete_invoice', (blocker,), fetch=False)
