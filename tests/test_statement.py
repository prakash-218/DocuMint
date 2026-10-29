"""A customer's statement: the year it covers, what was brought forward, the invoices still unpaid, and its email."""

from datetime import date

import mailsend
import statement as S

TODAY = date(2026, 10, 20)


def line(day, fy, owed=0.0, paid=0.0, balance=0.0, text='Tax Invoice 001'):
    return {'date': date.fromisoformat(day), 'fy': fy, 'text': text, 'sub': '', 'owed': owed, 'paid': paid, 'balance': balance, 'url': '/x'}


ACCOUNTS = [{'currency': 'INR', 'lines': [
    line('2026-02-10', '25-26', owed=50000, balance=50000),
    line('2026-03-20', '25-26', paid=20000, balance=30000, text='Payment on 001'),
    line('2026-05-06', '26-27', owed=100000, balance=130000, text='Tax Invoice 005'),
    line('2026-06-01', '26-27', paid=30000, balance=100000, text='Payment on 001'),
]}, {'currency': 'USD', 'lines': [line('2026-07-01', '26-27', owed=500, balance=500)]}]


def test_a_financial_year_runs_from_its_first_month():
    assert S.period('26-27') == (date(2026, 4, 1), date(2027, 3, 31))
    assert S.period('2026', start_month=1) == (date(2026, 1, 1), date(2026, 12, 31))


def test_one_year_with_what_was_brought_forward():
    latest = S.pick(ACCOUNTS)
    assert (latest['currency'], latest['fy'], latest['years']) == ('INR', '26-27', ['26-27', '25-26'])
    assert (latest['opening'], latest['closing'], latest['owed'], latest['paid']) == (30000, 100000, 100000, 30000)
    assert [x['text'] for x in latest['lines']] == ['Tax Invoice 005', 'Payment on 001']
    first = S.pick(ACCOUNTS, '25-26')
    assert (first['opening'], first['closing']) == (0.0, 30000)
    every = S.pick(ACCOUNTS, 'all')
    assert every['fy'] is None and len(every['lines']) == 4 and every['closing'] == 100000
    assert S.pick(ACCOUNTS, '19-20')['fy'] == '26-27'                       # a year with nothing: the latest
    assert S.pick(ACCOUNTS, currency='USD')['closing'] == 500
    assert S.pick([]) is None


def doc(number, issued, total, paid=0, status='pending', due=None, days=None, currency='INR', doc_type='invoice'):
    return {'doc_type': doc_type, 'doc_number': number, 'status': status, 'issue_date': issued, 'due_date': due, 'payment_days': days,
            'total_amount': total, 'paid_amount': paid, 'currency_code': currency, 'customer_site': 'Hosur plant'}


def test_the_invoices_still_unpaid_with_when_they_were_due():
    docs = [doc('011', '2026-09-01', 50000, paid=10000, days=30), doc('005', '2026-06-01', 20000, due='2026-06-15'),
            doc('012', '2026-10-10', 9000), doc('009', '2026-05-01', 7000, paid=7000, status='paid'),
            doc('Q/1', '2026-05-01', 7000, doc_type='quote', status='sent'), doc('E/1', '2026-05-01', 300, currency='USD')]
    owing = S.unpaid(docs, 'INR', TODAY)
    assert [(x['text'], x['due'], x['late'], x['balance']) for x in owing] == [
        ('Tax Invoice 005', date(2026, 6, 15), 127, 20000), ('Tax Invoice 011', date(2026, 10, 1), 19, 40000),
        ('Tax Invoice 012', None, 0, 9000)]
    assert S.unpaid(docs, 'INR', TODAY, usual=5)[2]['late'] == 5            # the usual terms, for one without its own


def test_its_title_file_name_and_email():
    data = {'customer': {'name': 'Gear Cutters Ltd.'}, 'account': S.pick(ACCOUNTS), 'today': TODAY,
            'unpaid': S.unpaid([doc('011', '2026-09-01', 50000, paid=10000, days=30)], 'INR', TODAY), 'overdue': 40000}
    assert S.title(data) == 'Statement of account FY 26-27' and S.filename(data) == 'Statement-Gear-Cutters-Ltd-FY-26-27.pdf'
    assert S.title({**data, 'account': S.pick(ACCOUNTS, 'all')}) == 'Statement of account to date'
    people = [{'name': 'Divya', 'email': 'accounts@gearco.example'}]
    assert mailsend.statement_message(people, ['accounts@gearco.example'], data, 'Techflow Tools') == '\n'.join([
        'Dear Divya,', '',
        'Please find attached our statement of account for FY 26-27, as of 20 Oct 2026. The balance due is ₹1,00,000.', '',
        'Of this, ₹40,000 is past its due date:',
        '- Tax Invoice 011 of 1 Sep 2026: ₹40,000, due 1 Oct (19 days late)', '',
        'Please let us know if anything differs from your records.', '', 'Regards,', 'Techflow Tools'])
