"""
Logging in and out, and getting in: DocuMint is invite-only (invites.py), so there's no signing up. An invite's link
sets a password, and a forgotten one is set again from an emailed (or handed-over) link.
"""

from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from db import db, DatabaseError
from auth import verify_password, generate_token, hash_password, require_auth

auth_bp = Blueprint('auth_bp', __name__)


# ---------------------------------------------------------------- The pages (nav.public: frontend/src/public/ draws them)

def _login_page():
    import nav
    return nav.public('login', 'Log in', action=url_for('auth_bp.login'), register=url_for('auth_bp.register'),
                      forgot=url_for('auth_bp.forgot'), portal=url_for('customer_portal_bp.login'))


def _page(screen, title, **props):
    import nav
    return nav.public(screen, title, login=url_for('auth_bp.login'), **props)


def _sign_in(user_id, email, org_id=None):
    """A session for them, in org_id (or their first active organization)."""
    orgs = db.execute_proc('sp_get_user_organizations', (user_id,)) or []
    session.clear()
    session['user_id'], session['email'] = user_id, email
    if orgs:
        session['user_organizations'] = orgs
        org = next((o for o in orgs if str(o['org_id']) == str(org_id)), None) or next((o for o in orgs if o.get('status') == 'active'), orgs[0])
        session.update(org_id=org['org_id'], org_name=org['name'], org_status=org.get('status', 'active'))
    session['token'] = generate_token(user_id, email, session.get('org_id'))
    session.permanent = True


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
    """DocuMint is invite-only (invites.py): this says so, and how to get in."""
    return _page('invite_only', 'Invite only', forgot=url_for('auth_bp.forgot'))


def _invite_page(invite, problem='', has_account=False):
    import permissions
    props = {'problem': problem, 'forgot': url_for('auth_bp.forgot')}
    if invite and not problem:
        props.update(email=invite['email'], org=invite.get('org_name') or '', new_org=not invite.get('org_id'),
                     role=permissions.role_label(invite.get('role'), invite.get('role_name')),
                     invited_by=invite.get('invited_by') or '', has_account=has_account, action=request.path)
    return _page('accept_invite', 'Your invite', **props)


@auth_bp.route('/invite/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    """An invite's link: they set a password (or sign in, when the address has an account already), and they're in the
    organization with the invite's role, or the owner of the organization they start."""
    import invites
    invite = (db.execute_proc('sp_find_invite', (invites.token_hash(token),)) or [None])[0]
    problem = invites.state(invite)
    if problem != 'ok':
        return _invite_page(None, problem), 404 if problem == 'missing' else 410
    email = invite['email']
    user = db.execute_proc_single('sp_get_user_by_email', (email,))
    if request.method == 'GET':
        return _invite_page(invite, has_account=bool(user))

    password = request.form.get('password') or ''
    if user:
        if not verify_password(password, user['password_hash']):
            flash("That password isn't right. Forgot it? Set a new one, then open this invite again.", 'error')
            return _invite_page(invite, has_account=True)
    elif len(password) < 8 or password != request.form.get('confirm_password'):
        flash('Passwords must match and be at least 8 characters', 'error')
        return _invite_page(invite)
    org_id = invite.get('org_id')
    org_name = (request.form.get('org_name') or '').strip()
    if not org_id and not org_name:
        flash("Your organization's name is required", 'error')
        return _invite_page(invite, has_account=bool(user))
    try:
        if not user:
            user = {'user_id': db.execute_proc_single('sp_create_user', (email, hash_password(password), None))['user_id']}
        if not org_id:
            f = request.form
            org_id = db.execute_proc_single('sp_create_organization', (
                org_name, invites.own_domain(email), f.get('street_address') or None, f.get('city') or None, f.get('state') or None,
                f.get('zip_code') or None, f.get('country') or None, None))['org_id']
        db.execute_proc('sp_accept_invite', (invite['invite_id'], user['user_id'], org_id))
    except DatabaseError as e:
        flash(f"Couldn't finish: {e}", 'error')
        return _invite_page(invite, has_account=bool(user))
    if not invite.get('org_id'):
        try:
            from document_service import create_starter_templates
            create_starter_templates(org_id)                    # a quotation, a proforma and invoices to start from
        except Exception:                                       # noqa: BLE001: they can add them from the profile
            pass
    _sign_in(user['user_id'], email, org_id)
    flash(f"Welcome to {invite.get('org_name') or org_name}.", 'success')
    return redirect(url_for('dashboard_bp.index'))


@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    """Forgot the password: a link to set a new one, emailed from the mailbox of an organization they're in. The answer
    is the same whether or not the address has an account."""
    import invites
    if request.method == 'POST':
        email = invites.clean_email(request.form.get('email'))
        user = db.execute_proc_single('sp_get_user_by_email', (email,)) if email else None
        if user:
            token = invites.new_token()
            db.execute_proc('sp_create_password_reset', (user['user_id'], invites.token_hash(token), None, invites.RESET_MINUTES))
            link = url_for('auth_bp.reset_password', token=token, _external=True)
            orgs = [o for o in db.execute_proc('sp_get_user_organizations', (user['user_id'],)) or [] if o.get('status') == 'active']
            next((o for o in orgs if invites.send(o['org_id'], email, invites.reset_message(link), o['name'])), None)
        return _page('forgot', 'Forgot your password', action=url_for('auth_bp.forgot'), sent=True)
    return _page('forgot', 'Forgot your password', action=url_for('auth_bp.forgot'), sent=False)


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """A reset link: a new password, once."""
    import invites
    reset = (db.execute_proc('sp_find_password_reset', (invites.token_hash(token),)) or [None])[0]
    if not reset:
        return _page('reset', 'New password', problem=True, forgot=url_for('auth_bp.forgot')), 410
    if request.method == 'POST':
        password = request.form.get('password') or ''
        if len(password) < 8 or password != request.form.get('confirm_password'):
            flash('Passwords must match and be at least 8 characters', 'error')
        else:
            db.execute_proc('sp_use_password_reset', (reset['reset_id'], hash_password(password)))
            flash('Your new password is set. Log in with it.', 'success')
            return redirect(url_for('auth_bp.login'))
    return _page('reset', 'New password', email=reset['email'], action=request.path, problem=False)


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth_bp.login'))

