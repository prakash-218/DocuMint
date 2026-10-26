"""
Database-facing helpers for document types: business profile, numbering,
per-document settings and converting one document into another.
"""

import json
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from db import db, DatabaseError
from documents import (DOC_TYPES, DEFAULT_EXPORT_QUOTE_TERMS, DEFAULT_QUOTE_CLOSING, DEFAULT_QUOTE_INTRO, DEFAULT_QUOTE_TERMS,
                       DETAIL_CARRY,
                       default_tax_rate, details_from_form, fiscal_year, format_number, fy_start_month,
                       get_type, load_json, number_format, settings_from_form, suggest_tax_mode)

logger = logging.getLogger(__name__)


class DocumentError(Exception):
    """A document operation failed in a way the user can fix (e.g. duplicate number)."""


# ---------------------------------------------------------------- Profile

def get_org_profile(org_id) -> Tuple[Dict, Dict]:
    """(organization row, parsed profile dict)"""
    row = db.execute_proc_single('sp_get_organization_profile', (org_id,)) or {}
    return row, load_json(row.get('profile'))


def save_org_profile(org_id, profile: Dict):
    db.execute_proc('sp_update_organization_profile', (org_id, json.dumps(profile)), fetch=False)


# ---------------------------------------------------------------- Numbering

def _fy(profile, on) -> str:
    return fiscal_year(on or date.today(), fy_start_month(profile))


def series_key(doc_type: str, profile: Dict) -> str:
    """Which numbering series a type draws from. Export invoices share the tax-invoice
    series by default (GST invoice numbers must be unique across both)."""
    if doc_type == 'export_invoice' and not profile.get('separate_export_series'):
        return 'invoice'
    return doc_type


MAX_SKIPPED_NUMBERS = 1000


def _taken(org_id, doc_type: str, profile: Dict, number: str) -> bool:
    """Numbers typed in by hand (earlier documents, a corrected number) don't move the series on,
    so the series can reach a number that's already used; GST numbers must stay unique."""
    key = series_key(doc_type, profile)
    sharing = [t for t in DOC_TYPES if series_key(t, profile) == key]
    row = db.execute_proc_single('sp_document_number_taken', (org_id, sharing, number)) or {}
    return bool(row.get('taken'))


def preview_number(org_id, doc_type: str, profile: Dict, on: Optional[date] = None) -> str:
    """The number the next document of this type will get (doesn't reserve it)."""
    fy = _fy(profile, on)
    row = db.execute_proc_single('sp_peek_document_number', (org_id, series_key(doc_type, profile), fy)) or {}
    n = int(row.get('number') or 1)
    for _ in range(MAX_SKIPPED_NUMBERS):
        number = format_number(number_format(profile, doc_type), n, fy, on)
        if not _taken(org_id, doc_type, profile, number):
            return number
        n += 1
    return number


def allocate_number(org_id, doc_type: str, profile: Dict, on: Optional[date] = None) -> Tuple[str, str]:
    """Reserve the next free number in the series, skipping any already used. Returns (number, fiscal year)."""
    fy = _fy(profile, on)
    for _ in range(MAX_SKIPPED_NUMBERS):
        row = db.execute_proc_single('sp_next_document_number', (org_id, series_key(doc_type, profile), fy)) or {}
        number = format_number(number_format(profile, doc_type), int(row.get('number') or 1), fy, on)
        if not _taken(org_id, doc_type, profile, number):
            return number, fy
    raise DocumentError('Could not find a free document number; set the next number in Settings → Business profile')


def series_status(org_id, profile: Dict, on: Optional[date] = None) -> List[Dict]:
    """Per type: format, next number and a preview, for the settings page."""
    fy = _fy(profile, on)
    out = []
    for key, doc_type in DOC_TYPES.items():
        shared = series_key(key, profile) != key
        row = db.execute_proc_single('sp_peek_document_number', (org_id, series_key(key, profile), fy)) or {}
        nxt = int(row.get('number') or 1)
        pattern = number_format(profile, key)
        out.append({'key': key, 'label': doc_type.label, 'format': pattern, 'next': nxt, 'shared': shared,
                    'preview': format_number(pattern, nxt, fy, on)})
    return out


def set_next_number(org_id, doc_type: str, profile: Dict, next_number: int, on: Optional[date] = None):
    db.execute_proc('sp_set_document_series', (org_id, series_key(doc_type, profile), _fy(profile, on), next_number),
                    fetch=False)


# ---------------------------------------------------------------- Forms

def form_defaults(doc_type: str, profile: Dict, org: Dict, customer: Optional[Dict] = None,
                  export: bool = False) -> Dict:
    """Initial values for a new document's settings and details. export: priced in a foreign currency."""
    details = {}
    if doc_type == 'quote':
        terms = (profile.get('export_quote_terms') or DEFAULT_EXPORT_QUOTE_TERMS) if export else \
            (profile.get('quote_terms') or DEFAULT_QUOTE_TERMS)
        details = {'intro': profile.get('quote_intro') or DEFAULT_QUOTE_INTRO,
                   'terms': terms,
                   'closing': profile.get('quote_closing') or DEFAULT_QUOTE_CLOSING,
                   'reference': 'Our discussion & enquiry mail'}
    tax_mode = suggest_tax_mode(doc_type, org, customer or {})
    return {
        'tax_mode': tax_mode,
        'tax_rate': default_tax_rate(profile) if tax_mode in ('cgst_sgst', 'igst') else 0,
        'advance_percent': None,
        'advance_basis': profile.get('advance_basis') or 'pre_tax',
        'details': details,
    }


def customer_tax_hints(doc_type: str, org: Dict, customers: List[Dict]) -> Dict[str, str]:
    """customer_id -> suggested tax mode, so the form can switch GST mode as you pick a customer."""
    return {c['customer_id']: suggest_tax_mode(doc_type, org, c) for c in customers}


def _details_with_currency(doc_type: str, form) -> Dict:
    from money import SYMBOLS
    details = details_from_form(doc_type, form)
    currency = (form.get('currency') or '').upper()
    if currency in SYMBOLS:
        details['currency'] = currency
    return details


def apply_document_form(invoice_id, org_id, doc_type: str, form, profile: Dict, *, new: bool,
                        issue_date=None, source_invoice_id=None, current_number=None):
    """Save number, tax/advance settings and details from a create/edit form.

    Documents created before numbering existed have no number; editing them
    keeps it that way unless one is typed in."""
    number = (form.get('doc_number') or '').strip()
    suggested = (form.get('suggested_number') or '').strip()
    fy = _fy(profile, issue_date)

    settings = settings_from_form(form)
    if doc_type == 'quote':
        settings['advance_percent'] = None
    try:
        if new:
            if not number or number == suggested:
                number, fy = allocate_number(org_id, doc_type, profile, issue_date)
            db.execute_proc('sp_init_document', (invoice_id, org_id, doc_type, number, fy, source_invoice_id),
                            fetch=False)
        elif not number:
            if current_number:
                raise DocumentError('Document number is required')
            number = None
        db.execute_proc('sp_update_document_settings', (
            invoice_id, org_id, number, settings['tax_mode'], settings['tax_rate'],
            settings['advance_percent'], settings['advance_basis'],
            json.dumps(_details_with_currency(doc_type, form)),
        ), fetch=False)
    except DatabaseError as e:
        if 'Duplicate entry' in str(e) or '1062' in str(e):
            raise DocumentError(f'{get_type(doc_type).label} number "{number}" is already used')
        raise


def save_details(header: Dict, org_id, details: Dict):
    """Replace a document's details JSON, keeping its number and tax/advance settings."""
    db.execute_proc('sp_update_document_settings', (
        header['invoice_id'], org_id, header.get('doc_number'), header.get('tax_mode') or 'none',
        header.get('tax_rate') or 0, header.get('advance_percent'), header.get('advance_basis') or 'pre_tax',
        json.dumps(details)), fetch=False)


def boxes_from_form(form, lines: List[Dict], box_fields: Optional[List[Dict]] = None) -> List[Dict]:
    """Parse the packing editor: box_<n>_<field key> for each box field, and qty_<n>_<ordinal>."""
    from layout import DEFAULT_BOX_FIELDS
    keys = [f['key'] for f in (box_fields or DEFAULT_BOX_FIELDS)]
    boxes = []
    try:
        count = min(int(form.get('box_count') or 0), 200)
    except ValueError:
        count = 0
    for n in range(1, count + 1):
        if not form.get(f'box_{n}_present'):
            continue   # removed in the editor
        contents = []
        for line in lines:
            raw = (form.get(f'qty_{n}_{line["ordinal"]}') or '').strip()
            try:
                qty = float(raw) if raw else 0.0
            except ValueError:
                qty = 0.0
            if qty > 0:
                contents.append({'ordinal': line['ordinal'], 'qty': qty})
        box = {key: (form.get(f'box_{n}_{key}') or '').strip()[:100] for key in keys}
        box = {k: v for k, v in box.items() if v}
        if contents or box:
            boxes.append({**box, 'contents': contents})
    return boxes


# ---------------------------------------------------------------- Conversion

# Different templates name the same column differently ("price" on a quote,
# "rate" on a GST invoice); conversion treats these as the same field.
FIELD_SYNONYMS = [
    {'price', 'rate', 'unit_price', 'unit_rate', 'rate_per_unit'},
    {'qty', 'quantity', 'nos', 'units'},
    {'description', 'description_of_goods', 'item', 'item_name', 'name', 'particulars'},
    {'hsn', 'hsn_sac', 'hsn_code', 'sac', 'hsn_sac_code'},
    {'item_code', 'part_no', 'part_number', 'code', 'sku'},
    {'per', 'unit', 'uom'},
    {'gst_rate', 'tax', 'tax_rate', 'gst'},
]


def _canonical(name: str) -> str:
    name = (name or '').strip().lower().replace(' ', '_')
    for group in FIELD_SYNONYMS:
        if name in group:
            return sorted(group)[0]
    return name


def _matching_field(value: Dict, fields: List[Dict]) -> Optional[Dict]:
    """The target field for a copied value: same section type, same (or synonymous) name.
    Prefers an exact section-name match, then any section of the same type."""
    name = _canonical(value.get('field_name'))
    kind = value.get('section_type') or 'normal'
    candidates = [f for f in fields if (f.get('section_type') or 'normal') == kind
                  and _canonical(f.get('field_name')) == name and not f.get('calculation_formula')]
    same_section = [f for f in candidates
                    if (f.get('section_name') or '').lower() == (value.get('section_name') or '').lower()]
    return (same_section or candidates or [None])[0]


def _copy_document(source: Dict, source_values: List[Dict], target_type: str, org_id, template_id: str,
                   number: str, fy: str, details: Dict, tax_mode: str, tax_rate, advance_percent, advance_basis) -> str:
    """Create a draft of target_type with source's line items and the given settings. Returns its id.

    Values are copied by (section name, field name, with synonyms), so this works
    across template versions and between templates that name columns differently."""
    from invoice_service import get_template_fields, recalculate_invoice
    from access import get_org_invoice

    result = db.execute_proc('sp_create_invoice', (org_id, source['customer_id'], template_id, None, None))
    new_id = result[0]['invoice_id']
    try:
        target_fields = get_template_fields(template_id)
        for v in source_values:
            if v.get('calculation_formula'):
                continue  # recalculated on the new document
            target = _matching_field(v, target_fields)
            if not target:
                continue
            ordinal = (v.get('value_ordinal') or 0) if target.get('section_type') == 'line_item' else None
            db.execute_proc('sp_save_invoice_value', (
                new_id, target['field_id'], v.get('val_string'), v.get('val_number'),
                v.get('val_date'), v.get('val_boolean'), ordinal), fetch=False)

        db.execute_proc('sp_update_invoice_dates', (new_id, date.today().isoformat(), None), fetch=False)
        db.execute_proc('sp_init_document', (new_id, org_id, target_type, number, fy, source['invoice_id']), fetch=False)
        db.execute_proc('sp_update_document_settings', (
            new_id, org_id, number, tax_mode, tax_rate or 0, advance_percent, advance_basis or 'pre_tax',
            json.dumps(details)), fetch=False)

        header, values = get_org_invoice(new_id, org_id)
        recalculate_invoice(new_id, header, values)
    except Exception:
        logger.exception("Copy of %s failed; removing partial document %s", source['invoice_id'], new_id)
        try:
            db.execute_proc('sp_delete_invoice', (new_id,), fetch=False)
        except DatabaseError:
            pass
        raise
    return new_id


def convert_document(source: Dict, source_values: List[Dict], target_type: str, org_id,
                     profile: Dict, template_id: Optional[str] = None) -> str:
    """
    Create a new draft document of target_type from source (e.g. quote -> proforma).
    The source is marked 'converted' when it's a quote or proforma.
    """
    if target_type == 'export_invoice':
        target_type = 'invoice'
    if target_type not in get_type(source.get('doc_type')).converts_to:
        raise DocumentError(f"A {get_type(source.get('doc_type')).short.lower()} can't be converted to that")
    from layout import template_is_export
    from documents import invoice_kind
    target_type = invoice_kind(target_type, template_is_export(template_id or source['template_id'], org_id))

    number, fy = allocate_number(org_id, target_type, profile, date.today())
    # Carry over the details both types share (PO number, dispatch...), the currency and the tax treatment
    source_details = load_json(source.get('details'))
    keys = {f.key for f in get_type(target_type).details}
    details = {k: v for k, v in source_details.items() if k in keys or k == 'currency'}
    for old, new in DETAIL_CARRY.items():
        if source_details.get(old) and new in keys and not details.get(new):
            details[new] = source_details[old]
    tax_mode = source.get('tax_mode') or 'none'
    if target_type == 'export_invoice' and tax_mode in ('cgst_sgst', 'igst'):
        tax_mode = 'lut'
    new_id = _copy_document(source, source_values, target_type, org_id, template_id or source['template_id'],
                            number, fy, details, tax_mode, source.get('tax_rate'),
                            source.get('advance_percent') if target_type == 'proforma' else None,
                            source.get('advance_basis'))

    if source.get('doc_type') in ('quote', 'proforma'):
        db.execute_proc('sp_update_invoice_status', (source['invoice_id'], 'converted'), fetch=False)
    return new_id


REVISABLE = ('sent', 'accepted', 'declined')


def revision_info(doc: Dict) -> Tuple[str, int]:
    """(base number, revision) of a quote: ('KKR/Q/027/26-27', 2) for '... Rev.2'."""
    details = load_json(doc.get('details'))
    base = details.get('base_number') or doc.get('doc_number') or ''
    return base, int(details.get('revision') or 0)


def revise_document(source: Dict, source_values: List[Dict], org_id) -> str:
    """
    New revision of a sent quote: same number with " Rev.N", everything copied,
    as a draft to edit and send again. The previous version is marked 'revised'.
    """
    if source.get('doc_type') != 'quote':
        raise DocumentError('Only quotations can be revised')
    if source.get('status') not in REVISABLE:
        raise DocumentError('Send the quotation before revising it; a draft can simply be edited')

    base, revision = revision_info(source)
    revision += 1
    details = dict(load_json(source.get('details')), base_number=base, revision=revision)
    new_id = _copy_document(source, source_values, 'quote', org_id, source['template_id'],
                            f'{base} Rev.{revision}', source.get('fiscal_year'), details,
                            source.get('tax_mode') or 'none', source.get('tax_rate'), None, source.get('advance_basis'))
    db.execute_proc('sp_update_invoice_status', (source['invoice_id'], 'revised'), fetch=False)
    return new_id


# ---------------------------------------------------------------- Starter templates

# (name, currency, [(section name, title, type, [(field, label, data_type, currency, formula)])], total field)
STARTER_TEMPLATES = [
    # Letter-style quotation: Sl.no, Description, Price, Qty, Amount.
    # "Unit" is optional; the PDF prints it next to the quantity ("1 set").
    ('Quotation', 'INR', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description', 'string', False, None),
            ('price', 'Price', 'number', True, None),
            ('qty', 'Qty', 'number', False, None),
            ('unit', 'Unit', 'string', False, None),
            ('amount', 'Amount', 'number', True, 'this.price * this.qty'),
        ]),
        ('totals', 'Totals', 'normal', [
            ('total', 'Total', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'total'),
    # Same quotation, plus a cost break-up table: each line says which item it explains.
    # Break-ups are printed under the items and never change the total.
    ('Quotation with cost break-up', 'INR', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description', 'string', False, None),
            ('price', 'Price', 'number', True, None),
            ('qty', 'Qty', 'number', False, None),
            ('unit', 'Unit', 'string', False, None),
            ('amount', 'Amount', 'number', True, 'this.price * this.qty'),
        ]),
        ('breakup', 'Cost break-up', 'line_item', [
            ('item_no', 'Item no.', 'number', False, None),
            ('description', 'Break-up', 'string', False, None),
            ('amount', 'Amount', 'number', True, None),
        ]),
        ('totals', 'Totals', 'normal', [
            ('total', 'Total', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'total'),
    # Proforma: column order of the usual proforma format
    ('Proforma Invoice', 'INR', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description of goods', 'string', False, None),
            ('hsn_sac', 'HSN/SAC', 'string', False, None),
            ('gst_rate', 'GST Rate', 'string', False, None),
            ('qty', 'Quantity', 'number', False, None),
            ('rate', 'Rate', 'number', True, None),
            ('per', 'Per', 'string', False, None),
            ('amount', 'Amount', 'number', True, 'this.rate * this.qty'),
        ]),
        ('totals', 'Totals', 'normal', [
            ('taxable_value', 'Taxable value', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'taxable_value'),
    # Tax invoice: rate before quantity; an item code goes on the first line of the description
    ('Tax Invoice', 'INR', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description of goods', 'string', False, None),
            ('hsn_sac', 'HSN/SAC', 'string', False, None),
            ('gst_rate', 'GST Rate', 'string', False, None),
            ('rate', 'Rate', 'number', True, None),
            ('qty', 'Quantity', 'number', False, None),
            ('per', 'Per', 'string', False, None),
            ('amount', 'Amount', 'number', True, 'this.rate * this.qty'),
        ]),
        ('totals', 'Totals', 'normal', [
            ('taxable_value', 'Taxable value', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'taxable_value'),
    # Quotation priced in a foreign currency for export: HS code and unit on each line
    ('Export Quotation', 'USD', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description', 'string', False, None),
            ('hsn_sac', 'HS code', 'string', False, None),
            ('qty', 'Qty', 'number', False, None),
            ('unit', 'Unit', 'string', False, None),
            ('price', 'Unit price', 'number', True, None),
            ('amount', 'Amount', 'number', True, 'this.price * this.qty'),
        ]),
        ('totals', 'Totals', 'normal', [
            ('total', 'Total', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'total'),
    ('Export Invoice', 'USD', [
        ('items', 'Items', 'line_item', [
            ('description', 'Description of goods', 'string', False, None),
            ('hsn_sac', 'HSN', 'string', False, None),
            ('qty', 'Quantity', 'number', False, None),
            ('rate', 'Rate', 'number', True, None),
            ('amount', 'Total', 'number', True, 'this.rate * this.qty'),
        ]),
        ('totals', 'Totals', 'normal', [
            ('total', 'Total', 'number', True, 'SUM(items.amount)'),
        ]),
    ], 'total'),
]


def create_starter_templates(org_id) -> List[str]:
    """Create the quotation / GST invoice / export invoice templates. Skips names that already exist."""
    existing = {t.get('name') for t in db.execute_proc('sp_list_templates', (org_id, True)) or []}
    created = []
    for name, currency, sections, total_name in STARTER_TEMPLATES:
        if name in existing:
            continue
        row = db.execute_proc_single('sp_create_template', (org_id, name, currency, None, None))
        template_id, version = row['template_id'], row['version']
        total_field_id = None
        for ordinal, (sec_name, title, sec_type, fields) in enumerate(sections, start=1):
            section = db.execute_proc_single('sp_create_section',
                                             (template_id, version, sec_name, title, ordinal, sec_type, None))
            for f_ordinal, (f_name, label, data_type, is_currency, formula) in enumerate(fields, start=1):
                field = db.execute_proc_single('sp_add_template_field', (
                    section['section_id'], f_name, label, data_type, False, is_currency, f_ordinal, formula, None))
                if f_name == total_name and sec_type == 'normal':
                    total_field_id = field['field_id']
        if total_field_id:
            db.execute_proc('sp_set_template_total_field', (template_id, version, total_field_id), fetch=False)
        created.append(name)
    return created
