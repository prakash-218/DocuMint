"""Several documents at once (exports.py): which ones go in, the CSV's rows, and the ZIP's file names."""
import csv
import io
import zipfile
from datetime import date

import exports

DOCS = [{'invoice_id': 'D-2', 'doc_type': 'invoice', 'doc_number': 'TF/058', 'issue_date': date(2026, 11, 18), 'customer_name': 'Gear Cutters Ltd',
         'customer_site': 'Hosur plant', 'project_id': 'P-1', 'project_no': 41, 'subject': 'Invoice for the hob arbor set', 'buyer_order_no': 'PO 4471',
         'status': 'pending', 'currency_code': 'INR', 'total_amount': 118000, 'paid_amount': 18000},
        {'invoice_id': 'D-1', 'doc_type': 'quote', 'doc_number': 'TF/Q/041', 'issue_date': date(2026, 10, 10), 'customer_name': 'Gear Cutters Ltd',
         'status': 'sent', 'currency_code': 'INR', 'total_amount': 100000, 'paid_amount': 0}]


def _read(data: bytes):
    assert data.startswith('﻿'.encode('utf-8'))                                  # Excel reads ₹ and names right
    return list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))


def test_only_the_lists_kinds_go_in_in_its_order():
    assert [d['invoice_id'] for d in exports.chosen(DOCS, ['D-1', 'D-2', 'D-9'], ('invoice', 'export_invoice'))] == ['D-2']
    assert exports.chosen(DOCS, [], ('quote',)) == []


def test_a_row_each_with_the_taxable_value_and_the_gst():
    header = {'customer_tax_id': '33AAACG0000X1Z5', 'customer_state': 'Tamil Nadu'}
    summary = {'taxable': 100000.0, 'total': 118000.0, 'tax_lines': [{'label': 'CGST', 'amount': 9000.0}, {'label': 'SGST', 'amount': 9000.0}]}
    head, row, quote = _read(exports.documents_csv([(DOCS[0], header, summary), (DOCS[1], {}, {'taxable': 100000.0, 'total': 100000.0})],
                                                   today=date(2026, 11, 20)))
    assert head == exports.DOC_COLUMNS
    assert dict(zip(head, row)) == {
        'Number': 'TF/058', 'Date': '2026-11-18', 'Type': 'Tax Invoice', 'Customer': 'Gear Cutters Ltd', 'Site': 'Hosur plant',
        'GSTIN': '33AAACG0000X1Z5', 'State': 'Tamil Nadu', 'Project': 'PRJ-041', 'Subject': 'Hob arbor set', 'PO number': 'PO 4471',
        'Status': 'Part paid', 'Currency': 'INR', 'Taxable value': '100000.00', 'CGST': '9000.00', 'SGST': '9000.00', 'IGST': '',
        'Total': '118000.00', 'Received': '18000.00', 'Due': '100000.00'}
    assert dict(zip(head, quote))['Received'] == '' and dict(zip(head, quote))['Due'] == ''        # a quotation takes no payments


def test_the_payments_as_they_are_shown():
    rows = [{'date': '2026-10-28', 'customer': {'name': 'Gear Cutters Ltd', 'site': None}, 'project': {'label': 'PRJ-041'},
             'document': {'number': 'TF/058', 'kind': 'Tax Invoice'}, 'note': 'Advance on PI 012', 'method': 'UPI', 'reference': 'UTR 1',
             'currency': 'INR', 'amount': 40000.0, 'credited': None},
            {'date': '2026-08-15', 'customer': {'name': 'Hydro Parts Inc', 'site': None}, 'project': None,
             'document': {'number': 'EX/003', 'kind': 'Export Invoice'}, 'note': '', 'method': 'SWIFT', 'reference': 'FX-55',
             'currency': 'USD', 'amount': 1200.0, 'credited': {'amount': 99840.0, 'currency': 'INR'}}]
    head, advance, foreign = _read(exports.payments_csv(rows))
    assert head == exports.PAYMENT_COLUMNS
    assert advance == ['2026-10-28', 'Gear Cutters Ltd', '', 'PRJ-041', 'TF/058', 'Tax Invoice', 'PI 012', 'UPI', 'UTR 1', 'INR', '40000.00', '40000.00']
    assert foreign[-3:] == ['USD', '1200.00', '99840.00']


def test_the_zip_has_each_pdf_once_by_its_name():
    data = exports.pdfs_zip(DOCS + [DOCS[0]], lambda d: (f"{d['doc_number'].replace('/', '_')}.pdf", b'%PDF-1.4 ' + d['invoice_id'].encode()))
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert names == ['TF_058.pdf', 'TF_Q_041.pdf', 'TF_058 (2).pdf']
