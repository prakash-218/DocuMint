"""
A customer's statement against real PostgreSQL (same opt-in as test_app_db.py): the PDF for a year or every year,
the email form with their billing contact and the PDF attached, who may do which, and (with GreenMail running,
see test_platform_db.py) the email going out with the statement on it.
"""

import email
import imaplib
import uuid
from email import policy

import pytest

from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401
from tests.integration.test_documents_db import _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_platform_db import _port_open
from tests.integration.test_sales_role_db import _set_role


def _account(client, org_id, tag):
    """A customer with a billing contact, a finalized invoice of ₹50,000 and ₹20,000 paid on it."""
    from db import db
    customer = _customer(org_id, f'Collet Works {tag}', 'Tamil Nadu', 'India')
    db.execute_proc('sp_save_contact', (org_id, None, customer, 'Divya', f'accounts@collet{tag}.example', None, 'Accounts', 'billing'),
                    fetch=False)
    invoice_id, number = _create(client, org_id, 'invoice', 'Tax Invoice', customer, [{'description': 'Collet chuck', 'rate': 50000, 'qty': 1}],
                                 tax_mode='none')
    assert client.post(f'/invoices/{invoice_id}/finalize').status_code == 302
    assert client.post(f'/invoices/{invoice_id}/payment', data={'amount': '20000', 'method': 'NEFT / RTGS'}).status_code == 302
    return customer, invoice_id, number


def test_the_statement_prints_and_its_email_form_starts_with_the_billing_contact(client, gst_org):
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    customer, _, number = _account(client, org_id, tag)

    for query in ('', '?fy=all', '?fy=all&currency=INR&download=1'):
        pdf = client.get(f'/customers/{customer}/statement.pdf{query}')
        assert pdf.status_code == 200 and pdf.headers['Content-Type'] == 'application/pdf' and pdf.data.startswith(b'%PDF')
    assert pdf.headers['Content-Disposition'].startswith('attachment; filename="Statement-Collet-Works-')
    page = client.get(f'/api/customers/{customer}').get_json()
    assert page['links']['statement_pdf'] == f'/customers/{customer}/statement.pdf'
    assert page['links']['statement_email'] == {'compose': f'/api/customers/{customer}/statement/compose',
                                               'send': f'/api/customers/{customer}/statement/emails'}

    form = client.get(f'/api/customers/{customer}/statement/compose?fy=all').get_json()
    assert form['to'] == [f'accounts@collet{tag}.example'] and form['attach'] == ['statement'] and form['fy'] == 'all'
    assert form['subject'] == f'Statement of account to date · Collet Works {tag}'
    assert form['body'].startswith('Dear Divya,') and 'The balance due is ₹30,000.' in form['body']

    # Viewers can print it but not email it; Sales see no money, so neither
    _set_role(client, VIEWER, 'viewer')
    login(client, VIEWER)
    try:
        assert client.get(f'/customers/{customer}/statement.pdf').status_code == 200
        assert client.get(f'/api/customers/{customer}/statement/compose').status_code == 403
        assert client.post(f'/api/customers/{customer}/statement/emails', json={}).status_code == 403
        assert client.get(f'/api/customers/{customer}').get_json()['links']['statement_email'] is None
        login(client, OWNER)
        _set_role(client, VIEWER, 'sales')
        login(client, VIEWER)
        assert client.get(f'/customers/{customer}/statement.pdf').status_code == 302
        assert client.get(f'/api/customers/{customer}/statement/compose').status_code == 403
    finally:
        login(client, OWNER)
        _set_role(client, VIEWER, 'viewer')


@pytest.mark.skipif(not (_port_open(3025) and _port_open(3143)), reason='GreenMail (SMTP 3025, IMAP 3143) is not running')
def test_the_statement_goes_out_by_email(client, gst_org, monkeypatch):
    org_id, tag = gst_org, uuid.uuid4().hex[:5]
    mailbox = f'desk.{tag}@techflow.com'
    for k, v in {'EMAIL_ACCOUNTS': 'TF', 'TF_IMAP_HOST': '127.0.0.1', 'TF_IMAP_PORT': '3143', 'TF_IMAP_SSL': '0',
                 'TF_IMAP_USER': mailbox, 'TF_IMAP_PASSWORD': 'x', 'TF_IMAP_FOLDERS': 'INBOX,Sent',
                 'TF_SMTP_HOST': '127.0.0.1', 'TF_SMTP_PORT': '3025', 'TF_SMTP_SSL': '0', 'TF_SMTP_STARTTLS': '0'}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv('EMAIL_SEND_FROM', raising=False)
    customer, _, _ = _account(client, org_id, tag)
    form = client.get(f'/api/customers/{customer}/statement/compose').get_json()
    assert form['can_send'] and form['from'] == mailbox

    sent =client.post(f'/api/customers/{customer}/statement/emails',
                       json={'to': form['to'], 'cc': [], 'subject': form['subject'], 'body': form['body'],
                             'invoice_ids': form['attach'], 'fy': form['fy'], 'currency': form['currency']})
    assert sent.status_code == 201, sent.get_data(as_text=True)
    result = sent.get_json()
    assert result['to'] == form['to'] and result['attached'][0].startswith('Statement-Collet-Works-') and result['thread_id']

    box = imaplib.IMAP4('127.0.0.1', 3143)
    box.login(form['to'][0], 'x')
    box.select('INBOX', readonly=True)
    _, found = box.search(None, 'ALL')
    got = email.message_from_bytes(box.fetch(found[0].split()[-1], '(RFC822)')[1][0][1], policy=policy.default)
    box.logout()
    assert got['Subject'] == form['subject']
    [pdf] = [part for part in got.iter_attachments()]
    assert pdf.get_content_type() == 'application/pdf' and pdf.get_content().startswith(b'%PDF')
    assert client.post(f'/api/customers/{customer}/statement/emails', json={'to': [], 'subject': 'x', 'body': 'y'}).status_code == 400
