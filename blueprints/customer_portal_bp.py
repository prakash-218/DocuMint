"""
Customer Portal Blueprint - Customer-facing routes for viewing invoices
"""

import logging
import doc_urls
from flask import Blueprint, request, redirect, url_for, flash, session, g, jsonify
from db import db, DatabaseError
from auth import require_customer_auth, verify_password
from access import get_customer_invoice
from invoice_service import render_invoice_pdf, PdfUnavailable

logger = logging.getLogger(__name__)

customer_portal_bp = Blueprint('customer_portal_bp', __name__)
doc_urls.install(customer_portal_bp)


def _login_page():
    import nav
    return nav.public('portal_login', 'Customer portal', action=url_for('customer_portal_bp.login'),
                      staff=url_for('auth_bp.login'))


@customer_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Customer login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'error')
            return _login_page()

        try:

            user_result = db.execute_proc_single('sp_get_customer_user_by_email', (email,))

            if not user_result:
                flash('Invalid email or password', 'error')
                return _login_page()


            if not verify_password(password, user_result['password_hash']):
                flash('Invalid email or password', 'error')
                return _login_page()

            customer_info = {
                'customer_user_id': user_result['customer_user_id'],
                'customer_id': user_result['customer_id'],
                'email': user_result['email'],
                'customer_name': user_result['customer_name'],
                'org_id': user_result.get('org_id')
            }


            session['customer_user_id'] = customer_info['customer_user_id']
            session['customer_id'] = customer_info['customer_id']
            session['customer_email'] = customer_info['email']
            session['customer_name'] = customer_info['customer_name']
            session['customer_org_id'] = customer_info.get('org_id')

            flash('Login successful', 'success')
            return redirect(url_for('customer_portal_bp.dashboard'))

        except DatabaseError as e:
            flash('Login failed. Please try again.', 'error')
            return _login_page()

    return _login_page()


@customer_portal_bp.route('/logout', methods=['POST'])
@require_customer_auth
def logout():
    """Customer logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('customer_portal_bp.login'))


@customer_portal_bp.route('/')
@require_customer_auth
def dashboard():
    """A customer's documents, in the portal's React app (portal_view.documents)."""
    import nav
    return nav.portal('My documents', 'list')


@customer_portal_bp.route('/invoice/<invoice_id>', defaults={'pdf': False})
@customer_portal_bp.route('/invoice/<invoice_id>/pdf', defaults={'pdf': True})
def legacy_invoice_link(invoice_id, pdf):
    """Links sent before documents had /quotes, /proformas, /invoices URLs."""
    return redirect(url_for('customer_portal_bp.export_pdf' if pdf else 'customer_portal_bp.view_invoice',
                            invoice_id=invoice_id), code=301)


@customer_portal_bp.route('/' + doc_urls.SEGMENT + '/<invoice_id>')
@require_customer_auth
def view_invoice(invoice_id):
    """View invoice details (customer view)"""
    """One document, in the portal's React app (portal_view.document)."""
    import nav
    from documents import display_number
    invoice_header, _ = get_customer_invoice(invoice_id, g.current_customer_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('customer_portal_bp.dashboard'))
    return nav.portal(display_number(invoice_header), 'doc')


# ---------------------------------------------------------------- JSON for the portal's React app

def _signed_in():
    """The customer, set on g as require_customer_auth does; None (and the API answers 401) when nobody is signed in."""
    from auth import get_current_customer
    customer = get_current_customer()
    if customer:
        g.current_customer, g.current_customer_id = customer, customer['customer_id']
    return customer


@customer_portal_bp.route('/api/documents')
def api_documents():
    """The customer's documents, a page at a time (portal_view.documents)."""
    import portal_view
    if not _signed_in():
        return jsonify(error='Sign in first'), 401
    try:
        return jsonify(portal_view.documents(g.current_customer_id, url_for))
    except DatabaseError:
        logger.exception("Failed to load the documents of customer %s", g.current_customer_id)
        return jsonify(error="Couldn't load your documents"), 500


@customer_portal_bp.route('/api/documents/<invoice_id>')
def api_document(invoice_id):
    """One of the customer's documents (portal_view.document); never another customer's, never a draft."""
    import portal_view
    if not _signed_in():
        return jsonify(error='Sign in first'), 401
    header, values = get_customer_invoice(invoice_id, g.current_customer_id)
    if not header:
        return jsonify(error='Not found'), 404
    try:
        return jsonify(portal_view.document(header, values, url_for))
    except DatabaseError:
        logger.exception("Failed to load invoice %s for customer", invoice_id)
        return jsonify(error="Couldn't load that document"), 500


@customer_portal_bp.route('/' + doc_urls.SEGMENT + '/<invoice_id>/pdf')
@require_customer_auth
def export_pdf(invoice_id):
    """Export invoice as PDF (customer view)"""
    invoice_header, invoice_values = get_customer_invoice(invoice_id, g.current_customer_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('customer_portal_bp.dashboard'))

    try:
        return render_invoice_pdf(invoice_header, invoice_values, request.args.get('copies', 1, type=int),
                                  packing=request.args.get('packing') == '1', page_key=request.args.get('page'))
    except LookupError:
        flash('That page isn\'t available', 'error')
    except PdfUnavailable:
        flash('PDF export is not available right now', 'error')
    except Exception:
        logger.exception("PDF generation failed for invoice %s", invoice_id)
        flash('Error generating PDF', 'error')
    return redirect(url_for('customer_portal_bp.view_invoice', invoice_id=invoice_id))
