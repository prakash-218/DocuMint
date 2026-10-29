"""
Contacts against real PostgreSQL (same opt-in as test_app_db.py): a customer's contacts, what each gets on a
project at one of its sites, and the people found in the project's emails.
"""

import uuid
from email.message import EmailMessage

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_sales_role_db import _set_role

SIGNATURE = 'Please find our PO attached.\n\nRegards,\nRavi Kumar | Purchase\nMob: +91 98765 43210\n'


def _mail(subject, sender, body, message_id, cc=None):
    m = EmailMessage()
    m['From'], m['To'], m['Subject'] = sender, 'info@techflow.com', subject
    if cc:
        m['Cc'] = cc
    m['Date'], m['Message-ID'] = 'Wed, 21 Oct 2026 11:00:00 +0530', message_id
    m.set_content(body)
    return m.as_bytes()


def _contact(org_id, customer_id, email):
    from db import db
    return next(c for c in db.execute_proc('sp_list_contacts', (org_id, [customer_id])) if c['email'] == email)


def test_contacts_people_on_a_project_and_who_the_emails_suggest(client, gst_org):
    import emailsync
    import projects
    from db import db, DatabaseError
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    domain = f'gearco{tag}.example'
    parent = _customer(org_id, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    site = _customer(org_id, f'Gear Cutters {tag} Hosur', 'Tamil Nadu', 'India')
    db.execute_proc('sp_set_customer_parent', (site, org_id, parent, 'Hosur plant'), fetch=False)
    project_id = projects.create_project(org_id, site, 'Hob arbor set')
    project_page = f'/projects/{project_id}'
    api = lambda path: client.get(f'/api{path}').get_json()

    # Contacts on the parent company; one email address once per customer
    page = client.post(f'/customers/{parent}/contacts', follow_redirects=True, data={
        'name': 'Ravi Kumar', 'email': f'Ravi.K@{domain}', 'role': 'Purchase', 'gets': 'all'}).get_data(as_text=True)
    assert 'Ravi Kumar added to the contacts' in page
    assert f'ravi.k@{domain}' in [p['email'] for p in api(f'/customers/{parent}')['people']]
    page = client.post(f'/customers/{parent}/contacts', data={'name': 'Again', 'email': f'ravi.k@{domain}'},
                       follow_redirects=True).get_data(as_text=True)
    assert 'is already a contact here' in page
    client.post(f'/customers/{parent}/contacts', data={'name': 'Divya', 'email': f'accounts@{domain}', 'role': 'Accounts',
                                                       'gets': 'billing'})
    ravi, divya = _contact(org_id, parent, f'ravi.k@{domain}'), _contact(org_id, parent, f'accounts@{domain}')

    # The site's project uses the parent's contacts, each with what they usually get, changeable per project
    people = {c['name']: c['project_gets'] for c in db.execute_proc('sp_list_project_contacts', (project_id, org_id))}
    assert people == {'Ravi Kumar': 'all', 'Divya': 'billing'}
    response = client.post(f'{project_page}/people', data={'contact_id': divya['contact_id'], 'gets': 'none'})
    assert response.headers['Location'].endswith(f'{project_page}#people')
    people = {c['name']: c['project_gets'] for c in db.execute_proc('sp_list_project_contacts', (project_id, org_id))}
    assert people['Divya'] == 'none' and _contact(org_id, parent, f'accounts@{domain}')['gets'] == 'billing'
    customer = api(f'/customers/{parent}')
    assert customer['usually'][{p['name']: p['gets'] for p in customer['people']}['Divya']] == 'Proformas and invoices'

    # Mail on the project: Ravi (a phone in his signature, copying Arun), and Meera, who isn't a contact yet
    label = projects.project_label(projects.get_project(project_id, org_id))
    account = db.execute_proc_single('sp_upsert_email_account', (org_id, 'info@techflow.com', 'TEST'))
    linker = emailsync.Linker(org_id, {'techflow.com'})
    for raw in (_mail(f'{label} PO for hob arbors', f'Ravi Kumar <ravi.k@{domain}>', SIGNATURE, f'<po.{tag}@{domain}>',
                      cc=f'arun.s@{domain}, md@techflow.com'),
                _mail(f'Re: {label} PO for hob arbors', f'Meera Iyer <meera@{domain}>', 'Inspection on Friday.', f'<i.{tag}@{domain}>')):
        linker.store(account['account_id'], emailsync.parse_message(raw, org_domains={'techflow.com'}))
    found = api(f'/projects/{project_id}')['found']
    assert [(p['name'], p['phone']) for p in found['phones']] == [('Ravi Kumar', '+91 98765 43210')]
    assert {'Meera Iyer', 'Arun S'} <= {p['name'] for p in found['people']}
    assert 'md@techflow.com' not in [p['email'] for p in found['people']]

    # Ignore one; add another from the suggestion (back to the project); save the phone to Ravi
    client.post(f'/customers/{site}/ignore-suggestion', data={'value': f'arun.s@{domain}', 'project_id': project_id})
    response = client.post(f'/customers/{site}/contacts', data={'name': 'Meera Iyer', 'email': f'meera@{domain}',
                                                                'role': 'Quality', 'project_id': project_id})
    assert response.headers['Location'].endswith(f'{project_page}#people')
    client.post(f"/customers/{parent}/contacts/{ravi['contact_id']}", data={
        'name': 'Ravi Kumar', 'email': ravi['email'], 'role': 'Purchase', 'gets': 'all', 'phone': '+91 98765 43210',
        'project_id': project_id})
    assert _contact(org_id, parent, f'ravi.k@{domain}')['phone'] == '+91 98765 43210'
    project = api(f'/projects/{project_id}')
    assert project['found'] == {'people': [], 'phones': []}
    assert {p['name']: p['role'] for p in project['people']}['Meera Iyer'] == 'Quality'

    # Viewers see the people but change nothing and see nothing from the mailbox; Sales change people, no mailbox
    login(client, VIEWER)
    project = api(f'/projects/{project_id}')
    assert 'Ravi Kumar' in [p['name'] for p in project['people']]
    assert not project['can']['edit'] and not project['can']['read_mail'] and project['found'] == {'people': [], 'phones': []}
    client.post(f'/customers/{parent}/contacts', data={'name': 'Not added', 'email': f'no@{domain}'})
    assert not [c for c in db.execute_proc('sp_list_contacts', (org_id, [parent])) if c['name'] == 'Not added']
    login(client, OWNER)
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        client.post(f'/customers/{site}/contacts', data={'name': 'Sundar', 'email': f'new.buyer@{domain}'})
        linker.store(account['account_id'], emailsync.parse_message(
            _mail(f'Re: {label} PO for hob arbors', f'Kumar <kumar@{domain}>', 'Noted.', f'<k.{tag}@{domain}>'),
            org_domains={'techflow.com'}))
        project = api(f'/projects/{project_id}')
        assert 'Sundar' in [p['name'] for p in project['people']] and project['can']['edit']
        assert project['found'] == {'people': [], 'phones': []}
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
    assert api(f'/projects/{project_id}')['found']['people']        # Kumar, for the owner

    # Another organization's ids get nowhere; removing a contact takes them off the project
    try:
        db.execute_proc('sp_save_contact', (str(uuid.uuid4()), ravi['contact_id'], parent, 'X', None, None, None, 'all'))
        raise AssertionError('saved into another organization')
    except DatabaseError as e:
        assert 'Customer not found' in str(e)
    other_customer = _customer(org_id, f'Other Works {tag}', 'Kerala', 'India')
    other = db.execute_proc_single('sp_save_contact', (org_id, None, other_customer, 'Elsewhere', None, None, None, 'all'))
    try:
        db.execute_proc('sp_set_project_contact', (project_id, org_id, other['contact_id'], 'all'))
        raise AssertionError("another customer's contact joined the project")
    except DatabaseError as e:
        assert 'Contact not found' in str(e)
    page = client.post(f"/customers/{parent}/contacts/{divya['contact_id']}/delete", follow_redirects=True).get_data(as_text=True)
    assert 'Contact removed' in page
    assert 'Divya' not in {c['name'] for c in db.execute_proc('sp_list_project_contacts', (project_id, org_id))}
