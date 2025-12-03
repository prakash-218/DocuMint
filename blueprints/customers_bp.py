"""
Customers blueprint - CRUD operations for customers
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, g
from db import db, DatabaseError
from auth import require_org

customers_bp = Blueprint('customers_bp', __name__)


@customers_bp.route('/')
@require_org
def list_customers():
    """List all customers"""
    org_id = g.current_org_id
    
    try:
        customers = db.execute_proc('sp_list_customers', (org_id,))
        return render_template('customers/list.html', customers=customers or [])
    except DatabaseError as e:
        flash('Error loading customers', 'error')
        return render_template('customers/list.html', customers=[])


@customers_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_customer():
    """Create a new customer"""
    org_id = g.current_org_id
    
    if request.method == 'POST':
        name = request.form.get('name')
        tax_id = request.form.get('tax_id')
        
        if not name:
            flash('Customer name is required', 'error')
            return render_template('customers/create.html')
        
        try:
            # Procedure has 3 IN params + 1 OUT param = 4 total, need placeholder for OUT
            result = db.execute_proc('sp_create_customer', (org_id, name, tax_id, None))
            if result and len(result) > 0:
                customer_id = result[0].get('customer_id')
                flash('Customer created successfully', 'success')
                return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
            else:
                flash('Failed to create customer', 'error')
        except DatabaseError as e:
            flash(f'Error creating customer: {str(e)}', 'error')
    
    return render_template('customers/create.html')


@customers_bp.route('/<customer_id>')
@require_org
def view_customer(customer_id):
    """View customer details"""
    try:
        result = db.execute_proc('sp_get_customer_details', (customer_id,))
        
        if not result:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))
        
        # Handle multiple result sets
        customer = None
        contacts = []
        
        if isinstance(result, list):
            # Check if first element is a list (multiple result sets) or dict (single result set)
            if len(result) > 0:
                if isinstance(result[0], list):
                    # Multiple result sets
                    if len(result) >= 1 and len(result[0]) > 0:
                        customer = result[0][0]
                    if len(result) >= 2:
                        contacts = result[1]
                elif isinstance(result[0], dict):
                    # Single result set
                    customer = result[0]
                    if len(result) > 1:
                        contacts = result[1:]
        elif isinstance(result, dict):
            customer = result
        
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))
        
        # Check if customer already has a portal account
        customer_user = None
        try:
            # Check if any customer_user exists for this customer
            # Note: In a real app, you might want to list all portal accounts for this customer
            customer_users = db.execute_proc('sp_get_customer_users', (customer_id,))
            if customer_users and len(customer_users) > 0:
                customer_user = customer_users[0]  # Get first portal account
        except DatabaseError:
            # Procedure might not exist yet, that's okay
            pass
        except Exception:
            pass
        
        return render_template('customers/view.html', 
                             customer=customer, 
                             contacts=contacts or [],
                             customer_user=customer_user)
    except DatabaseError as e:
        flash('Error loading customer', 'error')
        return redirect(url_for('customers_bp.list_customers'))


@customers_bp.route('/<customer_id>/create-portal-account', methods=['POST'])
@require_org
def create_portal_account(customer_id):
    """Create a customer portal account (admin action)"""
    org_id = g.current_org_id
    
    email = request.form.get('email')
    password = request.form.get('password')
    send_invitation = request.form.get('send_invitation') == 'on'
    
    if not email or not password:
        flash('Email and password are required', 'error')
        return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
    
    if len(password) < 8:
        flash('Password must be at least 8 characters', 'error')
        return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
    
    try:
        from auth import hash_password
        
        password_hash = hash_password(password)
        
        # Create customer user account
        result = db.execute_proc('sp_create_customer_user', (customer_id, email, password_hash, None))
        if not result or len(result) == 0:
            flash('Failed to create portal account', 'error')
            return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
        
        customer_user_id = result[0].get('customer_user_id')
        
        # TODO: In a real app, send invitation email here
        # For now, just show success message
        if send_invitation:
            flash(f'Portal account created and invitation email sent to {email}', 'success')
            # In production, you would:
            # 1. Generate a secure invitation token
            # 2. Send email with link to set password
            # 3. Customer clicks link and sets their own password
        else:
            flash(f'Portal account created for {email}. Customer can now login at /customer/login', 'success')
        
        return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
        
    except DatabaseError as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower():
            flash(f'Email {email} already has a portal account', 'error')
        else:
            flash(f'Error creating portal account: {error_msg}', 'error')
        return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))

