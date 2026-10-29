"""
Customers blueprint - CRUD operations for customers
"""

import re

from flask import Blueprint, request, render_template, redirect, url_for, flash, g
from db import db, DatabaseError
from auth import CUSTOMER_EDITORS, EDITORS, MAIL_READERS, require_org, get_current_org_role, quotations_only
from access import get_org_customer
from documents import load_json
import contacts
import customers as C

customers_bp = Blueprint('customers_bp', __name__)


def _form_context(org_id, customer=None, defaults=None):
    """What the customer form needs besides the customer: who it can be a site of, and its own sites."""
    everyone = db.execute_proc('sp_list_customers', (org_id, True)) or []
    customer_id = (customer or {}).get('customer_id')
    site_count = sum(1 for c in everyone if customer_id and c.get('parent_id') == customer_id)
    return {'parents': C.parent_choices(everyone, customer_id), 'site_count': site_count,
            'defaults': defaults or {}, 'custom_defs': _custom_defs(org_id)}


def _save_parent(customer_id, org_id, form):
    if 'parent_id' in form:                  # the form leaves it out for a customer that has sites
        db.execute_proc('sp_set_customer_parent', (customer_id, org_id, form.get('parent_id') or None,
                                                   form.get('site_name')), fetch=False)


def _custom_defs(org_id):
    """The org's customer custom-field definitions (from the business profile)."""
    from document_service import get_org_profile
    from layout import custom_field_defs
    return custom_field_defs(get_org_profile(org_id)[1], 'customer')


def _save_email_domains(customer_id, org_id, form):
    import re
    domains = [d.strip().lstrip('@').lower() for d in re.split(r'[,\s]+', form.get('email_domains') or '') if d.strip()]
    db.execute_proc('sp_update_customer_email_domains', (customer_id, org_id, ', '.join(dict.fromkeys(domains))), fetch=False)


def _save_custom(customer_id, org_id, form, defs):
    import json
    values = {f['key']: (form.get(f'custom_{f["key"]}') or '').strip() for f in defs}
    values = {k: v for k, v in values.items() if v}
    db.execute_proc('sp_update_customer_custom', (customer_id, org_id, json.dumps(values)), fetch=False)


@customers_bp.route('/')
@require_org
def list_customers():
    """List all customers"""
    org_id = g.current_org_id
    current_role = get_current_org_role()

    try:
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        customers = db.execute_proc('sp_list_customers', (org_id, include_archived)) or []
        query = (request.args.get('q') or '').strip()
        customers = C.search(customers, query)
        from pagination import paginate
        page = paginate(C.group(customers))         # whole groups, so a site stays with its customer
        return render_template('customers/list.html', customers=customers, groups=page.items, page=page,
                               include_archived=include_archived,
                               query=query, current_org_role=current_role)
    except DatabaseError:
        flash('Error loading customers', 'error')
        return render_template('customers/list.html', customers=[], groups=[], include_archived=False, query='',
                               current_org_role=current_role)


@customers_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_customer():
    """Create a new customer"""
    current_role = get_current_org_role()
    if current_role not in CUSTOMER_EDITORS:
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner, admin or sales to create customers.', 'error')
        return redirect(url_for('customers_bp.list_customers'))
    
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
            return render_template('customers/create.html', custom_values={}, **_form_context(org_id, defaults=request.form))

        try:

            result = db.execute_proc('sp_create_customer', (org_id, name, tax_id, street_address, city, state, zip_code, country, None))
            if result and len(result) > 0:
                customer_id = result[0].get('customer_id')
                _save_email_domains(customer_id, org_id, request.form)
                _save_parent(customer_id, org_id, request.form)
                defs = _custom_defs(org_id)
                if defs:
                    _save_custom(customer_id, org_id, request.form, defs)
                flash('Customer created successfully', 'success')
                return redirect(_customer_page(customer_id))
            else:
                flash('Failed to create customer', 'error')
        except DatabaseError as e:
            flash(f'Error creating customer: {str(e)}', 'error')

    defaults = {}
    parent, _ = get_org_customer(request.args['parent_id'], org_id) if request.args.get('parent_id') else (None, [])
    if parent and not parent.get('parent_id'):          # "Add site": start from the parent's details
        defaults = {k: parent.get(k) for k in ('name', 'tax_id', 'state', 'country')}
        defaults['parent_id'] = parent['customer_id']
    return render_template('customers/create.html', custom_values={},
                           **_form_context(org_id, defaults=request.form if request.method == 'POST' else defaults))


@customers_bp.route('/<customer_id>')
@require_org
def view_customer(customer_id):
    """View customer details"""
    current_role = get_current_org_role()
    try:
        customer, _ = get_org_customer(customer_id, g.current_org_id)

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

        import projects
        from documents import balance_of, sum_by_currency
        # A customer with sites shows theirs too: documents, what's outstanding, projects
        sites = db.execute_proc('sp_list_customer_sites', (g.current_org_id, customer_id)) or []
        family = {customer_id} | {s['customer_id'] for s in sites}
        docs = [d for d in db.execute_proc('sp_list_invoices', (g.current_org_id, None, 100000, 0)) or []
                if d.get('customer_id') in family]
        files = projects.list_attachments(g.current_org_id, customer_id=customer_id)
        if quotations_only():       # Sales: their quotations only, and nothing they owe
            docs = [d for d in docs if d.get('doc_type') == 'quote']
            files = [f for f in files if f.get('kind') not in projects.NOT_QUOTATIONS]
        unpaid = [d for d in docs if d.get('doc_type') in ('invoice', 'export_invoice') and d.get('status') == 'pending']
        family_projects = projects.list_projects(g.current_org_id, customer_id)
        import revisions
        return render_template('customers/view.html',
                             docs=revisions.collapse(docs),
                             outstanding=sum_by_currency(unpaid, balance_of),
                             projects=family_projects,
                             own_projects=[j for j in family_projects if j['customer_id'] == customer_id],
                             sites=sites,
                             files=files,
                             file_kinds=projects.DOCUMENT_KINDS,
                             custom_defs=_custom_defs(g.current_org_id),
                             custom_values=load_json(customer.get('custom')),
                             customer=customer,
                             contacts=contacts.for_customer(g.current_org_id, customer),
                             usually=contacts.USUALLY,
                             customer_user=customer_user,
                             current_org_role=current_role)
    except DatabaseError as e:
        flash('Error loading customer', 'error')
        return redirect(url_for('customers_bp.list_customers'))


@customers_bp.route('/<customer_id>/new')
@require_org
def view_customer_new(customer_id):
    """The new customer page: the React screen in frontend/src/islands/customer/ (GET /api/customers/<id>)."""
    try:
        customer, _ = get_org_customer(customer_id, g.current_org_id)
    except DatabaseError:
        customer = None
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers_bp.list_customers'))
    return render_template('customers/new_view.html', customer=customer)


def _customer_page(customer_id):
    """The customer's page to go back to: the new one when that's where the form was sent from (or the editor was
    opened from, ?from=new), else the classic one."""
    from urllib.parse import urlparse
    ref = urlparse(request.referrer or '')
    if (not ref.netloc or ref.netloc == request.host) and ref.path.rstrip('/').endswith(f'/{customer_id}/new')             or request.args.get('from') == 'new':
        return url_for('customers_bp.view_customer_new', customer_id=customer_id)
    return url_for('customers_bp.view_customer', customer_id=customer_id)


def _contact_back(customer_id):
    """Back to the project the form was on, when it's this organization's; else to the customer."""
    project_id = request.form.get('project_id')
    if project_id:
        import projects
        if projects.get_project(project_id, g.current_org_id):
            return url_for('projects_bp.view_project', project_id=project_id) + '#people'
    return url_for('customers_bp.view_customer', customer_id=customer_id) + '#contacts'


@customers_bp.route('/<customer_id>/contacts', methods=['POST'])
@customers_bp.route('/<customer_id>/contacts/<contact_id>', methods=['POST'])
@require_org
def save_contact(customer_id, contact_id=None):
    """Add a contact, or change one."""
    back = _contact_back(customer_id)
    if get_current_org_role() not in EDITORS:
        flash('Viewers can look at contacts but not change them.', 'error')
        return redirect(back)
    fields, problem = contacts.fields_from(request.form)
    if problem:
        flash(problem, 'error')
        return redirect(back)
    try:
        db.execute_proc('sp_save_contact', (g.current_org_id, contact_id, customer_id, *fields), fetch=False)
    except DatabaseError as e:
        flash(f'{fields[1]} is already a contact here.' if 'uq_contact_customer_email' in str(e)
              else 'Could not save the contact', 'error')
    else:
        flash(f'{fields[0]} saved' if contact_id else f'{fields[0]} added to the contacts', 'success')
    return redirect(back)


@customers_bp.route('/<customer_id>/contacts/<contact_id>/delete', methods=['POST'])
@require_org
def delete_contact(customer_id, contact_id):
    back = _contact_back(customer_id)
    if get_current_org_role() not in EDITORS:
        flash('Viewers can look at contacts but not change them.', 'error')
        return redirect(back)
    try:
        db.execute_proc('sp_delete_contact', (g.current_org_id, customer_id, contact_id), fetch=False)
    except DatabaseError:
        flash('Could not remove the contact', 'error')
    else:
        flash('Contact removed', 'success')
    return redirect(back)


@customers_bp.route('/<customer_id>/ignore-suggestion', methods=['POST'])
@require_org
def ignore_contact(customer_id):
    """Stop suggesting an address (or a phone number, 'tel:<digits>') found in this customer's emails."""
    back = _contact_back(customer_id)
    value = (request.form.get('value') or '').strip().lower()
    if get_current_org_role() in MAIL_READERS and value:
        try:
            db.execute_proc('sp_ignore_contact_suggestion', (g.current_org_id, customer_id, value), fetch=False)
        except DatabaseError:
            flash('Could not save that', 'error')
    return redirect(back)


@customers_bp.route('/<customer_id>/create-portal-account', methods=['POST'])
@require_org
def create_portal_account(customer_id):
    """Create a customer portal account (admin action)"""
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to create portal accounts.', 'error')
        return redirect(_customer_page(customer_id))
    
    org_id = g.current_org_id

    email = request.form.get('email')
    password = request.form.get('password')
    send_invitation = request.form.get('send_invitation') == 'on'

    if not email or not password:
        flash('Email and password are required', 'error')
        return redirect(_customer_page(customer_id))

    if len(password) < 8:
        flash('Password must be at least 8 characters', 'error')
        return redirect(_customer_page(customer_id))

    customer, _ = get_org_customer(customer_id, org_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers_bp.list_customers'))

    try:
        from auth import hash_password

        password_hash = hash_password(password)


        result = db.execute_proc('sp_create_customer_user', (customer_id, email, password_hash, None))
        if not result or len(result) == 0:
            flash('Failed to create portal account', 'error')
            return redirect(_customer_page(customer_id))

        customer_user_id = result[0].get('customer_user_id')



        if send_invitation:
            flash(f'Portal account created and invitation email sent to {email}', 'success')




        else:
            flash(f'Portal account created for {email}. Customer can now login at /customer/login', 'success')

        return redirect(_customer_page(customer_id))

    except DatabaseError as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower():
            flash(f'Email {email} already has a portal account', 'error')
        else:
            flash(f'Error creating portal account: {error_msg}', 'error')
        return redirect(_customer_page(customer_id))


@customers_bp.route('/<customer_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_customer(customer_id):
    """Edit customer details"""
    current_role = get_current_org_role()
    if current_role not in CUSTOMER_EDITORS:
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner, admin or sales to edit customers.', 'error')
        return redirect(_customer_page(customer_id))
    
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
            return render_template('customers/edit.html', customer=customer, custom_values=load_json(customer.get('custom')),
                                   **_form_context(org_id, customer))

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
            _save_email_domains(customer_id, org_id, request.form)
            _save_parent(customer_id, org_id, request.form)
            defs = _custom_defs(org_id)
            if defs:
                _save_custom(customer_id, org_id, request.form, defs)

            flash('Customer updated successfully', 'success')
            return redirect(_customer_page(customer_id))
        except DatabaseError as e:
            flash(f'Error updating customer: {str(e)}', 'error')

    return render_template('customers/edit.html', customer=customer, custom_values=load_json(customer.get('custom')),
                           **_form_context(org_id, customer))


@customers_bp.route('/<customer_id>/delete', methods=['POST'])
@require_org
def delete_customer(customer_id):
    """Delete a customer"""
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to delete customers.', 'error')
        return redirect(_customer_page(customer_id))
    
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
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to archive customers.', 'error')
        return redirect(_customer_page(customer_id))
    
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_archive_customer', (customer_id, org_id), fetch=False)
        flash('Customer archived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error archiving customer: {str(e)}', 'error')
    
    return redirect(_customer_page(customer_id))


@customers_bp.route('/<customer_id>/unarchive', methods=['POST'])
@require_org
def unarchive_customer(customer_id):
    """Unarchive a customer"""
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to unarchive customers.', 'error')
        return redirect(_customer_page(customer_id))
    
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_unarchive_customer', (customer_id, org_id), fetch=False)
        flash('Customer unarchived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error unarchiving customer: {str(e)}', 'error')
    
    return redirect(_customer_page(customer_id))

