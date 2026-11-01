"""
A document's page for the React app (GET /api/document/<id>, frontend/src/islands/document/DocumentPage.tsx): its
state and what to do next (document_view), its payments or advances and the forms to record them (an invoice's credit
and debit notes, a credit note's refunds), the document itself
and its versions (the same HTML the server pages and the customer portal draw, from invoices/_document.html and
_versions.html), and beside it the project's documents, who gets it, what happened, converting it, its project and
its files. The forms still post to the document routes in blueprints/invoices_bp.py, which come back to the page.
"""

from datetime import date
from typing import Callable, Dict

from flask import render_template_string

METHODS = ('Bank transfer', 'NEFT / RTGS', 'SWIFT (foreign remittance)', 'UPI', 'Card', 'Cheque', 'Cash', 'Other')
LISTS = {'quote': ('quotes', 'Quotations'), 'proforma': ('proformas', 'Proformas'), 'purchase_order': ('purchase-orders', 'Purchase orders')}


def _number(doc) -> str:
    from documents import display_number
    return display_number(doc or {})


def _html(template: str, context: Dict) -> str:
    # 'source' (the document this one came from) would clash with render_template_string's own argument
    return render_template_string(template, **{k: v for k, v in context.items() if k != 'source'})


def _payments(ctx: Dict, t, status: str, can_edit: bool, url: Callable) -> Dict:
    invoice, cur = ctx['invoice'], ctx['invoice'].get('currency_code') or 'INR'
    takes_advance = t.takes_advances and status in ('sent', 'converted')
    record = can_edit and ((t.takes_payments and status == 'pending') or takes_advance)
    rows = []
    for p in ctx['advances'] if t.takes_advances else ctx['payments']:
        amount = float(p.get('amount') or 0)
        received = float(p.get('received_amount') or 0)
        rows.append({
            'id': str(p.get('payment_id')), 'date': p.get('payment_date'), 'amount': amount,
            'label': f"Advance, against proforma {p['advance_number']}" if p.get('advance_number') else 'Advance' if t.takes_advances else 'Payment',
            'method': p.get('method'), 'reference': p.get('reference_number'),
            'credited': {'amount': received, 'currency': p.get('received_currency') or ctx['base_currency'],
                         'rate': f'{received / amount:.2f}' if amount else None} if received else None,
            'applied': ({'number': p.get('applied_number') or 'a draft invoice', 'url': url('invoices_bp.view_invoice', invoice_id=p['applied_to'])}
                        if p.get('applied') else None) if t.takes_advances else None,
            'take_off': {'action': url('invoices_bp.remove_advance', invoice_id=invoice['invoice_id'], payment_id=p['payment_id']),
                         'confirm': f"Take this advance off {_number(invoice)}? It goes back to {p['advance_number']}."}
            if p.get('advance_number') and can_edit else None})
    apply = None
    if can_edit and t.takes_payments and ctx['open_advances']:
        project = ctx['project']
        apply = {'action': url('invoices_bp.apply_advances', invoice_id=invoice['invoice_id']),
                 'note': f"Received on {invoice.get('customer_name')}'s proformas and not on an invoice yet.",
                 'button': f'Apply to {_number(invoice)}',
                 'rows': [{'payment_id': str(a['payment_id']), 'amount': float(a.get('amount') or 0), 'number': a.get('proforma_number'),
                           'date': a.get('payment_date'), 'reference': a.get('reference_number'),
                           'checked': bool(project and a.get('project_id') == project['project_id'])} for a in ctx['open_advances']]}
    form = None
    if record:
        summary, received = ctx['summary'], ctx['advance_received']
        if takes_advance:
            suggested = (float(summary['advance']['amount']) - received) if summary.get('advance') else (float(summary['total']) - received)
        else:
            suggested = float(summary.get('balance') or 0)
        form = {'action': url('invoices_bp.add_payment', invoice_id=invoice['invoice_id']), 'advance': takes_advance,
                'title': 'Record an advance' if takes_advance else 'Record a payment',
                'button': 'Record advance' if takes_advance else 'Record payment',
                'suggested': round(suggested, 2) if suggested > 0 else None, 'currency': cur, 'base_currency': ctx['base_currency'],
                'today': date.today().isoformat(), 'methods': METHODS}
    return {'title': 'Advances' if t.takes_advances else 'Payments', 'rows': rows, 'record': form, 'apply': apply,
            'record_label': ('Record the advance' if takes_advance else 'Record payment') if record else None,
            'empty': 'No advance received yet.' if t.takes_advances else 'No payments recorded yet.'}


def _receiving(ctx: Dict, status: str, can_edit: bool, url: Callable) -> Dict:
    """What's arrived on a purchase order (receiving.py): each line's ordered, received and still to come; each delivery
    (taken off by those who may edit it); and, while something's to come, the form to record the next."""
    from datetime import date
    invoice_id = ctx['invoice']['invoice_id']
    done = ctx.get('po_progress') or {'lines': [], 'state': 'none', 'arrived': 0}
    by_line = {l['line']: l for l in done['lines']}
    deliveries = [{'id': str(r['receipt_id']), 'date': r.get('received_on'), 'challan': r.get('challan_no') or '', 'note': r.get('note') or '',
                   'by': r.get('created_by') or '',
                   'lines': [{'description': by_line.get(int(i['line']), {}).get('description') or f"Line {i['line']}", 'qty': float(i['qty']),
                              'unit': by_line.get(int(i['line']), {}).get('unit') or ''} for i in r.get('lines') or []],
                   'delete': url('invoices_bp.delete_receipt', invoice_id=invoice_id, receipt_id=r['receipt_id']) if can_edit else None}
                  for r in ctx.get('po_receipts') or []]
    open_ = can_edit and status in ('sent', 'confirmed') and any(l['left'] > 1e-9 for l in done['lines'])
    return {'lines': done['lines'], 'state': done['state'], 'deliveries': deliveries,
            'record': {'action': url('invoices_bp.add_receipt', invoice_id=invoice_id), 'today': date.today().isoformat()} if open_ else None}


def _notes(ctx: Dict, url: Callable) -> Dict:
    """An invoice's credit and debit notes, every status: each with its state and amount (a credit note's taken off)."""
    from document_view import pill
    from documents import get_type
    rows = []
    for n in ctx.get('notes') or []:
        kind = get_type(n.get('doc_type'))
        rows.append({'id': str(n['invoice_id']), 'number': _number(n) or 'Draft', 'kind': kind.label, 'date': n.get('issue_date'),
                     'pill': pill(n, {}), 'reason': n.get('reason') or '',
                     'amount': float(n.get('total_amount') or 0) * (-1 if kind.adjusts < 0 else 1),
                     'url': url('invoices_bp.view_invoice', invoice_id=n['invoice_id'])})
    return {'rows': rows}


def _refunds(ctx: Dict, status: str, can_record: bool, url: Callable) -> Dict:
    """A credit note's refunds, and what its invoice still owes back (credit notes and payments past its total); the form
    to record one while something's owed back."""
    from documents import credit_of
    invoice, source = ctx['invoice'], ctx.get('source') or {}
    owed = round(credit_of(source), 2) if source else 0.0
    rows = [{'id': str(r['refund_id']), 'date': r.get('refunded_on'), 'amount': float(r.get('amount') or 0),
             'reference': r.get('reference') or '', 'by': r.get('created_by') or '',
             'delete': url('invoices_bp.delete_refund', invoice_id=invoice['invoice_id'], refund_id=r['refund_id']) if can_record else None}
            for r in ctx.get('refunds') or []]
    return {'rows': rows, 'owed': owed, 'against': source.get('doc_number') or '', 'currency': invoice.get('currency_code') or 'INR',
            'record': {'action': url('invoices_bp.add_refund', invoice_id=invoice['invoice_id']), 'today': date.today().isoformat(),
                       'suggested': owed} if can_record and status == 'issued' and owed > 0.005 else None}


def _change(ctx: Dict, t, url: Callable) -> Dict:
    invoice = ctx['invoice']
    status = invoice.get('status') or 'draft'
    revise = None
    if t.key in ('quote', 'proforma'):
        revise = {'possible': ctx['can_revise'], 'number': ctx['revision_number'],
                  'note': None if ctx['can_revise'] else ('A newer revision replaced this one.' if status == 'revised'
                                                          else 'It was converted already.' if status == 'converted' else 'Not possible now.'),
                  'action': url('invoices_bp.revise', invoice_id=invoice['invoice_id']),
                  'templates': [{'id': str(x['template_id']), 'name': x.get('name') or 'Template', 'same': x['template_id'] == invoice.get('template_id')}
                                for x in ctx['revise_templates']],
                  'current_template': str(invoice.get('template_id') or '')}
    return {'number': _number(invoice), 'short': t.short.lower(),
            'correct': url('invoices_bp.edit_invoice', invoice_id=invoice['invoice_id'], correct=1), 'revise': revise,
            'reopen': {'blocker': ctx['reopen_blocker'] or None, 'action': url('invoices_bp.reopen', invoice_id=invoice['invoice_id'])}}


def _pdf(ctx: Dict, t, status: str, can_edit: bool, url: Callable, perms) -> Dict:
    import permissions
    invoice_id = ctx['invoice']['invoice_id']
    links = [{'label': 'All copies' if t.takes_payments else 'Download PDF', 'icon': 'file-down', 'href': url('invoices_bp.export_pdf', invoice_id=invoice_id)}]
    if t.takes_payments:
        links.append({'label': 'Original only', 'icon': 'file', 'href': url('invoices_bp.export_pdf', invoice_id=invoice_id, copies=1)})
    for page in ctx['extra_pages']:
        links.append({'label': page.get('title') or 'Extra page', 'icon': 'package' if page.get('kind') == 'packing' else 'file-plus',
                      'href': url('invoices_bp.export_pdf', invoice_id=invoice_id, page=page['key'])})
    return {'seal': ctx['has_seal'], 'links': links,
            'packing': url('invoices_bp.packing', invoice_id=invoice_id) if ctx['has_packing'] and can_edit and permissions.can('invoices.write', perms=perms) else None,
            'delete': url('invoices_bp.delete_invoice', invoice_id=invoice_id) if status == 'draft' and permissions.may_delete(ctx['invoice'], perms) else None}


def build(ctx: Dict, perms, url: Callable) -> Dict:
    """Everything the page shows, from the document page's context (invoices_bp._view_context and view_invoice's), for
    someone with these permissions (permissions.granted(), or a built-in role's name)."""
    import discounts
    import permissions
    from documents import get_type
    from invoice_service import with_discount_column
    from project_view import _plain, file_row
    import customers
    import projects
    invoice, project = ctx['invoice'], ctx['project']
    t = get_type(invoice.get('doc_type'))
    status = invoice.get('status') or 'draft'
    can_edit, sales = permissions.can_doc('write', invoice.get('doc_type'), perms), permissions.quotations_only(perms)
    path, list_label = LISTS.get(t.key, ('invoices', 'Invoices'))
    # a note's list is the Invoices list, on its tab
    list_url = (url('invoices_bp.list_invoices', doc_path=path, status=t.key) if t.adjusts
                else url('invoices_bp.list_invoices', doc_path=path))
    doc_next, doc_money = dict(ctx['doc_next']), ctx['doc_money']
    makes_notes = (t.takes_payments and status in ('pending', 'paid') and can_edit
                   and permissions.can('invoices.write', perms=perms) and not sales)
    if makes_notes:                                       # against a sent invoice: a credit or a debit note
        from document_view import _post
        doc_next['actions'] = [*(doc_next.get('actions') or []),
                               _post('Credit note', url('invoices_bp.make_note', invoice_id=invoice['invoice_id']), {'kind': 'credit'}),
                               _post('Debit note', url('invoices_bp.make_note', invoice_id=invoice['invoice_id']), {'kind': 'debit'})]
    if t.takes_payments and ctx.get('notes') and status != 'draft':
        from document_view import money_strip
        doc_money = money_strip(invoice, ctx['summary'], ctx['payments'], ctx['advance_received'], ctx['notes'])
    refunds = (_refunds(ctx, status, can_edit and permissions.can('payments.write', perms=perms), url)
               if t.key == 'credit_note' and status != 'draft' else None)
    if refunds and refunds['owed'] > 0.005:
        from money import format_money
        from document_view import _link
        doc_next['sub'] = f"{format_money(refunds['owed'], refunds['currency'], decimals=False)} to refund on {refunds['against']}."
        if refunds['record']:
            doc_next['actions'] = [_link('Record a refund', '#refunds', True),
                                   *[{**a, 'primary': False} for a in (doc_next.get('actions') or [])]]
    if not refunds or not (refunds['rows'] or refunds['owed'] > 0.005):
        refunds = None
    project_url = url('projects_bp.view_project', project_id=project['project_id']) if project else None
    others = [d for d in ctx['project_docs'] if d['invoice_id'] != invoice['invoice_id'] and d.get('doc_type') in permissions.doc_types('read', perms)]
    return _plain({
        'invoice_id': invoice['invoice_id'], 'project_id': project['project_id'] if project else None,
        'number': _number(invoice), 'doc_type': t.key, 'status': status, 'currency': invoice.get('currency_code') or 'INR',
        'list': {'label': list_label, 'url': list_url},
        'head': {'number': _number(invoice), 'kind': t.label, 'pill': ctx['doc_pill'],
                 'customer': {'name': customers.label(invoice), 'url': url('customers_bp.view_customer', customer_id=invoice['customer_id'])},
                 'project': {'label': projects.project_label(project), 'title': project['title'], 'url': project_url} if project else None},
        'next': doc_next, 'money': doc_money,
        'pdf': _pdf(ctx, t, status, can_edit, url, perms),
        # a draft opens in the editor; a sent one offers a revision or a correction (the "Revise" or "Edit" button)
        'edit': url('invoices_bp.edit_invoice', invoice_id=invoice['invoice_id']) if status == 'draft' and can_edit else None,
        # WhatsApp, a private link, the PDF or an email (sharing.py), once it's sent
        'share': url('api_bp.share', invoice_id=invoice['invoice_id']) if status != 'draft' and can_edit else None,
        'change': _change(ctx, t, url) if status != 'draft' and can_edit else None,
        'payments': _payments(ctx, t, status, can_edit and permissions.can('payments.write', perms=perms), url) if (t.takes_payments or t.takes_advances) and status != 'draft' else None,
        'receiving': _receiving(ctx, status, can_edit, url) if t.purchase and status != 'draft' else None,
        # an invoice's credit and debit notes; a credit note's refunds
        'notes': _notes(ctx, url) if t.takes_payments and ctx.get('notes') else None,
        'refunds': refunds,
        'versions_html': _html("{% include 'invoices/_versions.html' %}", ctx) if ctx['versions'] else None,
        'document_html': _html("{% include 'invoices/_document.html' %}", {**ctx, 'sections_data': with_discount_column(ctx['sections_data'])}),
        'chain': ctx['doc_chain'],
        'people': {'list': ctx['doc_people'], 'url': project_url,
                   'empty': (f"{invoice.get('customer_name') or 'The supplier'} has no contacts yet." if t.purchase else
                      f"Nobody on this project gets {'quotations' if t.key == 'quote' else 'proformas and invoices'} yet.")} if project or t.purchase else None,
        'activity': ctx['doc_activity'][:8],
        'convert': {'label': 'Convert again' if status == 'converted' else 'Convert, choosing the template',
                    'action': url('invoices_bp.convert', invoice_id=invoice['invoice_id']),
                    'targets': [{'key': k, 'label': get_type(k).short, 'template': str(ctx['convert_defaults'].get(k) or '')} for k in t.converts_to],
                    'templates': [{'id': str(x['template_id']), 'name': x.get('name') or 'Template'} for x in ctx['templates']],
                    # its discounts in words: converting asks whether to keep them or take them into the prices
                    'discount': discounts.describe(invoice, invoice.get('currency_code') or 'INR') or None}
        if can_edit and t.converts_to and status not in ('draft', 'declined', 'revised') and not sales else None,
        'project': {
            'project': {'title': project['title'], 'label': projects.project_label(project), 'fy': project.get('fiscal_year'),
                        'reference': project.get('reference'), 'url': project_url} if project else None,
            'others': [{'number': _number(d), 'url': url('invoices_bp.view_invoice', invoice_id=d['invoice_id']), 'kind': get_type(d.get('doc_type')).label,
                        'versions': len(d.get('versions') or []) + 1 if d.get('versions') else 0} for d in others],
            'change': {'action': url('projects_bp.document_project', invoice_id=invoice['invoice_id']),
                       'options': (url('projects_bp.picker_options', status='open') if t.purchase else
                                   url('projects_bp.picker_options', customer_id=invoice['customer_id'], exact=1))} if can_edit else None},
        'files': [file_row(f, url) for f in ctx['files']],
        'upload': {'action': url('projects_bp.upload_file')} if can_edit else None,
    })
