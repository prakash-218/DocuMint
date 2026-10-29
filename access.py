"""
Org-scoped record lookups.

Most detail procedures (sp_get_invoice_details, sp_get_customer_details,
sp_get_template_fields, ...) look records up by ID alone, so every route that
takes an ID from the URL or form must confirm the record belongs to the
caller's organization before reading or changing it.
"""

from urllib.parse import urlparse
from flask import g, has_request_context, request, url_for
from db import db, DatabaseError
import doc_urls

db.add_row_observer(doc_urls.remember)


def fetch_invoice(invoice_id):
    """Return (header, values) for an invoice, or (None, []) if it doesn't exist."""
    try:
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
    except DatabaseError:
        return None, []
    if not result:
        return None, []
    if isinstance(result[0], list):
        header = result[0][0] if result[0] else None
        values = result[1] if len(result) > 1 else []
    else:
        # Only the header result set came back (invoice has no values yet)
        header = result[0]
        values = []
    return header, values or []


def get_org_invoice(invoice_id, org_id):
    """Like fetch_invoice, but returns (None, []) unless the invoice belongs to org_id."""
    header, values = fetch_invoice(invoice_id)
    if not header or str(header.get('org_id')) != str(org_id):
        return None, []
    if has_request_context() and not hasattr(g, 'nav_doc_type'):
        g.nav_doc_type = header.get('doc_type')   # highlights the right sidebar entry
    return header, values


def get_customer_invoice(invoice_id, customer_id):
    """Invoice as seen from the customer portal: must be theirs and not a draft."""
    header, values = fetch_invoice(invoice_id)
    if (not header
            or str(header.get('customer_id')) != str(customer_id)
            or header.get('status') in (None, 'draft')):
        return None, []
    return header, values


def get_org_customer(customer_id, org_id):
    """Return (customer, contacts) if the customer belongs to org_id, else (None, [])."""
    result = db.execute_proc('sp_get_customer_details', (customer_id,))
    if not result:
        return None, []
    if isinstance(result[0], list):
        customer = result[0][0] if result[0] else None
        contacts = result[1] if len(result) > 1 else []
    else:
        customer = result[0]
        contacts = []
    if not customer or str(customer.get('org_id')) != str(org_id):
        return None, []
    return customer, contacts or []


def get_org_template(template_id, org_id):
    """Return the latest-version template row for template_id if it belongs to org_id."""
    templates = db.execute_proc('sp_list_templates', (org_id, True)) or []
    matches = [t for t in templates if t.get('template_id') == template_id]
    if not matches:
        return None
    return max(matches, key=lambda t: t.get('latest_version') or 0)


def get_template_ids(template_id):
    """Return (section_ids, field_ids) in the latest version of a template."""
    try:
        fields = db.execute_proc('sp_get_template_fields', (template_id,)) or []
    except DatabaseError:
        return set(), set()
    return {f['section_id'] for f in fields}, {f['field_id'] for f in fields}


def safe_referrer(fallback_endpoint, **kwargs):
    """request.referrer if it points back at this site, otherwise the fallback URL."""
    ref = request.referrer
    if ref:
        parsed = urlparse(ref)
        if not parsed.netloc or parsed.netloc == request.host:
            return ref
    return url_for(fallback_endpoint, **kwargs)


def back_to_page(endpoint, **kwargs):
    """The page a form goes back to (a project, customer or document): its classic version when that's where the form
    was sent from, else the page."""
    page = url_for(endpoint, **kwargs)
    ref = urlparse(request.referrer or '')
    if (not ref.netloc or ref.netloc == request.host) and ref.path.rstrip('/') == f'{page}/classic':
        return url_for(f'{endpoint}_classic', **kwargs)
    return page
