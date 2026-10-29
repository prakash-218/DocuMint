"""
Dashboard blueprint - Home
"""

from flask import Blueprint, redirect, url_for

import nav
from auth import require_org

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/new')
@require_org
def index_new():
    """Where the new home was while it was opt-in."""
    return redirect(url_for('dashboard_bp.index'))


@dashboard_bp.route('/')
@require_org
def index():
    """Home, in the React app (frontend/src/islands/home/): what needs doing first, and the money to come in."""
    return nav.spa('Home', 'home')
