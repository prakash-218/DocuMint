"""The new customer page's logic: their statement of account, and their files by project."""

import customer_view as C


def url(endpoint, **values):
    return f"/{endpoint}" + ''.join(f'/{k}={v}' for k, v in sorted(values.items()))


def doc(n, doc_type, status, total, issued, currency='INR', site=None):
    return {'invoice_id': f'D-{n}', 'doc_type': doc_type, 'status': status, 'total_amount': total, 'issue_date': issued,
            'doc_number': f'{n:03}', 'currency_code': currency, 'customer_site': site}


def pay(n, on, doc_type, amount, paid, advance_number=None, method='NEFT / RTGS', ref=None, currency='INR'):
    return {'payment_id': f'P-{n}', 'invoice_id': on, 'doc_type': doc_type, 'doc_number': on.split('-')[1].zfill(3), 'amount': amount,
            'payment_date': paid, 'advance_number': advance_number, 'method': method, 'reference_number': ref, 'currency_code': currency}


def test_the_statement_is_what_they_owe_and_paid_with_the_balance_after_each():
    docs = [doc(7, 'proforma', 'converted', 40000, '2026-02-10'),        # asked for, not owed: not in it
            doc(58, 'invoice', 'paid', 118000, '2026-03-20'),
            doc(61, 'invoice', 'pending', 59000, '2026-04-12', site='Hosur plant'),
            doc(62, 'invoice', 'draft', 1000, '2026-04-20'),             # not sent: not owed yet
            doc(1, 'quote', 'accepted', 50000, '2026-01-05'),
            doc(9, 'proforma', 'sent', 20000, '2026-05-02')]
    payments = [pay(1, 'D-58', 'invoice', 40000, '2026-02-15T10:00:00+05:30', advance_number='PI 007'),   # came in on the PI
                pay(2, 'D-58', 'invoice', 78000, '2026-04-02', ref='UTR 1188'),
                pay(3, 'D-9', 'proforma', 10000, '2026-05-06')]                                          # still on its PI
    [account] = C.statement(docs, payments, url, sites=True)
    lines = [(x['date'].isoformat() if x['date'] else None, x['fy'], x['text'], x['owed'], x['paid'], x['balance'])
             for x in account['lines']]
    assert [x['date'] if isinstance(x['date'], str) else x['date'].isoformat() for x in account['lines']] == \
        ['2026-02-15', '2026-03-20', '2026-04-02', '2026-04-12', '2026-05-06']
    assert lines == [
        ('2026-02-15', '25-26', 'Advance on PI 007, applied to 058', 0, 40000, -40000),
        ('2026-03-20', '25-26', 'Tax Invoice 058', 118000, 0, 78000),
        ('2026-04-02', '26-27', 'Payment on 058', 0, 78000, 0),
        ('2026-04-12', '26-27', 'Tax Invoice 061', 59000, 0, 59000),
        ('2026-05-06', '26-27', 'Advance on 009', 0, 10000, 49000),
    ]
    assert (account['owed'], account['paid'], account['balance']) == (177000, 128000, 49000)
    assert account['lines'][2]['sub'] == 'NEFT / RTGS · UTR 1188' and account['lines'][3]['sub'] == 'Hosur plant'
    assert account['lines'][1]['url'] == '/invoices_bp.view_invoice_new/invoice_id=D-58'


def test_each_currency_has_its_own_account_and_an_invoice_and_payment_on_one_day_go_invoice_first():
    docs = [doc(5, 'export_invoice', 'pending', 1200, '2026-06-01', currency='USD'), doc(6, 'invoice', 'pending', 500, '2026-06-01')]
    payments = [pay(1, 'D-5', 'invoice', 200, '2026-06-01', currency='USD')]
    usd, inr = sorted(C.statement(docs, payments, url, start_month=1), key=lambda a: a['currency'], reverse=True)
    assert usd['currency'] == 'USD' and [x['text'] for x in usd['lines']] == ['Export Invoice 005', 'Payment on 005']
    assert [x['balance'] for x in usd['lines']] == [1200, 1000] and usd['lines'][0]['fy'] == '2026'
    assert (inr['currency'], inr['balance']) == ('INR', 500)
    assert C.statement([], [], url) == []


def test_files_are_grouped_by_project_newest_first_then_the_ones_in_none():
    def f(n, project_id, date):
        return {'attachment_id': f'A-{n}', 'project_id': project_id, 'project_no': 7, 'file_name': f'drawing-{n}.pdf', 'kind': 'drawing',
                'doc_date': date, 'file_size': 2048}
    projects = {'P-1': {'title': 'Hob arbor set', 'label': 'PRJ-001', 'url': '/p/1'},
                'P-2': {'title': 'Spline gauges', 'label': 'PRJ-002', 'url': '/p/2'}}
    groups = C.file_groups([f(1, 'P-1', '2026-03-01'), f(2, None, '2026-10-01'), f(3, 'P-2', '2026-09-01'), f(4, 'P-1', '2026-04-01'),
                            f(5, 'P-9', '2026-01-01')], projects, url)
    assert [(g['project'] or {}).get('title') for g in groups] == ['Spline gauges', 'Hob arbor set', 'PRJ-007', None]
    assert [x['id'] for x in groups[1]['files']] == ['A-1', 'A-4'] and groups[1]['project']['url'] == '/p/1'
    assert groups[2]['project']['url'] is None            # a project this role doesn't see listed
    assert groups[0]['files'][0]['url'] == '/projects_bp.download_file/attachment_id=A-3'
