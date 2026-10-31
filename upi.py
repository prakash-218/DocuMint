"""
Paying by UPI: a QR code any UPI app (GPay, PhonePe, Paytm, a bank's app) scans to pay the exact amount due on a
proforma or a tax invoice, to the UPI ID in the business profile. The code holds a upi://pay link (the NPCI's
format: pa, the UPI ID; pn, who's paid; am, the amount; cu, INR; tn, a note the payer sees), which a phone can also
open as a link. Rupees only; none without a UPI ID, or once nothing is due.
"""

import re
from typing import Dict, Optional
from urllib.parse import quote, urlencode

# name@handle: letters, digits, dots, dashes and underscores, then the bank or app's handle (okhdfcbank, ybl, paytm)
UPI_ID = re.compile(r'[A-Za-z0-9._-]{2,256}@[A-Za-z][A-Za-z0-9.-]{1,63}')


def valid(upi_id) -> bool:
    return bool(UPI_ID.fullmatch((upi_id or '').strip()))


def due(header: Dict, summary: Dict) -> float:
    """What a payment now would be for: a proforma's advance asked (its total when it asks for no part), less what came
    in; an invoice's balance. Nothing for a quotation, a draft's earlier versions, or one already taken forward."""
    from documents import get_type
    kind = get_type(header.get('doc_type'))
    if not (kind.takes_payments or kind.takes_advances) or (header.get('status') or 'draft') in ('revised', 'converted', 'paid'):
        return 0.0
    if kind.takes_advances:
        asked = float((summary.get('advance') or {}).get('amount') or summary.get('total') or 0)
        return round(max(0.0, asked - float(summary.get('paid') or 0)), 2)
    return round(float(summary.get('balance') or 0), 2)


def pay_link(upi_id: str, payee: str, amount: float, note: str) -> str:
    """upi://pay?pa=...&pn=...&am=4500.00&cu=INR&tn=...: what the QR code holds, and what a phone opens."""
    query = {'pa': upi_id.strip(), 'pn': (payee or '')[:50], 'am': f'{amount:.2f}', 'cu': 'INR', 'tn': (note or '')[:50]}
    return 'upi://pay?' + urlencode(query, safe='@', quote_via=quote)            # name@bank as it is: some apps don't read %40


def qr_png(link: str, scale: int = 4) -> str:
    """The link as a QR code: a PNG data: URI, which the PDFs and pages draw as an image."""
    import segno
    return segno.make(link, error='m', micro=False).png_data_uri(scale=scale, border=2)


def payment(header: Dict, summary: Dict, profile: Dict) -> Optional[Dict]:
    """{'upi_id', 'amount', 'link', 'qr'} to pay what's due on this document by UPI, or None: no UPI ID in the profile,
    not in rupees, or nothing due."""
    from documents import display_number
    upi_id = (profile.get('upi_id') or '').strip()
    currency = (header.get('currency_code') or 'INR').upper()
    amount = due(header, summary)
    if not valid(upi_id) or currency != 'INR' or amount <= 0:
        return None
    link = pay_link(upi_id, header.get('organization_name') or '', amount, display_number(header))
    return {'upi_id': upi_id, 'amount': amount, 'link': link, 'qr': qr_png(link)}
