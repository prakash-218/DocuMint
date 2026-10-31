"""Sharing a document (sharing.py) and paying it by UPI (upi.py): the pieces that need no database."""
from datetime import date

import pytest

import sharing
import upi

PROFILE = {'upi_id': 'demoengineering@okaxis'}


def doc(doc_type='invoice', **over):
    return {'invoice_id': 'D-1', 'doc_type': doc_type, 'doc_number': 'DM/INV/058/26-27', 'status': 'pending', 'currency_code': 'INR',
            'organization_name': 'Demo Engineering', 'issue_date': date(2026, 11, 18), 'details': '{"subject": "Hob arbor set (3 nos)"}', **over}


@pytest.mark.parametrize('upi_id,ok', [('demoengineering@okaxis', True), ('9876543210@ybl', True), ('ravi.k-1@oksbi', True),
                                       ('not an id', False), ('a@b', False), ('@okaxis', False), ('', False), (None, False)])
def test_what_a_upi_id_looks_like(upi_id, ok):
    assert upi.valid(upi_id) is ok


def test_what_is_due_now():
    assert upi.due(doc(), {'total': 100, 'balance': 40}) == 40
    assert upi.due(doc('proforma'), {'total': 1000, 'advance': {'amount': 400}, 'paid': 150}) == 250       # the advance asked
    assert upi.due(doc('proforma'), {'total': 1000, 'advance': None, 'paid': 0}) == 1000
    assert upi.due(doc('quote'), {'total': 1000}) == 0
    assert upi.due(doc('proforma', status='converted'), {'total': 1000, 'paid': 0}) == 0                    # the invoice has it now
    assert upi.due(doc(status='paid'), {'total': 100, 'balance': 0}) == 0


def test_the_qr_code_pays_the_amount_due_to_the_upi_id():
    pay = upi.payment(doc(), {'total': 297360, 'balance': 297360}, PROFILE)
    assert pay['link'] == 'upi://pay?pa=demoengineering@okaxis&pn=Demo%20Engineering&am=297360.00&cu=INR&tn=DM%2FINV%2F058%2F26-27'
    assert pay['qr'].startswith('data:image/png;base64,') and pay['amount'] == 297360
    assert upi.payment(doc(), {'balance': 10}, {}) is None                                   # no UPI ID
    assert upi.payment(doc(currency_code='USD'), {'balance': 10}, PROFILE) is None           # rupees only
    assert upi.payment(doc(), {'balance': 0}, PROFILE) is None                               # nothing due


@pytest.mark.parametrize('phone,number', [('98765 43210', '919876543210'), ('098765-43210', '919876543210'),
                                          ('+91 98765 43210', '919876543210'), ('+1 (415) 555-0100', '14155550100'),
                                          ('044 2345', ''), ('', ''), (None, '')])
def test_a_phone_number_for_whatsapp(phone, number):
    assert sharing.wa_number(phone) == number


def test_the_message_says_what_it_is_what_is_due_and_how_to_pay():
    pay = upi.payment(doc(), {'total': 297360, 'balance': 297360}, PROFILE)
    text = sharing.message(doc(due_date=date(2026, 12, 18)), {'total': 297360, 'balance': 297360, 'tax_lines': [1]}, 'https://x/s/T', pay,
                           today=date(2026, 12, 1))
    assert text == ('Please find our invoice DM/INV/058/26-27 for hob arbor set (3 nos): ₹2,97,360 incl. GST, ₹2,97,360 due by 18 Dec 2026.\n'
                    'Pay by UPI to demoengineering@okaxis, or scan the QR code on the page.\n'
                    'https://x/s/T\n\nRegards,\nDemo Engineering')
    late = sharing.message(doc(due_date=date(2026, 12, 18)), {'total': 100, 'balance': 60}, sharing.LINK, None, today=date(2027, 1, 2))
    assert late.startswith('Please find our invoice DM/INV/058/26-27 for hob arbor set (3 nos): ₹100, ₹60 due since 18 Dec 2026.\n[link]\n')
    quote = sharing.message(doc('quote', doc_number='DM/Q/041R1/26-27', details='{}'), {'total': 495600}, sharing.LINK, None)
    assert quote.startswith('Please find our quotation DM/Q/041R1/26-27: ₹4,95,600.\n[link]')
    advance = sharing.message(doc('proforma', doc_number='PI 012(26-27)', details='{}'), {'total': 1000, 'advance': {'amount': 400}, 'paid': 0},
                              sharing.LINK, None)
    assert advance.startswith('Please find our proforma invoice PI 012(26-27). The advance of ₹400 is due.')
    paid = sharing.message(doc(details='{}'), {'total': 100, 'balance': 0}, sharing.LINK, None)
    assert paid.startswith('Please find our invoice DM/INV/058/26-27: ₹100.')


def test_the_people_with_whatsapp_those_who_get_it_first():
    contacts = [{'contact_id': 'K-1', 'name': 'Mr. Senthil', 'phone': '98400 11111', 'project_gets': 'none'},
                {'contact_id': 'K-2', 'name': 'Ms. Divya', 'role': 'Accounts', 'phone': '91234 56789', 'project_gets': 'billing'},
                {'contact_id': 'K-3', 'name': 'Mr. Arun', 'phone': '', 'project_gets': 'all'}]
    found = sharing.people(contacts, doc())
    assert [(p['name'], p['number'], p['gets_it']) for p in found] == [('Ms. Divya', '919123456789', True), ('Mr. Senthil', '919840011111', False)]
    assert sharing.wa_link('Dear Divya,\n₹4,500 & thanks', '919123456789') == \
        'https://wa.me/919123456789?text=Dear%20Divya%2C%0A%E2%82%B94%2C500%20%26%20thanks'
    assert len(sharing.new_token()) == 43 and sharing.new_token() != sharing.new_token()
