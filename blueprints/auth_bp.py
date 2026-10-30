"""
Authentication blueprint - login, register, logout
"""

from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from db import db, DatabaseError
from auth import register_user, verify_password, generate_token, hash_password, require_auth
import traceback

auth_bp = Blueprint('auth_bp', __name__)


# ---------------------------------------------------------------- The pages (nav.public: frontend/src/public/ draws them)

def _login_page():
    import nav
    return nav.public('login', 'Log in', action=url_for('auth_bp.login'), register=url_for('auth_bp.register'),
                      portal=url_for('customer_portal_bp.login'))


def _register_page():
    import nav
    return nav.public('register', 'Register', action=url_for('auth_bp.register'), login=url_for('auth_bp.login'))


def _verify_page(email, domain):
    import nav
    return nav.public('verify', 'Verify your account', email=email, domain=domain or '',
                      action=url_for('auth_bp.verify_existing_user', email=email, domain=domain),
                      register=url_for('auth_bp.register'), login=url_for('auth_bp.login'))


def _choose_org_page(email, domain, existing_orgs, existing_user):
    import nav
    orgs = [{'id': str(o.get('org_id')), 'name': o.get('name') or '', 'domain': o.get('domain') or '',
             'created': str(o.get('created_at') or '')} for o in existing_orgs or []]
    # existing_user stays on the form's address: the next step trusts it only after verify_existing_user
    return nav.public('choose_org', 'Choose your organization', email=email, domain=domain or '', orgs=orgs,
                      existing_user=bool(existing_user), register=url_for('auth_bp.register'),
                      action=url_for('auth_bp.select_org_register', email=email, domain=domain,
                                     existing_user='true' if existing_user else None))


def _register_org_page(email, domain, existing_org_id=None, existing_org=None, existing_user=False):
    import nav
    org = {'name': existing_org.get('name') or '', 'domain': existing_org.get('domain') or ''} if existing_org else None
    back = ({'href': url_for('auth_bp.select_org_register', email=email, domain=domain), 'label': 'Back to organization selection'}
            if existing_org_id else {'href': url_for('auth_bp.register'), 'label': 'Back to email'})
    return nav.public('register_org', 'Set up your organization', email=email, domain=domain or '',
                      org_id=str(existing_org_id or ''), org=org, existing_user=bool(existing_user), back=back,
                      action=url_for('auth_bp.register_org', email=email, domain=domain, org_id=existing_org_id,
                                     existing_user='true' if existing_user else None))


def _is_verified_existing_user(email):
    """The existing_user flag comes from the client, so only trust it for an
    email whose password was checked in verify_existing_user this session."""
    return bool(email) and session.get('verified_registration_email') == email.lower()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'error')
            return _login_page()

        try:

            user_result = db.execute_proc_single('sp_get_user_by_email', (email,))

            if not user_result:
                flash('Invalid email or password', 'error')
                return _login_page()


            if not verify_password(password, user_result['password_hash']):
                flash('Invalid email or password', 'error')
                return _login_page()


            orgs = db.execute_proc('sp_get_user_organizations', (user_result['user_id'],))


            session['user_id'] = user_result['user_id']
            session['email'] = user_result['email']


            if orgs:
                session['user_organizations'] = orgs
                if len(orgs) > 0:
                    first_org = next((o for o in orgs if o.get('status') == 'active'), orgs[0])
                    session['org_id'] = first_org['org_id']
                    session['org_name'] = first_org['name']
                    session['org_status'] = first_org.get('status', 'active')

            token = generate_token(user_result['user_id'], user_result['email'], session.get('org_id'))
            session['token'] = token

            return redirect(url_for('dashboard_bp.index'))

        except DatabaseError as e:
            flash('Login failed. Please try again.', 'error')
            return _login_page()

    return _login_page()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Step 1: Email collection"""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Email is required', 'error')
            return _register_page()


        if '@' not in email or '.' not in email.split('@')[1]:
            flash('Please enter a valid email address', 'error')
            return _register_page()


        email_exists = False
        try:
            user_result = db.execute_proc('sp_get_user_by_email', (email,))
            if user_result and len(user_result) > 0:
                email_exists = True
        except DatabaseError:
            pass


        email_parts = email.split('@')
        if len(email_parts) == 2:
            email_domain = email_parts[1].lower()

            if email_exists:

                return redirect(url_for('auth_bp.verify_existing_user', email=email, domain=email_domain))
            else:

                try:
                    orgs = db.execute_proc('sp_find_organizations_by_domain', (email_domain,))
                    if orgs and len(orgs) > 0:

                        return redirect(url_for('auth_bp.select_org_register', email=email, domain=email_domain))
                    else:

                        return redirect(url_for('auth_bp.register_org', email=email, domain=email_domain))
                except DatabaseError:

                    return redirect(url_for('auth_bp.register_org', email=email, domain=email_domain))
        else:
            flash('Invalid email format', 'error')
            return _register_page()

    return _register_page()


@auth_bp.route('/register/verify', methods=['GET', 'POST'])
def verify_existing_user():
    """Step 2a: Verify password for existing user before allowing org join/create"""
    email = request.args.get('email') or request.form.get('email')
    domain = request.args.get('domain') or request.form.get('domain')

    if not email:
        flash('Please start registration from the beginning', 'error')
        return redirect(url_for('auth_bp.register'))


    if not domain and '@' in email:
        email_parts = email.split('@')
        if len(email_parts) == 2:
            domain = email_parts[1].lower()

    if request.method == 'POST':
        password = request.form.get('password')

        if not password:
            flash('Password is required', 'error')
            return _verify_page(email, domain)

        try:

            user_result = db.execute_proc('sp_get_user_by_email', (email,))
            if not user_result or len(user_result) == 0:
                flash('Account not found', 'error')
                return redirect(url_for('auth_bp.register'))


            from auth import verify_password
            if not verify_password(password, user_result[0]['password_hash']):
                flash('Incorrect password. Please try again.', 'error')
                return _verify_page(email, domain)

            session['verified_registration_email'] = email.lower()


            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                if orgs and len(orgs) > 0:

                    return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain, existing_user='true'))
                else:

                    return redirect(url_for('auth_bp.register_org', email=email, domain=domain, existing_user='true'))
            except DatabaseError:

                return redirect(url_for('auth_bp.register_org', email=email, domain=domain, existing_user='true'))

        except DatabaseError as e:
            flash(f'Error verifying account: {str(e)}', 'error')
            return _verify_page(email, domain)

    return _verify_page(email, domain)


@auth_bp.route('/register/select-org', methods=['GET', 'POST'])
def select_org_register():
    """Step 2: Select organization to join or create new (only one org allowed during registration)"""
    email = request.args.get('email') or request.form.get('email')
    domain = request.args.get('domain') or request.form.get('domain')
    existing_user = request.args.get('existing_user') == 'true' or request.form.get('existing_user') == 'true'

    if not email:
        flash('Please start registration from the beginning', 'error')
        return redirect(url_for('auth_bp.register'))


    if not domain and '@' in email:
        email_parts = email.split('@')
        if len(email_parts) == 2:
            domain = email_parts[1].lower()

    if request.method == 'POST':
        action = request.form.get('action')
        selected_org_id = request.form.get('org_id')

        if action == 'join' and selected_org_id:

            return redirect(url_for('auth_bp.register_org', email=email, domain=domain, org_id=selected_org_id, existing_user='true' if existing_user else None))
        elif action == 'create':

            return redirect(url_for('auth_bp.register_org', email=email, domain=domain, existing_user='true' if existing_user else None))
        else:
            flash('Please select an organization or choose to create a new one', 'error')


    existing_orgs = []
    if domain:
        try:
            orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
            if orgs:
                existing_orgs = orgs
        except DatabaseError:
            pass

    return _choose_org_page(email, domain, existing_orgs, existing_user)


@auth_bp.route('/register/org', methods=['GET', 'POST'])
def register_org():
    """Step 3: Password (if new user) and finalize organization setup"""
    email = request.args.get('email') or request.form.get('email')
    domain = request.args.get('domain') or request.form.get('domain')
    org_id = request.args.get('org_id') or request.form.get('org_id')
    existing_user = request.args.get('existing_user') == 'true' or request.form.get('existing_user') == 'true'

    if not email:
        flash('Please start registration from the beginning', 'error')
        return redirect(url_for('auth_bp.register'))

    if existing_user and not _is_verified_existing_user(email):
        flash('Please verify your password to continue', 'error')
        return redirect(url_for('auth_bp.verify_existing_user', email=email, domain=domain))


    if not domain and '@' in email:
        email_parts = email.split('@')
        if len(email_parts) == 2:
            domain = email_parts[1].lower()

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        org_name = request.form.get('org_name')
        org_domain = request.form.get('org_domain')
        existing_org_id = request.form.get('org_id') or org_id


        if not existing_user:
            if not password or not confirm_password:
                flash('Password fields are required', 'error')
                existing_org = None
                if existing_org_id:
                    try:
                        org_result = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                        if org_result and len(org_result) > 0:
                            existing_org = next((o for o in org_result if o.get('org_id') == existing_org_id or o['org_id'] == existing_org_id), None)
                    except DatabaseError:
                        pass
                return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id, existing_org=existing_org, existing_user=existing_user)

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                existing_org = None
                if existing_org_id:
                    try:
                        org_result = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                        if org_result and len(org_result) > 0:
                            existing_org = next((o for o in org_result if o.get('org_id') == existing_org_id or o['org_id'] == existing_org_id), None)
                    except DatabaseError:
                        pass
                return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id, existing_org=existing_org, existing_user=existing_user)

            if len(password) < 8:
                flash('Password must be at least 8 characters', 'error')
                existing_org = None
                if existing_org_id:
                    try:
                        org_result = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                        if org_result and len(org_result) > 0:
                            existing_org = next((o for o in org_result if o.get('org_id') == existing_org_id or o['org_id'] == existing_org_id), None)
                    except DatabaseError:
                        pass
                return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id, existing_org=existing_org, existing_user=existing_user)

        try:

            if not org_domain:
                org_domain = domain


            if existing_org_id:

                try:
                    org_result = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                    if not org_result or len(org_result) == 0:
                        flash('Selected organization no longer exists', 'error')
                        return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain, existing_user='true' if existing_user else None))
                    org = next((o for o in org_result if o.get('org_id') == existing_org_id or o['org_id'] == existing_org_id), None)
                    if not org:
                        flash('Selected organization not found', 'error')
                        return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain, existing_user='true' if existing_user else None))
                except DatabaseError:
                    flash('Error verifying organization', 'error')
                    return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain, existing_user='true' if existing_user else None))


                if existing_user:

                    user_result = db.execute_proc('sp_get_user_by_email', (email,))
                    if not user_result or len(user_result) == 0:
                        flash('User account not found', 'error')
                        return redirect(url_for('auth_bp.register'))
                    user_id = user_result[0].get('user_id')


                    user_orgs = db.execute_proc('sp_get_user_organizations', (user_id,))
                    if user_orgs:
                        for uo in user_orgs:
                            if uo.get('org_id') == existing_org_id or uo['org_id'] == existing_org_id:
                                flash('You are already a member of this organization', 'info')

                                session['user_id'] = user_id
                                session['email'] = email
                                session['org_id'] = existing_org_id
                                session['org_name'] = org['name']
                                if user_orgs:
                                    session['user_organizations'] = user_orgs
                                token = generate_token(user_id, email, existing_org_id)
                                session['token'] = token
                                session.permanent = True
                                return redirect(url_for('dashboard_bp.index'))
                else:

                    password_hash = hash_password(password)
                    user_result = db.execute_proc('sp_create_user', (email, password_hash, None))
                    if not user_result or len(user_result) == 0:
                        flash('Failed to create user account', 'error')
                        return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain))
                    user_id = user_result[0].get('user_id')


                db.execute_proc('sp_assign_user_to_org', (user_id, existing_org_id, 'member','pending'), fetch=False)


                org_result = db.execute_proc('sp_get_user_organizations', (user_id,))
                if org_result and len(org_result) > 0:
                    org = next((o for o in org_result if o.get('org_id') == existing_org_id or o['org_id'] == existing_org_id), org_result[0])

                    session['user_organizations'] = org_result
                else:
                    flash('Failed to retrieve organization details', 'error')
                    return redirect(url_for('auth_bp.select_org_register', email=email, domain=domain))


                session['user_id'] = user_id
                session['email'] = email
                session['org_id'] = org['org_id']
                session['org_name'] = org['name']
                session['org_status'] = org.get('status', 'pending')  # Set status from org data


                token = generate_token(user_id, email, org['org_id'])
                session['token'] = token
                session.permanent = True

                flash(f'Account created! You have been added to {org["name"]}.', 'success')
                
                # If status is pending, redirect to org_status page instead of dashboard
                if org.get('status') == 'pending':
                    return render_template('errors/org_status.html', 
                                         status='pending', 
                                         org_name=org['name'])
                
                return redirect(url_for('dashboard_bp.index'))


            if not org_name:
                flash('Organization name is required', 'error')
                return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)

            if not org_domain:
                org_domain = domain

            if existing_user:

                user_result = db.execute_proc('sp_get_user_by_email', (email,))
                if not user_result or len(user_result) == 0:
                    flash('User account not found', 'error')
                    return redirect(url_for('auth_bp.register'))
                user_id = user_result[0].get('user_id')


                try:
                    existing_orgs = db.execute_proc('sp_find_organizations_by_domain', (org_domain,))
                    if existing_orgs:
                        for org in existing_orgs:
                            if org.get('name') == org_name or org['name'] == org_name:
                                flash(f'An organization named "{org_name}" with domain "{org_domain}" already exists. Please choose a different name or domain.', 'error')
                                return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)
                except DatabaseError:
                    pass


                try:
                    street_address = request.form.get('street_address')
                    city = request.form.get('city')
                    state = request.form.get('state')
                    zip_code = request.form.get('zip_code')
                    country = request.form.get('country')
                    
                    org_result = db.execute_proc('sp_create_organization', (
                        org_name, 
                        org_domain, 
                        street_address or None,
                        city or None,
                        state or None,
                        zip_code or None,
                        country or None,
                        None
                    ))
                    if not org_result or len(org_result) == 0:
                        flash('Failed to create organization', 'error')
                        return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)
                except DatabaseError as e:
                    error_msg = str(e)
                    if 'Duplicate entry' in error_msg or '1062' in error_msg:
                        flash(f'An organization with domain "{org_domain}" already exists. Please choose a different domain or join the existing organization.', 'error')
                    else:
                        flash(f'Failed to create organization: {error_msg}', 'error')
                    return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)

                new_org_id = org_result[0].get('org_id')
                db.execute_proc('sp_assign_user_to_org', (user_id, new_org_id, 'owner','active'), fetch=False)


                orgs = db.execute_proc('sp_get_user_organizations', (user_id,))


                session['user_id'] = user_id
                session['email'] = email
                session['org_id'] = new_org_id
                session['org_name'] = org_name
                if orgs:
                    session['user_organizations'] = orgs


                token = generate_token(user_id, email, new_org_id)
                session['token'] = token
                session.permanent = True

                flash('Organization created successfully!', 'success')
                return redirect(url_for('dashboard_bp.index'))
            else:

                try:
                    existing_orgs = db.execute_proc('sp_find_organizations_by_domain', (org_domain,))
                    if existing_orgs:
                        for org in existing_orgs:
                            if org.get('name') == org_name or org['name'] == org_name:
                                flash(f'An organization named "{org_name}" with domain "{org_domain}" already exists. Please choose a different name or domain.', 'error')
                                return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)
                except DatabaseError:
                    pass


                try:
                    user_data = register_user(email, password, org_name, org_domain)
                except DatabaseError as e:
                    error_msg = str(e)
                    if 'Duplicate entry' in error_msg or '1062' in error_msg:
                        if 'domain' in error_msg.lower():
                            flash(f'An organization with domain "{org_domain}" already exists. Please choose a different domain or join the existing organization.', 'error')
                        else:
                            flash(f'Registration failed: {error_msg}', 'error')
                    else:
                        flash(f'Registration failed: {error_msg}', 'error')
                    return _register_org_page(email=email, domain=domain, existing_org_id=None, existing_user=existing_user)

                if not user_data or 'user_id' not in user_data:
                    flash('Registration failed: Invalid response from server', 'error')
                    return _register_org_page(email=email, domain=domain, existing_org_id=None)


                orgs = db.execute_proc('sp_get_user_organizations', (user_data['user_id'],))


                session['user_id'] = user_data['user_id']
                session['email'] = user_data['email']
                session['org_id'] = user_data['org_id']
                session['org_name'] = org_name
                if orgs:
                    session['user_organizations'] = orgs


                token = generate_token(user_data['user_id'], user_data['email'], user_data['org_id'])
                session['token'] = token
                session.permanent = True

                flash('Registration successful!', 'success')
                return redirect(url_for('dashboard_bp.index'))

        except ValueError as e:
            flash(str(e), 'error')
            return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id)
        except DatabaseError as e:
            error_msg = str(e)
            flash(f'Registration failed: {error_msg}', 'error')
            return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id)
        except Exception as e:
            error_msg = str(e)
            flash(f'Unexpected error: {error_msg}', 'error')
            return _register_org_page(email=email, domain=domain, existing_org_id=existing_org_id)


    existing_org = None
    if org_id and domain:
        try:
            org_result = db.execute_proc('sp_find_organizations_by_domain', (domain,))
            if org_result:
                existing_org = next((o for o in org_result if o.get('org_id') == org_id or o['org_id'] == org_id), None)
        except DatabaseError:
            pass

    return _register_org_page(email=email, domain=domain, existing_org_id=org_id, existing_org=existing_org, existing_user=existing_user)


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth_bp.login'))

