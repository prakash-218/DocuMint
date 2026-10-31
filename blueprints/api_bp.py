"""
JSON for the React screens (frontend/). The same session login, organization and roles as the pages
(auth.require_org); refusals come back as JSON (auth.wants_json) instead of redirects.

Anything that changes data must be sent as JSON: a form on another site can't send that with our session
cookie (SameSite=Lax keeps it off cross-site POSTs anyway, and a JSON body needs a CORS preflight we never allow).
"""

import logging
import re
from typing import Dict

from flask import Blueprint, g, jsonify, request, session, url_for

from auth import get_current_membership, require_org
from db import DatabaseError, db
import activity
import contacts
import mailsend
import permissions
import project_view
import projects

logger = logging.getLogger(__name__)
api_bp = Blueprint('api_bp', __name__)


def _project(project_id):
    """(project, None), or (None, a JSON refusal) when it isn't this organization's. What the person may do with it was
    checked before the endpoint ran (permissions.ENDPOINTS)."""
    project = projects.get_project(project_id, g.current_org_id)
    if not project:
        return None, (jsonify(error='Not found'), 404)
    return project, None


def _body() -> dict:
    return request.get_json(silent=True) or {}


@api_bp.before_request
def json_bodies_only():
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not request.is_json:
        return jsonify(error='Send the request as JSON'), 415


@api_bp.route('/me')
@require_org
def me():
    """Who is signed in, in which organization, their role and what it lets them do (permissions.PERMISSIONS)."""
    membership = get_current_membership() or {}
    return jsonify(email=session.get('email'), role=membership.get('role'),
                   role_label=permissions.role_label(membership.get('role'), membership.get('role_name')),
                   org={'id': g.current_org_id, 'name': session.get('org_name')},
                   permissions=sorted(permissions.granted()), can=permissions.flags())


@api_bp.route('/projects/<project_id>/compose')
@require_org
def compose(project_id):
    """What the email form starts with: who it goes to, the subject and message, the documents it can attach."""
    project, refused = _project(project_id)
    if refused:
        return refused
    return jsonify(mailsend.compose_context(g.current_org_id, session.get('org_name') or '', project,
                                            permissions.granted(), request.args.get('invoice_id'),
                                            request.args.get('thread_id')))


@api_bp.route('/projects/<project_id>/emails', methods=['POST'])
@require_org
def send_email(project_id):
    """Send an email about the project from the shared mailbox: {to, cc, subject, body, thread_id, invoice_ids}."""
    project, refused = _project(project_id)
    if refused:
        return refused
    try:
        sent = mailsend.send_for_project(g.current_org_id, session.get('org_name') or '', project,
                                         permissions.granted(), request.get_json(silent=True) or {})
    except mailsend.SendError as e:
        return jsonify(error=str(e)), e.status
    return jsonify(sent), 201


# ---------------------------------------------------------------- Home

@api_bp.route('/home')
@require_org
def home():
    """What needs doing and the money still to come in (home_view.build). Not for Sales: their home is projects."""
    import home_view
    return jsonify(home_view.build(g.current_org_id, permissions.granted(), url_for, email=session.get('email')))


@api_bp.route('/document/<invoice_id>')
@require_org
def document_page(invoice_id):
    """A document's page (document_page.py): its state, what's next, its money, payments, the document and beside it
    its project, people, activity and files."""
    from access import get_org_invoice
    from blueprints.invoices_bp import page_context
    import document_page as page
    header, _ = get_org_invoice(invoice_id, g.current_org_id)
    context = page_context(invoice_id) if header else None
    if not isinstance(context, dict):
        return jsonify(error='That document is not in this organization'), 404
    return jsonify(page.build(context, permissions.granted(), url_for))


@api_bp.route('/editor/new/<any(quotes, proformas, invoices, "purchase-orders"):group>')
@require_org
def new_document(group):
    """A new document's step (editor_page.new_page): the project it's for, its template, then the editor.
    ?doc_type= (else the address's), ?project_id=, ?template_id=."""
    import doc_urls
    import editor_page
    from documents import DOC_TYPES
    doc_type = request.args.get('doc_type')
    if doc_type == 'export_invoice':
        doc_type = 'invoice'
    if doc_type not in DOC_TYPES:
        doc_type = doc_urls.PATH_TYPES[group]
    # ?from_costing=<id>&lines=<item key>:<n>,...: a purchase order of a costing's lines, for those who see costings
    picks = [p for p in (request.args.get('lines') or '').split(',') if p]
    from_costing = ({'id': request.args['from_costing'], 'lines': picks}
                    if request.args.get('from_costing') and picks and permissions.can('costings.read') else None)
    return jsonify(project_view._plain(editor_page.new_page(g.current_org_id, doc_type, request.args.get('project_id'),
                                                            request.args.get('template_id'), url_for, from_costing)))


@api_bp.route('/editor/<invoice_id>')
@require_org
def edit_document(invoice_id):
    """A document in the editor (editor_page.edit_page): a draft, or with ?correct=1 a sent one being corrected."""
    from access import get_org_invoice
    import editor_page
    header, _ = get_org_invoice(invoice_id, g.current_org_id)
    if not header:
        return jsonify(error='That document is not in this organization'), 404
    correcting = (header.get('status') or 'draft') != 'draft' and request.args.get('correct') == '1'
    if (header.get('status') or 'draft') != 'draft' and not correcting:
        return jsonify(error='This document has been sent. Use "Change" on its page to correct it or make a revision.'), 409
    return jsonify(project_view._plain(editor_page.edit_page(g.current_org_id, header, correcting, url_for)))


@api_bp.route('/packing/<invoice_id>')
@require_org
def packing(invoice_id):
    """A document's packing, box by box (packing_page.build), when its template has a packing page."""
    from access import get_org_invoice
    from layout import load_layout, packing_page as page_of
    import packing_page
    header, values = get_org_invoice(invoice_id, g.current_org_id)
    if not header:
        return jsonify(error='That document is not in this organization'), 404
    pack_page = page_of(load_layout(header.get('template_id'), g.current_org_id), header.get('doc_type'))
    if not pack_page:
        return jsonify(error="This document's template has no packing list page. Add one under Templates → Pages & printing."), 404
    return jsonify(project_view._plain(packing_page.build(header, values, pack_page, url_for)))


@api_bp.route('/documents/<any(quotes, proformas, invoices, "purchase-orders"):group>')
@require_org
def documents(group):
    """The quotations, proformas or invoices list (document_list.build), for someone who may read them."""
    import doc_urls
    import document_list
    try:
        docs = db.execute_proc('sp_list_invoices', (g.current_org_id, None, 100000, 0)) or []
    except DatabaseError:
        logger.exception("Failed to list documents for org %s", g.current_org_id)
        return jsonify(error="Couldn't load the documents. Try again in a moment."), 500
    from document_service import get_org_profile
    from payment_terms import usual_days
    return jsonify(document_list.build(group, docs, url_for, can_create=permissions.can_doc('write', doc_urls.PATH_TYPES[group]),
                                       usual_days=usual_days(get_org_profile(g.current_org_id)[1])))


def _share(invoice_id, make=False):
    """The share dialog (sharing.py): the document's private link (made now when make), the WhatsApp message and who
    can get it, its UPI QR code, and the PDF. None when the document isn't in this organization."""
    from access import get_org_invoice
    from document_service import get_org_profile
    from documents import display_number, get_type
    from invoice_service import build_sections, invoice_summary
    from payment_terms import usual_days
    import sharing
    import upi
    header, values = get_org_invoice(invoice_id, g.current_org_id)
    if not header:
        return None
    if make:
        db.execute_proc('sp_create_share_link', (invoice_id, g.current_org_id, sharing.new_token(), g.current_user['user_id']))
    link = (db.execute_proc('sp_get_share_link', (invoice_id, g.current_org_id)) or [None])[0]
    payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,)) or []
    summary = invoice_summary(header, build_sections(header, values), payments)
    profile = get_org_profile(g.current_org_id)[1]
    pay = upi.payment(header, summary, profile)
    out = sharing.state(header, link, url_for, lambda path: request.host_url.rstrip('/') + path)
    project_id = projects.project_of(invoice_id, g.current_org_id)
    found = (contacts.for_supplier(g.current_org_id, header['customer_id']) if get_type(header.get('doc_type')).purchase
             else contacts.for_project(g.current_org_id, project_id) if project_id else [])
    return {**out, 'number': display_number(header), 'kind': get_type(header.get('doc_type')).label,
            'body': sharing.message(header, summary, out['link']['url'] if out['link'] else sharing.LINK, pay, usual_days(profile)),
            'people': sharing.people(found, header), 'pay': pay,
            'upi_missing': not pay and not upi.valid(profile.get('upi_id')) and (header.get('currency_code') or 'INR') == 'INR'
                           and upi.due(header, summary) > 0,
            'pdf': url_for('invoices_bp.export_pdf', invoice_id=invoice_id),
            'email': bool(project_id) and permissions.can('emails.send'),
            'actions': {'make': url_for('api_bp.share_on', invoice_id=invoice_id), 'off': url_for('api_bp.share_off', invoice_id=invoice_id)}}


@api_bp.route('/document/<invoice_id>/share')
@require_org
def share(invoice_id):
    """What the share dialog shows, without making a link."""
    data = _share(invoice_id)
    return jsonify(data) if data else (jsonify(error='That document is not in this organization'), 404)


@api_bp.route('/document/<invoice_id>/share', methods=['POST'])
@require_org
def share_on(invoice_id):
    """Makes the document's private link (or keeps the one it has), for WhatsApp or to copy."""
    data = _share(invoice_id, make=True)
    return jsonify(data) if data else (jsonify(error='That document is not in this organization'), 404)


@api_bp.route('/document/<invoice_id>/share', methods=['DELETE'])
@require_org
def share_off(invoice_id):
    """Turns the document's link off: anyone who has it gets "this link was turned off"."""
    db.execute_proc('sp_turn_off_share_link', (invoice_id, g.current_org_id))
    data = _share(invoice_id)
    return jsonify(data) if data else (jsonify(error='That document is not in this organization'), 404)


# ---------------------------------------------------------------- Invites and password reset links (invites.py)

def _sent(link: str, emailed: bool, to: str) -> Dict:
    """What the team's dialog shows after an invite or a reset link: the link to copy or send on WhatsApp, and whether
    it went by email."""
    return {'link': link, 'emailed': emailed, 'to': to}


@api_bp.route('/settings/invites', methods=['POST'])
@require_org
def invite_create():
    """Invites an address into the organization with a role they may give: emailed when the organization has a
    mailbox, and its link shown once."""
    import invites
    from blueprints.settings_bp import _role_choice
    data = request.get_json(silent=True) or {}
    email = invites.clean_email(data.get('email'))
    if not email:
        return jsonify(error="That isn't an email address."), 400
    role, role_id, given = _role_choice(g.current_org_id, data.get('role') or 'member')
    if not role:
        return jsonify(error="That isn't a role."), 400
    if not permissions.may_give(given):
        return jsonify(error='Only an owner can invite an owner.' if 'team.owners' in given else "That's more than your own role can give."), 403
    members = db.execute_proc('sp_get_org_members', (g.current_org_id,)) or []
    if any((m.get('email') or '').lower() == email and m.get('status') == 'active' for m in members):
        return jsonify(error=f'{email} is in the team already.'), 400
    token = invites.new_token()
    invite = db.execute_proc_single('sp_create_invite', (g.current_org_id, email, role, role_id, invites.token_hash(token),
                                                         g.current_user['user_id'], invites.INVITE_DAYS))
    link = url_for('auth_bp.accept_invite', token=token, _external=True)
    org_name = session.get('org_name') or invite.get('org_name') or ''
    message = invites.invite_message(org_name, permissions.role_label(role, invite.get('role_name')), link, g.current_user.get('email'))
    return jsonify(_sent(link, invites.send(g.current_org_id, email, message, org_name), email))


@api_bp.route('/settings/invites/<invite_id>/again', methods=['POST'])
@require_org
def invite_again(invite_id):
    """The same invite with a fresh link (the old one stops working), emailed again, and shown."""
    import invites
    from blueprints.settings_bp import _role_choice
    found = next((i for i in db.execute_proc('sp_list_invites', (g.current_org_id,)) or [] if str(i['invite_id']) == str(invite_id)), None)
    if not found:
        return jsonify(error='That invite was used or cancelled.'), 404
    _, _, given = _role_choice(g.current_org_id, str(found['role_id']) if found.get('role_id') else found['role'])
    if not permissions.may_give(given or ()):
        return jsonify(error="That's more than your own role can give."), 403
    token = invites.new_token()
    invite = db.execute_proc_single('sp_renew_invite', (found['invite_id'], g.current_org_id, invites.token_hash(token), invites.INVITE_DAYS))
    link = url_for('auth_bp.accept_invite', token=token, _external=True)
    org_name = session.get('org_name') or invite.get('org_name') or ''
    message = invites.invite_message(org_name, permissions.role_label(invite['role'], invite.get('role_name')), link, g.current_user.get('email'))
    return jsonify(_sent(link, invites.send(g.current_org_id, invite['email'], message, org_name), invite['email']))


@api_bp.route('/settings/invites/<invite_id>', methods=['DELETE'])
@require_org
def invite_cancel(invite_id):
    """The invite's link stops working."""
    db.execute_proc('sp_cancel_invite', (invite_id, g.current_org_id))
    return jsonify(ok=True)


@api_bp.route('/settings/members/<user_id>/reset', methods=['POST'])
@require_org
def member_reset(user_id):
    """A link for a member to set a new password, for when they forgot it and email doesn't reach them: shown to send
    another way, and emailed too when the organization has a mailbox. Not for yourself (use Forgot password), nor for
    someone whose role is beyond yours."""
    import invites
    member = next((m for m in db.execute_proc('sp_get_org_members', (g.current_org_id,)) or [] if str(m['user_id']) == str(user_id)), None)
    if not member or member.get('status') != 'active':
        return jsonify(error="That person isn't in the team."), 404
    if str(user_id) == str(g.current_user['user_id']) or not permissions.may_give(permissions.of(member)):
        return jsonify(error="You can't make a reset link for them."), 403
    token = invites.new_token()
    db.execute_proc('sp_create_password_reset', (user_id, invites.token_hash(token), g.current_user['user_id'], invites.RESET_MINUTES))
    link = url_for('auth_bp.reset_password', token=token, _external=True)
    emailed = invites.send(g.current_org_id, member['email'], invites.reset_message(link), session.get('org_name') or '')
    return jsonify(_sent(link, emailed, member['email']))


@api_bp.route('/payments')
@require_org
def payments():
    """Every payment received (payments_view.build), for someone who may read invoices."""
    import payments_view
    try:
        found = db.execute_proc('sp_list_org_payments', (g.current_org_id, None)) or []
        docs = db.execute_proc('sp_list_invoices', (g.current_org_id, None, 100000, 0)) or []
    except DatabaseError:
        logger.exception("Failed to list payments for org %s", g.current_org_id)
        return jsonify(error="Couldn't load the payments. Try again in a moment."), 500
    return jsonify(payments_view.build(found, docs, url_for))


# ---------------------------------------------------------------- The project page

@api_bp.route('/projects')
@require_org
def list_projects():
    """Every project with where it is and what's next (project_view.projects_list), for the list and the board."""
    return jsonify(project_view.projects_list(g.current_org_id, permissions.granted(), url_for))


@api_bp.route('/projects/<project_id>')
@require_org
def project(project_id):
    """Everything the project page shows (project_view.build), for this role."""
    found, refused = _project(project_id)
    if refused:
        return refused
    return jsonify(project_view.build(g.current_org_id, found, permissions.granted(), url_for))


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
    value = (_body().get('value') or '').strip().lower()
    if not value:
        return jsonify(error='Nothing to ignore.'), 400
    db.execute_proc('sp_ignore_contact_suggestion', (g.current_org_id, found['customer_id'], value), fetch=False)
    return jsonify(ok=True)


# ---------------------------------------------------------------- The customer page

def _customer(customer_id):
    """(customer, None), or (None, a JSON refusal) when it isn't this organization's. What the person may do with it was
    checked before the endpoint ran (permissions.ENDPOINTS)."""
    import uuid
    from access import get_org_customer
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
    return jsonify(customer_view.build(g.current_org_id, found, permissions.granted(), url_for))


@api_bp.route('/customers/<customer_id>/statement/compose')
@require_org
def statement_compose(customer_id):
    """The email form for a customer's statement (?fy=26-27 or all, ?currency=): their billing contacts, the PDF."""
    found, refused = _customer(customer_id)
    if refused:
        return refused
    return jsonify(mailsend.statement_compose(g.current_org_id, session.get('org_name') or '', found,
                                              request.args.get('fy'), request.args.get('currency')))


@api_bp.route('/customers/<customer_id>/statement/emails', methods=['POST'])
@require_org
def send_statement(customer_id):
    """Email a customer's statement: {to, cc, subject, body, invoice_ids: ['statement'], fy, currency}."""
    found, refused = _customer(customer_id)
    if refused:
        return refused
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
    found, refused = _customer(customer_id)
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
    found, refused = _customer(customer_id)
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
    found = projects.get_attachment(attachment_id, g.current_org_id)
    if not found or not permissions.file_kind_allowed(found.get('kind')):
        return jsonify(error='Not found'), 404
    data = _body()
    if not permissions.file_kind_allowed(data.get('kind')):
        return jsonify(error="Your role doesn't keep that kind of file."), 403
    try:
        filled = projects.update_attachment(g.current_org_id, found, data.get('kind'), data.get('reference_no') or '')
    except projects.UploadError as e:
        return jsonify(error=str(e)), 400
    except DatabaseError:
        logger.exception('Could not update file %s', attachment_id)
        return jsonify(error='Could not save that.'), 500
    return jsonify(ok=True, filled=filled)


# ---------------------------------------------------------------- Lists and forms (their forms post to the pages' routes)

@api_bp.route('/customers')
@require_org
def customers():
    """The customers list (customer_view.listing), or the suppliers with ?kind=supplier: ?q= searches,
    ?include_archived=true shows archived ones, ?page=."""
    import customer_view
    return jsonify(customer_view.listing(g.current_org_id, (request.args.get('q') or '').strip(),
                                         request.args.get('include_archived', '').lower() == 'true', permissions.granted(), url_for,
                                         'supplier' if request.args.get('kind') == 'supplier' else 'customer'))


@api_bp.route('/customers/new')
@require_org
def new_customer():
    """A new customer's form; ?parent_id= adds a site of that customer, starting from its details; ?kind=supplier
    starts it as a supplier."""
    import customer_view
    from access import get_org_customer
    defaults = {'kind': 'supplier'} if request.args.get('kind') == 'supplier' else {}
    parent = get_org_customer(request.args['parent_id'], g.current_org_id)[0] if request.args.get('parent_id') else None
    if parent and not parent.get('parent_id'):
        defaults = {k: parent.get(k) for k in ('name', 'tax_id', 'state', 'country')}
        defaults['parent_id'] = parent['customer_id']
    return jsonify(customer_view.form(g.current_org_id, None, defaults, url_for))


@api_bp.route('/customers/<customer_id>/form')
@require_org
def customer_form(customer_id):
    import customer_view
    found, refused = _customer(customer_id)
    if refused:
        return refused
    return jsonify(customer_view.form(g.current_org_id, found, {}, url_for))


@api_bp.route('/new-project')
@require_org
def new_project():
    """The new project form (project_view.new_project); ?customer_id= picks the customer."""
    return jsonify(project_view.new_project(g.current_org_id, request.args.get('customer_id'), url_for))


@api_bp.route('/emails')
@require_org
def emails():
    """The inbox (email_view.inbox): threads not in a project yet, or ?show=all; ?page=."""
    import email_view
    data = email_view.inbox(g.current_org_id, request.args.get('show', 'unlinked'), permissions.granted(), url_for)
    return jsonify(project_view._plain(data))


@api_bp.route('/emails/<thread_id>')
@require_org
def email_thread(thread_id):
    import email_view
    data = email_view.thread(g.current_org_id, thread_id, url_for)
    return jsonify(project_view._plain(data)) if data else (jsonify(error='Not found'), 404)


@api_bp.route('/notifications')
@require_org
def notifications():
    """Your notifications (notifications_view.build): unread, or ?show=all; ?page=."""
    import notifications_view
    data = notifications_view.build(g.current_user['user_id'], g.current_org_id, request.args.get('show') != 'all', url_for)
    return jsonify(project_view._plain(data))


@api_bp.route('/settings')
@require_org
def settings():
    """The settings page (settings_view.index): owners and admins also manage the team there."""
    import settings_view
    data = settings_view.index(g.current_user, g.current_org_id, session.get('org_name') or '', permissions.granted(), url_for)
    return jsonify(project_view._plain(data))


@api_bp.route('/settings/organizations/<org_id>')
@require_org
def organization(org_id):
    """The organization's name and address form; owners only, and only the one you're in."""
    import settings_view
    if str(org_id) != str(g.current_org_id):
        return jsonify(error='You can only edit the current organization'), 403
    found = db.execute_proc('sp_get_organization_details', (org_id,)) or []
    if not found:
        return jsonify(error='Not found'), 404
    return jsonify(settings_view.organization(found[0], url_for))


@api_bp.route('/settings/audit-log')
@require_org
def audit_log():
    """The audit log (settings_view.audit): ?table_name= one kind of change, ?page=; owners and admins."""
    import settings_view
    return jsonify(settings_view.audit(g.current_org_id, request.args.get('table_name') or '', url_for))


@api_bp.route('/settings/profile')
@require_org
def business_profile():
    """The business profile's form (settings_view.profile); owners and admins."""
    import settings_view
    return jsonify(project_view._plain(settings_view.profile(g.current_org_id, url_for)))


# ---------------------------------------------------------------- Roles: the built-in ones and the organization's own

@api_bp.route('/settings/roles')
@require_org
def roles():
    """The roles page (roles_view.listing)."""
    import roles_view
    return jsonify(roles_view.listing(g.current_org_id, permissions.granted(), url_for))


@api_bp.route('/settings/roles/new', defaults={'role_id': None})
@api_bp.route('/settings/roles/<role_id>')
@require_org
def role_form(role_id):
    """A role's editor (roles_view.editor); new, ?from=member starts from a built-in role's permissions."""
    import roles_view
    data = roles_view.editor(g.current_org_id, role_id, request.args.get('from'), permissions.granted(), url_for)
    if data is None:
        return jsonify(error='Not found'), 404
    return jsonify(data)


def _role_fields(data: dict):
    """(name, description, permissions) from {name, description, permissions: [...]}, or (None, a JSON refusal): a
    name nobody else's role has, and only permissions a custom role can grant that they have themselves."""
    name = ' '.join((data.get('name') or '').split())[:60]
    names = data.get('permissions')
    if not name:
        return None, (jsonify(error='Give the role a name.'), 400)
    if name.lower() in permissions.ROLES:
        return None, (jsonify(error=f'{name} is a built-in role. Call yours something else.'), 400)
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        return None, (jsonify(error='Send the permissions as a list of names.'), 400)
    unknown = [n for n in names if n not in permissions.PERMISSIONS]
    if unknown:
        return None, (jsonify(error=f"There's no permission called {unknown[0]}."), 400)
    owners = [n for n in names if n in permissions.OWNERS_ONLY]
    if owners:
        return None, (jsonify(error=f"Only owners can {permissions.PERMISSIONS[owners[0]][0].lower()}"
                                    f"{permissions.PERMISSIONS[owners[0]][1:]}: a role can't give that."), 400)
    chosen = permissions.with_implied(names)
    beyond = sorted(chosen - permissions.granted())
    if beyond:
        return None, (jsonify(error=f"You can't give what your own role doesn't have "
                                    f"({permissions.PERMISSIONS[beyond[0]][0].lower()}{permissions.PERMISSIONS[beyond[0]][1:]})."), 403)
    return (name, (data.get('description') or '').strip()[:255], sorted(chosen)), None


def _save_role(role_id, fields):
    """(its id, None), or (None, a JSON refusal)."""
    name, description, names = fields
    try:
        row = db.execute_proc_single('sp_save_role', (g.current_org_id, role_id, name, description, names))
    except DatabaseError as e:
        if 'uq_org_role_name' in str(e):
            return None, (jsonify(error=f'There is already a role called {name}.'), 409)
        if 'gone' in str(e):
            return None, (jsonify(error=str(e)), 404)
        logger.exception('Could not save role %s', role_id)
        return None, (jsonify(error='Could not save the role.'), 500)
    return row['role_id'], None


def _own_role(role_id):
    """(role, None), or (None, a JSON refusal) when it isn't this organization's or has more than they may give."""
    import roles_view
    row = db.execute_proc_single('sp_get_role', (g.current_org_id, role_id))
    if not row:
        return None, (jsonify(error='Not found'), 404)
    if not permissions.may_give(roles_view._custom(row)):
        return None, (jsonify(error="This role has more than your own role does, so you can't change it."), 403)
    return row, None


@api_bp.route('/settings/roles', methods=['POST'])
@require_org
def create_role():
    """A new role of the organization's own: {name, description, permissions: [names]}; 201 {id, url}."""
    fields, refused = _role_fields(_body())
    if refused:
        return refused
    saved, refused = _save_role(None, fields)
    if refused:
        return refused
    return jsonify(id=saved, url=url_for('settings_bp.role', role_id=saved)), 201


@api_bp.route('/settings/roles/<role_id>', methods=['PATCH'])
@require_org
def update_role(role_id):
    """Change a role: its name, description and permissions (all three are sent). Everyone with it has the new
    permissions on their next request."""
    _, refused = _own_role(role_id)
    if refused:
        return refused
    fields, refused = _role_fields(_body())
    if refused:
        return refused
    _, refused = _save_role(role_id, fields)
    return refused or jsonify(ok=True)


@api_bp.route('/settings/roles/<role_id>', methods=['DELETE'])
@require_org
def delete_role(role_id):
    """Delete a role nobody has (409 while someone does)."""
    _, refused = _own_role(role_id)
    if refused:
        return refused
    try:
        db.execute_proc('sp_delete_role', (g.current_org_id, role_id), fetch=False)
    except DatabaseError as e:
        return jsonify(error=str(e)), 409
    return jsonify(ok=True)


# ---------------------------------------------------------------- Costings and templates

def _base_currency():
    from document_service import get_org_profile
    return get_org_profile(g.current_org_id)[1].get('default_currency') or 'INR'


@api_bp.route('/costings/rates')
@require_org
def costing_rates():
    """The usual rates (costing_view.rates_page); ?back=<costing id> to go back to it. Owners and admins."""
    import costing as K
    import costing_view
    back = K.get(request.args['back'], g.current_org_id) if request.args.get('back') else None
    return jsonify(project_view._plain(costing_view.rates_page(g.current_org_id, back, _base_currency(), url_for)))


@api_bp.route('/costings/<costing_id>')
@require_org
def costing(costing_id):
    """A costing in its editor (costing_view.editor). Owners and admins."""
    import costing as K
    import costing_view
    row = K.get(costing_id, g.current_org_id)
    if not row:
        return jsonify(error='Not found'), 404
    return jsonify(project_view._plain(costing_view.editor(g.current_org_id, row, _base_currency(), url_for)))


@api_bp.route('/templates')
@require_org
def templates():
    """The templates as cards (template_view.cards); ?include_archived=true, ?page=."""
    import template_view
    return jsonify(template_view.cards(g.current_org_id, request.args.get('include_archived', '').lower() == 'true',
                                       permissions.granted(), url_for))


@api_bp.route('/templates/new')
@require_org
def new_template():
    import template_builder as TB
    import template_view
    return jsonify(template_view.builder(g.current_org_id, None, None, TB.STARTER, url_for))


@api_bp.route('/templates/<template_id>')
@require_org
def template(template_id):
    """A template's page (template_view.overview): its preview on sample values, formulas, pages, use and versions."""
    import template_view
    data = template_view.overview(g.current_org_id, template_id, permissions.granted(), url_for)
    return jsonify(project_view._plain(data)) if data else (jsonify(error='Not found'), 404)


@api_bp.route('/templates/<template_id>/layout')
@require_org
def template_layout(template_id):
    """Pages & printing (template_view.layout_page). Owners and admins."""
    import template_view
    from access import get_org_template
    info = get_org_template(template_id, g.current_org_id)
    if not info:
        return jsonify(error='Not found'), 404
    return jsonify(template_view.layout_page(g.current_org_id, template_id, info, url_for))


@api_bp.route('/templates/<template_id>/fields')
@require_org
def template_fields(template_id):
    """The latest version's fields in the builder (template_view.builder). Owners and admins."""
    import template_builder as TB
    import template_view
    info = next((t for t in db.execute_proc('sp_list_templates', (g.current_org_id, False)) or []
                 if t.get('template_id') == template_id and t.get('version') == t.get('latest_version')), None)
    if not info:
        return jsonify(error='Not found'), 404
    return jsonify(template_view.builder(g.current_org_id, template_id, info, TB.sections_for_editor(template_id, info['version']),
                                         url_for, in_use=TB.version_in_use(g.current_org_id, template_id, info['version'])))
