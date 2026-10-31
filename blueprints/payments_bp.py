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


@payments_bp.route('/export.csv', methods=['POST'])
@require_org
def export_csv():
    """The payments shown (ids), as a CSV for the accountant: date, customer, document, bank reference, amount and the
    rupees credited (exports.payments_csv)."""
    from datetime import date

    from flask import g, make_response, request, url_for

    from db import db
    import exports
    import payments_view
    found = db.execute_proc('sp_list_org_payments', (g.current_org_id, None)) or []
    docs = db.execute_proc('sp_list_invoices', (g.current_org_id, None, 100000, 0)) or []
    wanted = set(request.form.getlist('ids'))
    rows = [r for r in payments_view.rows(found, docs, url_for) if not wanted or r['id'] in wanted]
    response = make_response(exports.payments_csv(rows))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="Payments-{date.today().isoformat()}.csv"'
    return response
