"""The suppliers list: the companies we buy from (customers marked supplier, customer_view.listing), in the React app."""

from flask import Blueprint

from auth import require_org

suppliers_bp = Blueprint('suppliers_bp', __name__)


@suppliers_bp.route('/')
@require_org
def list_suppliers():
    """Suppliers, in the React app (GET /api/customers?kind=supplier)."""
    import nav
    return nav.spa('Suppliers', 'list')
