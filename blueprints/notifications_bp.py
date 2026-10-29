"""Notifications for owners and admins: what happened on projects."""

from flask import Blueprint, abort, g, redirect, url_for

from access import safe_referrer
from auth import require_org
from db import db

notifications_bp = Blueprint('notifications_bp', __name__)


def _user_id():
    return g.current_user['user_id']


@notifications_bp.route('/')
@require_org
def index():
    """Notifications, in the React app (notifications_view.build)."""
    import nav
    return nav.spa('Notifications', 'list')


@notifications_bp.route('/<notification_id>/open')
@require_org
def open_notification(notification_id):
    """Mark as read and go where it points."""
    row = db.execute_proc_single('sp_get_notification', (notification_id, _user_id()))
    if not row or str(row['org_id']) != str(g.current_org_id):
        abort(404)
    db.execute_proc('sp_mark_notifications_read', (_user_id(), g.current_org_id, notification_id), fetch=False)
    link = row.get('link') or ''
    return redirect(link if link.startswith('/') else url_for('notifications_bp.index'))


@notifications_bp.route('/read', methods=['POST'])
@require_org
def mark_all_read():
    db.execute_proc('sp_mark_notifications_read', (_user_id(), g.current_org_id, None), fetch=False)
    return redirect(safe_referrer('notifications_bp.index'))
