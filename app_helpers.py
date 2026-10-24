"""Small helpers shared by routes and templates."""

from datetime import date, datetime


def to_date(value):
    """Coerce a date, datetime or 'YYYY-MM-DD...' string to a date (or None)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def invoice_is_overdue(invoice) -> bool:
    """Finalized, unpaid and past its due date."""
    if not invoice or invoice.get('status') != 'pending':
        return False
    due = to_date(invoice.get('due_date'))
    return bool(due and due < date.today())


def describe_audit(log, docs):
    """An audit row in plain words: {'icon', 'title', 'detail', 'invoice_id'}.
    docs: {invoice_id: list row} to name documents and link to them."""
    info = {}
    for part in (log.get('additional_info') or '').split(' | '):
        key, _, value = part.partition(': ')
        if value.strip():
            info[key.strip().lower()] = value.strip()
    table, field = log.get('table_name'), log.get('field_name')
    old, new = log.get('old_value'), log.get('new_value')
    if table == 'invoice':
        doc = docs.get(log.get('record_id')) or {}
        from documents import get_type
        name = f"{get_type(doc.get('doc_type')).label} {doc.get('doc_number') or ''}".strip() if doc else 'Document'
        return {'icon': 'file-text', 'title': name, 'detail': f"{old} → {new}" if field == 'status' else f"{field}: {old} → {new}",
                'sub': info.get('customer', ''), 'invoice_id': log.get('record_id') if doc else None}
    if table == 'payment':
        doc = docs.get(info.get('invoice')) or {}
        try:
            amount = f"{float(new):,.2f}"
        except (TypeError, ValueError):
            amount = new
        return {'icon': 'banknote', 'title': f"Payment of {amount}", 'detail': info.get('method') or '',
                'sub': f"for {doc.get('doc_number') or 'an invoice'}", 'invoice_id': info.get('invoice') if doc else None}
    if table == 'user_organization':
        return {'icon': 'user-cog', 'title': 'Team role changed', 'detail': f"{old} → {new}", 'sub': '', 'invoice_id': None}
    if table == 'customer':
        return {'icon': 'users', 'title': info.get('customer') or 'Customer', 'detail': f"{field}: {old} → {new}", 'sub': '', 'invoice_id': None}
    if table == 'template':
        return {'icon': 'layout-template', 'title': info.get('template') or 'Template', 'detail': f"{field}: {old} → {new}", 'sub': '', 'invoice_id': None}
    return {'icon': 'history', 'title': table or 'Change', 'detail': f"{field}: {old} → {new}", 'sub': '', 'invoice_id': None}
