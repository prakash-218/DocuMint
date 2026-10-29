"""
JSON for the React screens (frontend/). The same session login, organization and roles as the pages
(auth.require_org); refusals come back as JSON (auth.wants_json) instead of redirects.

Anything that changes data must be sent as JSON: a form on another site can't send that with our session
cookie (SameSite=Lax keeps it off cross-site POSTs anyway, and a JSON body needs a CORS preflight we never allow).
"""

from flask import Blueprint, g, jsonify, request, session

from auth import CUSTOMER_EDITORS, EDITORS, MAIL_READERS, MANAGERS, SALES, get_current_org_role, require_org
import mailsend
import projects

api_bp = Blueprint('api_bp', __name__)


def _editable_project(project_id):
    """(project, None), or (None, a JSON refusal) when it isn't this organization's or the role can't send."""
    if get_current_org_role() not in EDITORS:
        return None, (jsonify(error='Viewers can read but not send email'), 403)
    project = projects.get_project(project_id, g.current_org_id)
    if not project:
        return None, (jsonify(error='Not found'), 404)
    return project, None


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
