"""
The Ctrl+K search's list against real PostgreSQL (same opt-in as test_app_db.py).
"""

from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_app_db import VIEWER, login, pytestmark  # noqa: F401


def test_search_lists_documents_projects_customers_and_templates(client, gst_org):
    import projects
    org_id = gst_org
    customer = _customer(org_id, 'Bolt Works Pvt Ltd', 'Tamil Nadu', 'India')
    project = projects.create_project(org_id, customer, 'Ring gauge set', reference='ENQ-5521')
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Ring gauge', 'price': 1500, 'qty': 2}],
                          tax_mode='none', detail_subject='Ring gauges, go / no-go', project_id=project)
    items = client.get('/search/items').get_json()['items']

    quote = next(i for i in items if i['url'] == f'/quotes/{quote_id}')
    assert quote['kind'] == 'document' and quote['title'].startswith('TF/Q/') and quote['badge'] == 'draft'
    assert quote['sub'].startswith('Quotation · Bolt Works Pvt Ltd · Ring gauges, go / no-go · ') and '₹3,000.00' in quote['sub']
    assert 'Ring gauge set' in quote['also']                                     # its project's name
    found = next(i for i in items if i['kind'] == 'project' and i['url'] == f'/projects/{project}')
    assert found['title'] == 'Ring gauge set' and 'ENQ-5521' in found['also'] and found['code'].startswith('PRJ-')
    assert any(i['kind'] == 'customer' and i['title'] == 'Bolt Works Pvt Ltd' for i in items)
    assert any(i['kind'] == 'template' and i['title'] == 'Quotation' and i['sub'].endswith('For quotations') for i in items)

    login(client, VIEWER)
    titles = {i['title'] for i in client.get('/search/items').get_json()['items']}
    assert 'Quotations' in titles and 'New quotation' not in titles
