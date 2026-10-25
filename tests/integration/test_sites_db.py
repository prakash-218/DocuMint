"""Customer sites, and email attachments joining the project their thread is in."""

import os
import re
import uuid
from email.message import EmailMessage

import pytest

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import _customer, app, client, gst_org  # noqa: F401


def _created_id(response):
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    return re.search(r'/customers/([0-9a-f-]{36})', response.headers['Location']).group(1)


def test_customer_sites(client, gst_org):
    import emailsync
    from db import DatabaseError, db
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    name = f'TAFE {tag}'
    parent = _created_id(client.post('/customers/create', data={
        'name': name, 'tax_id': '33AAACT2761Q1Z1', 'city': 'Chennai', 'country': 'India',
        'email_domains': f'tafe{tag}.com', 'parent_id': ''}))

    # "Add site" starts from the parent's details
    page = client.get(f'/customers/create?parent_id={parent}').get_data(as_text=True)
    assert f'value="{name}"' in page and f'<option value="{parent}" selected>' in page
    gears = _created_id(client.post('/customers/create', data={
        'name': name, 'parent_id': parent, 'site_name': 'Gears Division', 'city': 'Pudupakkam', 'country': 'India'}))
    madurai = _created_id(client.post('/customers/create', data={
        'name': name, 'parent_id': parent, 'site_name': '', 'city': 'Madurai', 'country': 'India',
        'email_domains': f'tafe{tag}.com'}))          # the same domain as its parent
    sites = db.execute_proc('sp_list_customer_sites', (org_id, parent))
    assert [s['site'] for s in sites] == ['Gears Division', 'Madurai']                  # site name, else city

    # One level deep, and not a site of itself
    loner = _customer(org_id, f'Loner {tag}', 'Tamil Nadu', 'India')
    for customer_id, parent_id, error in [(loner, gears, 'itself a site'), (parent, loner, 'has sites'),
                                          (loner, loner, 'site of itself')]:
        with pytest.raises(DatabaseError, match=error):
            db.execute_proc('sp_set_customer_parent', (customer_id, org_id, parent_id, None), fetch=False)
    with pytest.raises(DatabaseError, match='has sites'):
        db.execute_proc('sp_delete_customer', (parent, org_id), fetch=False)
    edit = client.get(f'/customers/{parent}/edit').get_data(as_text=True)
    assert '2 sites belong to this customer' in edit and 'name="parent_id"' not in edit

    # Pickers group the sites under their customer; lists say which site
    picker = client.get('/projects/new').get_data(as_text=True)
    group = picker[picker.index(f'<optgroup label="{name}">'):]
    group = group[:group.index('</optgroup>')]
    assert [parent, gears, madurai] == re.findall(r'value="([0-9a-f-]{36})"', group)
    assert '>Gears Division<' in group and '>Madurai<' in group
    response = client.post('/projects/new', data={'customer_id': gears, 'title': 'Spline gauges'})
    project_id = re.search(r'/projects/([0-9a-f-]{36})', response.headers['Location']).group(1)
    assert f'{name} · Gears Division' in client.get(f'/projects/{project_id}').get_data(as_text=True)

    # The parent's page has its sites and their projects; a site's page names its parent
    page = client.get(f'/customers/{parent}').get_data(as_text=True)
    assert 'Add site' in page and 'Gears Division' in page and 'Spline gauges' in page
    assert f'of <a href="/customers/{parent}">{name}</a>' in client.get(f'/customers/{madurai}').get_data(as_text=True)
    listing = client.get(f'/customers/?q=madurai').get_data(as_text=True)
    assert name in listing and 'Madurai' in listing and 'row-site' in listing and 'Gears Division' not in listing

    # Mail from the shared domain goes to the parent (which site isn't known until it's put in a project)
    m = {'from_address': f'buyer@tafe{tag}.com', 'direction': 'in', 'to': [], 'cc': []}
    assert emailsync.Linker(org_id, {'techflow.com'}).customer_for(m) == parent


def _mail(subject, files, message_id, in_reply_to=None, sender='Ravi <ravi@acme-tools.com>'):
    m = EmailMessage()
    m['From'], m['To'], m['Subject'] = sender, 'info@techflow.com', subject
    m['Date'], m['Message-ID'] = 'Tue, 20 Oct 2026 10:15:00 +0530', message_id
    if in_reply_to:
        m['In-Reply-To'] = m['References'] = in_reply_to
    m.set_content('See attached.')
    for name, data in files:
        maintype, subtype = ('image', 'png') if name.endswith('.png') else ('application', 'octet-stream')
        m.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    return m.as_bytes()


def test_thread_files_join_the_project(client, gst_org):
    import emailsync
    import projects
    from db import db
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    customer = _customer(org_id, 'Acme Tools Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, f'Jig {tag}')
    account = db.execute_proc_single('sp_upsert_email_account', (org_id, 'info@techflow.com', 'TEST'))
    linker = emailsync.Linker(org_id, {'techflow.com'})

    def store(raw):
        return linker.store(account['account_id'], emailsync.parse_message(raw, org_domains={'techflow.com'}))

    drawing, po = b'%PDF-1.4 drawing ' + tag.encode(), b'%PDF-1.4 po ' + tag.encode()
    photo, logo = b'\x89PNG' + os.urandom(40_000), b'\x89PNG' + b'0' * 500
    first = f'<a.{tag}@acme-tools.com>'
    thread_id = store(_mail(f'Jig enquiry {tag}', [('Drawing A.pdf', drawing), ('logo.png', logo)], first))['thread_id']
    store(_mail(f'Re: Jig enquiry {tag}', [('Drawing A.pdf', drawing), ('PO 4500.pdf', po), ('photo.png', photo)],
                f'<b.{tag}@acme-tools.com>', in_reply_to=first))

    # Linking copies the attachments once each, without the logo
    response = client.post(f'/emails/{thread_id}/project', data={'project_id': project_id}, follow_redirects=True)
    assert 'Added to the project, with 3 files (1 already there)' in response.get_data(as_text=True)
    files = projects.list_attachments(org_id, project_id=project_id)
    assert {f['file_name']: f['kind'] for f in files} == {'Drawing A.pdf': 'drawing', 'PO 4500.pdf': 'po',
                                                         'photo.png': 'other'}
    assert {f['email_thread_id'] for f in files} == {thread_id}
    page = client.get(f'/projects/{project_id}').get_data(as_text=True)
    assert 'From email' in page and f'/emails/{thread_id}' in page
    pdf = client.get(f"/projects/files/{next(f['attachment_id'] for f in files if f['kind'] == 'po')}")
    assert pdf.data == po

    # Later mail in the thread brings its new files along, not the repeats
    store(_mail(f'Re: Jig enquiry {tag}', [('Drawing A.pdf', drawing), ('Drawing B rev1.dwg', b'AC1027' + tag.encode())],
                f'<c.{tag}@acme-tools.com>', in_reply_to=first))
    files = projects.list_attachments(org_id, project_id=project_id)
    assert sorted(f['file_name'] for f in files) == ['Drawing A.pdf', 'Drawing B rev1.dwg', 'PO 4500.pdf', 'photo.png']

    # Moving the thread moves its files; taking it out takes them out; the emails keep theirs
    other = projects.create_project(org_id, customer, f'Other {tag}')
    client.post(f'/emails/{thread_id}/project', data={'project_id': other})
    assert projects.list_attachments(org_id, project_id=project_id) == []
    assert len(projects.list_attachments(org_id, project_id=other)) == 4
    response = client.post(f'/emails/{thread_id}/project', data={'project_id': ''}, follow_redirects=True)
    assert 'with the 4 files it had added' in response.get_data(as_text=True)
    assert projects.list_attachments(org_id, project_id=other) == []
    assert 'Drawing B rev1.dwg' in client.get(f'/emails/{thread_id}').get_data(as_text=True)



def test_every_list_page_is_paged(client, gst_org):
    """Each list renders on any page number (past the end shows the last page), with a pager when it's long."""
    import emailsync
    from db import db
    org_id = gst_org
    account = db.execute_proc_single('sp_upsert_email_account', (org_id, 'info@techflow.com', 'TEST'))
    linker = emailsync.Linker(org_id, {'techflow.com'})
    tag = uuid.uuid4().hex[:6]
    for i in range(30):                                           # more than a page of threads
        linker.store(account['account_id'], emailsync.parse_message(
            _mail(f'Paging check {tag} #{i:02d}', [], f'<p{i}.{tag}@acme-tools.com>'), org_domains={'techflow.com'}))
    first = client.get('/emails/?show=all').get_data(as_text=True)
    assert 'class="pager"' in first and '?show=all&amp;page=2' in first
    total = db.execute_proc_single('sp_count_email_threads', (org_id, None, None, False))['n']
    assert f'1–25 of {total} threads' in first
    last = client.get('/emails/?show=all&page=999').get_data(as_text=True)
    assert f'of {total} threads' in last and 'aria-current="page"' in last

    for path in ['/quotes/', '/proformas/', '/invoices/', '/projects/?status=all', '/customers/', '/templates/',
                 '/notifications/?show=all', '/settings/audit-log']:
        for page in (1, 2, 999, 'x'):
            response = client.get(f"{path}{'&' if '?' in path else '?'}page={page}")
            assert response.status_code == 200, (path, page, response.status_code)
