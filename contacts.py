"""
Contacts: the people at a customer that documents and emails go to, what each gets on a project, and
the people (and phone numbers) in a project's emails who aren't contacts yet.

A contact belongs to one customer (a site's projects also use the parent company's contacts). What a
contact gets is set on the contact, as what they usually get, and can be changed on each project.
"""

import os
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from db import db, DatabaseError

GETS = {'all': 'Gets everything', 'billing': 'Proformas and invoices only', 'none': 'Not on this project'}
USUALLY = {'all': 'Everything', 'billing': 'Proformas and invoices', 'none': 'Only when picked on a project'}
MAX_SUGGESTIONS = 8

NOT_A_PERSON = re.compile(r'^(no-?reply|do-?not-?reply|mailer-daemon|postmaster|bounces?|notifications?|alerts?)\b', re.I)
# Indian mobiles (+91 98400 12345, 9840012345) and landlines with an STD code (044-2345 6789)
PHONE = re.compile(r'(?<![\d+])(?:(?:\+|00)?91[\s.-]?)?(?:[6-9]\d{4}[\s.-]?\d{5}|0\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})(?![\d])')
# Where the quoted part of a reply starts: "> ...", "On <date>, X wrote:", Outlook's "From: ..." block
QUOTED = re.compile(r'^\s*(>|on\b.{0,200}\bwrote:|-{2,}\s*original message|_{5,}|from:\s)', re.I | re.M)
SIGNATURE_LINES = 15


def valid_gets(value: Optional[str], default: str = 'all') -> str:
    return value if value in GETS else default


def family_ids(customer: Dict) -> List[str]:
    """The customer, and its parent when it's a site: whose contacts it uses."""
    return [str(i) for i in (customer.get('customer_id'), customer.get('parent_id')) if i]


def initials(name: str) -> str:
    """'Mr. K. Arun Kumar' -> 'AK'"""
    words = [w for w in re.split(r'[\s.]+', re.sub(r'^(mr|mrs|ms|dr|shri|smt)\.?\s+', '', name or '', flags=re.I)) if len(w) > 1]
    return ''.join(w[0] for w in (words[:1] + words[-1:] if len(words) > 1 else words)).upper() or '?'


def _with_initials(rows: List[Dict]) -> List[Dict]:
    return [{**r, 'initials': initials(r.get('name'))} for r in rows]


def for_customer(org_id, customer: Dict) -> List[Dict]:
    try:
        return _with_initials(db.execute_proc('sp_list_contacts', (org_id, family_ids(customer))) or [])
    except DatabaseError:
        return []


def for_project(org_id, project_id) -> List[Dict]:
    try:
        return _with_initials(db.execute_proc('sp_list_project_contacts', (project_id, org_id)) or [])
    except DatabaseError:
        return []


# ---------------------------------------------------------------- Found in emails (pure)

def name_from_address(address: str) -> str:
    """'arun.s@x.com' -> 'Arun S': a starting point for someone who was only ever copied in."""
    local = address.split('@')[0].split('+')[0]
    words = [w for w in re.split(r'[._-]+', local) if w and not w.isdigit()]
    return ' '.join(w.capitalize() for w in words) or address


def new_part(body: str) -> str:
    """The text someone wrote in this message, without the earlier mail quoted under it."""
    found = QUOTED.search(body or '')
    return (body[:found.start()] if found else body or '').strip()


def phones_in(body: str, skip_digits: Iterable[str] = ()) -> List[str]:
    """Phone numbers in the signature: the last lines of what the sender wrote."""
    lines = new_part(body).splitlines()[-SIGNATURE_LINES:]
    out, seen = [], set(skip_digits)
    for match in PHONE.finditer('\n'.join(lines)):
        key = digits(match.group())
        if len(key) >= 10 and key not in seen:
            seen.add(key)
            out.append(tidy_phone(match.group()))
    return out


def digits(phone: str) -> str:
    """The last ten digits: '+91 98400 12345' and '098400 12345' compare equal."""
    return re.sub(r'\D', '', phone or '')[-10:]


def tidy_phone(raw: str) -> str:
    d = re.sub(r'\D', '', raw)
    if len(d) >= 10 and d[-10] in '6789' and (len(d) == 10 or d[:-10] in ('91', '091', '0091', '0')):
        return f'+91 {d[-10:-5]} {d[-5:]}'
    return re.sub(r'\s+', ' ', raw.strip())


def _addresses(text: Optional[str]) -> List[str]:
    return [a.strip().lower() for a in (text or '').split(',') if '@' in a]


def _when(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def suggestions(messages: List[Dict], contacts: List[Dict], ignored: Iterable[str], own_domains: Iterable[str],
                own_phones: str = '') -> Dict[str, List[Dict]]:
    """People in these emails who aren't contacts yet, and phone numbers in the signatures of people who
    are. messages: newest first, as sp_list_project_email_people gives them."""
    own = {d.lower().lstrip('@') for d in own_domains if d}
    ignored = set(ignored)
    known = {c['email']: c for c in contacts if c.get('email')}
    own_digits = {digits(p) for p in PHONE.findall(own_phones or '')}
    people: Dict[str, Dict] = {}
    phones: List[Dict] = []

    def outsider(address):
        return ('@' in address and address.split('@')[1] not in own and not NOT_A_PERSON.match(address)
                and address not in known and address not in ignored)

    for m in messages:
        sender = (m.get('from_address') or '').lower()
        incoming = m.get('direction') != 'out'
        when = _when(m.get('sent_at'))
        others = _addresses(m.get('to_addresses')) + _addresses(m.get('cc_addresses'))
        involved = ([(sender, 'wrote')] if incoming else []) + [(a, 'copied' if incoming else 'written to') for a in others]
        for address, how in involved:
            if not outsider(address):
                continue
            p = people.setdefault(address, {'email': address, 'name': name_from_address(address), 'wrote': 0,
                                            'copied': 0, 'written to': 0, 'last': when, 'phone': None})
            p[how] += 1
            if how == 'wrote' and (m.get('from_name') or '').strip() and m['from_name'].strip().lower() != address:
                p['name'] = m['from_name'].strip()[:150]
        if not incoming or not sender:
            continue
        for phone in phones_in(m.get('body_text') or '', own_digits):
            if 'tel:' + digits(phone) in ignored:
                continue
            if sender in people and not people[sender]['phone']:
                people[sender]['phone'] = phone
            contact = known.get(sender)
            if contact and digits(contact.get('phone') or '') != digits(phone) \
                    and not any(s['contact_id'] == contact['contact_id'] for s in phones):
                phones.append({'contact_id': contact['contact_id'], 'name': contact['name'], 'phone': phone,
                               'value': 'tel:' + digits(phone), 'when': when, 'replaces': contact.get('phone')})
            break       # the first number in a signature is usually theirs; the rest are the office's

    listed = sorted(people.values(), key=lambda p: (p['wrote'] == 0, -(p['last'].timestamp() if p['last'] else 0)))
    for p in listed:
        p['seen'] = seen_text(p)
    return {'people': listed[:MAX_SUGGESTIONS], 'phones': phones[:MAX_SUGGESTIONS]}


def seen_text(p: Dict) -> str:
    """'Wrote 3 emails, last 21 Oct', 'Copied on an email, 21 Oct', 'We emailed them, 4 Nov'."""
    if p['wrote']:
        n, what = p['wrote'], ('Wrote an email' if p['wrote'] == 1 else f"Wrote {p['wrote']} emails")
    elif p['copied']:
        n, what = p['copied'], ('Copied on an email' if p['copied'] == 1 else f"Copied on {p['copied']} emails")
    else:
        n, what = p['written to'], ('We emailed them' if p['written to'] == 1 else f"We emailed them {p['written to']} times")
    if not p.get('last'):
        return what
    return f"{what}, {'last ' if n > 1 else ''}{p['last'].day} {p['last']:%b}"


# ---------------------------------------------------------------- Found in emails (with the database)

def own_domains(org_id) -> List[str]:
    """Our side of the conversation: the organization's domain, its mailboxes' domains, EMAIL_ORG_DOMAIN."""
    found = {d.strip().lower() for d in (os.getenv('EMAIL_ORG_DOMAIN') or '').split(',') if d.strip()}
    try:
        org = db.execute_proc_single('sp_get_organization_details', (org_id,)) or {}
        if org.get('domain'):
            found.add(org['domain'].lower())
        for account in db.execute_proc('sp_list_email_accounts', (org_id,)) or []:
            if '@' in (account.get('address') or ''):
                found.add(account['address'].split('@')[1].lower())
    except DatabaseError:
        pass
    return sorted(found)


def project_suggestions(org_id, project: Dict, contacts: List[Dict], own_phones: str = '') -> Dict[str, List[Dict]]:
    """Who in the project's emails could be a contact. Ignored ones are kept per customer (and its parent)."""
    customer = {'customer_id': project.get('customer_id'), 'parent_id': project.get('customer_parent_id')}
    try:
        messages = db.execute_proc('sp_list_project_email_people', (project['project_id'], org_id)) or []
        ignored = [r['value'] for r in db.execute_proc('sp_list_ignored_contacts', (org_id, family_ids(customer))) or []] \
            if messages else []
    except DatabaseError:
        messages = []
    if not messages:
        return {'people': [], 'phones': []}
    return suggestions(messages, contacts, ignored, own_domains(org_id), own_phones)
