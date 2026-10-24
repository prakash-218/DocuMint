"""
Project activity and notifications.

record() writes an event (the project's activity feed) and notifies the org's owners
and admins, except whoever did it. Never lets a failure here break the action itself.
"""

import logging
from typing import Optional

from flask import g, has_request_context, url_for

from db import db, DatabaseError

logger = logging.getLogger(__name__)


def _actor():
    if has_request_context():
        return (getattr(g, 'current_user', None) or {}).get('user_id')
    return None


def record(kind: str, title: str, project_id: Optional[str] = None, link: Optional[str] = None,
           body: Optional[str] = None, org_id: Optional[str] = None, actor: Optional[str] = 'auto',
           notify: bool = True):
    org_id = org_id or (getattr(g, 'current_org_id', None) if has_request_context() else None)
    if not org_id:
        return None
    try:
        row = db.execute_proc_single('sp_record_event', (org_id, project_id, kind, title, body, link,
                                                          _actor() if actor == 'auto' else actor, notify))
        return (row or {}).get('event_id')
    except DatabaseError:
        logger.exception('Could not record event %s', kind)
        return None


def document_event(kind: str, header: dict, verb: str, project_id: Optional[str] = None):
    """e.g. document_event('document_sent', header, 'marked as sent')"""
    from documents import display_number, get_type
    label = get_type(header.get('doc_type')).label
    number = display_number(header) or 'draft'
    record(kind, f'{label} {number} {verb}', project_id=project_id or header.get('project_id'),
           link=url_for('invoices_bp.view_invoice', invoice_id=header['invoice_id']),
           body=header.get('customer_name'))


def unread_count(user_id, org_id) -> int:
    try:
        return int((db.execute_proc_single('sp_count_unread_notifications', (user_id, org_id)) or {}).get('n') or 0)
    except DatabaseError:
        return 0
