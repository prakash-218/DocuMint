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
    key = sheet['items'][0].pop('key')
    assert key.startswith('i') and len(key) == 9
    assert sheet == {'items': [{'name': 'Clamp', 'description': 'EN8, hardened', 'qty': 2.0, 'unit': '',
                                'cost_each': 123500.5, 'profit_percent': None, 'price_each': None, 'lines': []}],
                     'shared': [], 'exchange_rate': None, 'cost_currency': 'INR'}
    rows = quote_rows(compute(sheet, 'build', 10))
    assert rows == [{'description': 'Clamp\nEN8, hardened', 'qty': 2.0, 'unit': '', 'price': 135850.55,
                     'amount': 271701.1}]
    assert 'cost' not in str(rows[0].keys())                                     # costs never reach the quote
    assert number('₹ 1,000') == 1000 and number('abc') is None and number(float('nan')) is None
    assert compute(clean_sheet(None))['totals'] == {'cost': 0, 'cost_base': 0, 'shared': 0, 'price': 0, 'profit': 0,
                                                    'profit_on_cost': None, 'margin_of_price': None}


def test_item_keys_survive_and_shared_costs_name_real_items():
    sheet = clean_sheet({'items': [{'key': 'a1', 'name': 'A'}, {'key': 'a1', 'name': 'B'}, {'key': 'BAD KEY', 'name': 'C'}],
                         'shared': [{'description': 'Freight', 'unit_cost': 5000, 'items': ['a1', 'gone', 7]},
                                    {'description': '', 'kind': 'junk', 'spread': 'junk'}]})
    keys = [it['key'] for it in sheet['items']]
    assert keys[0] == 'a1' and len(set(keys)) == 3                               # duplicates and bad keys get new ones
    assert len(sheet['shared']) == 1 and sheet['shared'][0]['items'] == ['a1']
    assert (sheet['shared'][0]['kind'], sheet['shared'][0]['spread']) == ('amount', 'equal')


DESIGN = {'description': 'Design charge', 'unit_cost': 30000}                    # equally over all the items
FREIGHT = {'description': 'Freight', 'unit_cost': 12000, 'spread': 'cost', 'items': ['b', 'c']}
CHANGES = {'description': 'For changes', 'kind': 'percent', 'percent': 10}       # 10% of the items' own cost


def test_shared_costs_are_spread_over_the_items():
    items = [{'key': 'a', 'name': 'A', 'cost_each': 10000}, {'key': 'b', 'name': 'B', 'qty': 2, 'cost_each': 10000},
             {'key': 'c', 'name': 'C', 'cost_each': 40000}]
    r = compute(clean_sheet({'items': items, 'shared': [DESIGN, FREIGHT, CHANGES]}), 'build', 0)
    a, b, c = r['items']
    assert [s['amount'] for s in r['shared']] == [30000, 12000, 7000]           # 10% of 70,000
    assert [s['spread_over'] for s in r['shared']] == [3, 2, 3]
    # A: 10k + 10k design + 1k changes; B: 20k + 10k + 4k freight (20k of 60k) + 2k; C: 40k + 10k + 8k + 4k
    assert (a['shared_cost'], b['shared_cost'], c['shared_cost']) == (11000, 16000, 22000)
    assert (a['cost_total'], b['cost_total'], b['cost_each'], c['cost_total']) == (21000, 36000, 18000, 62000)
    assert r['totals']['cost'] == 119000 and r['totals']['shared'] == 49000 and r['totals']['price'] == 119000
    with_profit = compute(clean_sheet({'items': items, 'shared': [DESIGN]}), 'build', 10)
    assert with_profit['items'][1]['price'] == 16500                             # (20k + 10k) / 2 x 1.1


def test_costs_in_rupees_quoted_in_dollars():
    sheet = clean_sheet({'items': [{'name': 'Fixture', 'cost_each': 780000}], 'exchange_rate': '78'})
    r = compute(sheet, 'build', 15, currency='USD')
    it = r['items'][0]
    assert (it['cost_each'], it['cost_each_q'], it['price']) == (780000, 10000, 11500)
    assert (r['totals']['cost'], r['totals']['cost_base'], r['totals']['profit']) == (10000, 780000, 1500)
    assert r['currency'] == 'USD' and r['cost_currency'] == 'INR' and not r['needs_rate']
    assert compute(sheet, 'build', 15)['items'][0]['price'] == 897000            # quoted in rupees: no conversion
    no_rate = compute(clean_sheet({'items': [{'name': 'Fixture', 'cost_each': 780000}]}), 'build', 15, currency='USD')
    assert no_rate['needs_rate']
    back = compute(sheet, 'target', 15, target_total=11500, currency='USD')
    assert back['items'][0]['price'] == 11500 and back['totals']['budget'] == 10000
