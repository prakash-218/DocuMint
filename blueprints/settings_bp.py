"""
Settings blueprint - Organization settings and preferences
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, jsonify
from db import db, DatabaseError
from auth import require_auth, require_org

settings_bp = Blueprint('settings_bp', __name__)


@settings_bp.route('/')
@require_org
def index():
    """Settings page"""
    org_id = g.current_org_id
    return render_template('settings/index.html')


@settings_bp.route('/select-org', methods=['GET', 'POST'])
@require_auth
def select_org():
    """Select organization context"""
    user = g.current_user
    
    if request.method == 'POST':
        org_id = request.form.get('org_id')
        if org_id:
            # Verify user has access to this org
            orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
            org = next((o for o in (orgs or []) if o['org_id'] == org_id), None)
            
            if org:
                session['org_id'] = org_id
                session['org_name'] = org['name']
                flash('Organization selected', 'success')
                return redirect(url_for('dashboard_bp.index'))
            else:
                flash('Invalid organization', 'error')
    
    # Get user organizations
    try:
        orgs = db.execute_proc('sp_get_user_organizations', (user['user_id'],))
        return render_template('settings/select_org.html', organizations=orgs or [])
    except DatabaseError as e:
        flash('Error loading organizations', 'error')
        return render_template('settings/select_org.html', organizations=[])



