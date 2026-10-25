"""Emails synced from the company mailboxes, grouped in threads and attached to projects."""

import io
import logging

from flask import Blueprint, abort, flash, g, redirect, render_template, request, send_file, url_for

from auth import get_current_org_role, require_org
from db import DatabaseError, db

logger = logging.getLogger(__name__)
emails_bp = Blueprint('emails_bp', __name__)

READERS = ('owner', 'admin', 'member')          # viewers don't see mail
INLINE = {'application/pdf', 'image/png', 'image/jpeg', 'image/webp', 'image/gif'}


def _guard():
    if get_current_org_role() not in READERS:
        abort(403)


@emails_bp.route('/')
@require_org
def inbox():
    _guard()
    from pagination import Page
    show = request.args.get('show', 'unlinked')
    unlinked = show == 'unlinked'
    count = db.execute_proc_single('sp_count_email_threads', (g.current_org_id, None, None, unlinked)) or {}
    page = Page.from_count(count.get('n'))
    threads = db.execute_proc('sp_list_email_threads', (g.current_org_id, None, None, unlinked,
                                                         page.per_page, page.offset)) or []
    accounts = db.execute_proc('sp_list_email_accounts', (g.current_org_id,)) or []
    return render_template('emails/inbox.html', threads=threads, page=page, show=show, accounts=accounts,
                           current_org_role=get_current_org_role())


@emails_bp.route('/<thread_id>')
@require_org
def thread(thread_id):
    _guard()
    result = db.execute_proc('sp_get_email_thread', (thread_id, g.current_org_id))
    if not result:
        abort(404)
    sets = result if isinstance(result[0], list) else [result]
    thread, messages = sets[0][0], (sets[1] if len(sets) > 1 else [])
    files = sets[2] if len(sets) > 2 else []
    by_message = {}
    for f in files:
        by_message.setdefault(f['message_id'], []).append(f)
    projects = db.execute_proc('sp_list_projects', (g.current_org_id, thread.get('customer_id'), 'open')) or []
    if not projects and thread.get('customer_id'):
        projects = db.execute_proc('sp_list_projects', (g.current_org_id, None, 'open')) or []
    return render_template('emails/thread.html', thread=thread, messages=messages, files=by_message,
                           projects=projects, current_org_role=get_current_org_role())


@emails_bp.route('/<thread_id>/project', methods=['POST'])
@require_org
def link_project(thread_id):
    _guard()
    import projects
    org_id = g.current_org_id
    project_id = request.form.get('project_id') or None
    result = db.execute_proc('sp_get_email_thread', (thread_id, org_id))
    if not result:
        abort(404)
    current = (result[0] if isinstance(result[0], list) else result)[0]
    back = redirect(url_for('emails_bp.thread', thread_id=thread_id))
    if (current.get('project_id') or None) == project_id:
        return back
    try:
        db.execute_proc('sp_set_thread_project', (thread_id, org_id, project_id, 'manual'), fetch=False)
        removed = projects.remove_email_files(org_id, current['project_id'], thread_id) if current.get('project_id') else 0
        counts = projects.add_email_files(org_id, project_id, thread_id) if project_id else {}
    except DatabaseError as e:
        logger.exception('Could not move thread %s to project %s', thread_id, project_id)
        flash(str(e), 'error')
        return back
    if project_id:
        import activity
        activity.record('email_received', f"Email thread added: {current.get('subject') or 'Email'}", project_id=project_id,
                        link=url_for('emails_bp.thread', thread_id=thread_id), notify=False)
        flash('Added to the project' + _files_note(counts), 'success')
    else:
        flash('Removed from the project' + (f', with the {removed} file{"" if removed == 1 else "s"} it had added'
                                            if removed else ''), 'success')
    return back


def _files_note(counts) -> str:
    added, dupes = counts.get('added', 0), counts.get('duplicates', 0)
    if not added and not dupes:
        return ''
    note = f", with {added} file{'' if added == 1 else 's'}" if added else ', no new files'
    return note + (f" ({dupes} already there)" if dupes else '')


@emails_bp.route('/files/<file_id>')
@require_org
def download(file_id):
    _guard()
    f = db.execute_proc_single('sp_get_email_file', (file_id, g.current_org_id))
    if not f:
        abort(404)
    inline = f['content_type'] in INLINE and request.args.get('download') != '1'
    response = send_file(io.BytesIO(f['data']), mimetype=f['content_type'] if inline else 'application/octet-stream',
                         as_attachment=not inline, download_name=f['file_name'], max_age=0)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@emails_bp.route('/sync', methods=['POST'])
@require_org
def sync_now():
    if get_current_org_role() not in ('owner', 'admin'):
        abort(403)
    import emailsync
    if not emailsync.accounts_from_env():
        flash('No mailboxes are set up yet (EMAIL_ACCOUNTS).', 'error')
        return redirect(url_for('emails_bp.inbox'))
    results = emailsync.sync_all()
    stored = sum(r.get('stored') or 0 for r in results)
    errors = [f"{r['address']}: {r['error']}" for r in results if r.get('error')]
    flash(f"{stored} new email{'' if stored == 1 else 's'}." + (' Problems: ' + '; '.join(errors) if errors else ''),
          'warning' if errors else 'success')
    return redirect(url_for('emails_bp.inbox'))
