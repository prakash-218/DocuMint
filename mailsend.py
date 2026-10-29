"""
Sending email from DocuMint, through one of the synced mailboxes (emailsync), so it goes out from the
company's address, a copy lands in that mailbox's Sent folder, and replies come back into the same thread.

Railway variables, on the web service (the mailbox's IMAP ones are needed there too, for the Sent copy):
    EMAIL_SEND_FROM=INFO                    which mailbox sends; default: the first in EMAIL_ACCOUNTS
    INFO_SMTP_HOST=mail.example.com         sending is off until this is set
    INFO_SMTP_PORT=465  INFO_SMTP_SSL=1     the default; for port 587 set INFO_SMTP_SSL=0 (it then
                                            needs STARTTLS, unless INFO_SMTP_STARTTLS=0)
    INFO_SMTP_USER, INFO_SMTP_PASSWORD      default: the mailbox's IMAP login
    INFO_SMTP_FROM=info@company.com         send as this address (default: the mailbox's own)
    INFO_SENT_FOLDER=Sent                   where the copy goes when the server doesn't mark one \\Sent
    INFO_SAVE_SENT=0                        no copy: for servers that keep one themselves (the default
                                            for Gmail)

Through a Gmail that collects the company mail (emailsync's GMAIL example): GMAIL_SMTP_HOST=smtp.gmail.com
with the same app password, and GMAIL_SMTP_FROM=info@company.com when Gmail has that address under
"Send mail as" (otherwise Gmail sends it from the Gmail address). Gmail puts it in its Sent itself.
"""

import imaplib
import logging
import os
import re
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Dict, List, Optional, Tuple

import emailsync
from db import db, DatabaseError

logger = logging.getLogger(__name__)

EMAIL = re.compile(r'^[^@\s,;<>"]+@[^@\s,;<>"]+\.[^@\s,;<>"]+$')
MAX_RECIPIENTS = 20


class SendError(Exception):
    """What went wrong, in words for the person sending. status: 400 for what they can fix, 502 for the server."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- Configuration

def sender_config() -> Optional[Dict]:
    """The mailbox that sends, with its SMTP settings; None while sending isn't set up."""
    accounts = emailsync.accounts_from_env()
    wanted = (os.getenv('EMAIL_SEND_FROM') or '').strip().upper()
    cfg = next((a for a in accounts if a['prefix'] == wanted), None) if wanted else (accounts[0] if accounts else None)
    if not cfg:
        return None
    env = lambda k, d=None: os.getenv(f"{cfg['prefix']}_{k}", d)  # noqa: E731
    if not env('SMTP_HOST'):
        return None
    ssl = env('SMTP_SSL', '1') not in ('0', 'false', 'no')
    gmail = env('SMTP_HOST').lower().rstrip('.').endswith(('gmail.com', 'googlemail.com'))
    return {**cfg,
            'smtp_host': env('SMTP_HOST'), 'smtp_port': int(env('SMTP_PORT', '465' if ssl else '587')), 'smtp_ssl': ssl,
            'smtp_starttls': not ssl and env('SMTP_STARTTLS', '1') not in ('0', 'false', 'no'),
            'smtp_user': env('SMTP_USER', cfg['user']), 'smtp_password': env('SMTP_PASSWORD', cfg['password']),
            'from_address': (env('SMTP_FROM') or cfg['address']).strip().lower(),
            'save_sent': env('SAVE_SENT', '0' if gmail else '1') not in ('0', 'false', 'no'), 'sent_folder': env('SENT_FOLDER')}


def sender_for(org_id) -> Optional[Dict]:
    """The sending mailbox, when it's this organization's: the one the address it sends as belongs to (or, for
    a Gmail sending as itself, the domain the sync files its mail under)."""
    from contacts import FREE_MAIL
    cfg = sender_config()
    if not cfg:
        return None
    domain = cfg['from_address'].split('@')[-1]
    try:
        orgs = db.execute_proc('sp_find_organizations_by_domain', (cfg['org_domain'] if domain in FREE_MAIL else domain,)) or []
    except DatabaseError:
        return None
    return cfg if orgs and str(orgs[-1]['org_id']) == str(org_id) else None


# ---------------------------------------------------------------- The message (pure)

def clean_addresses(values) -> List[str]:
    """Lower-cased, de-duplicated addresses; raises SendError on one that isn't an address."""
    out = []
    for value in values or []:
        address = str(value).strip().lower()
        if not address:
            continue
        if not EMAIL.match(address):
            raise SendError(f'"{value}" isn\'t an email address.')
        if address not in out:
            out.append(address)
    return out


def build_message(sender_name: str, sender: str, to: List[str], cc: List[str], subject: str, body: str,
                  attachments: List[Tuple[str, bytes]] = (), reply_to: Optional[Dict] = None) -> EmailMessage:
    """reply_to: {'message_id': ..., 'references': ...} of the message this answers, to stay in its thread."""
    m = EmailMessage()
    m['From'] = formataddr((sender_name, sender))
    m['To'] = ', '.join(to)
    if cc:
        m['Cc'] = ', '.join(cc)
    m['Subject'] = subject
    m['Date'] = formatdate(localtime=True)
    m['Message-ID'] = make_msgid(domain=sender.split('@')[-1])
    if reply_to and reply_to.get('message_id'):
        m['In-Reply-To'] = reply_to['message_id']
        m['References'] = ' '.join([*(reply_to.get('references') or '').split(), reply_to['message_id']][-20:])
    m.set_content(body)
    for name, data in attachments:
        m.add_attachment(data, maintype='application', subtype='pdf', filename=name)
    return m


def reply_subject(subject: str) -> str:
    return subject if re.match(r'^\s*re\s*:', subject or '', re.I) else f'Re: {subject}'


# ---------------------------------------------------------------- Sending

def _said(e: smtplib.SMTPResponseException) -> str:
    """The server's reply, first line, e.g. '530 5.7.0 Authentication Required.'"""
    text = e.smtp_error.decode(errors='replace') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
    return f'{e.smtp_code} {text.splitlines()[0] if text else ""}'.strip()


def send(cfg: Dict, message: EmailMessage, recipients: List[str]) -> None:
    try:
        if cfg['smtp_ssl']:
            server = smtplib.SMTP_SSL(cfg['smtp_host'], cfg['smtp_port'], timeout=30)
        else:
            server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=30)
        with server:
            server.ehlo()                       # what the server offers (STARTTLS, AUTH) is only known after EHLO
            if cfg['smtp_starttls']:
                server.starttls()
                server.ehlo()
            if cfg['smtp_user'] and cfg['smtp_password'] and server.has_extn('auth'):
                server.login(cfg['smtp_user'], cfg['smtp_password'])
            server.send_message(message, to_addrs=recipients)
    except smtplib.SMTPRecipientsRefused as e:
        raise SendError('The mail server refused ' + ', '.join(e.recipients) + '. Nothing was sent.', 502) from e
    except smtplib.SMTPAuthenticationError as e:
        raise SendError(f"The mail server didn't accept the mailbox's login ({_said(e)}). Check its password.", 502) from e
    except smtplib.SMTPSenderRefused as e:
        logger.error('%s refused to send from %s: %s', cfg['smtp_host'], e.sender, _said(e))
        raise SendError(f'The mail server refused to send from {e.sender} ({_said(e)}). Nothing was sent.', 502) from e
    except smtplib.SMTPResponseException as e:
        logger.error('Sending through %s failed: %s', cfg['smtp_host'], _said(e))
        raise SendError(f'The mail server said: {_said(e)}. Nothing was sent.', 502) from e
    except (smtplib.SMTPException, OSError) as e:
        logger.exception('Sending through %s failed', cfg['smtp_host'])
        raise SendError(f"Couldn't reach the mail server ({type(e).__name__}). Nothing was sent.", 502) from e


def save_to_sent(cfg: Dict, message: EmailMessage) -> Optional[str]:
    """Put a copy in the mailbox's Sent folder, so it shows in the mail app too. Returns the folder, or None."""
    if not cfg.get('save_sent'):
        return None
    try:
        box = emailsync._connect(cfg)
        try:
            folder = cfg.get('sent_folder') or _sent_folder(box) or 'Sent'
            if not cfg.get('sent_folder') and folder == 'Sent':
                box.create(emailsync._quote(folder))             # fails harmlessly when it's there
            status, _ = box.append(emailsync._quote(folder), '(\\Seen)', imaplib.Time2Internaldate(time.time()),
                                   message.as_bytes())
            return folder if status == 'OK' else None
        finally:
            try:
                box.logout()
            except Exception:
                pass
    except (imaplib.IMAP4.error, OSError):
        logger.exception('Could not save a copy of a sent email in %s', cfg['address'])
        return None


def _sent_folder(box) -> Optional[str]:
    _, data = box.list()
    for line in data or []:
        text = line.decode(errors='replace') if isinstance(line, bytes) else str(line)
        if '\\Sent' in text:
            return emailsync.folder_name(text)
    return None


def record(org_id, cfg: Dict, message: EmailMessage, thread_id: Optional[str], project_id, customer_id) -> str:
    """Store what was sent in its thread (a new one for the project when it isn't a reply). The sync will
    see the same Message-ID in the Sent folder and leave it be."""
    m = emailsync.parse_message(message.as_bytes(), org_domains={cfg['org_domain']})
    m['direction'] = 'out'
    account = db.execute_proc_single('sp_upsert_email_account', (org_id, cfg['address'], cfg['prefix']))
    if not thread_id:
        thread_id = db.execute_proc_single('sp_create_email_thread', (
            org_id, emailsync.normalize_subject(m['subject']), project_id, customer_id, 'sent'))['thread_id']
    db.execute_proc('sp_add_email_message', (org_id, account['account_id'], thread_id, m), fetch=False)
    return thread_id


# ---------------------------------------------------------------- From a project

BILLING_TYPES = ('proforma', 'invoice', 'export_invoice')
NOT_SET_UP = ("Sending email isn't set up yet. An owner adds the mailbox's SMTP settings in Railway "
              "(see mailsend.py); then Send works.")


def default_recipients(people: List[Dict], doc_types: List[str]) -> Tuple[List[str], List[str]]:
    """To: whoever gets everything on the project. Cc: whoever gets proformas and invoices, when one is attached."""
    billing = any(t in BILLING_TYPES for t in doc_types)
    to = [p['email'] for p in people if p.get('email') and p.get('project_gets') == 'all']
    cc = [p['email'] for p in people if p.get('email') and p.get('project_gets') == 'billing' and billing]
    if not to and cc:
        to, cc = cc[:1], cc[1:]
    return to, cc


def greeting(people: List[Dict], to: List[str]) -> str:
    first = next((p for p in people if to and p.get('email') == to[0]), None)
    return f"Dear {first['name']}," if first and first.get('name') else 'Dear Sir/Madam,'


def first_message(people: List[Dict], to: List[str], document: Optional[Dict], project_title: str, org_name: str) -> str:
    lines = [greeting(people, to), '']
    if document:
        lines += [f"Please find attached our {document['kind'].lower()} {document['number']} for {project_title}.", '']
    return '\n'.join(lines + ['Regards,', org_name])


def _documents(org_id, project, sales: bool) -> List[Dict]:
    """The project's latest documents, and why one can't go out yet (a draft; Sales: anything but quotations)."""
    import projects
    import revisions
    from documents import display_number, get_type
    out = []
    for d in revisions.collapse(projects.project_documents(project['project_id'], org_id)):
        kind = get_type(d.get('doc_type'))
        why_not = ('Finalize it first' if (d.get('status') or 'draft') == 'draft' else
                   'Sales send quotations only' if sales and kind.key != 'quote' else None)
        out.append({'invoice_id': d['invoice_id'], 'doc_type': kind.key, 'kind': kind.label, 'number': display_number(d),
                    'label': f'{kind.label} {display_number(d)}', 'status': d.get('status'), 'why_not': why_not})
    return out


def compose_context(org_id, org_name: str, project: Dict, role: str, invoice_id=None, thread_id=None) -> Dict:
    """What the email form starts with, for a project: one of its documents attached, or a reply in one of its threads."""
    import contacts
    import projects
    from auth import MAIL_READERS, SALES
    reads_mail = role in MAIL_READERS
    people = [p for p in contacts.for_project(org_id, project['project_id']) if p.get('email')]
    documents = _documents(org_id, project, role == SALES)
    chosen = [d for d in documents if d['invoice_id'] == invoice_id and not d['why_not']]
    to, cc = default_recipients(people, [d['doc_type'] for d in chosen])
    threads = []
    if reads_mail:
        threads = [{'thread_id': t['thread_id'], 'subject': t['subject'], 'last_message_at': t.get('last_message_at')}
                   for t in db.execute_proc('sp_list_email_threads', (org_id, project['project_id'], None, False, 20)) or []]
    thread = next((t for t in threads if t['thread_id'] == thread_id), None)
    if not thread and chosen:            # a thread that's already about this document (any revision of it)
        base = re.sub(r'R\d+(?=/|$)', '', chosen[0]['number'])
        thread = next((t for t in threads if base and base in (t['subject'] or '')), None)
    new_subject = (f"{chosen[0]['label']} · " if chosen else '') + f"{project['title']} ({projects.project_label(project)})"
    subject = reply_subject(thread['subject']) if thread else new_subject
    found = [{'name': p['name'], 'email': p['email']}
             for p in contacts.project_suggestions(org_id, project, people)['people']] if reads_mail else []
    cfg = sender_for(org_id)
    return {'from': cfg['from_address'] if cfg else None, 'from_name': org_name, 'can_send': bool(cfg),
            'why_not': None if cfg else NOT_SET_UP,
            'people': [{'name': p['name'], 'email': p['email'], 'role': p.get('role'), 'gets': p.get('project_gets')}
                       for p in people],
            'found': found, 'to': to, 'cc': cc, 'threads': threads, 'thread_id': thread['thread_id'] if thread else None,
            'subject': subject, 'new_subject': new_subject, 'body': first_message(people, to, chosen[0] if chosen else None, project['title'], org_name),
            'documents': documents, 'attach': [d['invoice_id'] for d in chosen]}


def _pdf(org_id, invoice_id) -> Tuple[str, bytes]:
    """One copy of the document's PDF (an invoice's Original), as printing it would give."""
    from access import get_org_invoice
    from invoice_service import render_invoice_pdf
    header, values = get_org_invoice(invoice_id, org_id)
    response = render_invoice_pdf(header, values, copies=1)
    name = re.search(r'filename="([^"]+)"', response.headers.get('Content-Disposition', ''))
    return (name.group(1) if name else 'document.pdf'), response.get_data()


def send_for_project(org_id, org_name: str, project: Dict, role: str, data: Dict) -> Dict:
    """Send what the email form posted. Raises SendError with what to fix (or what went wrong on the server)."""
    import activity
    import contacts
    from auth import MAIL_READERS, SALES
    from flask import url_for
    cfg = sender_for(org_id)
    if not cfg:
        raise SendError(NOT_SET_UP)
    to = clean_addresses(data.get('to'))
    cc = [a for a in clean_addresses(data.get('cc')) if a not in to]
    subject = (data.get('subject') or '').strip()[:300]
    body = (data.get('body') or '').strip()[:50_000]
    if not to:
        raise SendError('Add at least one person in To.')
    if len(to) + len(cc) > MAX_RECIPIENTS:
        raise SendError(f"That's more than {MAX_RECIPIENTS} people. Send it in parts.")
    if not subject:
        raise SendError('Give the email a subject.')
    if not body:
        raise SendError('Write a message.')

    reply_to = None
    if data.get('thread_id'):
        if role not in MAIL_READERS:
            raise SendError("Your role can start new emails but not reply in the mailbox's threads.")
        reply_to = db.execute_proc_single('sp_get_thread_reply_headers', (data['thread_id'], org_id, project['project_id']))
        if not reply_to:
            raise SendError("That thread isn't on this project.")

    documents = {d['invoice_id']: d for d in _documents(org_id, project, role == SALES)}
    attach = []
    for invoice_id in dict.fromkeys(data.get('invoice_ids') or []):
        d = documents.get(invoice_id)
        if not d:
            raise SendError("One of the documents isn't on this project.")
        if d['why_not']:
            raise SendError(f"{d['label']}: {d['why_not'].lower()}.")
        attach.append(d)
    try:
        files = [_pdf(org_id, d['invoice_id']) for d in attach]
    except Exception as e:
        logger.exception('Could not make the PDFs for an email')
        raise SendError("Couldn't make the PDF to attach. Nothing was sent.", 502) from e

    message = build_message(org_name, cfg['from_address'], to, cc, subject, body, files, reply_to)
    send(cfg, message, to + cc)

    thread_id = (reply_to or {}).get('thread_id')
    try:
        thread_id = record(org_id, cfg, message, thread_id, project['project_id'], project['customer_id'])
    except DatabaseError:
        logger.exception('Sent, but could not store the email %s', message['Message-ID'])
    saved_to = save_to_sent(cfg, message)
    names = {p['email']: p['name'] for p in contacts.for_project(org_id, project['project_id']) if p.get('email')}
    what = ', '.join(d['label'] for d in attach) or f'"{subject}"'
    activity.record('email_sent', f"Emailed {what} to {', '.join(names.get(a, a) for a in to)}",
                    project_id=project['project_id'], notify=False,
                    link=url_for('emails_bp.thread', thread_id=thread_id) if thread_id else None)
    return {'thread_id': thread_id, 'to': to, 'cc': cc, 'attached': [d['label'] for d in attach], 'saved_to': saved_to}
