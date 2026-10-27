import io

import pytest

import costing_import as ci
from costing import clean_rates, clean_sheet, items_to_copy


def test_heading_row_and_columns_are_guessed():
    rows = [['Breakup Details', None, None], [None, None, None],
            ['S.No', 'Descripition', 'Qty', 'Value in Rs', 'Design Cost Adjustment', 'Total Value'],
            [1, 'Last PO', 1, 745420, 37271, 708149]]
    assert ci.guess_columns(rows) == {'header_row': 2, 'columns': {'name': 1, 'qty': 2, 'amount': 3}}
    proposal = [['No', 'Description', 'Technical specifications', 'Scope of supply', 'Price in Rs/Qty']]
    assert ci.guess_columns(proposal)['columns'] == {'name': 1, 'spec': 2, 'price': 4}   # "No" is the serial, not qty
    breakup = [[None, 'Activity', 'Perkg /cost'], [None, 'Material cost Rs 90/Kg', 90]]
    assert ci.guess_columns(breakup)['columns'] == {'name': 1, 'price': 2}
    assert ci.guess_columns([['Overall'], ['Base', 55000]])['header_row'] is None


def test_csv_and_refusals():
    data = io.BytesIO('Description,Qty,Rate,Amount\nMS plate,"1,200",85,"1,02,000"\n,,,\n'.encode('utf-8'))
    sheet = ci.read(data, 'rates.csv')['sheets'][0]
    assert sheet['name'] == 'rates' and sheet['rows'] == [['Description', 'Qty', 'Rate', 'Amount'], ['MS plate', 1200.0, 85.0, 102000.0]]
    assert sheet['columns'] == {'name': 0, 'qty': 1, 'price': 2, 'amount': 3}
    for name, message in (('old.xls', '.xlsx'), ('notes.txt', 'Excel workbook'), ('bad.xlsx', "couldn't be read")):
        with pytest.raises(ci.SheetError, match=message):
            ci.read(io.BytesIO(b'junk'), name)
    with pytest.raises(ci.SheetError, match='5 MB'):
        ci.read(io.BytesIO(b'x' * (ci.MAX_BYTES + 1)), 'big.xlsx')


def test_rates_are_cleaned_and_copies_drop_keys_and_typed_costs_under_lines():
    rates = clean_rates([{'description': 'MS', 'unit_cost': '90'}, {'description': 'ms', 'unit_cost': '85,000'},
                         {'description': 'MS', 'make': 'Tata', 'unit_cost': 'x'}, {'description': ''}, 'junk'])
    assert [(r['description'], r['make'], r['unit_cost']) for r in rates] == [('ms', '', 85000), ('MS', 'Tata', None)]
    sheet = clean_sheet({'items': [{'key': 'a', 'name': 'Frame', 'cost_each': 5, 'lines': [{'description': 'MS', 'qty': 2, 'unit_cost': 90}]},
                                   {'key': 'b', 'name': 'Bush', 'qty': 3, 'cost_each': 1000}],
                         'shared': [{'description': 'Design', 'unit_cost': 3000}]})
    copied = items_to_copy({'sheet': sheet, 'mode': 'build', 'currency': 'INR'})
    assert [it['name'] for it in copied] == ['Frame', 'Bush'] and all('key' not in it for it in copied)
    assert copied[0]['cost_each'] is None and copied[0]['own_cost_each'] == 180      # the lines' total, not the shared
    assert copied[1]['cost_each'] == 1000 and copied[1]['own_cost_each'] == 1000
