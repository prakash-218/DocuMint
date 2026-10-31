"""The sidebar both the server pages and the React app draw (nav.py): its links by role, and which one is lit."""
import pytest


@pytest.fixture
def keys(app):
    import nav

    def of(role, unread=0):
        with app.test_request_context():
            return [[i['key'] for i in s['items']] for s in nav.sidebar(role, unread)]
    return of


def test_each_role_sees_its_links(keys):
    # Home and Projects; Sales; People; Library; Organization, as the prototype groups them
    assert keys('owner') == [['home', 'notifications', 'projects'], ['quote', 'proforma', 'invoices'], ['customers', 'emails'],
                             ['templates', 'rates'], ['settings', 'audit']]
    assert keys('member') == [['home', 'projects'], ['quote', 'proforma', 'invoices'], ['customers', 'emails'], ['templates'], ['settings']]
    assert keys('viewer') == [['home', 'projects'], ['quote', 'proforma', 'invoices'], ['customers'], ['templates'], ['settings']]
    assert keys('sales') == [['projects'], ['quote'], ['customers'], ['settings']]   # quotations only, no money


def test_the_groups_have_names(app):
    import nav
    with app.test_request_context():
        sections = nav.sidebar('owner')
    assert [s['title'] for s in sections] == [None, 'Sales', 'People', 'Library', 'Organization']
    labels = [i['label'] for s in sections for i in s['items']]
    assert labels[:3] == ['Home', 'Notifications', 'Projects'] and 'Proformas' in labels and 'Rates' in labels


def test_links_lead_where_the_pages_are_and_the_longest_prefix_lights(app):
    import nav
    with app.test_request_context():
        sections = nav.sidebar('owner', unread=4)
    items = {i['key']: i for s in sections for i in s['items']}
    assert (items['quote']['href'], items['proforma']['href'], items['invoices']['href']) == ('/quotes/', '/proformas/', '/invoices/')
    assert items['notifications']['badge'] == 4 and items['projects']['badge'] == 0
    assert nav.active(sections, '/settings/audit-log') == 'audit'
    assert nav.active(sections, '/settings/profile') == 'settings'
    assert nav.active(sections, '/quotes/Q-1') == 'quote' and nav.active(sections, '/quotesx') is None
    assert nav.active(sections, '/costings/K-1') is None and nav.active(sections, '/costings/rates') == 'rates'


def test_the_new_menu_is_for_those_who_make_documents(app):
    import nav
    with app.test_request_context():
        assert [i['label'] for i in nav.new_menu('member')] == ['Quotation', 'Proforma Invoice', 'Tax Invoice', 'Project']
        assert nav.new_menu('viewer') == [] and nav.new_menu('sales') == []
