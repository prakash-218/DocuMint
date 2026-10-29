"""
Payment terms: how many days after the invoice date a customer pays (customer.payment_days; a site without its own
uses its parent's), else the organization's usual terms (the business profile's 'payment_days').

A tax invoice with no due date of its own is tracked as due that many days after its date: on the lists, on Home and
on its page. Nothing is written on the invoice, so its printed "Payment due by" line stays what was typed on it.
"""

from datetime import date, timedelta
from typing import Dict, Optional, Tuple

from app_helpers import to_date

MAX_DAYS = 365


def parse_days(value) -> Tuple[Optional[int], Optional[str]]:
    """(days, problem) from a form field: empty is None (not set), else a whole number of days, 0 to 365."""
    text = str(value if value is not None else '').strip()
    if not text:
        return None, None
    if not text.isdigit() or int(text) > MAX_DAYS:
        return None, f'Payment terms are a number of days, 0 to {MAX_DAYS}.'
    return int(text), None


def usual_days(profile: Dict) -> Optional[int]:
    """The organization's usual terms in days, from its business profile; None when they aren't set."""
    return parse_days((profile or {}).get('payment_days'))[0]


def describe(days: Optional[int]) -> str:
    """'30 days', 'On receipt' (0), or '' when not set."""
    if days is None:
        return ''
    return 'On receipt' if days == 0 else f'{days} day{"" if days == 1 else "s"}'


def due_on(doc: Dict, usual: Optional[int] = None) -> Optional[date]:
    """When a tax invoice is due: its own due date, else its date plus the customer's terms (or the usual ones)."""
    own = to_date(doc.get('due_date'))
    if own:
        return own
    days = doc.get('payment_days')
    days = usual if days is None else days
    issued = to_date(doc.get('issue_date'))
    return issued + timedelta(days=int(days)) if issued and days is not None else None
