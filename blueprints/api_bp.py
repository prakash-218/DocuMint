"""
JSON for the React screens (frontend/). The same session login, organization and roles as the pages
(auth.require_org); refusals come back as JSON (auth.wants_json) instead of redirects.

Anything that changes data must be sent as JSON: a form on another site can't send that with our session
cookie (SameSite=Lax keeps it off cross-site POSTs anyway, and a JSON body needs a CORS preflight we never allow).
"""

import logging
import re

from flask import Blueprint, g, jsonify, request, session, url_for

from auth import CUSTOMER_EDITORS, EDITORS, MAIL_READERS, MANAGERS, SALES, get_current_org_role, require_org
from db import DatabaseError, db
import activity
import contacts
import mailsend
import project_view
import projects

logger = logging.getLogger(__name__)
api_bp = Blueprint('api_bp', __name__)


def _project(project_id, editing=True, refusal='Viewers can look but not change things'):
    """(project, None), or (None, a JSON refusal) when it isn't this organization's or the role can't change it."""
    if editing and get_current_org_role() not in EDITORS:
        return None, (jsonify(error=refusal), 403)
    project = projects.get_project(project_id, g.current_org_id)
    if not project:
        return None, (jsonify(error='Not found'), 404)
    return project, None


def _editable_project(project_id):
    return _project(project_id, refusal='Viewers can read but not send email')


def _body() -> dict:
    return request.get_json(silent=True) or {}


@api_bp.before_request
def json_bodies_only():
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not request.is_json:
        return jsonify(error='Send the request as JSON'), 415


@api_bp.route('/me')
@require_org
def me():
    """Who is signed in, in which organization, and what their role lets them do."""
    role = get_current_org_role()
    return jsonify(email=session.get('email'), role=role,
                   org={'id': g.current_org_id, 'name': session.get('org_name')},
                   can={'edit': role in EDITORS, 'edit_customers': role in CUSTOMER_EDITORS, 'manage': role in MANAGERS,
                        'read_mail': role in MAIL_READERS, 'quotations_only': role == SALES})


@api_bp.route('/projects/<project_id>/compose')
@require_org
def compose(project_id):
    """What the email form starts with: who it goes to, the subject and message, the documents it can attach."""
    project, refused = _editable_project(project_id)
    if refused:
        return refused
    return jsonify(mailsend.compose_context(g.current_org_id, session.get('org_name') or '', project,
                                            get_current_org_role(), request.args.get('invoice_id'),
                                            request.args.get('thread_id')))


@api_bp.route('/projects/<project_id>/emails', methods=['POST'])
@require_org
def send_email(project_id):
    """Send an email about the project from the shared mailbox: {to, cc, subject, body, thread_id, invoice_ids}."""
    project, refused = _editable_project(project_id)
    if refused:
        return refused
    try:
        sent = mailsend.send_for_project(g.current_org_id, session.get('org_name') or '', project,
                                         get_current_org_role(), request.get_json(silent=True) or {})
    except mailsend.SendError as e:
        return jsonify(error=str(e)), e.status
    return jsonify(sent), 201


# ---------------------------------------------------------------- Home

@api_bp.route('/home')
@require_org
def home():
    """What needs doing and the money still to come in (home_view.build). Not for Sales: their home is projects."""
    import home_view
    return jsonify(home_view.build(g.current_org_id, get_current_org_role(), url_for, email=session.get('email')))


@api_bp.route('/documents/<any(quotes, proformas, invoices):group>')
@require_org
def documents(group):
    """The quotations, proformas or invoices list (document_list.build). Sales see quotations only."""
    import document_list
    role = get_current_org_role()
    if role == SALES and group != 'quotes':
        return jsonify(error='Your role is Sales: projects, quotations and customers only'), 403
    try:
        docs = db.execute_proc('sp_list_invoices', (g.current_org_id, None, 100000, 0)) or []
    except DatabaseError:
        logger.exception("Failed to list documents for org %s", g.current_org_id)
        return jsonify(error="Couldn't load the documents. Try again in a moment."), 500
    from document_service import get_org_profile
    from payment_terms import usual_days
    return jsonify(document_list.build(group, docs, url_for, can_create=role in EDITORS,
                                       usual_days=usual_days(get_org_profile(g.current_org_id)[1])))


# ---------------------------------------------------------------- The project page

@api_bp.route('/projects')
@require_org
def list_projects():
    """Every project with where it is and what's next (project_view.projects_list), for the list and the board."""
    return jsonify(project_view.projects_list(g.current_org_id, get_current_org_role(), url_for))


@api_bp.route('/projects/<project_id>')
@require_org
def project(project_id):
    """Everything the project page shows (project_view.build), for this role."""
    found, refused = _project(project_id, editing=False)
    if refused:
        return refused
    return jsonify(project_view.build(g.current_org_id, found, get_current_org_role(), url_for))


@api_bp.route('/projects/<project_id>', methods=['PATCH'])
@require_org
def update_project(project_id):
    """Change the project's name, reference, notes, financial year or status (only what's sent)."""
    found, refused = _project(project_id)
    if refused:
        return refused
    data = _body()
    title = (data.get('title', found['title']) or '').strip()[:200]
    status = data.get('status', found['status'])
    year = str(data.get('fiscal_year') or found['fiscal_year']).strip()
    if not title:
        return jsonify(error='Give the project a name.'), 400
    if status not in projects.PROJECT_STATUSES:
        return jsonify(error="That isn't a project status."), 400
    if not re.fullmatch(r'\d{2}-\d{2}|\d{4}', year):
        return jsonify(error='A financial year looks like 26-27.'), 400
    try:
        db.execute_proc('sp_update_project', (project_id, g.current_org_id, title,
                                              (data.get('reference', found.get('reference')) or '').strip()[:100],
                                              status, (data.get('notes', found.get('notes')) or '').strip(), year), fetch=False)
    except DatabaseError:
        logger.exception('Could not update project %s', project_id)
        return jsonify(error='Could not save the project.'), 500
    if status != found['status']:
        activity.record('project_status', f"Project {projects.project_label(found)} marked "
                        f"{projects.PROJECT_STATUSES[status].lower()}", project_id=project_id,
                        link=url_for('projects_bp.view_project', project_id=project_id))
    return jsonify(ok=True)


@api_bp.route('/projects/<project_id>/notes', methods=['POST'])
@require_org
def add_note(project_id):
    """A note on the project's timeline: a call, what was agreed, what's next."""
    found, refused = _project(project_id)
    if refused:
        return refused
    text = (_body().get('text') or '').strip()[:4000]
    if not text:
        return jsonify(error='Write the note first.'), 400
    first_line = text.splitlines()[0][:120]
    activity.record('note', f'Note: {first_line}', project_id=project_id, body=text, notify=False)
    return jsonify(ok=True), 201


@api_bp.route('/projects/<project_id>/people', methods=['POST'])
@require_org
def set_person(project_id):
    """What one of the customer's contacts gets on this project: {contact_id, gets}."""
    found, refused = _project(project_id)
    if refused:
        return refused
    data = _body()
    if data.get('gets') not in contacts.GETS:
        return jsonify(error='Pick what they get.'), 400
    try:
        db.execute_proc('sp_set_project_contact', (project_id, g.current_org_id, data.get('contact_id'), data['gets']),
                        fetch=False)
    except DatabaseError:
        return jsonify(error="That contact isn't one of this customer's."), 400
    return jsonify(ok=True)


@api_bp.route('/projects/<project_id>/contacts', methods=['POST'])
@require_org
def save_person(project_id):
    """Add a contact to the project's customer, or change one of theirs: {contact_id?, customer_id?, name, email,
    phone, role, gets}. customer_id may be the parent company's, for a site's project."""
    found, refused = _project(project_id)
    if refused:
        return refused
    data = _body()
    customer_id = data.get('customer_id') or found['customer_id']
    if customer_id not in (found['customer_id'], found.get('customer_parent_id')):
        return jsonify(error="That isn't this project's customer."), 400
    fields, problem = contacts.fields_from(data)
    if problem:
        return jsonify(error=problem), 400
    try:
        row = db.execute_proc_single('sp_save_contact', (g.current_org_id, data.get('contact_id') or None, customer_id, *fields))
    except DatabaseError as e:
        return jsonify(error=f'{fields[1]} is already a contact here.' if 'uq_contact_customer_email' in str(e)
                       else 'Could not save the contact.'), 400
    return jsonify(contact_id=(row or {}).get('contact_id')), 201


@api_bp.route('/projects/<project_id>/ignore', methods=['POST'])
@require_org
def ignore_person(project_id):
    """Stop suggesting an address (or 'tel:<digits>') found in the project's emails."""
    found, refused = _project(project_id)
    if refused:
        return refused
    if get_current_org_role() not in MAIL_READERS:
        return jsonify(error="Your role doesn't see what's in the mailbox."), 403
    value = (_body().get('value') or '').strip().lower()
    if not value:
        return jsonify(error='Nothing to ignore.'), 400
    db.execute_proc('sp_ignore_contact_suggestion', (g.current_org_id, found['customer_id'], value), fetch=False)
    return jsonify(ok=True)


# ---------------------------------------------------------------- The customer page

def _customer(customer_id, editing=False):
    """(customer, None), or (None, a JSON refusal) when it isn't this organization's or the role can't change it."""
    import uuid
    from access import get_org_customer
    if editing and get_current_org_role() not in EDITORS:
        return None, (jsonify(error='Viewers can look at contacts but not change them'), 403)
    try:
        found = get_org_customer(str(uuid.UUID(str(customer_id))), g.current_org_id)[0]
    except (ValueError, DatabaseError):
        found = None
    if not found:
        return None, (jsonify(error='Not found'), 404)
    return found, None


@api_bp.route('/customers/<customer_id>')
@require_org
def customer(customer_id):
    """Everything the customer page shows (customer_view.build), for this role."""
    import customer_view
    found, refused = _customer(customer_id)
    if refused:
        return refused
    return jsonify(customer_view.build(g.current_org_id, found, get_current_org_role(), url_for))


@api_bp.route('/customers/<customer_id>/statement/compose')
@require_org
def statement_compose(customer_id):
    """The email form for a customer's statement (?fy=26-27 or all, ?currency=): their billing contacts, the PDF."""
    found, refused = _customer(customer_id)
    if refused:
        return refused
    if get_current_org_role() not in EDITORS:
        return jsonify(error='Viewers can look at the statement but not email it'), 403
    return jsonify(mailsend.statement_compose(g.current_org_id, session.get('org_name') or '', found,
                                              request.args.get('fy'), request.args.get('currency')))


@api_bp.route('/customers/<customer_id>/statement/emails', methods=['POST'])
@require_org
def send_statement(customer_id):
    """Email a customer's statement: {to, cc, subject, body, invoice_ids: ['statement'], fy, currency}."""
    found, refused = _customer(customer_id)
    if refused:
        return refused
    if get_current_org_role() not in EDITORS:
        return jsonify(error='Viewers can look at the statement but not email it'), 403
    try:
        sent = mailsend.send_statement(g.current_org_id, session.get('org_name') or '', found, request.get_json(silent=True) or {})
    except mailsend.SendError as e:
        return jsonify(error=str(e)), e.status
    return jsonify(sent), 201


@api_bp.route('/customers/<customer_id>/contacts', methods=['POST'])
@api_bp.route('/customers/<customer_id>/contacts/<contact_id>', methods=['POST'])
@require_org
def save_customer_contact(customer_id, contact_id=None):
    """Add a contact to the customer, or change one of theirs: {name, email, phone, role, gets}."""
    found, refused = _customer(customer_id, editing=True)
    if refused:
        return refused
    fields, problem = contacts.fields_from(_body())
    if problem:
        return jsonify(error=problem), 400
    try:
        row = db.execute_proc_single('sp_save_contact', (g.current_org_id, contact_id, found['customer_id'], *fields))
    except DatabaseError as e:
        return jsonify(error=f'{fields[1]} is already a contact here.' if 'uq_contact_customer_email' in str(e)
                       else 'Could not save the contact.'), 400
    return jsonify(contact_id=(row or {}).get('contact_id') or contact_id), 200 if contact_id else 201


@api_bp.route('/customers/<customer_id>/contacts/<contact_id>', methods=['DELETE'])
@require_org
def delete_customer_contact(customer_id, contact_id):
    found, refused = _customer(customer_id, editing=True)
    if refused:
        return refused
    try:
        db.execute_proc('sp_delete_contact', (g.current_org_id, found['customer_id'], contact_id), fetch=False)
    except DatabaseError:
        return jsonify(error="That isn't one of this customer's contacts."), 404
    return jsonify(ok=True)


# ---------------------------------------------------------------- Files

@api_bp.route('/files/<attachment_id>', methods=['PATCH'])
@require_org
def update_file(attachment_id):
    """What a dropped-in file is, and its number: {kind, reference_no}. A PO's number goes onto the project's documents."""
    if get_current_org_role() not in EDITORS:
        return jsonify(error='Viewers can look at files but not change them'), 403
    found = projects.get_attachment(attachment_id, g.current_org_id)
    if not found or get_current_org_role() == SALES and found.get('kind') in projects.NOT_QUOTATIONS:
        return jsonify(error='Not found'), 404
    data = _body()
    if get_current_org_role() == SALES and data.get('kind') in projects.NOT_QUOTATIONS:
        return jsonify(error="Your role is Sales: that kind of file isn't yours to keep."), 403
    try:
        filled = projects.update_attachment(g.current_org_id, found, data.get('kind'), data.get('reference_no') or '')
    except projects.UploadError as e:
        return jsonify(error=str(e)), 400
    except DatabaseError:
        logger.exception('Could not update file %s', attachment_id)
        return jsonify(error='Could not save that.'), 500
    return jsonify(ok=True, filled=filled)
