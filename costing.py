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
"""

import math
import re
from typing import Any, Dict, List, Optional

MODES = {'build': 'Build up from costs', 'target': 'Work back from a total'}
ROUNDING = (0, 1, 10, 100, 1000)
DEFAULT_PROFIT = 15.0
MAX_ITEMS, MAX_LINES = 200, 200


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


def clean_sheet(raw: Any) -> Dict:
    """The sheet as stored: known keys only, numbers as numbers, blank rows dropped."""
    items = []
    for item in (raw or {}).get('items', [])[:MAX_ITEMS] if isinstance(raw, dict) else []:
        if not isinstance(item, dict):
            continue
        lines = []
        for line in (item.get('lines') or [])[:MAX_LINES]:
            if not isinstance(line, dict):
                continue
            row = {'description': _text(line.get('description'), 300), 'make': _text(line.get('make'), 120),
                   'qty': number(line.get('qty')), 'unit': _text(line.get('unit'), 20),
                   'unit_cost': number(line.get('unit_cost')), 'markup': number(line.get('markup'))}
            if row['description'] or row['unit_cost'] is not None:
                lines.append(row)
        row = {'name': _text(item.get('name'), 300), 'description': _text(item.get('description'), 2000),
               'qty': number(item.get('qty')), 'unit': _text(item.get('unit'), 20),
               'cost_each': number(item.get('cost_each')), 'profit_percent': number(item.get('profit_percent')),
               'price_each': number(item.get('price_each')), 'lines': lines}
        if row['name'] or lines or row['cost_each'] is not None or row['price_each'] is not None:
            items.append(row)
    return {'items': items}


def _round_to(value: float, step: int) -> float:
    if not step:
        return round(value, 2)
    return math.floor(value / step + 0.5) * step                         # half up: 1,23,450 -> 1,23,500


def _qty(value) -> float:
    q = number(value)
    return 1.0 if q is None else q


def compute(sheet: Dict, mode: str = 'build', profit_percent=DEFAULT_PROFIT, target_total=None,
            round_to: int = 0) -> Dict:
    """Every number on the sheet: per line, per item and in total."""
    mode = mode if mode in MODES else 'build'
    default_profit = number(profit_percent, DEFAULT_PROFIT)
    round_to = round_to if round_to in ROUNDING else 0
    items = []
    for item in sheet.get('items', []):
        lines = []
        for line in item.get('lines') or []:
            each = (line.get('unit_cost') or 0) * (1 + (line.get('markup') or 0) / 100)
            lines.append({**line, 'cost': round(_qty(line.get('qty')) * each, 2)})
        cost_each = sum(l['cost'] for l in lines) if lines else (item.get('cost_each') or 0)
        qty = _qty(item.get('qty'))
        own_profit = item.get('profit_percent')
        items.append({**item, 'lines': lines, 'qty_used': qty, 'cost_each': round(cost_each, 2),
                      'cost_total': round(cost_each * qty, 2), 'built_from_lines': bool(lines),
                      'profit_used': default_profit if own_profit is None else own_profit,
                      'manual_price': item.get('price_each') is not None})

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
                it['price'] = _round_to(it['cost_each'] * (1 + it['profit_used'] / 100), round_to)

    for it in items:
        it['price'] = round(it['price'], 2)
        it['amount'] = round(it['price'] * it['qty_used'], 2)
        it['profit'] = round(it['amount'] - it['cost_total'], 2)
        it['profit_on_cost'] = _percent(it['profit'], it['cost_total'])
        it['margin_of_price'] = _percent(it['profit'], it['amount'])

    total_cost = round(sum(it['cost_total'] for it in items), 2)
    total_price = round(sum(it['amount'] for it in items), 2)
    profit = round(total_price - total_cost, 2)
    totals = {'cost': total_cost, 'price': total_price, 'profit': profit,
              'profit_on_cost': _percent(profit, total_cost), 'margin_of_price': _percent(profit, total_price)}
    if mode == 'target' and target is not None:
        totals.update({'target': round(target, 2), 'budget': budget,
                       'left': round(budget - total_cost, 2) if budget is not None else None,
                       'off_target': round(total_price - target, 2)})
    return {'mode': mode, 'profit_percent': default_profit, 'round_to': round_to, 'items': items, 'totals': totals}


def _share_target(items: List[Dict], target: float, round_to: int):
    """Typed prices stay; the rest of the target is shared over the other items by cost
    (by quantity when nothing is costed yet). Rounding leftovers go to the largest single item."""
    fixed = sum(it['price_each'] * it['qty_used'] for it in items if it['manual_price'])
    free = [it for it in items if not it['manual_price']]
    rest = target - fixed
    weights = [it['cost_total'] for it in free]
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


def result_of(row: Dict) -> Dict:
    s = settings_from(row)
    return compute(clean_sheet(_sheet(row.get('sheet'))), s['mode'], s['profit_percent'], s['target_total'], s['round_to'])


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


def save(org_id, costing_id, title, sheet: Dict, settings: Dict, notes='') -> Dict:
    from db import db
    sheet = clean_sheet(sheet)
    result = compute(sheet, settings['mode'], settings['profit_percent'], settings['target_total'], settings['round_to'])
    db.execute_proc('sp_update_costing', (
        costing_id, org_id, (title or 'Costing').strip()[:200], settings['mode'], settings['profit_percent'],
        settings['target_total'], settings['round_to'], settings['currency'], sheet,
        result['totals']['cost'], result['totals']['price'], notes), fetch=False)
    return result


def create(org_id, project_id, title, user_id=None, copy_of: Optional[Dict] = None, currency='INR') -> Dict:
    """A new costing for the project: empty, or a copy of another (a new version to rework)."""
    from db import db
    sheet = copy_of['sheet'] if copy_of else {'items': []}
    settings = settings_from(copy_of) if copy_of else {'mode': 'build', 'profit_percent': DEFAULT_PROFIT,
                                                       'target_total': None, 'round_to': 0, 'currency': currency}
    result = compute(sheet, settings['mode'], settings['profit_percent'], settings['target_total'], settings['round_to'])
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
    db.execute_proc('sp_delete_invoice_values_by_fields',
                    (header['invoice_id'], [f['field_id'] for f in item_fields.values()]), fetch=False)
    _write_items(header['invoice_id'], item_fields, quote_rows(result_of(row)))
    header, values = get_org_invoice(header['invoice_id'], org_id)
    recalculate_invoice(header['invoice_id'], header, values)
    return header['invoice_id']
