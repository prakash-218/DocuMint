"""
A customer's statement of account, to print or email: their account in one currency for a financial year (or every
year), with what was brought forward, each invoice they owe and each payment they made, the balance after each,
and the invoices still unpaid with when they were due (payment_terms.py). The lines are customer_view.statement's,
so the PDF says what the customer page's Statement tab says.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from app_helpers import to_date
from documents import balance_of, display_number, fy_start_month, get_type
from payment_terms import due_on, usual_days

INVOICE_TYPES = ('invoice', 'export_invoice')


def period(fy: str, start_month: int = 4) -> Tuple[date, date]:
    """The first and last day of a financial year label: '26-27' -> 1 Apr 2026 to 31 Mar 2027; '2026' (a calendar
    year, start_month 1) -> 1 Jan to 31 Dec 2026."""
    first = int(fy) if start_month == 1 else 2000 + int(fy.split('-')[0])
    start = date(first, start_month, 1)
    return start, date(first + 1, start_month, 1) - timedelta(days=1)


def pick(accounts: List[Dict], fy: Optional[str] = None, currency: Optional[str] = None) -> Optional[Dict]:
    """One account for one year, as the Statement tab shows it: {currency, fy (None: every year), years, opening,
    lines, closing, owed, paid}. fy: a year it has lines in, 'all', or None for the latest."""
    account = next((a for a in accounts if a['currency'] == currency), accounts[0] if accounts else None)
    if not account:
        return None
    years = list(dict.fromkeys(line['fy'] for line in reversed(account['lines']) if line['fy']))
    fy = None if fy == 'all' else fy if fy in years else years[0] if years else None
    first = next((i for i, line in enumerate(account['lines']) if line['fy'] == fy), 0) if fy else 0
    lines = [line for line in account['lines'] if line['fy'] == fy] if fy else account['lines']
    opening = account['lines'][first - 1]['balance'] if fy and first > 0 else 0.0
    return {'currency': account['currency'], 'fy': fy, 'years': years, 'opening': opening, 'lines': lines,
            'closing': lines[-1]['balance'] if lines else opening,
            'owed': round(sum(line['owed'] for line in lines), 2), 'paid': round(sum(line['paid'] for line in lines), 2)}


def unpaid(docs: List[Dict], currency: str, today: date, usual: Optional[int] = None) -> List[Dict]:
    """Finalized tax invoices with something still to come in, oldest first, with when each was due and how late."""
    out = []
    for d in docs:
        if d.get('doc_type') not in INVOICE_TYPES or d.get('status') != 'pending' or (d.get('currency_code') or 'INR') != currency:
            continue
        balance = balance_of(d)
        if balance <= 0.005:
            continue
        due = due_on(d, usual)
        out.append({'text': f"{get_type(d['doc_type']).label} {display_number(d)}", 'site': d.get('customer_site'),
                    'date': to_date(d.get('issue_date')), 'due': due, 'late': max(0, (today - due).days) if due else 0,
                    'total': float(d.get('total_amount') or 0), 'balance': balance})
    return sorted(out, key=lambda x: x['date'] or date.min)


def gather(org_id, customer: Dict, url, fy: Optional[str] = None, currency: Optional[str] = None,
           today: Optional[date] = None) -> Dict:
    """Everything a statement prints, for a customer and (when it's a company) its sites."""
    import revisions
    from customer_view import statement
    from db import db
    from document_service import get_org_profile
    today = today or date.today()
    org, profile = get_org_profile(org_id)
    customer_id = str(customer['customer_id'])
    sites = [] if customer.get('parent_id') else db.execute_proc('sp_list_customer_sites', (org_id, customer_id)) or []
    family = [customer_id] + [str(s['customer_id']) for s in sites]
    docs = revisions.collapse([d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or []
                               if str(d.get('customer_id')) in family])
    payments = db.execute_proc('sp_list_customer_payments', (org_id, family)) or []
    start_month = fy_start_month(profile)
    account = pick(statement(docs, payments, url, start_month, sites=bool(sites)), fy, currency)
    cur = account['currency'] if account else (currency or 'INR')
    owing = unpaid(docs, cur, today, usual_days(profile))
    return {'org': org or {}, 'profile': profile, 'customer': customer, 'sites': bool(sites), 'today': today,
            'account': account, 'period': period(account['fy'], start_month) if account and account['fy'] else None,
            'unpaid': owing, 'overdue': round(sum(x['balance'] for x in owing if x['late'] > 0), 2)}


def title(data: Dict) -> str:
    """'Statement of account FY 26-27' (or 'to date', for every year)."""
    fy = (data.get('account') or {}).get('fy')
    return f'Statement of account FY {fy}' if fy else 'Statement of account to date'


def filename(data: Dict) -> str:
    name = ''.join(ch if ch.isalnum() else '-' for ch in data['customer'].get('name') or 'customer').strip('-')
    fy = (data.get('account') or {}).get('fy')
    return f"Statement-{name}-{('FY-' + fy) if fy else 'to-date'}.pdf"


def render_pdf(data: Dict) -> bytes:
    """The statement as an A4 PDF, under the organization's letterhead (the quotation's)."""
    from invoice_service import _document_pdf, pdf_fonts
    from layout import printed_org_fields
    org, profile = data['org'], data['profile']
    letterhead = {f'organization_{k}': org.get(k) for k in ('street_address', 'city', 'zip_code', 'country')}
    letterhead['organization_name'] = org.get('name')
    return _document_pdf('pdf/statement.html', number_if_long=True, invoice=letterhead, fonts=pdf_fonts(),
                         org_fields=printed_org_fields(profile), title=title(data), **data)
