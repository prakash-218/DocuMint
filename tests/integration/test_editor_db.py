"""
The editor the React app draws (editor_page.py), against real PostgreSQL (same opt-in as test_app_db.py): a new
document's steps, then its form posted as the app posts it, and a draft saved again unchanged keeps everything.
"""

import re
import uuid

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _customer, _summary, _template, app, client, gst_org  # noqa: F401
from tests.spa import editor, editor_form


def test_a_new_quotation_through_the_editor_and_saved_again_unchanged(client, gst_org):
    import projects
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    customer = _customer(org_id, f'Spline Works {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Spline gauges')
    template = _template(org_id, 'Quotation')

    # The steps: the project, then the template, then the form, with the project's customer and subject
    assert editor(client, '/quotes/create')['step'] == 'project'
    step = editor(client, f'/quotes/create?project_id={project_id}')
    assert step['step'] == 'template' and any(t['name'] == 'Quotation' for t in step['templates'])
    page = editor(client, f'/quotes/create?project_id={project_id}&template_id={template["template_id"]}')
    assert page['step'] == 'editor' and page['customer']['fixed']['id'] == customer
    assert page['details']['values']['subject'] == 'Spline gauges' and page['hidden']['project_id'] == project_id
    [items] = [s for s in page['sections'] if s['type'] == 'line_item']
    assert [r['row'] for r in items['rows']] == [1]                                    # one empty line to start
    by_name = {f['name']: f for f in items['fields']}

    # Filled in as the app would post it: two lines
    form = editor_form(page)
    for row, (desc, price, qty) in enumerate([('Spline gauge', '20000', '2'), ('Setting master', '5000', '1')], start=1):
        form[f"line_item_{items['id']}_{row}_field_{by_name['description']['id']}"] = desc
        form[f"line_item_{items['id']}_{row}_field_{by_name['price']['id']}"] = price
        form[f"line_item_{items['id']}_{row}_field_{by_name['qty']['id']}"] = qty
    form['tax_mode'] = 'none'
    response = client.post(page['action'], data=form)
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    quote_id = re.search(r'/quotes/([0-9a-f-]{36})', response.headers['Location']).group(1)
    header, summary = _summary(quote_id)
    assert summary['total'] == 45000 and projects.project_of(quote_id, org_id) == project_id

    # Its draft in the editor, saved again untouched: nothing changes
    draft = editor(client, f'/quotes/{quote_id}/edit')
    assert draft['editing'] and not draft['correcting'] and draft['action'] == f'/quotes/{quote_id}/edit'
    [items] = [s for s in draft['sections'] if s['type'] == 'line_item']
    assert [r['values'][by_name['description']['id']] for r in items['rows']] == ['Spline gauge', 'Setting master']
    assert client.post(draft['action'], data=editor_form(draft)).status_code == 302
    after, again = _summary(quote_id)
    assert again['total'] == 45000 and after['doc_number'] == header['doc_number']
    assert editor(client, f'/quotes/{quote_id}/edit')['details']['values'] == draft['details']['values']

    # Once sent, the editor only opens to correct it
    client.post(f'/invoices/{quote_id}/finalize')
    assert client.get(f'/api/editor/{quote_id}').status_code == 409
    assert editor(client, f'/quotes/{quote_id}/edit?correct=1')['correcting']
