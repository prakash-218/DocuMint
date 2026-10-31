"""
The document editor for the React app (frontend/src/islands/editor/): GET /api/editor/new/<group> walks a new document
through its steps (the project it's for, then the template, then the editor), and GET /api/editor/<id> opens an
existing one (?correct=1 to correct a sent one). The editor posts the same form the server pages did to
invoices_bp.create_invoice and edit_invoice, which save it, so what's saved and checked is unchanged:
    line_item_<section>_<row>_field_<field>, field_<field>, detail_<key>, customer_id, doc_number, issue_date, due_date,
    currency, tax_mode, tax_rate, advance_percent, advance_basis, doc_type, suggested_number, template_id, project_id,
    correct; and the discounts (discounts.py): line_discount_<section>_<row> for a line, discount for the whole.
"""

from datetime import date
from typing import Callable, Dict, List, Optional


def _num(v) -> str:
    return ('%.4f' % float(v)).rstrip('0').rstrip('.') if v not in (None, '') else ''


def _value(f: Dict, v: Optional[Dict]):
    """A saved value as the form shows it (the old _items.html _value macro)."""
    if not v:
        return False if f.get('data_type') == 'boolean' else ''
    kind = f.get('data_type')
    if kind == 'number':
        return _num(v.get('val_number'))
    if kind == 'date':
        return str(v.get('val_date') or '')
    if kind == 'boolean':
        return bool(v.get('val_boolean'))
    return v.get('val_string') or ''


def sections_with_values(invoice_id: str, header: Dict) -> Dict:
    """{section_id: {title, type, fields}} for an existing document, each line item field with its values by row
    ({ordinal: value}) and each other field with its value (what edit_invoice's form used to be given)."""
    from db import db
    from invoice_service import get_template_fields
    result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
    values: List[Dict] = []
    if result and isinstance(result, list) and len(result) >= 2:
        values = result[1] if isinstance(result[1], list) else result[1:]
    by_key = {(v.get('field_id'), v.get('value_ordinal') or 0): v for v in values}
    sections: Dict = {}
    if not header.get('template_id'):
        return sections
    for f in get_template_fields(header['template_id'], header.get('template_version')) or []:
        f['label'] = f.get('field_display_name') or f.get('label') or f.get('field_name')
        if not f.get('section_id'):
            continue
        sections.setdefault(f['section_id'], {
            'title': f.get('section_display_name') or f.get('section_title') or 'Untitled Section',
            'type': f.get('section_type') or 'normal', 'fields': []})['fields'].append(f)
    for s in sections.values():
        if s['type'] == 'line_item':
            ids = {f['field_id'] for f in s['fields']}
            ordinals = sorted({o for (fid, o) in by_key if fid in ids})
            for f in s['fields']:
                f['values'] = {o: by_key.get((f['field_id'], o)) for o in ordinals}
        else:
            for f in s['fields']:
                f['value'] = by_key.get((f['field_id'], 0))
    return sections


def _sections(sections_data: Dict, line_discounts: Optional[Dict] = None) -> List[Dict]:
    """The template's sections for the editor: line item tables with their rows (each with its discount, as typed), the
    field a line's discount comes off (amount_field; None: its lines can't be discounted), and the other fields with
    values. line_discounts: discounts.of(header)['lines']."""
    import discounts
    from calculations import amount_field, normalize_name
    out = []
    for section_id, s in sections_data.items():
        first_string = next((f for f in s['fields'] if f.get('data_type') == 'string'), None)
        fields = [{'id': str(f['field_id']), 'name': f.get('field_name') or '', 'label': f.get('label') or f.get('field_name') or '',
                   'data_type': f.get('data_type') or 'string', 'formula': f.get('calculation_formula') or None,
                   'money': bool(f.get('is_currency')), 'required': bool(f.get('is_required')),
                   'long': f.get('data_type') == 'string' and ('desc' in (f.get('field_name') or '') or f is first_string)}
                  for f in s['fields']]
        entry = {'id': str(section_id), 'type': s['type'], 'title': s['title'], 'fields': fields,
                 'name': ((s['fields'][0].get('section_name') or '') if s['fields'] else '').lower()}
        if s['type'] == 'line_item':
            ordinals = sorted({o for f in s['fields'] for o in (f.get('values') or {})}) or [1]
            off = (line_discounts or {}).get(normalize_name(s['fields'][0].get('section_name')) if s['fields'] else '', {})
            picked = amount_field(s['fields'])
            entry['amount_field'] = str(picked) if picked else None
            entry['rows'] = [{'row': o, 'values': {str(f['field_id']): _value(f, (f.get('values') or {}).get(o))
                                                   for f in s['fields'] if not f.get('calculation_formula')},
                              'discount': discounts.text(off.get(o))} for o in ordinals]
        else:
            entry['values'] = {str(f['field_id']): _value(f, f.get('value')) for f in s['fields'] if not f.get('calculation_formula')}
        out.append(entry)
    return out


def _customers(rows: List[Dict]) -> List[Dict]:
    """The customer select's options, a company's sites under it (the old customer_options macro)."""
    import customers
    groups = []
    for g in customers.group(rows):
        c = g['customer']
        if g['sites']:
            groups.append({'label': c['name'], 'options': [{'id': str(c['customer_id']), 'label': c['name'] + (f" — {c['city']}" if c.get('city') else '')}]
                           + [{'id': str(s['customer_id']), 'label': (s.get('site') or s['name']) + (f" — {s['name']}" if s['name'] != c['name'] and s.get('site') else '')}
                              for s in g['sites']]})
        else:
            groups.append({'label': None, 'options': [{'id': str(c['customer_id']), 'label': customers.label(c)}]})
    return groups


def _project(project: Optional[Dict], url: Callable) -> Optional[Dict]:
    import projects
    if not project:
        return None
    return {'id': project['project_id'], 'label': projects.project_label(project), 'title': project['title'],
            'url': url('projects_bp.view_project', project_id=project['project_id']),
            'customer_id': str(project['customer_id']), 'customer_name': project.get('customer_name')}


def _editor(doc: Dict, sections_data: Dict, url: Callable, *, project: Optional[Dict], header: Optional[Dict] = None,
            correcting: bool = False, customers: Optional[List[Dict]] = None, template_id: str = '', template_name: str = '') -> Dict:
    import discounts
    t, v = doc['type'], doc['values']
    details = v.get('details') or {}
    editing = bool(header)
    found = discounts.of(header) if editing else {'document': None, 'lines': {}}
    from documents import display_number
    number = (display_number(header) if editing else None) or doc['number']
    verb = 'Correct ' if correcting else 'Edit '
    title = verb + (number or t.label) if editing else f'New {t.label.lower()}'
    groups = [{'key': key, 'label': label, 'fields': [f.key for f in t.details if f.group == key],
               'open': any(f.key in details for f in t.details if f.group == key) or (key == 'export' and doc['export'])}
              for key, label in doc['groups']]
    hidden = {'doc_type': t.key, 'suggested_number': doc['suggested_number']}
    if correcting:
        hidden['correct'] = '1'
    if not editing:
        hidden['template_id'] = template_id
    if project:
        hidden['project_id'] = project['project_id']
    if editing:
        customer = {'fixed': {'id': None, 'name': header.get('customer_name')}, 'groups': []}
    elif project and not t.purchase:
        customer = {'fixed': {'id': str(project['customer_id']), 'name': project.get('customer_name')}, 'groups': []}
    elif t.purchase:                            # a purchase order: one of the suppliers
        suppliers = [c for c in customers or [] if c.get('is_supplier')]
        customer = {'fixed': None, 'groups': _customers(suppliers),
                    'add': url('customers_bp.create_customer', kind='supplier') if not suppliers else None}
    else:
        customer = {'fixed': None, 'groups': _customers(customers or [])}
    customer['label'] = t.party
    if editing:
        cancel = url('invoices_bp.view_invoice', invoice_id=header['invoice_id'])
    elif project:
        cancel = url('projects_bp.view_project', project_id=project['project_id'])
    elif t.purchase:
        import doc_urls
        cancel = url('invoices_bp.list_invoices', doc_path=doc_urls.path_for(t.key))
    else:
        cancel = url('invoices_bp.list_invoices', type=t.key if t.key in ('quote', 'proforma') else None)
    rate = v.get('tax_rate') or doc['default_rate']
    return {
        'step': 'editor', 'title': title, 'correcting': correcting, 'editing': editing,
        'type': {'key': t.key, 'label': t.label, 'sent_word': 'finalized' if t.sent_status == 'pending' else 'sent',
                 'takes_payments': t.takes_payments, 'proforma': t.key == 'proforma', 'due_label': 'Valid until' if t.key == 'quote' else 'Deliver by' if t.purchase else 'Due date'},
        'project': _project(project, url), 'template_name': template_name,
        'change_template': None if editing else url('invoices_bp.create_invoice', doc_type=t.key, project_id=project['project_id'] if project else None),
        'action': url('invoices_bp.edit_invoice', invoice_id=header['invoice_id']) if editing else url('invoices_bp.create_invoice', doc_type=t.key),
        'cancel': cancel,
        'submit': 'Save the correction' if correcting else ('Save' if editing else 'Create'),
        'submit_side': 'Save changes' if editing else f'Create {t.label.lower()}',
        'hidden': hidden, 'customer': customer,
        'number': {'value': number or '', 'required': bool(doc['number'] and not doc['suggested_number'])},
        'issue_date': str((header.get('issue_date') if editing else date.today().isoformat()) or ''),
        'due_date': str((header.get('due_date') if editing else '') or ''),
        'sections': _sections(sections_data, found['lines']),
        'discount': discounts.text(found['document']),
        'details': {'fields': [{'key': f.key, 'label': f.label, 'kind': f.kind, 'placeholder': f.placeholder, 'group': f.group} for f in t.details],
                    'values': {k: str(val) for k, val in details.items() if val is not None}, 'groups': groups},
        'settings': {'currencies': doc['currencies'], 'currency': doc['currency'], 'tax_modes': [[k, label] for k, label in doc['tax_modes'].items()],
                     'tax_mode': v.get('tax_mode') or 'none', 'tax_rate': ('%g' % float(rate)) if rate is not None else '',
                     'advance_percent': ('%g' % float(v['advance_percent'])) if v.get('advance_percent') else '',
                     'advance_basis': 'total' if v.get('advance_basis') == 'total' else 'pre_tax'},
        'tax_hints': doc['customer_hints'],
        # a customer that can't be changed here (a draft's, or the project's): the tax it usually gets, and why
        'tax_hint': doc['customer_hints'].get(header['customer_id'] if editing else project['customer_id'])
        if editing or (project and not t.purchase) else None,
    }


NO_PROJECT = 'none'       # ?project_id=none: a purchase order for no project (the workshop, stock)


def new_page(org_id: str, doc_type: str, project_id: Optional[str], template_id: Optional[str], url: Callable,
             from_costing: Optional[Dict] = None) -> Dict:
    """A new document's step: the project it's for, then its template, then the editor. from_costing ({'id', 'lines':
    picks}): a purchase order of a costing's lines (costing.purchase_lines), the editor's rows filled with them."""
    from blueprints.invoices_bp import _document_form_context, _editor_sections, _latest_templates, _templates_for
    from db import db
    from document_service import get_org_profile
    from documents import CHOOSABLE, DOC_TYPES, get_type, invoice_kind
    from invoice_service import get_template_fields
    from layout import template_is_export
    import projects
    t = get_type(doc_type)
    no_project = t.purchase and project_id == NO_PROJECT          # a purchase for the workshop or stock
    project = projects.get_project(project_id, org_id) if project_id and not no_project else None
    customers = db.execute_proc('sp_list_customers', (org_id, False)) or []
    if not project and not no_project:
        return {'step': 'project', 'title': f'New {t.label.lower()}', 'type': {'key': t.key, 'label': t.label},
                'has_open_projects': bool(projects.list_projects(org_id, None, 'open')),
                'options': url('projects_bp.picker_options', status='open'),
                'open_url': url('invoices_bp.create_invoice', doc_type=t.key, project_id='__ID__'),
                'no_project': url('invoices_bp.create_invoice', doc_type=t.key, project_id=NO_PROJECT) if t.purchase else None,
                'new_project': {'action': url('projects_bp.create_project'), 'next': t.key, 'customers': _customers(customers),
                                'add_customer': url('customers_bp.create_customer') if not customers else None}}

    templates = sorted(_latest_templates(org_id), key=lambda x: (x.get('name') or '').lower())
    selected = next((x for x in templates if x['template_id'] == template_id), None)
    if not selected:
        mine, others = _templates_for(org_id, templates, doc_type)
        from layout import types_by_template
        if t.purchase and not any(t.key in kinds for kinds in types_by_template(org_id, templates).values()):
            # the first purchase order: its starter template, and no other starter comes back
            from document_service import create_starter_templates
            create_starter_templates(org_id, only=('Purchase Order',))
            templates = sorted(_latest_templates(org_id), key=lambda x: (x.get('name') or '').lower())
            mine, others = _templates_for(org_id, templates, doc_type)
        carry = {'from_costing': from_costing['id'], 'lines': ','.join(from_costing['lines'])} if from_costing else {}
        project_id = project['project_id'] if project else NO_PROJECT
        link = lambda x: {'name': x.get('name') or 'Template', 'currency': x.get('currency_code'),  # noqa: E731
                          'href': url('invoices_bp.create_invoice', doc_type=t.key, template_id=x['template_id'], project_id=project_id,
                                      **carry)}
        return {'step': 'template', 'title': f'New {t.label.lower()}', 'type': {'key': t.key, 'label': t.label},
                'missing': bool(template_id), 'project': _project(project, url),
                # with no project, only purchases: a sale is always for one
                'kinds': [{'key': k, 'short': DOC_TYPES[k].short, 'icon': DOC_TYPES[k].icon, 'current': k == t.key,
                           'href': url('invoices_bp.create_invoice', doc_type=k, project_id=project_id)}
                          for k in CHOOSABLE if project or DOC_TYPES[k].purchase],
                'templates': [link(x) for x in mine], 'others': [link(x) for x in others],
                'templates_page': url('templates_bp.list_templates')}

    org, profile = get_org_profile(org_id)
    kind = invoice_kind(doc_type, template_is_export(template_id, org_id))
    doc = _document_form_context(kind, org, profile, customers, org_id=org_id, currency=selected.get('currency_code'))
    details = doc['values'].get('details') or {}
    if kind == 'quote' and project and not details.get('subject'):
        details['subject'] = project['title']
    if t.purchase:                              # to a supplier: not the customer's PO, nor the customer's tax
        doc['values']['details'] = details
    else:
        doc['values']['details'] = {**projects.po_details(projects.latest_purchase_order(org_id, project['project_id'])), **details}
        hint = doc['customer_hints'].get(project['customer_id'])
        if hint:
            doc['values']['tax_mode'] = hint['mode']
    sections = _editor_sections(get_template_fields(template_id))
    if from_costing and t.purchase and project:
        _fill_lines(sections, _costing_lines(org_id, project, from_costing))
    return _editor(doc, sections, url, project=project, customers=customers,
                   template_id=template_id, template_name=selected.get('name') or '')


def _costing_lines(org_id, project: Dict, from_costing: Dict) -> List[Dict]:
    """The picked lines of one of the project's costings (costing.purchase_lines); none from another project's."""
    import costing
    row = costing.get(from_costing['id'], org_id)
    if not row or str(row.get('project_id')) != str(project['project_id']):
        return []
    return costing.purchase_lines(row, from_costing['lines'])


def _fill_lines(sections: Dict, lines: List[Dict]) -> None:
    """The first line items table's rows, from lines [{description, qty, unit, rate}], into the fields of those names
    (a price field takes the rate); fields worked out by formula are left to work out."""
    table = next((s for s in sections.values() if s['type'] == 'line_item'), None)
    if not table or not lines:
        return
    names = {'description': ('description', 'item', 'item_details', 'particulars', 'description_of_goods'), 'qty': ('qty', 'quantity'),
             'unit': ('unit', 'uom', 'per'), 'rate': ('rate', 'price', 'unit_price', 'rate_unit')}
    for f in table['fields']:
        if f.get('calculation_formula'):
            continue
        key = next((k for k, options in names.items() if (f.get('field_name') or '').lower() in options), None)
        if key:
            kind = 'val_number' if f.get('data_type') == 'number' else 'val_string'
            f['values'] = {n: {kind: line[key]} for n, line in enumerate(lines, start=1)}


def edit_page(org_id: str, header: Dict, correcting: bool, url: Callable) -> Dict:
    """An existing document in the editor (a draft, or a sent one being corrected)."""
    from blueprints.invoices_bp import _document_form_context
    from document_service import customer_tax_hints, get_org_profile
    import projects
    org, profile = get_org_profile(org_id)
    doc = _document_form_context(header.get('doc_type') or 'invoice', org, profile, [], header=header)
    doc['customer_hints'] = customer_tax_hints(header.get('doc_type') or 'invoice', org, [header])   # its customer's
    project = projects.get_project(projects.project_of(header['invoice_id'], org_id), org_id)
    return _editor(doc, sections_with_values(header['invoice_id'], header), url, project=project, header=header,
                   correcting=correcting, template_name=header.get('template_name') or '')
