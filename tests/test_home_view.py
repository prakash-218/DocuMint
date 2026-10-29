"""The new home page's logic: what needs attention (from where each project is) and the money to come in."""

from datetime import date

import home_view as H

TODAY = date(2026, 10, 20)


def row(title, stage, pill, tone='wait', status='open', quoted=0, due=0, advance=0, action=None):
    return {'title': title, 'stage': stage, 'pill': {'text': pill, 'tone': tone}, 'tone': tone, 'status': status, 'quoted': quoted,
            'due': due, 'advance': advance, 'action': action, 'sub': '', 'label': 'PRJ-001', 'currency': 'INR', 'url': f'/p/{title}',
            'customer': {'name': 'Gear Cutters Ltd', 'site': 'Hosur plant'}}


def test_what_needs_attention_follows_where_each_project_is():
    rows = [row('Hob arbor set', 'accepted', 'Waiting for an answer', tone='action', quoted=495600, action='Send a follow-up'),
            row('Spline gauges', 'accepted', 'Waiting for an answer', quoted=100000),                 # under two weeks: fine
            row('Drill jig', 'advance', 'Accepted', tone='action', quoted=50000, action='Raise proforma for the advance'),
            row('Press tool', 'advance', 'Waiting for advance', advance=40000, action='Record the advance'),
            row('Collet chuck', 'invoiced', 'To invoice', tone='action', action='Create tax invoice'),
            row('Gear blank', 'paid', 'Waiting for payment', due=120000, action='Record payment'),
            row('Old fixture', None, 'Paid', tone='done', action='Mark the project completed'),
            row('Done job', None, 'Paid', tone='done', status='completed'),
            row('Cancelled job', 'quoted', 'Cancelled', status='cancelled')]
    drafts = [{'label': 'Quotation (draft)', 'sub': 'Axle Works', 'total': 9000, 'currency': 'INR', 'url': '/quotes/D-1/edit'}]
    groups = {g['key']: g for g in H.attention(rows, drafts)}
    assert list(groups) == ['follow_up', 'accepted', 'advance', 'invoice', 'payment', 'drafts', 'paid_open']
    assert [i['title'] for i in groups['follow_up']['items']] == ['Hob arbor set']
    assert groups['follow_up']['total'] == {'INR': 495600}
    assert groups['advance']['items'][0]['amount'] == 40000 and groups['advance']['total'] == {'INR': 40000}  # what was asked for
    assert groups['payment']['total'] == {'INR': 120000} and groups['payment']['items'][0]['action'] == 'Record payment'
    assert groups['drafts']['items'][0]['action'] == 'Finish it'
    assert groups['paid_open']['items'][0]['title'] == 'Old fixture'
    assert groups['follow_up']['items'][0]['sub'] == 'Hosur plant · PRJ-001'


def test_only_the_first_few_show_with_how_many_more():
    rows = [row(f'Job {n}', 'paid', 'Waiting for payment', due=1000 * n) for n in range(1, 9)]
    [group] = H.attention(rows, [])
    assert group['count'] == 8 and group['more'] == 3
    assert [i['title'] for i in group['items']] == ['Job 8', 'Job 7', 'Job 6', 'Job 5', 'Job 4']      # most owed first


def inv(customer, issued, total, paid=0, status='pending', currency='INR', site=None):
    return {'customer_id': customer, 'customer_name': customer.title(), 'customer_site': site, 'issue_date': issued,
            'total_amount': total, 'paid_amount': paid, 'status': status, 'currency_code': currency}


def test_money_to_receive_by_the_invoices_age_and_customer():
    invoices = [inv('gear', '2026-10-10', 10000), inv('gear', '2026-09-01', 5000, paid=1000), inv('axle', '2026-08-01', 8000),
                inv('axle', '2026-05-01', 300, currency='USD'), inv('gear', '2026-10-01', 7000, paid=7000, status='paid'),
                inv('gear', '2026-10-15', 2000, status='draft')]
    waiting = [row('Press tool', 'advance', 'Waiting for advance', advance=40000)]
    r = H.to_receive(invoices, waiting, TODAY)
    assert r['total'] == {'INR': 22000, 'USD': 300} and r['count'] == 4
    assert [(a['label'], a['count'], a['total']) for a in r['ages']] == [
        ('0–30 days', 1, {'INR': 10000}), ('31–60 days', 1, {'INR': 4000}), ('61–90 days', 1, {'INR': 8000}),
        ('Over 90 days', 1, {'USD': 300})]
    assert [(c['name'], c['total']) for c in r['customers']] == [('Gear', {'INR': 14000}), ('Axle', {'INR': 8000, 'USD': 300})]
    assert r['advances'] == {'count': 1, 'total': {'INR': 40000}}


def test_with_payment_terms_money_owed_goes_by_how_late_it_is():
    invoices = [{**inv('gear', '2026-10-10', 10000), 'payment_days': 30},                  # due 9 Nov: not yet
                {**inv('gear', '2026-09-01', 5000, paid=1000), 'payment_days': 30},        # due 1 Oct: 19 days late
                {**inv('axle', '2026-07-01', 8000), 'due_date': '2026-08-10'},             # typed on it: 71 days late
                {**inv('axle', '2026-09-10', 6000)}]                                       # the usual 30 days: 10 days late
    r = H.to_receive(invoices, [], TODAY, usual=30)
    assert r['aged_by'] == 'due' and r['overdue'] == {'count': 3, 'total': {'INR': 18000}}
    assert [(a['label'], a['count'], a['total']) for a in r['ages']] == [
        ('Not due yet', 1, {'INR': 10000}), ('1–30 days late', 2, {'INR': 10000}), ('31–60 days late', 0, {}),
        ('Over 60 days late', 1, {'INR': 8000})]
    # While some have no due date at all, by the invoices' age as before
    mixed = H.to_receive(invoices, [], TODAY)
    assert mixed['aged_by'] == 'date' and mixed['ages'][0]['label'] == '0–30 days' and mixed['overdue']['count'] == 2


def test_overdue_invoices_come_first():
    overdue = [{'label': 'Tax Invoice 058', 'sub': 'Hosur plant · 12 days late', 'total': 60000, 'currency': 'INR', 'url': '/invoices/I-58'}]
    groups = H.attention([row('Press tool', 'invoiced', 'To invoice', quoted=5000)], [], overdue)
    assert [g['key'] for g in groups] == ['overdue', 'invoice']
    assert groups[0]['label'] == '1 invoice past its due date' and groups[0]['total'] == {'INR': 60000}
    assert groups[0]['items'][0]['action'] == 'Send a reminder'


def test_rows_say_how_many_and_which_and_the_greeting_uses_a_first_name():
    rows = [row(f'Job {n}', 'paid', 'Waiting for payment', due=1000 * n) for n in range(1, 7)]
    [group] = H.attention(rows, [])
    assert group['label'] == '6 projects waiting for payment'
    assert group['names'] == 'Job 6 · Job 5 · Job 4 · Job 3 and 2 more'      # most owed first
    [one] = H.attention([row('Drill jig', 'invoiced', 'To invoice', tone='action')], [])
    assert one['label'] == '1 project ready to invoice'
    assert H.first_name('ravi@example.com') == 'Ravi'
    assert H.first_name('info@example.com') == '' and H.first_name('demo-1@example.com') == '' and H.first_name(None) == ''
