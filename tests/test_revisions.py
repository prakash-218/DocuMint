import revisions


def _q(i, source=None, number=None, date='2026-10-01', status='sent', total=100, doc_type='quote'):
    return {'invoice_id': i, 'doc_type': doc_type, 'source_invoice_id': source, 'doc_number': number or i,
            'issue_date': date, 'status': status, 'total_amount': total, 'customer_name': 'Farm Gear Works'}


def test_a_revised_quotation_is_one_row_as_its_latest_version():
    docs = [_q('r2', 'r1', 'Q/029R2', '2026-10-26', 'draft'), _q('other', number='Q/030'),
            _q('r1', 'q', 'Q/029R1', '2026-10-24', 'revised'), _q('q', number='Q/029', date='2026-10-11', status='revised'),
            _q('pi', 'r2', 'PI/007', doc_type='proforma')]
    versions = revisions.chains(docs)
    assert [v['invoice_id'] for v in versions['q']] == ['q', 'r1', 'r2'] and versions['r1'] is versions['r2']
    assert 'other' not in versions and 'pi' not in versions          # never revised; not a quotation
    rows = revisions.collapse(docs)
    assert [r['invoice_id'] for r in rows] == ['r2', 'other', 'pi']
    assert [v['doc_number'] for v in rows[0]['versions']] == ['Q/029R1', 'Q/029']     # newest first
    assert 'versions' not in rows[1]
    # A search for an old number finds the quotation
    assert revisions.matches(rows[0], lambda d: 'Q/029R1' in d['doc_number'])
    assert not revisions.matches(rows[1], lambda d: 'Q/029' in d['doc_number'])
    assert revisions.previous(versions['q'], 'r2')['invoice_id'] == 'r1' and revisions.previous(versions['q'], 'q') is None


def test_a_loop_of_sources_doesnt_hang():
    docs = [_q('a', 'b'), _q('b', 'a')]                  # can't happen (a source is older), but mustn't loop forever
    assert len(revisions.collapse(docs)) == 2


def _version(lines, total, due='2026-11-10', **details):
    return {'header': {'due_date': due}, 'details': details, 'total': total,
            'lines': [{'description': d, 'qty': q, 'amount': a, 'unit': 'no.'} for d, q, a in lines]}


def test_what_changed_between_versions():
    before = _version([('Axle final assembly\nMechanical', 1, 240000), ('P&F & Transportation', 1, 8000),
                       ('Commissioning', 1, 25000)], 273000, subject='Axle assembly',
                      terms='Taxes: 18% GST\nDelivery: (10-12) weeks')
    after = _version([('Axle final assembly\nMechanical, pneumatic', 1, 225000), ('Commissioning', 2, 50000),
                      ('Electrical panel', 1, 35000)], 310000, due='2026-11-24', subject='Axle assembly',
                     terms='Taxes: 18% GST\nDelivery: (8-10) weeks')
    c = revisions.compare(before, after)
    by = {i['description'].splitlines()[0]: i for i in c['items']}
    assert by['Axle final assembly']['change'] == 'changed' and by['Axle final assembly']['what'] == ['price', 'description']
    assert by['Axle final assembly']['price_after'] == 225000
    assert by['Commissioning']['what'] == ['qty']                      # same price, twice the days
    assert by['Electrical panel']['change'] == 'added' and by['P&F & Transportation']['change'] == 'removed'
    assert [f['label'] for f in c['fields']] == ['Valid until']
    assert c['terms'] == {'added': ['Delivery: (8-10) weeks'], 'removed': ['Delivery: (10-12) weeks']}
    assert c['total_change'] == 37000 and not c['nothing']


def test_a_plain_copy_changed_nothing():
    v = _version([('Gauge', 2, 2000)], 2000, terms='Taxes: 18% GST')
    c = revisions.compare(v, _version([('Gauge', 2, 2000)], 2000, terms='Taxes: 18% GST'))
    assert c['nothing'] and c['items'] == [] and c['terms'] is None
