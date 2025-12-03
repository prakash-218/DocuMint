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
        # Ensure invoices is a list
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
            # Create invoice - procedure returns invoice_id and template_version
            # Procedure has 3 IN params + 2 OUT params = 5 total, need placeholders for OUT
            result = db.execute_proc('sp_create_invoice', (org_id, customer_id, template_id, None, None))
            
            if not result or len(result) == 0:
                flash('Failed to create invoice', 'error')
                return redirect(url_for('invoices_bp.create_invoice'))
            
            invoice_id = result[0].get('invoice_id')
            
            # Get template fields to save values
            fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
            fields = fields_result if fields_result else []
            
            # Group fields by section to handle line items
            sections = {}
            for field in fields:
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)
            
            # Save invoice values from form
            for section_id, section_data in sections.items():
                section_type = section_data['type']
                
                if section_type == 'line_item':
                    # Handle line items - multiple rows
                    # Find all line item rows for this section
                    line_item_keys = [k for k in request.form.keys() if k.startswith(f'line_item_{section_id}_')]
                    
                    # Group by row number
                    rows = {}
                    for key in line_item_keys:
                        # Format: line_item_{section_id}_{row}_field_{field_id}
                        # Example: line_item_abc123_0_field_def456
                        prefix = f'line_item_{section_id}_'
                        if key.startswith(prefix):
                            remaining = key[len(prefix):]  # e.g., "0_field_def456"
                            parts = remaining.split('_field_', 1)
                            if len(parts) == 2:
                                row_num = int(parts[0])
                                field_id = parts[1]
                                
                                if row_num not in rows:
                                    rows[row_num] = {}
                                rows[row_num][field_id] = request.form.get(key)
                    
                    # Save each row
                    for row_num, row_data in rows.items():
                        for field in section_data['fields']:
                            field_id = field['field_id']
                            data_type = field['data_type']
                            
                            val_string = None
                            val_number = None
                            val_date = None
                            val_boolean = None
                            
                            value = row_data.get(field_id)
                            
                            # Always save the field, even if empty (for line items)
                            if value and value.strip():  # Only process non-empty values
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
                            
                            # Save with ordinal for line items (always save, even if empty)
                            db.execute_proc('sp_save_invoice_value', 
                                           (invoice_id, field_id, val_string, val_number, val_date, val_boolean, row_num),
                                           fetch=False)
                else:
                    # Handle normal sections - single values
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
                        
                        # Save the value (ordinal is None for normal fields)
                        db.execute_proc('sp_save_invoice_value', 
                                       (invoice_id, field_id, val_string, val_number, val_date, val_boolean, None),
                                       fetch=False)
            
            # Update invoice dates if provided
            issue_date = request.form.get('issue_date')
            due_date = request.form.get('due_date')
            if issue_date or due_date:
                db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date or None, due_date or None), fetch=False)
            
            # Calculate and save calculated field values
            from calculations import calculate_invoice_fields
            
            # Get all invoice values to compute calculations
            invoice_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
            current_invoice_values = []
            if invoice_values_result and isinstance(invoice_values_result, list):
                if len(invoice_values_result) >= 2:
                    if isinstance(invoice_values_result[1], list):
                        current_invoice_values = invoice_values_result[1]
                    else:
                        current_invoice_values = invoice_values_result[1:]
            
            # Rebuild sections_data for calculation
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
            
            # Organize line items if needed
            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] == 'line_item':
                    # Group values by ordinal
                    section_info['line_item_rows'] = {}
                    for value in current_invoice_values:
                        if value.get('section_title') == section_title:
                            ordinal = value.get('value_ordinal', 0) or 0
                            if ordinal not in section_info['line_item_rows']:
                                section_info['line_item_rows'][ordinal] = []
                            section_info['line_item_rows'][ordinal].append(value)
            
            # Calculate values
            calculated_values = calculate_invoice_fields(current_invoice_values, sections_for_calc)
            
            # Save calculated values
            for (field_id, ordinal), calc_value in calculated_values.items():
                db.execute_proc('sp_save_invoice_value',
                              (invoice_id, field_id, None, calc_value, None, None, ordinal),
                              fetch=False)
            
            # Final update of invoice total (sp_save_invoice_value already calls it, but ensure it's up to date)
            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)
            
            flash('Invoice created successfully', 'success')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
            
        except DatabaseError as e:
            flash(f'Error creating invoice: {str(e)}', 'error')
            return redirect(url_for('invoices_bp.create_invoice'))
    
    # GET request - show form
    try:
        # Get customers and templates for dropdowns
        customers = db.execute_proc('sp_list_customers', (org_id,))
        templates = db.execute_proc('sp_list_templates', (org_id,))
        
        # Get template fields if template_id is provided
        template_id = request.args.get('template_id') or request.form.get('template_id')
        fields = []
        sections_data = {}
        
        if template_id:
            try:
                fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                
                # Ensure fields is a list
                if fields_result:
                    if isinstance(fields_result, list):
                        # Check if it's a list of lists (multiple result sets)
                        if len(fields_result) > 0 and isinstance(fields_result[0], list):
                            fields = fields_result[0] if len(fields_result) > 0 else []
                        else:
                            fields = fields_result
                    else:
                        fields = [fields_result]
                    
                    # Group fields by section for easier template rendering
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
        
        return render_template('invoices/create.html',
                             customers=customers or [],
                             templates=templates or [],
                             fields=fields,
                             sections_data=sections_data,
                             selected_template_id=template_id)
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
        # Get invoice details (returns multiple result sets)
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))
        
        # Handle multiple result sets
        # When multiple result sets: result is a list of result sets (each is a list of dicts)
        # When single result set: result is a list of dicts
        invoice_header = None
        invoice_values = []
        
        if isinstance(result, list):
            # Check if first element is a list (multiple result sets) or dict (single result set)
            if len(result) > 0:
                if isinstance(result[0], list):
                    # Multiple result sets: result[0] is first result set, result[1] is second
                    if len(result) >= 1 and len(result[0]) > 0:
                        invoice_header = result[0][0]
                    if len(result) >= 2:
                        invoice_values = result[1]
                elif isinstance(result[0], dict):
                    # Single result set: result is list of dicts, first dict is header
                    invoice_header = result[0]
                    # If there are more rows, they might be values
                    if len(result) > 1:
                        invoice_values = result[1:]
        elif isinstance(result, dict):
            # Single row returned as dict
            invoice_header = result
        
        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))
        
        # Process values to group by section and handle line items
        sections_data = {}
        
        # Debug: Print what we got
        print(f"\nDEBUG: Invoice values count: {len(invoice_values) if invoice_values else 0}")
        if invoice_values:
            print(f"DEBUG: First value sample: {invoice_values[0] if len(invoice_values) > 0 else 'None'}")
        
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
                # Group by ordinal for line items
                ordinal = value.get('value_ordinal', 0)
                if ordinal is None:
                    ordinal = 0
                
                if ordinal not in sections_data[section_title]['line_item_rows']:
                    sections_data[section_title]['line_item_rows'][ordinal] = []
                
                sections_data[section_title]['line_item_rows'][ordinal].append(value)
                
                # Collect unique field labels in order for headers
                if field_label and field_label not in sections_data[section_title]['line_item_headers']:
                    sections_data[section_title]['line_item_headers'].append(field_label)
            else:
                sections_data[section_title]['fields'].append(value)
        
        # For line items, reorganize into rows and headers
        for section_title, section_info in sections_data.items():
            if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                # Get all unique field IDs and their labels in order
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
                
                # Sort fields by ordinal
                sorted_fields = sorted(field_order.items(), key=lambda x: x[1]['ordinal'])
                section_info['line_item_headers'] = [f[1]['label'] for f in sorted_fields]
                field_ids_ordered = [f[0] for f in sorted_fields]
                
                # Reorganize rows: each row should have values in field order
                organized_rows = []
                for ordinal in sorted(section_info['line_item_rows'].keys()):
                    row_values = section_info['line_item_rows'][ordinal]
                    # Create a dict by field_id for quick lookup
                    row_dict = {v.get('field_id'): v for v in row_values}
                    # Build row in field order
                    organized_row = [row_dict.get(fid) for fid in field_ids_ordered]
                    organized_rows.append(organized_row)
                
                section_info['line_item_rows'] = organized_rows
        
        print(f"DEBUG: Processed sections_data keys: {list(sections_data.keys())}")
        for key, val in sections_data.items():
            print(f"DEBUG: Section '{key}': type={val['type']}, fields_count={len(val.get('fields', []))}, line_item_rows_count={len(val.get('line_item_rows', [])) if val.get('line_item_rows') else 0}")
        
        # Get template fields to build proper sections_data with calculation_formula
        template_id = invoice_header.get('template_id')
        sections_for_calc = None
        if template_id:
            # Query template fields directly to ensure calculation_formula is included
            # The stored procedure seems to have issues returning calculation_formula
            import pymysql
            with db.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Get latest version
                    cursor.execute(
                        "SELECT MAX(version) as max_version FROM template WHERE template_id = %s",
                        (template_id,)
                    )
                    version_result = cursor.fetchone()
                    if version_result and version_result.get('max_version'):
                        max_version = version_result['max_version']
                        # Get fields with calculation_formula
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
            # Fallback to stored procedure if direct query fails
            if not fields:
                fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                fields = fields_result if fields_result else []
            
            # Build sections_for_calc from template fields (includes calculation_formula)
            # First, create a map of field_id -> field for quick lookup
            field_map = {}
            for field in fields:
                field_id = field.get('field_id')
                if field_id:
                    field_map[field_id] = field
            
            print(f"DEBUG: Created field_map with {len(field_map)} fields")
            for field_id, field in field_map.items():
                formula_val = field.get('calculation_formula')
                # Check if it's None, empty string, or the string 'None'
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
            
            # Organize invoice values into sections_for_calc structure
            for value in invoice_values or []:
                section_title = value.get('section_title', '')
                if section_title in sections_for_calc:
                    section_info = sections_for_calc[section_title]
                    field_id = value.get('field_id')
                    
                    # Merge field metadata with value using field_map
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
            
            # Convert line_item_rows from dict to list for calculation (calculation engine expects list)
            for section_title, section_info in sections_for_calc.items():
                if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                    rows_list = []
                    for ordinal in sorted(section_info['line_item_rows'].keys()):
                        row = section_info['line_item_rows'][ordinal]
                        # Debug: Check if formulas are in the row
                        for val in row:
                            if val:
                                print(f"DEBUG: Row {ordinal}, field '{val.get('field_label')}': formula={val.get('calculation_formula')}")
                        rows_list.append(row)
                    section_info['line_item_rows'] = rows_list
                    print(f"DEBUG: Converted {section_title} line_item_rows to list with {len(rows_list)} rows")
                elif section_info['type'] == 'normal':
                    # Debug: Check formulas in normal section fields
                    for val in section_info.get('fields', []):
                        if val:
                            print(f"DEBUG: Normal section '{section_title}', field '{val.get('field_label')}': formula={val.get('calculation_formula')}")
        
        # Evaluate calculated fields
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
        
        # Save calculated values to database (they might be missing or outdated)
        for (field_id, ordinal), calc_value in calculated_values.items():
            if calc_value is not None:
                try:
                    db.execute_proc('sp_save_invoice_value',
                                  (invoice_id, field_id, None, calc_value, None, None, ordinal),
                                  fetch=False)
                except Exception as e:
                    print(f"Warning: Failed to save calculated value for field {field_id}, ordinal {ordinal}: {str(e)}")
        
        # Update invoice total
        try:
            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)
        except Exception as e:
            print(f"Warning: Failed to update invoice total: {str(e)}")
        
        # Reload invoice values after saving calculated values
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if result and isinstance(result, list):
            if len(result) >= 2:
                if isinstance(result[1], list):
                    invoice_values = result[1]
                else:
                    invoice_values = result[1:]
        
        # Rebuild sections_data with updated values
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
        
        # Reorganize line items again
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
        
        # Apply calculated values to sections_data for display
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
        
        # Get payments
        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,))
        
        return render_template('invoices/view.html',
                             invoice=invoice_header,
                             values=invoice_values or [],
                             sections_data=sections_data,
                             payments=payments or [])
    except DatabaseError as e:
        flash('Error loading invoice', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))


@invoices_bp.route('/<invoice_id>/pdf')
@require_org
def export_pdf(invoice_id):
    """Export invoice as PDF"""
    if not PDF_AVAILABLE:
        flash('PDF export is not available. Please install xhtml2pdf: pip install xhtml2pdf', 'error')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
    
    try:
        # Get invoice details (same logic as view_invoice)
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))
        
        # Handle multiple result sets
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
        
        # Process values to group by section (simplified version of view_invoice logic)
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
        
        # Reorganize line items
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
        
        # Get payments
        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,))
        
        # Render PDF template
        html_content = render_template('invoices/pdf.html',
                                     invoice=invoice_header,
                                     sections_data=sections_data,
                                     payments=payments or [],
                                     current_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Convert HTML to PDF using xhtml2pdf
        from io import BytesIO
        pdf_buffer = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode('utf-8')), pdf_buffer)
        
        if pdf.err:
            flash(f'Error generating PDF: {pdf.err}', 'error')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
        
        # Create response
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
        # Get current invoice status
        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        if not result:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))
        
        # Extract invoice header
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
        
        # Only allow finalizing draft invoices
        if current_status != 'draft':
            flash(f'Invoice is already {current_status}. Only draft invoices can be finalized.', 'error')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
        
        # Update status to 'pending' (finalized)
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
    if request.method == 'POST':
        try:
            # Update status if provided
            status = request.form.get('status')
            if status:
                db.execute_proc('sp_update_invoice_status', (invoice_id, status), fetch=False)
            
            # Update dates
            issue_date = request.form.get('issue_date')
            due_date = request.form.get('due_date')
            if issue_date or due_date:
                db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date or None, due_date or None), fetch=False)
            
            # Update values
            fields_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
            invoice_values = []
            if fields_result:
                # Handle multiple result sets
                if isinstance(fields_result, list):
                    if len(fields_result) > 0:
                        if isinstance(fields_result[0], list):
                            # Multiple result sets
                            if len(fields_result) >= 2:
                                invoice_values = fields_result[1]
                        elif isinstance(fields_result[0], dict):
                            # Single result set, skip first (header)
                            if len(fields_result) > 1:
                                invoice_values = fields_result[1:]
                
                for value_row in invoice_values:
                    field_id = value_row.get('field_id')
                    if not field_id:
                        continue
                    
                    data_type = value_row.get('data_type')
                    form_key = f'field_{field_id}'
                    form_value = request.form.get(form_key)
                    
                    val_string = None
                    val_number = None
                    val_date = None
                    val_boolean = None
                    
                    if form_value:
                        if data_type == 'string':
                            val_string = form_value
                        elif data_type == 'number':
                            try:
                                val_number = float(form_value)
                            except ValueError:
                                pass
                        elif data_type == 'date':
                            val_date = form_value
                        elif data_type == 'boolean':
                            val_boolean = 1 if form_value.lower() in ('true', '1', 'on', 'yes') else 0
                    
                    db.execute_proc('sp_save_invoice_value',
                                   (invoice_id, field_id, val_string, val_number, val_date, val_boolean, None),
                                   fetch=False)
            
            # Recalculate calculated fields and update totals
            from calculations import calculate_invoice_fields
            
            # Get updated invoice values
            updated_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
            updated_invoice_values = []
            if updated_values_result and isinstance(updated_values_result, list):
                if len(updated_values_result) >= 2:
                    if isinstance(updated_values_result[1], list):
                        updated_invoice_values = updated_values_result[1]
                    else:
                        updated_invoice_values = updated_values_result[1:]
            
            # Get template fields for calculation context
            invoice_header = None
            if updated_values_result and isinstance(updated_values_result, list):
                if len(updated_values_result) > 0:
                    if isinstance(updated_values_result[0], list):
                        if len(updated_values_result[0]) > 0:
                            invoice_header = updated_values_result[0][0]
                    elif isinstance(updated_values_result[0], dict):
                        invoice_header = updated_values_result[0]
            
            if invoice_header:
                template_id = invoice_header.get('template_id')
                if template_id:
                    fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                    fields = fields_result if fields_result else []
                    
                    # Rebuild sections_data for calculation
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
                    
                    # Organize line items if needed
                    for section_title, section_info in sections_for_calc.items():
                        if section_info['type'] == 'line_item':
                            section_info['line_item_rows'] = {}
                            for value in updated_invoice_values:
                                if value.get('section_title') == section_title:
                                    ordinal = value.get('value_ordinal', 0) or 0
                                    if ordinal not in section_info['line_item_rows']:
                                        section_info['line_item_rows'][ordinal] = []
                                    section_info['line_item_rows'][ordinal].append(value)
                    
                    # Calculate values
                    calculated_values = calculate_invoice_fields(updated_invoice_values, sections_for_calc)
                    
                    # Save calculated values
                    for (field_id, ordinal), calc_value in calculated_values.items():
                        db.execute_proc('sp_save_invoice_value',
                                      (invoice_id, field_id, None, calc_value, None, None, ordinal),
                                      fetch=False)
            
            # Final update of invoice total (sp_save_invoice_value already calls it, but ensure it's up to date)
            db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)
            
            flash('Invoice updated successfully', 'success')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
            
        except DatabaseError as e:
            flash(f'Error updating invoice: {str(e)}', 'error')
            return redirect(url_for('invoices_bp.edit_invoice', invoice_id=invoice_id))
    
    # GET request - show edit form
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


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
        # Procedure has 4 IN params + 1 OUT param = 5 total, need placeholder for OUT
        db.execute_proc('sp_record_payment', (invoice_id, float(amount), method, reference_number, None), fetch=False)
        flash('Payment recorded successfully', 'success')
    except DatabaseError as e:
        flash(f'Error recording payment: {str(e)}', 'error')
    
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))

