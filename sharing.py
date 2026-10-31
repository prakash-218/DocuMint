"""
Sharing a document where an email can't go. A private link (the share_link table) opens the document's page and its
PDF without signing in: its token is long and random, so it can't be guessed, and it works until someone turns it
off. WhatsApp gets a message with that link (wa.me can't attach a file), to a contact of the project you pick or to
whoever you choose in WhatsApp. A proforma or invoice with something due also shows its UPI QR code (upi.py).
"""

import re
import secrets
from datetime import date
from typing import Callable, Dict, List, Optional
from urllib.parse import quote

from documents import display_number, get_type, load_json
from money import format_money


def new_token() -> str:
    """43 random characters: the link's only key, so it's as hard to guess as a strong password."""
    return secrets.token_urlsafe(32)


def wa_number(phone) -> str:
    """A phone number as wa.me wants it, digits with the country code: a 10-digit Indian mobile gets 91; '' when it
    isn't a number WhatsApp could have."""
    digits = re.sub(r'\D', '', phone or '')
    if len(digits) == 10:
        return '91' + digits
    if len(digits) == 11 and digits.startswith('0'):
        return '91' + digits[1:]
    return digits if 11 <= len(digits) <= 15 else ''


def wa_link(text: str, number: str = '') -> str:
    """WhatsApp with this message ready: to the number, or to whoever is picked in WhatsApp."""
    return f"https://wa.me/{number}?text={quote(text, safe='')}"


def _when(value) -> str:
    from app_helpers import to_date
    found = to_date(value)
    return f'{found.day} {found:%b %Y}' if found else ''


def message(header: Dict, summary: Dict, link: str, pay: Optional[Dict], usual_days: Optional[int] = None,
            today: Optional[date] = None) -> str:
    """The message the link goes with, after the greeting: what the document is and what it's for, what's due and by
    when, how to pay by UPI, the link, and who it's from."""
    from document_list import short_subject
    from payment_terms import due_on
    kind = get_type(header.get('doc_type'))
    currency = header.get('currency_code') or 'INR'
    money = lambda v: format_money(v, currency, decimals=False)  # noqa: E731
    number = display_number(header)
    subject = short_subject(load_json(header.get('details')).get('subject'))
    what = {'quote': 'quotation', 'proforma': 'proforma invoice'}.get(kind.key, 'invoice')
    about = f'our {what} {number}' + (f' for {subject[:1].lower()}{subject[1:]}' if subject else '')
    total = float(summary.get('total') or 0)
    gst = ' incl. GST' if summary.get('tax_lines') else ''
    lines = []
    if kind.key == 'quote':
        lines.append(f'Please find {about}: {money(total)}{gst}.')
    elif pay or (kind.takes_payments and float(summary.get('balance') or 0) > 0.005):
        owed = pay['amount'] if pay else float(summary.get('balance') or 0)
        due = due_on(header, usual_days) if kind.takes_payments else None
        if kind.takes_advances:
            lines.append(f'Please find {about}. The advance of {money(owed)} is due.')
        else:
            late = due and due < (today or date.today())
            lines.append(f'Please find {about}: {money(total)}{gst}, {money(owed)} '
                         + (f'due since {_when(due)}.' if late else f'due by {_when(due)}.' if due else 'due.'))
        if pay:
            lines.append(f"Pay by UPI to {pay['upi_id']}, or scan the QR code on the page.")
    else:
        lines.append(f'Please find {about}: {money(total)}{gst}.')
    lines += [link, '', 'Regards,', header.get('organization_name') or '']
    return '\n'.join(lines)


def people(contacts: List[Dict], doc: Dict) -> List[Dict]:
    """The project's contacts with a WhatsApp number, those who get this kind of document first: [{name, role, phone,
    number, gets_it}]. Nobody is picked for you."""
    from document_view import who_gets_it
    getting = {c.get('contact_id') for c in who_gets_it(doc, contacts)}
    out = [{'name': c.get('name') or '', 'role': c.get('role') or '', 'phone': c.get('phone') or '',
            'number': wa_number(c.get('phone')), 'gets_it': c.get('contact_id') in getting} for c in contacts]
    return sorted([p for p in out if p['number']], key=lambda p: not p['gets_it'])


def state(header: Dict, link: Optional[Dict], url: Callable, external: Callable) -> Dict:
    """The share dialog's link: its address and how often it was opened, or None while there's none. external(path)
    makes the full address someone else can open."""
    if not link:
        return {'link': None}
    return {'link': {'url': external(url('shared_bp.page', token=link['token'])), 'opens': int(link.get('opens') or 0),
                     'last_opened': _when(link.get('last_opened_at')), 'made': _when(link.get('created_at'))}}
