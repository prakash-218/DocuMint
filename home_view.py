"""
The new home page (frontend/src/islands/home/): what needs doing, and the money still to come in, as one
JSON (GET /api/home). What needs doing comes from where each project is (project_view.projects_list), so
it says the same as the projects list and the project pages.

Until customers have payment terms, money owed is aged by the invoice's date (as Tally can), not a due date.
"""

from datetime import date, datetime
from typing import Callable, Dict, List, Optional

from app_helpers import to_date
from document_service import get_org_profile
from documents import balance_of, display_number, fiscal_year, fy_start_month, get_type

AGES = ((30, '0–30 days'), (60, '31–60 days'), (90, '61–90 days'), (None, 'Over 90 days'))
SHOWN = 5

# Where a project is -> the heading it needs attention under (in this order), and what moves it on
ATTENTION = (
    ('follow_up', 'Quotations with no answer for over two weeks'),
    ('accepted', 'Accepted, advance not asked for'),
    ('advance', "Advances that haven't arrived"),
    ('invoice', 'Ready to invoice'),
    ('payment', 'Waiting for payment'),
    ('drafts', 'Drafts not sent'),
    ('paid_open', 'Paid in full, still open'),
)


# How many, in words, for the row on Home: "3 projects ready to invoice"
COUNTED = {
    'follow_up': ('quotation with no answer after 14 days', 'quotations with no answer after 14 days'),
    'accepted': ('quotation accepted, advance not asked for', 'quotations accepted, advance not asked for'),
    'advance': ('advance requested, not received', 'advances requested, not received'),
    'invoice': ('project ready to invoice', 'projects ready to invoice'),
    'payment': ('project waiting for payment', 'projects waiting for payment'),
    'drafts': ('draft not sent', 'drafts not sent'),
    'paid_open': ('project paid in full, still open', 'projects paid in full, still open'),
}


def _group_of(row: Dict) -> Optional[str]:
    if row['status'] != 'open':
        return None
    stage, pill = row['stage'], row['pill']['text']
    if stage == 'accepted' and row['tone'] == 'action':
        return 'follow_up'
    if stage == 'advance':
        return 'advance' if pill == 'Waiting for advance' else 'accepted' if pill == 'Accepted' else None
    if stage == 'invoiced' and pill == 'To invoice':
        return 'invoice'
    if stage == 'paid':
        return 'payment'
    if stage is None and pill == 'Paid':
        return 'paid_open'
    return None


def _totals(rows: List[Dict], amount) -> Dict[str, float]:
    """Per currency, to the paisa."""
    out: Dict[str, float] = {}
    for r in rows:
        value = amount(r)
        if value:
            currency = r.get('currency') or r.get('currency_code') or 'INR'
            out[currency] = round(out.get(currency, 0) + float(value), 2)
    return out


def attention(rows: List[Dict], drafts: List[Dict]) -> List[Dict]:
    """The headings with something under them: count, total where it's money, and the first few."""
    groups: Dict[str, List[Dict]] = {key: [] for key, _ in ATTENTION}
    for r in rows:
        key = _group_of(r)
        if key:
            groups[key].append(r)
    out = []
    for key, title in ATTENTION:
        if key == 'drafts':
            items = [{'title': d['label'], 'sub': d['sub'], 'amount': d['total'], 'currency': d['currency'], 'url': d['url'],
                      'action': 'Finish it'} for d in drafts]
            total = _totals(drafts, lambda d: d['total'])
        else:
            amount = {'payment': lambda r: r['due'], 'advance': lambda r: r['advance']}.get(key, lambda r: r['quoted'])
            members = sorted(groups[key], key=lambda r: -(amount(r) or 0)) if key in ('payment', 'advance') else groups[key]
            items = [{'title': r['title'], 'sub': ' · '.join(filter(None, [r['customer']['site'] or r['customer']['name'], r['label'], r['sub']])),
                      'amount': amount(r), 'currency': r['currency'], 'url': r['url'], 'action': r['action']} for r in members]
            total = _totals(members, amount)
        if items:
            one, many = COUNTED[key]
            names = [i['title'] for i in items]
            out.append({'key': key, 'title': title, 'label': f'{len(items)} {one if len(items) == 1 else many}',
                        'names': ' · '.join(names[:4]) + (f' and {len(names) - 4} more' if len(names) > 4 else ''),
                        'count': len(items), 'total': total, 'items': items[:SHOWN], 'more': max(0, len(items) - SHOWN)})
    return out


def to_receive(invoices: List[Dict], waiting_for_advance: List[Dict], today: date) -> Dict:
    """Money owed on sent tax invoices, by the invoices' age and by customer; and the advances asked for on the
    projects still waiting for one (projects_list rows)."""
    owed = [d for d in invoices if d.get('status') != 'draft' and balance_of(d) > 0.005]
    ages = []
    for limit, label in AGES:
        lower = ages[-1]['limit'] if ages else -1
        bucket = [d for d in owed if (to_date(d.get('issue_date')) and lower < (today - to_date(d['issue_date'])).days
                                      and (limit is None or (today - to_date(d['issue_date'])).days <= limit))]
        ages.append({'label': label, 'limit': limit if limit is not None else 10 ** 6, 'count': len(bucket),
                     'total': _totals(bucket, balance_of)})
    by_customer: Dict[str, Dict] = {}
    for d in owed:
        name = ' · '.join(filter(None, [d.get('customer_name'), d.get('customer_site')]))
        c = by_customer.setdefault(d['customer_id'], {'name': name, 'count': 0, 'total': {}})
        c['count'] += 1
        cur = d.get('currency_code') or 'INR'
        c['total'][cur] = c['total'].get(cur, 0) + balance_of(d)
    customers = sorted(by_customer.items(), key=lambda kv: -sum(kv[1]['total'].values()))[:SHOWN]
    return {'total': _totals(owed, balance_of), 'count': len(owed),
            'ages': [{k: v for k, v in a.items() if k != 'limit'} for a in ages],
            'customers': [{'id': cid, **c} for cid, c in customers],
            'advances': {'count': len(waiting_for_advance), 'total': _totals(waiting_for_advance, lambda r: r['advance'])}}


def first_name(email: Optional[str]) -> str:
    """'ravi@...' -> 'Ravi', for the greeting; nothing when the address isn't a name ('info@', 'demo-1@')."""
    local = (email or '').split('@')[0]
    return '' if not local.isalpha() or local.lower() in ('info', 'admin', 'office', 'accounts', 'sales', 'contact') else local.capitalize()


def build(org_id, role: str, url: Callable, today: Optional[date] = None, email: Optional[str] = None) -> Dict:
    import project_view
    import revisions
    from auth import MAIL_READERS
    from db import db
    today = today or date.today()
    rows = project_view.projects_list(org_id, role, url, today)['projects']
    docs = revisions.collapse(db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [])
    live = [d for d in docs if d.get('status') != 'revised']
    drafts = [{'label': f"{get_type(d.get('doc_type')).label} {display_number(d) or '(draft)'}",
               'sub': d.get('customer_site') or d.get('customer_name') or '', 'total': float(d.get('total_amount') or 0),
               'currency': d.get('currency_code') or 'INR', 'url': url('invoices_bp.edit_invoice', invoice_id=d['invoice_id'])}
              for d in live if (d.get('status') or 'draft') == 'draft']
    invoices = [d for d in live if d.get('doc_type') in ('invoice', 'export_invoice')]
    sent_quotes = [d for d in live if d.get('doc_type') == 'quote' and d.get('status') == 'sent']
    month_start = today.replace(day=1)
    payments = db.execute_proc('sp_list_org_payments', (org_id, month_start.isoformat())) or []
    month_invoiced = [d for d in invoices if d.get('status') != 'draft' and to_date(d.get('issue_date')) and to_date(d['issue_date']) >= month_start]
    unfiled = 0
    if role in MAIL_READERS:
        unfiled = (db.execute_proc_single('sp_count_email_threads', (org_id, None, None, True)) or {}).get('n') or 0
    events = db.execute_proc('sp_list_recent_events', (org_id, 8)) or []
    receive = to_receive(invoices, [r for r in rows if _group_of(r) == 'advance'], today)
    for c in receive['customers']:
        c['url'] = url('customers_bp.view_customer_new', customer_id=c['id'])
    return project_view._plain({
        'attention': attention(rows, drafts),
        'unfiled_emails': {'count': unfiled, 'url': url('emails_bp.inbox')} if unfiled else None,
        'to_receive': receive,
        'hello': {'name': first_name(email), 'today': today, 'fy': fiscal_year(today, fy_start_month(get_org_profile(org_id)[1])),
                  'greeting': 'Good morning' if datetime.now().hour < 12 else 'Good afternoon' if datetime.now().hour < 17 else 'Good evening'},
        'open_quotes': {'count': len(sent_quotes), 'total': _totals(sent_quotes, lambda d: d.get('total_amount'))},
        'month': {'label': f'{today:%B}', 'invoiced': _totals(month_invoiced, lambda d: d.get('total_amount')),
                  'received': _totals([{'currency': p.get('currency_code'), 'amount': p.get('amount')} for p in payments],
                                      lambda p: p['amount'])},
        'recent': [{'id': e['event_id'], 'kind': e['kind'], 'title': e['title'], 'when': e['created_at'], 'link': e.get('link'),
                    'who': (e.get('actor_email') or '').split('@')[0] or None, 'project': e.get('project_title'),
                    'project_url': url('projects_bp.view_project_new', project_id=e['project_id']) if e.get('project_id') else None}
                   for e in events],
        'links': {'projects': url('projects_bp.board'), 'classic': url('dashboard_bp.index')},
    })
