"""
The new document page against real PostgreSQL (same opt-in as test_app_db.py): a quotation, its proforma and its
tax invoice, each with what to do next, and every form sent from the new page coming back to it.
"""

import re
import uuid

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role
from tests.spa import document


def _page(client, path):
    """The page at path (the app's), and what the app is given for it (GET /api/document/<id>)."""
    assert client.get(path).status_code == 200, path
    return document(client, path)


def _labels(props):
    return [a['label'] + ('*' if a['primary'] else '') for a in props['next']['actions']]


def _send(client, path, action, data=None):
    """Send a form from the page at path (its Referer), the way the browser would; where it goes next."""
    response = client.post(action['action'] if isinstance(action, dict) else action,
                           data=data if data is not None else action['fields'], headers={'Referer': f'http://localhost{path}'})
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return response.headers['Location']


def test_a_quotation_to_its_invoice_on_the_new_page(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, f'Axle Works {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Spline gauges')
    quote_id, quote_no = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Spline gauge', 'price': 20000, 'qty': 1}],
                                 tax_mode='none', project_id=project_id)
    quote = f'/quotes/{quote_id}'
    props = _page(client, quote)
    assert _labels(props) == ['Mark as sent*', 'Edit'] and props['head']['pill'] == {'text': 'Draft', 'tone': 'draft'}
    assert props['head']['number'] == quote_no and props['money'] is None                       # no money strip on a quotation
    assert props['next']['actions'][1]['href'].endswith(f'/quotes/{quote_id}/edit')
    # the project page's documents open the new page
    doc = client.get(f'/api/projects/{project_id}').get_json()['documents'][0]
    assert doc['url'] == quote

    assert _send(client, quote, props['next']['actions'][0]).endswith(quote)  # mark as sent, and back here
    props = _page(client, quote)
    assert _labels(props) == ['Mark accepted*', 'Send a follow-up', 'Mark declined', 'Make a revision']
    assert props['change'] and props['project_id'] == project_id                  # Change: correct, revise, back to draft
    assert _send(client, quote, props['next']['actions'][0]).endswith(quote)  # the customer said yes
    props = _page(client, quote)
    assert _labels(props) == ['Raise proforma for the advance*', 'Invoice in full instead', 'Undo: not answered yet']

    edit = _send(client, quote, props['next']['actions'][0])                  # the proforma, in the editor
    assert edit.endswith('/edit')
    proforma_id = re.search(r'/proformas/([0-9a-f-]{36})/edit', edit).group(1)
    proforma = f'/proformas/{proforma_id}'
    client.post(f'/proformas/{proforma_id}/finalize')
    props = _page(client, proforma)
    assert _labels(props)[0] == 'Record the advance*' and props['next']['actions'][0]['href'] == '#payment'
    assert props['payments']['record']['title'] == 'Record an advance'                 # the form the next step points at
    form = {'amount': '6000', 'method': 'Bank transfer', 'payment_date': '2026-10-20'}
    assert _send(client, proforma, f'/proformas/{proforma_id}/payment', form).endswith(proforma)
    props = _page(client, proforma)
    assert _labels(props) == ['Create tax invoice*']
    assert props['head']['pill'] == {'text': 'Advance received', 'tone': 'done'}
    assert [(m['label'], m['value']) for m in props['money']][2:] == [('Advance received', 6000), ('Still to come', 14000)]

    edit = _send(client, proforma, props['next']['actions'][0])               # the tax invoice, advance carried
    invoice_id = re.search(r'/invoices/([0-9a-f-]{36})/edit', edit).group(1)
    invoice = f'/invoices/{invoice_id}'
    client.post(f'/invoices/{invoice_id}/finalize')
    props = _page(client, invoice)
    assert _labels(props) == ['Record payment*', 'Email a reminder'] and props['next']['text'].endswith(' due.')

    # Sales open the quotation's new page, not the proforma's; viewers see it all and can do nothing
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        props = _page(client, quote)
        assert props['next']['tone'] == 'done' and props['next']['text'] == 'Accepted and taken forward.'
        assert client.get(proforma).status_code == 302
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
        login(client, VIEWER)
        props = _page(client, invoice)
        assert props['next']['actions'] == [] and props['payments']['record'] is None and props['change'] is None
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')

    assert client.get(f'/invoices/{uuid.uuid4()}').status_code == 302    # not there: back to the list
