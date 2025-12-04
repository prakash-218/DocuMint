"""
Authentication and authorization module using JWT.
"""

import jwt
import bcrypt
from functools import wraps
from flask import request, session, g, redirect, url_for
from datetime import datetime, timedelta
import os
from db import db, DatabaseError


JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
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
            'org_name': session.get('org_name')
        }
    return None


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('auth_bp.login'))


        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def require_org(f):
    """Decorator to require organization context"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get('org_id'):
            return redirect(url_for('settings_bp.select_org'))


        g.current_org_id = user['org_id']
        return f(*args, **kwargs)
    return decorated_function


def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticate a user and return user info with organizations.

    Returns:
        dict with user_id, email, and organizations list
    """
    try:



        result = db.execute_proc('sp_authenticate_user', (email, password, None, None))

        if not result:
            return None


        user_info = None
        orgs = []

        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):

                    if len(result) >= 1 and len(result[0]) > 0:
                        user_info = result[0][0]
                    if len(result) >= 2:
                        orgs = result[1]
                elif isinstance(result[0], dict):



                    user_info = result[0] if len(result) == 1 else None
                    orgs = result if len(result) > 1 else []
        elif isinstance(result, dict):
            user_info = result

        if not user_info:
            return None

        return {
            'user_id': user_info.get('user_id'),
            'email': user_info.get('email') or email,
            'organizations': orgs or []
        }
    except DatabaseError as e:

        if 'Invalid email or password' in str(e):
            return None
        raise


def register_user(email: str, password: str, org_name: str, org_domain: str) -> dict:
    """
    Register a new user and create their organization.

    Returns:
        dict with user_id, org_id, and email
    """
    try:
        password_hash = hash_password(password)



        org_result = db.execute_proc('sp_create_organization', (org_name, org_domain, None))
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


        db.execute_proc('sp_assign_user_to_org', (user_id, org_id, 'owner'), fetch=False)

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


def authenticate_customer(email: str, password: str) -> dict:
    """
    Authenticate a customer and return customer info.

    Returns:
        dict with customer_user_id, customer_id, email, customer_name
    """
    try:

        user_result = db.execute_proc_single(
            'SELECT customer_user_id, customer_id, email, password_hash FROM customer_user WHERE email = %s',
            (email,)
        )

        if not user_result:
            return None


        if not verify_password(password, user_result['password_hash']):
            return None


        customer_result = db.execute_proc('sp_authenticate_customer', (email, hash_password(password)))
        if not customer_result or len(customer_result) == 0:
            return None

        customer_info = customer_result[0]
        return {
            'customer_user_id': customer_info.get('customer_user_id'),
            'customer_id': customer_info.get('customer_id'),
            'email': customer_info.get('email'),
            'customer_name': customer_info.get('customer_name'),
            'org_id': customer_info.get('org_id')
        }
    except DatabaseError as e:
        if 'Invalid email or password' in str(e):
            return None
        raise


def create_customer_user(customer_id: str, email: str, password: str) -> dict:
    """
    Create a customer user account.

    Returns:
        dict with customer_user_id, customer_id, email
    """
    try:
        password_hash = hash_password(password)


        result = db.execute_proc('sp_create_customer_user', (customer_id, email, password_hash, None))
        if not result or len(result) == 0:
            raise DatabaseError("Failed to create customer user")

        customer_user_id = result[0].get('customer_user_id')

        return {
            'customer_user_id': customer_user_id,
            'customer_id': customer_id,
            'email': email
        }
    except DatabaseError as e:
        if 'already exists' in str(e).lower():
            raise ValueError("Email already exists")
        raise

