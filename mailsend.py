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


def _documents(org_id, project, perms) -> List[Dict]:
    """The project's latest documents, and why one can't go out yet: a draft, or a kind their role doesn't read (Sales
    send quotations only)."""
    import permissions
    import projects
    import revisions
    from documents import display_number, get_type
    out = []
    for d in revisions.collapse(projects.project_documents(project['project_id'], org_id)):
        kind = get_type(d.get('doc_type'))
        why_not = ('Finalize it first' if (d.get('status') or 'draft') == 'draft' else
                   "Your role doesn't send this kind of document" if not permissions.can_doc('read', kind.key, perms) else None)
        out.append({'invoice_id': d['invoice_id'], 'doc_type': kind.key, 'kind': kind.label, 'number': display_number(d),
                    'label': f'{kind.label} {display_number(d)}', 'status': d.get('status'), 'why_not': why_not})
    return out


def compose_context(org_id, org_name: str, project: Dict, perms, invoice_id=None, thread_id=None) -> Dict:
    """What the email form starts with, for a project: one of its documents attached, or a reply in one of its threads."""
    import contacts
    import permissions
    import projects
    reads_mail = permissions.can('emails.read', perms=perms)
    documents = _documents(org_id, project, perms)
    chosen = [d for d in documents if d['invoice_id'] == invoice_id and not d['why_not']]
    if chosen and chosen[0]['doc_type'] == 'purchase_order':      # to the supplier's people; you pick whom
        from access import get_org_invoice
        supplier = (get_org_invoice(invoice_id, org_id)[0] or {}).get('customer_id')
        people = [{**p, 'project_gets': p.get('gets')} for p in contacts.for_supplier(org_id, supplier) if p.get('email')]
    else:
        people = [p for p in contacts.for_project(org_id, project['project_id']) if p.get('email')]
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


def _checked(org_id, data: Dict) -> Tuple[Dict, List[str], List[str], str, str]:
    """(sender config, to, cc, subject, body) from what the email form posted, or SendError with what to fix."""
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
    return cfg, to, cc, subject, body


def send_for_project(org_id, org_name: str, project: Dict, perms, data: Dict) -> Dict:
    """Send what the email form posted. Raises SendError with what to fix (or what went wrong on the server)."""
    import activity
    import contacts
    import permissions
    from flask import url_for
    cfg, to, cc, subject, body = _checked(org_id, data)

    reply_to = None
    if data.get('thread_id'):
        if not permissions.can('emails.read', perms=perms):
            raise SendError("Your role can start new emails but not reply in the mailbox's threads.")
        reply_to = db.execute_proc_single('sp_get_thread_reply_headers', (data['thread_id'], org_id, project['project_id']))
        if not reply_to:
            raise SendError("That thread isn't on this project.")

    documents = {d['invoice_id']: d for d in _documents(org_id, project, perms)}
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


# ---------------------------------------------------------------- A customer's statement

STATEMENT = 'statement'          # what the email form calls the statement among the attachments


def statement_message(people: List[Dict], to: List[str], data: Dict, org_name: str) -> str:
    """The email that goes with a statement: what it covers, the balance, and what's past its due date."""
    from money import format_money
    account = data.get('account')
    lines = [greeting(people, to), '']
    if not account:
        return '\n'.join(lines + ['Regards,', org_name])
    cur = account['currency']
    money = lambda v: format_money(v, cur, decimals=False)  # noqa: E731
    period = f"FY {account['fy']}" if account['fy'] else 'every year to date'
    balance = (f"The balance due is {money(account['closing'])}." if account['closing'] > 0.005 else
               f"You have paid {money(-account['closing'])} ahead." if account['closing'] < -0.005 else 'Nothing is due.')
    on = lambda d, year=True: f"{d.day} {d:%b %Y}" if year else f"{d.day} {d:%b}"  # noqa: E731
    lines += [f"Please find attached our statement of account for {period}, as of {on(data['today'])}. {balance}", '']
    late = [x for x in data.get('unpaid') or [] if x['late'] > 0]
    if late:
        lines.append(f"Of this, {money(data['overdue'])} is past its due date:")
        lines += [f"- {x['text']} of {on(x['date'])}: {money(x['balance'])}, due {on(x['due'], False)} "
                  f"({x['late']} day{'' if x['late'] == 1 else 's'} late)" for x in late]
        lines.append('')
    lines += ['Please let us know if anything differs from your records.', '', 'Regards,', org_name]
    return '\n'.join(lines)


def statement_compose(org_id, org_name: str, customer: Dict, fy: Optional[str] = None, currency: Optional[str] = None) -> Dict:
    """What the email form starts with for a customer's statement: their billing contacts, and the PDF attached."""
    import contacts
    import statement
    from flask import url_for
    data = statement.gather(org_id, customer, url_for, fy, currency)
    people = [p for p in contacts.for_customer(org_id, customer) if p.get('email')]
    billing = [p['email'] for p in people if p.get('gets') == 'billing'] or [p['email'] for p in people if p.get('gets') == 'all']
    subject = f"{statement.title(data)} · {customer['name']}"
    cfg = sender_for(org_id)
    return {'from': cfg['from_address'] if cfg else None, 'from_name': org_name, 'can_send': bool(cfg),
            'why_not': None if cfg else NOT_SET_UP,
            'people': [{'name': p['name'], 'email': p['email'], 'role': p.get('role'), 'gets': p.get('gets')} for p in people],
            'found': [], 'to': billing[:1], 'cc': billing[1:], 'threads': [], 'thread_id': None,
            'subject': subject, 'new_subject': subject, 'body': statement_message(people, billing[:1], data, org_name),
            'documents': [{'invoice_id': STATEMENT, 'doc_type': STATEMENT, 'label': f'{statement.title(data)} (PDF)',
                           'why_not': None if data['account'] else 'No invoices or payments yet'}],
            'attach': [STATEMENT] if data['account'] else [],
            'fy': (data['account'] or {}).get('fy') or 'all', 'currency': (data['account'] or {}).get('currency')}


def send_statement(org_id, org_name: str, customer: Dict, data: Dict) -> Dict:
    """Send the statement email the form posted (its fy and currency say which statement). Raises SendError."""
    import activity
    import contacts
    import statement
    from flask import url_for
    cfg, to, cc, subject, body = _checked(org_id, data)
    files = []
    if STATEMENT in (data.get('invoice_ids') or []):
        made = statement.gather(org_id, customer, url_for, data.get('fy'), data.get('currency'))
        if not made['account']:
            raise SendError('There is nothing on the statement yet.')
        try:
            files = [(statement.filename(made), statement.render_pdf(made))]
        except Exception as e:
            logger.exception('Could not make the statement to attach')
            raise SendError("Couldn't make the statement PDF to attach. Nothing was sent.", 502) from e
    message = build_message(org_name, cfg['from_address'], to, cc, subject, body, files)
    send(cfg, message, to + cc)
    thread_id = None
    try:
        thread_id = record(org_id, cfg, message, None, None, str(customer['customer_id']))
    except DatabaseError:
        logger.exception('Sent, but could not store the email %s', message['Message-ID'])
    saved_to = save_to_sent(cfg, message)
    names = {p['email']: p['name'] for p in contacts.for_customer(org_id, customer) if p.get('email')}
    what = f"the statement ({made['account']['fy'] and 'FY ' + made['account']['fy'] or 'to date'})" if files else f'"{subject}"'
    activity.record('email_sent', f"Emailed {what} to {', '.join(names.get(a, a) for a in to)}", body=customer.get('name'),
                    notify=False, link=url_for('emails_bp.thread', thread_id=thread_id) if thread_id else None)
    return {'thread_id': thread_id, 'to': to, 'cc': cc, 'attached': [name for name, _ in files], 'saved_to': saved_to}
