"""
Several documents at once, from the quotation, proforma and invoice lists: their PDFs in one ZIP, or a CSV with a row
each (number, date, customer and GSTIN, taxable value, CGST/SGST/IGST, total, received, due) for an accountant or for
Tally. And the payments list as a CSV. Only an organization's own documents of the list's kinds go in.
"""

import csv
import io
import zipfile
from datetime import date
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from documents import balance_of, display_number, get_type

# A ZIP is made while you wait: each PDF takes a moment
MAX_PDFS = 60

DOC_COLUMNS = ['Number', 'Date', 'Type', 'Customer', 'Site', 'GSTIN', 'State', 'Project', 'Subject', 'PO number', 'Status',
               'Currency', 'Taxable value', 'CGST', 'SGST', 'IGST', 'Total', 'Received', 'Due']
PAYMENT_COLUMNS = ['Date', 'Customer', 'Site', 'Project', 'Document', 'Type', 'Advance on', 'Method', 'Reference', 'Currency',
                   'Amount', 'Credited (INR)']


def chosen(docs: List[Dict], ids: Iterable[str], types: Tuple[str, ...]) -> List[Dict]:
    """The organization's documents among ids, of these kinds, in the list's order (newest first)."""
    wanted = {str(i) for i in ids}
    return [d for d in docs if str(d['invoice_id']) in wanted and (d.get('doc_type') or 'invoice') in types]


def _number(v) -> str:
    return '' if v is None else f'{float(v):.2f}'


def _csv(columns: List[str], rows: List[List]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(columns)
    writer.writerows(rows)
    return ('﻿' + out.getvalue()).encode('utf-8')              # the BOM: Excel reads ₹ and Tamil names right


def documents_csv(items: List[Tuple[Dict, Dict, Dict]], usual_days: Optional[int] = None, today: Optional[date] = None) -> bytes:
    """A row per document: items are (its list row, its header, its invoice_summary) - the row says where it stands,
    the header has the customer's GSTIN and state, the summary the taxable value and the tax. With credit or debit
    notes among them, a last column says which invoice each note is against. An invoice's Due is after its notes."""
    import projects
    from document_list import short_subject, state
    notes = any(get_type(d.get('doc_type')).adjusts for d, _, _ in items)
    rows = []
    for d, header, s in items:
        kind = get_type(d.get('doc_type'))
        tax = {line['label']: line['amount'] for line in s.get('tax_lines') or []}
        takes = kind.takes_payments or kind.takes_advances
        rows.append([display_number(d), str(d.get('issue_date') or ''), kind.label, d.get('customer_name') or '', d.get('customer_site') or '',
                     header.get('customer_tax_id') or '', header.get('customer_state') or '', projects.project_label(d),
                     short_subject(d.get('subject')), d.get('buyer_order_no') or '',
                     state(d, today or date.today(), usual_days)['tag']['text'], d.get('currency_code') or 'INR',
                     _number(s.get('taxable')), _number(tax.get('CGST')), _number(tax.get('SGST')), _number(tax.get('IGST')),
                     _number(s.get('total', d.get('total_amount'))), _number(d.get('paid_amount') or 0) if takes else '',
                     _number(balance_of(d)) if kind.takes_payments else '']
                    + ([header.get('source_number') or '' if kind.adjusts else ''] if notes else []))
    return _csv(DOC_COLUMNS + (['Against invoice'] if notes else []), rows)


def payments_csv(rows: List[Dict]) -> bytes:
    """The payments list's rows (payments_view.rows), as they're shown."""
    out = []
    for r in rows:
        credited = r.get('credited')
        out.append([r['date'], r['customer']['name'], r['customer'].get('site') or '', (r.get('project') or {}).get('label', ''),
                    r['document']['number'], r['document']['kind'], r['note'].removeprefix('Advance on ') if r['note'].startswith('Advance on ') else '',
                    r['method'], r['reference'], r['currency'], _number(r['amount']),
                    _number(credited['amount']) if credited and credited.get('currency') == 'INR' else
                    (_number(r['amount']) if r['currency'] == 'INR' else '')])
    return _csv(PAYMENT_COLUMNS, out)


def pdfs_zip(docs: List[Dict], pdf: Callable[[Dict], Tuple[str, bytes]]) -> bytes:
    """The documents' PDFs in one ZIP. pdf(doc) -> (file name, bytes); a name used twice gets (2), (3)."""
    out = io.BytesIO()
    seen: Dict[str, int] = {}
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for d in docs:
            name, data = pdf(d)
            seen[name] = seen.get(name, 0) + 1
            if seen[name] > 1:
                stem, _, ext = name.rpartition('.')
                name = f'{stem} ({seen[name]}).{ext}'
            z.writestr(name, data)
    return out.getvalue()
