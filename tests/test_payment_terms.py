"""Payment terms: days after the invoice date a customer pays, and when an invoice is due because of them."""

from datetime import date

import pytest

import payment_terms as T


@pytest.mark.parametrize('value, parsed', [
    ('30', (30, None)), (' 45 ', (45, None)), ('0', (0, None)), (365, (365, None)), ('', (None, None)), (None, (None, None)),
    ('366', (None, 'Payment terms are a number of days, 0 to 365.')), ('-5', (None, 'Payment terms are a number of days, 0 to 365.')),
    ('30 days', (None, 'Payment terms are a number of days, 0 to 365.')),
])
def test_terms_are_a_whole_number_of_days(value, parsed):
    assert T.parse_days(value) == parsed


def test_the_usual_terms_and_how_they_read():
    assert T.usual_days({'payment_days': 30}) == 30 and T.usual_days({}) is None and T.usual_days(None) is None
    assert [T.describe(d) for d in (0, 1, 45, None)] == ['On receipt', '1 day', '45 days', '']


def test_an_invoice_is_due_on_its_own_date_else_after_the_terms():
    invoice = {'issue_date': '2026-10-01', 'due_date': None, 'payment_days': 45}
    assert T.due_on(invoice) == date(2026, 11, 15)                                        # the customer's terms
    assert T.due_on(invoice, usual=30) == date(2026, 11, 15)                              # theirs win over the usual ones
    assert T.due_on({**invoice, 'payment_days': None}, usual=30) == date(2026, 10, 31)
    assert T.due_on({**invoice, 'payment_days': 0}, usual=30) == date(2026, 10, 1)        # on receipt
    assert T.due_on({**invoice, 'due_date': '2026-10-10'}, usual=30) == date(2026, 10, 10)    # typed on the invoice
    assert T.due_on({**invoice, 'payment_days': None}) is None                            # no terms anywhere
    assert T.due_on({'issue_date': None, 'payment_days': 30}) is None
