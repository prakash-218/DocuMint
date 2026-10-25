"""
Templates blueprint - Template management
"""

import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash, g
from db import db, DatabaseError
from auth import require_org, get_current_org_role
from access import get_org_template, get_template_ids
from calculations import validate_formula
from invoice_service import get_template_fields

logger = logging.getLogger(__name__)

templates_bp = Blueprint('templates_bp', __name__)


def _warn_invalid_formulas(template_id):
    """Flash a warning for each formula that won't evaluate against the template."""
    fields = get_template_fields(template_id)
    for field in fields:
        formula = field.get('calculation_formula')
        if not formula:
            continue
        error = validate_formula(formula, fields, field.get('section_name') or '')
        if error:
            label = field.get('field_display_name') or field.get('field_name')
            flash(f'Formula for "{label}" will not calculate ({error}): {formula}', 'warning')


@templates_bp.route('/')
@require_org
def list_templates():
    """Templates as cards: one per template (latest version), with columns and usage"""
    from template_service import template_cards

    org_id = g.current_org_id
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    try:
        cards = template_cards(org_id, include_archived)
    except DatabaseError:
        logger.exception("Failed to list templates for %s", org_id)
        flash('Error loading templates', 'error')
        cards = []
    from pagination import paginate
    page = paginate(cards, per_page=12)                 # cards: a grid of 12
    return render_template('templates/list.html', templates=page.items, page=page, include_archived=include_archived,
                           current_org_role=get_current_org_role())


@templates_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_template():
    """New template in the builder (owners)."""
    import template_builder as TB
    if get_current_org_role() not in ('owner', 'admin'):
        flash('Only owners and admins can create templates', 'error')
        return redirect(url_for('templates_bp.list_templates'))
    org_id = g.current_org_id
    if request.method == 'POST':
        try:
            template_id, _ = TB.save(org_id, request.form)
        except TB.TemplateError as e:
            flash(str(e), 'error')
            sections, _ = TB.sections_from_form(request.form)
            return _builder(None, None, sections or TB.STARTER)
        except DatabaseError:
            logger.exception("Template create failed")
            flash('Could not create the template', 'error')
            return _builder(None, None, TB.STARTER)
        flash('Template created', 'success')
        _warn_invalid_formulas(template_id)
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    return _builder(None, None, TB.STARTER)


def _builder(template_id, info, sections, in_use=0):
    import template_builder as TB
    from document_service import get_org_profile
    from money import SYMBOLS
    total_key = ''
    for i, sec in enumerate(sections, start=1):
        for j, f in enumerate(sec['fields'], start=1):
            if f.get('total'):
                total_key = f'{i}:{j}'
    return render_template('templates/builder.html', template_id=template_id, info=info, sections=sections,
                           total_key=total_key, in_use=in_use, field_types=TB.FIELD_TYPES,
                           section_types=TB.SECTION_TYPES, currencies=list(SYMBOLS),
                           default_currency=get_org_profile(g.current_org_id)[1].get('default_currency') or 'INR')


@templates_bp.route('/<template_id>')
@require_org
def view_template(template_id):
    """Template page: calculated preview with sample values, formulas, versions, usage"""
    from template_service import template_overview

    org_id = g.current_org_id
    try:
        overview = template_overview(org_id, template_id)
    except DatabaseError:
        logger.exception("Failed to load template %s", template_id)
        overview = None
    if not overview:
        flash('Template not found', 'error')
        return redirect(url_for('templates_bp.list_templates'))
    return render_template('templates/view.html', template_id=template_id, t=overview,
                           template_info=overview['info'], current_org_role=get_current_org_role())


@templates_bp.route('/<template_id>/layout', methods=['GET', 'POST'])
@require_org
def edit_layout(template_id):
    """Pages & printing: which pages the template prints, their columns, copies and box fields."""
    from documents import DOC_TYPES
    from layout import PAGE_KINDS, layout_from_form, load_layout, new_page, save_layout, template_is_export

    org_id = g.current_org_id
    if get_current_org_role() not in ('owner', 'admin'):
        flash('Only owners and admins can change how templates print', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    info = get_org_template(template_id, org_id)
    if not info:
        flash('Template not found', 'error')
        return redirect(url_for('templates_bp.list_templates'))

    layout = load_layout(template_id, org_id)
    if request.method == 'POST':
        layout = layout_from_form(request.form)
        if request.form.get('add_page') in ('packing', 'annexure'):
            layout['pages'].append(new_page(request.form['add_page']))
        try:
            save_layout(template_id, org_id, layout)
        except DatabaseError:
            logger.exception("Failed to save layout for %s", template_id)
            flash('Could not save the page settings', 'error')
            return redirect(url_for('templates_bp.edit_layout', template_id=template_id))
        if request.form.get('add_page'):
            flash('Page added. Set it up below, then save.', 'success')
        else:
            flash('Pages & printing saved', 'success')
        return redirect(url_for('templates_bp.edit_layout', template_id=template_id))

    fields = get_template_fields(template_id, info.get('latest_version'))
    item_fields, section_choices = [], []
    for f in fields:
        if f.get('section_type') == 'line_item' and 'break' not in (f.get('section_name') or '').lower():
            if f['field_name'] not in [x['field_name'] for x in item_fields]:
                item_fields.append({'field_name': f['field_name'], 'label': f.get('field_display_name') or f['field_name']})
        sec = {'name': (f.get('section_name') or '').lower(), 'label': f.get('section_display_name') or f.get('section_name')}
        if sec not in section_choices:
            section_choices.append(sec)
    return render_template('templates/layout.html', template_id=template_id, info=info, layout=layout,
                           item_fields=item_fields, section_choices=section_choices,
                           doc_types=DOC_TYPES, page_kinds=PAGE_KINDS,
                           auto_export=template_is_export(template_id, org_id, {**layout, 'export': None}))


@templates_bp.route('/<template_id>/create-version', methods=['POST'])
@require_org
def create_template_version(template_id):
    """Create a new version of an existing template"""
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to create template versions.', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    
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
    """Edit the latest version in the builder. Nothing is written until Save; a version
    that documents use is kept and the next version is made instead."""
    import template_builder as TB
    if get_current_org_role() not in ('owner', 'admin'):
        flash('Only owners and admins can edit templates', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    org_id = g.current_org_id
    info = next((t for t in db.execute_proc('sp_list_templates', (org_id, False)) or []
                 if t.get('template_id') == template_id and t.get('version') == t.get('latest_version')), None)
    if not info:
        flash('Template not found', 'error')
        return redirect(url_for('templates_bp.list_templates'))

    if request.method == 'POST':
        try:
            _, new_version = TB.save(org_id, request.form, template_id)
        except TB.TemplateError as e:
            flash(str(e), 'error')
            sections, _ = TB.sections_from_form(request.form)
            return _builder(template_id, info, sections or TB.sections_for_editor(template_id, info['version']))
        except DatabaseError:
            logger.exception("Template save failed for %s", template_id)
            flash('Could not save the template', 'error')
            return redirect(url_for('templates_bp.edit_template', template_id=template_id))
        flash(f'Saved as v{new_version}. Existing documents keep v{new_version - 1}.' if new_version else 'Template saved',
              'success')
        _warn_invalid_formulas(template_id)
        return redirect(url_for('templates_bp.view_template', template_id=template_id))

    return _builder(template_id, info, TB.sections_for_editor(template_id, info['version']),
                    in_use=TB.version_in_use(org_id, template_id, info['version']))


@templates_bp.route('/<template_id>/section/<section_id>/delete', methods=['POST'])
@require_org
def delete_section(template_id, section_id):
    """Delete a section from template"""
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to delete sections.', 'error')
        return redirect(url_for('templates_bp.edit_template', template_id=template_id))
    
    allowed_section_ids, allowed_field_ids = (get_template_ids(template_id)
                                              if get_org_template(template_id, g.current_org_id) else (set(), set()))
    if section_id not in allowed_section_ids:
        flash('Section not found', 'error')
        return redirect(url_for('templates_bp.edit_template', template_id=template_id))

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
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to delete fields.', 'error')
        return redirect(url_for('templates_bp.edit_template', template_id=template_id))
    
    allowed_section_ids, allowed_field_ids = (get_template_ids(template_id)
                                              if get_org_template(template_id, g.current_org_id) else (set(), set()))
    if field_id not in allowed_field_ids:
        flash('Field not found', 'error')
        return redirect(url_for('templates_bp.edit_template', template_id=template_id))

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
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to archive templates.', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    
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
    current_role = get_current_org_role()
    if current_role not in ('owner', 'admin'):
        flash(f'Your role is {current_role or "unknown"}. You need to be an owner or admin to unarchive templates.', 'error')
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    
    org_id = g.current_org_id
    
    try:
        db.execute_proc('sp_unarchive_template', (template_id, org_id), fetch=False)
        flash('Template unarchived successfully', 'success')
    except DatabaseError as e:
        flash(f'Error unarchiving template: {str(e)}', 'error')
    
    return redirect(url_for('templates_bp.view_template', template_id=template_id))

