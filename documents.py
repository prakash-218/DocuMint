"""
Document types: quotation, proforma invoice, tax invoice and export invoice.

All four are rows in the invoice table, told apart by doc_type. Each type has
its own statuses, numbering series (per financial year) and header details.
Quotes and proformas use statuses the revenue reports don't count
('sent', 'accepted', ...), so only real invoices show up as revenue.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from app_helpers import to_date


@dataclass(frozen=True)
class DetailField:
    key: str
    label: str
    kind: str = 'text'          # text | date | textarea
    placeholder: str = ''
    group: str = ''             # '' = always shown; otherwise folded under DETAIL_GROUPS[group]


@dataclass(frozen=True)
class DocType:
    key: str
    label: str                  # printed title, e.g. "Proforma Invoice"
    short: str                  # nav / badges, e.g. "Proforma"
    plural: str
    statuses: Tuple[str, ...]
    sent_status: str            # status a draft moves to when finalized
    default_format: str
    converts_to: Tuple[str, ...] = ()
    takes_payments: bool = False
    takes_advances: bool = False   # money received before the invoice, applied to it later (advances.py)
    counts_as_revenue: bool = False
    details: Tuple[DetailField, ...] = field(default_factory=tuple)
    icon: str = 'file-text'
    # A purchase: to a supplier (a company marked supplier), not a customer; outside every sale and its money
    purchase: bool = False
    party: str = 'Customer'                 # who it's to, in the editor and on its page


_ORDER = (
    DetailField('buyer_order_no', "Buyer's order no."),
    DetailField('buyer_order_date', "Buyer's order date", 'date'),
)
_DISPATCH = (
    DetailField('dc_ref', 'DC ref', group='dispatch'),
    DetailField('delivery_date', 'Delivery date', 'date', group='dispatch'),
    DetailField('despatched_through', 'Despatched through', placeholder='By road / By air', group='dispatch'),
    DetailField('destination', 'Destination', group='dispatch'),
    DetailField('terms_of_delivery', 'Terms of delivery', placeholder='FOB Chennai', group='dispatch'),
)

DETAIL_GROUPS = {'export': 'Export terms', 'dispatch': 'Dispatch', 'shipping': 'Shipping & packing',
                 'letter': 'Opening & closing text', 'delivery': 'Delivery address'}

# Details that mean the same thing under another name on the next document (quote -> export invoice)
DETAIL_CARRY = {'incoterms': 'terms_of_delivery', 'final_destination': 'destination'}

DOC_TYPES: Dict[str, DocType] = {
    'quote': DocType(
        key='quote', label='Quotation', short='Quote', plural='Quotations', icon='file-pen-line',
        statuses=('draft', 'sent', 'accepted', 'declined', 'revised', 'converted'),
        sent_status='sent',
        default_format='Q/{num:03}/{fy}',
        converts_to=('proforma', 'invoice'),
        details=(
            DetailField('kind_attn', 'Kind attn', placeholder='Mr. A. Kumar'),
            DetailField('subject', 'Subject', placeholder='Quotation for drill jig'),
            DetailField('reference', 'Ref', placeholder='Your enquiry dated ...'),
            DetailField('incoterms', 'Incoterms', placeholder='FOB Chennai', group='export'),
            DetailField('port_of_loading', 'Port of loading', placeholder='Chennai, India', group='export'),
            DetailField('port_of_discharge', 'Port of discharge', placeholder='Savannah, USA', group='export'),
            DetailField('final_destination', 'Final destination', placeholder='United States', group='export'),
            DetailField('notes', 'Notes & scope', 'textarea', placeholder='Printed below the items'),
            DetailField('terms', 'Terms & conditions', 'textarea', placeholder='One per line'),
            DetailField('intro', 'Opening paragraph', 'textarea', group='letter'),
            DetailField('closing', 'Closing paragraph', 'textarea', group='letter'),
        ),
    ),
    'proforma': DocType(
        key='proforma', label='Proforma Invoice', short='Proforma', plural='Proforma invoices', icon='file-clock',
        statuses=('draft', 'sent', 'revised', 'converted'),
        sent_status='sent',
        default_format='PI {num:03}({fy})',
        converts_to=('invoice',),
        takes_advances=True,
        details=_ORDER + _DISPATCH,
    ),
    'invoice': DocType(
        key='invoice', label='Tax Invoice', short='Invoice', plural='Invoices', icon='file-text',
        statuses=('draft', 'pending', 'paid'),
        sent_status='pending',
        default_format='{num:03}',
        takes_payments=True, counts_as_revenue=True,
        details=_ORDER + _DISPATCH,
    ),
    'export_invoice': DocType(
        key='export_invoice', label='Export Invoice', short='Export', plural='Export invoices', icon='plane',
        statuses=('draft', 'pending', 'paid'),
        sent_status='pending',
        default_format='{num:03}',
        takes_payments=True, counts_as_revenue=True,
        details=_ORDER + _DISPATCH + (
            DetailField('packing_list_no', 'Packing list no.', group='shipping'),
            DetailField('packing_list_date', 'Packing list date', 'date', group='shipping'),
            DetailField('net_weight', 'Net weight', placeholder='39 kg', group='shipping'),
            DetailField('gross_weight', 'Gross weight', placeholder='42 kg', group='shipping'),
            DetailField('packages', 'No. of packages', placeholder='2 wooden boxes', group='shipping'),
            DetailField('package_dimensions', 'Package dimensions', placeholder='60 x 40 x 30 cm', group='shipping'),
            DetailField('marks', 'Marks & nos.', placeholder='ACME/1-2', group='shipping'),
        ),
    ),
}

# Not a sale: what we buy, sent to a supplier (the usual details: order type, their quotation, delivery, payment terms)
DOC_TYPES['purchase_order'] = DocType(
    key='purchase_order', label='Purchase Order', short='PO', plural='Purchase orders', icon='shopping-cart',
    statuses=('draft', 'sent', 'confirmed', 'received', 'cancelled'),
    sent_status='sent',
    default_format='{num:03}',
    purchase=True, party='Supplier',
    details=(
        DetailField('order_type', 'Order type', placeholder='Bought-out'),
        DetailField('supplier_ref', 'Their quotation', placeholder='Q-118 dated 12 Oct'),
        DetailField('delivery', 'Delivery', placeholder='Immediate'),
        DetailField('payment_terms', 'Payment terms', placeholder='Against delivery'),
        DetailField('notes', 'Notes', 'textarea', placeholder='Printed below the items'),
        DetailField('deliver_to', 'Deliver to', 'textarea', placeholder='Our works, when it isn\'t the address on top',
                    group='delivery'),
    ),
)
SALES_TYPES = ('quote', 'proforma', 'invoice', 'export_invoice')
PURCHASE_TYPES = ('purchase_order',)

DEFAULT_TYPE = 'invoice'

# Types you pick when creating or converting. An invoice made with an export
# template is stored and printed as 'export_invoice' (LUT, shipping, packing list).
CHOOSABLE = ('quote', 'proforma', 'invoice', 'purchase_order')


def invoice_kind(doc_type: str, export: bool) -> str:
    """'invoice' or 'export_invoice' for an invoice, by its template; other types unchanged."""
    if doc_type in ('invoice', 'export_invoice'):
        return 'export_invoice' if export else 'invoice'
    return doc_type

TAX_MODES = {
    'none': 'No tax',
    'cgst_sgst': 'CGST + SGST (same state)',
    'igst': 'IGST (other state)',
    'lut': 'Export under LUT (no tax)',
}

DEFAULT_QUOTE_TERMS = (
    'Taxes: 18% GST\n'
    'Offer validity – 30 days\n'
    'Delivery: (4-6) weeks from the date of PO\n'
    'Warranty – 6 months from the date of invoice & misuse does not cover under warranty'
)
DEFAULT_EXPORT_QUOTE_TERMS = (
    'Prices: FOB Chennai, in USD\n'
    'Payment: 100% advance by wire transfer (T/T)\n'
    'Delivery: (4-6) weeks from receipt of PO and advance\n'
    'Packing: Seaworthy wooden boxes, included\n'
    'Offer validity – 30 days\n'
    'Warranty – 6 months from the date of shipment'
)
DEFAULT_QUOTE_INTRO = ('We thankfully acknowledge the receipt of your above enquiry and are pleased to '
                       'submit our competitive quote for the same.')
DEFAULT_QUOTE_CLOSING = ('We hope you will find our offer most suitable and in line with your requirements and '
                         'if you require any further information, please feel free to contact us.\n\n'
                         'Thanking you and we look forward to receive your valued order at the earliest.')


def get_type(key: Optional[str]) -> DocType:
    return DOC_TYPES.get(key or DEFAULT_TYPE, DOC_TYPES[DEFAULT_TYPE])


# ---------------------------------------------------------------- Profile

def load_json(value) -> dict:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def fy_start_month(profile: dict) -> int:
    try:
        month = int(profile.get('fy_start_month') or 4)
    except (TypeError, ValueError):
        month = 4
    return month if 1 <= month <= 12 else 4


def number_format(profile: dict, doc_type: str) -> str:
    formats = profile.get('number_formats') or {}
    return formats.get(doc_type) or get_type(doc_type).default_format


# ---------------------------------------------------------------- Numbering

def fiscal_year(on: Optional[date] = None, start_month: int = 4) -> str:
    """Indian-style financial year label: Apr 2026 - Mar 2027 -> '26-27'.
    With start_month=1 it's just the calendar year, '2026'."""
    on = to_date(on) or date.today()
    if start_month == 1:
        return str(on.year)
    first = on.year if on.month >= start_month else on.year - 1
    return f'{first % 100:02d}-{(first + 1) % 100:02d}'


_TOKEN = re.compile(r'\{(num|fy|yyyy|yy)(?::(0?\d+))?\}')


def format_number(pattern: str, num: int, fy: str, on: Optional[date] = None) -> str:
    """Fill a numbering pattern. Tokens: {num} / {num:03} (zero-padded), {fy}, {yyyy}, {yy}."""
    on = to_date(on) or date.today()

    def fill(m):
        token, width = m.group(1), m.group(2)
        if token == 'num':
            return str(num).zfill(int(width)) if width else str(num)
        if token == 'fy':
            return fy
        if token == 'yyyy':
            return str(on.year)
        return f'{on.year % 100:02d}'

    return _TOKEN.sub(fill, pattern or '{num}')


def display_number(doc: dict) -> str:
    """The number shown to people: the document's own number, or a fallback for older rows."""
    if doc.get('doc_number'):
        return doc['doc_number']
    return 'INV-' + (doc.get('invoice_id') or '')[:8].upper()


# ---------------------------------------------------------------- Tax

def _norm(text) -> str:
    return re.sub(r'[^a-z]', '', (text or '').lower())


def is_india(country) -> bool:
    return _norm(country) in ('india', 'in', 'ind', 'bharat')


# The GST state codes: a GSTIN's first two digits are the state it's registered in. 25 (Daman and Diu) was merged into
# 26, and Andhra Pradesh has the old 28 and the new 37, so they compare by name.
GST_STATES = {
    '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab', '04': 'Chandigarh', '05': 'Uttarakhand',
    '06': 'Haryana', '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh', '10': 'Bihar', '11': 'Sikkim',
    '12': 'Arunachal Pradesh', '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram', '16': 'Tripura', '17': 'Meghalaya',
    '18': 'Assam', '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha', '22': 'Chhattisgarh', '23': 'Madhya Pradesh',
    '24': 'Gujarat', '25': 'Dadra and Nagar Haveli and Daman and Diu', '26': 'Dadra and Nagar Haveli and Daman and Diu',
    '27': 'Maharashtra', '28': 'Andhra Pradesh', '29': 'Karnataka', '30': 'Goa', '31': 'Lakshadweep', '32': 'Kerala',
    '33': 'Tamil Nadu', '34': 'Puducherry', '35': 'Andaman and Nicobar Islands', '36': 'Telangana', '37': 'Andhra Pradesh',
    '38': 'Ladakh', '97': 'Other Territory',
}


def gstin_state(gstin) -> str:
    """The state a GSTIN is registered in, from its first two digits ('33...' is Tamil Nadu); '' when it isn't a GSTIN."""
    code = re.sub(r'[\s-]', '', gstin or '').upper()
    return GST_STATES.get(code[:2], '') if re.fullmatch(r'\d{2}[0-9A-Z]{13}', code) else ''


def tax_suggestion(doc_type: str, org: dict, customer: dict) -> dict:
    """{'mode', 'why'}: the usual GST treatment from where the buyer is, and why in a few words ('Karnataka GSTIN, another
    state'; '' when it's only a guess). When both sides have a GSTIN, the states are its first two digits; otherwise
    they're the addresses' states. Only for GST-registered businesses (a GSTIN in the profile); everyone else defaults
    to no tax."""
    profile = load_json(org.get('profile'))
    if not profile.get('gstin') or doc_type == 'quote':
        # Quotations state the GST rate in their terms instead of adding tax rows. A purchase order carries the GST its
        # supplier will charge: from the supplier's GSTIN, as an invoice's from the customer's
        return {'mode': 'none', 'why': ''}
    customer_country = (customer.get('country') or customer.get('customer_country') or '').strip()
    if doc_type == 'export_invoice':
        return {'mode': 'lut', 'why': 'An export invoice'}
    if customer_country and not is_india(customer_country):
        return {'mode': 'lut', 'why': f'{customer_country}, outside India'}
    ours, theirs = gstin_state(profile.get('gstin')), gstin_state(customer.get('tax_id') or customer.get('customer_tax_id'))
    if ours and theirs:
        return {'mode': 'cgst_sgst', 'why': f'{theirs} GSTIN'} if ours == theirs else             {'mode': 'igst', 'why': f'{theirs} GSTIN, another state'}
    org_state = (org.get('state') or org.get('organization_state') or '').strip()
    customer_state = (customer.get('state') or customer.get('customer_state') or '').strip()
    if org_state and customer_state and _norm(org_state) != _norm(customer_state):
        return {'mode': 'igst', 'why': f'{customer_state}, another state'}
    return {'mode': 'cgst_sgst', 'why': customer_state if org_state else ''}


TAX_SHORT = {'cgst_sgst': 'CGST + SGST', 'igst': 'IGST', 'lut': 'no GST under LUT'}


def tax_note(suggestion: dict) -> str:
    """A tax_suggestion in words, as the editor and the customer page say it: 'Tamil Nadu GSTIN, so CGST + SGST', or just
    'IGST' without a reason; '' for no tax."""
    short = TAX_SHORT.get(suggestion['mode'], '')
    return f"{suggestion['why']}, so {short}" if short and suggestion['why'] else short


def suggest_tax_mode(doc_type: str, org: dict, customer: dict) -> str:
    """The usual GST treatment for this buyer (tax_suggestion's mode)."""
    return tax_suggestion(doc_type, org, customer)['mode']


def default_tax_rate(profile: dict) -> float:
    try:
        return float(profile.get('default_gst_rate', 18))
    except (TypeError, ValueError):
        return 18.0


# ---------------------------------------------------------------- Form handling

def details_from_form(doc_type: str, form) -> dict:
    """Collect the type's detail fields from a submitted form (empty values dropped)."""
    details = {}
    for f in get_type(doc_type).details:
        value = (form.get(f'detail_{f.key}') or '').strip()
        if value:
            details[f.key] = value
    return details


def settings_from_form(form) -> dict:
    """Tax and advance settings from a submitted form, validated."""
    tax_mode = form.get('tax_mode') or 'none'
    if tax_mode not in TAX_MODES:
        tax_mode = 'none'

    def number(name, default=None, lo=0.0, hi=100.0):
        raw = (form.get(name) or '').strip()
        if raw == '':
            return default
        try:
            value = float(raw)
        except ValueError:
            return default
        return min(max(value, lo), hi)

    tax_rate = number('tax_rate', 0.0) if tax_mode in ('cgst_sgst', 'igst') else 0.0
    advance_percent = number('advance_percent')
    advance_basis = form.get('advance_basis') if form.get('advance_basis') in ('pre_tax', 'total') else 'pre_tax'
    return {'tax_mode': tax_mode, 'tax_rate': tax_rate,
            'advance_percent': advance_percent if advance_percent else None,
            'advance_basis': advance_basis}


def status_label(doc: dict) -> str:
    return (doc.get('status') or 'draft').replace('_', ' ')


def detail_items(doc: dict) -> List[Tuple[str, str]]:
    """(label, value) pairs of the filled-in details, in the type's order."""
    details = load_json(doc.get('details'))
    out = []
    for f in get_type(doc.get('doc_type')).details:
        if details.get(f.key) and f.kind != 'textarea':
            out.append((f.label, details[f.key]))
    return out


def sum_by_currency(docs, amount) -> Dict[str, float]:
    """{currency: total} of amount(doc) over docs, largest first. Never adds ₹ to $."""
    totals: Dict[str, float] = {}
    for d in docs:
        value = amount(d)
        if value:
            cur = d.get('currency_code') or 'USD'
            totals[cur] = totals.get(cur, 0.0) + float(value)
    return dict(sorted(totals.items(), key=lambda kv: -kv[1]))


def balance_of(doc) -> float:
    return max(float(doc.get('total_amount') or 0) - float(doc.get('paid_amount') or 0), 0.0)
