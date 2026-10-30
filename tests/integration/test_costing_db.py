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
    assert costing.get(costing_id, org_id)['sheet']['items'] == []

    response = client.post(f'/costings/{costing_id}', data=_form(SHEET, action='save'), follow_redirects=True)
    page = response.get_data(as_text=True)
    from tests.spa import screen
    saved = screen(client, f'/api/costings/{costing_id}')
    assert 'Costing saved' in page and 'HEC torqueing station' in [i['name'] for i in saved['sheet']['items']]
    assert 'Hiwin' in [l['make'] for i in saved['sheet']['items'] for l in i['lines']]
    saved = costing.get(costing_id, org_id)
    assert (float(saved['total_cost']), float(saved['total_price'])) == (191300, 220000)
    assert f'/costings/{costing_id}' in [k['url'] for k in client.get(f'/api/projects/{project_id}').get_json()['costings']]

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
        assert client.get(f'/api/costings/{costing_id}').status_code == 403 and client.get('/api/costings/rates').status_code == 403
        assert client.post(f'/costings/{costing_id}/preview', data=_form(SHEET)).status_code == 403
        assert client.get(f'/api/projects/{project_id}').get_json()['costings'] is None
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


def test_shared_costs_a_dollar_quote_and_copying_items(client, gst_org):
    """Design spread over the items, costs in rupees quoted in dollars, and items copied into another costing."""
    import costing
    import projects
    from access import get_org_invoice
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Hydraulics Inc', '', 'United States')
    project_id = projects.create_project(org_id, customer, f'Test powerunit {uuid.uuid4().hex[:5]}')
    costing_id = _new_costing(client, project_id)
    from tests.spa import boot_of, screen
    assert boot_of(client.get(f'/costings/{costing_id}').get_data(as_text=True))              # the app's page
    page = screen(client, f'/api/costings/{costing_id}')
    assert page['urls']['import'] == f'/costings/{costing_id}/import' and page['urls']['library'] == '/costings/library'

    sheet = {'items': [{'key': 'unit1', 'name': 'Powerunit', 'qty': 1, 'cost_each': 600000},
                       {'key': 'tank1', 'name': 'Tank', 'qty': 2, 'cost_each': 50000}],
             'shared': [{'description': 'Design', 'unit_cost': 40000, 'spread': 'equal'},
                        {'description': 'Freight to Chennai port', 'unit_cost': 10000, 'items': ['unit1']}],
             'exchange_rate': '80'}
    usd = _form(sheet, currency='USD', round_to='0')
    preview = client.post(f'/costings/{costing_id}/preview', data=usd).get_json()
    unit, tank = preview['items']
    assert (unit['shared_cost'], tank['shared_cost']) == (30000, 20000)        # 20k design each, 10k freight
    assert unit['cost_total_q'] == 7875 and unit['price'] == 9056.25           # 6,30,000 / 80, + 15%
    assert preview['totals']['cost_base'] == 750000 and preview['totals']['cost'] == 9375

    # No exchange rate, no dollar quote
    no_rate = _form({**sheet, 'exchange_rate': ''}, currency='USD', round_to='0')
    template_id = next(t['template_id'] for t in db.execute_proc('sp_list_templates', (org_id, False)) if t['name'] == 'Quotation')
    response = client.post(f'/costings/{costing_id}', data={**no_rate, 'action': 'quote', 'template_id': template_id},
                           follow_redirects=True)
    assert 'Enter the exchange rate' in response.get_data(as_text=True)
    assert costing.get(costing_id, org_id)['quote_id'] is None

    response = client.post(f'/costings/{costing_id}', data={**usd, 'action': 'quote', 'template_id': template_id})
    quote_id = re.search(r'/quotes/([0-9a-f-]{36})', response.headers['Location']).group(1)
    header, _ = get_org_invoice(quote_id, org_id)
    assert header['currency_code'] == 'USD' and float(header['total_amount']) == 10781.25   # 9,056.25 + 2 x 862.50
    saved = costing.get(costing_id, org_id)
    assert saved['sheet']['exchange_rate'] == 80 and saved['sheet']['cost_currency'] == 'INR'
    assert float(saved['total_cost']) == 9375                                   # in the quote's currency, like the price
    db.execute_proc('sp_delete_invoice', (quote_id,), fetch=False)

    # Copy items into a costing for another project: lines and costs come, keys are new, shared costs stay
    other = projects.create_project(org_id, customer, f'Second unit {uuid.uuid4().hex[:5]}')
    other_id = _new_costing(client, other)
    found = client.get('/costings/library?q=Assembly').get_json()
    assert any(r['costing_id'] == costing_id for r in found)
    assert not any(r['costing_id'] == costing_id for r in client.get('/costings/library?q=nothing-like-it').get_json())
    copied = client.get(f'/costings/{costing_id}/items').get_json()
    assert [it['name'] for it in copied['items']] == ['Powerunit', 'Tank'] and 'key' not in copied['items'][0]
    assert copied['items'][1]['own_cost_each'] == 50000
    client.post(f'/costings/{other_id}/delete')

    # Members don't get any of it
    login(client, MEMBER)
    for url in ('/costings/library', f'/costings/{costing_id}/items', '/costings/rates'):
        assert client.get(url).status_code == 403
    login(client, OWNER)


def test_rates_list_and_spreadsheet_import(client, gst_org):
    import io
    import openpyxl
    import costing
    import projects
    org_id = gst_org
    customer = _customer(org_id, 'Acme Tools Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, f'Bush press {uuid.uuid4().hex[:5]}')
    costing_id = _new_costing(client, project_id)
    client.post(f'/costings/{costing_id}', data=_form(SHEET, action='save'))

    rates = [{'description': 'MS raw material', 'unit': 'kg', 'unit_cost': '90'},
             {'description': 'LM guide with block', 'make': 'Hiwin', 'unit_cost': '34000', 'markup': '10'},
             {'description': 'ms raw material', 'unit': 'kg', 'unit_cost': '88'},          # the same rate again: last wins
             {'description': '  ', 'unit_cost': '5'}]                                    # blank: dropped
    response = client.post('/costings/rates', data={'rates_json': json.dumps(rates)}, follow_redirects=True)
    assert 'Rates saved (2)' in response.get_data(as_text=True)
    saved = costing.rates(org_id)
    assert [(r['description'], r['unit_cost']) for r in saved] == [('LM guide with block', 34000), ('ms raw material', 88)]
    from tests.spa import screen
    page = screen(client, '/api/costings/rates')
    assert 'Raw material MS' in [s['description'] for s in page['suggestions']]   # a costing line not in the list yet
    editor = screen(client, f'/api/costings/{costing_id}')
    assert ('LM guide with block', 'Hiwin') in [(r['description'], r['make']) for r in editor['rates']]   # offered as lines are typed

    # A workbook: the heading row and columns are guessed, nothing is stored
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = 'Costing'
    ws.append(['Breakup'])
    ws.append([])
    ws.append(['S.No', 'Description', 'Specifications', 'Price', 'Qty', 'Total in Rs'])
    ws.append([1, 'Table', 'with reaction', 150000, 1, 150000])
    ws.append([2, 'Pneumatic cylinder', '80 bore', 25000, 1, 25000])
    ws.append([None, 'Total', None, None, None, 175000])
    data = io.BytesIO()
    book.save(data)
    data.seek(0)
    response = client.post(f'/costings/{costing_id}/import', data={'file': (data, 'Costing.xlsx')},
                           content_type='multipart/form-data')
    sheet = response.get_json()['sheets'][0]
    assert sheet['name'] == 'Costing' and sheet['header_row'] == 2
    assert sheet['columns'] == {'name': 1, 'spec': 2, 'price': 3, 'qty': 4, 'amount': 5}
    assert sheet['rows'][3] == [1, 'Table', 'with reaction', 150000, 1, 150000]
    old = client.post(f'/costings/{costing_id}/import', data={'file': (io.BytesIO(b'junk'), 'old.xls')},
                      content_type='multipart/form-data')
    assert old.status_code == 400 and '.xlsx' in old.get_json()['error']
    bad = client.post(f'/costings/{costing_id}/import', data={'file': (io.BytesIO(b'not a zip'), 'bad.xlsx')},
                      content_type='multipart/form-data')
    assert bad.status_code == 400 and 'error' in bad.get_json()
    client.post('/costings/rates', data={'rates_json': '[]'})
    assert costing.rates(org_id) == []
    client.post(f'/costings/{costing_id}/delete')
