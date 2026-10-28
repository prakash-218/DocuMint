"""
JSON for the React screens (frontend/). The same session login, organization and roles as the pages
(auth.require_org); refusals come back as JSON (auth.wants_json) instead of redirects.

Anything that changes data must be sent as JSON: a form on another site can't send that with our session
cookie (SameSite=Lax keeps it off cross-site POSTs anyway, and a JSON body needs a CORS preflight we never allow).
"""

from flask import Blueprint, g, jsonify, request, session

from auth import CUSTOMER_EDITORS, EDITORS, MAIL_READERS, MANAGERS, SALES, get_current_org_role, require_org

api_bp = Blueprint('api_bp', __name__)


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
