"""
Settings blueprint - Organization settings and preferences
"""

import logging
import re
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, jsonify
from db import db, DatabaseError
from auth import require_auth, require_org
from store.schema import ROLES
from access import safe_referrer
import nav

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings_bp', __name__)


# ---------------------------------------------------------------- Choosing, making and joining an organization
# Pages outside the app (nav.public), as signing in is: they're for people who may not be in an organization yet.

def _select_org_page(orgs):
    return nav.public('select_org', 'Choose an organization', action=url_for('settings_bp.select_org'),
                      orgs=[{'id': str(o.get('org_id')), 'name': o.get('name') or '', 'domain': o.get('domain') or '',
                             'status': o.get('status') or 'active'} for o in orgs or []],
                      logout=url_for('auth_bp.logout'))


def _create_org_page():
    return nav.public('create_org', 'Create an organization', action=url_for('settings_bp.create_organization'),
                      cancel=url_for('settings_bp.index'))


def _join_org_page(existing_orgs=None, domain='', user_domain=None):
    return nav.public('join_org', 'Join an organization', action=url_for('settings_bp.join_organization'),
                      domain=domain or '', user_domain=user_domain or '', cancel=url_for('settings_bp.index'),
                      create=url_for('settings_bp.create_organization'),
                      orgs=[{'id': str(o.get('org_id')), 'name': o.get('name') or '', 'domain': o.get('domain') or ''}
                            for o in existing_orgs or []])


@settings_bp.route('/')
@require_org
def index():
    """The settings page, in the React app (settings_view.index)."""
    import nav
    return nav.spa('Settings', 'page')


@settings_bp.route('/select-org', methods=['GET', 'POST'])
@require_auth
def select_org():
    """Select organization context"""
    try:
        user = g.current_user
        logger.info(f"select_org called - User ID: {user.get('user_id') if user else 'None'}, Method: {request.method}")

        if request.method == 'POST':
            org_id = request.form.get('org_id')
            logger.info(f"POST request - org_id from form: {org_id}, type: {type(org_id)}")
            
            if not org_id:
                logger.warning("No org_id provided in POST request")
                flash('Organization ID is required', 'error')
                return redirect(url_for('settings_bp.select_org'))

            try:
                orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
                logger.info(f"Retrieved {len(orgs) if orgs else 0} organizations for user")
                
                if orgs:
                    logger.debug(f"Available org IDs: {[str(o.get('org_id', '')) for o in orgs]}")
                    logger.debug(f"Looking for org_id: {str(org_id)}")
                
                # Compare org_id as strings to handle UUID format differences
                org = next((o for o in (orgs or []) if str(o.get('org_id', '')) == str(org_id)), None)

                if org:
                    logger.info(f"Organization found: {org.get('name')}, Status: {org.get('status')}")
                    
                    try:
                        session['org_id'] = str(org_id)  # Ensure it's a string
                        session['org_name'] = org.get('name')
                        session['org_status'] = org.get('status', 'active')
                        logger.info(f"Session updated - org_id: {session.get('org_id')}, org_name: {session.get('org_name')}, org_status: {session.get('org_status')}")

                        if org.get('status') != 'active':
                            logger.warning(f"Organization status is not active: {org.get('status')}")
                            return render_template('errors/org_status.html', 
                                                 status=org.get('status'), 
                                                 org_name=org.get('name'))

                        # Refresh user organizations list
                        orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
                        if orgs:
                            session['user_organizations'] = orgs
                            logger.info(f"User organizations list refreshed: {len(orgs)} orgs")
                        
                        # Regenerate token with new org_id
                        from auth import generate_token
                        new_token = generate_token(user['user_id'], user.get('email'), str(org_id))
                        session['token'] = new_token
                        logger.info("Token regenerated successfully")
                        
                        flash('Organization switched successfully', 'success')
                        redirect_url = safe_referrer('dashboard_bp.index')
                        logger.info(f"Redirecting to: {redirect_url}")
                        return redirect(redirect_url)
                    except Exception as e:
                        logger.error(f"Error updating session or generating token: {str(e)}", exc_info=True)
                        flash(f'Error switching organization: {str(e)}', 'error')
                        return redirect(url_for('settings_bp.select_org'))
                else:
                    logger.warning(f"Organization not found or user doesn't have access - org_id: {org_id}")
                    logger.debug(f"User {user['user_id']} tried to switch to org {org_id}")
                    logger.debug(f"User has access to orgs: {[str(o.get('org_id')) for o in (orgs or [])]}")
                    flash('You do not have access to this organization', 'error')
                    return redirect(url_for('settings_bp.select_org'))
                    
            except DatabaseError as e:
                logger.error(f"Database error in select_org POST: {str(e)}", exc_info=True)
                flash(f'Error loading organizations: {str(e)}', 'error')
                return redirect(url_for('settings_bp.select_org'))
            except Exception as e:
                logger.error(f"Unexpected error in select_org POST: {str(e)}", exc_info=True)
                flash(f'An unexpected error occurred: {str(e)}', 'error')
                return redirect(url_for('settings_bp.select_org'))

        # GET request
        try:
            orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
            logger.info(f"GET request - Loaded {len(orgs) if orgs else 0} organizations")
            return _select_org_page(orgs or [])
        except DatabaseError as e:
            logger.error(f"Database error in select_org GET: {str(e)}", exc_info=True)
            flash('Error loading organizations', 'error')
            return _select_org_page([])
    except Exception as e:
        logger.error(f"Critical error in select_org: {str(e)}", exc_info=True)
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('dashboard_bp.index'))


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
            return _create_org_page()

        if not org_domain:
            flash('Organization domain is required', 'error')
            return _create_org_page()


        try:
            existing_orgs = db.execute_proc('sp_find_organizations_by_domain', (org_domain.lower(),))
            if existing_orgs:
                for org in existing_orgs:
                    if org.get('name') == org_name or org['name'] == org_name:
                        flash(f'An organization named "{org_name}" with domain "{org_domain}" already exists. Please choose a different name or domain.', 'error')
                        return _create_org_page()
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
                return _create_org_page()
        except DatabaseError as e:
            error_msg = str(e)
            if 'Duplicate entry' in error_msg or '1062' in error_msg:
                flash(f'An organization with domain "{org_domain}" already exists. Please choose a different domain or join the existing organization.', 'error')
            else:
                flash(f'Failed to create organization: {error_msg}', 'error')
            return _create_org_page()

        new_org_id = org_result[0].get('org_id')


        db.execute_proc('sp_assign_user_to_org', (user['user_id'], new_org_id, 'owner','active'), fetch=False)


        orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        if orgs:
            session['user_organizations'] = orgs

        flash(f'Organization "{org_name}" created successfully!', 'success')
        return redirect(url_for('settings_bp.index'))

    return _create_org_page()


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
            return _join_org_page(existing_orgs=[], user_domain=user_domain)

        domain = domain.lower()


        if user_domain and domain != user_domain:
            flash(f'You can only join organizations with domain "{user_domain}" (your email domain).', 'error')
            return _join_org_page(existing_orgs=[], domain=domain, user_domain=user_domain)


        if selected_org_id:

            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                org = next((o for o in (orgs or []) if o.get('org_id') == selected_org_id or o['org_id'] == selected_org_id), None)

                if not org:
                    flash('Selected organization not found', 'error')
                    return _join_org_page(existing_orgs=orgs or [], domain=domain, user_domain=user_domain)


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
                return _join_org_page(existing_orgs=[], domain=domain, user_domain=user_domain)
        else:
            flash('Please select an organization to join', 'error')

            try:
                orgs = db.execute_proc('sp_find_organizations_by_domain', (domain,))
                return _join_org_page(existing_orgs=orgs or [], domain=domain, user_domain=user_domain)
            except DatabaseError:
                return _join_org_page(existing_orgs=[], domain=domain, user_domain=user_domain)


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

    return _join_org_page(existing_orgs=existing_orgs, domain=domain, user_domain=user_domain)


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
                return nav.spa('Name & address', 'page', posted=True)
            
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
        
        return nav.spa('Name & address', 'page', posted=request.method == 'POST')   # the form: settings_view.organization
    except DatabaseError as e:
        flash(f'Error loading organization: {str(e)}', 'error')
        return redirect(url_for('settings_bp.index'))
    

@settings_bp.route('/members/approve', methods=['POST'])
@require_org
def approve_member():
    """Approve, Reject, Deactivate, Reactivate, or Change Role of a member"""
    org_id = g.current_org_id
    user_id = request.form.get('user_id')
    role = request.form.get('role') 
    action = request.form.get('action')
    
    # Check if current user is owner
    current_role = None
    if session.get('user_organizations'):
        for org in session['user_organizations']:
            if str(org.get('org_id')) == str(org_id):
                current_role = org.get('role')
                break
    
    if current_role not in ('owner', 'admin'):
        flash('Only owners and admins can manage the team', 'error')
        return redirect(safe_referrer('settings_bp.index'))

    if not user_id or not action:
        flash('Invalid request', 'error')
        return redirect(safe_referrer('settings_bp.index'))

    if role and role not in ROLES:
        flash('Invalid role', 'error')
        return redirect(safe_referrer('settings_bp.index'))

    # Admins manage members and viewers; only owners make or change owners
    if current_role == 'admin':
        target = next((m for m in db.execute_proc('sp_get_org_members', (org_id,)) or []
                       if str(m.get('user_id')) == str(user_id)), None)
        if role == 'owner' or (target and target.get('role') == 'owner'):
            flash('Only an owner can make or change owners', 'error')
            return redirect(safe_referrer('settings_bp.index'))

    if str(user_id) == str(g.current_user['user_id']) and (
            action in ('reject', 'deactivate') or (action == 'change_role' and role != current_role)):
        flash('You cannot remove or demote yourself. Ask another owner to do it.', 'error')
        return redirect(safe_referrer('settings_bp.index'))

    try:
        if action == 'approve':
            if not role:
                flash('Role is required', 'error')
                return redirect(safe_referrer('settings_bp.index'))
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'active', role), fetch=False)
            flash('Member approved', 'success')
            
        elif action == 'reject':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'rejected', 'viewer'), fetch=False)
            flash('User rejected and removed', 'info')
            
        elif action == 'deactivate':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'deactivated', None), fetch=False)
            flash('Member deactivated. They can no longer access this organization.', 'warning')
            
        elif action == 'reactivate':
            db.execute_proc('sp_update_member_status', (org_id, user_id, 'active', 'member'), fetch=False)
            flash('Member reactivated successfully', 'success')
            
        elif action == 'change_role':
            if not role:
                flash('Role is required', 'error')
                return redirect(safe_referrer('settings_bp.index'))
            # Get current member status to preserve it
            members = db.execute_proc('sp_get_org_members', (org_id,))
            current_member = next((m for m in (members or []) if m.get('user_id') == user_id), None)
            current_status = current_member.get('status', 'active') if current_member else 'active'
            db.execute_proc('sp_update_member_status', (org_id, user_id, current_status, role), fetch=False)
            flash(f'Member role changed to {role.title()} successfully', 'success')

    except DatabaseError as e:
        flash(f'Error updating member: {str(e)}', 'error')

    return redirect(safe_referrer('settings_bp.index'))


@settings_bp.route('/audit-log')
@require_org
def audit_log():
    """View audit log (owners only)"""
    org_id = g.current_org_id
    
    # Get current role
    current_role = None
    if session.get('user_organizations'):
        for org in session['user_organizations']:
            if str(org.get('org_id')) == str(org_id):
                current_role = org.get('role')
                break
    
    if current_role not in ('owner', 'admin'):
        flash('Only owners and admins can view the audit log', 'error')
        return redirect(url_for('settings_bp.index'))
    
    return nav.spa('Audit log', 'list')                    # the list: settings_view.audit



# ---------------------------------------------------------------- Business profile

PROFILE_TEXT_FIELDS = (
    'gstin', 'pan', 'iec_code', 'lut_number', 'ad_code', 'state_code', 'phone', 'email', 'website',
    'bank_name', 'bank_account', 'bank_ifsc', 'bank_branch', 'bank_swift', 'signatory_name',
    'quote_intro', 'quote_terms', 'quote_closing', 'footer_note',
)
PROFILE_IMAGES = ('logo', 'logo_small', 'stamp', 'signature')
MAX_IMAGE_BYTES = 300 * 1024
CURRENCIES = ('INR', 'USD', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD', 'AED')


def _current_role(org_id):
    for org in session.get('user_organizations') or []:
        if str(org.get('org_id')) == str(org_id):
            return org.get('role')
    return None


def _image_data_uri(upload):
    """Read an uploaded PNG/JPEG into a data: URI (stored in the profile; PDFs embed it directly)."""
    import base64
    data = upload.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f'{upload.filename}: images must be under {MAX_IMAGE_BYTES // 1024} KB')
    if data.startswith(b'\x89PNG'):
        mime = 'image/png'
    elif data.startswith(b'\xff\xd8'):
        mime = 'image/jpeg'
    else:
        raise ValueError(f'{upload.filename}: use a PNG or JPEG image')
    return f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')


@settings_bp.route('/profile', methods=['GET', 'POST'])
@require_org
def business_profile():
    """Tax registrations, bank details, numbering and document defaults (owners only)."""
    from documents import DOC_TYPES
    from document_service import get_org_profile, save_org_profile, set_next_number

    org_id = g.current_org_id
    if _current_role(org_id) not in ('owner', 'admin'):
        flash('Only organization owners can change the business profile', 'error')
        return redirect(url_for('settings_bp.index'))

    org, profile = get_org_profile(org_id)

    if request.method == 'POST':
        for key in PROFILE_TEXT_FIELDS:
            value = (request.form.get(key) or '').strip()
            if value:
                profile[key] = value
            else:
                profile.pop(key, None)
        profile['gstin'] = profile.get('gstin', '').upper() or None
        if not profile['gstin']:
            profile.pop('gstin')

        currency = request.form.get('default_currency')
        profile['default_currency'] = currency if currency in CURRENCIES else 'INR'
        try:
            profile['default_gst_rate'] = max(0.0, min(100.0, float(request.form.get('default_gst_rate') or 18)))
            month = int(request.form.get('fy_start_month') or 4)
            profile['fy_start_month'] = month if 1 <= month <= 12 else 4
        except ValueError:
            flash('GST rate and financial-year month must be numbers', 'error')
            return redirect(url_for('settings_bp.business_profile'))
        from contacts import team_addresses
        team, not_addresses = team_addresses(request.form.get('team_addresses') or '')
        if not_addresses:
            flash(f"Not an email address: {', '.join(not_addresses[:3])}", 'error')
            return redirect(url_for('settings_bp.business_profile'))
        if team:
            profile['team_addresses'] = team
        else:
            profile.pop('team_addresses', None)
        from payment_terms import parse_days
        days, problem = parse_days(request.form.get('payment_days'))
        if problem:
            flash(problem, 'error')
            return redirect(url_for('settings_bp.business_profile'))
        if days is None:
            profile.pop('payment_days', None)
        else:
            profile['payment_days'] = days
        profile['advance_basis'] = 'total' if request.form.get('advance_basis') == 'total' else 'pre_tax'
        profile['separate_export_series'] = bool(request.form.get('separate_export_series'))
        # The quotation letterhead (templates/pdf/quote.html)
        profile['letterhead_style'] = 'left' if request.form.get('letterhead_style') == 'left' else 'centred'
        for key in ('letterhead_color', 'letterhead_accent'):
            colour = (request.form.get(key) or '').strip().lower()
            if re.fullmatch(r'#[0-9a-f]{6}', colour):
                profile[key] = colour
            else:
                profile.pop(key, None)
        profile['logo_has_name'] = bool(request.form.get('logo_has_name'))
        from layout import defs_from_form
        profile['custom_fields'] = defs_from_form(request.form, 'orgcf', with_value=True)
        profile['customer_fields'] = defs_from_form(request.form, 'custcf', with_value=False)

        formats = {}
        for key in DOC_TYPES:
            pattern = (request.form.get(f'format_{key}') or '').strip()
            if pattern:
                if '{num' not in pattern:
                    flash(f'Number format for {DOC_TYPES[key].label} must contain {{num}}', 'error')
                    return redirect(url_for('settings_bp.business_profile'))
                formats[key] = pattern
        profile['number_formats'] = formats

        try:
            for name in PROFILE_IMAGES:
                upload = request.files.get(name)
                if request.form.get(f'remove_{name}'):
                    profile.pop(name, None)
                elif upload and upload.filename:
                    profile[name] = _image_data_uri(upload)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('settings_bp.business_profile'))

        try:
            save_org_profile(org_id, profile)
            from document_service import series_key
            for key in DOC_TYPES:
                raw = (request.form.get(f'next_{key}') or '').strip()
                if raw and series_key(key, profile) == key:   # shared series are set via their owner
                    set_next_number(org_id, key, profile, int(raw))
        except (DatabaseError, ValueError) as e:
            logger.exception("Failed to save business profile for %s", org_id)
            flash(f'Could not save the profile: {e}', 'error')
            return redirect(url_for('settings_bp.business_profile'))

        flash('Business profile saved', 'success')
        return redirect(url_for('settings_bp.business_profile'))

    return nav.spa('Business profile', 'page')             # the form: settings_view.profile


@settings_bp.route('/profile/starter-templates', methods=['POST'])
@require_org
def starter_templates():
    from document_service import create_starter_templates

    org_id = g.current_org_id
    if _current_role(org_id) not in ('owner', 'admin'):
        flash('Only organization owners can add templates', 'error')
        return redirect(url_for('settings_bp.index'))
    try:
        created = create_starter_templates(org_id)
    except DatabaseError:
        logger.exception("Failed to create starter templates for %s", org_id)
        flash('Could not create the starter templates', 'error')
        return redirect(url_for('settings_bp.business_profile'))
    if created:
        flash(f'Added templates: {", ".join(created)}', 'success')
    else:
        flash('The starter templates already exist', 'info')
    return redirect(url_for('templates_bp.list_templates'))
