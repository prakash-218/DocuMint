"""
Templates blueprint - Template management
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, g
from db import db, DatabaseError
from auth import require_org

templates_bp = Blueprint('templates_bp', __name__)


@templates_bp.route('/')
@require_org
def list_templates():
    """List all templates"""
    org_id = g.current_org_id

    try:
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        templates = db.execute_proc('sp_list_templates', (org_id, include_archived))
        return render_template('templates/list.html', templates=templates or [], include_archived=include_archived)
    except DatabaseError as e:
        flash('Error loading templates', 'error')
        return render_template('templates/list.html', templates=[])


@templates_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_template():
    """Create a new template"""
    org_id = g.current_org_id

    if request.method == 'POST':
        name = request.form.get('name')
        currency_code = request.form.get('currency_code')

        if not name or not currency_code:
            flash('Template name and currency are required', 'error')
            return render_template('templates/create.html')

        try:

            print("\n" + "="*50)
            print("DEBUG: Template Creation Started")
            print("="*50)
            print(f"Form data received:")
            for key in sorted(request.form.keys()):
                print(f"  {key} = {request.form.get(key)}")
            print(f"org_id = {org_id}")
            print(f"name = {name}")
            print(f"currency_code = {currency_code}")



            print(f"\nCalling sp_create_template with: org_id={org_id}, name={name}, currency_code={currency_code}")
            result = db.execute_proc('sp_create_template', (org_id, name, currency_code, None, None))
            print(f"sp_create_template returned: {result}")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result) if result else 0}")

            if not result or len(result) == 0:
                flash('Failed to create template - no result returned from stored procedure', 'error')
                print("ERROR: No result returned from sp_create_template")
                return render_template('templates/create.html')

            template_id = result[0].get('template_id')
            template_version = result[0].get('version') or 1
            print(f"Template created: template_id={template_id}, version={template_version}")


            section_count_str = request.form.get('section_count', '0')
            print(f"\nSection count from form: '{section_count_str}'")
            try:
                section_count = int(section_count_str)
            except (ValueError, TypeError):
                section_count = 0
                print(f"WARNING: Could not parse section_count, defaulting to 0")

            print(f"Processing {section_count} sections...")


            field_id_map = {}

            if section_count == 0:
                print("WARNING: No sections to create!")
                flash('Template created but no sections were added. Please add at least one section with fields.', 'warning')
            else:
                for i in range(1, section_count + 1):
                    print(f"\n--- Processing Section {i} ---")
                    section_title = request.form.get(f'section_{i}_title')
                    section_type = request.form.get(f'section_{i}_type', 'normal')
                    section_ordinal_str = request.form.get(f'section_{i}_ordinal', str(i))

                    print(f"  section_{i}_title = {section_title}")
                    print(f"  section_{i}_type = {section_type}")
                    print(f"  section_{i}_ordinal = {section_ordinal_str}")


                    if section_type not in ['normal', 'line_item']:
                        section_type = 'normal'
                        print(f"  WARNING: Invalid section_type, defaulting to 'normal'")

                    try:
                        section_ordinal = int(section_ordinal_str) if section_ordinal_str else i
                    except ValueError:
                        section_ordinal = i
                        print(f"  WARNING: Could not parse ordinal, defaulting to {i}")

                    if section_title:


                        # Convert section_title to name (no spaces) and display_name (original)
                        section_name = section_title.replace(' ', '_').lower()
                        section_display_name = section_title
                        print(f"  Calling sp_create_section with: template_id={template_id}, version={template_version}, name={section_name}, display_name={section_display_name}, ordinal={section_ordinal}, type={section_type}")
                        try:
                            section_result = db.execute_proc('sp_create_section',
                                                             (template_id, template_version, section_name, section_display_name, section_ordinal, section_type, None))
                            print(f"  sp_create_section returned: {section_result}")

                            if section_result and len(section_result) > 0:
                                section_id = section_result[0].get('section_id')
                                print(f"  Section created: section_id={section_id}")


                                field_count_str = request.form.get(f'section_{i}_field_count', '0')
                                print(f"  Field count for section {i}: '{field_count_str}'")
                                try:
                                    field_count = int(field_count_str)
                                except ValueError:
                                    field_count = 0
                                    print(f"  WARNING: Could not parse field_count, defaulting to 0")

                                print(f"  Processing {field_count} fields...")


                                for j in range(1, field_count + 1):
                                    field_label = request.form.get(f'section_{i}_field_{j}_label')
                                    field_type = request.form.get(f'section_{i}_field_{j}_type')
                                    field_required = 1 if request.form.get(f'section_{i}_field_{j}_required') == 'on' else 0
                                    field_currency = 1 if request.form.get(f'section_{i}_field_{j}_currency') == 'on' else 0
                                    field_ordinal_str = request.form.get(f'section_{i}_field_{j}_ordinal', str(j))
                                    field_calculation = request.form.get(f'section_{i}_field_{j}_calculation', '').strip() or None

                                    print(f"    Field {j}: label={field_label}, type={field_type}, required={field_required}, currency={field_currency}, ordinal={field_ordinal_str}, calculation={field_calculation}")

                                    try:
                                        field_ordinal = int(field_ordinal_str) if field_ordinal_str else j
                                    except ValueError:
                                        field_ordinal = j

                                    if field_label and field_type:
                                        # Convert field_label to name (no spaces) and display_name (original)
                                        field_name = field_label.replace(' ', '_').lower()
                                        field_display_name = field_label

                                        field_type_lower = field_type.lower().strip()
                                        valid_types = ['string', 'number', 'date', 'boolean']
                                        if field_type_lower not in valid_types:
                                            print(f"    WARNING: Invalid field_type '{field_type}', defaulting to 'string'")
                                            field_type_lower = 'string'

                                        if field_type_lower != 'number':
                                            field_currency = 0

                                        print(f"    Calling sp_add_template_field with: section_id={section_id}, name={field_name}, display_name={field_display_name}, type={field_type_lower}, required={field_required}, currency={field_currency}, ordinal={field_ordinal}, calculation={field_calculation}")
                                        try:

                                            field_result = db.execute_proc('sp_add_template_field',
                                                          (section_id, field_name, field_display_name, field_type_lower, field_required, field_currency, field_ordinal, field_calculation, None))
                                            if field_result and len(field_result) > 0:
                                                field_id = field_result[0].get('field_id')
                                                field_id_map[(i, j)] = field_id
                                                print(f"    Field '{field_label}' created successfully with type '{field_type_lower}', field_id={field_id}")
                                            else:
                                                print(f"    WARNING: Field '{field_label}' created but no field_id returned")
                                        except DatabaseError as field_error:
                                            print(f"    ERROR creating field '{field_label}': {str(field_error)}")
                                            flash(f'Error creating field "{field_label}": {str(field_error)}', 'error')
                                            raise
                                    else:
                                        print(f"    WARNING: Field {j} skipped - missing label or type")
                            else:
                                error_msg = f'Failed to create section "{section_title}" - no result returned'
                                print(f"  ERROR: {error_msg}")
                                flash(error_msg, 'error')
                                raise DatabaseError(error_msg)
                        except DatabaseError as section_error:
                            print(f"  ERROR creating section '{section_title}': {str(section_error)}")
                            raise
                    else:
                        print(f"  WARNING: Section {i} has no title, skipping")
                        flash(f'Section {i} has no title, skipping', 'warning')


            total_field_selection = request.form.get('total_field', '').strip()
            if total_field_selection:

                try:
                    parts = total_field_selection.split('_')
                    if len(parts) == 2:
                        selected_section_num = int(parts[0])
                        selected_field_num = int(parts[1])
                        total_field_key = (selected_section_num, selected_field_num)


                        if total_field_key in field_id_map:
                            total_field_id = field_id_map[total_field_key]
                            print(f"  Setting total_field_id to: {total_field_id} (section {selected_section_num}, field {selected_field_num})")
                            db.execute_proc('sp_set_template_total_field',
                                          (template_id, template_version, total_field_id),
                                          fetch=False)
                        else:
                            print(f"  WARNING: Could not find field_id for section {selected_section_num}, field {selected_field_num}")
                except (ValueError, IndexError) as e:
                    print(f"  WARNING: Invalid total_field selection '{total_field_selection}': {str(e)}")

            print("\n" + "="*50)
            print("DEBUG: Template Creation Completed Successfully")
            print("="*50 + "\n")

            flash('Template created successfully', 'success')
            return redirect(url_for('templates_bp.view_template', template_id=template_id))

        except DatabaseError as e:
            error_msg = str(e)
            print("\n" + "="*50)
            print("DEBUG: DatabaseError occurred")
            print("="*50)
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*50 + "\n")

            flash(f'Error creating template: {error_msg}', 'error')

            if 'template_id' in locals() and template_id:
                flash(f'Template was created but sections/fields may be incomplete. Template ID: {template_id}', 'warning')
            return render_template('templates/create.html')
        except Exception as e:
            error_msg = str(e)
            print("\n" + "="*50)
            print("DEBUG: Unexpected Exception occurred")
            print("="*50)
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*50 + "\n")

            flash(f'Unexpected error: {error_msg}', 'error')

            if 'template_id' in locals() and template_id:
                flash(f'Template was created but sections/fields may be incomplete. Template ID: {template_id}', 'warning')
            return render_template('templates/create.html')

    return render_template('templates/create.html')


@templates_bp.route('/<template_id>')
@require_org
def view_template(template_id):
    """View template details"""
    org_id = g.current_org_id
    try:
        fields = db.execute_proc('sp_get_template_fields', (template_id,))


        templates = db.execute_proc('sp_list_templates', (org_id, True))
        template_info = None
        for t in templates or []:
            if t.get('template_id') == template_id:
                template_info = t
                break


        sections = {}
        if fields:
            for field in fields:
                # Map field_display_name to label for template compatibility
                if 'field_display_name' in field and 'label' not in field:
                    field['label'] = field['field_display_name']
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'section_id': section_id,
                        'title': field.get('section_title') or field.get('section_display_name') or 'Untitled Section',
                        'ordinal': field['section_ordinal'],
                        'section_type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)


        sorted_sections = sorted(sections.values(), key=lambda x: x['ordinal'])

        return render_template('templates/view.html',
                             template_id=template_id,
                             template_info=template_info,
                             sections=sorted_sections)
    except DatabaseError as e:
        flash('Error loading template', 'error')
        return redirect(url_for('templates_bp.list_templates'))


@templates_bp.route('/<template_id>/create-version', methods=['POST'])
@require_org
def create_template_version(template_id):
    """Create a new version of an existing template"""
    org_id = g.current_org_id

    try:

        result = db.execute_proc('sp_create_template_version', (template_id, org_id, None))

        if not result or len(result) == 0:
            flash('Failed to create new template version', 'error')
            return redirect(url_for('templates_bp.view_template', template_id=template_id))

        new_version = result[0].get('new_version')
        flash(f'New version {new_version} created successfully. You can now edit it.', 'success')


        return redirect(url_for('templates_bp.edit_template', template_id=template_id))
    except DatabaseError as e:
        flash(f'Error creating new version: {str(e)}', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))


@templates_bp.route('/<template_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_template(template_id):
    """Edit template (latest version)"""
    org_id = g.current_org_id

    if request.method == 'POST':
        try:

            templates = db.execute_proc('sp_list_templates', (org_id, True))
            template_info = None
            latest_version = None
            for t in templates or []:
                if t.get('template_id') == template_id:
                    if template_info is None or t.get('latest_version', 0) > latest_version:
                        template_info = t
                        latest_version = t.get('latest_version', 1)

            if not template_info or latest_version is None:
                flash('Template not found', 'error')
                return redirect(url_for('templates_bp.list_templates'))


            section_ids = request.form.getlist('section_id')
            for section_id in section_ids:
                title = request.form.get(f'section_{section_id}_title')
                ordinal = request.form.get(f'section_{section_id}_ordinal')
                section_type = request.form.get(f'section_{section_id}_type')

                if title:
                    try:
                        ordinal_int = int(ordinal) if ordinal else None
                        # Convert title to name (no spaces) and display_name (original)
                        section_name = title.replace(' ', '_').lower()
                        section_display_name = title
                        db.execute_proc('sp_update_section',
                                       (section_id, section_name, section_display_name, ordinal_int, section_type),
                                       fetch=False)
                    except (ValueError, DatabaseError) as e:
                        flash(f'Error updating section: {str(e)}', 'error')


            field_ids = request.form.getlist('field_id')
            for field_id in field_ids:
                label = request.form.get(f'field_{field_id}_label')
                data_type = request.form.get(f'field_{field_id}_type')
                is_required = 1 if request.form.get(f'field_{field_id}_required') == 'on' else 0
                is_currency = 1 if request.form.get(f'field_{field_id}_currency') == 'on' else 0
                ordinal = request.form.get(f'field_{field_id}_ordinal')
                calculation = request.form.get(f'field_{field_id}_calculation', '').strip() or None

                if label and data_type:
                    if data_type != 'number':
                        is_currency = 0
                    try:
                        ordinal_int = int(ordinal) if ordinal else None
                        # Convert label to name (no spaces) and display_name (original)
                        field_name = label.replace(' ', '_').lower()
                        field_display_name = label
                        db.execute_proc('sp_update_field',
                                       (field_id, field_name, field_display_name, data_type, is_required, is_currency, ordinal_int, calculation),
                                       fetch=False)
                    except (ValueError, DatabaseError) as e:
                        flash(f'Error updating field: {str(e)}', 'error')


            for section_id in section_ids:

                new_field_keys = [k for k in request.form.keys() if k.startswith(f'new_field_{section_id}_')]
                if new_field_keys:

                    field_nums = set()
                    for key in new_field_keys:
                        parts = key.split('_')
                        if len(parts) >= 4:
                            try:
                                field_nums.add(int(parts[3]))
                            except ValueError:
                                pass

                    for field_num in field_nums:
                        field_label = request.form.get(f'new_field_{section_id}_{field_num}_label')
                        field_type = request.form.get(f'new_field_{section_id}_{field_num}_type')
                        field_required = 1 if request.form.get(f'new_field_{section_id}_{field_num}_required') == 'on' else 0
                        field_currency = 1 if request.form.get(f'new_field_{section_id}_{field_num}_currency') == 'on' else 0
                        field_ordinal = request.form.get(f'new_field_{section_id}_{field_num}_ordinal', str(field_num))
                        field_calculation = request.form.get(f'new_field_{section_id}_{field_num}_calculation', '').strip() or None

                        if field_label and field_type:
                            if field_type != 'number':
                                field_currency = 0
                            try:
                                field_ordinal_int = int(field_ordinal) if field_ordinal else field_num
                                # Convert field_label to name (no spaces) and display_name (original)
                                field_name = field_label.replace(' ', '_').lower()
                                field_display_name = field_label
                                db.execute_proc('sp_add_template_field',
                                               (section_id, field_name, field_display_name, field_type, field_required, field_currency, field_ordinal_int, field_calculation, None),
                                               fetch=False)
                            except DatabaseError as e:
                                flash(f'Error adding field: {str(e)}', 'error')


            new_section_count = int(request.form.get('new_section_count', 0))
            for i in range(1, new_section_count + 1):
                title = request.form.get(f'new_section_{i}_title')
                ordinal = request.form.get(f'new_section_{i}_ordinal')
                section_type = request.form.get(f'new_section_{i}_type', 'normal')

                if title:
                    try:
                        ordinal_int = int(ordinal) if ordinal else latest_version
                        # Convert title to name (no spaces) and display_name (original)
                        section_name = title.replace(' ', '_').lower()
                        section_display_name = title
                        result = db.execute_proc('sp_create_section',
                                                 (template_id, latest_version, section_name, section_display_name, ordinal_int, section_type, None))
                        if result and len(result) > 0:
                            new_section_id = result[0].get('section_id')


                            field_count = int(request.form.get(f'new_section_{i}_field_count', 0))
                            for j in range(1, field_count + 1):
                                field_label = request.form.get(f'new_section_{i}_field_{j}_label')
                                field_type = request.form.get(f'new_section_{i}_field_{j}_type')
                                field_required = 1 if request.form.get(f'new_section_{i}_field_{j}_required') == 'on' else 0
                                field_currency = 1 if request.form.get(f'new_section_{i}_field_{j}_currency') == 'on' else 0
                                field_ordinal = request.form.get(f'new_section_{i}_field_{j}_ordinal', str(j))
                                field_calculation = request.form.get(f'new_section_{i}_field_{j}_calculation', '').strip() or None

                                if field_label and field_type:
                                    if field_type != 'number':
                                        field_currency = 0
                                    try:
                                        field_ordinal_int = int(field_ordinal) if field_ordinal else j
                                        # Convert field_label to name (no spaces) and display_name (original)
                                        field_name = field_label.replace(' ', '_').lower()
                                        field_display_name = field_label
                                        db.execute_proc('sp_add_template_field',
                                                       (new_section_id, field_name, field_display_name, field_type, field_required, field_currency, field_ordinal_int, field_calculation, None),
                                                       fetch=False)
                                    except DatabaseError as e:
                                        flash(f'Error adding field: {str(e)}', 'error')
                    except (ValueError, DatabaseError) as e:
                        flash(f'Error adding section: {str(e)}', 'error')


            total_field_selection = request.form.get('total_field', '').strip()
            if total_field_selection:



                try:

                    if len(total_field_selection) == 36 and total_field_selection.count('-') == 4:

                        db.execute_proc('sp_set_template_total_field',
                                      (template_id, latest_version, total_field_selection),
                                      fetch=False)
                        print(f"  Set total_field_id to existing field: {total_field_selection}")
                    else:


                        print(f"  WARNING: New field selected as total, but field_id not yet available. Please set it after saving.")
                except (ValueError, DatabaseError) as e:
                    print(f"  WARNING: Could not set total_field_id: {str(e)}")
            else:

                try:
                    db.execute_proc('sp_set_template_total_field',
                                  (template_id, latest_version, None),
                                  fetch=False)
                    print(f"  Cleared total_field_id")
                except (ValueError, DatabaseError) as e:
                    print(f"  WARNING: Could not clear total_field_id: {str(e)}")

            flash('Template updated successfully', 'success')
            return redirect(url_for('templates_bp.view_template', template_id=template_id))

        except DatabaseError as e:
            flash(f'Error updating template: {str(e)}', 'error')
            return redirect(url_for('templates_bp.edit_template', template_id=template_id))


    try:

        templates = db.execute_proc('sp_list_templates', (org_id, False))
        template_info = None
        latest_version = None
        for t in templates or []:
            if t.get('template_id') == template_id:
                if template_info is None or t.get('latest_version', 0) > latest_version:
                    template_info = t
                    latest_version = t.get('latest_version', 1)

        if not template_info or latest_version is None:
            flash('Template not found', 'error')
            return redirect(url_for('templates_bp.list_templates'))



        try:

            check_result = db.execute_proc('sp_check_template_version_has_invoices',
                                          (template_id, latest_version, org_id))

            has_invoices = False
            invoice_count = 0
            if check_result and len(check_result) > 0:
                has_invoices = check_result[0].get('has_invoices', 0) == 1
                invoice_count = check_result[0].get('invoice_count', 0)


            if has_invoices:
                print(f"Template version {latest_version} has {invoice_count} invoice(s). Creating new version for editing...")
                result = db.execute_proc('sp_create_template_version', (template_id, org_id, None))

                if result and len(result) > 0:
                    new_version = result[0].get('new_version')
                    flash(f'A new version (v{new_version}) was created automatically to preserve existing invoices. You are now editing the new version.', 'info')

                    templates = db.execute_proc('sp_list_templates', (org_id, True))
                    for t in templates or []:
                        if t.get('template_id') == template_id and t.get('version') == new_version:
                            template_info = t
                            latest_version = new_version
                            break
                else:
                    flash('Failed to create new template version', 'error')
                    return redirect(url_for('templates_bp.view_template', template_id=template_id))
        except Exception as e:
            print(f"Error checking for invoices or creating new version: {str(e)}")

            pass


        fields = db.execute_proc('sp_get_template_fields', (template_id,))


        if template_info.get('version') != latest_version:
            flash('Template not found or you can only edit the latest version', 'error')
            return redirect(url_for('templates_bp.list_templates'))


        total_field_id = None
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT total_field_id
                    FROM template
                    WHERE template_id = %s AND version = %s
                """, (template_id, latest_version))
                result = cursor.fetchone()
                if result:
                    total_field_id = result.get('total_field_id')
                cursor.close()
        except Exception as e:
            print(f"Warning: Could not fetch total_field_id: {e}")


        sections = {}
        if fields:
            for field in fields:
                # Map field_display_name to label for template compatibility
                if 'field_display_name' in field and 'label' not in field:
                    field['label'] = field['field_display_name']
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'section_id': section_id,
                        'title': field.get('section_title') or field.get('section_display_name') or 'Untitled Section',
                        'ordinal': field['section_ordinal'],
                        'section_type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)

        sorted_sections = sorted(sections.values(), key=lambda x: x['ordinal'])


        template_info['total_field_id'] = total_field_id

        return render_template('templates/edit.html',
                             template_id=template_id,
                             template_info=template_info,
                             sections=sorted_sections)
    except DatabaseError as e:
        flash('Error loading template', 'error')
        return redirect(url_for('templates_bp.list_templates'))


@templates_bp.route('/<template_id>/section/<section_id>/delete', methods=['POST'])
@require_org
def delete_section(template_id, section_id):
    """Delete a section from template"""
    try:
        db.execute_proc('sp_delete_section', (section_id,), fetch=False)
        flash('Section deleted successfully', 'success')
    except DatabaseError as e:
        flash(f'Error deleting section: {str(e)}', 'error')

    return redirect(url_for('templates_bp.edit_template', template_id=template_id))


@templates_bp.route('/<template_id>/field/<field_id>/delete', methods=['POST'])
@require_org
def delete_field(template_id, field_id):
    """Delete a field from template"""
    try:
        db.execute_proc('sp_delete_field', (field_id,), fetch=False)
        flash('Field deleted successfully', 'success')
    except DatabaseError as e:
        flash(f'Error deleting field: {str(e)}', 'error')

    return redirect(url_for('templates_bp.edit_template', template_id=template_id))


@templates_bp.route('/<template_id>/archive', methods=['POST'])
@require_org
def archive_template(template_id):
    """Archive a template"""
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_archive_template', (template_id, org_id), fetch=False)
        flash('Template archived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error archiving template: {str(e)}', 'error')
    
    return redirect(url_for('templates_bp.view_template', template_id=template_id))


@templates_bp.route('/<template_id>/unarchive', methods=['POST'])
@require_org
def unarchive_template(template_id):
    """Unarchive a template"""
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_unarchive_template', (template_id, org_id), fetch=False)
        flash('Template unarchived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error unarchiving template: {str(e)}', 'error')
    
    return redirect(url_for('templates_bp.view_template', template_id=template_id))

