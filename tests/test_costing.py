import pytest

from costing import clean_sheet, compute, number, quote_rows

FRAME = {'name': 'Torque tool frame', 'qty': 1, 'lines': [
    {'description': 'Raw material MS', 'qty': 900, 'unit': 'kg', 'unit_cost': 85},
    {'description': 'LM guide with block', 'make': 'Hiwin', 'qty': 2, 'unit_cost': 34000, 'markup': 10},  # x 1.1
]}
BUSH = {'name': 'Bush', 'qty': 3, 'cost_each': 1000, 'profit_percent': 20}
GAUGE = {'name': 'Gauge', 'qty': 1, 'cost_each': 4000, 'price_each': 5000}                              # typed price


def test_build_up_from_costs():
    r = compute(clean_sheet({'items': [FRAME, BUSH, GAUGE]}), 'build', 15)
    frame, bush, gauge = r['items']
    assert [l['cost'] for l in frame['lines']] == [76500, 74800] and frame['cost_each'] == 151300
    assert frame['price'] == pytest.approx(173995) and frame['profit_on_cost'] == 15.0
    assert (bush['price'], bush['amount'], bush['cost_total'], bush['profit']) == (1200, 3600, 3000, 600)
    assert (gauge['price'], gauge['profit'], gauge['manual_price']) == (5000, 1000, True)
    t = r['totals']
    assert (t['cost'], t['price'], t['profit']) == (158300, 182595, 24295)
    assert t['profit_on_cost'] == 15.3 and t['margin_of_price'] == 13.3
    rounded = compute(clean_sheet({'items': [FRAME]}), 'build', 15, round_to=1000)
    assert rounded['items'][0]['price'] == 174000                                # 1,73,995 -> 1,74,000


def test_work_back_from_a_known_total():
    r = compute(clean_sheet({'items': [FRAME, BUSH, GAUGE]}), 'target', 15, target_total='2,00,000')
    frame, bush, gauge = r['items']
    assert gauge['price'] == 5000                                                # a typed price keeps its share
    assert bush['price'] == pytest.approx(1263.77)                               # the rest goes by cost
    assert r['totals']['price'] == 200000                                        # the leftover paisa goes to the frame
    assert r['totals']['budget'] == pytest.approx(173913.04)                     # 2,00,000 / 1.15
    assert r['totals']['left'] == pytest.approx(15613.04) and r['totals']['off_target'] == 0
    over = compute(clean_sheet({'items': [FRAME]}), 'target', 15, target_total=150000)
    assert over['totals']['left'] < 0 and over['items'][0]['profit'] == -1300
    nothing_costed = compute(clean_sheet({'items': [{'name': 'A', 'qty': 1}, {'name': 'B', 'qty': 3}]}), 'target', 15, 4000)
    assert [it['amount'] for it in nothing_costed['items']] == [1000, 3000]      # by quantity until there are costs
    no_target = compute(clean_sheet({'items': [BUSH]}), 'target', 15, None)
    assert no_target['items'][0]['price'] == 1200 and 'budget' not in no_target['totals']


def test_cleaning_and_the_quote_rows():
    sheet = clean_sheet({'items': [
        {'name': '  Clamp  ', 'description': 'EN8, hardened', 'qty': '2', 'cost_each': '1,23,500.50', 'junk': 'x'},
        {'name': '', 'lines': [{'description': ''}]},                           # blank: dropped
        'not an item',
    ]})
    assert sheet == {'items': [{'name': 'Clamp', 'description': 'EN8, hardened', 'qty': 2.0, 'unit': '',
                                'cost_each': 123500.5, 'profit_percent': None, 'price_each': None, 'lines': []}]}
    rows = quote_rows(compute(sheet, 'build', 10))
    assert rows == [{'description': 'Clamp\nEN8, hardened', 'qty': 2.0, 'unit': '', 'price': 135850.55,
                     'amount': 271701.1}]
    assert 'cost' not in str(rows[0].keys())                                     # costs never reach the quote
    assert number('₹ 1,000') == 1000 and number('abc') is None and number(float('nan')) is None
    assert compute(clean_sheet(None))['totals'] == {'cost': 0, 'price': 0, 'profit': 0, 'profit_on_cost': None,
                                                    'margin_of_price': None}
