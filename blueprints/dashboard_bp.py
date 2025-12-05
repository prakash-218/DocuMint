"""
Dashboard blueprint - main dashboard with statistics
"""

from flask import Blueprint, render_template, session, g
from db import db, DatabaseError
from auth import require_org

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/')
@require_org
def index():
    """Dashboard home page"""
    org_id = g.current_org_id

    try:

        stats = db.execute_proc_single('sp_get_dashboard_stats', (org_id,))


        recent_invoices = db.execute_proc('sp_list_invoices', (org_id, None, 10, 0))


        revenue_timeseries = db.execute_proc('sp_get_revenue_timeseries', (org_id,))
        status_distribution = db.execute_proc('sp_get_invoice_status_distribution', (org_id,))
        revenue_by_status = db.execute_proc('sp_get_revenue_by_status', (org_id,))


        print("DEBUG: revenue_timeseries raw:", revenue_timeseries)
        print("DEBUG: status_distribution raw:", status_distribution)
        print("DEBUG: revenue_by_status raw:", revenue_by_status)


        if recent_invoices is None:
            recent_invoices = []
        elif not isinstance(recent_invoices, list):
            recent_invoices = [recent_invoices] if recent_invoices else []


        if revenue_timeseries is None:
            revenue_timeseries = []
        elif not isinstance(revenue_timeseries, list):
            revenue_timeseries = [revenue_timeseries] if revenue_timeseries else []

        if status_distribution is None:
            status_distribution = []
        elif not isinstance(status_distribution, list):
            status_distribution = [status_distribution] if status_distribution else []

        if revenue_by_status is None:
            revenue_by_status = []
        elif not isinstance(revenue_by_status, list):
            revenue_by_status = [revenue_by_status] if revenue_by_status else []

        print("DEBUG: revenue_timeseries processed:", revenue_timeseries)

        return render_template('dashboard.html',
                             stats=stats or {},
                             recent_invoices=recent_invoices,
                             revenue_timeseries=revenue_timeseries,
                             status_distribution=status_distribution,
                             revenue_by_status=revenue_by_status)
    except DatabaseError as e:
        import traceback
        traceback.print_exc()
        return render_template('dashboard.html',
                             stats={},
                             recent_invoices=[],
                             revenue_timeseries=[],
                             status_distribution=[],
                             revenue_by_status=[],
                             error=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('dashboard.html',
                             stats={},
                             recent_invoices=[],
                             revenue_timeseries=[],
                             status_distribution=[],
                             revenue_by_status=[],
                             error=str(e))

