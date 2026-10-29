"""
Sending email from a project, against PostgreSQL and a GreenMail SMTP/IMAP server (see test_platform_db.py):
the customer gets the quotation as a PDF, a copy goes to Sent, and the conversation stays in one thread.
"""

import email
import imaplib
import uuid
from email import policy

import pytest

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_platform_db import _port_open, _send
from tests.integration.test_sales_role_db import _set_role

pytestmark = [pytestmark, pytest.mark.skipif(not (_port_open(3025) and _port_open(3143)),
                                             reason='GreenMail (SMTP 3025, IMAP 3143) is not running')]


def _inbox(address, folder='INBOX'):
    box = imaplib.IMAP4('127.0.0.1', 3143)
    box.login(address, 'x')
    box.select(folder, readonly=True)
    _, data = box.search(None, 'ALL')
    messages = [email.message_from_bytes(box.fetch(n, '(RFC822)')[1][0][1], policy=policy.default) for n in data[0].split()]
    box.logout()
    return messages


def test_a_quotation_emailed_from_its_project(client, gst_org, monkeypatch):
    import emailsync
    import projects
    from db import db
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    mailbox, domain = f'desk.{tag}@techflow.com', f'gearco{tag}.example'
    ravi, accounts = f'ravi@{domain}', f'accounts@{domain}'
    for k, v in {'EMAIL_ACCOUNTS': 'TF', 'TF_IMAP_HOST': '127.0.0.1', 'TF_IMAP_PORT': '3143', 'TF_IMAP_SSL': '0',
                 'TF_IMAP_USER': mailbox, 'TF_IMAP_PASSWORD': 'x', 'TF_IMAP_FOLDERS': 'INBOX,Sent',
                 'TF_SMTP_HOST': '127.0.0.1', 'TF_SMTP_PORT': '3025', 'TF_SMTP_SSL': '0', 'TF_SMTP_STARTTLS': '0'}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv('EMAIL_SEND_FROM', raising=False)

    customer = _customer(org_id, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Hob arbor set')
    label = projects.project_label(projects.get_project(project_id, org_id))
    for name, address, gets in (('Ravi Kumar', ravi, 'all'), ('Divya', accounts, 'billing')):
        db.execute_proc('sp_save_contact', (org_id, None, customer, name, address, None, None, gets), fetch=False)
    quote_id, quote_no = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Hob arbor', 'price': 9000, 'qty': 3}],
                                 tax_mode='none', project_id=project_id)
    assert client.post(f'/quotes/{quote_id}/finalize').status_code == 302

    # The form starts with Ravi (gets everything; Divya only gets proformas and invoices) and the quotation
    form = client.get(f'/api/projects/{project_id}/compose?invoice_id={quote_id}').get_json()
    assert form['can_send'] and form['from'] == mailbox
    assert form['to'] == [ravi] and form['cc'] == [] and form['attach'] == [quote_id] and form['thread_id'] is None
    assert form['subject'] == f'Quotation {quote_no} · Hob arbor set ({label})'
    assert form['body'].startswith('Dear Ravi Kumar,') and quote_no in form['body']

    response = client.post(f'/api/projects/{project_id}/emails', json={
        'to': form['to'], 'cc': [accounts], 'subject': form['subject'], 'body': form['body'], 'thread_id': None,
        'invoice_ids': [quote_id]})
    assert response.status_code == 201, response.get_json()
    sent = response.get_json()
    assert sent['to'] == [ravi] and sent['cc'] == [accounts] and sent['saved_to'] == 'Sent'

    # Ravi has it, from the mailbox, with the PDF; Divya was copied; a copy is in Sent
    [got] = _inbox(ravi)
    assert got['From'].addresses[0].addr_spec == mailbox and got['Subject'] == form['subject']
    [pdf] = list(got.iter_attachments())
    assert pdf.get_content_type() == 'application/pdf' and pdf.get_content()[:5] == b'%PDF-'
    assert len(_inbox(accounts)) == 1
    [copy] = _inbox(mailbox, 'Sent')
    assert copy['Message-ID'] == got['Message-ID']

    # It's on the project: a thread of ours, and the activity says who got what
    [thread] = db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 10))
    assert thread['thread_id'] == sent['thread_id'] and thread['message_count'] == 1
    events = db.execute_proc('sp_list_project_events', (project_id, org_id, 30))
    assert f'Emailed Quotation {quote_no} to Ravi Kumar' in [e['title'] for e in events]
    [mail] = [t for t in client.get(f'/api/projects/{project_id}').get_json()['timeline'] if t['type'] == 'email']
    assert mail['direction'] == 'out' and ravi in mail['who']

    # Ravi answers; the sync files it in the same thread, and doesn't store our copy in Sent a second time
    _send(f'Ravi Kumar <{ravi}>', mailbox, f"Re: {form['subject']}", 'Thanks, PO follows.', in_reply_to=got['Message-ID'])
    [result] = emailsync.sync_all()
    assert result['error'] is None and result['stored'] == 1
    [thread] = db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 10))
    assert thread['message_count'] == 2

    # Replying keeps the thread: the form offers it, and the email refers to Ravi's
    form = client.get(f"/api/projects/{project_id}/compose?thread_id={thread['thread_id']}").get_json()
    assert form['thread_id'] == thread['thread_id'] and form['subject'].lower().startswith('re: ')
    response = client.post(f'/api/projects/{project_id}/emails', json={
        'to': [ravi], 'subject': form['subject'], 'body': 'Noted, thank you.', 'thread_id': thread['thread_id']})
    assert response.status_code == 201 and response.get_json()['thread_id'] == thread['thread_id']
    reply = next(m for m in _inbox(ravi) if m['Subject'] == form['subject'] and 'Noted' in m.get_body().get_content())
    assert reply['In-Reply-To'] and reply['In-Reply-To'] != got['Message-ID']        # Ravi's message, not ours

    # What gets refused, and why
    def refused(data):
        r = client.post(f'/api/projects/{project_id}/emails', json={'to': [ravi], 'subject': 's', 'body': 'b', **data})
        return r.status_code, r.get_json()['error']
    assert refused({'to': ['ravi at gearco']}) == (400, '"ravi at gearco" isn\'t an email address.')
    assert refused({'to': []}) == (400, 'Add at least one person in To.')
    assert refused({'thread_id': str(uuid.uuid4())}) == (400, "That thread isn't on this project.")
    draft_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Spare', 'price': 100, 'qty': 1}],
                          tax_mode='none', project_id=project_id)
    status, error = refused({'invoice_ids': [draft_id]})
    assert status == 400 and 'finalize it first' in error

    # Sales send their quotations as new emails, but don't reply in the mailbox's threads; viewers don't send
    _set_role(client, VIEWER, 'sales')
    try:
        login(client, VIEWER)
        form = client.get(f'/api/projects/{project_id}/compose').get_json()
        assert form['threads'] == [] and form['found'] == []
        assert refused({'thread_id': thread['thread_id']})[0] == 400
        response = client.post(f'/api/projects/{project_id}/emails', json={
            'to': [ravi], 'subject': 'Our quotation', 'body': 'Attached.', 'invoice_ids': [quote_id]})
        assert response.status_code == 201
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')
        login(client, VIEWER)
        assert client.get(f'/api/projects/{project_id}/compose').status_code == 403
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')

    # Without SMTP settings the form says sending isn't set up, and nothing goes out
    monkeypatch.delenv('TF_SMTP_HOST')
    form = client.get(f'/api/projects/{project_id}/compose').get_json()
    assert form['can_send'] is False and "isn't set up" in form['why_not']
    assert refused({})[0] == 400


def test_through_a_collecting_mailbox_as_the_company_address(client, gst_org, monkeypatch):
    """Like a Gmail that collects the company mail: it sends as the company's address, and keeps its own Sent copy."""
    import projects
    from db import db
    org_id, tag = gst_org, uuid.uuid4().hex[:6]
    collector, desk, buyer = f'collector.{tag}@mailhost.example', f'desk.{tag}@techflow.com', f'buyer@gearco{tag}.example'
    for k, v in {'EMAIL_ACCOUNTS': 'GM', 'GM_IMAP_HOST': '127.0.0.1', 'GM_IMAP_PORT': '3143', 'GM_IMAP_SSL': '0',
                 'GM_IMAP_USER': collector, 'GM_IMAP_PASSWORD': 'x', 'GM_SMTP_HOST': '127.0.0.1', 'GM_SMTP_PORT': '3025',
                 'GM_SMTP_SSL': '0', 'GM_SMTP_STARTTLS': '0', 'GM_SMTP_FROM': desk, 'GM_SAVE_SENT': '0'}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv('EMAIL_SEND_FROM', raising=False)
    customer = _customer(org_id, f'Gear Cutters {tag}', 'Tamil Nadu', 'India')
    project_id = projects.create_project(org_id, customer, 'Spline gauges')

    form = client.get(f'/api/projects/{project_id}/compose').get_json()
    assert form['can_send'] and form['from'] == desk
    response = client.post(f'/api/projects/{project_id}/emails', json={'to': [buyer], 'subject': form['subject'], 'body': 'Hello.'})
    assert response.status_code == 201 and response.get_json()['saved_to'] is None
    [got] = _inbox(buyer)
    assert got['From'].addresses[0].addr_spec == desk
    # filed under the collecting mailbox, which is the one the sync reads
    [thread] = db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 10))
    message = db.execute_proc('sp_get_email_thread', (thread['thread_id'], org_id))[1]
    assert message[0]['mailbox'] == collector and message[0]['direction'] == 'out'
