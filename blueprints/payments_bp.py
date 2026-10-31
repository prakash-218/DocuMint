"""The payments list: every payment received, with its bank reference (payments_view, in the React app)."""

from flask import Blueprint

from auth import require_org

payments_bp = Blueprint('payments_bp', __name__)


@payments_bp.route('/')
@require_org
def index():
    """Payments, in the React app (payments_view.build, from api_bp.payments)."""
    import nav
    return nav.spa('Payments', 'list')
