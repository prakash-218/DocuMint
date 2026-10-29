"""
Notifications, for the React app (frontend/src/islands/notifications/): what happened on projects, unread first or all.
Opening one still goes through notifications_bp.open_notification (marks it read); Mark all read posts to mark_all_read.
"""

from typing import Callable, Dict


def build(user_id, org_id, unread_only: bool, url: Callable) -> Dict:
    from db import db
    from pagination import Page
    from projects import project_label
    count = db.execute_proc_single('sp_count_notifications', (user_id, org_id, unread_only)) or {}
    page = Page.from_count(count.get('n'))
    items = db.execute_proc('sp_list_notifications', (user_id, org_id, page.per_page, unread_only, page.offset)) or []

    def sub(n):
        parts = [f"{project_label(n)} · {n.get('project_title') or ''}"] if n.get('project_no') else []
        parts += [n['body']] if n.get('body') else []
        text = ' · '.join(parts)
        return text + (f" · by {n['actor_email']}" if n.get('actor_email') else '')

    return {
        'title': 'Notifications',
        'unread_only': unread_only,
        'mark_read': url('notifications_bp.mark_all_read') if items and unread_only else None,
        'filters': [{'label': 'Unread', 'href': url('notifications_bp.index'), 'active': unread_only},
                    {'label': 'All', 'href': url('notifications_bp.index', show='all'), 'active': not unread_only}],
        'items': [{'id': str(n['notification_id']), 'url': url('notifications_bp.open_notification', notification_id=n['notification_id']),
                   'title': n.get('title') or '', 'sub': sub(n), 'kind': n.get('kind') or '', 'unread': not n.get('read_at'),
                   'when': n.get('created_at')} for n in items],
        'page': page.json(),
        'empty': 'All caught up' if unread_only else 'No notifications yet',
    }
