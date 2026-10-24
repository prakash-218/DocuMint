"""
Customer Portal Blueprint - Customer-facing routes for viewing invoices
"""

import logging
import doc_urls
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g
from db import db, DatabaseError
from auth import require_customer_auth, verify_password
from access import get_customer_invoice
from app_helpers import invoice_is_overdue
from documents import balance_of, get_type, sum_by_currency
from invoice_service import build_sections, invoice_summary, render_invoice_pdf, PdfUnavailable

logger = logging.getLogger(__name__)

customer_portal_bp = Blueprint('customer_portal_bp', __name__)
doc_urls.install(customer_portal_bp)


@customer_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Customer login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('customer/login.html')

        try:

            user_result = db.execute_proc_single('sp_get_customer_user_by_email', (email,))

            if not user_result:
                flash('Invalid email or password', 'error')
                return render_template('customer/login.html')


            if not verify_password(password, user_result['password_hash']):
                flash('Invalid email or password', 'error')
                return render_template('customer/login.html')

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
            return render_template('customer/login.html')

    return render_template('customer/login.html')


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
    """Customer dashboard"""
    customer_id = g.current_customer_id

    try:
        invoices = db.execute_proc('sp_get_customer_invoices', (customer_id,))
        if invoices is None:
            invoices = []
        elif not isinstance(invoices, list):
            invoices = [invoices] if invoices else []

        payable = [i for i in invoices if get_type(i.get('doc_type')).takes_payments and i.get('status') == 'pending']
        stats = {
            'outstanding': sum_by_currency(payable, balance_of),
            'overdue': sum(1 for i in payable if invoice_is_overdue(i)),
            'paid': sum_by_currency(invoices, lambda i: i.get('paid_amount')),
        }
        return render_template('customer/dashboard.html', invoices=invoices, stats=stats)
    except DatabaseError as e:
        flash(f'Error loading invoices: {str(e)}', 'error')
        return render_template('customer/dashboard.html', invoices=[], stats={'outstanding': {}, 'overdue': 0, 'paid': {}})


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
    invoice_header, invoice_values = get_customer_invoice(invoice_id, g.current_customer_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('customer_portal_bp.dashboard'))

    try:
        sections_data = build_sections(invoice_header, invoice_values)
        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,)) or []
    except DatabaseError:
        logger.exception("Failed to load invoice %s for customer", invoice_id)
        flash('Error loading invoice', 'error')
        return redirect(url_for('customer_portal_bp.dashboard'))

    return render_template('customer/invoice_view.html',
                           invoice=invoice_header,
                           sections_data=sections_data,
                           payments=payments,
                           summary=invoice_summary(invoice_header, sections_data, payments))


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
