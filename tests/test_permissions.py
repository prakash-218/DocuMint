"""Permissions: every page and API endpoint says what it needs, and the built-in roles open what they always did."""

import pytest

import permissions as P

ROLES = ('owner', 'admin', 'member', 'sales', 'viewer')
DOC_TYPES = ('quote', 'proforma', 'invoice', 'export_invoice')
EVERYONE = set(ROLES)
NOT_SALES = EVERYONE - {'sales'}
MANAGERS = {'owner', 'admin'}
EDITORS = {'owner', 'admin', 'member', 'sales'}


def test_every_route_says_what_it_needs(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    outside = {e for e in endpoints if e in P.OUTSIDE or e.partition('.')[0] in P.OUTSIDE_BLUEPRINTS}
    assert sorted(endpoints - outside - set(P.ENDPOINTS)) == []          # a new page is closed until it's listed
    assert sorted(set(P.ENDPOINTS) - endpoints) == []                    # nothing listed that's gone


def test_an_unlisted_endpoint_is_refused():
    assert P.needs('nowhere_bp.page') is None
    assert not P.allows('nowhere_bp.page', perms='owner')


def test_the_roles_are_sets_of_known_permissions():
    assert set(P.ROLES) == set(ROLES) == set(P.ROLE_LABELS)
    assert all(perms <= set(P.PERMISSIONS) for perms in P.ROLES.values())
    assert P.ROLES['owner'] == set(P.PERMISSIONS)
    assert P.ROLES['owner'] - P.ROLES['admin'] == {'organization.write', 'team.owners'}
    assert P.ROLES['viewer'] < P.ROLES['member'] < P.ROLES['admin']
    assert not {p for p in P.ROLES['viewer'] if not p.endswith('.read')}


def test_no_permissions_means_none():
    """An empty set (a role that grants nothing) is nothing, not the current person's."""
    assert not P.can('projects.read', perms=frozenset())
    assert not P.can('projects.read', perms=None) and not P.can('projects.read', perms='no-such-role')
    assert P.doc_types('read', frozenset()) == ()


# What each built-in role opened before permissions (the views' role checks and auth.SALES_PAGES)
BEFORE = {
    'dashboard_bp.index': NOT_SALES, 'api_bp.home': NOT_SALES,
    'projects_bp.list_projects': EVERYONE, 'projects_bp.view_project': EVERYONE, 'projects_bp.download_file': EVERYONE,
    'api_bp.project': EVERYONE, 'api_bp.list_projects': EVERYONE,
    'projects_bp.create_project': EDITORS, 'projects_bp.edit_project': EDITORS, 'projects_bp.set_person': EDITORS,
    'projects_bp.upload_file': EDITORS, 'projects_bp.delete_file': EDITORS, 'api_bp.update_project': EDITORS,
    'api_bp.add_note': EDITORS, 'api_bp.update_file': EDITORS, 'api_bp.new_project': EDITORS,
    'projects_bp.delete_project': MANAGERS | {'sales'},
    'customers_bp.list_customers': EVERYONE, 'customers_bp.view_customer': EVERYONE, 'api_bp.customer': EVERYONE,
    'customers_bp.create_customer': MANAGERS | {'sales'}, 'customers_bp.edit_customer': MANAGERS | {'sales'},
    'api_bp.customer_form': MANAGERS | {'sales'},
    'customers_bp.save_contact': EDITORS, 'customers_bp.delete_contact': EDITORS, 'api_bp.save_person': EDITORS,
    'customers_bp.ignore_contact': {'owner', 'admin', 'member'},
    'customers_bp.statement_pdf': NOT_SALES,
    'customers_bp.create_portal_account': MANAGERS, 'customers_bp.delete_customer': MANAGERS,
    'customers_bp.archive_customer': MANAGERS,
    'emails_bp.inbox': {'owner', 'admin', 'member'}, 'emails_bp.thread': {'owner', 'admin', 'member'},
    'emails_bp.sync_now': MANAGERS, 'api_bp.compose': EDITORS, 'api_bp.send_email': EDITORS,
    'costings_bp.edit': MANAGERS, 'costings_bp.rates': MANAGERS, 'costings_bp.create': MANAGERS,
    'templates_bp.list_templates': NOT_SALES, 'templates_bp.view_template': NOT_SALES,
    'templates_bp.edit_template': MANAGERS, 'templates_bp.create_template': MANAGERS,
    'settings_bp.index': EVERYONE, 'api_bp.settings': EVERYONE, 'search_bp.items': EVERYONE, 'api_bp.me': EVERYONE,
    'settings_bp.edit_organization': {'owner'}, 'settings_bp.approve_member': MANAGERS,
    'settings_bp.audit_log': MANAGERS, 'settings_bp.business_profile': MANAGERS, 'settings_bp.starter_templates': MANAGERS,
    'notifications_bp.index': MANAGERS,         # the sidebar only ever showed notifications to owners and admins
}


@pytest.mark.parametrize('endpoint', sorted(BEFORE))
def test_the_roles_open_what_they_did(endpoint):
    assert {r for r in ROLES if P.allows(endpoint, perms=r)} == BEFORE[endpoint]


# The documents: (endpoints, who for a quotation, who for the others)
DOCUMENTS = [
    (('list_invoices', 'view_invoice', 'export_pdf'), EVERYONE, NOT_SALES),
    (('create_invoice', 'edit_invoice', 'finalize_invoice', 'set_status', 'revise', 'reopen'), EDITORS, EDITORS - {'sales'}),
    (('add_payment', 'apply_advances', 'remove_advance', 'packing'), EDITORS - {'sales'}, EDITORS - {'sales'}),
    (('delete_invoice',), MANAGERS | {'sales'}, MANAGERS),
]


@pytest.mark.parametrize('pages, quotes, others', DOCUMENTS)
def test_the_roles_open_the_documents_they_did(app, pages, quotes, others):
    with app.test_request_context(method='POST'):
        for page in pages:
            for doc_type in DOC_TYPES:
                names = P.needs(f'invoices_bp.{page}', doc_type)
                assert {r for r in ROLES if P.can(*names, perms=r)} == (quotes if doc_type == 'quote' else others), (page, doc_type)


@pytest.mark.parametrize('target', ['proforma', 'invoice', None])
def test_converting_needs_making_what_it_becomes(app, target):
    with app.test_request_context(method='POST', data={'target': target} if target else {}):
        names = P.needs('invoices_bp.convert', 'quote')
        assert {r for r in ROLES if P.can(*names, perms=r)} == {'owner', 'admin', 'member'}
        assert P.doc_permission('write', target) in names


def _sales_pages_before(endpoint, doc_type):
    """auth.sales_may as it was: Sales opened these pages, and only about quotations."""
    pages = {
        'projects_bp': None, 'search_bp': None,
        'invoices_bp': {'list_invoices', 'create_invoice', 'view_invoice', 'view_invoice_new', 'export_pdf', 'finalize_invoice',
                        'set_status', 'revise', 'edit_invoice', 'reopen', 'delete_invoice'},
        'customers_bp': {'list_customers', 'view_customer', 'view_customer_new', 'create_customer', 'edit_customer',
                         'save_contact', 'delete_contact'},
        'api_bp': {'me', 'documents', 'document_page', 'new_document', 'edit_document', 'compose', 'send_email', 'list_projects',
                   'project', 'update_project', 'add_note', 'set_person', 'save_person', 'customer', 'save_customer_contact',
                   'delete_customer_contact', 'update_file', 'customers', 'new_customer', 'customer_form', 'new_project',
                   'settings',
                   'share', 'share_on', 'share_off'},           # since: sharing a quotation, as they email it
        'settings_bp': {'index'},
    }
    blueprint, _, page = endpoint.partition('.')
    if blueprint not in pages or pages[blueprint] is not None and page not in pages[blueprint]:
        return False
    return doc_type in (None, 'quote')


def test_sales_open_what_they_did(app):
    with app.test_request_context(method='POST', data={'target': 'invoice'}):
        for endpoint, rule in P.ENDPOINTS.items():
            for doc_type in DOC_TYPES + (() if isinstance(rule, P.Doc) else (None,)):
                assert P.can(*P.needs(endpoint, doc_type), perms='sales') == _sales_pages_before(endpoint, doc_type), \
                    (endpoint, doc_type)


def test_a_request_about_a_document_needs_reading_it():
    assert P.needs('projects_bp.document_project', 'proforma') == ('projects.write', 'proformas.read')
    assert P.needs('projects_bp.document_project') == ('projects.write',)


@pytest.mark.parametrize('role, draft, sent', [('owner', True, True), ('admin', True, True), ('sales', True, False),
                                               ('member', False, False), ('viewer', False, False)])
def test_who_deletes_a_quotation(role, draft, sent):
    assert P.may_delete({'doc_type': 'quote', 'status': 'draft'}, role) is draft
    assert P.may_delete({'doc_type': 'quote', 'status': 'sent'}, role) is sent
    assert P.may_delete({'doc_type': 'invoice', 'status': 'draft'}, role) is (role in MANAGERS)


def test_file_kinds():
    assert P.file_kind_allowed('po', 'sales') and P.file_kind_allowed('our_quote', 'sales')
    assert not P.file_kind_allowed('our_invoice', 'sales') and not P.file_kind_allowed('our_proforma', 'sales')
    assert P.file_kind_allowed('our_invoice', 'viewer')


def test_the_apps_shorthand():
    assert P.flags('sales') == {'edit': True, 'edit_customers': True, 'manage': False, 'read_mail': False,
                                'quotations_only': True}
    assert P.quotations_only('sales') and not P.quotations_only('viewer')
    assert P.doc_types('write', 'sales') == ('quote',)
    assert P.doc_types('read', 'member') == DOC_TYPES
