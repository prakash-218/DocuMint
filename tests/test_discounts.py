"""Discounts: on a line (off its amount, before the totals) and on the whole document (off its total, before tax)."""

import json

import pytest
from werkzeug.datastructures import MultiDict

import discounts as D
from calculations import amount_field, calculate


def test_an_amount_or_a_percent():
    assert [D.parse(t) for t in ('10%', '12.5 %', '5,000', '₹5000', 'Rs. 5000', '', '0', None)] == [
        ('percent', 10.0), ('percent', 12.5), ('amount', 5000.0), ('amount', 5000.0), ('amount', 5000.0), None, None, None]
    for bad in ('10x', 'ten', '150%', '5-000'):
        with pytest.raises(D.DiscountError):
            D.parse(bad)
    assert D.off(('percent', 12.5), 1000) == 125 and D.off(('amount', 45000), 300000) == 45000
    assert D.off(('amount', 900), 100) == 100 and D.off(None, 100) == 0               # never more than there is
    assert (D.text(('percent', 10.0)), D.text(('amount', 5000.0)), D.label(('amount', 5000.0), 'INR')) == ('10%', '5000', '₹5,000.00')


FIELDS = [
    {'field_id': 'd', 'section_name': 'items', 'section_type': 'line_item', 'field_name': 'description'},
    {'field_id': 'p', 'section_name': 'items', 'section_type': 'line_item', 'field_name': 'price'},
    {'field_id': 'q', 'section_name': 'items', 'section_type': 'line_item', 'field_name': 'qty'},
    {'field_id': 'a', 'section_name': 'items', 'section_type': 'line_item', 'field_name': 'amount', 'calculation_formula': 'this.price * this.qty'},
    {'field_id': 't', 'section_name': 'totals', 'section_type': 'normal', 'field_name': 'total', 'calculation_formula': 'SUM(items.amount)'},
]
VALUES = [{'field_id': 'p', 'value_ordinal': 1, 'val_number': 1000}, {'field_id': 'q', 'value_ordinal': 1, 'val_number': 3},
          {'field_id': 'p', 'value_ordinal': 2, 'val_number': 500}, {'field_id': 'q', 'value_ordinal': 2, 'val_number': 2}]


def test_a_line_discount_comes_off_its_amount_before_the_totals():
    assert amount_field([f for f in FIELDS if f['section_name'] == 'items']) == 'a'
    assert calculate(FIELDS, VALUES) == {('a', 1): 3000.0, ('a', 2): 1000.0, ('t', 0): 4000.0}
    assert calculate(FIELDS, VALUES, {('items', 1): ('percent', 10.0), ('items', 2): ('amount', 250.0)}) == \
        {('a', 1): 2700.0, ('a', 2): 750.0, ('t', 0): 3450.0}
    assert calculate(FIELDS, VALUES, {('items', 2): ('amount', 5000.0)})[('a', 2)] == 0        # not below nothing


def test_the_editor_posts_them_and_copies_take_them_along():
    form = MultiDict({'discount': '10%', 'line_discount_S-1_3': '5000', 'line_discount_S-1_4': '', 'line_discount_S-9_1': '5%'})
    kept = D.from_form(form, {'S-1': 'Line Items'})
    assert kept == {'document': '10%', 'lines': {'line_items': {'3': '5000'}}}               # unknown sections are left out
    with pytest.raises(D.DiscountError, match='Line 2'):
        D.from_form(MultiDict({'line_discount_S-1_2': 'lots'}), {'S-1': 'items'})
    assert D.from_form(MultiDict({'discount': ''}), {}) is None
    assert D.remap(kept, {'line_items': 'items'}) == {'document': '10%', 'lines': {'items': {'3': '5000'}}}
    header = {'details': json.dumps({'discounts': kept}), 'currency_code': 'INR'}
    assert D.of(header) == {'document': ('percent', 10.0), 'lines': {'line_items': {3: ('amount', 5000.0)}}}
    assert D.describe(header, 'INR') == '10% off the total; a discount on 1 line'
    assert D.describe({'details': '{}'}) == '' and not D.any_of({'details': None})


def _header(found):
    return {'invoice_id': 'INV-A', 'org_id': 'a' * 36, 'template_id': 'T-A', 'template_version': 1, 'currency_code': 'INR',
            'tax_mode': 'none', 'tax_rate': 0, 'details': json.dumps({'discounts': found})}


def test_the_summary_takes_the_documents_discount_before_tax(fake_db):
    from invoice_service import build_sections, invoice_summary, with_discount_column
    header = _header({'document': '10%', 'lines': {'items': {'1': '5'}}})
    sections = build_sections(header, fake_db._values_for('INV-A'))
    rows = sections['Items']['line_item_rows']
    amount = next(c for c in rows[0] if c['field_name'] == 'total')
    assert (amount['val_number'], amount['gross'], amount['discount']) == (15.0, 20.0, '₹5.00')   # 2 × 10, less 5
    summary = invoice_summary(header, sections, [])
    # the template's grand total: lines 15 + 15, its own 10% tax: 33; then 10% off the document
    assert (summary['subtotal'], summary['discount']['amount'], summary['taxable'], summary['total']) == (33.0, 3.3, 29.7, 29.7)
    assert summary['discount']['percent'] == 10 and summary['discount']['label'] == '10%'

    shown = with_discount_column(sections)['Items']
    at = shown['line_item_headers'].index('Disc.')
    assert shown['line_item_headers'][at + 1] == 'Total'                                   # before the line's amount
    assert [r[at]['val_string'] for r in shown['line_item_rows']] == ['₹5.00', '']
    assert 'Disc.' not in sections['Items']['line_item_headers']                          # the summaries' sections stay as they are


def test_without_discounts_nothing_changes(fake_db):
    from invoice_service import build_sections, invoice_summary, with_discount_column
    header = _header(None)
    sections = build_sections(header, fake_db._values_for('INV-A'))
    summary = invoice_summary(header, sections, [])
    assert summary['discount'] is None and summary['subtotal'] == summary['taxable'] == summary['total'] == 38.5
    assert with_discount_column(sections) == sections


def test_the_gst_summary_shares_out_the_documents_discount():
    from invoice_service import _hsn_summary
    row = lambda hsn, amount: [{'field_name': 'hsn', 'data_type': 'string', 'val_string': hsn},  # noqa: E731
                               {'field_name': 'amount', 'data_type': 'number', 'val_number': amount, 'calculation_formula': 'x'}]
    sections = {'Items': {'type': 'line_item', 'line_item_rows': [row('8466', 30000), row('9987', 10000)]}}
    hsn = _hsn_summary(sections, 'cgst_sgst', 18, 0.9)
    assert [(h['hsn'], h['taxable'], round(h['tax'], 2)) for h in hsn] == [('8466', 27000.0, 4860.0), ('9987', 9000.0, 1620.0)]


def test_the_editor_opens_with_them():
    from editor_page import _sections
    data = {'S-1': {'title': 'Items', 'type': 'line_item', 'fields': [
        {'field_id': 'p', 'field_name': 'price', 'section_name': 'Items', 'data_type': 'number', 'values': {1: {'val_number': 10}, 2: {'val_number': 5}}},
        {'field_id': 'a', 'field_name': 'amount', 'section_name': 'Items', 'data_type': 'number', 'calculation_formula': 'this.price', 'values': {}}]}}
    entry = _sections(data, {'items': {2: ('percent', 10.0)}})[0]
    assert entry['amount_field'] == 'a'
    assert [(r['row'], r['discount']) for r in entry['rows']] == [(1, ''), (2, '10%')]


def test_a_version_tells_a_discount_from_a_new_price():
    import revisions
    line = lambda amount, gross=None, discount='': {'description': 'Gauge', 'qty': 2, 'amount': amount,  # noqa: E731
                                                    'gross': gross, 'discount': discount}
    version = lambda lines, details: {'header': {'details': json.dumps(details), 'currency_code': 'INR'},  # noqa: E731
                                      'lines': lines, 'details': details, 'total': sum(x['amount'] for x in lines)}
    changes = revisions.compare(version([line(2000)], {}), version([line(1800, 2000, '10%')], {'discounts': {'document': '500'}}))
    item = changes['items'][0]
    assert item['what'] == ['discount'] and (item['discount_before'], item['discount_after']) == ('', '10%')   # not a new price
    assert {'label': 'Discount on the total', 'before': 'None', 'after': '₹500.00'} in changes['fields']
