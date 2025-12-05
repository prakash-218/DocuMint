"""
Settings blueprint - Organization settings and preferences
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, jsonify
from db import db, DatabaseError
from auth import require_auth, require_org, hash_password

settings_bp = Blueprint('settings_bp', __name__)


@settings_bp.route('/')
@require_org
def index():
    """Settings page"""
    user = g.current_user

    try:
        user_orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        current_org_id = g.current_org_id if hasattr(g, 'current_org_id') else None
        return render_template('settings/index.html', user_organizations=user_orgs or [], current_org_id=current_org_id)
    except DatabaseError:
        current_org_id = g.current_org_id if hasattr(g, 'current_org_id') else None
        return render_template('settings/index.html', user_organizations=[], current_org_id=current_org_id)


@settings_bp.route('/select-org', methods=['GET', 'POST'])
@require_auth
def select_org():
    """Select organization context"""
    user = g.current_user

    if request.method == 'POST':
        org_id = request.form.get('org_id')
        if org_id:

            orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
            org = next((o for o in (orgs or []) if o['org_id'] == org_id), None)

            if org:
                session['org_id'] = org_id
                session['org_name'] = org['name']
                session['org_status'] = org.get('status', 'active')

                if org.get('status') != 'active':
                    return render_template('errors/org_status.html', 
                                         status=org.get('status'), 
                                         org_name=org['name'])

                orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
                if orgs:
                    session['user_organizations'] = orgs
                flash('Organization switched successfully', 'success')
                return redirect(request.referrer or url_for('dashboard_bp.index'))
            else:
                flash('Invalid organization', 'error')


    try:
        orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        return render_template('settings/select_org.html', organizations=orgs or [])
    except DatabaseError as e:
        flash('Error loading organizations', 'error')
        return render_template('settings/select_org.html', organizations=[])


@settings_bp.route('/organizations/create', methods=['GET', 'POST'])
@require_auth
def create_organization():
    """Create a new organization"""
    user = g.current_user

    if request.method == 'POST':
        org_name = request.form.get('org_name')
        org_domain = request.form.get('org_domain')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')

        if not org_name:
            flash('Organization name is required', 'error')
            return render_template('settings/create_org.html')

        if not org_domain:
            flash('Organization domain is required', 'error')
            return render_template('settings/create_org.html')


        try:
            existing_orgs = db.execute_proc('sp_find_organizations_by_domain', (org_domain.lower(),))
            if existing_orgs:
                for org in existing_orgs:
                    if org.get('name') == org_name or org['name'] == org_name:
                        flash(f'An organization named "{org_name}" with domain "{org_domain}" already exists. Please choose a different name or domain.', 'error')
                        return render_template('settings/create_org.html')
        except DatabaseError:
            pass


        try:
            org_result = db.execute_proc('sp_create_organization', (
                org_name, 
                org_domain.lower(), 
                street_address or None,
                city or None,
                state or None,
                zip_code or None,
                country or None,
                None
            ))
            if not org_result or len(org_result) == 0:
                flash('Failed to create organization', 'error')
                return render_template('settings/create_org.html')
        except DatabaseError as e:
            error_msg = str(e)
            if 'Duplicate entry' in error_msg or '1062' in error_msg:
                flash(f'An organization with domain "{org_domain}" already exists. Please choose a different domain or join the existing organization.', 'error')
            else:
                flash(f'Failed to create organization: {error_msg}', 'error')
            return render_template('settings/create_org.html')

        new_org_id = org_result[0].get('org_id')


        db.execute_proc('sp_assign_user_to_org', (user['user_id'], new_org_id, 'owner','active'), fetch=False)


        orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        if orgs:
            session['user_organizations'] = orgs

        flash(f'Organization "{org_name}" created successfully!', 'success')
        return redirect(url_for('settings_bp.index'))

    return render_template('settings/create_org.html')


@settings_bp.route('/organizations/join', methods=['GET', 'POST'])
@require_auth
def join_organization():
    """Join an existing organization by domain (only from user's email domain)"""
    user = g.current_user
    user_email = user.get('email') or session.get('email', '')


    user_domain = None
    if '@' in user_email:
        email_parts = user_email.split('@')
        if len(email_parts) == 2:
            user_domain = email_parts[1].lower()

    if request.method == 'POST':
        domain = request.form.get('domain')
        selected_org_id = request.form.get('org_id')

        if not domain:
            flash('Domain is required', 'error')
            return render_template('settings/join_org.html', existing_orgs=[], user_domain=user_domain)

        domain = domain.lower()


        if user_domain and domain != user_domain:
            flash(f'You can only join organizations with domain "{user_domain}" (your email domain).', 'error')
            return render_template('settings/join_org.html', existing_orgs=[], domain=domain, user_domain=user_domain)


        if selected_org_id:

            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                org = next((o for o in (orgs or []) if o.get('org_id') == selected_org_id or o['org_id'] == selected_org_id), None)

                if not org:
                    flash('Selected organization not found', 'error')
                    return render_template('settings/join_org.html', existing_orgs=orgs or [], domain=domain, user_domain=user_domain)


                user_orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
                if user_orgs:
                    for uo in user_orgs:
                        if uo.get('org_id') == selected_org_id or uo['org_id'] == selected_org_id:
                            flash('You are already a member of this organization', 'info')
                            return redirect(url_for('settings_bp.index'))


                db.execute_proc('sp_assign_user_to_org', (user['user_id'], selected_org_id, 'member','pending'), fetch=False)


                orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
                if orgs:
                    session['user_organizations'] = orgs

                flash(f'You have been added to {org["name"]}', 'success')
                return redirect(url_for('settings_bp.index'))
            except DatabaseError as e:
                flash(f'Error joining organization: {str(e)}', 'error')
                return render_template('settings/join_org.html', existing_orgs=[], domain=domain, user_domain=user_domain)
        else:
            flash('Please select an organization to join', 'error')

            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                return render_template('settings/join_org.html', existing_orgs=orgs or [], domain=domain, user_domain=user_domain)
            except DatabaseError:
                return render_template('settings/join_org.html', existing_orgs=[], domain=domain, user_domain=user_domain)


    domain = request.args.get('domain', '')
    existing_orgs = []
    if domain:
        domain = domain.lower()

        if user_domain and domain != user_domain:
            flash(f'You can only join organizations with domain "{user_domain}" (your email domain).', 'error')
        else:
            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                if orgs:
                    existing_orgs = orgs
            except DatabaseError:
                pass

    return render_template('settings/join_org.html', existing_orgs=existing_orgs, domain=domain, user_domain=user_domain)


@settings_bp.route('/organizations/<org_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_organization(org_id):
    """Edit organization details (only for owners)"""
    user = g.current_user
    current_org_id = g.current_org_id
    
    if org_id != current_org_id:
        flash('You can only edit the current organization', 'error')
        return redirect(url_for('settings_bp.index'))
    
    try:
        user_orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        current_org = next((o for o in (user_orgs or []) if o.get('org_id') == org_id or o['org_id'] == org_id), None)
        
        if not current_org:
            flash('Organization not found', 'error')
            return redirect(url_for('settings_bp.index'))
        
        if current_org.get('role') != 'owner' and current_org['role'] != 'owner':
            flash('Only organization owners can edit organization details', 'error')
            return redirect(url_for('settings_bp.index'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            street_address = request.form.get('street_address')
            city = request.form.get('city')
            state = request.form.get('state')
            zip_code = request.form.get('zip_code')
            country = request.form.get('country')
            
            if not name:
                flash('Organization name is required', 'error')
                org_details = db.execute_proc('sp_get_organization_details', (org_id,))
                org = org_details[0] if org_details and len(org_details) > 0 else None
                return render_template('settings/edit_org.html', organization=org)
            
            try:
                db.execute_proc('sp_update_organization', (
                    org_id,
                    name,
                    street_address or None,
                    city or None,
                    state or None,
                    zip_code or None,
                    country or None
                ), fetch=False)
                flash('Organization updated successfully', 'success')
                return redirect(url_for('settings_bp.index'))
            except DatabaseError as e:
                flash(f'Error updating organization: {str(e)}', 'error')
        
        org_details = db.execute_proc('sp_get_organization_details', (org_id,))
        org = org_details[0] if org_details and len(org_details) > 0 else None
        
        if not org:
            flash('Organization not found', 'error')
            return redirect(url_for('settings_bp.index'))
        
        return render_template('settings/edit_org.html', organization=org)
    except DatabaseError as e:
        flash(f'Error loading organization: {str(e)}', 'error')
        return redirect(url_for('settings_bp.index'))
    

@settings_bp.route('/members/approve', methods=['POST'])
@require_org
def approve_member():
    """Approve, Reject, or Deactivate a member"""
    org_id = g.current_org_id
    user_id = request.form.get('user_id')
    role = request.form.get('role') 
    action = request.form.get('action')

    if not user_id or not action:
        flash('Invalid request', 'error')
        return redirect(url_for('settings_bp.members'))

    try:
        if action == 'approve':
            if not role:
                flash('Role is required', 'error')
                return redirect(url_for('settings_bp.members'))
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'active', role), fetch=False)
            flash('Member approved', 'success')
            
        elif action == 'reject':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'rejected', 'viewer'), fetch=False)
            flash('User rejected and removed', 'info')
            
        elif action == 'deactivate':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'deactivated', 'viewer'), fetch=False)
            flash('Member deactivated. They can no longer access this organization.', 'warning')
            
        elif action == 'reactivate':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'active', 'member'), fetch=False)
            flash('Member reactivated successfully', 'success')

    except DatabaseError as e:
        flash(f'Error updating member: {str(e)}', 'error')

    return redirect(request.referrer or url_for('dashboard_bp.index'))

