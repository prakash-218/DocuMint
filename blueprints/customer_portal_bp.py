"""
Customer Portal Blueprint - Customer-facing routes for viewing invoices
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, make_response
from db import db, DatabaseError
from auth import authenticate_customer, get_current_customer, require_customer_auth, verify_password, hash_password
from datetime import datetime

# Check if PDF generation is available
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

customer_portal_bp = Blueprint('customer_portal_bp', __name__)


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


@customer_portal_bp.route('/logout')
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

        return render_template('customer/dashboard.html', invoices=invoices)
    except DatabaseError as e:
        flash(f'Error loading invoices: {str(e)}', 'error')
        return render_template('customer/dashboard.html', invoices=[])


@customer_portal_bp.route('/invoice/<invoice_id>')
@require_customer_auth
def view_invoice(invoice_id):
    """View invoice details (customer view)"""
    customer_id = g.current_customer_id

    try:

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))

        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))


        invoice_header = None
        invoice_values = []

        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result) >= 1 and len(result[0]) > 0:
                        invoice_header = result[0][0]
                    if len(result) >= 2:
                        invoice_values = result[1]
                elif isinstance(result[0], dict):
                    invoice_header = result[0]
                    if len(result) > 1:
                        invoice_values = result[1:]
        elif isinstance(result, dict):
            invoice_header = result

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))


        if invoice_header.get('customer_id') != customer_id:
            flash('Access denied', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))


        sections_data = {}

        for value in (invoice_values or []):
            section_title = value.get('section_title', '') or value.get('section_title', 'Untitled Section')
            section_type = value.get('section_type', 'normal') or 'normal'
            field_label = value.get('field_label', '')
            data_type = value.get('data_type', 'string')

            if not section_title:
                section_title = 'Untitled Section'

            if section_title not in sections_data:
                sections_data[section_title] = {
                    'type': section_type,
                    'fields': [],
                    'line_item_rows': {} if section_type == 'line_item' else None,
                    'line_item_headers': [] if section_type == 'line_item' else None
                }

            if section_type == 'line_item':

                ordinal = value.get('value_ordinal', 0)
                if ordinal is None:
                    ordinal = 0

                if ordinal not in sections_data[section_title]['line_item_rows']:
                    sections_data[section_title]['line_item_rows'][ordinal] = []

                sections_data[section_title]['line_item_rows'][ordinal].append(value)
            else:
                sections_data[section_title]['fields'].append(value)


        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item' and section_info['line_item_rows']:

                field_order = {}
                for ordinal, values in section_info['line_item_rows'].items():
                    for value in values:
                        field_id = value.get('field_id')
                        field_label = value.get('field_label', '')
                        field_ordinal = value.get('field_ordinal', 0) or 0
                        if field_id and field_id not in field_order:
                            field_order[field_id] = {
                                'label': field_label,
                                'ordinal': field_ordinal
                            }


                sorted_fields = sorted(field_order.items(), key=lambda x: x[1]['ordinal'])
                section_info['line_item_headers'] = [f[1]['label'] for f in sorted_fields]
                field_ids_ordered = [f[0] for f in sorted_fields]


                organized_rows = []
                for ordinal in sorted(section_info['line_item_rows'].keys()):
                    row_values = section_info['line_item_rows'][ordinal]

                    row_dict = {v.get('field_id'): v for v in row_values}

                    organized_row = [row_dict.get(fid) for fid in field_ids_ordered]
                    organized_rows.append(organized_row)

                section_info['line_item_rows'] = organized_rows


        from calculations import calculate_invoice_fields
        calculated_values = calculate_invoice_fields(invoice_values or [], sections_data)


        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item':

                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value and value.get('calculation_formula'):
                                field_id = value.get('field_id')
                                key = (field_id, row_idx)
                                if key in calculated_values:
                                    value['val_number'] = calculated_values[key]
                                    value['calculated'] = True
            else:

                for value in section_info.get('fields', []):
                    if value and value.get('calculation_formula'):
                        field_id = value.get('field_id')
                        key = (field_id, 0)
                        if key in calculated_values:
                            value['val_number'] = calculated_values[key]
                            value['calculated'] = True


        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,))

        return render_template('customer/invoice_view.html',
                             invoice=invoice_header,
                             values=invoice_values or [],
                             sections_data=sections_data,
                             payments=payments or [])
    except DatabaseError as e:
        flash('Error loading invoice', 'error')
        return redirect(url_for('customer_portal_bp.dashboard'))


@customer_portal_bp.route('/invoice/<invoice_id>/pdf')
@require_customer_auth
def export_pdf(invoice_id):
    """Export invoice as PDF (customer view)"""
    if not PDF_AVAILABLE:
        flash('PDF export is not available. Please install xhtml2pdf: pip install xhtml2pdf', 'error')
        return redirect(url_for('customer_portal_bp.view_invoice', invoice_id=invoice_id))

    customer_id = g.current_customer_id

    try:
        # Get invoice details
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))

        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))

        # Parse invoice data
        invoice_header = None
        invoice_values = []

        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result) >= 1 and len(result[0]) > 0:
                        invoice_header = result[0][0]
                    if len(result) >= 2:
                        invoice_values = result[1]
                elif isinstance(result[0], dict):
                    invoice_header = result[0]
                    if len(result) > 1:
                        invoice_values = result[1:]
        elif isinstance(result, dict):
            invoice_header = result

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))

        # Verify customer has access to this invoice
        if invoice_header.get('customer_id') != customer_id:
            flash('Access denied', 'error')
            return redirect(url_for('customer_portal_bp.dashboard'))

        # Build sections data
        sections_data = {}

        for value in (invoice_values or []):
            section_title = value.get('section_title', '') or 'Untitled Section'
            section_type = value.get('section_type', 'normal') or 'normal'

            if section_title not in sections_data:
                sections_data[section_title] = {
                    'type': section_type,
                    'fields': [],
                    'line_item_rows': {} if section_type == 'line_item' else None,
                    'line_item_headers': [] if section_type == 'line_item' else None
                }

            if section_type == 'line_item':
                ordinal = value.get('value_ordinal', 0) or 0
                if ordinal not in sections_data[section_title]['line_item_rows']:
                    sections_data[section_title]['line_item_rows'][ordinal] = []
                sections_data[section_title]['line_item_rows'][ordinal].append(value)
            else:
                sections_data[section_title]['fields'].append(value)

        # Organize line items
        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                field_order = {}
                for ordinal, values in section_info['line_item_rows'].items():
                    for value in values:
                        field_id = value.get('field_id')
                        field_label = value.get('field_label', '')
                        field_ordinal = value.get('field_ordinal', 0) or 0
                        if field_id and field_id not in field_order:
                            field_order[field_id] = {
                                'label': field_label,
                                'ordinal': field_ordinal
                            }

                sorted_fields = sorted(field_order.items(), key=lambda x: x[1]['ordinal'])
                section_info['line_item_headers'] = [f[1]['label'] for f in sorted_fields]
                field_ids_ordered = [f[0] for f in sorted_fields]

                organized_rows = []
                for ordinal in sorted(section_info['line_item_rows'].keys()):
                    row_values = section_info['line_item_rows'][ordinal]
                    row_dict = {v.get('field_id'): v for v in row_values}
                    organized_row = [row_dict.get(fid) for fid in field_ids_ordered]
                    organized_rows.append(organized_row)

                section_info['line_item_rows'] = organized_rows

        # Calculate fields
        from calculations import calculate_invoice_fields
        calculated_values = calculate_invoice_fields(invoice_values or [], sections_data)

        # Apply calculated values
        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item':
                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value and value.get('calculation_formula'):
                                field_id = value.get('field_id')
                                key = (field_id, row_idx)
                                if key in calculated_values:
                                    value['val_number'] = calculated_values[key]
            else:
                for value in section_info.get('fields', []):
                    if value and value.get('calculation_formula'):
                        field_id = value.get('field_id')
                        key = (field_id, 0)
                        if key in calculated_values:
                            value['val_number'] = calculated_values[key]

        # Get payments
        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,))

        # Generate PDF
        html_content = render_template('invoices/pdf.html',
                                     invoice=invoice_header,
                                     sections_data=sections_data,
                                     payments=payments or [],
                                     current_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        from io import BytesIO
        pdf_buffer = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode('utf-8')), pdf_buffer)

        if pdf.err:
            flash(f'Error generating PDF: {pdf.err}', 'error')
            return redirect(url_for('customer_portal_bp.view_invoice', invoice_id=invoice_id))

        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=invoice_{invoice_id[:8]}.pdf'

        return response

    except DatabaseError as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('customer_portal_bp.view_invoice', invoice_id=invoice_id))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return redirect(url_for('customer_portal_bp.view_invoice', invoice_id=invoice_id))

