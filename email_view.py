"""
The emails synced from the company mailboxes, for the React app (frontend/src/islands/emails/): the inbox (threads not
in a project yet, or all of them) and a thread with its messages and files. Moving a thread to a project still posts
to emails_bp.link_project; Sync now posts to emails_bp.sync_now.
"""

from typing import Callable, Dict, Optional


def inbox(org_id, show: str, role: str, url: Callable) -> Dict:
    from db import db
    from pagination import Page
    from projects import project_label
    unlinked = show == 'unlinked'
    count = db.execute_proc_single('sp_count_email_threads', (org_id, None, None, unlinked)) or {}
    page = Page.from_count(count.get('n'))
    threads = db.execute_proc('sp_list_email_threads', (org_id, None, None, unlinked, page.per_page, page.offset)) or []
    accounts = db.execute_proc('sp_list_email_accounts', (org_id,)) or []
    return {
        'title': 'Emails',
        'accounts': ' · '.join(a['address'] for a in accounts) if accounts else 'No mailboxes synced yet',
        'problems': [f"{a['address']}: {a['last_error']}" for a in accounts if a.get('last_error')],
        'sync': url('emails_bp.sync_now') if role in ('owner', 'admin') else None,
        'filters': [{'label': 'Not in a project', 'href': url('emails_bp.inbox'), 'active': unlinked},
                    {'label': 'All', 'href': url('emails_bp.inbox', show='all'), 'active': not unlinked}],
        'threads': [{'id': str(t['thread_id']), 'url': url('emails_bp.thread', thread_id=t['thread_id']),
                     'subject': t.get('subject') or '', 'count': t.get('message_count') or 0,
                     'from': t.get('last_from_name') or t.get('last_from_address') or '',
                     'customer': t.get('customer_name') or '', 'project': project_label(t) if t.get('project_no') else '',
                     'files': t.get('file_count') or 0, 'snippet': t.get('snippet') or '', 'when': t.get('last_message_at')}
                    for t in threads],
        'page': page.json('threads'),
        'empty': 'Nothing to sort' if unlinked else 'No emails yet',
    }


LINKED_BY = {'number': 'project number in the subject', 'document': 'document number in the subject'}


def thread(org_id, thread_id: str, url: Callable) -> Optional[Dict]:
    """A thread and its messages, oldest first, with each message's files; None when it isn't this organization's."""
    from db import db
    from projects import human_size, project_label
    result = db.execute_proc('sp_get_email_thread', (thread_id, org_id))
    if not result:
        return None
    sets = result if isinstance(result[0], list) else [result]
    t, messages = sets[0][0], (sets[1] if len(sets) > 1 else [])
    files: Dict[str, list] = {}
    for f in sets[2] if len(sets) > 2 else []:
        files.setdefault(str(f['message_id']), []).append(
            {'name': f['file_name'], 'url': url('emails_bp.download', file_id=f['file_id']), 'size': human_size(f.get('file_size'))})
    project = ({'id': str(t['project_id']), 'label': project_label(t), 'title': t.get('project_title') or '',
                'url': url('projects_bp.view_project', project_id=t['project_id'])} if t.get('project_id') else None)
    linked_by = t.get('linked_by')
    return {
        'title': t.get('subject') or '(no subject)',
        'count': t.get('message_count') or len(messages),
        'customer': {'id': str(t['customer_id']), 'name': t.get('customer_name') or '',
                     'url': url('customers_bp.view_customer', customer_id=t['customer_id'])} if t.get('customer_id') else None,
        'project': project,
        'back': project['url'] if project else url('emails_bp.inbox'),
        'messages': [{'id': str(m['message_id']), 'from_name': m.get('from_name') or '', 'from_address': m.get('from_address') or '',
                      'to': m.get('to_addresses') or '', 'cc': m.get('cc_addresses') or '', 'sent_at': m.get('sent_at'),
                      'body': m.get('body_text') or '', 'outgoing': m.get('direction') == 'out',
                      'files': files.get(str(m['message_id']), [])} for m in messages],
        'link': {'action': url('emails_bp.link_project', thread_id=thread_id), 'options': url('projects_bp.picker_options'),
                 'auto': f"Linked automatically ({LINKED_BY.get(linked_by, linked_by)})." if linked_by and linked_by != 'manual' else ''},
    }
