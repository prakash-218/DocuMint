"""
Authentication and authorization module using JWT.
"""

import jwt
import bcrypt
from functools import wraps
from flask import render_template, request, session, g, redirect, url_for
from datetime import datetime, timedelta
import os
from db import db, DatabaseError


JWT_SECRET = os.getenv('JWT_SECRET') or os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id: str, email: str, org_id: str = None) -> str:
    """Generate a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'org_id': org_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def get_current_user():
    """Get current user from session/token"""
    if 'user_id' in session:
        return {
            'user_id': session.get('user_id'),
            'email': session.get('email'),
            'org_id': session.get('org_id'),
            'org_name': session.get('org_name'),
            'status': session.get('status'),
            'role': session.get('role')
        }
    return None


def wants_json() -> bool:
    """A request from the React screens (/api/...): refusals come back as JSON, not as redirects to a page."""
    return request.blueprint == 'api_bp'


def _refuse(status, message, page):
    """JSON for /api requests; otherwise the page (a redirect, usually)."""
    from flask import jsonify
    return (jsonify(error=message), status) if wants_json() else page


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _refuse(401, 'Sign in first', redirect(url_for('auth_bp.login')))


        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def require_org(f):
    """Decorator to require organization context and ACTIVE status"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user or not user.get('org_id'):
            return _refuse(403, 'Pick an organization first', redirect(url_for('settings_bp.select_org')))

        # Re-read membership on every request so role changes, deactivations
        # and removals take effect immediately instead of at next login.
        try:
            orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],)) or []
        except DatabaseError:
            orgs = None
        if orgs is not None:
            session['user_organizations'] = orgs
            membership = next((o for o in orgs if str(o.get('org_id')) == str(user['org_id'])), None)
            if not membership:
                for key in ('org_id', 'org_name', 'org_status'):
                    session.pop(key, None)
                return _refuse(403, 'You are not a member of this organization', redirect(url_for('settings_bp.select_org')))
            session['org_name'] = membership.get('name')
            session['org_status'] = membership.get('status', 'active')

        org_status = session.get('org_status')
        if org_status and org_status != 'active':
            # Render the "Access Status" page instead of the requested route
            if wants_json():
                return _refuse(403, f'This organization is {org_status}', None)
            return render_template('errors/org_status.html', status=org_status, org_name=session.get('org_name'))
        
        g.current_org_id = user['org_id']
        if get_current_org_role() == SALES:
            refused = _sales_refusal()
            if refused:
                return refused
        return f(*args, **kwargs)
    return decorated_function


def get_current_org_role():
    """Get current user's role in the current organization"""
    if not session.get('user_organizations') or not hasattr(g, 'current_org_id'):
        return None
    
    org_id = g.current_org_id
    for org in session.get('user_organizations', []):
        if str(org.get('org_id')) == str(org_id):
            return org.get('role')
    return None


def require_role(allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        @require_org
        def decorated_function(*args, **kwargs):
            current_role = get_current_org_role()
            if not current_role or current_role not in allowed_roles:
                from flask import flash
                flash('You do not have permission to perform this action', 'error')
                return redirect(url_for('dashboard_bp.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Roles, most to least: owner (everything), admin (runs the business: customers, templates,
# settings, team except owners), member (creates and edits documents), viewer (read only).
# Beside them, sales: projects (and their files), quotations and customers, and nothing else.
SALES = 'sales'
MANAGERS = ('owner', 'admin')
EDITORS = ('owner', 'admin', 'member', SALES)          # create and edit documents (sales: quotations only)
CUSTOMER_EDITORS = ('owner', 'admin', SALES)           # add and edit customers
MAIL_READERS = ('owner', 'admin', 'member')            # read the mailbox (and what's found in it)

# What Sales may open: blueprint -> its pages (None: all of them). Anything else is refused, so a page
# added later stays closed to Sales until it's listed here. Every document a request is about must be a
# quotation, which also keeps out converting one to a proforma or invoice.
SALES_PAGES = {
    'projects_bp': None,
    'invoices_bp': {'list_invoices', 'create_invoice', 'view_invoice', 'view_invoice_new', 'export_pdf', 'finalize_invoice',
                    'set_status', 'revise', 'edit_invoice', 'reopen', 'delete_invoice'},
    'customers_bp': {'list_customers', 'view_customer', 'view_customer_new', 'create_customer', 'edit_customer', 'save_contact',
                     'delete_contact'},
    'search_bp': None,
    'api_bp': {'me', 'compose', 'send_email', 'list_projects', 'project', 'update_project', 'add_note', 'set_person',
               'save_person', 'customer', 'save_customer_contact', 'delete_customer_contact', 'update_file'},
    'settings_bp': {'index', 'select_org'},
}


def sales_may(endpoint, doc_type=None) -> bool:
    """Whether Sales may open this page (endpoint), about a document of this type if any."""
    blueprint, _, page = (endpoint or '').partition('.')
    if blueprint not in SALES_PAGES or SALES_PAGES[blueprint] is not None and page not in SALES_PAGES[blueprint]:
        return False
    return doc_type in (None, 'quote')


def _request_doc_type():
    """The type of document this request is about: the one in its URL or form, or for the document pages the
    type their address or form names (/quotes/create, doc_type=proforma)."""
    import doc_urls
    invoice_id = (request.view_args or {}).get('invoice_id') or request.form.get('invoice_id')
    if invoice_id:
        return doc_urls.doc_type_of(invoice_id)
    if (request.endpoint or '').startswith('invoices_bp.'):
        return request.values.get('doc_type') or doc_urls.PATH_TYPES.get(getattr(g, 'doc_path', None), 'invoice')
    return None


def _sales_refusal():
    """None when Sales may open this request; otherwise where to send them (their home: projects)."""
    from flask import flash
    home = url_for('projects_bp.list_projects')
    if request.endpoint == 'dashboard_bp.index':
        return redirect(home)
    if sales_may(request.endpoint, _request_doc_type()):
        return None
    if wants_json():
        return _refuse(403, 'Your role is Sales: projects, quotations and customers only', None)
    flash('Your role is Sales: you can open projects, quotations and customers.', 'error')
    return redirect(home)


def quotations_only() -> bool:
    """Sales: pages show quotations only, and no money beyond what was quoted."""
    return get_current_org_role() == SALES


def can_manage():
    """Customers, templates, business settings, team, audit log, deleting drafts."""
    return get_current_org_role() in MANAGERS


def can_create_invoice():
    return get_current_org_role() in EDITORS


def can_edit_invoice():
    return get_current_org_role() in EDITORS


def can_delete_invoice(doc=None):
    """Owners and admins; Sales their draft quotations (doc: the document, when there is one)."""
    if can_manage():
        return True
    return (quotations_only() and bool(doc) and doc.get('doc_type') == 'quote'
            and (doc.get('status') or 'draft') == 'draft')


def can_delete_project():
    """Deleting a project only ungroups it: its documents and files stay."""
    return can_manage() or quotations_only()


def can_finalize_invoice():
    return get_current_org_role() in EDITORS

def register_user(email: str, password: str, org_name: str, org_domain: str) -> dict:
    """
    Register a new user and create their organization.

    Returns:
        dict with user_id, org_id, and email
    """
    try:
        password_hash = hash_password(password)



        org_result = db.execute_proc('sp_create_organization', (
            org_name, 
            org_domain, 
            None,  # street_address
            None,  # city
            None,  # state
            None,  # zip_code
            None,  # country
            None   # OUT p_org_id
        ))
        if not org_result or len(org_result) == 0:
            raise DatabaseError("Failed to create organization - no result returned")


        org_id = org_result[0].get('org_id')
        if not org_id:
            raise DatabaseError(f"Failed to create organization - invalid result: {org_result}")



        user_result = db.execute_proc('sp_create_user', (email, password_hash, None))
        if not user_result or len(user_result) == 0:
            raise DatabaseError("Failed to create user - no result returned")


        user_id = user_result[0].get('user_id')
        if not user_id:
            raise DatabaseError(f"Failed to create user - invalid result: {user_result}")


        db.execute_proc('sp_assign_user_to_org', (user_id, org_id, 'owner','active'), fetch=False)

        return {
            'user_id': user_id,
            'org_id': org_id,
            'email': email
        }

    except DatabaseError as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower():
            raise ValueError("Email or domain already exists")

        raise DatabaseError(f"Registration error: {error_msg}")
    except Exception as e:
        raise DatabaseError(f"Unexpected registration error: {str(e)}")


def get_current_customer():
    """Get current customer from session"""
    if 'customer_user_id' in session:
        return {
            'customer_user_id': session.get('customer_user_id'),
            'customer_id': session.get('customer_id'),
            'email': session.get('customer_email'),
            'customer_name': session.get('customer_name')
        }
    return None


def require_customer_auth(f):
    """Decorator to require customer authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        customer = get_current_customer()
        if not customer:
            return redirect(url_for('customer_portal_bp.login'))

        g.current_customer = customer
        g.current_customer_id = customer['customer_id']
        return f(*args, **kwargs)
    return decorated_function
