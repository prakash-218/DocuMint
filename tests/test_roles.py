"""Custom roles: an organization's own sets of permissions, given only within what the person giving them has."""

import pytest

import permissions as P
from tests.fakedb import ORG_A


@pytest.fixture
def owner(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    return client


def _as(fake_db, role, names=None, role_id='R-ME'):
    """The signed-in person (alice) gets a built-in role, or a custom one with these permissions."""
    me = fake_db.members['U-A'][0]
    me.update(role=role, role_id=role_id if role == 'custom' else None,
              role_permissions=names if role == 'custom' else None, role_name='Their role' if role == 'custom' else None)


def _role(fake_db, role_id, name, names):
    fake_db.roles[role_id] = {'role_id': role_id, 'org_id': ORG_A, 'name': name, 'description': '', 'permissions': sorted(names)}


# ---------------------------------------------------------------- The permissions a custom role grants

def test_a_custom_role_grants_its_permissions(owner, fake_db):
    _as(fake_db, 'custom', ['quotes.read', 'projects.read'])
    me = owner.get('/api/me').get_json()
    assert me['role'] == 'custom' and me['role_label'] == 'Their role'
    assert me['permissions'] == ['projects.read', 'quotes.read']
    assert owner.get('/quotes/').status_code == 200 and owner.get('/projects/').status_code == 200
    assert owner.get('/invoices/').status_code == 302 and owner.get('/api/customers').status_code == 403


def test_a_custom_role_never_grants_what_only_owners_have():
    granted = P.of({'role': 'custom', 'role_permissions': ['team.owners', 'organization.write', 'quotes.write', 'gone.away']})
    assert granted == {'quotes.write', 'quotes.read'}                    # and writing needs reading


def test_the_built_in_roles_have_what_their_permissions_need():
    assert all(P.with_implied(perms) == perms for perms in P.ROLES.values())
    assert P.GRANTABLE == set(P.PERMISSIONS) - {'organization.write', 'team.owners'}
    assert {n for area in P.AREAS for n in P.PERMISSIONS if n.split('.')[0] == area[0]} >= P.GRANTABLE


@pytest.mark.parametrize('giver, given, ok', [
    ('owner', 'owner', True), ('admin', 'owner', False), ('admin', 'admin', True), ('member', 'sales', False),
    ('member', 'viewer', True), ('sales', 'viewer', False)])
def test_nobody_gives_more_than_they_have(giver, given, ok):
    assert P.may_give(given, giver) is ok


# ---------------------------------------------------------------- The pages and the API

def test_the_roles_page_lists_built_in_and_own_roles(owner, fake_db):
    _role(fake_db, 'R-1', 'Estimator', ['costings.read', 'costings.write', 'quotes.read'])
    data = owner.get('/api/settings/roles').get_json()
    assert [r['key'] for r in data['built_in']] == ['owner', 'admin', 'member', 'sales', 'viewer']
    assert data['built_in'][0]['copy'] is None and data['built_in'][2]['copy'] == '/settings/roles/new?from=member'
    assert data['custom'] == [{'id': 'R-1', 'name': 'Estimator', 'description': '', 'members': 0, 'permissions': 3,
                               'url': '/settings/roles/R-1', 'editable': True}]
    assert owner.get('/settings/roles').status_code == 200 and owner.get('/settings/roles/R-1').status_code == 200
    assert owner.get('/settings/roles/R-404').status_code == 404


def test_a_new_role_can_start_from_a_built_in_one(owner):
    data = owner.get('/api/settings/roles/new?from=member').get_json()
    assert data['role']['name'] == 'Member (copy)' and data['role']['permissions'] == sorted(P.ROLES['member'])
    assert data['method'] == 'POST' and data['save'] == '/api/settings/roles' and data['delete'] is None
    areas = {a['key']: a for a in data['catalog']}
    assert [p['name'] for p in areas['team']['permissions']] == ['team.manage']          # never team.owners
    assert {'name': 'quotes.write', 'label': 'Make, edit and send quotations', 'needs': ['quotes.read'], 'yours': True} \
        in areas['quotes']['permissions']


def test_making_a_role(owner, fake_db):
    response = owner.post('/api/settings/roles', json={'name': '  Site   estimator ', 'description': 'Prices jobs',
                                                       'permissions': ['costings.write', 'quotes.write']})
    assert response.status_code == 201 and response.get_json() == {'id': 'R-1', 'url': '/settings/roles/R-1'}
    assert fake_db.roles['R-1']['name'] == 'Site estimator'
    assert fake_db.roles['R-1']['permissions'] == ['costings.read', 'costings.write', 'quotes.read', 'quotes.write']


@pytest.mark.parametrize('body, status, words', [
    ({'name': '', 'permissions': []}, 400, 'name'),
    ({'name': 'Owner', 'permissions': []}, 400, 'built-in role'),
    ({'name': 'Odd', 'permissions': 'quotes.read'}, 400, 'list'),
    ({'name': 'Odd', 'permissions': ['quotes.fly']}, 400, 'no permission called quotes.fly'),
    ({'name': 'Odd', 'permissions': ['team.owners']}, 400, 'Only owners'),
])
def test_what_a_role_cannot_be(owner, body, status, words):
    response = owner.post('/api/settings/roles', json=body)
    assert response.status_code == status and words in response.get_json()['error']


def test_two_roles_cannot_share_a_name(owner, fake_db):
    _role(fake_db, 'R-1', 'Estimator', [])
    response = owner.post('/api/settings/roles', json={'name': 'Estimator', 'permissions': []})
    assert response.status_code == 409


def test_a_manager_only_gives_what_they_have(owner, fake_db):
    _as(fake_db, 'custom', ['team.manage', 'quotes.read', 'quotes.write'])
    ok = owner.post('/api/settings/roles', json={'name': 'Quoter', 'permissions': ['quotes.write']})
    assert ok.status_code == 201
    response = owner.post('/api/settings/roles', json={'name': 'Biller', 'permissions': ['invoices.write']})
    assert response.status_code == 403 and "doesn't have" in response.get_json()['error']
    _role(fake_db, 'R-9', 'Accounts', ['invoices.read', 'invoices.write'])
    assert owner.patch('/api/settings/roles/R-9', json={'name': 'Accounts', 'permissions': []}).status_code == 403
    assert owner.delete('/api/settings/roles/R-9', json={}).status_code == 403
    assert owner.get('/api/settings/roles/R-9').get_json()['editable'] is False


def test_changing_and_deleting_a_role(owner, fake_db):
    _role(fake_db, 'R-1', 'Estimator', ['quotes.read'])
    response = owner.patch('/api/settings/roles/R-1', json={'name': 'Estimator', 'description': '', 'permissions': ['costings.read']})
    assert response.status_code == 200 and fake_db.roles['R-1']['permissions'] == ['costings.read']
    fake_db.members['U-B'][0].update(org_id=ORG_A, role='custom', role_id='R-1')           # someone has it
    response = owner.delete('/api/settings/roles/R-1', json={})
    assert response.status_code == 409 and 'Give them another role first' in response.get_json()['error']
    fake_db.members['U-B'][0].update(role='viewer', role_id=None)
    assert owner.delete('/api/settings/roles/R-1', json={}).status_code == 200 and 'R-1' not in fake_db.roles
    assert owner.patch('/api/settings/roles/R-1', json={'name': 'X', 'permissions': []}).status_code == 404


@pytest.mark.parametrize('role', ['member', 'sales', 'viewer'])
def test_only_team_managers_see_roles(owner, fake_db, role):
    _as(fake_db, role)
    assert owner.get('/api/settings/roles').status_code == 403
    assert owner.post('/api/settings/roles', json={'name': 'X', 'permissions': []}).status_code == 403
    assert owner.get('/settings/roles').status_code == 302


# ---------------------------------------------------------------- Giving people roles

def test_the_team_offers_the_roles_they_may_give(owner, fake_db):
    _role(fake_db, 'R-1', 'Estimator', ['quotes.read'])
    _role(fake_db, 'R-2', 'Everything', sorted(P.GRANTABLE))
    fake_db.team = [{'user_id': 'U-B', 'email': 'ravi@gearco.example', 'role': 'custom', 'role_id': 'R-1', 'role_name': 'Estimator',
                     'role_permissions': ['quotes.read'], 'status': 'active'},
                    {'user_id': 'U-C', 'email': 'meena@gearco.example', 'role': 'owner', 'status': 'active'}]
    _as(fake_db, 'admin')
    data = owner.get('/api/settings').get_json()
    assert data['roles'] == [['viewer', 'Viewer'], ['sales', 'Sales (projects and quotations)'], ['member', 'Member'],
                             ['admin', 'Admin'], ['R-1', 'Estimator'], ['R-2', 'Everything']]          # no owner
    assert [(m['role'], m['role_label'], m['manage']) for m in data['members']] == [('R-1', 'Estimator', True), ('owner', 'Owner', False)]
    assert any(link['title'] == 'Roles' for link in data['links'])


def test_giving_someone_a_custom_role(owner, fake_db):
    _role(fake_db, 'R-1', 'Estimator', ['quotes.read'])
    fake_db.team = [{'user_id': 'U-B', 'email': 'ravi@gearco.example', 'role': 'viewer', 'status': 'active'}]
    owner.post('/settings/members/approve', data={'user_id': 'U-B', 'action': 'change_role', 'role': 'R-1'})
    assert ('sp_update_member_status', (ORG_A, 'U-B', 'active', 'custom', 'R-1')) in fake_db.calls
    owner.post('/settings/members/approve', data={'user_id': 'U-B', 'action': 'change_role', 'role': 'R-404'})
    assert not [c for c in fake_db.calls if c[0] == 'sp_update_member_status' and c[1][4:] == (None, 'R-404')]


@pytest.mark.parametrize('giver, target, given, refused', [
    ('admin', 'member', 'owner', 'Only an owner'),
    ('admin', 'owner', 'member', 'Only an owner'),
    ('member', 'viewer', 'viewer', None),        # members don't manage the team at all: refused before (403 page)
])
def test_nobody_changes_roles_beyond_their_own(owner, fake_db, giver, target, given, refused):
    _as(fake_db, giver)
    fake_db.team = [{'user_id': 'U-B', 'email': 'ravi@gearco.example', 'role': target, 'status': 'active'}]
    response = owner.post('/settings/members/approve', data={'user_id': 'U-B', 'action': 'change_role', 'role': given})
    assert response.status_code == 302
    assert not [c for c in fake_db.calls if c[0] == 'sp_update_member_status']
    if refused:
        assert refused in owner.get('/settings/').get_data(as_text=True)


def test_a_custom_manager_cannot_promote_beyond_themselves(owner, fake_db):
    _as(fake_db, 'custom', ['team.manage', 'quotes.read'])
    fake_db.team = [{'user_id': 'U-B', 'email': 'ravi@gearco.example', 'role': 'viewer', 'status': 'active'}]
    owner.post('/settings/members/approve', data={'user_id': 'U-B', 'action': 'change_role', 'role': 'admin'})
    assert not [c for c in fake_db.calls if c[0] == 'sp_update_member_status']
    assert "more than your own role can give" in owner.get('/settings/').get_data(as_text=True)
