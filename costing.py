"""
Costings: working out a quotation's prices before making it.

A costing belongs to a project and lists the quote's items. Each item's cost is
typed in, or built from cost lines (material, machining, bought-outs ...), each
with an optional markup (a bought-out at cost x 1.1 is a 10% markup).

Two ways of working, one sheet:
  build   price = cost + profit (the costing's profit %, or the item's own)
  target  the total is known: the cost budget is total / (1 + profit %), and the
          total is shared out over the items in proportion to their cost

Profit is a markup on cost (15% on a cost of 100 is a price of 115); the sheet also
shows it as a share of the price. A price typed for an item is kept as it is in
either mode. Internal only: owners and admins see costings, never customers.

Shared costs (design, a reference station, freight, "10% for changes") belong to no
single item: a fixed amount, or a % of the items' cost, spread over all the items or
the chosen ones, equally or in proportion to their cost.

Costs are in the business's own currency; a quote in another currency converts them at
the costing's exchange rate (rupees per dollar), and prices, profit and totals are in
the quote's currency.
"""

import math
import re
import secrets
from typing import Any, Dict, List, Optional

MODES = {'build': 'Build up from costs', 'target': 'Work back from a total'}
ROUNDING = (0, 1, 10, 100, 1000)
SPREADS = {'equal': 'equally', 'cost': 'by cost'}
SHARED_KINDS = {'amount': 'Amount', 'percent': '% of cost'}
DEFAULT_PROFIT = 15.0
MAX_ITEMS, MAX_LINES, MAX_SHARED = 200, 200, 50


def number(value, default=None) -> Optional[float]:
    """'1,23,500.50' -> 123500.5; blanks and junk -> default."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else default
    text = re.sub(r'[,\s₹$€£]', '', str(value))
    try:
        out = float(text)
    except ValueError:
        return default
    return out if math.isfinite(out) else default


def _text(value, limit) -> str:
    return str(value or '').strip()[:limit]


KEY = re.compile(r'^[a-z0-9]{1,16}$')


def new_key() -> str:
    return 'i' + secrets.token_hex(4)


def _line(line: Dict) -> Optional[Dict]:
    row = {'description': _text(line.get('description'), 300), 'make': _text(line.get('make'), 120),
           'qty': number(line.get('qty')), 'unit': _text(line.get('unit'), 20),
           'unit_cost': number(line.get('unit_cost')), 'markup': number(line.get('markup'))}
    return row if row['description'] or row['unit_cost'] is not None else None


def clean_sheet(raw: Any) -> Dict:
    """The sheet as stored: known keys only, numbers as numbers, blank rows dropped. Items keep a
    key (shared costs name the items they're spread over by it, so dropping a blank row can't shift them)."""
    raw = raw if isinstance(raw, dict) else {}
    items, keys = [], set()
    for item in (raw.get('items') or [])[:MAX_ITEMS]:
        if not isinstance(item, dict):
            continue
        lines = [r for r in (_line(l) for l in (item.get('lines') or [])[:MAX_LINES] if isinstance(l, dict)) if r]
        key = str(item.get('key') or '')
        if not KEY.match(key) or key in keys:
            key = new_key()
        row = {'key': key, 'name': _text(item.get('name'), 300), 'description': _text(item.get('description'), 2000),
               'qty': number(item.get('qty')), 'unit': _text(item.get('unit'), 20),
               'cost_each': number(item.get('cost_each')), 'profit_percent': number(item.get('profit_percent')),
               'price_each': number(item.get('price_each')), 'lines': lines}
        if row['name'] or lines or row['cost_each'] is not None or row['price_each'] is not None:
            items.append(row)
            keys.add(key)
    shared = []
    for s in (raw.get('shared') or [])[:MAX_SHARED]:
        if not isinstance(s, dict):
            continue
        row = _line(s) or {'description': '', 'make': '', 'qty': None, 'unit': '', 'unit_cost': None, 'markup': None}
        kind = s.get('kind') if s.get('kind') in SHARED_KINDS else 'amount'
        row.update({'kind': kind, 'percent': number(s.get('percent')),
                    # a % of cost is that % on each item's cost, so it always goes by cost
                    'spread': 'cost' if kind == 'percent' else s.get('spread') if s.get('spread') in SPREADS else 'equal',
                    'items': [k for k in (s.get('items') or []) if isinstance(k, str) and k in keys]})
        if row['description'] or row['unit_cost'] is not None or row['percent'] is not None:
            shared.append(row)
    rate = number(raw.get('exchange_rate'))
    return {'items': items, 'shared': shared, 'exchange_rate': rate if rate and rate > 0 else None,
            'cost_currency': (str(raw.get('cost_currency') or 'INR').upper()[:3])}


def _round_to(value: float, step: int) -> float:
    if not step:
        return round(value, 2)
    return math.floor(value / step + 0.5) * step                         # half up: 1,23,450 -> 1,23,500


def _qty(value) -> float:
    q = number(value)
    return 1.0 if q is None else q


def _line_cost(line: Dict) -> float:
    each = (line.get('unit_cost') or 0) * (1 + (line.get('markup') or 0) / 100)
    return round(_qty(line.get('qty')) * each, 2)


def _spread(shared: List[Dict], items: List[Dict]) -> List[Dict]:
    """Each shared cost's amount, and every item's share of it (added to item['shared_cost'])."""
    out = []
    for s in shared:
        targets = [it for it in items if it['key'] in s['items']] or items
        own = sum(it['own_cost_total'] for it in targets)
        amount = round((s.get('percent') or 0) / 100 * own, 2) if s['kind'] == 'percent' else _line_cost(s)
        weights = [it['own_cost_total'] for it in targets] if s['spread'] == 'cost' and own else [1] * len(targets)
        total_weight = sum(weights)
        for it, w in zip(targets, weights):
            it['shared_cost'] += amount * w / total_weight if total_weight else 0
        out.append({**s, 'amount': amount, 'spread_over': len(targets), 'all_items': len(targets) == len(items)})
    return out


def compute(sheet: Dict, mode: str = 'build', profit_percent=DEFAULT_PROFIT, target_total=None,
            round_to: int = 0, currency: Optional[str] = None) -> Dict:
    """Every number on the sheet: per line, per item and in total. Costs (cost_each, cost_total) are
    in the sheet's cost currency; prices, amounts, profit and the totals in the quote's currency."""
    mode = mode if mode in MODES else 'build'
    default_profit = number(profit_percent, DEFAULT_PROFIT)
    round_to = round_to if round_to in ROUNDING else 0
    cost_currency = (sheet.get('cost_currency') or 'INR').upper()
    currency = (currency or cost_currency).upper()
    rate = sheet.get('exchange_rate') if currency != cost_currency else None
    fx = (rate or 1) if currency != cost_currency else 1        # rupees per unit of the quote's currency
    items = []
    for item in sheet.get('items', []):
        lines = [{**line, 'cost': _line_cost(line)} for line in item.get('lines') or []]
        own_each = sum(l['cost'] for l in lines) if lines else (item.get('cost_each') or 0)
        qty = _qty(item.get('qty'))
        own_profit = item.get('profit_percent')
        items.append({**item, 'key': item.get('key') or new_key(), 'lines': lines, 'qty_used': qty,
                      'cost_typed': item.get('cost_each'),
                      'own_cost_each': round(own_each, 2), 'own_cost_total': round(own_each * qty, 2), 'shared_cost': 0.0,
                      'built_from_lines': bool(lines), 'profit_used': default_profit if own_profit is None else own_profit,
                      'manual_price': item.get('price_each') is not None})
    shared = _spread(sheet.get('shared') or [], items)
    for it in items:
        it['shared_cost'] = round(it['shared_cost'], 2)
        it['shared_each'] = round(it['shared_cost'] / it['qty_used'], 2) if it['qty_used'] else 0
        it['cost_total'] = round(it['own_cost_total'] + it['shared_cost'], 2)
        it['cost_each'] = round(it['cost_total'] / it['qty_used'], 2) if it['qty_used'] else it['own_cost_each']
        it['cost_total_q'] = round(it['cost_total'] / fx, 2)          # in the quote's currency
        it['cost_each_q'] = round(it['cost_each'] / fx, 2)

    target = number(target_total)
    budget = None
    if mode == 'target' and target is not None:
        _share_target(items, target, round_to)
        budget = round(target / (1 + default_profit / 100), 2) if default_profit > -100 else None
    else:
        for it in items:
            if it['manual_price']:
                it['price'] = it['price_each']
            else:
                it['price'] = _round_to(it['cost_each_q'] * (1 + it['profit_used'] / 100), round_to)

    for it in items:
        it['price'] = round(it['price'], 2)
        it['amount'] = round(it['price'] * it['qty_used'], 2)
        it['profit'] = round(it['amount'] - it['cost_total_q'], 2)
        it['profit_on_cost'] = _percent(it['profit'], it['cost_total_q'])
        it['margin_of_price'] = _percent(it['profit'], it['amount'])

    cost_base = round(sum(it['cost_total'] for it in items), 2)
    total_cost = round(sum(it['cost_total_q'] for it in items), 2)
    total_price = round(sum(it['amount'] for it in items), 2)
    profit = round(total_price - total_cost, 2)
    totals = {'cost': total_cost, 'cost_base': cost_base, 'shared': round(sum(s['amount'] for s in shared), 2),
              'price': total_price, 'profit': profit,
              'profit_on_cost': _percent(profit, total_cost), 'margin_of_price': _percent(profit, total_price)}
    if mode == 'target' and target is not None:
        totals.update({'target': round(target, 2), 'budget': budget,
                       'left': round(budget - total_cost, 2) if budget is not None else None,
                       'off_target': round(total_price - target, 2)})
    return {'mode': mode, 'profit_percent': default_profit, 'round_to': round_to, 'items': items, 'shared': shared,
            'totals': totals, 'currency': currency, 'cost_currency': cost_currency, 'exchange_rate': rate,
            'needs_rate': currency != cost_currency and not rate}


def _share_target(items: List[Dict], target: float, round_to: int):
    """Typed prices stay; the rest of the target is shared over the other items by cost
    (by quantity when nothing is costed yet). Rounding leftovers go to the largest single item."""
    fixed = sum(it['price_each'] * it['qty_used'] for it in items if it['manual_price'])
    free = [it for it in items if not it['manual_price']]
    rest = target - fixed
    weights = [it['cost_total_q'] for it in free]
    if not any(weights):
        weights = [it['qty_used'] for it in free]
    total_weight = sum(weights)
    for it in items:
        if it['manual_price']:
            it['price'] = it['price_each']
    for it, w in zip(free, weights):
        share = rest * w / total_weight if total_weight else 0
        it['price'] = _round_to(share / it['qty_used'], round_to) if it['qty_used'] else 0
    leftover = round(target - sum(it['price'] * it['qty_used'] for it in items), 2)
    singles = [it for it in free if it['qty_used'] == 1]
    if leftover and singles:
        biggest = max(singles, key=lambda it: it['price'])
        biggest['price'] = round(biggest['price'] + leftover, 2)


def _percent(part: float, whole: float) -> Optional[float]:
    return round(part / whole * 100, 1) if whole else None


def quote_rows(result: Dict) -> List[Dict]:
    """The quote's line items: what the customer sees (never the costs)."""
    rows = []
    for it in result['items']:
        description = it.get('name') or ''
        if it.get('description'):
            description = f"{description}\n{it['description']}" if description else it['description']
        rows.append({'description': description, 'qty': it['qty_used'], 'unit': it.get('unit') or '',
                     'price': it['price'], 'amount': it['amount']})
    return rows


# ---------------------------------------------------------------- Stored costings

class CostingError(ValueError):
    pass


def settings_from(source: Dict) -> Dict:
    """Mode, profit, target, rounding and currency from a form or a stored row."""
    mode = source.get('mode') if source.get('mode') in MODES else 'build'
    round_to = int(number(source.get('round_to'), 0) or 0)
    currency = (source.get('currency') or 'INR').upper()[:3]
    return {'mode': mode, 'profit_percent': number(source.get('profit_percent'), DEFAULT_PROFIT),
            'target_total': number(source.get('target_total')), 'round_to': round_to if round_to in ROUNDING else 0,
            'currency': currency}


def _sheet(value) -> Dict:
    if isinstance(value, str):
        import json
        try:
            return json.loads(value)
        except ValueError:
            return {'items': []}
    return value or {'items': []}


def run(sheet: Dict, settings: Dict) -> Dict:
    return compute(sheet, settings['mode'], settings['profit_percent'], settings['target_total'], settings['round_to'],
                   settings['currency'])


def result_of(row: Dict) -> Dict:
    return run(clean_sheet(_sheet(row.get('sheet'))), settings_from(row))


def get(costing_id, org_id) -> Optional[Dict]:
    from db import db, DatabaseError
    try:
        row = db.execute_proc_single('sp_get_costing', (costing_id, org_id))
    except DatabaseError:
        return None
    if row:
        row['sheet'] = clean_sheet(_sheet(row.get('sheet')))
    return row


def list_for(org_id, project_id) -> List[Dict]:
    from db import db
    rows = db.execute_proc('sp_list_costings', (org_id, project_id)) or []
    for r in rows:
        r['profit'] = number(r.get('total_price'), 0) - number(r.get('total_cost'), 0)
        r['profit_on_cost'] = _percent(r['profit'], number(r.get('total_cost'), 0))
    return rows


def save(org_id, costing_id, title, sheet: Dict, settings: Dict, notes='', cost_currency: Optional[str] = None) -> Dict:
    """Store the sheet; total_cost is kept in the quote's currency, so it compares with total_price."""
    from db import db
    sheet = clean_sheet(sheet)
    if cost_currency:
        sheet['cost_currency'] = cost_currency
    result = run(sheet, settings)
    db.execute_proc('sp_update_costing', (
        costing_id, org_id, (title or 'Costing').strip()[:200], settings['mode'], settings['profit_percent'],
        settings['target_total'], settings['round_to'], settings['currency'], sheet,
        result['totals']['cost'], result['totals']['price'], notes), fetch=False)
    return result


def create(org_id, project_id, title, user_id=None, copy_of: Optional[Dict] = None, currency='INR') -> Dict:
    """A new costing for the project: empty, or a copy of another (a new version to rework)."""
    from db import db
    sheet = copy_of['sheet'] if copy_of else {'items': [], 'cost_currency': currency}
    settings = settings_from(copy_of) if copy_of else {'mode': 'build', 'profit_percent': DEFAULT_PROFIT,
                                                       'target_total': None, 'round_to': 0, 'currency': currency}
    result = run(clean_sheet(sheet), settings)
    return db.execute_proc_single('sp_create_costing', (
        org_id, project_id, (title or 'Costing').strip()[:200], settings['mode'], settings['profit_percent'],
        settings['target_total'], settings['round_to'], settings['currency'], sheet,
        result['totals']['cost'], result['totals']['price'], (copy_of or {}).get('notes') or '', user_id))


# ---------------------------------------------------------------- The quote made from a costing

def _item_fields(fields: List[Dict]) -> Dict[str, Dict]:
    """The quote template's item table, by field name (with synonyms: price/rate, unit/per ...)."""
    from document_service import _canonical
    from invoice_service import is_breakup_section
    sections: Dict[str, List[Dict]] = {}
    for f in fields:
        if (f.get('section_type') or 'normal') != 'line_item':
            continue
        if is_breakup_section(f.get('section_name') or '', f.get('section_display_name') or ''):
            continue
        sections.setdefault(f['section_id'], []).append(f)
    if not sections:
        return {}
    return {_canonical(f.get('field_name')): f for f in next(iter(sections.values()))}


def _write_items(invoice_id, item_fields: Dict[str, Dict], rows: List[Dict]):
    from db import db
    from document_service import _canonical
    for n, row in enumerate(rows, start=1):
        for key, value in row.items():
            f = item_fields.get(_canonical(key))
            if not f or f.get('calculation_formula') or value in (None, ''):
                continue
            is_number = f.get('data_type') == 'number'
            db.execute_proc('sp_save_invoice_value', (
                invoice_id, f['field_id'], None if is_number else str(value), number(value) if is_number else None,
                None, None, n), fetch=False)


def make_quote(org_id, row: Dict, template_id) -> str:
    """A draft quotation from the costing's items and selling prices. Returns its id."""
    import json
    from datetime import date
    from access import get_org_customer, get_org_invoice
    from db import db, DatabaseError
    from document_service import allocate_number, form_defaults, get_org_profile
    from invoice_service import get_template_fields, recalculate_invoice
    import activity
    import projects

    result = result_of(row)
    if not result['items']:
        raise CostingError('Add the items to quote first')
    if result['needs_rate']:
        raise CostingError(f"Enter the exchange rate to turn the costs into {result['currency']}")
    item_fields = _item_fields(get_template_fields(template_id))
    if not item_fields:
        raise CostingError("That template has no item table for the costing's items")
    org, profile = get_org_profile(org_id)
    customer, _ = get_org_customer(row['customer_id'], org_id)
    currency = settings_from(row)['currency']
    new_id = db.execute_proc('sp_create_invoice', (org_id, row['customer_id'], template_id, None, None))[0]['invoice_id']
    try:
        _write_items(new_id, item_fields, quote_rows(result))
        db.execute_proc('sp_update_invoice_dates', (new_id, date.today().isoformat(), None), fetch=False)
        quote_number, fy = allocate_number(org_id, 'quote', profile, date.today())
        db.execute_proc('sp_init_document', (new_id, org_id, 'quote', quote_number, fy, None), fetch=False)
        defaults = form_defaults('quote', profile, org, customer,
                                 export=currency != (profile.get('default_currency') or 'INR'))
        details = {**defaults['details'], 'subject': row['title'], 'currency': currency}
        db.execute_proc('sp_update_document_settings', (
            new_id, org_id, quote_number, defaults['tax_mode'], defaults['tax_rate'], None, defaults['advance_basis'],
            json.dumps(details)), fetch=False)
        header, values = get_org_invoice(new_id, org_id)
        recalculate_invoice(new_id, header, values)
        projects.set_project(new_id, org_id, row['project_id'])
        db.execute_proc('sp_set_costing_quote', (row['costing_id'], org_id, new_id), fetch=False)
    except Exception:
        try:
            db.execute_proc('sp_delete_invoice', (new_id,), fetch=False)
        except DatabaseError:
            pass
        raise
    header, _ = get_org_invoice(new_id, org_id)
    activity.document_event('document_created', header, 'made from a costing', project_id=row['project_id'])
    return new_id


def update_quote(org_id, row: Dict) -> str:
    """Put the costing's items and prices on its quote, while that's still a draft."""
    from access import get_org_invoice
    from db import db
    from invoice_service import get_template_fields, recalculate_invoice
    header, _ = get_org_invoice(row['quote_id'], org_id) if row.get('quote_id') else (None, [])
    if not header:
        raise CostingError('This costing has no quote yet')
    if (header.get('status') or 'draft') != 'draft':
        raise CostingError('That quote has been sent, so it stays as it is. Make a new version and a new quote.')
    item_fields = _item_fields(get_template_fields(header['template_id'], header.get('template_version')))
    if not item_fields:
        raise CostingError("The quote's template has no item table")
    result = result_of(row)
    if result['needs_rate']:
        raise CostingError(f"Enter the exchange rate to turn the costs into {result['currency']}")
    db.execute_proc('sp_delete_invoice_values_by_fields',
                    (header['invoice_id'], [f['field_id'] for f in item_fields.values()]), fetch=False)
    _write_items(header['invoice_id'], item_fields, quote_rows(result))
    header, values = get_org_invoice(header['invoice_id'], org_id)
    recalculate_invoice(header['invoice_id'], header, values)
    return header['invoice_id']


# ---------------------------------------------------------------- Copying from earlier costings

def library(org_id, search='', limit=50) -> List[Dict]:
    """The org's costings, newest first, for picking one to copy items from."""
    from db import db
    return db.execute_proc('sp_list_org_costings', (org_id, search or '', limit)) or []


def items_to_copy(row: Dict) -> List[Dict]:
    """A costing's items (with their cost lines and worked-out cost) to add to another sheet. They get new
    keys there; shared costs stay behind, since they're spread over that sheet's own items."""
    result = result_of(row)
    keep = ('name', 'description', 'qty', 'unit', 'cost_each', 'profit_percent', 'price_each', 'lines')
    out = []
    for raw, it in zip(row['sheet']['items'], result['items']):
        item = {k: raw.get(k) for k in keep}
        item['cost_each'] = raw.get('cost_each') if not raw.get('lines') else None
        item['own_cost_each'] = it['own_cost_each']
        out.append(item)
    return out


# ---------------------------------------------------------------- The rates list

RATE_FIELDS = ('description', 'make', 'unit', 'unit_cost', 'markup', 'notes')
MAX_RATES = 1000


def clean_rates(raw: Any) -> List[Dict]:
    """Rates as typed on the rates page: blank rows dropped, one per description and make (the last wins)."""
    rows: Dict[tuple, Dict] = {}
    for r in (raw if isinstance(raw, list) else [])[:MAX_RATES]:
        if not isinstance(r, dict):
            continue
        row = {'description': _text(r.get('description'), 300), 'make': _text(r.get('make'), 120),
               'unit': _text(r.get('unit'), 20), 'unit_cost': number(r.get('unit_cost')),
               'markup': number(r.get('markup')), 'notes': _text(r.get('notes'), 300)}
        if row['description']:
            rows[(row['description'].lower(), row['make'].lower())] = row
    return sorted(rows.values(), key=lambda r: (r['description'].lower(), r['make'].lower()))


def rates(org_id) -> List[Dict]:
    from db import db
    return [{k: (number(r[k]) if k in ('unit_cost', 'markup') else r[k]) for k in RATE_FIELDS}
            for r in db.execute_proc('sp_list_cost_rates', (org_id,)) or []]


def save_rates(org_id, raw) -> List[Dict]:
    from db import db
    rows = clean_rates(raw)
    db.execute_proc('sp_replace_cost_rates', (org_id, rows), fetch=False)
    return rows


def rate_suggestions(org_id, known: List[Dict], limit=40) -> List[Dict]:
    """Cost lines from the org's costings that aren't in the rates list yet: the most used first,
    each with the rate it had most recently."""
    from db import db
    have = {(r['description'].lower(), (r.get('make') or '').lower()) for r in known}
    seen: Dict[tuple, Dict] = {}
    for row in db.execute_proc('sp_list_costing_sheets', (org_id, 200)) or []:      # newest first
        sheet = clean_sheet(_sheet(row.get('sheet')))
        for line in [l for it in sheet['items'] for l in it['lines']] + [s for s in sheet['shared'] if s['kind'] == 'amount']:
            key = (line['description'].lower(), (line.get('make') or '').lower())
            if not line['description'] or line.get('unit_cost') is None or key in have:
                continue
            if key in seen:
                seen[key]['used'] += 1
            else:
                seen[key] = {'description': line['description'], 'make': line.get('make') or '',
                             'unit': line.get('unit') or '', 'unit_cost': line['unit_cost'],
                             'markup': line.get('markup'), 'notes': '', 'used': 1}
    return sorted(seen.values(), key=lambda r: (-r['used'], r['description'].lower()))[:limit]


def purchase_lines(row: Dict, picks: List[str]) -> List[Dict]:
    """A costing's cost lines to buy on a purchase order: picks are "<item key>:<line number>" (from 0). Each becomes
    [{description (with its make), qty (the line's for one item, times the items), unit, rate (its unit cost)}], in
    the costing's order; a pick that isn't there is left out."""
    wanted = set(picks or [])
    out = []
    for item in (row.get('sheet') or {}).get('items') or []:
        times = number(item.get('qty')) or 1
        for n, line in enumerate(item.get('lines') or []):
            if f"{item.get('key')}:{n}" not in wanted:
                continue
            text = (line.get('description') or item.get('name') or 'Item').strip()
            make = (line.get('make') or '').strip()
            out.append({'description': f'{text} ({make})' if make else text, 'qty': (number(line.get('qty')) or 1) * times,
                        'unit': (line.get('unit') or '').strip(), 'rate': number(line.get('unit_cost')) or 0})
    return out
