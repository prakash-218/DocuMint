"""
Discounts on a document, on its lines and on the whole of it, each an amount ("5000") or a percent ("10%").

A line's discount comes off that line's amount (the column calculations.amount_field picks), before any total adds the
lines up, so the printed amount, the totals and the GST summary all see the line after its discount. The document's
discount comes off its total before tax (the template's total field), so GST is worked out on what's left, and so is a
proforma's advance.

They're kept in the document's details as typed, keyed by line-item section and line:

    details['discounts'] = {'document': '10%', 'lines': {'items': {'3': '5000'}}}

A copy of the document (a revision, a conversion) takes them along; converting can instead spread them into the line
prices (spread()), so the new document shows net prices and no discount.
"""

import re
from typing import Dict, Iterable, List, Optional, Tuple

from calculations import normalize_name

Spec = Tuple[str, float]                    # ('percent', 10.0) or ('amount', 5000.0)
PRICE_NAMES = ('price', 'rate', 'unit_price', 'unit_rate', 'price_per_unit', 'unit_cost', 'cost')
QTY_NAMES = ('qty', 'quantity', 'nos', 'no_of_units')


class DiscountError(ValueError):
    pass


# An amount ("5000", "5,000.50", "₹5000", "Rs. 5000") or a percent ("10%", "12.5 %")
_TYPED = re.compile(r'(?:rs\.?|inr|usd|eur|gbp|aud|cad|sgd|aed|[₹$€£])?\s*(\d[\d,]*(?:\.\d+)?|\.\d+)\s*(%?)', re.IGNORECASE)


def parse(typed) -> Optional[Spec]:
    """'10%' -> ('percent', 10.0); '5,000' or '₹5000' -> ('amount', 5000.0); '' or 0 -> None. Raises DiscountError for
    anything else, or a percent over 100."""
    raw = str(typed or '').strip()
    if not raw:
        return None
    found = _TYPED.fullmatch(raw)
    if not found:
        raise DiscountError(f'"{raw}" isn’t a discount: type an amount like 5000 or a percent like 10%')
    value, percent = float(found.group(1).replace(',', '')), found.group(2) == '%'
    if percent and value > 100:
        raise DiscountError(f'"{raw}" is more than 100%')
    if not value:
        return None
    return ('percent' if percent else 'amount', value)


def off(spec: Optional[Spec], base: float) -> float:
    """What the discount takes off base (never more than base, never below nothing)."""
    if not spec or base <= 0:
        return 0.0
    kind, value = spec
    taken = base * value / 100 if kind == 'percent' else value
    return round(min(max(taken, 0.0), base), 2)


def text(spec: Optional[Spec]) -> str:
    """As it's kept and typed: '10%', '5000'."""
    if not spec:
        return ''
    kind, value = spec
    return f'{value:g}%' if kind == 'percent' else f'{value:g}'


def label(spec: Optional[Spec], currency: str = 'INR') -> str:
    """As it's printed: '10%', '₹5,000.00'."""
    from money import format_money
    if not spec:
        return ''
    kind, value = spec
    return f'{value:g}%' if kind == 'percent' else format_money(value, currency)


# ---------------------------------------------------------------- A document's discounts

def of(header: Dict) -> Dict:
    """{'document': spec or None, 'lines': {section: {ordinal: spec}}} from a document's details."""
    from documents import load_json
    kept = load_json(header.get('details')).get('discounts') or {}
    lines: Dict[str, Dict[int, Spec]] = {}
    for section, rows in (kept.get('lines') or {}).items():
        for ordinal, typed in (rows or {}).items():
            try:
                spec = parse(typed)
            except DiscountError:
                spec = None
            if spec:
                lines.setdefault(normalize_name(section), {})[int(ordinal)] = spec
    try:
        document = parse(kept.get('document'))
    except DiscountError:
        document = None
    return {'document': document, 'lines': lines}


def for_engine(header: Dict) -> Dict[Tuple[str, int], Spec]:
    """The line discounts as calculations.calculate takes them: {(section, ordinal): spec}."""
    return {(section, ordinal): spec for section, rows in of(header)['lines'].items() for ordinal, spec in rows.items()}


def any_of(header: Dict) -> bool:
    found = of(header)
    return bool(found['document'] or found['lines'])


def kept(document: Optional[Spec], lines: Dict[str, Dict[int, Spec]]) -> Optional[Dict]:
    """What goes in details['discounts'] (None when there are none)."""
    rows = {s: {str(o): text(spec) for o, spec in sorted(r.items())} for s, r in lines.items() if r}
    if not document and not rows:
        return None
    return {'document': text(document) or None, 'lines': rows}


def from_form(form, section_names: Dict[str, str]) -> Optional[Dict]:
    """The discounts the editor posted: 'discount' for the document, 'line_discount_<section id>_<row>' for a line.
    section_names: {section id: section name}. Raises DiscountError for one that isn't an amount or a percent."""
    document = parse(form.get('discount'))
    lines: Dict[str, Dict[int, Spec]] = {}
    for key in form.keys():
        if not key.startswith('line_discount_'):
            continue
        section_id, _, row = key[len('line_discount_'):].rpartition('_')
        if section_id not in section_names or not row.isdigit():
            continue
        try:
            spec = parse(form.get(key))
        except DiscountError as e:
            raise DiscountError(f'Line {row}: {e}') from None
        if spec:
            lines.setdefault(normalize_name(section_names[section_id]), {})[int(row)] = spec
    return kept(document, lines)


def remap(discounts: Optional[Dict], sections: Dict[str, str]) -> Optional[Dict]:
    """A copy's discounts, its line sections renamed {source section: target section} (another template's names)."""
    if not discounts:
        return discounts
    lines = {}
    for section, rows in (discounts.get('lines') or {}).items():
        target = sections.get(normalize_name(section), normalize_name(section))
        lines.setdefault(target, {}).update(rows or {})
    return {**discounts, 'lines': lines}


def describe(header: Dict, currency: str = 'INR') -> str:
    """'₹53,000.00 off the total; a discount on 2 lines', for the choice when converting. '' without any."""
    found = of(header)
    parts = []
    if found['document']:
        parts.append(f"{label(found['document'], currency)} off the total")
    count = sum(len(rows) for rows in found['lines'].values())
    if count:
        parts.append(f"a discount on {count} line{'s' if count != 1 else ''}")
    return '; '.join(parts)


# ---------------------------------------------------------------- Spreading them into the prices

def _price_field(amount: Dict, fields: List[Dict]) -> Optional[Dict]:
    """The line's unit price: the field the amount formula multiplies by the quantity (this.price * this.qty)."""
    refs = [normalize_name(r) for r in re.findall(r'this\.(\w+)', amount.get('calculation_formula') or '', flags=re.I)]
    by_name = {normalize_name(f.get('field_name')): f for f in fields if not f.get('calculation_formula')}
    named = [by_name[r] for r in refs if r in by_name]
    priced = [f for f in named if normalize_name(f.get('field_name')) in PRICE_NAMES]
    if priced:
        return priced[0]
    others = [f for f in named if normalize_name(f.get('field_name')) not in QTY_NAMES]
    return others[0] if len(others) == 1 else None


def spread(header: Dict, fields: List[Dict], values: List[Dict]) -> Tuple[List[Dict], float]:
    """The document's values with its discounts taken into the line prices, for a copy that shows net prices and no
    discount: each line's price comes down by its own discount and its share of the document's. A rounding difference
    is put on a line of quantity 1 when there is one; what's left of it (in money) comes back, 0.0 when none.
    Raises DiscountError when the lines have no price to change."""
    from calculations import amount_field, calculate
    from invoice_service import build_sections, invoice_summary
    found = of(header)
    if not found['document'] and not found['lines']:
        return values, 0.0
    summary = invoice_summary(header, build_sections(header, values), [])
    target = summary['taxable']                             # what the copy's total before tax must come to
    gross = calculate(fields, values)                       # every line's amount before its discount
    net = calculate(fields, values, for_engine(header))     # and after it

    by_section: Dict[str, List[Dict]] = {}
    for f in fields:
        if (f.get('section_type') or 'normal') == 'line_item':
            by_section.setdefault(normalize_name(f.get('section_name')), []).append(f)
    from invoice_service import is_breakup_section
    plans = []
    for section, sfields in by_section.items():
        if is_breakup_section(section):
            continue
        amount_id = amount_field(sfields)
        amount = next((f for f in sfields if f['field_id'] == amount_id), None)
        price = _price_field(amount, sfields) if amount else None
        rows = sorted({v.get('value_ordinal') or 0 for v in values if v.get('field_id') in {f['field_id'] for f in sfields}})
        if any(gross.get((amount_id, o)) for o in rows) and not price:
            raise DiscountError("These lines have no price column to take the discount into. Keep it as a discount instead.")
        if price:
            qty = next((f for f in sfields if normalize_name(f.get('field_name')) in QTY_NAMES), None)
            plans.append((amount_id, price, qty, rows))

    lines_net = sum(net.get((a, o), 0.0) for a, _, _, rows in plans for o in rows)
    share = (summary['discount'] or {}).get('amount') or 0.0
    out = [dict(v) for v in values]
    cell = {(v.get('field_id'), v.get('value_ordinal') or 0): v for v in out}
    for amount_id, price, qty, rows in plans:
        for o in rows:
            before, after = gross.get((amount_id, o), 0.0), net.get((amount_id, o), 0.0)
            if not before:
                continue
            after -= share * after / lines_net if lines_net else 0.0
            v = cell.get((price['field_id'], o))
            if v is not None and v.get('val_number') is not None:
                v['val_number'] = round(float(v['val_number']) * after / before, 2)

    # Rounding: the prices are to the paisa, so the total can be a few paise out; a line of quantity 1 takes it
    plain = {**header, 'details': {k: val for k, val in _details(header).items() if k != 'discounts'}}
    left = round(target - invoice_summary(plain, build_sections(plain, out), [])['taxable'], 2)
    if abs(left) >= 0.005:
        for amount_id, price, qty, rows in plans:
            one = next((o for o in rows if qty and float((cell.get((qty['field_id'], o)) or {}).get('val_number') or 0) == 1
                        and cell.get((price['field_id'], o))), None)
            if one is not None:
                v = cell[(price['field_id'], one)]
                v['val_number'] = round(float(v['val_number']) + left, 2)
                left = 0.0
                break
    return out, left


# ---------------------------------------------------------------- Part of a document: every price at a share of it

DESCRIPTION_NAMES = ('description', 'item', 'item_details', 'item_description', 'particulars', 'description_of_goods')


def scale(header: Dict, fields: List[Dict], values: List[Dict], share: float, label: str = '') -> Tuple[List[Dict], float]:
    """The document's values for a part of it (a tax invoice for 60% of a quotation): its discounts taken into the
    prices first (spread), then each line's price at that share, and its description followed by "(label)". A
    rounding difference goes on a line of quantity 1, as spread does; what's left of it comes back, 0.0 when none.
    Raises DiscountError when the lines have no price, or when the total holds more than its lines (charges typed
    beside them), which a part would bill again."""
    from calculations import amount_field
    from invoice_service import build_sections, invoice_summary, is_breakup_section
    values, _ = spread(header, fields, values)
    plain = {**header, 'details': {k: v for k, v in _details(header).items() if k != 'discounts'}}
    target = round(invoice_summary(plain, build_sections(plain, values), [])['taxable'] * share, 2)
    by_section: Dict[str, List[Dict]] = {}
    for f in fields:
        if (f.get('section_type') or 'normal') == 'line_item':
            by_section.setdefault(normalize_name(f.get('section_name')), []).append(f)
    out = [dict(v) for v in values]
    cell = {(v.get('field_id'), v.get('value_ordinal') or 0): v for v in out}
    plans = []
    for section, sfields in by_section.items():
        if is_breakup_section(section):
            continue
        amount = next((f for f in sfields if f['field_id'] == amount_field(sfields)), None)
        price = _price_field(amount, sfields) if amount else None
        ids = {f['field_id'] for f in sfields}
        rows = sorted({v.get('value_ordinal') or 0 for v in out if v.get('field_id') in ids})
        if not price:
            if any((cell.get((amount['field_id'], o)) or {}).get('val_number') for o in rows) if amount else False:
                raise DiscountError("These lines have no price column to invoice part of.")
            continue
        qty = next((f for f in sfields if normalize_name(f.get('field_name')) in QTY_NAMES), None)
        text = next((f for f in sfields if normalize_name(f.get('field_name')) in DESCRIPTION_NAMES), None)
        plans.append((price, qty, rows))
        for o in rows:
            v = cell.get((price['field_id'], o))
            if v is not None and v.get('val_number') is not None:
                v['val_number'] = round(float(v['val_number']) * share, 2)
            t = cell.get((text['field_id'], o)) if text else None
            if label and t is not None and (t.get('val_string') or '').strip():
                t['val_string'] = f"{t['val_string'].rstrip()} ({label})"

    left = round(target - invoice_summary(plain, build_sections(plain, out), [])['taxable'], 2)
    if abs(left) > 0.01 * (sum(len(rows) for _, _, rows in plans) + 1):
        raise DiscountError("This document's total holds more than its lines, so part of it can't be worked out from them. "
                            "Invoice it in full instead.")
    if abs(left) >= 0.005:
        for price, qty, rows in plans:
            one = next((o for o in rows if qty and float((cell.get((qty['field_id'], o)) or {}).get('val_number') or 0) == 1
                        and cell.get((price['field_id'], o))), None)
            if one is not None:
                v = cell[(price['field_id'], one)]
                v['val_number'] = round(float(v['val_number']) + left, 2)
                left = 0.0
                break
    return out, left


def _details(header: Dict) -> Dict:
    from documents import load_json
    return load_json(header.get('details'))


def amounts_by_line(header: Dict, fields: Iterable[Dict]) -> Dict[Tuple[str, int], Spec]:
    """{(amount field id, ordinal): spec} for the document's discounted lines (to mark them where they're shown)."""
    from calculations import amount_field
    by_section: Dict[str, List[Dict]] = {}
    for f in fields:
        if (f.get('section_type') or 'normal') == 'line_item':
            by_section.setdefault(normalize_name(f.get('section_name')), []).append(f)
    out = {}
    for section, rows in of(header)['lines'].items():
        amount_id = amount_field(by_section.get(section, []))
        if amount_id:
            for ordinal, spec in rows.items():
                out[(amount_id, ordinal)] = spec
    return out
