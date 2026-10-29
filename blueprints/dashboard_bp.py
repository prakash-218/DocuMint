"""
Dashboard blueprint - main dashboard with statistics
"""

import logging
from datetime import date

from flask import Blueprint, render_template, g, request, redirect, url_for

from db import db, DatabaseError
from auth import require_org, get_current_org_role
from app_helpers import invoice_is_overdue, to_date
from documents import get_type, sum_by_currency
from document_service import get_org_profile

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard_bp', __name__)

STATUS_ORDER = ('paid', 'pending', 'overdue', 'draft')


def _balance(invoice):
    return max(float(invoice.get('total_amount') or 0) - float(invoice.get('paid_amount') or 0), 0.0)


def _status_key(invoice):
    if invoice_is_overdue(invoice):
        return 'overdue'
    status = invoice.get('status') or 'draft'
    return status if status in STATUS_ORDER else 'draft'


def _last_12_months(rows, today):
    """Monthly revenue for the trailing 12 months, oldest first, zero-filled."""
    by_month = {r.get('month'): float(r.get('revenue') or 0) for r in rows or []}
    months = []
    year, month = today.year, today.month
    for _ in range(12):
        months.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    series = []
    for y, m in reversed(months):
        label = date(y, m, 1).strftime('%b')
        series.append({'key': f'{y}-{m:02d}', 'label': label, 'full_label': f'{label} {y}',
                       'revenue': by_month.get(f'{y}-{m:02d}', 0.0)})
    return series


def _month(d):
    d = to_date(d)
    return f'{d.year}-{d.month:02d}' if d else None


def build_dashboard(org_id, today=None, base_currency=None, home_currency='INR'):
    """
    Dashboard numbers. Only tax/export invoices count as revenue; quotes and
    proformas feed the 'open quotes' card. Money is never added across
    currencies: headline figures use the base currency (the profile's default,
    else the most used), and other currencies are listed separately.
    """
    today = today or date.today()
    documents = db.execute_proc('sp_list_invoices', (org_id, None, 1000, 0)) or []
    invoices = [d for d in documents if get_type(d.get('doc_type')).counts_as_revenue]
    quotes = [d for d in documents if d.get('doc_type') == 'quote']

    used = sum_by_currency(invoices, lambda d: 1)
    currencies = list(dict.fromkeys([home_currency] + list(used)))   # home first, then by usage
    if not base_currency or base_currency not in currencies:
        base_currency = home_currency if home_currency in used or not used else next(iter(used))
    in_base = lambda d: (d.get('currency_code') or 'USD') == base_currency
    base_invoices = [i for i in invoices if in_base(i)]

    breakdown = {key: {'count': 0, 'amount': 0.0} for key in STATUS_ORDER}
    for inv in base_invoices:
        key = _status_key(inv)
        breakdown[key]['count'] += 1
        breakdown[key]['amount'] += float(inv.get('total_amount') or 0)

    open_all = [i for i in invoices if i.get('status') == 'pending' and _balance(i) > 0]
    open_invoices = [i for i in open_all if in_base(i)]
    overdue = [i for i in open_invoices if invoice_is_overdue(i)]
    other_outstanding = {k: v for k, v in sum_by_currency(open_all, _balance).items() if k != base_currency}

    # Revenue = finalized invoices by issue month, base currency
    revenue_rows = {}
    for inv in base_invoices:
        if inv.get('status') in ('pending', 'paid') and _month(inv.get('issue_date')):
            m = _month(inv['issue_date'])
            revenue_rows[m] = revenue_rows.get(m, 0.0) + float(inv.get('total_amount') or 0)
    this_key = f'{today.year}-{today.month:02d}'
    last = date(today.year - (today.month == 1), (today.month - 2) % 12 + 1, 1)
    this_month = revenue_rows.get(this_key, 0.0)
    last_month = revenue_rows.get(f'{last.year}-{last.month:02d}', 0.0)
    delta = ((this_month - last_month) / last_month * 100) if last_month else None
    issued_this_month = sum(1 for i in invoices if _month(i.get('issue_date')) == this_key)

    # Payments this month: in the selected currency, and what reached the bank in the
    # home currency (home-currency payments + foreign ones at their credited amount)
    month_start = today.replace(day=1)
    payments = db.execute_proc('sp_list_org_payments', (org_id, month_start.isoformat())) or []
    collected = sum(float(p['amount'] or 0) for p in payments if (p.get('currency_code') or 'USD') == base_currency)
    received_home, foreign_converted, foreign_pending = 0.0, {}, 0
    for p in payments:
        cur = p.get('currency_code') or 'USD'
        if cur == home_currency:
            received_home += float(p['amount'] or 0)
        elif p.get('received_amount') and (p.get('received_currency') or home_currency) == home_currency:
            received_home += float(p['received_amount'])
            foreign_converted[cur] = foreign_converted.get(cur, 0.0) + float(p['amount'] or 0)
        else:
            foreign_pending += 1

    open_quotes = [q for q in quotes if q.get('status') in ('sent', 'accepted')]

    owed = {}
    for inv in open_invoices:
        entry = owed.setdefault(inv.get('customer_id'), {'name': inv.get('customer_name'), 'amount': 0.0, 'count': 0})
        entry['amount'] += _balance(inv)
        entry['count'] += 1
    top_owed = sorted(owed.values(), key=lambda e: e['amount'], reverse=True)[:5]

    due_soon = sorted(open_all, key=lambda i: to_date(i.get('due_date')) or date.max)[:6]

    return {
        'currency': base_currency,
        'currencies': currencies if len(currencies) > 1 else [],
        'home_currency': home_currency,
        'received': {'home': received_home, 'foreign_converted': foreign_converted, 'foreign_pending': foreign_pending},
        'kpis': {
            'outstanding': sum(_balance(i) for i in open_invoices),
            'outstanding_count': len(open_invoices),
            'other_outstanding': other_outstanding,
            'overdue': sum(_balance(i) for i in overdue),
            'overdue_count': len(overdue),
            'collected_this_month': collected,
            'invoiced_this_month': this_month,
            'invoiced_delta': delta,
            'invoices_this_month': issued_this_month,
            'open_quotes': len(open_quotes),
            'open_quotes_value': sum_by_currency(open_quotes, lambda q: q.get('total_amount')),
        },
        'revenue_series': _last_12_months([{'month': k, 'revenue': v} for k, v in revenue_rows.items()], today),
        'breakdown': breakdown,
        'breakdown_total': sum(b['count'] for b in breakdown.values()),
        'recent_invoices': documents[:6],
        'due_soon': due_soon,
        'top_owed': top_owed,
        'has_invoices': bool(documents),
    }


@dashboard_bp.route('/classic')
@require_org
def index_classic():
    """Dashboard home page"""
    org_id = g.current_org_id
    current_role = get_current_org_role()

    try:
        _, profile = get_org_profile(org_id)
        data = build_dashboard(org_id, base_currency=request.args.get('currency'),
                               home_currency=profile.get('default_currency') or 'INR')
    except DatabaseError:
        logger.exception("Failed to build dashboard for org %s", org_id)
        data = build_empty()
        data['error'] = True

    pending_requests = []
    if current_role in ('owner', 'admin'):
        try:
            pending_requests = db.execute_proc('sp_get_pending_members', (org_id,)) or []
        except DatabaseError:
            logger.exception("Failed to load pending members for org %s", org_id)

    return render_template('dashboard.html', current_org_role=current_role,
                           pending_requests=pending_requests, **data)


def build_empty():
    return {
        'currency': 'USD',
        'currencies': [],
        'home_currency': 'INR',
        'received': {'home': 0.0, 'foreign_converted': {}, 'foreign_pending': 0},
        'kpis': {'outstanding': 0, 'outstanding_count': 0, 'other_outstanding': {}, 'overdue': 0, 'overdue_count': 0,
                 'collected_this_month': None, 'invoiced_this_month': 0, 'invoiced_delta': None,
                 'invoices_this_month': 0, 'open_quotes': 0, 'open_quotes_value': {}},
        'revenue_series': _last_12_months([], date.today()),
        'breakdown': {key: {'count': 0, 'amount': 0.0} for key in STATUS_ORDER},
        'breakdown_total': 0,
        'recent_invoices': [],
        'due_soon': [],
        'top_owed': [],
        'has_invoices': False,
    }


@dashboard_bp.route('/new')
@require_org
def index_new():
    """Where the new home was while it was opt-in."""
    return redirect(url_for('dashboard_bp.index'))


@dashboard_bp.route('/')
@require_org
def index():
    """Home (React, frontend/src/islands/home/): what needs doing first, and the money to come in."""
    return render_template('dashboard_new.html')
