"""
Projects blueprint - group a customer's quote, proforma and invoices, and keep
their documents (PO, drawings...) with them.
"""

import io
import logging
import re

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, send_file, url_for

from access import get_org_customer, get_org_invoice, safe_referrer
from auth import MAIL_READERS, can_delete_project, can_edit_invoice, get_current_org_role, quotations_only, require_org
from db import DatabaseError, db
from document_service import get_org_profile
import projects as J
import activity
import contacts
import costing
import revisions

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


def _need_editor(back):
    if can_edit_invoice():
        return None
    flash('You need to be a Member or Owner to change projects and files.', 'error')
    return redirect(back)


@projects_bp.route('/')
@require_org
def list_projects():
    org_id = g.current_org_id
    status = request.args.get('status', 'open')
    status = status if status in J.PROJECT_STATUSES or status == 'all' else 'open'
    customer_id = request.args.get('customer_id') or None
    fy = _fiscal_year(request.args.get('fy')) or ''
    query = (request.args.get('q') or '').strip()
    try:
        found = J.list_projects(org_id, customer_id, None)
        years = sorted({r['fiscal_year'] for r in found if r.get('fiscal_year')}, reverse=True)
        if fy:
            found = [r for r in found if r.get('fiscal_year') == fy]
        if query:
            found = J.search_projects(found, query)
        counts = {}
        for r in found:
            counts[r['status']] = counts.get(r['status'], 0) + 1
        rows = [r for r in found if status == 'all' or r['status'] == status]
        ungrouped = J.ungrouped_families(org_id)
        customers = db.execute_proc('sp_list_customers', (org_id, False)) or []
    except DatabaseError:
        logger.exception("Failed to list projects")
        flash('Could not load projects', 'error')
        rows, counts, ungrouped, customers, years = [], {}, 0, [], []
    from pagination import paginate
    page = paginate(rows)
    return render_template('projects/list.html', projects=page.items, page=page, status=status, counts=counts,
                           customers=customers, years=years, fy=fy, query=query,
                           customer_id=customer_id, ungrouped=ungrouped, statuses=J.PROJECT_STATUSES,
                           current_org_role=get_current_org_role())


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


@projects_bp.route('/group-linked', methods=['POST'])
@require_org
def group_linked():
    """Start projects for documents that are already linked (converted / revised) but not grouped."""
    back = url_for('projects_bp.list_projects')
    denied = _need_editor(back)
    if denied:
        return denied
    try:
        created = J.group_all(g.current_org_id, _user_id())
    except DatabaseError:
        logger.exception("Grouping linked documents failed")
        flash('Could not group the documents', 'error')
        return redirect(back)
    flash(f'Grouped linked documents into {created} new project{"" if created == 1 else "s"}.' if created
          else 'Everything linked is already in a project.', 'success')
    return redirect(back)


@projects_bp.route('/new', methods=['GET', 'POST'])
@require_org
def create_project():
    org_id = g.current_org_id
    back = url_for('projects_bp.list_projects')
    denied = _need_editor(back)
    if denied:
        return denied

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

    customers = db.execute_proc('sp_list_customers', (org_id, False)) or []
    return render_template('projects/create.html', customers=customers, customer_id=request.args.get('customer_id'),
                           years=J.recent_fiscal_years(org_id))


@projects_bp.route('/<project_id>')
@require_org
def view_project(project_id):
    org_id = g.current_org_id
    project = _project_or_404(project_id)
    docs = J.project_documents(project_id, org_id)
    all_files = J.list_attachments(org_id, project_id=project_id)
    other_files = [f for f in J.list_attachments(org_id, customer_id=project['customer_id']) if not f.get('project_id')]
    addable = J.unassigned_documents(org_id, project['customer_id'])
    events = db.execute_proc('sp_list_project_events', (project_id, org_id, 30)) or []
    sales = quotations_only()
    if sales:                       # Sales: the quotations, and nothing about proformas, invoices or payments
        docs, addable = [d for d in docs if d.get('doc_type') == 'quote'], [d for d in addable if d.get('doc_type') == 'quote']
        all_files, other_files = [[f for f in fs if f.get('kind') not in J.NOT_QUOTATIONS] for fs in (all_files, other_files)]
        events = [e for e in events if e.get('kind') in ('project_created', 'project_status', 'file_uploaded')
                  or '/quotes/' in (e.get('link') or '')]
    stages = [s for s in J.project_stages(revisions.collapse(docs), all_files) if not sales or s['key'] == 'quote']
    files = [f for f in all_files if f.get('kind') not in J.EARLIER_KINDS]       # earlier documents show in the stages
    reads_mail = get_current_org_role() in MAIL_READERS
    people = contacts.for_project(org_id, project_id)
    found = contacts.project_suggestions(org_id, project, people, get_org_profile(org_id)[1].get('phone') or '') \
        if reads_mail else {'people': [], 'phones': []}
    return render_template('projects/view.html', project=project, docs=docs, money=J.project_money(docs, all_files),
                           people=people, found=found, contact_gets=contacts.GETS, usually=contacts.USUALLY,
                           stages=stages, files=files, other_files=other_files, addable=addable,
                           statuses=J.PROJECT_STATUSES, kinds=J.DOCUMENT_KINDS, po=J.latest_purchase_order(org_id, project_id),
                           years=J.recent_fiscal_years(org_id),
                           events=events,
                           threads=db.execute_proc('sp_list_email_threads', (org_id, project_id, None, False, 50)) or []
                           if reads_mail else [],
                           costings=costing.list_for(org_id, project_id) if get_current_org_role() in ('owner', 'admin') else [],
                           current_org_role=get_current_org_role())


@projects_bp.route('/<project_id>/edit', methods=['POST'])
@require_org
def edit_project(project_id):
    project = _project_or_404(project_id)
    back = url_for('projects_bp.view_project', project_id=project_id)
    denied = _need_editor(back)
    if denied:
        return denied
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
                            project_id=project_id, link=back)
        flash('Project updated', 'success')
    return redirect(back)


@projects_bp.route('/<project_id>/people', methods=['POST'])
@require_org
def set_person(project_id):
    """What one of the customer's contacts gets on this project: everything, proformas and invoices, or nothing."""
    _project_or_404(project_id)
    back = url_for('projects_bp.view_project', project_id=project_id) + '#people'
    denied = _need_editor(back)
    if denied:
        return denied
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
    if not can_delete_project():
        flash('Only owners can delete projects', 'error')
        return redirect(url_for('projects_bp.view_project', project_id=project_id))
    try:
        db.execute_proc('sp_delete_project', (project_id, g.current_org_id), fetch=False)
    except DatabaseError:
        logger.exception("Failed to delete project %s", project_id)
        flash('Could not delete the project', 'error')
        return redirect(url_for('projects_bp.view_project', project_id=project_id))
    flash('Project deleted. Its documents and files are kept, just no longer grouped.', 'success')
    return redirect(url_for('projects_bp.list_projects'))


@projects_bp.route('/<project_id>/documents', methods=['POST'])
@require_org
def project_document(project_id):
    """Add (or remove) one of the customer's documents to this project."""
    org_id = g.current_org_id
    _project_or_404(project_id)
    back = url_for('projects_bp.view_project', project_id=project_id)
    denied = _need_editor(back)
    if denied:
        return denied
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
    denied = _need_editor(back)
    if denied:
        return denied
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
    denied = _need_editor(back)
    if denied:
        return denied
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
    try:
        result = J.add_attachment(org_id, customer_id, request.form, request.files.get('file'),
                                         _user_id(), project_id=project_id, invoice_id=invoice_id)
    except J.UploadError as e:
        flash(str(e), 'error')
        return redirect(back)
    except DatabaseError:
        logger.exception("Upload failed")
        flash('Could not save the file', 'error')
        return redirect(back)
    message = 'File uploaded'
    kind_label = J.DOCUMENT_KINDS.get(request.form.get('kind'), 'File')
    activity.record('file_uploaded', f"{kind_label} uploaded: {request.files['file'].filename}"
                    + (f" (No. {request.form.get('reference_no')})" if request.form.get('reference_no') else ''),
                    project_id=project_id, link=back if project_id else None)
    if result['filled']:
        message += f". PO number filled in on {', '.join(result['filled'])}"
    flash(message, 'success')
    return redirect(back)


@projects_bp.route('/files/<attachment_id>')
@require_org
def download_file(attachment_id):
    doc = J.get_attachment(attachment_id, g.current_org_id)
    if not doc or quotations_only() and doc.get('kind') in J.NOT_QUOTATIONS:
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
    denied = _need_editor(back)
    if denied:
        return denied
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
    denied = _need_editor(back)
    if denied:
        return denied
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
