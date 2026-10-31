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
        import permissions
        refused = permissions.check()             # what this page or endpoint needs (permissions.ENDPOINTS)
        if refused:
            return refused
        return f(*args, **kwargs)
    return decorated_function


def get_current_membership():
    """Their membership of the current organization (sp_get_user_organizations' row: role, and for a custom role its
    role_id, role_name and role_permissions), or None."""
    if not session.get('user_organizations') or not hasattr(g, 'current_org_id'):
        return None
    return next((o for o in session['user_organizations'] if str(o.get('org_id')) == str(g.current_org_id)), None)


def get_current_org_role():
    """Their role in the current organization: a built-in one, or 'custom' (get_current_membership has which)."""
    membership = get_current_membership()
    return membership.get('role') if membership else None


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
