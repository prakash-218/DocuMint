import pytest

from calculations import calculate, calculate_invoice_fields, validate_formula


def field(fid, section, name, formula=None, section_type='normal'):
    return {
        'field_id': fid, 'field_name': name, 'field_display_name': name.replace('_', ' ').title(),
        'calculation_formula': formula, 'section_name': section,
        'section_display_name': section.title(), 'section_type': section_type, 'data_type': 'number',
    }


def value(f, number, ordinal=0):
    return {**f, 'value_ordinal': ordinal, 'val_number': number}


# The "Standard Invoice" layout from data_dump.sql: note the normal section
# called "total" that also contains a field called "total".
NAME = field('name', 'items', 'name', section_type='line_item')
QTY = field('qty', 'items', 'qty', section_type='line_item')
PRICE = field('price', 'items', 'price', section_type='line_item')
LINE_TOTAL = field('line_total', 'items', 'total', 'this.price * this.qty', section_type='line_item')
TOTAL = field('total', 'total', 'total', 'SUM(items.total)')
TAX = field('tax', 'total', 'tax', 'total * 0.1')
GRAND = field('grand', 'total', 'grand_total', 'total + tax')
STANDARD = [NAME, QTY, PRICE, LINE_TOTAL, TOTAL, TAX, GRAND]


def rows(*items):
    values = []
    for ordinal, (qty, price) in enumerate(items, start=1):
        values += [value(QTY, qty, ordinal), value(PRICE, price, ordinal)]
    return values


def test_standard_invoice():
    result = calculate(STANDARD, rows((2, 10), (3, 5)))
    assert result[('line_total', 1)] == 20
    assert result[('line_total', 2)] == 15
    assert result[('total', 0)] == 35
    assert result[('tax', 0)] == pytest.approx(3.5)
    assert result[('grand', 0)] == pytest.approx(38.5)


def test_formula_order_does_not_matter():
    # grand_total depends on fields listed after it
    result = calculate([GRAND, TAX, TOTAL, LINE_TOTAL, QTY, PRICE], rows((1, 100)))
    assert result[('grand', 0)] == pytest.approx(110)


def test_stale_stored_values_are_recomputed():
    values = rows((1, 10)) + [value(LINE_TOTAL, 999, 1), value(TOTAL, 999), value(GRAND, 999)]
    result = calculate(STANDARD, values)
    assert result[('total', 0)] == 10
    assert result[('grand', 0)] == pytest.approx(11)


def test_no_rows_gives_zero_totals():
    result = calculate(STANDARD, [])
    assert result[('total', 0)] == 0
    assert result[('grand', 0)] == 0
    assert not any(k[0] == 'line_total' for k in result)


def test_empty_cells_count_as_zero():
    result = calculate(STANDARD, [value(QTY, None, 1), value(PRICE, 4, 1)])
    assert result[('line_total', 1)] == 0


@pytest.mark.parametrize('formula,expected', [
    ('AVG(items.price)', 7.5),
    ('COUNT(items)', 2),
    ('COUNT(items.price)', 2),
    ('MIN(items.price)', 5),
    ('MAX(items.price)', 10),
    ('sum(items.total)', 35),          # function names are case-insensitive
    ('SUM("items.total")', 35),        # older quoted style
    ('GET("total.tax")', 3.5),
    ('items.total', 35),               # a line-item column on its own is its sum
    ('ROUND(total / 3, 2)', 11.67),
    ('ABS(0 - total)', 35),
    ('Total * 2', 70),                 # names are case-insensitive
])
def test_functions(formula, expected):
    probe = field('probe', 'summary', 'probe', formula)
    result = calculate(STANDARD + [probe], rows((2, 10), (3, 5)))
    assert result[('probe', 0)] == pytest.approx(expected)


@pytest.mark.parametrize('formula', [
    'unknown_field * 2',
    'nosuch.field',
    'total / 0',
    'this.qty',          # this. outside a line-item section
    'total +',
    '__import__("os")',
])
def test_bad_formulas_are_skipped(formula):
    probe = field('probe', 'summary', 'probe', formula)
    result = calculate(STANDARD + [probe], rows((1, 1)))
    assert ('probe', 0) not in result
    assert result[('total', 0)] == 1   # other formulas still work


def test_cycle_terminates():
    a = field('a', 'summary', 'a', 'b + 1')
    b = field('b', 'summary', 'b', 'a + 1')
    calculate([a, b], [])  # must not hang


def test_values_carry_metadata_without_fields():
    values = rows((2, 3)) + [value(LINE_TOTAL, None, 1), value(TOTAL, None)]
    result = calculate_invoice_fields(values)
    assert result[('line_total', 1)] == 6
    assert result[('total', 0)] == 6


def test_validate_formula():
    assert validate_formula('SUM(items.total) * 1.2', STANDARD, 'total') is None
    assert validate_formula('this.price * this.qty', STANDARD, 'items') is None
    assert validate_formula('subtotal / qty_sum', [field('s', 'x', 'subtotal'), field('q', 'x', 'qty_sum')], 'x') is None
    assert 'unknown' in validate_formula('SUM(items.nope)', STANDARD, 'total')
    assert validate_formula('total +', STANDARD, 'total') is not None
