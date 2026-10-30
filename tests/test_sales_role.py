"""The Sales role: projects, quotations and customers, and nothing else."""

import pytest

from tests.fakedb import ORG_A


@pytest.fixture
def sales(client, login_as, fake_db):
    fake_db.members['U-A'][0]['role'] = 'sales'
    fake_db.invoices['Q-1'] = {**fake_db.invoices['INV-A'], 'invoice_id': 'Q-1', 'doc_type': 'quote', 'status': 'draft',
                               'doc_number': 'TF/Q/031/26-27'}
    fake_db.invoices['Q-2'] = {**fake_db.invoices['Q-1'], 'invoice_id': 'Q-2', 'status': 'sent', 'doc_number': 'TF/Q/032/26-27'}
    login_as('U-A', ORG_A, 'alice@a.com')
    return client


@pytest.mark.parametrize('path', ['/projects/', '/projects/new', '/quotes/', '/quotes/Q-1', '/quotes/create',
                                  '/customers/', '/customers/create', '/customers/C-A', '/customers/C-A/edit', '/settings/'])
def test_sales_open_projects_quotations_and_customers(sales, path):
    response = sales.get(path)
    assert response.status_code == 200, (path, response.headers.get('Location'))


@pytest.mark.parametrize('path', ['/invoices/', '/proformas/', '/invoices/INV-A', '/invoices/INV-A/pdf', '/invoices/INV-A/edit',
                                  '/proformas/create', '/quotes/create?doc_type=invoice', '/templates/', '/templates/T-A',
                                  '/notifications/', '/settings/audit-log', '/settings/profile'])
def test_sales_are_kept_out_of_everything_else(sales, path):
    response = sales.get(path)
    assert response.status_code == 302 and response.headers['Location'].endswith('/projects/'), path
    assert "Your role doesn&#39;t allow that" in sales.get('/projects/').get_data(as_text=True)


@pytest.mark.parametrize('path', ['/emails/', '/costings/rates'])
def test_mail_and_costings_are_not_there_for_sales(sales, path):
    assert sales.get(path).status_code == 403, path


def test_sales_start_on_projects(sales):
    response = sales.get('/dashboard/')
    assert response.status_code == 302 and response.headers['Location'].endswith('/projects/')
    assert "doesn&#39;t allow" not in sales.get('/projects/').get_data(as_text=True)      # no complaint: it's their home


def test_sales_cannot_post_to_other_documents(sales, fake_db):
    for path, data in (('/quotes/Q-2/convert', {'target': 'proforma'}), ('/invoices/INV-A/payment', {'amount': '10'}),
                       ('/invoices/INV-A/finalize', {}), ('/projects/for-document/INV-A', {'project_id': 'P-1'}),
                       ('/projects/P-1/documents', {'invoice_id': 'INV-A'})):
        response = sales.post(path, data=data)
        assert response.headers['Location'].endswith('/projects/'), path
    assert not fake_db.written()


def test_sales_delete_their_draft_quotations_only(sales, fake_db):
    assert sales.post('/quotes/Q-2/delete').headers['Location'].endswith('/quotes/Q-2')          # sent: kept
    assert ('sp_delete_invoice', ('Q-2',)) not in fake_db.calls
    assert sales.post('/quotes/Q-1/delete').headers['Location'].endswith('/quotes/')
    assert ('sp_delete_invoice', ('Q-1',)) in fake_db.calls


@pytest.mark.parametrize('path', ['/api/customers', '/api/customers/new', '/api/new-project',
                                  '/api/settings'])
def test_sales_read_the_screens_they_open(sales, path):
    assert sales.get(path).status_code == 200, path


@pytest.mark.parametrize('path', ['/api/emails', '/api/notifications', '/api/settings/audit-log', '/api/settings/profile'])
def test_sales_dont_read_the_others(sales, path):
    assert sales.get(path).status_code == 403, path


def test_sales_menu_and_search(sales):
    from tests.spa import boot_of
    boot = boot_of(sales.get('/customers/').get_data(as_text=True))
    nav = [i['label'] for s in boot['sidebar'] for i in s['items']]
    assert {'Quotations', 'Projects', 'Customers'} <= set(nav)
    assert not set(nav) & {'Dashboard', 'Proforma invoices', 'Invoices', 'Templates', 'Emails', 'Audit log'}
    assert sales.get('/api/customers').get_json()['new'] == '/customers/create'        # Sales add customers
    items = sales.get('/search/items').get_json()['items']
    titles = {i['title'] for i in items}
    assert {'Projects', 'Quotations', 'Customers', 'New quotation', 'New project', 'New customer'} <= titles
    assert not titles & {'Dashboard', 'Invoices', 'Proforma invoices', 'Templates', 'Emails', 'New invoice', 'New proforma invoice'}
    assert {i['title'] for i in items if i['kind'] == 'document'} == {'TF/Q/031/26-27', 'TF/Q/032/26-27'}
    assert not any(i['kind'] == 'template' for i in items)


def test_sales_quotation_page_has_no_convert(sales):
    html = sales.get('/quotes/Q-2').get_data(as_text=True)
    assert 'TF/Q/032/26-27' in html and '/convert' not in html


def test_members_are_unchanged(client, login_as, fake_db):
    fake_db.members['U-A'][0]['role'] = 'member'
    login_as('U-A', ORG_A, 'alice@a.com')
    assert client.get('/invoices/INV-A').status_code == 200 and client.get('/dashboard/').status_code == 200
    assert client.get('/customers/create').headers['Location'].endswith('/dashboard/')    # adding customers: still owners and admins
