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
    ('KKR/Q/{num:03}/{fy}', 'KKR/Q/027/26-27'),
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
