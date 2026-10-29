"""
Invoices blueprint - CRUD operations for invoices
"""

import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, make_response
from db import db, DatabaseError
from auth import require_org, get_current_org_role, can_create_invoice, can_edit_invoice, can_delete_invoice, can_finalize_invoice
from access import get_org_invoice, get_org_template
from documents import CHOOSABLE, DOC_TYPES, TAX_MODES, get_type, invoice_kind, load_json
from document_service import (REVISABLE, DocumentError, apply_document_form, convert_document, customer_tax_hints,
                              form_defaults, get_org_profile, next_revision_number, preview_number, revise_document)
import uuid
from datetime import date, datetime
from layout import load_layout, packing_page, pages_for, template_is_export, types_by_template
import projects
import activity
import advances
import doc_urls
import revisions
from invoice_service import (get_template_fields, build_sections, invoice_summary, item_lines, recalculate_invoice,
                             render_invoice_pdf, PdfUnavailable)

logger = logging.getLogger(__name__)

invoices_bp = Blueprint('invoices_bp', __name__)
doc_urls.install(invoices_bp)


@invoices_bp.route('/')
@require_org
def list_invoices():
    """Quotations, proformas or invoices (the address says which): the React list in frontend/src/islands/documents/,
    fed by GET /api/documents/<doc_path>. ?status= opens a tab and ?q= a search, as links from elsewhere ask."""
    return render_template('invoices/lists.html', group=g.doc_path, tab=request.args.get('status') or 'all',
                           query=(request.args.get('q') or '').strip())


@invoices_bp.route('/create', methods=['GET', 'POST'])
@require_org
def create_invoice():
    """Create a new invoice"""
    current_role = get_current_org_role()
    if not can_create_invoice():
        flash(f'Your role is {current_role or "unknown"}. You need to be a Member or Owner to create invoices.', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))
    
    org_id = g.current_org_id

    doc_type = request.values.get('doc_type')
    if doc_type == 'export_invoice':      # old links: an export invoice is an invoice with an export template
        doc_type = 'invoice'
    if doc_type not in DOC_TYPES:
        doc_type = doc_urls.PATH_TYPES[g.doc_path]

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        template_id = request.form.get('template_id')

        if not customer_id or not template_id:
            flash('Customer and template are required', 'error')
            return redirect(url_for('invoices_bp.create_invoice', doc_type=doc_type))
        doc_type = invoice_kind(doc_type, template_is_export(template_id, org_id))
        project = projects.get_project(request.form.get('project_id'), org_id)
        if project and project['customer_id'] != customer_id:
            project = None
        if not project:                           # every document belongs to a project
            flash(f'Choose the project this {get_type(doc_type).label.lower()} is for', 'error')
            return redirect(url_for('invoices_bp.create_invoice', doc_type=doc_type))

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
                # Map field_display_name to label for template compatibility
                if 'field_display_name' in field and 'label' not in field:
                    field['label'] = field['field_display_name']
                # Map section_display_name to title for line item headers
                if 'section_display_name' in field and 'section_title' not in field:
                    field['section_title'] = field['section_display_name']
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'type': field.get('section_type', 'normal'),
                        'title': field.get('section_title') or field.get('section_display_name') or 'Untitled Section',
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


            _, profile = get_org_profile(org_id)
            try:
                apply_document_form(invoice_id, org_id, doc_type, request.form, profile,
                                    new=True, issue_date=issue_date or None)
            except DocumentError as e:
                db.execute_proc('sp_delete_invoice', (invoice_id,), fetch=False)
                flash(str(e), 'error')
                return redirect(url_for('invoices_bp.create_invoice', doc_type=doc_type, template_id=template_id))

            invoice_header, invoice_values = get_org_invoice(invoice_id, org_id)
            recalculate_invoice(invoice_id, invoice_header, invoice_values)
            if project:
                projects.set_project(invoice_id, org_id, project['project_id'])

            activity.document_event('document_created', invoice_header, 'created', project_id=project['project_id'] if project else None)
            flash(f'{get_type(doc_type).label} {invoice_header.get("doc_number") or ""} created', 'success')
            return redirect(_back(invoice_id))

        except DatabaseError as e:
            logger.exception("Failed to create %s", doc_type)
            flash(f'Error creating {get_type(doc_type).label.lower()}: {str(e)}', 'error')
            return redirect(url_for('invoices_bp.create_invoice', doc_type=doc_type))


    try:
        return _create_form(org_id, doc_type)
    except DatabaseError:
        logger.exception("Failed to load the create form")
        flash('Could not load the form', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))


# Template names that suit each document type, for the "Suggested" badge and ordering
def _latest_templates(org_id):
    return [t for t in db.execute_proc('sp_list_templates', (org_id, False)) or []
            if t.get('version') == t.get('latest_version')]


def _templates_for(org_id, templates, doc_type):
    """(the templates for doc_type, the others): what each template is used for, from its settings.
    An export invoice is an invoice made with an export template. With none for the type, all are offered."""
    kind = 'invoice' if doc_type == 'export_invoice' else doc_type
    types = types_by_template(org_id, templates)
    mine = [t for t in templates if kind in types[t['template_id']]]
    return (mine, [t for t in templates if t not in mine]) if mine else (templates, [])


def _editor_sections(fields):
    """{section_id: {title, type, fields}} in template order, for the document editor."""
    sections = {}
    for f in fields:
        f['label'] = f.get('field_display_name') or f.get('field_name')
        sections.setdefault(f['section_id'], {
            'title': f.get('section_display_name') or f.get('section_name') or 'Items',
            'type': f.get('section_type') or 'normal',
            'fields': [],
        })['fields'].append(f)
    return sections


def _create_form(org_id, doc_type):
    """GET /<type>/create: choose a project (quotes), then a template, then fill in the document."""
    project = projects.get_project(request.args.get('project_id'), org_id)
    customers = db.execute_proc('sp_list_customers', (org_id, False)) or []
    if not project:
        return render_template('invoices/create.html', step='project', doc_type=get_type(doc_type), project=None,
                               has_open_projects=bool(projects.list_projects(org_id, None, 'open')), customers=customers)

    templates = sorted(_latest_templates(org_id), key=lambda t: (t.get('name') or '').lower())
    template_id = request.args.get('template_id')
    selected = next((t for t in templates if t['template_id'] == template_id), None)
    if not selected:
        if template_id:
            flash('Template not found', 'error')
        mine, others = _templates_for(org_id, templates, doc_type)
        return render_template('invoices/create.html', step='template', doc_type=get_type(doc_type),
                               doc_types={k: DOC_TYPES[k] for k in CHOOSABLE}, templates=mine, other_templates=others,
                               project=project)

    org, profile = get_org_profile(org_id)
    doc_type = invoice_kind(doc_type, template_is_export(template_id, org_id))
    doc = _document_form_context(doc_type, org, profile, customers, org_id=org_id,
                                 currency=selected.get('currency_code'))
    if project:
        details = doc['values'].get('details') or {}
        if doc_type == 'quote' and not details.get('subject'):
            details['subject'] = project['title']
        doc['values']['details'] = {**projects.po_details(projects.latest_purchase_order(org_id, project['project_id'])), **details}
        hint = doc['customer_hints'].get(project['customer_id'])
        if hint:
            doc['values']['tax_mode'] = hint
    return render_template('invoices/editor.html', doc=doc, project=project, customers=customers,
                           sections_data=_editor_sections(get_template_fields(template_id)),
                           selected_template_id=template_id, template_name=selected.get('name') or '',
                           today=date.today().isoformat())


@invoices_bp.route('/<invoice_id>/new')
@require_org
def view_invoice_new(invoice_id):
    """Where the new page was while it was opt-in."""
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<invoice_id>')
@require_org
def view_invoice(invoice_id):
    """A document: its state, what to do next and its money (document_view), the document, and beside it the project's
    documents, who gets it and what happened."""
    context = _view_context(invoice_id)
    if not isinstance(context, dict):
        return context
    import document_view
    from auth import SALES
    invoice, project, summary = context['invoice'], context['project'], context['summary']
    role = context['current_org_role']
    can = {'edit': can_edit_invoice(), 'sales': role == SALES}
    from payment_terms import usual_days
    context['doc_next'] = document_view.next_step(invoice, summary, context['advance_received'], context['open_advances'], can,
                                                  url_for, context['convert_defaults'], can_email=bool(project),
                                                  usual_days=usual_days(load_json(invoice.get('organization_profile'))))
    context['doc_steps'] = document_view.steps(invoice, summary, context['advance_received'])
    # As the prototype draws it: its state, the money, and beside it the project's documents, who gets it, what happened
    advance_received = context['advance_received']
    doc_pill = document_view.pill(invoice, summary, advance_received)
    people, events = [], []
    if project:
        import contacts
        people = contacts.for_project(g.current_org_id, project['project_id'])
        events = db.execute_proc('sp_list_project_events', (project['project_id'], g.current_org_id, 200)) or []
    if role == SALES:                                   # their files: not the POs, invoices and the like
        context['files'] = [f for f in context['files'] if f.get('kind') not in projects.NOT_QUOTATIONS]
    context.update(
        doc_pill=doc_pill,
        doc_money=document_view.money_strip(invoice, summary, context['payments'], advance_received),
        doc_chain=document_view.chain(context['project_docs'], invoice_id, url_for) if project else [],
        doc_people=[] if role == SALES and invoice.get('doc_type') != 'quote' else document_view.who_gets_it(invoice, people),
        doc_activity=document_view.activity(events, invoice_id, (invoice.get('customer_name'), invoice.get('customer_site'))))
    return render_template('invoices/new_view.html', **context)


def _back(invoice_id):
    """Where a form on a document page goes back to: the page."""
    return url_for('invoices_bp.view_invoice', invoice_id=invoice_id)


def _editor(invoice_id, from_id):
    """The editor for a document (one just made from from_id by converting or revising it, or the one being saved again)."""
    return url_for('invoices_bp.edit_invoice', invoice_id=invoice_id)


def _view_context(invoice_id):
    """What a document page shows, or a redirect when the document can't be shown."""
    invoice_header, invoice_values = get_org_invoice(invoice_id, g.current_org_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    try:
        sections_data = build_sections(invoice_header, invoice_values)
        payments = db.execute_proc('sp_get_invoice_payments', (invoice_id,)) or []
    except DatabaseError:
        logger.exception("Failed to load invoice %s", invoice_id)
        flash('Error loading invoice', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    source = None
    if invoice_header.get('source_invoice_id'):
        source, _ = get_org_invoice(invoice_header['source_invoice_id'], g.current_org_id)
    templates = [t for t in (db.execute_proc('sp_list_templates', (g.current_org_id, False)) or [])
                 if t.get('version') == t.get('latest_version')]
    # Template each conversion starts with: the export one when this document is for export
    export = invoice_header.get('doc_type') == 'export_invoice' or invoice_header.get('tax_mode') == 'lut'
    types = types_by_template(g.current_org_id, templates)
    convert_defaults = {}
    for target in get_type(invoice_header.get('doc_type')).converts_to:
        match = [t['template_id'] for t in templates if target in types[t['template_id']] and len(types[t['template_id']]) < 3]
        same_market = [tid for tid in match if template_is_export(tid, g.current_org_id) == export]
        convert_defaults[target] = (same_market or match or [invoice_header.get('template_id')])[0]
    # Revising can move to another template made for the same type ("Quotation" -> "Quotation with cost break-up")
    own_type = 'invoice' if invoice_header.get('doc_type') == 'export_invoice' else invoice_header.get('doc_type')
    revise_templates = sorted((t for t in templates if own_type in types[t['template_id']] or t['template_id'] == invoice_header.get('template_id')),
                              key=lambda t: (t['template_id'] != invoice_header.get('template_id'), (t.get('name') or '').lower()))

    doc_type = get_type(invoice_header.get('doc_type'))
    advances_in = advances.on_proforma(invoice_id) if doc_type.takes_advances else []
    open_advances = advances.open_for(invoice_header, g.current_org_id) \
        if doc_type.takes_payments and (invoice_header.get('status') or 'draft') in ('draft', 'pending') else []

    _, org_profile = get_org_profile(g.current_org_id)
    pages = pages_for(load_layout(invoice_header.get('template_id'), g.current_org_id), invoice_header.get('doc_type'))
    project = projects.get_project(projects.project_of(invoice_id, g.current_org_id), g.current_org_id)
    files = projects.list_attachments(g.current_org_id, project_id=project['project_id']) if project else \
        projects.list_attachments(g.current_org_id, invoice_id=invoice_id)
    return dict(convert_defaults=convert_defaults, revise_templates=revise_templates,
                can_revise=(invoice_header.get('status') or 'draft') in REVISABLE.get(invoice_header.get('doc_type'), ()),
                revision_number=next_revision_number(invoice_header)[0],
                reopen_blocker=reopen_blocker(invoice_header, payments),
                project=project,
                project_docs=revisions.collapse(projects.project_documents(project['project_id'], g.current_org_id))
                if project else [],
                files=files, file_kinds=projects.DOCUMENT_KINDS,
                extra_pages=[p for p in pages if not p['with_document']],
                has_packing=any(p['kind'] == 'packing' for p in pages),
                base_currency=org_profile.get('default_currency') or 'INR',
                has_seal=bool(org_profile.get('stamp')),
                today=date.today().isoformat(),
                **_versions(invoice_header, sections_data, g.current_org_id),
                invoice=invoice_header,
                sections_data=sections_data,
                payments=payments,
                summary=invoice_summary(invoice_header, sections_data, payments),
                advances=advances_in, advance_received=sum(float(a['amount'] or 0) for a in advances_in),
                open_advances=open_advances,
                source=source,
                templates=templates,
                current_org_role=get_current_org_role())


@invoices_bp.route('/<invoice_id>/pdf')
@require_org
def export_pdf(invoice_id):
    """Export invoice as PDF"""
    invoice_header, invoice_values = get_org_invoice(invoice_id, g.current_org_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    try:
        return render_invoice_pdf(invoice_header, invoice_values, request.args.get('copies', type=int),
                                  packing=request.args.get('packing') == '1', page_key=request.args.get('page'),
                                  seal=request.args.get('seal') != '0')
    except LookupError:
        flash('That page isn\'t part of this document\'s template', 'error')
    except PdfUnavailable:
        flash('PDF export is not available on this server', 'error')
    except Exception:
        logger.exception("PDF generation failed for invoice %s", invoice_id)
        flash('Error generating PDF', 'error')
    return redirect(_back(invoice_id))


@invoices_bp.route('/<invoice_id>/finalize', methods=['POST'])
@require_org
def finalize_invoice(invoice_id):
    """Finalize a draft: invoices become 'pending' (awaiting payment), quotes/proformas 'sent'."""
    if not can_finalize_invoice():
        flash('You need to be a Member or Owner to finalize documents.', 'error')
        return redirect(_back(invoice_id))

    invoice_header, _ = get_org_invoice(invoice_id, g.current_org_id)
    if not invoice_header:
        flash('Document not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    doc_type = get_type(invoice_header.get('doc_type'))
    if (invoice_header.get('status') or 'draft') != 'draft':
        flash(f'This {doc_type.short.lower()} is already {invoice_header.get("status")}.', 'error')
        return redirect(_back(invoice_id))

    try:
        db.execute_proc('sp_update_invoice_status', (invoice_id, doc_type.sent_status), fetch=False)
        db.execute_proc('sp_settle_invoice', (invoice_id,), fetch=False)       # advances may cover it already
    except DatabaseError:
        logger.exception("Failed to finalize %s", invoice_id)
        flash('Error finalizing document', 'error')
    else:
        activity.document_event('document_sent', invoice_header, 'marked as sent' if doc_type.sent_status == 'sent' else 'finalized')
        flash(f'{doc_type.label} finalized. The customer can now see it in their portal.', 'success')
    return redirect(_back(invoice_id))


QUOTE_OUTCOMES = {'accepted': 'marked as accepted', 'declined': 'marked as declined', 'sent': 'reopened'}


@invoices_bp.route('/<invoice_id>/status', methods=['POST'])
@require_org
def set_status(invoice_id):
    """Record a customer's answer to a quote."""
    if not can_edit_invoice():
        flash('You need to be a Member or Owner to update documents.', 'error')
        return redirect(_back(invoice_id))

    invoice_header, _ = get_org_invoice(invoice_id, g.current_org_id)
    status = request.form.get('status')
    if not invoice_header or invoice_header.get('doc_type') != 'quote' or status not in QUOTE_OUTCOMES:
        flash("That status change isn't allowed", 'error')
        return redirect(_back(invoice_id))
    if invoice_header.get('status') in ('draft', 'converted'):
        flash('Finalize the quote before recording an answer', 'error')
        return redirect(_back(invoice_id))

    db.execute_proc('sp_update_invoice_status', (invoice_id, status), fetch=False)
    if status in ('accepted', 'declined'):
        activity.document_event(f'quote_{status}', invoice_header, status)
    flash(f'Quote {QUOTE_OUTCOMES[status]}', 'success')
    return redirect(_back(invoice_id))


@invoices_bp.route('/<invoice_id>/convert', methods=['POST'])
@require_org
def convert(invoice_id):
    """Turn a quote into a proforma/invoice, or a proforma into an invoice."""
    if not can_create_invoice():
        flash('You need to be a Member or Owner to create documents.', 'error')
        return redirect(_back(invoice_id))

    org_id = g.current_org_id
    source, values = get_org_invoice(invoice_id, org_id)
    if not source:
        flash('Document not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    target = request.form.get('target')
    template_id = request.form.get('template_id') or None
    if template_id and not get_org_template(template_id, org_id):
        flash('Template not found', 'error')
        return redirect(_back(invoice_id))

    _, profile = get_org_profile(org_id)
    try:
        new_id = convert_document(source, values, target, org_id, profile, template_id)
    except DocumentError as e:
        flash(str(e), 'error')
        return redirect(_back(invoice_id))
    except DatabaseError:
        flash('Conversion failed. Nothing was changed.', 'error')
        return redirect(_back(invoice_id))

    _into_project(source, new_id, org_id)
    carried = 0.0
    if get_type(source.get('doc_type')).takes_advances:
        try:
            carried = advances.carry_over(org_id, invoice_id, new_id)
        except DatabaseError as e:
            flash(f"The proforma's advance stays on it: {e}", 'error')
    new_header, _ = get_org_invoice(new_id, org_id)
    if new_header:
        activity.document_event('document_converted', new_header, f'made from {source.get("doc_number") or "a draft"}')
    from money import format_money
    flash(f'Created {get_type(target).label.lower()} from {source.get("doc_number") or "this document"}'
          + (f', with its advance of {format_money(carried, source.get("currency_code"))}' if carried else '')
          + '. Check the details, then finalize it.', 'success')
    return redirect(_editor(new_id, invoice_id))


def _into_project(source, new_id, org_id):
    """Keep a converted / revised document in its source's project, and give it the project's PO number."""
    project_id = projects.follow_source(source, new_id, org_id)
    po = projects.latest_purchase_order(org_id, project_id) if project_id else None
    if po:
        projects.fill_purchase_order(org_id, project_id, po['reference_no'], str(po['doc_date']) if po.get('doc_date') else None)


@invoices_bp.route('/<invoice_id>/revise', methods=['POST'])
@require_org
def revise(invoice_id):
    """Start a new revision of a sent quotation or proforma (Q/029 -> Q/029R1), in its template or another one."""
    if not can_create_invoice():
        flash('You need to be a Member or Owner to revise documents.', 'error')
        return redirect(_back(invoice_id))

    source, values = get_org_invoice(invoice_id, g.current_org_id)
    if not source:
        flash('Document not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices', type='quote'))
    template_id = request.form.get('template_id') or None
    if template_id and not get_org_template(template_id, g.current_org_id):
        flash('Template not found', 'error')
        return redirect(_back(invoice_id))
    try:
        new_id = revise_document(source, values, g.current_org_id, template_id)
    except DocumentError as e:
        flash(str(e), 'error')
        return redirect(_back(invoice_id))
    except DatabaseError:
        flash('Could not create the revision. Nothing was changed.', 'error')
        return redirect(_back(invoice_id))

    _into_project(source, new_id, g.current_org_id)
    new_header, _ = get_org_invoice(new_id, g.current_org_id)
    if new_header:
        activity.document_event('quote_revised', new_header, 'started (revision)')
    moved = source.get('doc_type') == 'proforma' and bool(advances.on_proforma(new_id))
    flash(f"Revision {(new_header or {}).get('doc_number') or ''} created as a draft"
          f"{', with the advances received' if moved else ''}. Make your changes, then mark it as sent.", 'success')
    return redirect(_editor(new_id, invoice_id))


@invoices_bp.route('/<invoice_id>/packing', methods=['GET', 'POST'])
@require_org
def packing(invoice_id):
    """Box-by-box packing, for documents whose template has a packing page (editable after finalizing; it's logistics)."""
    from document_service import boxes_from_form, save_details
    from invoice_service import build_sections, item_lines, packing_summary

    header, values = get_org_invoice(invoice_id, g.current_org_id)
    if not header:
        flash('Document not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))
    pack_page = packing_page(load_layout(header.get('template_id'), g.current_org_id), header.get('doc_type'))
    if not pack_page:
        flash("This document's template has no packing list page. Add one under Templates → Pages & printing.", 'error')
        return redirect(_back(invoice_id))
    box_fields = pack_page['box_fields']
    if not can_edit_invoice():
        flash('You need to be a Member or Owner to edit packing.', 'error')
        return redirect(_back(invoice_id))

    sections = build_sections(header, values)
    lines = item_lines(sections)

    if request.method == 'POST':
        details = load_json(header.get('details'))
        boxes = boxes_from_form(request.form, lines, box_fields)
        details['boxes'] = boxes
        if boxes:
            details['packages'] = f"{len(boxes)} {'box' if len(boxes) == 1 else 'boxes'}"
        for key in ('packing_list_no', 'marks'):
            value = (request.form.get(key) or '').strip()
            if value:
                details[key] = value
            else:
                details.pop(key, None)
        try:
            save_details(header, g.current_org_id, details)
        except DatabaseError:
            logger.exception("Failed to save packing for %s", invoice_id)
            flash('Could not save the packing', 'error')
            return redirect(url_for('invoices_bp.packing', invoice_id=invoice_id))
        header, values = get_org_invoice(invoice_id, g.current_org_id)
        summary = packing_summary(header, build_sections(header, values), box_fields)
        if summary['unpacked'] or summary['over']:
            flash('Packing saved, but the quantities in boxes don\'t match the invoice yet (see below).', 'warning')
        else:
            flash(f"Packing saved: {summary['count']} {'box' if summary['count'] == 1 else 'boxes'}.", 'success')
        return redirect(url_for('invoices_bp.packing', invoice_id=invoice_id))

    details = load_json(header.get('details'))
    boxes = details.get('boxes') or [{'contents': []}]
    packed = [{c['ordinal']: c['qty'] for c in (b.get('contents') or [])} for b in boxes]
    return render_template('invoices/packing.html', invoice=header, lines=lines, boxes=boxes, packed=packed,
                           details=details, box_fields=box_fields, pack_page=pack_page,
                           summary=packing_summary(header, sections, box_fields))


def _version(header, sections) -> dict:
    return {'header': header, 'lines': item_lines(sections), 'details': load_json(header.get('details')),
            'total': header.get('total_amount')}


def _versions(header, sections, org_id) -> dict:
    """A revised quotation's or proforma's versions (oldest first), and what changed from the one before this."""
    if header.get('doc_type') not in revisions.REVISED_TYPES:
        return {'versions': [], 'changes': None, 'changed_from': None}
    docs = db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or []
    versions = revisions.chains(docs).get(header['invoice_id']) or []
    before = revisions.previous(versions, header['invoice_id'])
    changes = None
    if before:
        before_header, before_values = get_org_invoice(before['invoice_id'], org_id)
        if before_header:
            changes = revisions.compare(_version(before_header, build_sections(before_header, before_values)),
                                        _version(header, sections))
    return {'versions': versions, 'changes': changes, 'changed_from': before}


def _document_form_context(doc_type, org, profile, customers, header=None, org_id=None, currency=None):
    """Everything the shared 'document details' form block needs."""
    from money import SYMBOLS
    t = get_type(doc_type)
    if header:
        values = {
            'tax_mode': header.get('tax_mode') or 'none',
            'tax_rate': float(header.get('tax_rate') or 0),
            'advance_percent': header.get('advance_percent'),
            'advance_basis': header.get('advance_basis') or 'pre_tax',
            'details': load_json(header.get('details')),
        }
        number, suggested = header.get('doc_number') or '', ''
    else:
        values = form_defaults(doc_type, profile, org, export=(currency or 'INR') != 'INR')
        number = suggested = preview_number(org_id or org.get('org_id'), doc_type, profile)
    from documents import DETAIL_GROUPS
    groups = [(k, label) for k, label in DETAIL_GROUPS.items() if any(f.group == k for f in t.details)]
    return {
        'groups': groups,
        'export': (currency or (header or {}).get('currency_code') or 'INR') != 'INR',
        'type': t,
        'number': number,
        'suggested_number': suggested,
        'values': values,
        'tax_modes': TAX_MODES,
        'gst_enabled': bool(profile.get('gstin')),
        'default_rate': float(profile.get('default_gst_rate') or 18),
        'customer_hints': customer_tax_hints(doc_type, org, customers) if customers else {},
        'currency': (header.get('currency_code') if header else currency) or 'INR',
        'currencies': list(SYMBOLS),
    }


@invoices_bp.route('/<invoice_id>/edit', methods=['GET', 'POST'])
@require_org
def edit_invoice(invoice_id):
    """Edit invoice"""
    current_role = get_current_org_role()
    if not can_edit_invoice():
        flash(f'Your role is {current_role or "unknown"}. You need to be a Member or Owner to edit invoices.', 'error')
        return redirect(_back(invoice_id))
    
    org_id = g.current_org_id


    try:
        invoice_header, _ = get_org_invoice(invoice_id, org_id)

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))


        current_status = invoice_header.get('status') or 'draft'
        # A sent document is corrected in place (same number) only when asked for: ?correct=1
        correcting = current_status != 'draft' and request.values.get('correct') == '1'
        if current_status != 'draft' and not correcting:
            flash('This document has been sent. Use "Change" on its page to correct it or make a revision.', 'error')
            return redirect(_back(invoice_id))
        total_before = invoice_header.get('total_amount')
    except DatabaseError as e:
        flash('Error loading invoice', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))

    if request.method == 'POST':
        try:
            logger.debug(f"DEBUG EDIT -- POST request: Saving invoice {invoice_id}")
            logger.debug(f"DEBUG EDIT -- Total form keys received: {len(request.form.keys())}")
            logger.debug(f"DEBUG EDIT -- All form keys: {list(request.form.keys())}")


            issue_date = request.form.get('issue_date')
            due_date = request.form.get('due_date')
            if issue_date or due_date:
                db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date or None, due_date or None), fetch=False)


            template_id = invoice_header.get('template_id')
            fields = get_template_fields(template_id, invoice_header.get('template_version'))
            logger.debug(f"DEBUG EDIT -- Loaded {len(fields)} template fields")


            sections = {}
            for field in fields:
                # Map field_display_name to label for template compatibility
                if 'field_display_name' in field and 'label' not in field:
                    field['label'] = field['field_display_name']
                # Map section_display_name to title for line item headers
                if 'section_display_name' in field and 'section_title' not in field:
                    field['section_title'] = field['section_display_name']
                section_id = field['section_id']
                if section_id not in sections:
                    sections[section_id] = {
                        'type': field.get('section_type', 'normal'),
                        'title': field.get('section_title') or field.get('section_display_name') or 'Untitled Section',
                        'fields': []
                    }
                sections[section_id]['fields'].append(field)


            for section_id, section_data in sections.items():
                section_type = section_data['type']

                if section_type == 'line_item':
                    # First, delete all existing line item values for this section
                    # This ensures deleted rows are removed and prevents conflicts
                    field_ids = [f['field_id'] for f in section_data['fields']]
                    if field_ids:
                        # Format field_ids as comma-separated quoted values for the stored procedure
                        field_ids_str = ','.join([f"'{fid}'" for fid in field_ids])
                        db.execute_proc('sp_delete_invoice_values_by_fields', (invoice_id, field_ids_str), fetch=False)
                        logger.debug(f"DEBUG EDIT -- Deleted existing line item values for section {section_id}")

                    line_item_keys = [k for k in request.form.keys() if k.startswith(f'line_item_{section_id}_')]
                    logger.debug(f"DEBUG EDIT -- Section {section_id}: Found {len(line_item_keys)} line item form keys")


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
                                    logger.debug(f"DEBUG EDIT -- Section {section_id}: Row {row_num}, field {field_id} = '{request.form.get(key)}'")
                                except ValueError:
                                    logger.debug(f"DEBUG EDIT -- ERROR: Could not parse row number from key: {key}")

                    logger.debug(f"DEBUG EDIT -- Section {section_id}: Found {len(rows)} unique rows: {sorted(rows.keys())}")


                    for row_num, row_data in rows.items():
                        logger.debug(f"DEBUG EDIT -- Saving row {row_num} for section {section_id} with {len(row_data)} fields")
                        for field in section_data['fields']:
                            field_id = field['field_id']
                            data_type = field['data_type']

                            val_string = None
                            val_number = None
                            val_date = None
                            val_boolean = None

                            value = row_data.get(field_id)

                            # Save the value even if it's empty (to clear previous values)
                            if value is not None:
                                value_str = str(value).strip() if value else ''
                                if data_type == 'string':
                                    val_string = value_str if value_str else None
                                elif data_type == 'number':
                                    try:
                                        val_number = float(value_str) if value_str else None
                                    except ValueError:
                                        val_number = None
                                elif data_type == 'date':
                                    val_date = value_str if value_str else None
                                elif data_type == 'boolean':
                                    val_boolean = 1 if value_str.lower() in ('true', '1', 'on', 'yes') else (0 if value_str else None)
                                
                                logger.debug(f"DEBUG EDIT -- Saving field {field_id} (row {row_num}): string={val_string}, number={val_number}, date={val_date}, boolean={val_boolean}")
                                db.execute_proc('sp_save_invoice_value',
                                                (invoice_id, field_id, val_string, val_number, val_date, val_boolean, row_num),
                                                fetch=False)
                                logger.debug(f"DEBUG EDIT -- Saved field {field_id} for row {row_num}")
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


            _, profile = get_org_profile(org_id)
            try:
                apply_document_form(invoice_id, org_id, invoice_header.get('doc_type') or 'invoice',
                                    request.form, profile, new=False,
                                    current_number=invoice_header.get('doc_number'))
            except DocumentError as e:
                flash(str(e), 'error')
                return redirect(_editor(invoice_id, invoice_id))

            invoice_header, invoice_values = get_org_invoice(invoice_id, org_id)
            recalculate_invoice(invoice_id, invoice_header, invoice_values)

            if correcting:
                _corrected(invoice_header, total_before)
                flash(f'{invoice_header.get("doc_number") or "Document"} corrected. It keeps its number; download the PDF '
                      'again and send the corrected one.', 'success')
                return redirect(_back(invoice_id))
            flash(f'{get_type(invoice_header.get("doc_type")).label} updated', 'success')

            return redirect(_back(invoice_id))

        except DatabaseError as e:
            flash(f'Error updating invoice: {str(e)}', 'error')
            return redirect(_editor(invoice_id, invoice_id))


    try:
        logger.debug(f"DEBUG EDIT -- GET request: Loading edit form for invoice {invoice_id}")

        result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        invoice_values = []
        if result and isinstance(result, list):
            if len(result) >= 2:
                if isinstance(result[1], list):
                    invoice_values = result[1]
                else:
                    invoice_values = result[1:]

        logger.debug(f"DEBUG EDIT -- GET: Loaded {len(invoice_values)} invoice values from database")

        ordinals_found = {}
        for value in invoice_values:
            section_title = value.get('section_title', '')
            ordinal = value.get('value_ordinal', 0) or 0
            if section_title not in ordinals_found:
                ordinals_found[section_title] = set()
            ordinals_found[section_title].add(ordinal)
        for section_title, ords in ordinals_found.items():
            logger.debug(f"DEBUG EDIT -- GET: Section '{section_title}' has ordinals: {sorted(ords)}")


        template_id = invoice_header.get('template_id')
        fields = []
        sections_data = {}

        if template_id:
            fields = get_template_fields(template_id, invoice_header.get('template_version'))
            if fields:


                for field in fields:
                    # Map field_display_name to label for template compatibility
                    if 'field_display_name' in field and 'label' not in field:
                        field['label'] = field['field_display_name']
                    # Map section_display_name to title for line item headers
                    if 'section_display_name' in field and 'section_title' not in field:
                        field['section_title'] = field['section_display_name']
                    section_id = field.get('section_id')
                    if section_id:
                        if section_id not in sections_data:
                            sections_data[section_id] = {
                                'title': field.get('section_title', '') or field.get('section_display_name', '') or 'Untitled Section',
                                'type': field.get('section_type', 'normal') or 'normal',
                                'fields': []
                            }
                        sections_data[section_id]['fields'].append(field)


                value_map = {}
                logger.debug(f"DEBUG EDIT -- Total invoice_values received: {len(invoice_values)}")
                for value in invoice_values:
                    field_id = value.get('field_id')
                    ordinal = value.get('value_ordinal', 0) or 0
                    key = (field_id, ordinal)
                    value_map[key] = value
                    logger.debug(f"DEBUG EDIT -- Mapped value: field_id={field_id}, ordinal={ordinal}, section_title={value.get('section_title')}")

                logger.debug(f"DEBUG EDIT -- Total values in value_map: {len(value_map)}")


                for section_id, section_info in sections_data.items():
                    logger.debug(f"DEBUG EDIT -- Processing section: {section_id}, type={section_info.get('type')}, title={section_info.get('title')}")
                    if section_info['type'] == 'line_item':


                        section_ordinals = set()
                        section_title = section_info.get('title', '')


                        section_field_ids = {field['field_id'] for field in section_info['fields']}
                        logger.debug(f"DEBUG EDIT -- Section {section_id} has {len(section_field_ids)} fields: {list(section_field_ids)}")


                        for value in invoice_values:
                            value_field_id = value.get('field_id')
                            value_section_title = value.get('section_title', '')

                            if value_field_id in section_field_ids:
                                ordinal = value.get('value_ordinal', 0) or 0
                                section_ordinals.add(ordinal)
                                logger.debug(f"DEBUG EDIT -- Found value for section {section_id}: field_id={value_field_id}, ordinal={ordinal}, section_title={value_section_title}")


                        for field_id in section_field_ids:
                            for key, value in value_map.items():
                                if key[0] == field_id:
                                    section_ordinals.add(key[1])

                        logger.debug(f"DEBUG EDIT -- Section {section_id} collected ordinals: {sorted(section_ordinals)}")


                        for field in section_info['fields']:
                            field_id = field['field_id']
                            field['values'] = {}

                            for ordinal in sorted(section_ordinals):
                                key = (field_id, ordinal)
                                if key in value_map:
                                    field['values'][ordinal] = value_map[key]
                                    logger.debug(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) has value for ordinal {ordinal}")
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
                                    logger.debug(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) created empty value for ordinal {ordinal}")

                            logger.debug(f"DEBUG EDIT -- Field {field_id} ({field.get('label')}) now has {len(field.get('values', {}))} value entries")
                    else:

                        for field in section_info['fields']:
                            field_id = field['field_id']
                            key = (field_id, 0)
                            if key in value_map:
                                field['value'] = value_map[key]

        org, profile = get_org_profile(org_id)
        return render_template('invoices/editor.html',
                             invoice=invoice_header, correcting=correcting,
                             sections_data=sections_data,
                             template_name=invoice_header.get('template_name') or '',
                             project=projects.get_project(projects.project_of(invoice_id, org_id), org_id),
                             doc=_document_form_context(invoice_header.get('doc_type') or 'invoice', org, profile,
                                                        [], header=invoice_header))
    except DatabaseError as e:
        flash('Error loading form data', 'error')
    return redirect(_back(invoice_id))


def _corrected(header, total_before):
    """After a sent document is corrected: an invoice's paid / pending follows its new total; the audit log and
    the project's activity say what happened."""
    from money import format_money
    invoice_id = header['invoice_id']
    total_after = (get_org_invoice(invoice_id, g.current_org_id)[0] or header).get('total_amount')
    db.execute_proc('sp_settle_invoice', (invoice_id,), fetch=False)
    db.execute_proc('sp_log_document_change', (invoice_id, 'corrected', total_before, total_after,
                                                f"Corrected after it was sent, by {(g.get('current_user') or {}).get('email') or 'a user'}"),
                    fetch=False)
    changed = abs(float(total_before or 0) - float(total_after or 0)) > 0.004
    currency = header.get('currency_code') or 'INR'
    activity.document_event('document_corrected', header, 'corrected after sending' + (
        f" (total {format_money(total_before or 0, currency)} → {format_money(total_after or 0, currency)})" if changed else ''))


REOPENABLE = ('sent', 'accepted', 'declined', 'pending')


def reopen_blocker(header, payments) -> str:
    """Why a sent document can't go back to draft, or '' when it can."""
    status = header.get('status') or 'draft'
    label = get_type(header.get('doc_type')).short.lower()
    if status == 'draft':
        return 'It is a draft already.'
    if status == 'converted':
        return f'It was converted; the {"invoice" if header.get("doc_type") == "proforma" else "document"} made from it would lose its source.'
    if status == 'revised':
        return 'A newer revision replaced it.'
    if payments:
        return f'Payments are recorded on this {label}. Remove them first, or correct it instead.'
    if status not in REOPENABLE:
        return f"A {status} {label} can't go back to draft."
    return ''


@invoices_bp.route('/<invoice_id>/reopen', methods=['POST'])
@require_org
def reopen(invoice_id):
    """Undo "Mark as sent" / "Finalize": back to a draft (same number) to edit and send again."""
    back = redirect(_back(invoice_id))
    if not can_finalize_invoice():
        flash('You need to be a Member or Owner to change documents.', 'error')
        return back
    header, _ = get_org_invoice(invoice_id, g.current_org_id)
    if not header:
        flash('Document not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))
    blocker = reopen_blocker(header, db.execute_proc('sp_get_invoice_payments', (invoice_id,)) or [])
    if blocker:
        flash(f"Can't move it back to draft. {blocker}", 'error')
        return back
    try:
        db.execute_proc('sp_update_invoice_status', (invoice_id, 'draft'), fetch=False)
    except DatabaseError:
        logger.exception("Failed to reopen %s", invoice_id)
        flash('Could not move it back to draft', 'error')
        return back
    activity.document_event('document_reopened', header, 'moved back to draft')
    flash('Back to draft. Edit it, then send it again; it keeps its number.', 'success')
    return back


@invoices_bp.route('/<invoice_id>/delete', methods=['POST'])
@require_org
def delete_invoice(invoice_id):
    """Delete an invoice"""
    current_role = get_current_org_role()
    org_id = g.current_org_id
    invoice_header = None

    try:
        invoice_header, _ = get_org_invoice(invoice_id, org_id)

        if not invoice_header:
            flash('Invoice not found', 'error')
            return redirect(url_for('invoices_bp.list_invoices'))
        if not can_delete_invoice(invoice_header):
            flash(f'Your role is {current_role or "unknown"}. You need to be an Owner to delete invoices.', 'error')
            return redirect(_back(invoice_id))


        db.execute_proc('sp_delete_invoice', (invoice_id,), fetch=False)
        flash('Invoice deleted successfully', 'success')
    except DatabaseError as e:
        flash(f'Error deleting invoice: {str(e)}', 'error')

    return redirect(url_for('invoices_bp.list_invoices', type=(invoice_header or {}).get('doc_type')))


@invoices_bp.route('/<invoice_id>/payment', methods=['POST'])
@require_org
def add_payment(invoice_id):
    """Add payment to invoice"""
    current_role = get_current_org_role()
    if not can_edit_invoice():
        flash(f'Your role is {current_role or "unknown"}. You need to be a Member or Owner to add payments.', 'error')
        return redirect(_back(invoice_id))
    
    amount = request.form.get('amount')
    method = request.form.get('method')
    reference_number = request.form.get('reference_number')

    if not amount:
        flash('Amount is required', 'error')
        return redirect(_back(invoice_id))

    invoice_header, _ = get_org_invoice(invoice_id, g.current_org_id)
    if not invoice_header:
        flash('Invoice not found', 'error')
        return redirect(url_for('invoices_bp.list_invoices'))
    doc_type = get_type(invoice_header.get('doc_type'))
    if not (doc_type.takes_payments or doc_type.takes_advances):
        flash('Payments are recorded against invoices, and advances against proformas', 'error')
        return redirect(_back(invoice_id))
    if doc_type.takes_advances and (invoice_header.get('status') or 'draft') == 'draft':
        flash('Finalize the proforma before recording an advance on it', 'error')
        return redirect(_back(invoice_id))

    try:
        amount_value = float(amount)
    except ValueError:
        flash('Amount must be a number', 'error')
        return redirect(_back(invoice_id))

    # Foreign-currency invoices: what the bank actually credited in the home currency
    _, profile = get_org_profile(g.current_org_id)
    base_currency = profile.get('default_currency') or 'INR'
    received = None
    raw_received = (request.form.get('received_amount') or '').strip()
    if raw_received and (invoice_header.get('currency_code') or base_currency) != base_currency:
        try:
            received = float(raw_received)
        except ValueError:
            flash('Amount credited must be a number', 'error')
            return redirect(_back(invoice_id))
    payment_date = (request.form.get('payment_date') or '').strip() or None

    try:
        row = db.execute_proc_single('sp_record_payment', (invoice_id, amount_value, method, reference_number, None))
        if row and (payment_date or received is not None):
            db.execute_proc('sp_set_payment_details', (
                row['payment_id'], invoice_id, payment_date, received,
                base_currency if received is not None else None), fetch=False)
        from money import format_money
        activity.record('payment', f"{'Advance' if doc_type.takes_advances else 'Payment'} of "
                                   f"{format_money(amount_value, invoice_header.get('currency_code'))} on "
                                   f"{invoice_header.get('doc_number') or 'a ' + doc_type.short.lower()}",
                        project_id=invoice_header.get('project_id'), body=invoice_header.get('customer_name'),
                        link=url_for('invoices_bp.view_invoice', invoice_id=invoice_id))
        flash('Advance recorded' if doc_type.takes_advances else 'Payment recorded successfully', 'success')
    except DatabaseError as e:
        flash(f'Error recording payment: {str(e)}', 'error')

    return redirect(_back(invoice_id))


@invoices_bp.route('/<invoice_id>/advances', methods=['POST'])
@require_org
def apply_advances(invoice_id):
    """Apply advances received on the customer's proformas to this invoice."""
    back = redirect(_back(invoice_id))
    if not can_edit_invoice():
        flash('You need to be a Member or Owner to apply advances.', 'error')
        return back
    header, _ = get_org_invoice(invoice_id, g.current_org_id)
    if not header or not get_type(header.get('doc_type')).takes_payments:
        flash('Advances are applied to invoices', 'error')
        return back
    chosen = request.form.getlist('payment_id')
    if not chosen:
        flash('Choose the advance to apply', 'error')
        return back
    try:
        n = advances.apply(g.current_org_id, invoice_id, chosen)
        flash(f"{n} advance{'s' if n != 1 else ''} applied", 'success')
    except DatabaseError as e:
        flash(f'Could not apply the advance: {e}', 'error')
    return back


@invoices_bp.route('/<invoice_id>/advances/<payment_id>/remove', methods=['POST'])
@require_org
def remove_advance(invoice_id, payment_id):
    """Take an applied advance off this invoice; it goes back to its proforma."""
    back = redirect(_back(invoice_id))
    if not can_edit_invoice():
        flash('You need to be a Member or Owner to change advances.', 'error')
        return back
    try:
        db.execute_proc('sp_unapply_advance', (payment_id, invoice_id, g.current_org_id), fetch=False)
        flash('The advance is back on its proforma', 'success')
    except DatabaseError as e:
        flash(f'Could not take the advance off: {e}', 'error')
    return back

