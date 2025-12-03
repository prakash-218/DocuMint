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
        templates = db.execute_proc('sp_list_templates', (org_id,))
        return render_template('templates/list.html', templates=templates or [])
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
            # Debug: Print all form data
            print("\n" + "="*50)
            print("DEBUG: Template Creation Started")
            print("="*50)
            print(f"Form data received:")
            for key in sorted(request.form.keys()):
                print(f"  {key} = {request.form.get(key)}")
            print(f"org_id = {org_id}")
            print(f"name = {name}")
            print(f"currency_code = {currency_code}")
            
            # Create template
            # Procedure has 3 IN params + 2 OUT params = 5 total, need placeholders for OUT
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
            
            # Create sections and fields
            section_count_str = request.form.get('section_count', '0')
            print(f"\nSection count from form: '{section_count_str}'")
            try:
                section_count = int(section_count_str)
            except (ValueError, TypeError):
                section_count = 0
                print(f"WARNING: Could not parse section_count, defaulting to 0")
            
            print(f"Processing {section_count} sections...")
            
            # Track field IDs: (section_num, field_num) -> field_id
            field_id_map = {}
            
            if section_count == 0:
                print("WARNING: No sections to create!")
                flash('Template created but no sections were added. Please add at least one section with fields.', 'warning')
            else:
                for i in range(1, section_count + 1):  # JavaScript uses 1-based indexing
                    print(f"\n--- Processing Section {i} ---")
                    section_title = request.form.get(f'section_{i}_title')
                    section_type = request.form.get(f'section_{i}_type', 'normal')
                    section_ordinal_str = request.form.get(f'section_{i}_ordinal', str(i))
                    
                    print(f"  section_{i}_title = {section_title}")
                    print(f"  section_{i}_type = {section_type}")
                    print(f"  section_{i}_ordinal = {section_ordinal_str}")
                    
                    # Validate section_type
                    if section_type not in ['normal', 'line_item']:
                        section_type = 'normal'
                        print(f"  WARNING: Invalid section_type, defaulting to 'normal'")
                    
                    try:
                        section_ordinal = int(section_ordinal_str) if section_ordinal_str else i
                    except ValueError:
                        section_ordinal = i
                        print(f"  WARNING: Could not parse ordinal, defaulting to {i}")
                    
                    if section_title:
                        # Create section
                        # Procedure has 5 IN params + 1 OUT param = 6 total, need placeholder for OUT
                        print(f"  Calling sp_create_section with: template_id={template_id}, version={template_version}, title={section_title}, ordinal={section_ordinal}, type={section_type}")
                        try:
                            section_result = db.execute_proc('sp_create_section', 
                                                             (template_id, template_version, section_title, section_ordinal, section_type, None))
                            print(f"  sp_create_section returned: {section_result}")
                            
                            if section_result and len(section_result) > 0:
                                section_id = section_result[0].get('section_id')
                                print(f"  Section created: section_id={section_id}")
                                
                                # Create fields for this section
                                field_count_str = request.form.get(f'section_{i}_field_count', '0')
                                print(f"  Field count for section {i}: '{field_count_str}'")
                                try:
                                    field_count = int(field_count_str)
                                except ValueError:
                                    field_count = 0
                                    print(f"  WARNING: Could not parse field_count, defaulting to 0")
                                
                                print(f"  Processing {field_count} fields...")
                                
                                # JavaScript uses 1-based indexing for fields too
                                for j in range(1, field_count + 1):
                                    field_label = request.form.get(f'section_{i}_field_{j}_label')
                                    field_type = request.form.get(f'section_{i}_field_{j}_type')
                                    field_required = 1 if request.form.get(f'section_{i}_field_{j}_required') == 'on' else 0
                                    field_ordinal_str = request.form.get(f'section_{i}_field_{j}_ordinal', str(j))
                                    field_calculation = request.form.get(f'section_{i}_field_{j}_calculation', '').strip() or None
                                    
                                    print(f"    Field {j}: label={field_label}, type={field_type}, required={field_required}, ordinal={field_ordinal_str}, calculation={field_calculation}")
                                    
                                    try:
                                        field_ordinal = int(field_ordinal_str) if field_ordinal_str else j
                                    except ValueError:
                                        field_ordinal = j
                                    
                                    if field_label and field_type:
                                        # Validate and normalize field_type
                                        field_type_lower = field_type.lower().strip()
                                        valid_types = ['string', 'number', 'date', 'boolean']
                                        if field_type_lower not in valid_types:
                                            print(f"    WARNING: Invalid field_type '{field_type}', defaulting to 'string'")
                                            field_type_lower = 'string'
                                        
                                        print(f"    Calling sp_add_template_field with: section_id={section_id}, label={field_label}, type={field_type_lower}, required={field_required}, ordinal={field_ordinal}, calculation={field_calculation}")
                                        try:
                                            # Procedure has 6 IN params + 1 OUT param = 7 total, need placeholder for OUT
                                            field_result = db.execute_proc('sp_add_template_field',
                                                          (section_id, field_label, field_type_lower, field_required, field_ordinal, field_calculation, None))
                                            if field_result and len(field_result) > 0:
                                                field_id = field_result[0].get('field_id')
                                                field_id_map[(i, j)] = field_id
                                                print(f"    Field '{field_label}' created successfully with type '{field_type_lower}', field_id={field_id}")
                                            else:
                                                print(f"    WARNING: Field '{field_label}' created but no field_id returned")
                                        except DatabaseError as field_error:
                                            print(f"    ERROR creating field '{field_label}': {str(field_error)}")
                                            flash(f'Error creating field "{field_label}": {str(field_error)}', 'error')
                                            raise  # Re-raise to trigger outer exception handler
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
            
            # Set total_field_id if specified
            total_field_selection = request.form.get('total_field', '').strip()
            if total_field_selection:
                # Format: "section_num_field_num" (e.g., "2_3" means section 2, field 3)
                try:
                    parts = total_field_selection.split('_')
                    if len(parts) == 2:
                        selected_section_num = int(parts[0])
                        selected_field_num = int(parts[1])
                        total_field_key = (selected_section_num, selected_field_num)
                        
                        # Find the field_id from our tracking
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
            # If template was created but sections/fields failed, provide helpful message
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
            # If template was created but sections/fields failed, provide helpful message
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
        
        # Get template info to show version
        templates = db.execute_proc('sp_list_templates', (org_id,))
        template_info = None
        for t in templates or []:
            if t.get('template_id') == template_id:
                template_info = t
                break
        
        # Group fields by section
        sections = {}
        if fields:
            for field in fields:
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'section_id': section_id,
                        'title': field['section_title'],
                        'ordinal': field['section_ordinal'],
                        'section_type': field.get('section_type', 'normal'),
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)
        
        # Sort sections by ordinal
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
        # Create new version (copies all sections and fields)
        result = db.execute_proc('sp_create_template_version', (template_id, org_id, None))
        
        if not result or len(result) == 0:
            flash('Failed to create new template version', 'error')
            return redirect(url_for('templates_bp.view_template', template_id=template_id))
        
        new_version = result[0].get('new_version')
        flash(f'New version {new_version} created successfully. You can now edit it.', 'success')
        
        # Redirect back to view the template (will show latest version)
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    except DatabaseError as e:
        flash(f'Error creating new version: {str(e)}', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))

