"""
Invoices blueprint - CRUD operations for invoices
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, make_response
from db import db, DatabaseError
from auth import require_org
import uuid
from datetime import datetime
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pisa = None

invoices_bp = Blueprint('invoices_bp', __name__)


@invoices_bp.route('/')
@require_org
def list_invoices():
    """List all invoices"""
    org_id = g.current_org_id
    status_filter = request.args.get('status')

    try:
        invoices = db.execute_proc('sp_list_invoices', (org_id, status_filter, 50, 0))

        if invoices is None:
            invoices = []
        elif not isinstance(invoices, list):
            invoices = [invoices] if invoices else []
        return render_template('invoices/list.html', invoices=invoices)
    except DatabaseError as e:
        flash(f'Error loading invoices: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return render_template('invoices/list.html', invoices=[])
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return render_template('invoices/list.html', invoices=[])


@invoices_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_invoice():
    """Create a new invoice"""
    org_id = g.current_org_id

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        template_id = request.form.get('template_id')

        if not customer_id or not template_id:
            flash('Customer and template are required', 'error')
            return redirect(url_for('invoices_bp.create_invoice'))

        try:


            result = db.execute_proc('sp_create_invoice', (org_id, customer_id, template_id, None, None))

            if not result or len(result) == 0:
                flash('Failed to create invoice', 'error')
                return redirect(url_for('invoices_bp.create_invoice'))

            invoice_id = result[0].get('invoice_id')


            fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
            fields = fields_result if fields_result else []


            sections = {}
            for field in fields:
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)


            for section_id, section_data in sections.items():
                section_type = section_data['type']

                if section_type == 'line_item':


                    line_item_keys = [k for k in request.form.keys() if k.startswith(f'line_item_{section_id}_')]


                    rows = {}
                    for key in line_item_keys:


                        prefix = f'line_item_{section_id}_'
                        if key.startswith(prefix):
                            remaining = key[len(prefix):]
                            parts = remaining.split('_field_', 1)
                            if len(parts) == 2:
                                row_num = int(parts[0])
                                field_id = parts[1]

                                if row_num not in rows:
                                    rows[row_num] = {}
                                rows[row_num][field_id] = request.form.get(key)


                    for row_num, row_data in rows.items():
                        for field in section_data['fields']:
                            field_id = field['field_id']
                            data_type = field['data_type']

                            val_string = None
                            val_number = None
                            val_date = None
                            val_boolean = None

                            value = row_data.get(field_id)


                            if value and value.strip():
                                if data_type == 'string':
                                    val_string = value.strip()
                                elif data_type == 'number':
                                    try:
                                        val_number = float(value)
                                    except ValueError:
                                        pass
                                elif data_type == 'date':
                                    val_date = value
                                elif data_type == 'boolean':
                                    val_boolean = 1 if value.lower() in ('true', '1', 'on', 'yes') else 0


                            db.execute_proc('sp_save_invoice_value',
                                           (invoice_id, field_id, val_string, val_number, val_date, val_boolean, row_num),
                                           fetch=False)
                else:

                    for field in section_data['fields']:
                        field_id = field['field_id']
                        data_type = field['data_type']

                        val_string = None
                        val_number = None
                        val_date = None
                        val_boolean = None

                        form_key = f'field_{field_id}'
                        value = request.form.get(form_key)

                        if value:
                            if data_type == 'string':
                                val_string = value
                            elif data_type == 'number':
                                try:
                                    val_number = float(value)
                                except ValueError:
                                    pass
                            elif data_type == 'date':
                                val_date = value
                            elif data_type == 'boolean':
                                val_boolean = 1 if value.lower() in ('true', '1', 'on', 'yes') else 0


                        db.execute_proc('sp_save_invoice_value',
                                       (invoice_id, field_id, val_string, val_number, val_date, val_boolean, None),
                                       fetch=False)


            issue_date = request.form.get('issue_date')
            due_date = request.form.get('due_date')
            if issue_date or due_date:
                db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date or None, due_date or None), fetch=False)


            from calculations import calculate_invoice_fields


            invoice_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
            current_invoice_values = []
            if invoice_values_result and isinstance(invoice_values_result, list):
                if len(invoice_values_result) >= 2:
                    if isinstance(invoice_values_result[1], list):
                        current_invoice_values = invoice_values_result[1]
                    else:
                        current_invoice_values = invoice_values_result[1:]


            sections_for_calc = {}
            for field in fields:
                section_title = field.get('section_title', '')
                section_type = field.get('section_type', 'normal')
                if section_title not in sections_for_calc:
                    sections_for_calc[section_title] = {
                        'type': section_type,
                        'fields': [],
                        'line_item_rows': {} if section_type == 'line_item' else None
                    }
                sections_for_calc[section_title]['fields'].append(field)


            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] == 'line_item':

                    section_info['line_item_rows'] = {}
                    for value in current_invoice_values:
                        if value.get('section_title') == section_title:
                            ordinal = value.get('value_ordinal', 0) or 0
                            if ordinal not in section_info['line_item_rows']:
                                section_info['line_item_rows'][ordinal] = []
                            section_info['line_item_rows'][ordinal].append(value)


            calculated_values = calculate_invoice_fields(current_invoice_values, sections_for_calc)


            for (field_id, ordinal), calc_value in calculated_values.items():
                db.execute_proc('sp_save_invoice_value',
                              (invoice_id, field_id, None, calc_value, None, None, ordinal),
                              fetch=False)


            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)

            flash('Invoice created successfully', 'success')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

        except DatabaseError as e:
            flash(f'Error creating invoice: {str(e)}', 'error')
            return redirect(url_for('invoices_bp.create_invoice'))


    try:

        template_id = request.args.get('template_id') or request.form.get('template_id')


        if not template_id:

            all_templates = db.execute_proc('sp_list_templates', (org_id, False))
            templates = []
            seen_template_ids = set()


            if all_templates:

                sorted_templates = sorted(all_templates,
                                         key=lambda t: (t.get('template_id'), -t.get('version', 0)))

                for template in sorted_templates:
                    tid = template.get('template_id')
                    if tid and tid not in seen_template_ids:

                        if template.get('version') == template.get('latest_version'):
                            templates.append(template)
                            seen_template_ids.add(tid)

            return render_template('invoices/create.html',
                                 customers=[],
                                 templates=templates or [],
                                 fields=[],
                                 sections_data={},
                                 selected_template_id=None,
                                 step='template')



        customers = db.execute_proc('sp_list_customers', (org_id, False))


        all_templates = db.execute_proc('sp_list_templates', (org_id, False))
        templates = []
        seen_template_ids = set()

        if all_templates:
            sorted_templates = sorted(all_templates,
                                     key=lambda t: (t.get('template_id'), -t.get('version', 0)))

            for template in sorted_templates:
                tid = template.get('template_id')
                if tid and tid not in seen_template_ids:
                    if template.get('version') == template.get('latest_version'):
                        templates.append(template)
                        seen_template_ids.add(tid)

        fields = []
        sections_data = {}

        if template_id:
            try:
                fields_result = db.execute_proc('sp_get_template_fields', (template_id,))


                if fields_result:
                    if isinstance(fields_result, list):

                        if len(fields_result) > 0 and isinstance(fields_result[0], list):
                            fields = fields_result[0] if len(fields_result) > 0 else []
                        else:
                            fields = fields_result
                    else:
                        fields = [fields_result]


                    for field in fields:
                        section_id = field.get('section_id')
                        if section_id:
                            if section_id not in sections_data:
                                sections_data[section_id] = {
                                    'title': field.get('section_title', '') or 'Untitled Section',
                                    'type': field.get('section_type', 'normal') or 'normal',
                                    'fields': []
                                }
                            sections_data[section_id]['fields'].append(field)
            except DatabaseError as e:
                flash(f'Error loading template fields: {str(e)}', 'error')
            except Exception as e:
                flash(f'Unexpected error loading fields: {str(e)}', 'error')


        selected_template_info = None
        for t in templates or []:
            if t.get('template_id') == template_id:
                selected_template_info = t
                break

        return render_template('invoices/create.html',
                             customers=customers or [],
                             templates=templates or [],
                             fields=fields,
                             sections_data=sections_data,
                             selected_template_id=template_id,
                             selected_template_info=selected_template_info,
                             step='fields')
    except DatabaseError as e:
        flash('Error loading form data', 'error')
        return render_template('invoices/create.html',
                             customers=[],
                             templates=[],
                             fields=[],
                             sections_data={})


@invoices_bp.route('/<invoice_id>')
@require_org
def view_invoice(invoice_id):
    """View invoice details"""
    try:

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))

        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))




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
            return redirect(url_for('invoices_bp.list_invoices'))


        sections_data = {}


        print(f"\nDEBUG: Invoice values count: {len(invoice_values) if invoice_values else 0}")
        if invoice_values:
            print(f"DEBUG: First value sample: {invoice_values[0] if len(invoice_values) > 0 else 'None'}")

        for value in (invoice_values or []):
            section_title = value.get('section_title', '') or value.get('section_display_name', '') or 'Untitled Section'
            section_type = value.get('section_type', 'normal') or 'normal'
            field_label = value.get('field_label', '') or value.get('field_display_name', '')
            data_type = value.get('data_type', 'string')
            
            value['field_label'] = field_label
            value['section_title'] = section_title
            if 'is_currency' not in value or value.get('is_currency') is None:
                value['is_currency'] = False

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


                if field_label and field_label not in sections_data[section_title]['line_item_headers']:
                    sections_data[section_title]['line_item_headers'].append(field_label)
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

        print(f"DEBUG: Processed sections_data keys: {list(sections_data.keys())}")
        for key, val in sections_data.items():
            print(f"DEBUG: Section '{key}': type={val['type']}, fields_count={len(val.get('fields', []))}, line_item_rows_count={len(val.get('line_item_rows', [])) if val.get('line_item_rows') else 0}")


        template_id = invoice_header.get('template_id')
        sections_for_calc = None
        if template_id:


            import pymysql
            with db.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                    cursor.execute(
                        "SELECT MAX(version) as max_version FROM template WHERE template_id = %s",
                        (template_id,)
                    )
                    version_result = cursor.fetchone()
                    if version_result and version_result.get('max_version'):
                        max_version = version_result['max_version']

                        cursor.execute("""
                            SELECT
                                s.section_id,
                                s.title AS section_title,
                                s.ordinal AS section_ordinal,
                                s.section_type,
                                f.field_id,
                                f.label,
                                f.data_type,
                                f.is_required,
                                f.ordinal AS field_ordinal,
                                f.calculation_formula
                            FROM section s
                            JOIN field f ON s.section_id = f.section_id
                            WHERE s.template_id = %s
                              AND s.template_version = %s
                            ORDER BY s.ordinal, f.ordinal
                        """, (template_id, max_version))
                        fields = cursor.fetchall()
                    else:
                        fields = []

            if not fields:
                fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                fields = fields_result if fields_result else []



            field_map = {}
            for field in fields:
                field_id = field.get('field_id')
                if field_id:
                    field_map[field_id] = field

            print(f"DEBUG: Created field_map with {len(field_map)} fields")
            for field_id, field in field_map.items():
                formula_val = field.get('calculation_formula')

                if formula_val is None or formula_val == '' or str(formula_val).lower() == 'none':
                    formula_str = 'None'
                else:
                    formula_str = formula_val
                print(f"DEBUG: Field {field_id}: label='{field.get('label')}', formula='{formula_str}' (type: {type(formula_val).__name__})")

            sections_for_calc = {}
            for field in fields:
                section_title = field.get('section_title', '')
                section_type = field.get('section_type', 'normal')
                if section_title not in sections_for_calc:
                    sections_for_calc[section_title] = {
                        'type': section_type,
                        'fields': [],
                        'line_item_rows': {} if section_type == 'line_item' else None
                    }
                sections_for_calc[section_title]['fields'].append(field)


            for value in invoice_values or []:
                section_title = value.get('section_title', '')
                if section_title in sections_for_calc:
                    section_info = sections_for_calc[section_title]
                    field_id = value.get('field_id')


                    if field_id in field_map:
                        field = field_map[field_id]
                        value['calculation_formula'] = field.get('calculation_formula')
                        value['field_label'] = field.get('label', value.get('field_label', ''))
                        value['data_type'] = field.get('data_type', value.get('data_type', 'string'))
                        print(f"DEBUG: Merged formula for field_id {field_id}: '{value.get('calculation_formula')}'")
                    else:
                        print(f"DEBUG: WARNING: field_id {field_id} not found in field_map!")

                    if section_info['type'] == 'line_item':
                        ordinal = value.get('value_ordinal', 0) or 0
                        if section_info['line_item_rows'] is None:
                            section_info['line_item_rows'] = {}
                        if ordinal not in section_info['line_item_rows']:
                            section_info['line_item_rows'][ordinal] = []
                        section_info['line_item_rows'][ordinal].append(value)
                    else:
                        section_info['fields'].append(value)


            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                    rows_list = []
                    for ordinal in sorted(section_info['line_item_rows'].keys()):
                        row = section_info['line_item_rows'][ordinal]

                        for val in row:
                            if val:
                                print(f"DEBUG: Row {ordinal}, field '{val.get('field_label')}': formula={val.get('calculation_formula')}")
                        rows_list.append(row)
                    section_info['line_item_rows'] = rows_list
                    print(f"DEBUG: Converted {section_title} line_item_rows to list with {len(rows_list)} rows")
                elif section_info['type'] == 'normal':

                    for val in section_info.get('fields', []):
                        if val:
                            print(f"DEBUG: Normal section '{section_title}', field '{val.get('field_label')}': formula={val.get('calculation_formula')}")


        from calculations import calculate_invoice_fields
        calc_sections = sections_for_calc if sections_for_calc else sections_data
        print(f"DEBUG: Calling calculate_invoice_fields with {len(invoice_values or [])} values and {len(calc_sections)} sections")
        print(f"DEBUG: Sections in calc_sections: {list(calc_sections.keys())}")
        for sec_name, sec_info in calc_sections.items():
            if sec_info.get('type') == 'line_item':
                rows = sec_info.get('line_item_rows', [])
                print(f"DEBUG: Section '{sec_name}' has {len(rows)} rows")
                for i, row in enumerate(rows):
                    print(f"DEBUG:   Row {i} has {len(row)} values")
                    for val in row:
                        if val:
                            print(f"DEBUG:     Value: field_id={val.get('field_id')}, label={val.get('field_label')}, formula={val.get('calculation_formula')}")
        calculated_values = calculate_invoice_fields(invoice_values or [], calc_sections)
        print(f"DEBUG: Calculated {len(calculated_values)} values: {calculated_values}")


        for (field_id, ordinal), calc_value in calculated_values.items():
            if calc_value is not None:
                try:
                    db.execute_proc('sp_save_invoice_value',
                                  (invoice_id, field_id, None, calc_value, None, None, ordinal),
                                  fetch=False)
                except Exception as e:
                    print(f"Warning: Failed to save calculated value for field {field_id}, ordinal {ordinal}: {str(e)}")


        try:
            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)
        except Exception as e:
            print(f"Warning: Failed to update invoice total: {str(e)}")


        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if result and isinstance(result, list):
            if len(result) >= 2:
                if isinstance(result[1], list):
                    invoice_values = result[1]
                else:
                    invoice_values = result[1:]


        sections_data = {}
        for value in invoice_values or []:
            section_title = value.get('section_title', '')
            section_type = value.get('section_type', 'normal') or 'normal'

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
                ordinal = value.get('value_ordinal', 0) or 0
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


        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item':
                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value and value.get('calculation_formula'):
                                field_id = value.get('field_id')
                                ordinal = value.get('value_ordinal', 0) or 0
                                key = (field_id, ordinal)
                                if key in calculated_values:
                                    value['val_number'] = calculated_values[key]
                                    value['calculated'] = True
                                elif (field_id, row_idx) in calculated_values:
                                    value['val_number'] = calculated_values[(field_id, row_idx)]
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

        return render_template('invoices/view.html',
                             invoice=invoice_header,
                             values=invoice_values or [],
                             sections_data=sections_data,
                             payments=payments or [])
    except DatabaseError as e:
        import traceback
        print(f"ERROR loading invoice {invoice_id}: {str(e)}")
        traceback.print_exc()
        flash(f'Error loading invoice: {str(e)}', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))
    except Exception as e:
        import traceback
        print(f"UNEXPECTED ERROR loading invoice {invoice_id}: {str(e)}")
        traceback.print_exc()
        flash(f'Error loading invoice: {str(e)}', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))


@invoices_bp.route('/<invoice_id>/pdf')
@require_org
def export_pdf(invoice_id):
    """Export invoice as PDF"""
    if not PDF_AVAILABLE:
        flash('PDF export is not available. Please install xhtml2pdf: pip install xhtml2pdf', 'error')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

    try:

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))

        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


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
            return redirect(url_for('invoices_bp.list_invoices'))


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


        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,))


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
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=invoice_{invoice_id[:8]}.pdf'

        return response

    except DatabaseError as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<invoice_id>/finalize', methods=['POST'])
@require_org
def finalize_invoice(invoice_id):
    """Finalize an invoice (change status from draft to pending)"""
    try:

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        invoice_header = None
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result[0]) > 0:
                        invoice_header = result[0][0]
                elif isinstance(result[0], dict):
                    invoice_header = result[0]

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))

        current_status = invoice_header.get('status', 'draft')


        if current_status != 'draft':
            flash(f'Invoice is already {current_status}. Only draft invoices can be finalized.', 'error')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


        db.execute_proc('sp_update_invoice_status', (invoice_id, 'pending'), fetch=False)

        flash('Invoice finalized successfully. Customer can now view it in the portal.', 'success')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

    except DatabaseError as e:
        flash(f'Error finalizing invoice: {str(e)}', 'error')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<invoice_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_invoice(invoice_id):
    """Edit invoice"""
    org_id = g.current_org_id


    try:
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        invoice_header = None
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result[0]) > 0:
                        invoice_header = result[0][0]
                elif isinstance(result[0], dict):
                    invoice_header = result[0]

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        if invoice_header.get('org_id') != org_id:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        current_status = invoice_header.get('status', 'draft')
        if current_status != 'draft':
            flash('Only draft invoices can be edited', 'error')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
    except DatabaseError as e:
        flash('Error loading invoice', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    if request.method == 'POST':
        try:
            print(f"DEBUG EDIT -- POST request: Saving invoice {invoice_id}")
            print(f"DEBUG EDIT -- Total form keys received: {len(request.form.keys())}")
            print(f"DEBUG EDIT -- All form keys: {list(request.form.keys())}")


            issue_date = request.form.get('issue_date')
            due_date = request.form.get('due_date')
            if issue_date or due_date:
                db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date or None, due_date or None), fetch=False)


            template_id = invoice_header.get('template_id')
            fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
            fields = fields_result if fields_result else []
            print(f"DEBUG EDIT -- Loaded {len(fields)} template fields")


            sections = {}
            for field in fields:
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)


            for section_id, section_data in sections.items():
                section_type = section_data['type']

                if section_type == 'line_item':

                    line_item_keys = [k for k in request.form.keys() if k.startswith(f'line_item_{section_id}_')]
                    print(f"DEBUG EDIT -- Section {section_id}: Found {len(line_item_keys)} line item form keys")


                    rows = {}
                    for key in line_item_keys:
                        prefix = f'line_item_{section_id}_'
                        if key.startswith(prefix):
                            remaining = key[len(prefix):]
                            parts = remaining.split('_field_', 1)
                            if len(parts) == 2:
                                try:
                                    row_num = int(parts[0])
                                    field_id = parts[1]

                                    if row_num not in rows:
                                        rows[row_num] = {}
                                    rows[row_num][field_id] = request.form.get(key)
                                    print(f"DEBUG EDIT -- Section {section_id}: Row {row_num}, field {field_id} = '{request.form.get(key)}'")
                                except ValueError:
                                    print(f"DEBUG EDIT -- ERROR: Could not parse row number from key: {key}")

                    print(f"DEBUG EDIT -- Section {section_id}: Found {len(rows)} unique rows: {sorted(rows.keys())}")


                    for row_num, row_data in rows.items():
                        print(f"DEBUG EDIT -- Saving row {row_num} for section {section_id} with {len(row_data)} fields")
                        for field in section_data['fields']:
                            field_id = field['field_id']
                            data_type = field['data_type']

                    val_string = None
                    val_number = None
                    val_date = None
                    val_boolean = None


                    value = row_data.get(field_id)


                    if value is not None and str(value).strip():
                        value_str = str(value).strip()
                        if data_type == 'string':
                            val_string = value_str
                        elif data_type == 'number':
                            try:
                                val_number = float(value_str)
                            except ValueError:
                                pass
                        elif data_type == 'date':
                            val_date = value_str
                        elif data_type == 'boolean':
                            val_boolean = 1 if value_str.lower() in ('true', '1', 'on', 'yes') else 0
                        print(f"DEBUG EDIT -- Saving field {field_id} (row {row_num}): string={val_string}, number={val_number}, date={val_date}, boolean={val_boolean}")
                        db.execute_proc('sp_save_invoice_value',
                                        (invoice_id, field_id, val_string, val_number, val_date, val_boolean, row_num),
                                        fetch=False)
                        print(f"DEBUG EDIT -- Saved field {field_id} for row {row_num}")
                else:

                    for field in section_data['fields']:
                        field_id = field['field_id']
                        data_type = field['data_type']

                        val_string = None
                        val_number = None
                        val_date = None
                        val_boolean = None

                        form_key = f'field_{field_id}'
                        value = request.form.get(form_key)

                        if value:
                            if data_type == 'string':
                                val_string = value
                            elif data_type == 'number':
                                try:
                                    val_number = float(value)
                                except ValueError:
                                    pass
                            elif data_type == 'date':
                                val_date = value
                            elif data_type == 'boolean':
                                val_boolean = 1 if value.lower() in ('true', '1', 'on', 'yes') else 0

                    db.execute_proc('sp_save_invoice_value',
                                   (invoice_id, field_id, val_string, val_number, val_date, val_boolean, None),
                                   fetch=False)


            from calculations import calculate_invoice_fields

            invoice_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
            current_invoice_values = []
            if invoice_values_result and isinstance(invoice_values_result, list):
                if len(invoice_values_result) >= 2:
                    if isinstance(invoice_values_result[1], list):
                        current_invoice_values = invoice_values_result[1]
                    else:
                        current_invoice_values = invoice_values_result[1:]


            field_map = {}
            for field in fields:
                field_id = field.get('field_id')
                if field_id:
                    field_map[field_id] = field


            sections_for_calc = {}
            for field in fields:
                section_title = field.get('section_title', '')
                section_type = field.get('section_type', 'normal')
                if section_title not in sections_for_calc:
                    sections_for_calc[section_title] = {
                        'type': section_type,
                        'fields': [],
                        'line_item_rows': {} if section_type == 'line_item' else None
                    }
                sections_for_calc[section_title]['fields'].append(field)


            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] != 'line_item':
                    section_info['fields'] = []


            for value in current_invoice_values:
                section_title = value.get('section_title', '')
                if section_title in sections_for_calc:
                    section_info = sections_for_calc[section_title]
                    field_id = value.get('field_id')


                    if field_id and field_id in field_map:
                        field_meta = field_map[field_id]
                        value['calculation_formula'] = field_meta.get('calculation_formula')
                        value['field_label'] = field_meta.get('label', value.get('field_label', ''))
                        value['data_type'] = field_meta.get('data_type', value.get('data_type', 'string'))

                    if section_info['type'] == 'line_item':
                        ordinal = value.get('value_ordinal', 0) or 0
                        if section_info['line_item_rows'] is None:
                            section_info['line_item_rows'] = {}
                        if ordinal not in section_info['line_item_rows']:
                            section_info['line_item_rows'][ordinal] = []
                        section_info['line_item_rows'][ordinal].append(value)
                    else:

                        section_info['fields'].append(value)


            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                    rows_list = []
                    for ordinal in sorted(section_info['line_item_rows'].keys()):
                        row = section_info['line_item_rows'][ordinal]
                        rows_list.append(row)
                    section_info['line_item_rows'] = rows_list

            calculated_values = calculate_invoice_fields(current_invoice_values, sections_for_calc)

            for (field_id, ordinal), calc_value in calculated_values.items():
                db.execute_proc('sp_save_invoice_value',
                              (invoice_id, field_id, None, calc_value, None, None, ordinal),
                              fetch=False)

            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)

            flash('Invoice updated successfully', 'success')

            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

        except DatabaseError as e:
            flash(f'Error updating invoice: {str(e)}', 'error')
            return redirect(url_for('invoices_bp.edit_invoice', invoice_id=invoice_id))


    try:
        print(f"DEBUG EDIT -- GET request: Loading edit form for invoice {invoice_id}")

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        invoice_values = []
        if result and isinstance(result, list):
            if len(result) >= 2:
                if isinstance(result[1], list):
                    invoice_values = result[1]
                else:
                    invoice_values = result[1:]

        print(f"DEBUG EDIT -- GET: Loaded {len(invoice_values)} invoice values from database")

        ordinals_found = {}
        for value in invoice_values:
            section_title = value.get('section_title', '')
            ordinal = value.get('value_ordinal', 0) or 0
            if section_title not in ordinals_found:
                ordinals_found[section_title] = set()
            ordinals_found[section_title].add(ordinal)
        for section_title, ords in ordinals_found.items():
            print(f"DEBUG EDIT -- GET: Section '{section_title}' has ordinals: {sorted(ords)}")


        template_id = invoice_header.get('template_id')
        fields = []
        sections_data = {}

        if template_id:
            fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
            if fields_result:
                if isinstance(fields_result, list):
                    if len(fields_result) > 0 and isinstance(fields_result[0], list):
                        fields = fields_result[0] if len(fields_result) > 0 else []
                    else:
                        fields = fields_result
                else:
                    fields = [fields_result]


                for field in fields:
                    section_id = field.get('section_id')
                    if section_id:
                        if section_id not in sections_data:
                            sections_data[section_id] = {
                                'title': field.get('section_title', '') or 'Untitled Section',
                                'type': field.get('section_type', 'normal') or 'normal',
                                'fields': []
                            }
                        sections_data[section_id]['fields'].append(field)


                value_map = {}
                print(f"DEBUG EDIT -- Total invoice_values received: {len(invoice_values)}")
                for value in invoice_values:
                    field_id = value.get('field_id')
                    ordinal = value.get('value_ordinal', 0) or 0
                    key = (field_id, ordinal)
                    value_map[key] = value
                    print(f"DEBUG EDIT -- Mapped value: field_id={field_id}, ordinal={ordinal}, section_title={value.get('section_title')}")

                print(f"DEBUG EDIT -- Total values in value_map: {len(value_map)}")


                for section_id, section_info in sections_data.items():
                    print(f"DEBUG EDIT -- Processing section: {section_id}, type={section_info.get('type')}, title={section_info.get('title')}")
                    if section_info['type'] == 'line_item':


                        section_ordinals = set()
                        section_title = section_info.get('title', '')


                        section_field_ids = {field['field_id'] for field in section_info['fields']}
                        print(f"DEBUG EDIT -- Section {section_id} has {len(section_field_ids)} fields: {list(section_field_ids)}")


                        for value in invoice_values:
                            value_field_id = value.get('field_id')
                            value_section_title = value.get('section_title', '')

                            if value_field_id in section_field_ids:
                                ordinal = value.get('value_ordinal', 0) or 0
                                section_ordinals.add(ordinal)
                                print(f"DEBUG EDIT -- Found value for section {section_id}: field_id={value_field_id}, ordinal={ordinal}, section_title={value_section_title}")


                        for field_id in section_field_ids:
                            for key, value in value_map.items():
                                if key[0] == field_id:
                                    section_ordinals.add(key[1])

                        print(f"DEBUG EDIT -- Section {section_id} collected ordinals: {sorted(section_ordinals)}")


                        for field in section_info['fields']:
                            field_id = field['field_id']
                            field['values'] = {}

                            for ordinal in sorted(section_ordinals):
                                key = (field_id, ordinal)
                                if key in value_map:
                                    field['values'][ordinal] = value_map[key]
                                    print(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) has value for ordinal {ordinal}")
                                else:


                                    field['values'][ordinal] = {
                                        'field_id': field_id,
                                        'val_string': None,
                                        'val_number': None,
                                        'val_date': None,
                                        'val_boolean': None,
                                        'value_ordinal': ordinal,
                                        'field_label': field.get('label', ''),
                                        'data_type': field.get('data_type', 'string')
                                    }
                                    print(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) created empty value for ordinal {ordinal}")

                            print(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) now has {len(field.get('values', {}))} value entries")
                    else:

                        for field in section_info['fields']:
                            field_id = field['field_id']
                            key = (field_id, 0)
                            if key in value_map:
                                field['value'] = value_map[key]

        return render_template('invoices/edit.html',
                             invoice=invoice_header,
                             fields=fields,
                             sections_data=sections_data)
    except DatabaseError as e:
        flash('Error loading form data', 'error')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<invoice_id>/delete', methods=['POST'])
@require_org
def delete_invoice(invoice_id):
    """Delete an invoice"""
    org_id = g.current_org_id

    try:

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))

        invoice_header = None
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], list):
                    if len(result[0]) > 0:
                        invoice_header = result[0][0]
                elif isinstance(result[0], dict):
                    invoice_header = result[0]

        if not invoice_header or invoice_header.get('org_id') != org_id:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        db.execute_proc('sp_delete_invoice', (invoice_id,), fetch=False)
        flash('Invoice deleted successfully', 'success')
    except DatabaseError as e:
        flash(f'Error deleting invoice: {str(e)}', 'error')

    return redirect(url_for('invoices_bp.list_invoices'))


@invoices_bp.route('/<invoice_id>/payment', methods=['POST'])
@require_org
def add_payment(invoice_id):
    """Add payment to invoice"""
    amount = request.form.get('amount')
    method = request.form.get('method')
    reference_number = request.form.get('reference_number')

    if not amount:
        flash('Amount is required', 'error')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

    try:

        db.execute_proc('sp_record_payment', (invoice_id, float(amount), method, reference_number, None), fetch=False)
        flash('Payment recorded successfully', 'success')
    except DatabaseError as e:
        flash(f'Error recording payment: {str(e)}', 'error')

    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

