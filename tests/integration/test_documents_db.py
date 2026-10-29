"""
Quote -> proforma -> tax invoice, against real MySQL with migrations applied.
Same opt-in as test_app_db.py (DOCUMINT_INTEGRATION_DB=1, scratch database only).
"""

import os
import re
from datetime import date

import pytest

from tests.integration.test_app_db import OWNER, login, org_of, pytestmark  # noqa: F401  (shared skip marker)
from tests.spa import document, document_text


@pytest.fixture(scope='module')
def app():
    from app import create_app
    app = create_app('testing')
    app.config.update(TESTING=True, SECRET_KEY='integration')
    return app


@pytest.fixture
def client(app):
    return app.test_client()


PROFILE = {
    'gstin': '33abcde1234f1z5', 'pan': 'ABCDE1234F', 'default_currency': 'INR', 'default_gst_rate': '18',
    'fy_start_month': '4', 'advance_basis': 'pre_tax', 'bank_name': 'Test Bank',
    'format_quote': 'TF/Q/{num:03}/{fy}', 'format_proforma': 'PI {num:03}({fy})', 'format_invoice': '{num:03}',
    'format_export_invoice': 'EXP-{num:03}', 'next_quote': '27',
}


@pytest.fixture
def gst_org(client):
    """Owner logged in; their org set up as a GST-registered business in Tamil Nadu."""
    from db import db
    login(client, OWNER)
    org_id = org_of(client)
    db.execute_proc('sp_update_organization', (org_id, 'TechFlow USA', '9D Test Street', 'Chennai',
                                               'Tamil Nadu', '600050', 'India'), fetch=False)
    response = client.post('/settings/profile', data=PROFILE)
    assert response.status_code == 302
    assert client.post('/settings/profile/starter-templates').status_code == 302
    return org_id


def _template(org_id, name):
    from db import db
    return next(t for t in db.execute_proc('sp_list_templates', (org_id, False)) if t['name'] == name)


def _customer(org_id, name, state, country):
    from db import db
    existing = next((c for c in db.execute_proc('sp_list_customers', (org_id, False)) if c['name'] == name), None)
    if existing:
        return existing['customer_id']
    row = db.execute_proc_single('sp_create_customer', (org_id, name, '33AAACT2761Q1Z1', 'RS-51/1', 'Pudupakkam',
                                                        state, '603103', country, None))
    return row['customer_id']


def _create(client, org_id, doc_type, template_name, customer_id, rows, **extra):
    from db import db
    template = _template(org_id, template_name)
    fields = db.execute_proc('sp_get_template_fields', (template['template_id'],))
    items = {f['field_name']: f for f in fields if f['section_type'] == 'line_item'}
    section_id = next(iter(items.values()))['section_id']
    if 'project_id' not in extra:                                   # every document belongs to a project
        import projects
        extra['project_id'] = projects.create_project(org_id, customer_id, 'Test project')
    from tests.spa import editor
    suggested = editor(client, f'/invoices/create?doc_type={doc_type}&template_id={template["template_id"]}'
                               f'&project_id={extra.get("project_id", "")}')['hidden']['suggested_number']
    form = {'doc_type': doc_type, 'template_id': template['template_id'], 'customer_id': customer_id,
            'issue_date': date.today().isoformat(), 'doc_number': suggested, 'suggested_number': suggested, **extra}
    for i, row in enumerate(rows, start=1):
        for name, value in row.items():
            form[f'line_item_{section_id}_{i}_field_{items[name]["field_id"]}'] = str(value)
    response = client.post('/invoices/create', data=form)
    assert response.status_code == 302, response.get_data(as_text=True)[:800]
    match = re.search(r"/(?:quotes|proformas|invoices)/([0-9a-f-]{36})", response.headers["Location"])
    assert match, (response.headers["Location"], re.findall(r'class="alert[^"]*"[^>]*>(.*?)</div>', client.get(response.headers["Location"]).get_data(as_text=True), re.S)[:2])
    return match.group(1), suggested


def _summary(invoice_id):
    from access import fetch_invoice
    from invoice_service import build_sections, invoice_summary
    header, values = fetch_invoice(invoice_id)
    return header, invoice_summary(header, build_sections(header, values), [])


def test_quote_to_proforma_to_invoice(client, app, gst_org):
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Farm Gear Works Ltd', 'Tamil Nadu', 'India')

    # Quotation, numbered from the series we set (27), with default terms
    quote_id, number = _create(client, org_id, 'quote', 'Quotation', customer,
                               [{'description': 'Shaft main drive tool', 'price': 5500, 'qty': 2},
                                {'description': 'Transport', 'price': 800, 'qty': 1}],
                               tax_mode='none', detail_kind_attn='Mr. Krishnamoorthi', detail_subject='Quotation for tools',
                               detail_terms='Taxes: 18% GST\nOffer validity - 30 days')
    fy = '{:02d}-{:02d}'.format(*(((date.today().year - (date.today().month < 4)) % 100,
                                   (date.today().year - (date.today().month < 4) + 1) % 100)))
    assert number == f'TF/Q/027/{fy}'
    header, s = _summary(quote_id)
    assert header['doc_type'] == 'quote' and header['doc_number'] == number
    assert s['total'] == 11800
    page = document_text(client, f'/quotes/{quote_id}')
    assert '₹11,800.00' in page and 'Mr. Krishnamoorthi' in page and 'Offer validity' in page

    # Quotes never count as revenue, even once sent
    assert client.post(f'/invoices/{quote_id}/finalize').status_code == 302
    assert client.post(f'/invoices/{quote_id}/status', data={'status': 'accepted'}).status_code == 302
    header, _ = _summary(quote_id)
    assert header['status'] == 'accepted'

    # Convert to a proforma on the GST template: values copy across by field name
    response = client.post(f'/invoices/{quote_id}/convert',
                           data={'target': 'proforma', 'template_id': _template(org_id, 'Proforma Invoice')['template_id']})
    assert response.status_code == 302, response.get_data(as_text=True)[:500]
    proforma_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    header, _ = _summary(quote_id)
    assert header['status'] == 'converted'

    # Set GST + 50% advance on the pre-tax value via the edit form (as a person would)
    edit_page = client.get(f'/proformas/{proforma_id}/edit')
    assert edit_page.status_code == 200
    p_header, _ = _summary(proforma_id)
    assert p_header['doc_number'] == f'PI 001({fy})'
    assert p_header['source_invoice_id'] == quote_id
    from access import fetch_invoice
    _, values = fetch_invoice(proforma_id)
    fields = db.execute_proc('sp_get_template_fields', (p_header['template_id'],))
    items = {f['field_name']: f for f in fields if f['section_type'] == 'line_item'}
    section_id = next(iter(items.values()))['section_id']
    form = {'doc_number': p_header['doc_number'], 'tax_mode': 'cgst_sgst', 'tax_rate': '18',
            'advance_percent': '50', 'advance_basis': 'pre_tax', 'detail_buyer_order_no': '2010031535',
            'issue_date': date.today().isoformat()}
    rows = {}
    for v in values:
        if v['section_type'] == 'line_item' and v['field_name'] in ('description', 'qty', 'rate'):
            rows.setdefault(v['value_ordinal'], {})[v['field_name']] = v['val_string'] or v['val_number']
    for ordinal, row in rows.items():
        for name, value in row.items():
            form[f'line_item_{section_id}_{ordinal}_field_{items[name]["field_id"]}'] = str(value)
        form[f'line_item_{section_id}_{ordinal}_field_{items["hsn_sac"]["field_id"]}'] = '84629190'
    assert client.post(f'/invoices/{proforma_id}/edit', data=form).status_code == 302

    p_header, s = _summary(proforma_id)
    assert s['taxable'] == 11800
    assert [line['amount'] for line in s['tax_lines']] == [1062, 1062]
    assert s['total'] == 13924
    assert s['advance']['amount'] == 5900          # 50% of the pre-tax value
    assert s['words'] == 'INR Five Thousand Nine Hundred Rupees Only'
    assert s['hsn'][0]['hsn'] == '84629190' and s['hsn'][0]['taxable'] == 11800
    listed = next(d for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) if d['invoice_id'] == proforma_id)
    assert float(listed['total_amount']) == 13924   # stored total includes GST
    assert client.post(f'/invoices/{proforma_id}/finalize').status_code == 302

    # Proforma -> tax invoice; GST settings carry over, advance doesn't
    response = client.post(f'/invoices/{proforma_id}/convert', data={'target': 'invoice'})
    invoice_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    i_header, s = _summary(invoice_id)
    assert i_header['doc_type'] == 'invoice' and i_header['tax_mode'] == 'cgst_sgst'
    assert s['advance'] is None and s['total'] == 13924
    from documents import load_json
    assert load_json(i_header['details']).get('buyer_order_no') == '2010031535'

    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    # Paying the pre-tax amount leaves the GST due: the total keeps its tax and the invoice stays pending
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '11800', 'method': 'NEFT / RTGS'})
    i_header, _ = _summary(invoice_id)
    assert (float(i_header['total_amount']), i_header['status']) == (13924, 'pending')
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': '2124', 'method': 'NEFT / RTGS'})
    i_header, _ = _summary(invoice_id)
    assert (float(i_header['total_amount']), i_header['status']) == (13924, 'paid')

    # Every document renders, and every PDF generates
    for doc_id in (quote_id, proforma_id, invoice_id):
        assert client.get(f'/invoices/{doc_id}', follow_redirects=True).status_code == 200
        pdf = client.get(f'/invoices/{doc_id}/pdf', follow_redirects=True)
        assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf', doc_id

    # Lists are split by type
    assert client.get('/invoices/?type=quote').headers['Location'].endswith('/quotes/')   # old links
    from tests.spa import boot_of
    assert boot_of(client.get('/quotes/').get_data(as_text=True))                   # the React app's page
    listed = [r['number'] for r in client.get('/api/documents/quotes').get_json()['rows']]
    assert number in listed and p_header['doc_number'] not in listed
    assert client.get('/dashboard/').status_code == 200


def test_duplicate_number_is_rejected(client, gst_org):
    org_id = gst_org
    customer = _customer(org_id, 'Farm Gear Works Ltd', 'Tamil Nadu', 'India')
    first, number = _create(client, org_id, 'invoice', 'Proforma Invoice', customer,
                            [{'description': 'Bush', 'rate': 100, 'qty': 1}], tax_mode='cgst_sgst', tax_rate='18')
    from db import db
    template = _template(org_id, 'Proforma Invoice')
    import projects
    response = client.post('/invoices/create', data={
        'doc_type': 'invoice', 'template_id': template['template_id'], 'customer_id': customer,
        'project_id': projects.create_project(org_id, customer, 'Duplicate test'),
        'doc_number': number, 'suggested_number': 'something-else', 'tax_mode': 'none'})
    assert response.status_code == 302
    with client.session_transaction() as s:
        flashes = [m for _, m in s.get('_flashes', [])]
    assert any('already used' in m for m in flashes), flashes
    same = [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0))
            if d['doc_type'] == 'invoice' and d['doc_number'] == number]
    assert len(same) == 1


def test_export_invoice_suggests_lut(client, gst_org):
    org_id = gst_org
    customer = _customer(org_id, 'Hydro Parts Inc', 'Pennsylvania', 'United States of America')
    # There's no "export invoice" to pick: an invoice made with the export template is one
    import projects
    project_id = projects.create_project(org_id, customer, 'Export test')
    from tests.spa import editor
    assert 'export_invoice' not in [k['key'] for k in editor(client, f'/invoices/create?project_id={project_id}')['kinds']]
    page = editor(client, f'/invoices/create?doc_type=invoice&project_id={project_id}&template_id={_template(org_id, "Export Invoice")["template_id"]}')
    assert page['tax_hints'][customer] == 'lut' and 'Packing list no.' in [f['label'] for f in page['details']['fields']]
    tax_form = editor(client, f'/invoices/create?doc_type=invoice&project_id={project_id}&template_id={_template(org_id, "Tax Invoice")["template_id"]}')
    assert 'Packing list no.' not in [f['label'] for f in tax_form['details']['fields']]
    export_id, _ = _create(client, org_id, 'invoice', 'Export Invoice', customer,
                           [{'description': 'Toggle clamp', 'rate': 13, 'qty': 10},
                            {'description': 'Transport', 'rate': 579, 'qty': 1}],
                           tax_mode='lut', detail_packing_list_no='PL 029(26-27)', detail_net_weight='39 kg')
    header, s = _summary(export_id)
    assert header['doc_type'] == 'export_invoice'
    assert header['currency_code'] == 'USD' and s['total'] == 709 and s['tax_lines'] == []
    assert s['words'] == 'USD Seven Hundred Nine Dollars Only'
    pdf = client.get(f'/invoices/{export_id}/pdf')
    assert pdf.status_code == 200


def test_quote_revisions(client, gst_org):
    org_id = gst_org
    # The fixture resets the quote series to 27; move this test to its own range
    from document_service import get_org_profile, set_next_number
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 500)
    customer = _customer(org_id, 'Farm Gear Works Ltd', 'Tamil Nadu', 'India')
    quote_id, number = _create(client, org_id, 'quote', 'Quotation', customer,
                               [{'description': 'Gauge', 'price': 1000, 'qty': 2}], tax_mode='none')
    # A draft can't be revised; it's simply edited
    client.post(f'/invoices/{quote_id}/revise')
    header, _ = _summary(quote_id)
    assert header['status'] == 'draft'

    client.post(f'/invoices/{quote_id}/finalize')
    response = client.post(f'/invoices/{quote_id}/revise')
    rev1 = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    r1, s1 = _summary(rev1)
    head, tail = number.rsplit('/', 1)                          # TF/Q/500/26-27 -> TF/Q/500R1/26-27
    rev1_number, rev2_number = f'{head}R1/{tail}', f'{head}R2/{tail}'
    assert r1['doc_number'] == rev1_number and r1['status'] == 'draft' and s1['total'] == 2000
    assert _summary(quote_id)[0]['status'] == 'revised'

    client.post(f'/invoices/{rev1}/finalize')
    response = client.post(f'/invoices/{rev1}/revise')
    rev2 = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert _summary(rev2)[0]['doc_number'] == rev2_number
    # The latest version's page: every version, and what changed from the one before (nothing: it's a copy)
    page = document_text(client, f'/quotes/{rev2}')
    assert 'class="version-bar"' in page and 'Revision 2' in page and rev1_number in page
    assert f'What changed from {rev1_number}' in page and 'Nothing changed in the items, prices or terms' in page
    assert 'This is an earlier version' not in page
    # An earlier version says so, and links to the latest
    page = document_text(client, f'/quotes/{quote_id}')
    assert 'This is an earlier version' in page and f'/quotes/{rev2}' in page
    # The list shows the quotation once, as its latest version; searching the original number finds it
    rows = client.get('/api/documents/quotes').get_json()['rows']
    found = [r for r in rows if number in (r['number'], *r['search'])]
    assert [r['number'] for r in found] == [rev2_number] and len(found[0]['versions']) == 2


def _pages(pdf_bytes):
    return pdf_bytes.count(b'/Type /Page') - pdf_bytes.count(b'/Type /Pages')


def test_copies_packing_list_and_foreign_payment(client, gst_org):
    from db import db
    org_id = gst_org
    customer = _customer(org_id, 'Hydro Parts Inc', 'Pennsylvania', 'United States of America')
    export_id, _ = _create(client, org_id, 'export_invoice', 'Export Invoice', customer,
                           [{'description': 'Clamp', 'rate': 100, 'qty': 3}], tax_mode='lut',
                           detail_packing_list_no='PL 1', detail_packages='1 box', detail_net_weight='5 kg')
    # Invoices print Original + Duplicate + Transporter by default; "Original only" is one page
    assert _pages(client.get(f'/invoices/{export_id}/pdf').data) == 3
    assert _pages(client.get(f'/invoices/{export_id}/pdf?copies=1').data) == 1
    packing = client.get(f'/invoices/{export_id}/pdf?packing=1')
    assert packing.status_code == 200 and _pages(packing.data) == 1
    assert 'Packing_List' in packing.headers['Content-Disposition']

    # A USD payment with the INR the bank credited
    client.post(f'/invoices/{export_id}/finalize')
    client.post(f'/invoices/{export_id}/payment', data={'amount': '300', 'method': 'SWIFT (foreign remittance)',
                                                         'received_amount': '25000', 'payment_date': date.today().isoformat()})
    header, _ = _summary(export_id)
    assert header['status'] == 'paid'
    payment = db.execute_proc('sp_get_invoice_payments', (export_id,))[0]
    assert float(payment['received_amount']) == 25000 and payment['received_currency'] == 'INR'
    [row] = document(client, f'/invoices/{export_id}')['payments']['rows']
    assert row['credited'] == {'amount': 25000, 'currency': 'INR', 'rate': '83.33'}


def test_packing_by_box(client, gst_org):
    org_id = gst_org
    customer = _customer(org_id, 'Hydro Parts Inc', 'Pennsylvania', 'United States of America')
    export_id, _ = _create(client, org_id, 'export_invoice', 'Export Invoice', customer,
                           [{'description': 'Toggle clamp', 'rate': 13, 'qty': 10},
                            {'description': 'Aluminum bracket', 'rate': 15, 'qty': 10},
                            {'description': 'Name plate', 'rate': 3, 'qty': 50}], tax_mode='lut')
    from access import fetch_invoice
    from invoice_service import build_sections, item_lines, packing_summary
    header, values = fetch_invoice(export_id)
    lines = item_lines(build_sections(header, values))
    o = [l['ordinal'] for l in lines]

    from tests.spa import boot_of, packing
    assert boot_of(client.get(f'/invoices/{export_id}/packing').get_data(as_text=True))   # the app's page
    empty = packing(client, export_id)
    assert [l['label'] for l in empty['lines']] == ['Toggle clamp', 'Aluminum bracket', 'Name plate']
    assert empty['boxes'] == [{'values': {'dimensions': '', 'net_weight': '', 'gross_weight': ''}, 'packed': {}}]
    form = {'box_count': '2', 'packing_list_no': 'PL 900', 'marks': 'HYDRO/1-2',
            'box_1_present': '1', 'box_1_dimensions': '60 x 40 x 30 cm', 'box_1_net_weight': '18', 'box_1_gross_weight': '20',
            f'qty_1_{o[0]}': '10', f'qty_1_{o[1]}': '4',
            'box_2_present': '1', 'box_2_dimensions': '40 x 30 x 20 cm', 'box_2_net_weight': '9.5', 'box_2_gross_weight': '11',
            f'qty_2_{o[1]}': '6', f'qty_2_{o[2]}': '40'}
    client.post(f'/invoices/{export_id}/packing', data=form)
    header, values = fetch_invoice(export_id)
    pack = packing_summary(header, build_sections(header, values))
    assert pack['count'] == 2 and pack['net_weight'] == 27.5 and pack['gross_weight'] == 31
    assert [len(b['contents']) for b in pack['boxes']] == [2, 2]
    assert [(u['description'], u['missing']) for u in pack['unpacked']] == [('Name plate', 10)]
    saved = packing(client, export_id)
    assert saved['packing_list_no'] == 'PL 900' and saved['unpacked'] == [{'label': 'Name plate', 'qty': 10}]
    assert saved['boxes'][1] == {'values': {'dimensions': '40 x 30 x 20 cm', 'net_weight': '9.5', 'gross_weight': '11'},
                                 'packed': {str(o[1]): 6, str(o[2]): 40}}

    pdf = client.get(f'/invoices/{export_id}/pdf?packing=1')
    assert pdf.status_code == 200 and _pages(pdf.data) == 1

    # A quotation's template has no packing page: nothing to pack, and its address goes back to the quotation
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Toggle clamp', 'price': 13, 'qty': 1}])
    assert client.get(f'/api/packing/{quote_id}').status_code == 404
    assert client.get(f'/quotes/{quote_id}/packing').headers['Location'].endswith(f'/quotes/{quote_id}')


def test_quote_cost_breakup(client, gst_org):
    org_id = gst_org
    from document_service import get_org_profile, set_next_number
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 700)
    customer = _customer(org_id, 'Farm Gear Works Ltd', 'Tamil Nadu', 'India')
    from db import db
    template = _template(org_id, 'Quotation with cost break-up')
    fields = db.execute_proc('sp_get_template_fields', (template['template_id'],))
    by = {(f['section_name'], f['field_name']): f for f in fields}
    items_sid, breakup_sid = by[('items', 'description')]['section_id'], by[('breakup', 'description')]['section_id']
    import projects
    project_id = projects.create_project(org_id, customer, 'Press reconditioning')
    from tests.spa import editor
    suggested = editor(client, f'/quotes/create?template_id={template["template_id"]}&project_id={project_id}')['hidden']['suggested_number']
    form = {'doc_type': 'quote', 'template_id': template['template_id'], 'customer_id': customer, 'project_id': project_id,
            'issue_date': date.today().isoformat(), 'doc_number': suggested, 'suggested_number': suggested,
            'tax_mode': 'none'}

    def put(sid, row, section, name, value):
        form[f'line_item_{sid}_{row}_field_{by[(section, name)]["field_id"]}'] = str(value)
    put(items_sid, 1, 'items', 'description', 'Press reconditioning'); put(items_sid, 1, 'items', 'price', 62000)
    put(items_sid, 1, 'items', 'qty', 1)
    for row, (desc, amount) in enumerate([('Electrical work', 20000), ('Mechanical work', 30000), ('Painting', 12000)], 1):
        put(breakup_sid, row, 'breakup', 'item_no', 1); put(breakup_sid, row, 'breakup', 'description', desc)
        put(breakup_sid, row, 'breakup', 'amount', amount)
    response = client.post('/invoices/create', data=form)
    quote_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)

    header, s = _summary(quote_id)
    assert s['total'] == 62000                       # break-ups don't add to the total
    [group] = s['breakups']
    assert group['total'] == 62000 and group['matches'] and len(group['parts']) == 3
    page = document_text(client, f'/quotes/{quote_id}')
    assert 'Cost break-up' in page and 'Mechanical work' in page and "adds up to" not in page
    assert client.get(f'/quotes/{quote_id}/pdf').status_code == 200


def test_template_pages_and_custom_fields(client, gst_org):
    """Pages & printing: a packing list with custom box details on tax invoices, an annexure
    printed with the document, and org / customer custom fields on the PDF."""
    import io
    from pypdf import PdfReader
    from db import db
    from access import fetch_invoice
    from invoice_service import build_sections, item_lines, packing_summary
    from layout import DEFAULT_PAGES, load_layout, save_layout
    org_id = gst_org
    tid = _template(org_id, 'Tax Invoice')['template_id']
    before = load_layout(tid, org_id)
    try:
        editor = f'/templates/{tid}/layout'
        assert client.get(editor).status_code == 200
        # Add a packing page, then an annexure; each add saves what's on screen first
        assert client.post(editor, data={'page_count': '1', 'page_1_present': '1', 'page_1_kind': 'document',
                                         'add_page': 'packing'}).status_code == 302
        assert [p['kind'] for p in load_layout(tid, org_id)['pages']] == ['document', 'packing']
        client.post(editor, data={
            'page_count': '3',
            'page_1_present': '1', 'page_1_kind': 'document', 'page_1_key': 'document',
            'page_2_present': '1', 'page_2_kind': 'packing', 'page_2_key': 'packing', 'page_2_title': 'Shipping list',
            'page_2_doc_types': 'invoice',
            'page_2_box_label_1': 'Pallet no.', 'page_2_box_label_2': 'Net Wt (kg)', 'page_2_box_key_2': 'net_weight',
            'page_2_box_sum_2': 'on',
            'page_3_kind': 'annexure',                # not present: dropped
            'add_page': 'annexure',
        })
        layout = load_layout(tid, org_id)
        pack, annex = layout['pages'][1], layout['pages'][2]
        assert pack['key'] == 'packing' and pack['title'] == 'Shipping list' and pack['doc_types'] == ['invoice']
        assert [(f['key'], f['sum']) for f in pack['box_fields']] == [('pallet_no', False), ('net_weight', True)]
        assert annex['kind'] == 'annexure' and annex['with_document']
        annex['title'], annex['include_terms'] = 'Terms of supply', True
        save_layout(tid, org_id, layout)
        assert 'Shipping list' in client.get(f'/templates/{tid}').get_data(as_text=True)
        assert 'Shipping list' in client.get(editor).get_data(as_text=True)

        # Custom fields: one about us, one defined for customers and filled on the customer
        client.post('/settings/profile', data={**PROFILE, 'orgcf_label_1': 'MSME No.', 'orgcf_value_1': 'UDYAM-TN-02-0000001',
                                               'orgcf_print_1': 'on', 'custcf_label_1': 'Vendor code', 'custcf_print_1': 'on'})
        customer = _customer(org_id, 'Brakes India Ltd', 'Tamil Nadu', 'India')
        assert 'Vendor code' in client.get(f'/customers/{customer}/edit').get_data(as_text=True)
        db.execute_proc('sp_update_customer_custom', (customer, org_id, '{"vendor_code": "BIL-4471"}'), fetch=False)

        invoice_id, _ = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                                [{'description': 'Fixture plate', 'rate': 1000, 'qty': 4}])
        pdf = document(client, f'/invoices/{invoice_id}')['pdf']
        assert pdf['packing'] == f'/invoices/{invoice_id}/packing'
        assert any('page=packing' in link['href'] and link['label'] == 'Shipping list' for link in pdf['links'])
        assert not any('page=terms_of_supply' in link['href'] for link in pdf['links'])   # printed with the document

        from tests.spa import packing
        labels = [f['label'] for f in packing(client, invoice_id)['box_fields']]
        assert 'Pallet no.' in labels and not any('Gross' in label for label in labels)
        header, values = fetch_invoice(invoice_id)
        [line] = item_lines(build_sections(header, values))
        client.post(f'/invoices/{invoice_id}/packing', data={
            'box_count': '2', 'box_1_present': '1', 'box_1_pallet_no': 'P-1', 'box_1_net_weight': '12.5',
            f'qty_1_{line["ordinal"]}': '3',
            'box_2_present': '1', 'box_2_pallet_no': 'P-2', 'box_2_net_weight': '4', f'qty_2_{line["ordinal"]}': '1'})
        header, values = fetch_invoice(invoice_id)
        summary = packing_summary(header, build_sections(header, values), pack['box_fields'])
        assert [b['values']['pallet_no'] for b in summary['boxes']] == ['P-1', 'P-2']
        assert summary['totals'] == {'net_weight': 16.5} and not summary['unpacked']

        # Main PDF: 3 copies + the annexure; the shipping list is its own PDF
        main = client.get(f'/invoices/{invoice_id}/pdf')
        assert main.status_code == 200 and _pages(main.data) == 4
        text = PdfReader(io.BytesIO(main.data)).pages[0].extract_text()
        assert 'UDYAM-TN-02-0000001' in text and 'BIL-4471' in text
        assert 'Terms of supply' in PdfReader(io.BytesIO(main.data)).pages[3].extract_text()
        shipping = client.get(f'/invoices/{invoice_id}/pdf?page=packing')
        assert shipping.status_code == 200 and _pages(shipping.data) == 1
        ship_text = PdfReader(io.BytesIO(shipping.data)).pages[0].extract_text()
        assert 'P-1' in ship_text and '16.5' in ship_text
        assert client.get(f'/invoices/{invoice_id}/pdf?page=nope').status_code == 302
    finally:
        save_layout(tid, org_id, before if before['pages'] else {'pages': DEFAULT_PAGES})
        client.post('/settings/profile', data=PROFILE)


def test_template_builder_versions(client, gst_org):
    """Opening Edit never writes; saving a template that documents use makes the next version."""
    import template_builder as TB
    from db import db
    org_id = gst_org
    tpl = _template(org_id, 'Quotation')
    versions = lambda: max(t['version'] for t in db.execute_proc('sp_list_templates', (org_id, True))
                           if t['template_id'] == tpl['template_id'])
    before = versions()
    assert client.get(f"/templates/{tpl['template_id']}/edit").status_code == 200
    assert versions() == before

    page = client.get(f"/templates/{tpl['template_id']}/edit").get_data(as_text=True)
    sections = TB.sections_for_editor(tpl['template_id'], before)
    form = {'section_count': str(len(sections)), 'total': ''}
    for i, s in enumerate(sections, 1):
        form.update({f's{i}_present': '1', f's{i}_title': s['title'], f's{i}_name': s['name'], f's{i}_type': s['type'],
                     f's{i}_field_count': str(len(s['fields']))})
        for j, f in enumerate(s['fields'], 1):
            form.update({f's{i}_f{j}_present': '1', f's{i}_f{j}_label': f['label'], f's{i}_f{j}_name': f['name'],
                         f's{i}_f{j}_type': f['type'], f's{i}_f{j}_formula': f['formula']})
            if f['currency']:
                form[f's{i}_f{j}_currency'] = 'on'
            if f['total']:
                form['total'] = f'{i}:{j}'
    form['s1_f2_label'] = 'Unit price'                       # rename a column
    in_use = TB.version_in_use(org_id, tpl['template_id'], before)
    assert client.post(f"/templates/{tpl['template_id']}/edit", data=form).status_code == 302
    after = versions()
    assert after == (before + 1 if in_use else before)
    new = TB.sections_for_editor(tpl['template_id'], after)
    assert new[0]['fields'][1]['label'] == 'Unit price' and new[0]['fields'][1]['name'] == sections[0]['fields'][1]['name']
    assert any(f['total'] for s in new for f in s['fields'])

    # A brand-new template from the builder
    response = client.post('/templates/create', data={**form, 'name': 'Builder test', 'currency_code': 'EUR'})
    assert response.status_code == 302
    created = _template(org_id, 'Builder test')
    assert created['currency_code'] == 'EUR'
    assert 'Builder test' in client.get('/templates/').get_data(as_text=True)


def test_export_quotation(client, gst_org):
    """USD quotation with export terms: printed on the quote, carried into the export invoice."""
    import io
    from pypdf import PdfReader
    from document_service import get_org_profile, set_next_number
    from documents import load_json
    org_id = gst_org
    client.post('/settings/profile', data={**PROFILE, 'bank_name': 'Test Bank', 'bank_account': '00112233', 'bank_swift': 'TESTINBB'})
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 950)
    customer = _customer(org_id, 'Delta Tooling USA', 'Washington', 'United States')
    import projects
    project_id = projects.create_project(org_id, customer, 'Fixture for line 4')
    from tests.spa import editor
    form_page = editor(client, f"/quotes/create?project_id={project_id}&template_id={_template(org_id, 'Export Quotation')['template_id']}")
    assert 'Export terms' in [g['label'] for g in form_page['details']['groups']]                # export defaults for USD
    assert any('Payment: 100% advance by wire transfer' in v for v in form_page['details']['values'].values())
    quote_id, _ = _create(client, org_id, 'quote', 'Export Quotation', customer,
                          [{'description': 'Welding fixture', 'hsn_sac': '84669390', 'qty': 2, 'unit': 'set', 'price': 1500}],
                          project_id=project_id, tax_mode='none', currency='USD', detail_incoterms='FOB Chennai',
                          detail_port_of_loading='Chennai, India', detail_final_destination='United States')
    header, s = _summary(quote_id)
    assert s['total'] == 3000 and header['currency_code'] == 'USD'
    pdf = client.get(f'/quotes/{quote_id}/pdf')
    text = PdfReader(io.BytesIO(pdf.data)).pages[0].extract_text()
    assert 'FOB Chennai' in text and 'TESTINBB' in text and 'United States' in text

    client.post(f'/invoices/{quote_id}/finalize')
    response = client.post(f'/invoices/{quote_id}/convert', data={
        'target': 'export_invoice', 'template_id': _template(org_id, 'Export Invoice')['template_id']})
    export_id = re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)
    details = load_json(_summary(export_id)[0].get('details'))
    assert details['terms_of_delivery'] == 'FOB Chennai' and details['destination'] == 'United States'
    assert projects.project_of(export_id, org_id) == project_id
    client.post('/settings/profile', data=PROFILE)


def test_pdf_with_or_without_seal(client, gst_org, monkeypatch):
    """The company stamp prints by default; seal=0 leaves it off (the signature and the rest stay)."""
    import base64
    import invoice_service
    from document_service import get_org_profile, save_org_profile
    org_id = gst_org
    _, profile = get_org_profile(org_id)
    stamp = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'0' * 64).decode()
    save_org_profile(org_id, {**profile, 'stamp': stamp})
    customer = _customer(org_id, 'Farm Gear Works Limited, Gears Division', 'Tamil Nadu', 'India')
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Seal check', 'price': 100, 'qty': 1}])
    rendered = []
    real = invoice_service.render_template
    monkeypatch.setattr(invoice_service, 'render_template', lambda *a, **k: rendered.append(real(*a, **k)) or rendered[-1])
    monkeypatch.setattr(invoice_service, '_pdf_bytes', lambda html: b'%PDF-1.4')
    monkeypatch.setattr(invoice_service, '_page_count', lambda pdf: 1)
    monkeypatch.setattr(invoice_service, '_merge', lambda parts: parts[0])
    try:
        assert client.get(f'/quotes/{quote_id}/pdf').status_code == 200
        assert stamp in rendered[-1]
        assert client.get(f'/quotes/{quote_id}/pdf?seal=0').status_code == 200
        assert stamp not in rendered[-1] and 'Seal check' in rendered[-1]
        pdf = document(client, f'/quotes/{quote_id}')['pdf']
        assert pdf['seal'] and pdf['links']                                    # "Print with seal" in the PDF menu
    finally:
        save_org_profile(org_id, profile)
    assert not document(client, f'/quotes/{quote_id}')['pdf']['seal']
