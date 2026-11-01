from datetime import date

import pytest

from documents import (fiscal_year, format_number, settings_from_form, suggest_tax_mode,
                       display_number, details_from_form)
from money import amount_in_words, format_money


# Figures taken from real sample documents (proforma 006/009, export 029, tax invoice 037)
@pytest.mark.parametrize('value,currency,expected', [
    (2063000, 'INR', '₹20,63,000.00'),
    (2434340, 'INR', '₹24,34,340.00'),
    (185670, 'INR', '₹1,85,670.00'),
    (11800, 'INR', '₹11,800.00'),
    (999, 'INR', '₹999.00'),
    (123456789, 'INR', '₹12,34,56,789.00'),
    (3247, 'USD', '$3,247.00'),
    (1234567.5, 'USD', '$1,234,567.50'),
    (-500, 'INR', '-₹500.00'),
    (None, 'USD', '$0.00'),
    (10, 'JPY', 'JPY 10.00'),
])
def test_format_money(value, currency, expected):
    assert format_money(value, currency) == expected


@pytest.mark.parametrize('value,currency,expected', [
    (1031500, 'INR', 'INR Ten Lakh Thirty One Thousand Five Hundred Rupees Only'),
    (28910, 'INR', 'INR Twenty Eight Thousand Nine Hundred Ten Rupees Only'),
    (4410, 'INR', 'INR Four Thousand Four Hundred Ten Rupees Only'),
    (4957, 'USD', 'USD Four Thousand Nine Hundred Fifty Seven Dollars Only'),
    (2497, 'USD', 'USD Two Thousand Four Hundred Ninety Seven Dollars Only'),
    (2434340, 'INR', 'INR Twenty Four Lakh Thirty Four Thousand Three Hundred Forty Rupees Only'),
    (125000000, 'INR', 'INR Twelve Crore Fifty Lakh Rupees Only'),
    (1000000, 'USD', 'USD One Million Dollars Only'),
    (12.5, 'USD', 'USD Twelve Dollars and Fifty Cents Only'),
    (100.75, 'INR', 'INR One Hundred Rupees and Seventy Five Paise Only'),
    (0, 'INR', 'INR Zero Rupees Only'),
])
def test_amount_in_words(value, currency, expected):
    assert amount_in_words(value, currency) == expected


@pytest.mark.parametrize('on,start,expected', [
    (date(2026, 4, 1), 4, '26-27'),
    (date(2027, 3, 31), 4, '26-27'),
    (date(2026, 3, 31), 4, '25-26'),
    (date(2099, 12, 1), 4, '99-00'),
    (date(2026, 6, 1), 1, '2026'),
])
def test_fiscal_year(on, start, expected):
    assert fiscal_year(on, start) == expected


@pytest.mark.parametrize('pattern,expected', [
    ('TF/Q/{num:03}/{fy}', 'TF/Q/027/26-27'),
    ('PI {num:03}({fy})', 'PI 027(26-27)'),
    ('{num:03}', '027'),
    ('INV-{yyyy}-{num:4}', 'INV-2026-0027'),
    ('{num}', '27'),
])
def test_format_number(pattern, expected):
    assert format_number(pattern, 27, '26-27', date(2026, 10, 5)) == expected


def test_display_number_falls_back_for_old_rows():
    assert display_number({'doc_number': 'PI 009(26-27)'}) == 'PI 009(26-27)'
    assert display_number({'invoice_id': 'abcdef12-xxxx'}) == 'INV-ABCDEF12'


GST_ORG = {'state': 'Tamil Nadu', 'country': 'India', 'profile': '{"gstin": "33ABCDE1234F1Z5"}'}


@pytest.mark.parametrize('doc_type,org,customer,expected', [
    ('invoice', GST_ORG, {'state': 'Tamil Nadu', 'country': 'India'}, 'cgst_sgst'),
    ('invoice', GST_ORG, {'state': 'tamil nadu', 'country': 'IN'}, 'cgst_sgst'),
    ('invoice', GST_ORG, {'state': 'Karnataka', 'country': 'India'}, 'igst'),
    ('proforma', GST_ORG, {'state': 'WA', 'country': 'USA'}, 'lut'),
    ('export_invoice', GST_ORG, {'state': '', 'country': ''}, 'lut'),
    ('invoice', {'state': 'CA', 'country': 'USA', 'profile': None}, {'state': 'NY'}, 'none'),
    ('quote', GST_ORG, {'state': 'Tamil Nadu', 'country': 'India'}, 'none'),
])
def test_suggest_tax_mode(doc_type, org, customer, expected):
    assert suggest_tax_mode(doc_type, org, customer) == expected


def test_the_gstins_decide_the_state_and_say_why():
    from documents import gstin_state, tax_note, tax_suggestion
    assert (gstin_state('33ABCDE1234F1Z5'), gstin_state(' 29abcde1234f1z5 '), gstin_state('37ABCDE1234F1Z5')) ==         ('Tamil Nadu', 'Karnataka', 'Andhra Pradesh')
    assert gstin_state('33ABCDE') == gstin_state('ABN 51 824 753 556') == gstin_state(None) == ''   # not a GSTIN
    # the GSTIN wins over an address typed another way ('TN'), or a wrong one
    same = tax_suggestion('invoice', GST_ORG, {'tax_id': '33AAACG0000X1Z5', 'state': 'TN', 'country': 'India'})
    other = tax_suggestion('invoice', GST_ORG, {'tax_id': '29AAACG0000X1Z5', 'state': 'Tamil Nadu', 'country': 'India'})
    assert same == {'mode': 'cgst_sgst', 'why': 'Tamil Nadu GSTIN'} and tax_note(same) == 'Tamil Nadu GSTIN, so CGST + SGST'
    assert other == {'mode': 'igst', 'why': 'Karnataka GSTIN, another state'}
    assert tax_note(other) == 'Karnataka GSTIN, another state, so IGST'
    # without a GSTIN, the addresses; abroad, an export
    by_address = tax_suggestion('invoice', GST_ORG, {'state': 'Kerala', 'country': 'India'})
    assert tax_note(by_address) == 'Kerala, another state, so IGST'
    assert tax_note(tax_suggestion('invoice', GST_ORG, {'state': 'Tamil Nadu'})) == 'Tamil Nadu, so CGST + SGST'
    assert tax_note(tax_suggestion('invoice', GST_ORG, {})) == 'CGST + SGST'                  # a guess: no reason given
    assert tax_note(tax_suggestion('proforma', GST_ORG, {'country': 'USA'})) == 'USA, outside India, so no GST under LUT'
    assert tax_note(tax_suggestion('quote', GST_ORG, {'tax_id': '29AAACG0000X1Z5'})) == ''     # quotations add no tax rows


def test_a_purchase_order_carries_its_suppliers_gst():
    from documents import tax_suggestion
    assert tax_suggestion('purchase_order', GST_ORG, {'tax_id': '27AAACT0000T1Z5'}) == {'mode': 'igst', 'why': 'Maharashtra GSTIN, another state'}
    assert tax_suggestion('purchase_order', GST_ORG, {'tax_id': '33AAACT0000T1Z5'})['mode'] == 'cgst_sgst'


def test_the_editor_gets_each_customers_tax_and_why():
    from document_service import customer_tax_hints
    hints = customer_tax_hints('invoice', GST_ORG, [{'customer_id': 'C-1', 'tax_id': '29AAACG0000X1Z5'},
                                                    {'customer_id': 'C-2', 'state': 'Tamil Nadu'}])
    assert hints == {'C-1': {'mode': 'igst', 'note': 'Karnataka GSTIN, another state, so IGST'},
                     'C-2': {'mode': 'cgst_sgst', 'note': 'Tamil Nadu, so CGST + SGST'}}
    assert customer_tax_hints('quote', GST_ORG, [{'customer_id': 'C-1'}]) == {'C-1': {'mode': 'none', 'note': ''}}


def test_settings_from_form_validates():
    s = settings_from_form({'tax_mode': 'cgst_sgst', 'tax_rate': '18', 'advance_percent': '50', 'advance_basis': 'total'})
    assert s == {'tax_mode': 'cgst_sgst', 'tax_rate': 18.0, 'advance_percent': 50.0, 'advance_basis': 'total'}
    s = settings_from_form({'tax_mode': 'bogus', 'tax_rate': '18', 'advance_percent': '250', 'advance_basis': 'x'})
    assert s == {'tax_mode': 'none', 'tax_rate': 0.0, 'advance_percent': 100.0, 'advance_basis': 'pre_tax'}
    assert settings_from_form({'tax_mode': 'lut', 'tax_rate': '18'})['tax_rate'] == 0.0


def test_details_from_form_keeps_only_type_fields():
    form = {'detail_kind_attn': ' Mr. X ', 'detail_buyer_order_no': 'PO-1', 'detail_subject': ''}
    assert details_from_form('quote', form) == {'kind_attn': 'Mr. X'}
    assert details_from_form('invoice', form) == {'buyer_order_no': 'PO-1'}


@pytest.mark.parametrize('number,details,expected', [
    ('TF/Q/029/26-27', {}, 'TF/Q/029R1/26-27'),          # the way revisions were numbered before DocuMint
    ('TF/Q/029R1/26-27', {}, 'TF/Q/029R2/26-27'),
    ('TF/Q/023A/26-27', {}, 'TF/Q/023AR1/26-27'),        # an alternative offer, revised
    ('PI 007(26-27)', {}, 'PI 007R1(26-27)'),
    ('TF-PI-005', {}, 'TF-PI-005 Rev.1'),                 # no year at the end: " Rev.N"
    ('Q/027/26-27 Rev.1', {'base_number': 'Q/027/26-27', 'revision': 1}, 'Q/027/26-27 Rev.2'),   # revised that way before
])
def test_revision_numbers(number, details, expected):
    import json
    from document_service import next_revision_number
    new, keep = next_revision_number({'doc_number': number, 'details': json.dumps(details)})
    assert new == expected
    assert bool(keep) == expected.endswith(tuple(f' Rev.{n}' for n in range(1, 10)))     # only " Rev.N" remembers its base


def test_imported_revisions_keep_their_numbering():
    """Q/029R1 was imported through the app's revise, so its details say base Q/029, revision 1: the number decides."""
    import json
    from document_service import next_revision_number
    doc = {'doc_number': 'TF/Q/029R1/26-27', 'details': json.dumps({'base_number': 'TF/Q/029/26-27', 'revision': 1})}
    assert next_revision_number(doc)[0] == 'TF/Q/029R2/26-27'


def test_what_is_owed_back_comes_only_from_credit_notes():
    from documents import balance_of, credit_of
    assert credit_of({'total_amount': 100, 'paid_amount': 100.01}) == 0        # a paisa over, no credit note: nothing to refund
    paid_then_credited = {'total_amount': 118000, 'paid_amount': 118000, 'credited_amount': 23600}
    assert (balance_of(paid_then_credited), credit_of(paid_then_credited)) == (0, 23600)
    part_paid = {'total_amount': 118000, 'paid_amount': 50000, 'credited_amount': 23600}
    assert (balance_of(part_paid), credit_of(part_paid)) == (44400, 0)
