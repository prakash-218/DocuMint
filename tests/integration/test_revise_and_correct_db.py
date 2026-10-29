"""
Changing a document after it was sent: correcting it in place, taking "sent" back, revising (also into another
template, also a proforma with advances), and templates that say which document types they're for.
Same opt-in as test_app_db.py; named to run after test_documents_db (document numbers are shared).
"""

import re

from tests.integration.test_documents_db import (_create, _customer, _summary, _template, app, client,  # noqa: F401
                                                    gst_org)
from tests.integration.test_app_db import login, pytestmark  # noqa: F401


def _new_id(response):
    return re.search(r'/(?:quotes|proformas|invoices)/([0-9a-f-]{36})', response.headers['Location']).group(1)


def _flashes(client):
    with client.session_transaction() as s:
        return [m for _, m in s.pop('_flashes', [])]


def _audit(org_id, record_id):
    from db import db
    return [r for r in db.execute_proc('sp_get_audit_log', (org_id, 'invoice', 200, 0)) or [] if r.get('record_id') == record_id]


def _edit_form(client, invoice_id, **changes):
    """The editor's form as it is (every field it posts), with changes; correct=1 when the page asks for it."""
    page = client.get(f'/invoices/{invoice_id}/edit?correct=1').get_data(as_text=True)
    form = {}
    for tag in re.findall(r'<(?:input|select|textarea)[^>]*>', page):
        name = re.search(r'name="([^"]+)"', tag)
        if not name or 'type="submit"' in tag or ('type="checkbox"' in tag and 'checked' not in tag):
            continue
        value = re.search(r'value="([^"]*)"', tag)
        form[name.group(1)] = value.group(1) if value else ''
    for block in re.findall(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', page, re.S):
        chosen = re.search(r'<option[^>]*value="([^"]*)"[^>]*selected', block[1])
        form[block[0]] = chosen.group(1) if chosen else ''
    for name, text in re.findall(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', page, re.S):
        form[name] = text
    form.update(changes)
    return page, form


def test_correcting_a_sent_invoice_and_taking_sent_back(client, gst_org):
    from db import db
    from document_service import get_org_profile, set_next_number
    org_id = gst_org
    set_next_number(org_id, 'invoice', get_org_profile(org_id)[1], 700)
    customer = _customer(org_id, 'Farm Gear Works Limited', 'Tamil Nadu', 'India')
    invoice_id, number = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                                 [{'description': 'Conveyor', 'rate': 1000, 'qty': 1}])
    client.post(f'/invoices/{invoice_id}/finalize')
    # A sent document can't be edited the old way...
    response = client.get(f'/invoices/{invoice_id}/edit')
    assert response.status_code == 302 and 'Change' in ' '.join(_flashes(client))
    # ...its page offers Change: correct, or back to draft (no revisions for tax invoices)
    page = client.get(f'/invoices/{invoice_id}').get_data(as_text=True)
    assert 'id="change-dialog"' in page and 'Correct this invoice' in page and 'Make a revision' not in page
    assert f'/invoices/{invoice_id}/reopen' in page

    # Paid in full, then corrected to a bigger amount: it's pending again, same number, and the audit log says so
    total = float(_summary(invoice_id)[0]['total_amount'])
    client.post(f'/invoices/{invoice_id}/payment', data={'amount': f'{total:.2f}', 'method': 'NEFT / RTGS'})
    assert _summary(invoice_id)[0]['status'] == 'paid'
    page, form = _edit_form(client, invoice_id)
    assert "You're correcting a tax invoice" in page and form.get('correct') == '1'
    qty = next(k for k, v in form.items() if k.startswith('line_item_') and v == '1')
    form[qty] = '2'
    response = client.post(f'/invoices/{invoice_id}/edit', data=form)
    assert response.status_code == 302 and 'corrected' in ' '.join(_flashes(client))
    header, _ = _summary(invoice_id)
    assert header['doc_number'] == number and float(header['total_amount']) == 2 * total and header['status'] == 'pending'
    assert any(r['field_name'] == 'corrected' and float(r['new_value']) == 2 * total for r in _audit(org_id, invoice_id))
    events = db.execute_proc('sp_list_project_events', (header['project_id'], org_id, 10)) or []
    assert any('corrected after sending' in e['title'] for e in events)

    # With a payment on it, it can't go back to draft
    client.post(f'/invoices/{invoice_id}/reopen')
    assert 'Payments are recorded' in ' '.join(_flashes(client)) and _summary(invoice_id)[0]['status'] == 'pending'

    # Without one it can: same number, a draft again
    other_id, other_number = _create(client, org_id, 'invoice', 'Tax Invoice', customer,
                                     [{'description': 'Spares', 'rate': 500, 'qty': 1}])
    client.post(f'/invoices/{other_id}/finalize')
    client.post(f'/invoices/{other_id}/reopen')
    header, _ = _summary(other_id)
    assert header['status'] == 'draft' and header['doc_number'] == other_number
    assert client.get(f'/invoices/{other_id}/edit').status_code == 200


def test_revising_a_quotation_into_another_template(client, gst_org):
    from document_service import get_org_profile, set_next_number
    org_id = gst_org
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 600)
    customer = _customer(org_id, 'Hydro Parts Private Limited', 'Tamil Nadu', 'India')
    quote_id, number = _create(client, org_id, 'quote', 'Quotation', customer,
                               [{'description': 'Assembly fixture', 'price': 250000, 'qty': 1}], tax_mode='none')
    client.post(f'/invoices/{quote_id}/finalize')
    page = client.get(f'/quotes/{quote_id}').get_data(as_text=True)
    head, tail = number.rsplit('/', 1)
    assert f'Make {head}R1/{tail}' in page                       # the old way: Q/600/26-27 -> Q/600R1/26-27
    breakup = _template(org_id, 'Quotation with cost break-up')
    assert f'value="{breakup["template_id"]}"' in page            # another quotation template to revise into
    assert f'value="{_template(org_id, "Tax Invoice")["template_id"]}"' not in page.split('id="revise_template"')[1].split('</select>')[0]

    response = client.post(f'/invoices/{quote_id}/revise', data={'template_id': breakup['template_id']})
    revision = _new_id(response)
    header, summary = _summary(revision)
    assert header['doc_number'] == f'{head}R1/{tail}' and header['template_id'] == breakup['template_id']
    assert header['status'] == 'draft' and summary['total'] == 250000          # the items came across
    assert _summary(quote_id)[0]['status'] == 'revised'
    # The old version: no revising it again, no going back to draft
    page = client.get(f'/quotes/{quote_id}').get_data(as_text=True)
    assert 'A newer revision replaced this one' in page and 'Not possible: a newer revision replaced it' in page
    # Revising the revision: R2
    client.post(f'/invoices/{revision}/finalize')
    second = _new_id(client.post(f'/invoices/{revision}/revise'))
    assert _summary(second)[0]['doc_number'] == f'{head}R2/{tail}' and _summary(revision)[0]['status'] == 'revised'


def test_revising_a_proforma_moves_its_advances(client, gst_org):
    import advances
    from document_service import get_org_profile, set_next_number
    org_id = gst_org
    set_next_number(org_id, 'proforma', get_org_profile(org_id)[1], 800)
    customer = _customer(org_id, 'Precision Hydraulic Private Limited', 'Tamil Nadu', 'India')
    pi_id, number = _create(client, org_id, 'proforma', 'Proforma Invoice', customer,
                            [{'description': '5 ton press', 'rate': 100000, 'qty': 1}], advance_percent='50')
    client.post(f'/invoices/{pi_id}/finalize')
    client.post(f'/invoices/{pi_id}/payment', data={'amount': '50000', 'method': 'NEFT / RTGS'})
    assert len(advances.on_proforma(pi_id)) == 1
    page = client.get(f'/proformas/{pi_id}').get_data(as_text=True)
    assert 'Make a revision' in page and 'advances received move to the revision' in page
    assert 'Not possible: payments are recorded on this proforma' in page        # so no "back to draft"

    revision = _new_id(client.post(f'/invoices/{pi_id}/revise'))
    header, _ = _summary(revision)
    assert header['doc_type'] == 'proforma' and header['doc_number'] == number.replace('(', 'R1(', 1)
    assert 'with the advances received' in ' '.join(_flashes(client))
    assert [float(a['amount']) for a in advances.on_proforma(revision)] == [50000] and not advances.on_proforma(pi_id)
    assert _summary(pi_id)[0]['status'] == 'revised'
    # The list shows the proforma once; its page shows both versions
    found = [r for r in client.get('/api/documents/proformas').get_json()['rows'] if number in (r['number'], *r['search'])]
    assert len(found) == 1 and len(found[0]['versions']) == 1
    assert 'class="version-bar"' in client.get(f'/proformas/{revision}').get_data(as_text=True)


def test_templates_say_what_they_are_for(client, gst_org):
    import projects
    from layout import load_layout
    org_id = gst_org
    quotation, invoice = _template(org_id, 'Quotation'), _template(org_id, 'Tax Invoice')
    assert load_layout(quotation['template_id'], org_id)['used_for'] == ['quote']        # set with the starter templates
    customer = _customer(org_id, 'Wheels India Limited', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Drop set')
    page = client.get(f'/quotes/create?project_id={project_id}').get_data(as_text=True)
    mine, others = page.split('Other templates')
    assert 'Quotation with cost break-up' in mine and 'Tax Invoice' not in mine and 'Tax Invoice' in others

    # Changing it: the Tax Invoice template is offered for quotations too
    layout_page = client.get(f'/templates/{invoice["template_id"]}/layout').get_data(as_text=True)
    assert 'name="used_for" value="invoice" class="form-checkbox" checked' in layout_page
    form = {'page_count': '0', 'export': 'auto', 'used_for': ['invoice', 'quote']}
    assert client.post(f'/templates/{invoice["template_id"]}/layout', data=form).status_code == 302
    assert load_layout(invoice['template_id'], org_id)['used_for'] == ['invoice', 'quote']
    mine = client.get(f'/quotes/create?project_id={project_id}').get_data(as_text=True).split('Other templates')[0]
    assert 'Tax Invoice' in mine
    client.post(f'/templates/{invoice["template_id"]}/layout', data={**form, 'used_for': ['invoice']})
    assert 'For invoices' in client.get('/templates/').get_data(as_text=True)
