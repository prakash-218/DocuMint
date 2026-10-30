"""
Templates blueprint - Template management
"""

import logging
from flask import Blueprint, request, redirect, url_for, flash, g
from db import db, DatabaseError
from auth import require_org
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
    import nav
    return nav.spa('Templates', 'list')                     # the cards: template_view.cards


@templates_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_template():
    """New template in the builder (owners)."""
    import template_builder as TB
    org_id = g.current_org_id
    if request.method == 'POST':
        try:
            template_id, _ = TB.save(org_id, request.form)
        except TB.TemplateError as e:
            flash(str(e), 'error')
            return _builder('New template')
        except DatabaseError:
            logger.exception("Template create failed")
            flash('Could not create the template', 'error')
            return _builder('New template')
        _save_used_for(template_id, org_id, request.form.getlist('used_for'))
        flash('Template created', 'success')
        _warn_invalid_formulas(template_id)
        return redirect(url_for('templates_bp.view_template', template_id=template_id))
    return _builder('New template')


def _builder(title):
    """The builder, in the React app (template_view.builder). After a POST that didn't save, it starts from what was
    sent (nav.spa(posted=True))."""
    import nav
    return nav.spa(title, 'page', posted=request.method == 'POST')


@templates_bp.route('/<template_id>')
@require_org
def view_template(template_id):
    """Template page: calculated preview with sample values, formulas, versions, usage"""
    import nav
    from template_service import template_versions
    versions = template_versions(g.current_org_id, template_id)
    if not versions:
        flash('Template not found', 'error')
        return redirect(url_for('templates_bp.list_templates'))
    return nav.spa(versions[0].get('name') or 'Template', 'page')     # the page: template_view.overview


@templates_bp.route('/<template_id>/layout', methods=['GET', 'POST'])
@require_org
def edit_layout(template_id):
    """Pages & printing: which pages the template prints, their columns, copies and box fields."""
    from layout import layout_from_form, load_layout, new_page, save_layout

    org_id = g.current_org_id
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

    import nav
    return nav.spa(f"Pages & printing · {info.get('name') or ''}", 'page')    # the form: template_view.layout_page


def _save_used_for(template_id, org_id, used_for):
    """A new template's "Used for" (none ticked: guessed from its name until it's set)."""
    from layout import load_layout, save_layout
    if not used_for:
        return
    try:
        save_layout(template_id, org_id, {**load_layout(template_id, org_id), 'used_for': used_for})
    except DatabaseError:
        logger.exception("Could not save what template %s is used for", template_id)


def _ticked_types(info, layout):
    """The "Used for" boxes to tick: the template's setting, or the types its name suggests (none when it says nothing)."""
    from documents import CHOOSABLE
    from layout import template_types
    if layout.get('used_for') is not None:
        return layout['used_for']
    guess = template_types(info.get('name') or info.get('template_name'), layout)
    return [] if guess == list(CHOOSABLE) else guess


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
    """Edit the latest version in the builder. Nothing is written until Save; a version
    that documents use is kept and the next version is made instead."""
    import template_builder as TB
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
            return _builder(f"Edit {info.get('name') or ''}")
        except DatabaseError:
            logger.exception("Template save failed for %s", template_id)
            flash('Could not save the template', 'error')
            return redirect(url_for('templates_bp.edit_template', template_id=template_id))
        flash(f'Saved as v{new_version}. Existing documents keep v{new_version - 1}.' if new_version else 'Template saved',
              'success')
        _warn_invalid_formulas(template_id)
        return redirect(url_for('templates_bp.view_template', template_id=template_id))

    return _builder(f"Edit {info.get('name') or ''}")


@templates_bp.route('/<template_id>/section/<section_id>/delete', methods=['POST'])
@require_org
def delete_section(template_id, section_id):
    """Delete a section from template"""
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

