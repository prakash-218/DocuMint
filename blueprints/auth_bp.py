"""
Authentication blueprint - login, register, logout
"""

from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from db import db, DatabaseError
from auth import authenticate_user, register_user, verify_password, generate_token, hash_password, require_auth
import traceback

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        try:
            # Get user from database to verify password
            user_result = db.execute_proc_single('sp_get_user_by_email', (email,))
            
            if not user_result:
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html')
            
            # Verify password
            if not verify_password(password, user_result['password_hash']):
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html')
            
            # Get organizations
            orgs = db.execute_proc('sp_get_user_organizations', (user_result['user_id'],))
            
            # Set session
            session['user_id'] = user_result['user_id']
            session['email'] = user_result['email']
            
            # Set default org if available
            if orgs and len(orgs) > 0:
                session['org_id'] = orgs[0]['org_id']
                session['org_name'] = orgs[0]['name']
            
            # Generate token (for API use if needed)
            token = generate_token(user_result['user_id'], user_result['email'], session.get('org_id'))
            session['token'] = token
            
            return redirect(url_for('dashboard_bp.index'))
            
        except DatabaseError as e:
            flash('Login failed. Please try again.', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        org_name = request.form.get('org_name')
        org_domain = request.form.get('org_domain')
        
        # Validation
        if not all([email, password, confirm_password, org_name, org_domain]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('auth/register.html')
        
        try:
            user_data = register_user(email, password, org_name, org_domain)
            
            if not user_data or 'user_id' not in user_data:
                flash('Registration failed: Invalid response from server', 'error')
                return render_template('auth/register.html')
            
            # Set session
            session['user_id'] = user_data['user_id']
            session['email'] = user_data['email']
            session['org_id'] = user_data['org_id']
            session['org_name'] = org_name
            
            # Generate token
            token = generate_token(user_data['user_id'], user_data['email'], user_data['org_id'])
            session['token'] = token
            
            # Force session to be saved
            session.permanent = True
            
            print(f"DEBUG: Registration successful for {email}, redirecting to dashboard")
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard_bp.index'))
            
        except ValueError as e:
            print(f"DEBUG: ValueError during registration: {str(e)}")
            flash(str(e), 'error')
            return render_template('auth/register.html')
        except DatabaseError as e:
            error_msg = str(e)
            print(f"DEBUG: DatabaseError during registration: {error_msg}")
            print(traceback.format_exc())
            flash(f'Registration failed: {error_msg}', 'error')
            return render_template('auth/register.html')
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: Unexpected error during registration: {error_msg}")
            print(traceback.format_exc())
            flash(f'Unexpected error: {error_msg}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@require_auth
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth_bp.login'))

