"""The Ctrl+K search: what /search/items lists for each role, and how static/js/palette.js ranks it (run in Node)."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.fakedb import ORG_A

PALETTE = Path(__file__).resolve().parents[1] / 'static' / 'js' / 'palette.js'
NODE = shutil.which('node')


def _items(client):
    response = client.get('/search/items')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    return response.get_json()['items']


def test_lists_pages_actions_documents_and_customers(client, login_as, fake_db):
    fake_db.invoices['INV-A'].update(doc_number='TF/INV/007/26-27', issue_date='2026-10-05', subject='Drill jig',
                                     buyer_order_no='PO-4471')
    login_as('U-A', ORG_A, 'alice@a.com')
    items = _items(client)
    assert {'page', 'action', 'document', 'customer', 'template'} <= {i['kind'] for i in items}
    doc = next(i for i in items if i['kind'] == 'document')
    assert doc['title'] == 'TF/INV/007/26-27' and doc['code'] == 'INV · TF/INV/007/26-27' and doc['url'] == '/invoices/INV-A'
    assert doc['sub'] == 'Tax Invoice · Acme · Drill jig · Oct 5, 2026 · $38.50'
    assert 'PO-4471' in doc['also'] and doc['badge'] == 'pending' and doc['tone'] == 'warning'
    customer = next(i for i in items if i['kind'] == 'customer')
    assert customer['title'] == 'Acme' and customer['url'] == '/customers/C-A'
    titles = {i['title'] for i in items}
    assert {'Dashboard', 'Quotations', 'Audit log', 'New quotation', 'New customer'} <= titles


def test_viewers_find_things_but_no_actions(client, login_as, fake_db):
    fake_db.members['U-A'][0]['role'] = 'viewer'
    login_as('U-A', ORG_A, 'alice@a.com')
    titles = {i['title'] for i in _items(client)}
    assert {'Invoices', 'Projects', 'Acme'} <= titles
    assert not titles & {'New quotation', 'New project', 'New customer', 'Audit log', 'Notifications', 'Emails'}


def test_needs_a_login(client):
    assert client.get('/search/items').status_code == 302


def test_every_page_has_the_search(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    html = client.get('/customers/').get_data(as_text=True)
    assert 'id="palette"' in html and 'data-palette-open' in html and 'data-source="/search/items"' in html
    assert html.index('js/fuzzy.js') < html.index('js/project-picker.js') < html.index('js/palette.js')
    with client.session_transaction() as s:
        s.clear()
    assert 'id="palette"' not in client.get('/auth/login').get_data(as_text=True)


# ---------------------------------------------------------------- Ranking (palette.js, in Node)

ITEMS = [
    {'kind': 'page', 'title': 'Invoices', 'name': 'Invoices', 'also': 'tax export bills'},
    {'kind': 'action', 'title': 'New invoice', 'name': 'New invoice', 'also': 'create tax'},
    {'kind': 'project', 'title': 'Torque fixture', 'code': 'PRJ-047', 'name': 'Torque fixture',
     'also': 'Acme Tools 26-27', 'date': '2026-09-01'},
    {'kind': 'document', 'title': 'TF/Q/029/26-27', 'code': 'TF/Q/029/26-27', 'name': 'Torque fixture',
     'also': 'Quotation Quote Acme Tools', 'date': '2026-08-01', 'old': True},
    {'kind': 'document', 'title': 'TF/Q/029R1/26-27', 'code': 'TF/Q/029R1/26-27', 'name': 'Torque fixture',
     'also': 'Quotation Quote Acme Tools', 'date': '2026-08-20'},
    {'kind': 'document', 'title': 'TF/INV/012/25-26', 'code': 'TF/INV/012/25-26', 'name': 'Drill jig',
     'also': 'Tax Invoice Invoice Bolt Works PO-4471', 'date': '2025-11-03'},
    {'kind': 'document', 'title': '009', 'code': 'PI · 009', 'name': 'Drill jig', 'also': 'Proforma Invoice Proforma Bolt Works',
     'date': '2026-01-10'},
    {'kind': 'customer', 'title': 'Acme Tools', 'name': 'Acme Tools', 'also': 'Pune'},
]

RUN = """
const P = require(process.argv[1]);
let input = '';
process.stdin.on('data', d => input += d).on('end', () => {
    const { items, queries, code } = JSON.parse(input);
    console.log(JSON.stringify({ ranked: queries.map(q => P.rank(items, q).map(i => i.title)), words: P.codeWords(code) }));
});
"""


def _palette(queries, code=''):
    if not NODE:
        pytest.skip('Node.js is not installed')
    out = subprocess.run([NODE, '-e', RUN, str(PALETTE)], input=json.dumps({'items': ITEMS, 'queries': queries, 'code': code}),
                         capture_output=True, text=True, check=True, timeout=30)
    return json.loads(out.stdout)


def test_document_numbers_are_found_by_their_short_forms():
    words = _palette([], 'TF/Q/029R1/26-27')['words']
    assert {'q029r1', 'q29r1', 'q029', 'q29', '029', '29'} <= set(words)
    q29, inv12, revision, pi9, joined = _palette(['q29', 'inv 12', 'Q/029R1', 'pi 9', 'pi9'])['ranked']
    assert q29 == ['TF/Q/029R1/26-27', 'TF/Q/029/26-27']                   # the current revision first
    assert inv12 == ['TF/INV/012/25-26'] and revision == ['TF/Q/029R1/26-27']
    assert pi9 == joined == ['009']                                         # a bare number, by its type's short code


def test_typos_abbreviations_and_years():
    typo, by_year, swapped, po = _palette(['trq fixtre', 'acme 26-27', 'acem', 'bolt 4471'])['ranked']
    assert typo[0] == 'Torque fixture'                                      # the project before its documents
    assert by_year == ['TF/Q/029R1/26-27', 'TF/Q/029/26-27', 'Torque fixture']
    assert swapped[0] == 'Acme Tools' and po == ['TF/INV/012/25-26']


def test_pages_come_before_the_documents_that_mention_them():
    assert _palette(['inv'])['ranked'][0][:3] == ['Invoices', 'New invoice', 'TF/INV/012/25-26']
