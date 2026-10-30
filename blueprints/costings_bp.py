"""Costings: work out a quote's prices (cost + profit, or back from a total), then make the quote.
Costs and margins need costings.read (owners and admins): they never reach members, viewers or customers."""

import json
import logging

from flask import Blueprint, abort, flash, g, jsonify, redirect, request, url_for

import costing as K
import projects
from auth import require_org
from db import DatabaseError, db

logger = logging.getLogger(__name__)
costings_bp = Blueprint('costings_bp', __name__)


def _costing_or_404(costing_id):
    row = K.get(costing_id, g.current_org_id)
    if not row:
        abort(404)
    return row


def _sheet_from_request():
    try:
        return json.loads(request.form.get('sheet_json') or '{}')
    except ValueError:
        return {'items': []}


def _quote_templates(org_id, currency):
    """The org's templates, the likeliest first: a quotation, the export one when pricing in a foreign currency."""
    from document_service import get_org_profile
    export = currency != (get_org_profile(org_id)[1].get('default_currency') or 'INR')
    rows = [t for t in db.execute_proc('sp_list_templates', (org_id, False)) or []
            if t.get('version') == t.get('latest_version')]

    def rank(t):
        name = (t.get('name') or '').lower()
        return ('quot' not in name, ('export' in name) != export, 'break' in name, name)
    return sorted(rows, key=rank)


@costings_bp.route('/new', methods=['POST'])
@require_org
def create():
    org_id = g.current_org_id
    project = projects.get_project(request.form.get('project_id'), org_id)
    if not project:
        abort(404)
    source = K.get(request.form['copy_of'], org_id) if request.form.get('copy_of') else None
    if source and source['project_id'] != project['project_id']:
        source = None
    from document_service import get_org_profile
    currency = get_org_profile(org_id)[1].get('default_currency') or 'INR'
    try:
        row = K.create(org_id, project['project_id'], (source or {}).get('title') or project['title'],
                       g.current_user.get('user_id'), copy_of=source, currency=currency)
    except DatabaseError:
        logger.exception('Could not create a costing for project %s', project['project_id'])
        flash('Could not start the costing', 'error')
        return redirect(url_for('projects_bp.view_project', project_id=project['project_id']))
    if source:
        flash(f"Version {row['version']} started from version {source['version']}", 'success')
    return redirect(url_for('costings_bp.edit', costing_id=row['costing_id']))


@costings_bp.route('/<costing_id>')
@require_org
def edit(costing_id):
    """A costing in its editor, in the React app (costing_view.editor)."""
    row = _costing_or_404(costing_id)
    import nav
    return nav.spa(f"Costing v{row['version']} · {row.get('title') or ''}", 'page')


@costings_bp.route('/<costing_id>/preview', methods=['POST'])
@require_org
def preview(costing_id):
    """The worked-out numbers for the sheet being edited (nothing is saved)."""
    _costing_or_404(costing_id)
    sheet = K.clean_sheet(_sheet_from_request())
    sheet['cost_currency'] = _base_currency()
    return jsonify(K.run(sheet, K.settings_from(request.form)))


def _base_currency():
    from document_service import get_org_profile
    return get_org_profile(g.current_org_id)[1].get('default_currency') or 'INR'


def _save_from_form(row):
    return K.save(g.current_org_id, row['costing_id'], request.form.get('title') or row['title'],
                  _sheet_from_request(), K.settings_from(request.form), request.form.get('notes') or '',
                  cost_currency=_base_currency())


@costings_bp.route('/<costing_id>', methods=['POST'])
@require_org
def save(costing_id):
    """Save, and (with action=quote / update_quote) make or update the quote from it."""
    org_id = g.current_org_id
    row = _costing_or_404(costing_id)
    action = request.form.get('action') or 'save'
    back = redirect(url_for('costings_bp.edit', costing_id=costing_id))
    try:
        _save_from_form(row)
    except DatabaseError as e:
        logger.exception('Could not save costing %s', costing_id)
        flash(f'Could not save the costing: {e}', 'error')
        return back
    if action not in ('quote', 'update_quote'):
        flash('Costing saved', 'success')
        return back

    from document_service import DocumentError
    row = K.get(costing_id, org_id)
    try:
        if action == 'quote':
            if not request.form.get('template_id'):
                raise K.CostingError('Choose the template for the quote')
            quote_id = K.make_quote(org_id, row, request.form['template_id'])
            flash('Quote made from the costing. Check the terms, then finalize it.', 'success')
        else:
            quote_id = K.update_quote(org_id, row)
            flash("The quote's items and prices now match the costing", 'success')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=quote_id))
    except (K.CostingError, DocumentError) as e:
        flash(f'Costing saved, but the quote was not {"made" if action == "quote" else "updated"}: {e}', 'error')
    except DatabaseError as e:
        logger.exception('Could not %s for costing %s', action, costing_id)
        flash(f'Costing saved, but the quote was not {"made" if action == "quote" else "updated"}: {e}', 'error')
    return back


@costings_bp.route('/library')
@require_org
def library():
    """The org's costings, to pick one to copy items from (JSON for the editor's dialog)."""
    from projects import project_label
    rows = K.library(g.current_org_id, (request.args.get('q') or '')[:100])
    return jsonify([{'costing_id': r['costing_id'], 'title': r['title'], 'version': r['version'],
                     'project': project_label(r), 'project_title': r['project_title'], 'customer': r['customer_name'],
                     'items': r['item_count'], 'total': K.number(r['total_price'], 0), 'currency': r['currency'],
                     'updated': r['updated_at'].date().isoformat() if r.get('updated_at') else None} for r in rows])


@costings_bp.route('/<costing_id>/items')
@require_org
def items(costing_id):
    row = _costing_or_404(costing_id)
    return jsonify({'items': K.items_to_copy(row), 'cost_currency': row['sheet'].get('cost_currency') or 'INR'})


@costings_bp.route('/<costing_id>/import', methods=['POST'])
@require_org
def read_spreadsheet(costing_id):
    """A spreadsheet's sheets as grids, for the editor to turn into items or cost lines. Nothing is kept."""
    _costing_or_404(costing_id)
    import costing_import
    upload = request.files.get('file')
    if not upload or not upload.filename:
        return jsonify({'error': 'Choose a file'}), 400
    try:
        return jsonify(costing_import.read(upload.stream, upload.filename))
    except costing_import.SheetError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception('Could not read %s for costing %s', upload.filename, costing_id)
        return jsonify({'error': "That file couldn't be read. Save it again as .xlsx and try once more."}), 400


@costings_bp.route('/rates', methods=['GET', 'POST'])
@require_org
def rates():
    """The usual rates, offered as cost lines are typed (seeing them needs costings.read; saving them costings.write)."""
    import permissions
    org_id = g.current_org_id
    if request.method == 'POST':
        if not permissions.can('costings.write'):
            abort(403)
        try:
            raw = json.loads(request.form.get('rates_json') or '[]')
        except ValueError:
            raw = []
        try:
            saved = K.save_rates(org_id, raw)
            flash(f"Rates saved ({len(saved)})", 'success')
        except DatabaseError as e:
            logger.exception('Could not save the rates for %s', org_id)
            flash(f'Could not save the rates: {e}', 'error')
        return redirect(url_for('costings_bp.rates', back=request.args.get('back') or None))
    import nav
    return nav.spa('Rates list', 'page')                   # the list: costing_view.rates_page


@costings_bp.route('/<costing_id>/delete', methods=['POST'])
@require_org
def delete(costing_id):
    row = _costing_or_404(costing_id)
    db.execute_proc('sp_delete_costing', (costing_id, g.current_org_id), fetch=False)
    flash(f"Costing version {row['version']} deleted", 'success')
    return redirect(url_for('projects_bp.view_project', project_id=row['project_id']) + '#costings')
