"""
Projects blueprint - group a customer's quote, proforma and invoices, and keep
their documents (PO, drawings...) with them.
"""

import io
import logging
import re

from flask import Blueprint, abort, flash, g, jsonify, redirect, request, send_file, url_for

from access import get_org_customer, get_org_invoice, safe_referrer
from auth import require_org
import permissions
from db import DatabaseError, db
import projects as J
import activity
import contacts
import nav

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects_bp', __name__)


def _user_id():
    return (getattr(g, 'current_user', None) or {}).get('user_id')


def _project_or_404(project_id):
    project = J.get_project(project_id, g.current_org_id)
    if not project:
        abort(404)
    return project


def _fiscal_year(value):
    """A financial year typed or picked in a form ('26-27', or '2026' for calendar years), else None."""
    value = (value or '').strip()
    return value if re.fullmatch(r'\d{2}-\d{2}|\d{4}', value) else None


@projects_bp.route('/options')
@require_org
def picker_options():
    """Projects to pick from, for the project picker (JSON): a customer's (with exact=1, not its sites'),
    or every customer's; status=open for open ones only."""
    customer_id = request.args.get('customer_id') or None
    status = request.args.get('status') if request.args.get('status') in J.PROJECT_STATUSES else None
    rows = J.list_projects(g.current_org_id, customer_id, status)
    if customer_id and request.args.get('exact'):
        rows = [r for r in rows if str(r['customer_id']) == customer_id]
    return jsonify(projects=J.picker_rows(rows), this_year=J.current_fiscal_year(g.current_org_id))


@projects_bp.route('/new', methods=['GET', 'POST'])
@require_org
def create_project():
    org_id = g.current_org_id
    back = url_for('projects_bp.list_projects')

    if request.method == 'POST':
        from_invoice = request.form.get('invoice_id')
        title = (request.form.get('title') or '').strip()
        try:
            if from_invoice:
                header, _ = get_org_invoice(from_invoice, org_id)
                if not header:
                    abort(404)
                project_id = J.group_family(from_invoice, org_id, _user_id(), title=title or None)
            else:
                customer_id = request.form.get('customer_id')
                if not customer_id or not get_org_customer(customer_id, org_id)[0]:
                    flash('Choose the customer this project is for', 'error')
                    return redirect(url_for('projects_bp.create_project'))
                if not title:
                    flash('Give the project a name, e.g. "Welding fixture for Line 3"', 'error')
                    return redirect(url_for('projects_bp.create_project', customer_id=customer_id))
                project_id = J.create_project(org_id, customer_id, title, request.form.get('reference'),
                                              request.form.get('notes'), _user_id(), _fiscal_year(request.form.get('fiscal_year')))
        except DatabaseError:
            logger.exception("Failed to create project")
            flash('Could not create the project', 'error')
            return redirect(back)
        created = J.get_project(project_id, org_id)
        if created:
            activity.record('project_created', f"Project {J.project_label(created)} · {created['title']}", project_id=project_id,
                            body=created['customer_name'], link=url_for('projects_bp.view_project', project_id=project_id))
        if request.form.get('next') in ('quote', 'proforma', 'invoice'):
            return redirect(url_for('invoices_bp.create_invoice', doc_type=request.form['next'], project_id=project_id))
        flash('Project created', 'success')
        return redirect(url_for('projects_bp.view_project', project_id=project_id))

    import nav
    return nav.spa('New project', 'page')                  # the form: project_view.new_project


@projects_bp.route('/')
@require_org
def list_projects():
    """Every project with where it stands, as a list or a board by stage, in the React app (frontend/src/islands/board/)."""
    return nav.spa('Projects', 'list')


@projects_bp.route('/board')
@require_org
def board():
    """Where the new list was while it was opt-in."""
    return redirect(url_for('projects_bp.list_projects'))


@projects_bp.route('/<project_id>')
@require_org
def view_project(project_id):
    """A project: where it is, what's next, its documents, timeline, people and files, in the React app
    (frontend/src/islands/project/)."""
    project = _project_or_404(project_id)
    return nav.spa(f"{project['title']} · {J.project_label(project)}", 'page')


@projects_bp.route('/<project_id>/new')
@require_org
def view_project_new(project_id):
    """Where the new page was while it was opt-in."""
    return redirect(url_for('projects_bp.view_project', project_id=project_id))


@projects_bp.route('/<project_id>/edit', methods=['POST'])
@require_org
def edit_project(project_id):
    project = _project_or_404(project_id)
    back = _project_page(project_id)
    status = request.form.get('status', project['status'])
    try:
        db.execute_proc('sp_update_project', (
            project_id, g.current_org_id,
            (request.form.get('title', project['title']) or project['title']).strip()[:200],
            (request.form.get('reference', project.get('reference') or '') or '').strip()[:100],
            status if status in J.PROJECT_STATUSES else project['status'],
            (request.form.get('notes', project.get('notes') or '') or '').strip(),
            _fiscal_year(request.form.get('fiscal_year')) or project['fiscal_year']), fetch=False)
    except DatabaseError:
        logger.exception("Failed to update project %s", project_id)
        flash('Could not save the project', 'error')
    else:
        if status != project['status'] and status in J.PROJECT_STATUSES:
            activity.record('project_status', f"Project {J.project_label(project)} marked {J.PROJECT_STATUSES[status].lower()}",
                            project_id=project_id, link=url_for('projects_bp.view_project', project_id=project_id))
        flash('Project updated', 'success')
    return redirect(back)


@projects_bp.route('/<project_id>/people', methods=['POST'])
@require_org
def set_person(project_id):
    """What one of the customer's contacts gets on this project: everything, proformas and invoices, or nothing."""
    _project_or_404(project_id)
    back = _project_page(project_id) + '#people'
    gets = request.form.get('gets')
    if gets not in contacts.GETS:
        return redirect(back)
    try:
        db.execute_proc('sp_set_project_contact', (project_id, g.current_org_id, request.form.get('contact_id'), gets),
                        fetch=False)
    except DatabaseError:
        flash('Could not change that contact', 'error')
    return redirect(back)


@projects_bp.route('/<project_id>/delete', methods=['POST'])
@require_org
def delete_project(project_id):
    _project_or_404(project_id)
    try:
        db.execute_proc('sp_delete_project', (project_id, g.current_org_id), fetch=False)
    except DatabaseError:
        logger.exception("Failed to delete project %s", project_id)
        flash('Could not delete the project', 'error')
        return redirect(_project_page(project_id))
    flash('Project deleted. Its documents and files are kept, just no longer grouped.', 'success')
    return redirect(url_for('projects_bp.list_projects'))


def _project_page(project_id):
    """The project's page to go back to."""
    return url_for('projects_bp.view_project', project_id=project_id)


@projects_bp.route('/<project_id>/documents', methods=['POST'])
@require_org
def project_document(project_id):
    """Add (or remove) one of the customer's documents to this project."""
    org_id = g.current_org_id
    _project_or_404(project_id)
    back = _project_page(project_id)
    invoice_id = request.form.get('invoice_id')
    header, _ = get_org_invoice(invoice_id, org_id) if invoice_id else (None, None)
    if not header:
        flash('Document not found', 'error')
        return redirect(back)
    try:
        if request.form.get('action') == 'remove':
            J.set_project(invoice_id, org_id, None)
            flash(f'{header.get("doc_number") or "Document"} removed from the project', 'success')
        else:
            J.set_project(invoice_id, org_id, project_id)
            flash(f'{header.get("doc_number") or "Document"} added to the project', 'success')
    except DatabaseError as e:
        flash('That document is for a different customer' if 'same customer' in str(e) else 'Could not update the project',
              'error')
    return redirect(back)


@projects_bp.route('/for-document/<invoice_id>', methods=['POST'])
@require_org
def document_project(invoice_id):
    """From a document page: put it in an existing project of the customer, or take it out."""
    org_id = g.current_org_id
    back = url_for('invoices_bp.view_invoice', invoice_id=invoice_id)
    header, _ = get_org_invoice(invoice_id, org_id)
    if not header:
        abort(404)
    project_id = request.form.get('project_id') or None
    try:
        if project_id == 'new':
            project_id = J.group_family(invoice_id, org_id, _user_id())
            flash('Project started with this document and the ones linked to it', 'success')
        else:
            J.set_project(invoice_id, org_id, project_id)
            flash('Added to the project' if project_id else 'Removed from the project', 'success')
    except DatabaseError:
        logger.exception("Failed to set project for %s", invoice_id)
        flash('Could not change the project', 'error')
    return redirect(back)


# ---------------------------------------------------------------- Customer documents

@projects_bp.route('/files', methods=['POST'])
@require_org
def upload_file():
    org_id = g.current_org_id
    back = safe_referrer('projects_bp.list_projects')
    customer_id = request.form.get('customer_id')
    project_id = request.form.get('project_id') or None
    invoice_id = request.form.get('invoice_id') or None
    if project_id:
        project = J.get_project(project_id, org_id)
        if not project:
            abort(404)
        customer_id = project['customer_id']
    if invoice_id:
        header, _ = get_org_invoice(invoice_id, org_id)
        if not header:
            abort(404)
        customer_id = header['customer_id']
        project_id = project_id or J.project_of(invoice_id, org_id)
    if not customer_id or not get_org_customer(customer_id, org_id)[0]:
        flash('Customer not found', 'error')
        return redirect(back)
    uploads = [f for f in request.files.getlist('file') if f and f.filename]    # one, or several dropped at once
    if not uploads:
        flash('Choose a file to upload', 'error')
        return redirect(back)
    filled, saved = [], []
    for upload in uploads:
        try:
            result = J.add_attachment(org_id, customer_id, request.form, upload, _user_id(), project_id=project_id,
                                      invoice_id=invoice_id)
        except J.UploadError as e:
            flash(f'{upload.filename}: {e}' if len(uploads) > 1 else str(e), 'error')
            continue
        except DatabaseError:
            logger.exception("Upload failed")
            flash(f'Could not save {upload.filename}', 'error')
            continue
        saved.append(upload.filename)
        filled += result['filled']
        kind = request.form.get('kind') if request.form.get('kind') in J.DOCUMENT_KINDS else J.guess_kind(upload.filename)
        activity.record('file_uploaded', f"{J.DOCUMENT_KINDS.get(kind, 'File')} uploaded: {upload.filename}"
                        + (f" (No. {request.form.get('reference_no')})" if request.form.get('reference_no') else ''),
                        project_id=project_id, link=url_for('projects_bp.view_project', project_id=project_id) if project_id else None)
    if saved:
        message = 'File uploaded' if len(saved) == 1 else f'{len(saved)} files uploaded'
        if filled:
            message += f". PO number filled in on {', '.join(filled)}"
        flash(message, 'success')
    return redirect(back)


@projects_bp.route('/files/<attachment_id>')
@require_org
def download_file(attachment_id):
    doc = J.get_attachment(attachment_id, g.current_org_id)
    if not doc or not permissions.file_kind_allowed(doc.get('kind')):
        abort(404)
    inline = doc['content_type'] in J.INLINE_TYPES and request.args.get('download') != '1'
    response = send_file(io.BytesIO(doc['data']), mimetype=doc['content_type'], as_attachment=not inline,
                         download_name=doc['file_name'], max_age=0)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@projects_bp.route('/files/<attachment_id>/link', methods=['POST'])
@require_org
def link_file(attachment_id):
    back = safe_referrer('projects_bp.list_projects')
    if not J.get_attachment(attachment_id, g.current_org_id):
        abort(404)
    try:
        db.execute_proc('sp_link_attachment', (attachment_id, g.current_org_id,
                                                      request.form.get('project_id') or None), fetch=False)
    except DatabaseError:
        flash('Could not move the file', 'error')
    else:
        flash('File moved' if request.form.get('project_id') else 'File removed from the project (still on the customer)',
              'success')
    return redirect(back)


@projects_bp.route('/files/<attachment_id>/delete', methods=['POST'])
@require_org
def delete_file(attachment_id):
    back = safe_referrer('projects_bp.list_projects')
    doc = J.get_attachment(attachment_id, g.current_org_id)
    if not doc:
        abort(404)
    try:
        db.execute_proc('sp_delete_attachment', (attachment_id, g.current_org_id), fetch=False)
    except DatabaseError:
        flash('Could not delete the file', 'error')
    else:
        flash(f'Deleted {doc["file_name"]}', 'success')
    return redirect(back)
