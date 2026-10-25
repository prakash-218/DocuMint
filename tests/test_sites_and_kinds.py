"""Customer site grouping and the kind a file name suggests (no database)."""

import customers


def test_file_kinds_and_wanted():
    from projects import email_file_wanted, guess_kind
    cases = {('PO 4500123.pdf', False): 'po', ('po_4500.pdf', False): 'po', ('Wipro purchase order.pdf', False): 'po',
             ('Test report.pdf', False): 'report', ('GA drg rev2.pdf', False): 'drawing', ('part.STEP', False): 'drawing',
             ('RFQ-118.xlsx', False): 'enquiry', ('KKR Q020(26-27).pdf', True): 'our_quote',
             ('PI 007(26-27) Wipro.pdf', True): 'our_proforma', ('Invoice 037.pdf', True): 'our_invoice',
             ('KKR Q020(26-27).pdf', False): 'other', ('photo.jpg', False): 'other', ('Report card.pdf', True): 'report'}
    assert {k: guess_kind(*k) for k in cases} == cases
    assert email_file_wanted({'file_name': 'a.pdf'}, b'%PDF-1.4')
    assert not email_file_wanted({'file_name': 'a.pdf'}, b'<html>')                  # not what it says it is
    assert not email_file_wanted({'file_name': 'image001.png'}, b'\x89PNG' + b'0' * 100)
    assert not email_file_wanted({'file_name': 'invite.ics'}, b'BEGIN:VCALENDAR')


PARENT = {'customer_id': 'p', 'name': 'TAFE', 'parent_id': None, 'city': 'Chennai'}
GEARS = {'customer_id': 'g', 'name': 'TAFE', 'parent_id': 'p', 'site': 'Gears Division', 'city': 'Pudupakkam'}
MADURAI = {'customer_id': 'm', 'name': 'TAFE', 'parent_id': 'p', 'site': 'Madurai', 'city': 'Madurai'}
ACME = {'customer_id': 'a', 'name': 'acme tools', 'parent_id': None, 'city': 'Hosur'}


def test_grouping_labels_and_search():
    groups = customers.group([MADURAI, ACME, GEARS, PARENT])
    assert [(g['customer']['customer_id'], [s['customer_id'] for s in g['sites']]) for g in groups] ==         [('a', []), ('p', ['g', 'm'])]
    assert [g['customer']['customer_id'] for g in customers.group([GEARS])] == ['g']    # parent not listed
    assert customers.label(GEARS) == 'TAFE · Gears Division' and customers.label(PARENT) == 'TAFE'
    assert customers.label({'customer_name': 'TAFE', 'customer_site': 'Madurai', 'name': 'x'}) == 'TAFE · Madurai'
    everyone = [PARENT, GEARS, MADURAI, ACME]
    assert [c['customer_id'] for c in customers.search(everyone, 'madurai')] == ['p', 'm']   # with its parent
    assert [c['customer_id'] for c in customers.search(everyone, 'tafe')] == ['p', 'g', 'm']
    assert [c['customer_id'] for c in customers.parent_choices(everyone, 'a')] == ['p']
