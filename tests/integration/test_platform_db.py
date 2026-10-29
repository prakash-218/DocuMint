"""
Email sync, notifications, the admin role and bucket storage, against real services:
PostgreSQL (see conftest.py), a GreenMail IMAP/SMTP server and an S3-compatible mock.

    docker run -d --name documint-mail -e GREENMAIL_OPTS="-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 -Dgreenmail.auth.disabled" -p 3143:3143 -p 3025:3025 greenmail/standalone:2.0.1
    docker run -d --name documint-s3 -e initialBuckets=documint -p 9010:9090 adobe/s3mock:3.11.0
"""

import imaplib
import io
import re
import smtplib
import socket
import uuid
from email.message import EmailMessage

import pytest

from tests.integration.test_documents_db import PROFILE, _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401

PDF = b'%PDF-1.4\n% drawing\n'


def _port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def _send(sender, to, subject, body='Hello', message_id=None, in_reply_to=None, files=()):
    m = EmailMessage()
    m['From'], m['To'], m['Subject'] = sender, to, subject
    m['Message-ID'] = message_id or f'<{uuid.uuid4().hex}@test>'
    if in_reply_to:
        m['In-Reply-To'] = m['References'] = in_reply_to
    m.set_content(body)
    for name, data in files:
        m.add_attachment(data, maintype='application', subtype='pdf', filename=name)
    with smtplib.SMTP('127.0.0.1', 3025) as s:
        s.send_message(m)
    return m['Message-ID']


@pytest.mark.skipif(not _port_open(3143), reason='GreenMail (IMAP on 3143) is not running')
def test_email_sync_links_threads_to_projects(client, gst_org, monkeypatch):
    import emailsync
    import projects
    from db import db
    org_id = gst_org
    mailbox = f'info.{uuid.uuid4().hex[:6]}@techflow.com'          # a fresh GreenMail mailbox per run
    for k, v in {'EMAIL_ACCOUNTS': 'TF', 'TF_IMAP_HOST': '127.0.0.1', 'TF_IMAP_PORT': '3143', 'TF_IMAP_SSL': '0',
                 'TF_IMAP_USER': mailbox, 'TF_IMAP_PASSWORD': 'x', 'TF_IMAP_FOLDERS': 'INBOX'}.items():
        monkeypatch.setenv(k, v)

    customer = _customer(org_id, 'Acme Tools Ltd', 'Tamil Nadu', 'India')
    db.execute_proc('sp_update_customer_email_domains', (customer, org_id, 'acme-tools.com'), fetch=False)
    project_id = projects.create_project(org_id, customer, 'Fixtures for line 9')
    label = projects.project_label(projects.get_project(project_id, org_id))

    first = _send('Ravi <ravi@acme-tools.com>', mailbox, f'RFQ for fixtures {label}', 'Please quote 2 sets.',
                  files=[('Drawing A.pdf', PDF)])
    _send('Ravi <ravi@acme-tools.com>', mailbox, 'Re: RFQ for fixtures', 'Also add a spare.', in_reply_to=first)
    _send('Someone <someone@elsewhere.org>', mailbox, 'Hello there', 'Unrelated mail.')

    [result] = emailsync.sync_all()
    assert result['error'] is None and result['stored'] == 3
    assert emailsync.sync_all()[0]['stored'] == 0                     # nothing twice

    # Mail stays unread on the server (BODY.PEEK)
    box = imaplib.IMAP4('127.0.0.1', 3143)
    box.login(mailbox, 'x')
    box.select('INBOX', readonly=True)
    typ, data = box.search(None, 'UNSEEN')
    assert len(data[0].split()) == 3
    box.logout()

    linked = db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 10))
    assert len(linked) == 1 and linked[0]['message_count'] == 2 and linked[0]['file_count'] == 1
    assert linked[0]['customer_id'] == customer and linked[0]['linked_by'] == 'number'
    unlinked = db.execute_proc('sp_list_email_threads', (org_id, None, None, True, 50))
    hello = next(t for t in unlinked if t['subject'] == 'Hello there')
    assert hello['customer_id'] is None

    # Pages: project shows the thread; the inbox shows the unsorted one; the thread shows the mail
    assert 'RFQ for fixtures' in client.get(f'/projects/{project_id}/classic').get_data(as_text=True)
    assert 'Hello there' in client.get('/emails/').get_data(as_text=True)
    page = client.get(f"/emails/{linked[0]['thread_id']}").get_data(as_text=True)
    assert 'Please quote 2 sets.' in page and 'Also add a spare.' in page and 'Drawing A.pdf' in page
    file_id = re.search(r'/emails/files/([0-9a-f-]{36})', page).group(1)
    download = client.get(f'/emails/files/{file_id}')
    assert download.data == PDF and download.headers['X-Content-Type-Options'] == 'nosniff'

    # Linking by hand
    client.post(f"/emails/{hello['thread_id']}/project", data={'project_id': project_id})
    assert len(db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 10))) == 2

    # The owner hears about the customer's email (it came in, nobody in the team did it)
    notes = client.get('/notifications/').get_data(as_text=True)
    assert f'Email from Ravi: RFQ for fixtures {label}' in notes

    # Viewers don't read mail
    login(client, VIEWER)
    assert client.get('/emails/').status_code == 403
    login(client, OWNER)


@pytest.mark.skipif(not _port_open(3143), reason='GreenMail (IMAP on 3143) is not running')
def test_email_sync_match_keeps_personal_mail_out(gst_org, monkeypatch):
    """A personal mailbox that collects the company mail only copies the company's threads."""
    import emailsync
    from db import db
    mailbox = f'me.{uuid.uuid4().hex[:6]}@gmail.test'
    for k, v in {'EMAIL_ACCOUNTS': 'ME', 'ME_IMAP_HOST': '127.0.0.1', 'ME_IMAP_PORT': '3143', 'ME_IMAP_SSL': '0',
                 'ME_IMAP_USER': mailbox, 'ME_IMAP_PASSWORD': 'x', 'ME_IMAP_FOLDERS': 'INBOX',
                 'ME_IMAP_MATCH': 'techflow.com, acme-tools.com', 'EMAIL_ORG_DOMAIN': 'techflow.com'}.items():
        monkeypatch.setenv(k, v)
    tag = uuid.uuid4().hex[:6]
    _send('Ravi <ravi@acme-tools.com>', mailbox, f'Fixture drawings {tag}')
    _send('Bank <alerts@bank.example>', mailbox, f'Your statement {tag}')
    _send('Mom <mom@family.example>', f'{mailbox}, Sales <sales@techflow.com>', f'Dinner {tag}')   # cc'd/to company

    [result] = emailsync.sync_all()
    assert result['error'] is None and result['stored'] == 2
    subjects = {t['subject'] for t in db.execute_proc('sp_list_email_threads', (gst_org, None, None, False, 200))}
    assert {f'Fixture drawings {tag}', f'Dinner {tag}'} <= subjects and f'Your statement {tag}' not in subjects
    _send('Bank <alerts@bank.example>', mailbox, f'Another statement {tag}')
    _send('Ravi <ravi@acme-tools.com>', mailbox, f'Re: Fixture drawings {tag}')
    assert emailsync.sync_all()[0]['stored'] == 1                    # later runs filter too


def test_notifications_and_admin_role(client, gst_org):
    """Owners and admins hear about project activity; admins run the business but can't touch owners."""
    import projects
    from db import db
    org_id = gst_org
    members = {m['email']: m for m in db.execute_proc('sp_get_org_members', (org_id,))}
    viewer, owner = members[VIEWER], members[OWNER]

    from document_service import get_org_profile, set_next_number
    set_next_number(org_id, 'quote', get_org_profile(org_id)[1], 1200)
    # Owner makes the viewer an admin
    client.post('/settings/members/approve', data={'user_id': viewer['user_id'], 'action': 'change_role', 'role': 'admin'})
    try:
        _admin_checks(client, org_id, viewer, owner)
    finally:
        login(client, OWNER)
        client.post('/settings/members/approve', data={'user_id': viewer['user_id'], 'action': 'change_role', 'role': 'viewer'})
        assert {m['email']: m for m in db.execute_proc('sp_get_org_members', (org_id,))}[VIEWER]['role'] == 'viewer'


def _admin_checks(client, org_id, viewer, owner):
    import projects
    from db import db
    members = {m['email']: m for m in db.execute_proc('sp_get_org_members', (org_id,))}
    assert members[VIEWER]['role'] == 'admin'

    # The owner creates a quotation in a project: the admin is told, the owner isn't (they did it)
    customer = _customer(org_id, 'Bosch Ltd', 'Karnataka', 'India')
    project_id = projects.create_project(org_id, customer, 'Gauge set')
    quote_id, number = _create(client, org_id, 'quote', 'Quotation', customer,
                               [{'description': 'Gauge', 'price': 900, 'qty': 3}], project_id=project_id)
    admin_notes = db.execute_proc('sp_list_notifications', (viewer['user_id'], org_id, 20, True)) or []
    assert any(n['title'] == f'Quotation {number} created' and n['project_id'] == project_id for n in admin_notes)
    owner_notes = db.execute_proc('sp_list_notifications', (owner['user_id'], org_id, 20, True)) or []
    assert not any(n['title'] == f'Quotation {number} created' for n in owner_notes)
    assert f'Quotation {number} created' in client.get(f'/projects/{project_id}/classic').get_data(as_text=True)   # activity

    # As the admin: sees the badge, can open settings pages, can't make or change owners
    login(client, VIEWER)
    page = client.get('/dashboard/').get_data(as_text=True)
    assert 'nav-badge' in page
    assert client.get('/settings/audit-log').status_code == 200
    assert client.get('/settings/profile').status_code == 200
    client.post('/settings/members/approve', data={'user_id': owner['user_id'], 'action': 'change_role', 'role': 'member'})
    assert {m['email']: m for m in db.execute_proc('sp_get_org_members', (org_id,))}[OWNER]['role'] == 'owner'
    # opening a notification marks it read
    note = next(n for n in db.execute_proc('sp_list_notifications', (viewer['user_id'], org_id, 20, True))
                if n['title'] == f'Quotation {number} created')
    assert client.get(f"/notifications/{note['notification_id']}/open").status_code == 302
    assert not any(n['notification_id'] == note['notification_id']
                   for n in db.execute_proc('sp_list_notifications', (viewer['user_id'], org_id, 20, True)) or [])



@pytest.mark.skipif(not _port_open(9010), reason='S3 mock (port 9010) is not running')
def test_attachments_in_a_bucket(client, gst_org, monkeypatch):
    import storage
    import projects
    org_id = gst_org
    for k, v in {'S3_BUCKET': 'documint', 'S3_ENDPOINT': 'http://127.0.0.1:9010', 'S3_REGION': 'us-east-1',
                 'S3_ACCESS_KEY_ID': 'x', 'S3_SECRET_ACCESS_KEY': 'y', 'S3_ADDRESSING_STYLE': 'path'}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(storage._local, 'client', None, raising=False)
    customer = _customer(org_id, 'Bucket Test Pvt Ltd', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Bucket project')
    response = client.post('/projects/files', data={'project_id': project_id, 'kind': 'drawing', 'title': 'GA drawing',
                                                    'file': (io.BytesIO(PDF), 'ga.pdf')},
                           content_type='multipart/form-data', headers={'Referer': f'http://localhost/projects/{project_id}'})
    assert response.status_code == 302
    [f] = projects.list_attachments(org_id, project_id=project_id)
    assert storage.get(f['storage_key']) == PDF                       # really in the bucket
    assert client.get(f"/projects/files/{f['attachment_id']}").data == PDF
    client.post(f"/projects/files/{f['attachment_id']}/delete", headers={'Referer': f'http://localhost/projects/{project_id}'})
    with pytest.raises(Exception):
        storage.get(f['storage_key'])
    monkeypatch.setattr(storage._local, 'client', None, raising=False)
