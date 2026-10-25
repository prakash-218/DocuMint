"""
Email sync: copy mail from IMAP mailboxes (info@, ramesh@ ...) into threads, and attach
threads to projects.

Configuration (Railway variables on the worker; passwords never go in the code):
    EMAIL_ACCOUNTS=INFO,RAMESH              one prefix per mailbox
    INFO_IMAP_HOST=mail.kkrengineering.com  INFO_IMAP_PORT=993  INFO_IMAP_SSL=1
    INFO_IMAP_USER=info@kkrengineering.com  INFO_IMAP_PASSWORD=...
    INFO_IMAP_FOLDERS=INBOX,INBOX.Sent      optional; default INBOX plus the folder marked \\Sent
    INFO_IMAP_MATCH=kkrengineering.com      optional; only mail from/to/cc these addresses or domains
    EMAIL_ORG_DOMAIN=kkrengineering.com     optional; default: the mailbox's own domain
    EMAIL_SYNC_DAYS=90                      how far back the first sync goes

A personal Gmail that collects the company mail (POP "check mail from other accounts"):
    EMAIL_ACCOUNTS=GMAIL  GMAIL_IMAP_HOST=imap.gmail.com  GMAIL_IMAP_USER=you@gmail.com
    GMAIL_IMAP_PASSWORD=<app password>  GMAIL_IMAP_FOLDERS=[Gmail]/All Mail
    GMAIL_IMAP_MATCH=kkrengineering.com     so personal mail stays out

Mail is read with BODY.PEEK, so nothing is marked as read on the server, and each
folder remembers the last message (UID) it copied.

Linking a thread to a project, in order: a project number in the subject ("PRJ-012"),
a document number in the subject ("KKR/Q/027/26-27"), a reply in a thread that's
already linked. The sender's domain (customer "email domains", portal logins) picks
the customer. Anything else waits in the inbox to be linked by hand.
"""

import email
import hashlib
import html
import imaplib
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from email import policy
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from typing import Dict, List, Optional

from db import db, DatabaseError

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_BODY_CHARS = 100_000
PROJECT_REF = re.compile(r'\bPRJ[-\s]?0*(\d{1,6})\b', re.I)
SUBJECT_PREFIX = re.compile(r'^\s*((re|fw|fwd|aw|wg|sv|antw)(\[\d+\])?\s*:\s*|\[[^\]]{1,30}\]\s*)+', re.I)


# ---------------------------------------------------------------- Configuration

def accounts_from_env() -> List[Dict]:
    out = []
    for prefix in [p.strip().upper() for p in (os.getenv('EMAIL_ACCOUNTS') or '').split(',') if p.strip()]:
        env = lambda k, d=None: os.getenv(f'{prefix}_IMAP_{k}', d)  # noqa: E731
        user = env('USER')
        if not (env('HOST') and user and env('PASSWORD')):
            logger.warning('Email account %s is missing HOST, USER or PASSWORD; skipped', prefix)
            continue
        ssl = env('SSL', '1') not in ('0', 'false', 'no')
        out.append({
            'prefix': prefix, 'address': env('ADDRESS', user).lower(), 'host': env('HOST'),
            'port': int(env('PORT', '993' if ssl else '143')), 'ssl': ssl, 'user': user,
            'password': env('PASSWORD'),
            'folders': [f.strip() for f in (env('FOLDERS') or '').split(',') if f.strip()],
            'match': [m.strip().strip('"') for m in (env('MATCH') or '').split(',') if m.strip().strip('"')],
            'org_domain': (os.getenv('EMAIL_ORG_DOMAIN') or user.split('@')[-1]).lower(),
        })
    return out


# ---------------------------------------------------------------- Parsing (pure)

def normalize_subject(subject: str) -> str:
    s = SUBJECT_PREFIX.sub('', subject or '')
    return re.sub(r'\s+', ' ', s).strip()[:500] or '(no subject)'


def html_to_text(markup: str) -> str:
    markup = re.sub(r'(?is)<(script|style|head)\b.*?</\1>', '', markup)
    markup = re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>', '\n', markup)
    text = html.unescape(re.sub(r'<[^>]+>', '', markup))
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t\r\f\v]+', ' ', text)).strip()


def _addresses(values) -> List[str]:
    return [a.lower() for _, a in getaddresses([str(v) for v in values if v]) if a and '@' in a]


def parse_message(raw: bytes, uid: Optional[int] = None, org_domains=()) -> Dict:
    msg = email.message_from_bytes(raw, policy=policy.default)
    name, sender = parseaddr(str(msg.get('From', '')))
    sender = sender.lower()
    message_id = (str(msg.get('Message-ID') or '').strip() or
                  f'<sync-{hashlib.sha256(raw).hexdigest()[:32]}@documint>')
    refs = re.findall(r'<[^>]+>', str(msg.get('References') or ''))
    in_reply_to = (re.findall(r'<[^>]+>', str(msg.get('In-Reply-To') or '')) or [None])[0]
    try:
        sent_at = parsedate_to_datetime(str(msg.get('Date')))
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        sent_at = datetime.now(timezone.utc)

    body_plain, body_html, files = None, None, []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disposition = (part.get_content_disposition() or '').lower()
        filename = part.get_filename()
        if filename or disposition == 'attachment':
            data = part.get_payload(decode=True) or b''
            # signatures and logos pasted inline are noise; real attachments are kept
            if disposition == 'inline' and ctype.startswith('image/') and len(data) < 20_000:
                continue
            if data and len(data) <= MAX_FILE_BYTES:
                files.append({'name': (filename or 'attachment').replace('/', '_')[:200], 'type': ctype, 'data': data})
            continue
        if ctype == 'text/plain' and body_plain is None:
            body_plain = part.get_content()
        elif ctype == 'text/html' and body_html is None:
            body_html = part.get_content()
    body = body_plain if body_plain and body_plain.strip() else (html_to_text(body_html) if body_html else '')

    domain = sender.split('@')[-1] if '@' in sender else ''
    return {
        'uid': uid, 'message_id': message_id[:500], 'in_reply_to': in_reply_to, 'references': refs[-30:],
        'from_address': sender, 'from_name': (name or sender)[:200],
        'to': _addresses(msg.get_all('To', [])), 'cc': _addresses(msg.get_all('Cc', [])),
        'subject': str(msg.get('Subject') or '').strip(), 'sent_at': sent_at,
        'body_text': (body or '').strip()[:MAX_BODY_CHARS],
        'direction': 'out' if domain and domain in org_domains else 'in',
        'files': files,
    }


def external_addresses(m: Dict, org_domains) -> List[str]:
    """The other side of the conversation: the sender for mail we received, recipients for mail we sent."""
    pool = [m['from_address']] if m['direction'] == 'in' else m['to'] + m['cc']
    return [a for a in pool if a.split('@')[-1] not in org_domains]


def project_number_in(subject: str) -> Optional[int]:
    found = PROJECT_REF.search(subject or '')
    return int(found.group(1)) if found else None


# ---------------------------------------------------------------- Storing and linking

class Linker:
    """Finds the thread, customer and project for messages of one organization."""

    def __init__(self, org_id, org_domains):
        self.org_id = org_id
        self.org_domains = set(org_domains)
        self._numbers = None

    def _doc_numbers(self):
        if self._numbers is None:
            self._numbers = db.execute_proc('sp_list_document_numbers', (self.org_id,)) or []
        return self._numbers

    def project_from_subject(self, subject: str):
        number = project_number_in(subject)
        if number:
            row = db.execute_proc_single('sp_find_project_by_number', (self.org_id, number))
            if row:
                return row['project_id'], row['customer_id'], 'number'
        low = (subject or '').lower()
        for d in self._doc_numbers():
            if d['doc_number'].lower() in low:
                return d.get('project_id'), d.get('customer_id'), 'document'
        return None, None, None

    def customer_for(self, m: Dict):
        rows = db.execute_proc('sp_match_customers_by_email', (self.org_id, external_addresses(m, self.org_domains)))
        rows = rows or []
        return rows[0]['customer_id'] if len(rows) == 1 else None

    def store(self, account_id, m: Dict) -> Optional[Dict]:
        """Save one parsed message. Returns {'thread_id', 'project_id', 'customer_id', 'new_thread'} or None if known."""
        if db.execute_proc('sp_email_message_exists', (self.org_id, m['message_id'])):
            return None
        headers = [h for h in [m.get('in_reply_to')] + list(m.get('references') or []) if h]
        known = db.execute_proc('sp_find_threads_by_headers', (self.org_id, headers)) or []
        project_id, customer_id, linked_by = self.project_from_subject(m['subject'])
        thread = known[0] if known else None
        if not customer_id:
            customer_id = (thread or {}).get('customer_id') or self.customer_for(m)
        subject = normalize_subject(m['subject'])
        if not thread:
            since = (m['sent_at'] - timedelta(days=90)).isoformat()
            thread = db.execute_proc_single('sp_find_thread_by_subject', (self.org_id, subject, customer_id, since))
        new_thread = thread is None
        if new_thread:
            row = db.execute_proc_single('sp_create_email_thread', (self.org_id, subject, project_id, customer_id, linked_by))
            thread = {'thread_id': row['thread_id'], 'project_id': project_id, 'customer_id': customer_id}
        elif project_id and not thread.get('project_id'):
            db.execute_proc('sp_set_thread_project', (thread['thread_id'], self.org_id, project_id, linked_by), fetch=False)
            thread['project_id'] = project_id
        saved = db.execute_proc_single('sp_add_email_message', (self.org_id, account_id, thread['thread_id'], m))
        if not saved:
            return None
        for f in m.get('files') or []:
            db.execute_proc('sp_add_email_file', (self.org_id, saved['message_id'], f['name'], f['type'], f['data']))
        result = {'thread_id': thread['thread_id'], 'project_id': thread.get('project_id'),
                  'customer_id': thread.get('customer_id') or customer_id, 'new_thread': new_thread}
        self._notify(m, result)
        return result

    def _notify(self, m: Dict, r: Dict):
        import activity
        who = m['from_name'] or m['from_address']
        link = f"/emails/{r['thread_id']}"
        if r['project_id']:
            activity.record('email_received' if m['direction'] == 'in' else 'email_sent',
                            f"{'Email from ' + who if m['direction'] == 'in' else 'Email sent'}: {normalize_subject(m['subject'])}",
                            project_id=r['project_id'], link=link, body=(m['body_text'] or '')[:200],
                            org_id=self.org_id, actor=None, notify=m['direction'] == 'in')
        elif r['customer_id'] and m['direction'] == 'in' and r['new_thread']:
            activity.record('email_received', f'New email from {who} (not in a project yet): {normalize_subject(m["subject"])}',
                            link=link, body=(m['body_text'] or '')[:200], org_id=self.org_id, actor=None)


# ---------------------------------------------------------------- IMAP

def _connect(cfg):
    box = (imaplib.IMAP4_SSL if cfg['ssl'] else imaplib.IMAP4)(cfg['host'], cfg['port'], timeout=60)
    box.login(cfg['user'], cfg['password'])
    return box


LIST_LINE = re.compile(r'^\((?P<flags>[^)]*)\)\s+(?:"(?:[^"\\]|\\.)*"|NIL)\s+(?P<name>"(?:[^"\\]|\\.)*"|\S+)\s*$')


def folder_name(list_line: str) -> Optional[str]:
    """The folder in a LIST reply line: (\\HasNoChildren \\Sent) "/" "[Gmail]/Sent Mail" -> [Gmail]/Sent Mail"""
    m = LIST_LINE.match(list_line.strip())
    if not m:
        return None
    name = m.group('name')
    if name.startswith('"'):
        name = re.sub(r'\\(.)', r'\1', name[1:-1])
    return name


def _folders(box, cfg) -> List[str]:
    if cfg['folders']:
        return cfg['folders']
    folders = ['INBOX']
    typ, data = box.list()
    for line in data or []:
        text = line.decode(errors='replace') if isinstance(line, bytes) else str(line)
        if '\\Sent' in text:
            name = folder_name(text)
            if name and name not in folders:
                folders.append(name)
    return folders


def _quote(folder: str) -> str:
    return '"' + folder.replace('\\', '\\\\').replace('"', '\\"') + '"'


def involves(headers: bytes, terms: List[str]) -> bool:
    """Is any From/To/Cc address one of these addresses, or at one of these domains (or a subdomain)?"""
    msg = email.message_from_bytes(headers or b'')
    addresses = [a.lower() for _, a in getaddresses(sum((msg.get_all(h) or [] for h in ('From', 'To', 'Cc')), []))]
    for term in (t.lower() for t in terms):
        if any(a == term if '@' in term else a.endswith('@' + term) or a.endswith('.' + term) for a in addresses):
            return True
    return False


def _matching_uids(box, uids: List[int], terms: List[str], chunk: int = 200) -> set:
    """Fetch just the address headers (servers disagree on SEARCH FROM/TO semantics) and filter here."""
    wanted = set()
    for i in range(0, len(uids), chunk):
        typ, parts = box.uid('FETCH', ','.join(map(str, uids[i:i + chunk])),
                             '(UID BODY.PEEK[HEADER.FIELDS (FROM TO CC)])')
        for part in parts or []:
            if isinstance(part, tuple) and len(part) > 1:
                m = re.search(rb'\bUID (\d+)', part[0])
                if m and involves(part[1], terms):
                    wanted.add(int(m.group(1)))
    return wanted


def sync_folder(box, folder, state: Dict, store_one, since_days: int, match: Optional[List[str]] = None) -> int:
    typ, _ = box.select(_quote(folder), readonly=True)
    if typ != 'OK':
        logger.warning('Cannot open folder %s', folder)
        return 0
    validity = int((box.untagged_responses.get('UIDVALIDITY') or [b'0'])[0])
    if state.get('uidvalidity') != validity:          # folder was rebuilt on the server: start over
        state.clear()
        state['uidvalidity'] = validity
    last = int(state.get('last_uid') or 0)
    if last:
        typ, data = box.uid('SEARCH', None, f'UID {last + 1}:*')
    else:
        since = (datetime.now() - timedelta(days=since_days)).strftime('%d-%b-%Y')
        typ, data = box.uid('SEARCH', None, f'SINCE {since}')
    uids = sorted(int(u) for u in (data[0].split() if data and data[0] else []) if int(u) > last)
    wanted = _matching_uids(box, uids, match) if match else set(uids)
    count = 0
    for uid in uids:
        if uid in wanted:
            typ, parts = box.uid('FETCH', str(uid), '(BODY.PEEK[])')
            raw = next((p[1] for p in parts or [] if isinstance(p, tuple) and len(p) > 1), None)
            if raw and store_one(raw, uid):
                count += 1
        state['last_uid'] = uid                       # skipped mail isn't looked at again either
    return count


def sync_account(cfg: Dict, since_days: Optional[int] = None) -> Dict:
    since_days = since_days or int(os.getenv('EMAIL_SYNC_DAYS', '90'))
    orgs = db.execute_proc('sp_find_organizations_by_domain', (cfg['org_domain'],)) or []
    if not orgs:
        return {'address': cfg['address'], 'error': f"No organization with domain {cfg['org_domain']}"}
    org_id = orgs[-1]['org_id']                       # the oldest organization with this domain
    account = db.execute_proc_single('sp_upsert_email_account', (org_id, cfg['address'], cfg['prefix']))
    state = dict(account.get('folder_state') or {})
    linker = Linker(org_id, {cfg['org_domain']})
    stored = 0

    def store_one(raw, uid):
        try:
            return linker.store(account['account_id'], parse_message(raw, uid, linker.org_domains))
        except DatabaseError:
            logger.exception('Could not store message %s in %s', uid, cfg['address'])
            return None

    error = None
    try:
        box = _connect(cfg)
        try:
            for folder in _folders(box, cfg):
                folder_state = state.setdefault(folder, {})
                stored += sync_folder(box, folder, folder_state, store_one, since_days, cfg['match'])
                db.execute_proc('sp_save_email_account_state', (account['account_id'], state, None), fetch=False)
        finally:
            try:
                box.logout()
            except Exception:
                pass
    except (imaplib.IMAP4.error, OSError) as e:
        error = f'{type(e).__name__}: {e}'[:500]
        logger.error('Email sync failed for %s: %s', cfg['address'], error)
    db.execute_proc('sp_save_email_account_state', (account['account_id'], state, error), fetch=False)
    return {'address': cfg['address'], 'stored': stored, 'error': error}


def sync_all() -> List[Dict]:
    results = [sync_account(cfg) for cfg in accounts_from_env()]
    for r in results:
        logger.info('email sync', extra={'event': 'email_sync', **{k: v for k, v in r.items() if k != 'error'},
                                         'error': r.get('error')})
    return results
