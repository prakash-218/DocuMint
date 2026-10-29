from email.message import EmailMessage

from emailsync import (external_addresses, folder_name, html_to_text, involves, normalize_subject,
                       parse_message, project_number_in)


def _raw(**kw):
    m = EmailMessage()
    m['From'] = kw.get('sender', 'Ravi Kumar <ravi@acme-tools.com>')
    m['To'] = kw.get('to', 'info@techflow.com')
    if kw.get('cc'):
        m['Cc'] = kw['cc']
    m['Subject'] = kw.get('subject', 'RFQ for fixtures')
    m['Date'] = 'Tue, 20 Oct 2026 10:15:00 +0530'
    m['Message-ID'] = kw.get('message_id', '<abc123@acme-tools.com>')
    if kw.get('in_reply_to'):
        m['In-Reply-To'] = kw['in_reply_to']
        m['References'] = kw['in_reply_to']
    if kw.get('html'):
        m.set_content('<p>Dear Sir,<br>Please quote.</p><script>alert(1)</script>', subtype='html')
    else:
        m.set_content(kw.get('body', 'Please quote for 2 sets.'))
    for name, data, ctype in kw.get('files', []):
        maintype, subtype = ctype.split('/')
        m.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    return m.as_bytes()


def test_subjects_and_project_numbers():
    assert normalize_subject('RE: Fwd: [EXT] Re:  Quote  for jig') == 'Quote for jig'
    assert normalize_subject('') == '(no subject)'
    assert project_number_in('Drawings for PRJ-012 rev B') == 12
    assert project_number_in('prj 7 update') == 7
    assert project_number_in('Project 12') is None


def test_parse_message_with_attachment():
    raw = _raw(files=[('PO 4500.pdf', b'%PDF-1.4 po', 'application/pdf')], cc='Buyer <buyer@acme-tools.com>')
    m = parse_message(raw, uid=7, org_domains={'techflow.com'})
    assert m['message_id'] == '<abc123@acme-tools.com>' and m['uid'] == 7
    assert m['from_address'] == 'ravi@acme-tools.com' and m['from_name'] == 'Ravi Kumar'
    assert m['to'] == ['info@techflow.com'] and m['cc'] == ['buyer@acme-tools.com']
    assert m['direction'] == 'in' and 'Please quote' in m['body_text']
    assert m['sent_at'].isoformat() == '2026-10-20T10:15:00+05:30'
    assert [(f['name'], f['type'], f['data']) for f in m['files']] == [('PO 4500.pdf', 'application/pdf', b'%PDF-1.4 po')]
    assert external_addresses(m, {'techflow.com'}) == ['ravi@acme-tools.com']


def test_html_only_mail_becomes_text_and_outgoing_is_detected():
    m = parse_message(_raw(html=True, sender='Mohan <mohan@techflow.com>', to='ravi@acme-tools.com'),
                      org_domains={'techflow.com'})
    assert m['body_text'] == 'Dear Sir,\nPlease quote.'
    assert m['direction'] == 'out' and external_addresses(m, {'techflow.com'}) == ['ravi@acme-tools.com']
    assert html_to_text('a &amp; b<style>x{}</style>') == 'a & b'


def test_message_without_id_gets_a_stable_one():
    raw = _raw(message_id='')
    assert parse_message(raw)['message_id'] == parse_message(raw)['message_id'].strip()
    assert parse_message(raw)['message_id'].startswith('<sync-')


def test_address_matching_and_folder_names():
    headers = b'From: Mom <mom@family.example>\r\nTo: me@gmail.com,\r\n  Sales <Sales@TechFlow.com>\r\n'
    assert involves(headers, ['techflow.com'])
    assert involves(headers, ['sales@techflow.com']) and not involves(headers, ['info@techflow.com'])
    assert involves(b'Cc: a@mail.techflow.com\r\n', ['techflow.com'])          # subdomain
    assert not involves(b'From: x@nottechflow.com\r\n', ['techflow.com'])
    assert not involves(headers, []) and not involves(b'', ['techflow.com'])
    assert folder_name(r'(\HasNoChildren \Sent) "/" "[Gmail]/Sent Mail"') == '[Gmail]/Sent Mail'
    assert folder_name(r'(\HasNoChildren \Sent) "." INBOX.Sent') == 'INBOX.Sent'
    assert folder_name(r'(\Sent) "/" "Say \"hi\""') == 'Say "hi"'
    assert folder_name('garbage') is None
