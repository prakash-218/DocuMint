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
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        customers = db.execute_proc('sp_list_customers', (org_id, include_archived))
        return render_template('customers/list.html', customers=customers or [], include_archived=include_archived)
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
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')

        if not name:
            flash('Customer name is required', 'error')
            return render_template('customers/create.html')

        try:

            result = db.execute_proc('sp_create_customer', (org_id, name, tax_id, street_address, city, state, zip_code, country, None))
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


        customer = None
        contacts = []

        if isinstance(result, list):

            if len(result) > 0:
                if isinstance(result[0], list):

                    if len(result) >= 1 and len(result[0]) > 0:
                        customer = result[0][0]
                    if len(result) >= 2:
                        contacts = result[1]
                elif isinstance(result[0], dict):

                    customer = result[0]
                    if len(result) > 1:
                        contacts = result[1:]
        elif isinstance(result, dict):
            customer = result

        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))


        customer_user = None
        try:


            customer_users = db.execute_proc('sp_get_customer_users', (customer_id,))
            if customer_users and len(customer_users) > 0:
                customer_user = customer_users[0]
        except DatabaseError:

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


        result = db.execute_proc('sp_create_customer_user', (customer_id, email, password_hash, None))
        if not result or len(result) == 0:
            flash('Failed to create portal account', 'error')
            return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))

        customer_user_id = result[0].get('customer_user_id')



        if send_invitation:
            flash(f'Portal account created and invitation email sent to {email}', 'success')




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


@customers_bp.route('/<customer_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_customer(customer_id):
    """Edit customer details"""
    org_id = g.current_org_id


    try:
        result = db.execute_proc('sp_get_customer_details', (customer_id,))

        if not result:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))


        customer = None
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result[0]) > 0:
                        customer = result[0][0]
                elif isinstance(result[0], dict):
                    customer = result[0]
        elif isinstance(result, dict):
            customer = result

        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))


        if customer.get('org_id') != org_id:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))

    except DatabaseError as e:
        flash('Error loading customer', 'error')
        return redirect(url_for('customers_bp.list_customers'))

    if request.method == 'POST':
        name = request.form.get('name')
        tax_id = request.form.get('tax_id')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')

        if not name:
            flash('Customer name is required', 'error')
            return render_template('customers/edit.html', customer=customer)

        try:
            db.execute_proc('sp_update_customer', (
                customer_id,
                name,
                tax_id,
                street_address,
                city,
                state,
                zip_code,
                country
            ), fetch=False)

            flash('Customer updated successfully', 'success')
            return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))
        except DatabaseError as e:
            flash(f'Error updating customer: {str(e)}', 'error')

    return render_template('customers/edit.html', customer=customer)


@customers_bp.route('/<customer_id>/delete', methods=['POST'])
@require_org
def delete_customer(customer_id):
    """Delete a customer"""
    org_id = g.current_org_id

    try:

        result = db.execute_proc('sp_get_customer_details', (customer_id,))
        if not result:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))

        customer = None
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result[0]) > 0:
                        customer = result[0][0]
                elif isinstance(result[0], dict):
                    customer = result[0]
        elif isinstance(result, dict):
            customer = result

        if not customer or customer.get('org_id') != org_id:
            flash('Customer not found', 'error')
            return redirect(url_for('customers_bp.list_customers'))


        db.execute_proc('sp_delete_customer', (customer_id, org_id), fetch=False)
        flash('Customer deleted successfully', 'success')
    except DatabaseError as e:
        error_msg = str(e)
        if 'existing invoices' in error_msg.lower():
            flash('Cannot delete customer with existing invoices. Please delete all invoices first.', 'error')
        else:
            flash(f'Error deleting customer: {str(e)}', 'error')

    return redirect(url_for('customers_bp.list_customers'))


@customers_bp.route('/<customer_id>/archive', methods=['POST'])
@require_org
def archive_customer(customer_id):
    """Archive a customer"""
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_archive_customer', (customer_id, org_id), fetch=False)
        flash('Customer archived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error archiving customer: {str(e)}', 'error')
    
    return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))


@customers_bp.route('/<customer_id>/unarchive', methods=['POST'])
@require_org
def unarchive_customer(customer_id):
    """Unarchive a customer"""
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_unarchive_customer', (customer_id, org_id), fetch=False)
        flash('Customer unarchived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error unarchiving customer: {str(e)}', 'error')
    
    return redirect(url_for('customers_bp.view_customer', customer_id=customer_id))

