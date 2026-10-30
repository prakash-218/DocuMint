"""Sending email from the app: settings, the message, who it goes to, and who may send."""

import pytest

import mailsend
from tests.fakedb import ORG_A

IMAP = {'EMAIL_ACCOUNTS': 'DESK', 'DESK_IMAP_HOST': 'imap.ourworks.example', 'DESK_IMAP_USER': 'desk@ourworks.example',
        'DESK_IMAP_PASSWORD': 'imap-secret'}


@pytest.fixture
def mailbox(monkeypatch):
    for k in ('EMAIL_SEND_FROM', 'EMAIL_ORG_DOMAIN', 'DESK_SMTP_HOST', 'DESK_SMTP_PORT', 'DESK_SMTP_SSL', 'DESK_SMTP_USER',
              'DESK_SMTP_PASSWORD', 'DESK_SMTP_FROM', 'DESK_SAVE_SENT'):
        monkeypatch.delenv(k, raising=False)
    for k, v in IMAP.items():
        monkeypatch.setenv(k, v)
    return monkeypatch


def test_sending_is_off_until_the_smtp_host_is_set(mailbox):
    assert mailsend.sender_config() is None
    mailbox.setenv('DESK_SMTP_HOST', 'smtp.ourworks.example')
    cfg = mailsend.sender_config()
    assert (cfg['smtp_host'], cfg['smtp_port'], cfg['smtp_ssl'], cfg['smtp_starttls']) == ('smtp.ourworks.example', 465, True, False)
    assert (cfg['smtp_user'], cfg['smtp_password']) == ('desk@ourworks.example', 'imap-secret')    # the mailbox's login


def test_port_587_with_starttls_and_its_own_login(mailbox):
    for k, v in {'DESK_SMTP_HOST': 'smtp.ourworks.example', 'DESK_SMTP_SSL': '0', 'DESK_SMTP_USER': 'sender',
                 'DESK_SMTP_PASSWORD': 'smtp-secret'}.items():
        mailbox.setenv(k, v)
    cfg = mailsend.sender_config()
    assert (cfg['smtp_port'], cfg['smtp_ssl'], cfg['smtp_starttls'], cfg['smtp_user']) == (587, False, True, 'sender')


def test_through_gmail_as_the_company_address(mailbox, fake_db):
    for k, v in {'DESK_IMAP_HOST': 'imap.gmail.com', 'DESK_IMAP_USER': 'collector@gmail.com', 'DESK_SMTP_HOST': 'smtp.gmail.com',
                 'DESK_SMTP_FROM': 'Desk@A.com'}.items():
        mailbox.setenv(k, v)
    cfg = mailsend.sender_config()
    assert (cfg['address'], cfg['from_address'], cfg['save_sent']) == ('collector@gmail.com', 'desk@a.com', False)
    assert mailsend.sender_for(ORG_A)['from_address'] == 'desk@a.com'      # a.com is Org A's domain
    mailbox.setenv('DESK_SAVE_SENT', '1')
    assert mailsend.sender_config()['save_sent'] is True


def test_a_gmail_sending_as_itself_belongs_to_the_domain_its_mail_is_filed_under(mailbox, fake_db):
    for k, v in {'DESK_IMAP_USER': 'collector@gmail.com', 'DESK_SMTP_HOST': 'smtp.gmail.com'}.items():
        mailbox.setenv(k, v)
    assert mailsend.sender_for(ORG_A) is None                 # gmail.com is nobody's organization
    mailbox.setenv('EMAIL_ORG_DOMAIN', 'a.com')
    assert mailsend.sender_for(ORG_A)['from_address'] == 'collector@gmail.com'


def test_email_send_from_picks_the_mailbox(mailbox):
    for k, v in {'EMAIL_ACCOUNTS': 'DESK,OTHER', 'OTHER_IMAP_HOST': 'h', 'OTHER_IMAP_USER': 'other@ourworks.example',
                 'OTHER_IMAP_PASSWORD': 'p', 'OTHER_SMTP_HOST': 'smtp', 'EMAIL_SEND_FROM': 'other'}.items():
        mailbox.setenv(k, v)
    assert mailsend.sender_config()['address'] == 'other@ourworks.example'


class FakeGmail:
    """Like smtp.gmail.com: AUTH is only offered after EHLO, and nothing is sent without logging in."""

    def __init__(self, host, port, timeout=None):
        self.features, self.logged_in, self.sent = {}, None, []
        FakeGmail.last = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        self.features = {'auth': 'LOGIN PLAIN XOAUTH2'}

    def has_extn(self, name):
        return name.lower() in self.features

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, message, to_addrs=None):
        import smtplib
        if not self.logged_in:
            raise smtplib.SMTPSenderRefused(530, b'5.7.0 Authentication Required. For more information...', message['From'])
        self.sent.append(to_addrs)


def test_it_logs_in_to_gmail_before_sending(monkeypatch):
    monkeypatch.setattr(mailsend.smtplib, 'SMTP_SSL', FakeGmail)
    cfg = {'smtp_host': 'smtp.gmail.com', 'smtp_port': 465, 'smtp_ssl': True, 'smtp_starttls': False,
           'smtp_user': 'collector@gmail.com', 'smtp_password': 'app-password'}
    message = mailsend.build_message('Our Works', 'desk@ourworks.example', ['ravi@gearco.example'], [], 'Hello', 'Hi.')
    mailsend.send(cfg, message, ['ravi@gearco.example'])
    assert FakeGmail.last.logged_in == ('collector@gmail.com', 'app-password')
    assert FakeGmail.last.sent == [['ravi@gearco.example']]

    # and when the server still refuses, the person sending sees what it said
    with pytest.raises(mailsend.SendError) as refused:
        mailsend.send({**cfg, 'smtp_password': None}, message, ['ravi@gearco.example'])
    assert str(refused.value) == ('The mail server refused to send from Our Works <desk@ourworks.example> '
                                  '(530 5.7.0 Authentication Required. For more information...). Nothing was sent.')


def test_a_reply_stays_in_its_thread_and_carries_the_pdfs():
    m = mailsend.build_message('Our Works', 'desk@ourworks.example', ['ravi@gearco.example'], ['accounts@gearco.example'],
                               'Re: PO for hob arbors', 'Dear Ravi,\n\nAttached.', [('Quote_Q-041.pdf', b'%PDF-1.4 x')],
                               reply_to={'message_id': '<po.1@gearco.example>', 'references': '<rfq.1@gearco.example>'})
    assert m['From'] == 'Our Works <desk@ourworks.example>' and m['To'] == 'ravi@gearco.example'
    assert m['Cc'] == 'accounts@gearco.example' and m['Message-ID'].endswith('@ourworks.example>')
    assert m['In-Reply-To'] == '<po.1@gearco.example>'
    assert m['References'] == '<rfq.1@gearco.example> <po.1@gearco.example>'
    [pdf] = list(m.iter_attachments())
    assert pdf.get_filename() == 'Quote_Q-041.pdf' and pdf.get_content() == b'%PDF-1.4 x'


def test_who_it_goes_to():
    people = [{'name': 'Ravi', 'email': 'ravi@gearco.example', 'project_gets': 'all'},
              {'name': 'Divya', 'email': 'accounts@gearco.example', 'project_gets': 'billing'},
              {'name': 'Sundar', 'email': 'plant@gearco.example', 'project_gets': 'none'}]
    assert mailsend.default_recipients(people, ['quote']) == (['ravi@gearco.example'], [])
    assert mailsend.default_recipients(people, ['invoice']) == (['ravi@gearco.example'], ['accounts@gearco.example'])
    assert mailsend.default_recipients(people[1:], ['proforma']) == (['accounts@gearco.example'], [])
    assert mailsend.greeting(people, ['ravi@gearco.example']) == 'Dear Ravi,'
    assert mailsend.greeting(people, ['new@gearco.example']) == 'Dear Sir/Madam,'


def test_addresses_are_checked():
    assert mailsend.clean_addresses([' Ravi@GearCo.example', 'ravi@gearco.example', '']) == ['ravi@gearco.example']
    with pytest.raises(mailsend.SendError, match='"ravi at gearco" isn\'t an email address'):
        mailsend.clean_addresses(['ravi at gearco'])


@pytest.fixture
def signed_in(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    return client


def test_viewers_cannot_send(signed_in, fake_db):
    fake_db.members['U-A'][0]['role'] = 'viewer'
    assert signed_in.get('/api/projects/P-1/compose').status_code == 403
    response = signed_in.post('/api/projects/P-1/emails', json={'to': ['ravi@gearco.example']})
    assert response.status_code == 403 and "doesn't allow that (email documents" in response.get_json()['error']


def test_sending_takes_json_only(signed_in):
    response = signed_in.post('/api/projects/P-1/emails', data={'to': 'ravi@gearco.example'})
    assert response.status_code == 415 and response.get_json() == {'error': 'Send the request as JSON'}


def test_an_unknown_project_is_not_found(signed_in):
    assert signed_in.get('/api/projects/P-404/compose').status_code == 404
