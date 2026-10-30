"""
A document's page for the React app (GET /api/document/<id>, frontend/src/islands/document/DocumentPage.tsx): its
state and what to do next (document_view), its payments or advances and the forms to record them, the document itself
and its versions (the same HTML the server pages and the customer portal draw, from invoices/_document.html and
_versions.html), and beside it the project's documents, who gets it, what happened, converting it, its project and
its files. The forms still post to the document routes in blueprints/invoices_bp.py, which come back to the page.
"""

from datetime import date
from typing import Callable, Dict

from flask import render_template_string

METHODS = ('Bank transfer', 'NEFT / RTGS', 'SWIFT (foreign remittance)', 'UPI', 'Card', 'Cheque', 'Cash', 'Other')
LISTS = {'quote': ('quotes', 'Quotations'), 'proforma': ('proformas', 'Proformas')}


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


def _change(ctx: Dict, t, url: Callable) -> Dict:
    invoice = ctx['invoice']
    status = invoice.get('status') or 'draft'
    revise = None
    if t.key in ('quote', 'proforma'):
        revise = {'possible': ctx['can_revise'], 'number': ctx['revision_number'],
                  'note': None if ctx['can_revise'] else ('A newer revision replaced this one; revise the latest.' if status == 'revised'
                                                          else 'It was converted already.' if status == 'converted' else 'Not possible now.'),
                  'action': url('invoices_bp.revise', invoice_id=invoice['invoice_id']),
                  'templates': [{'id': str(x['template_id']), 'name': x.get('name') or 'Template', 'same': x['template_id'] == invoice.get('template_id')}
                                for x in ctx['revise_templates']],
                  'current_template': str(invoice.get('template_id') or '')}
    return {'number': _number(invoice), 'short': t.short.lower(), 'takes_payments': t.takes_payments, 'proforma': t.key == 'proforma',
            'sent_word': 'finalized' if t.sent_status == 'pending' else 'sent',
            'undo': 'Finalize' if t.sent_status == 'pending' else 'Mark as sent', 'again': 'finalize' if t.sent_status == 'pending' else 'send',
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
    project_url = url('projects_bp.view_project', project_id=project['project_id']) if project else None
    others = [d for d in ctx['project_docs'] if d['invoice_id'] != invoice['invoice_id'] and d.get('doc_type') in permissions.doc_types('read', perms)]
    return _plain({
        'invoice_id': invoice['invoice_id'], 'project_id': project['project_id'] if project else None,
        'number': _number(invoice), 'doc_type': t.key, 'status': status, 'currency': invoice.get('currency_code') or 'INR',
        'list': {'label': list_label, 'url': url('invoices_bp.list_invoices', doc_path=path)},
        'head': {'number': _number(invoice), 'kind': t.label, 'pill': ctx['doc_pill'],
                 'customer': {'name': customers.label(invoice), 'url': url('customers_bp.view_customer', customer_id=invoice['customer_id'])},
                 'project': {'label': projects.project_label(project), 'title': project['title'], 'url': project_url} if project else None},
        'next': ctx['doc_next'], 'money': ctx['doc_money'],
        'pdf': _pdf(ctx, t, status, can_edit, url, perms),
        'change': _change(ctx, t, url) if status != 'draft' and can_edit else None,
        'payments': _payments(ctx, t, status, can_edit and permissions.can('payments.write', perms=perms), url) if (t.takes_payments or t.takes_advances) and status != 'draft' else None,
        'versions_html': _html("{% include 'invoices/_versions.html' %}", ctx) if ctx['versions'] else None,
        'document_html': _html("{% include 'invoices/_document.html' %}", {**ctx, 'sections_data': with_discount_column(ctx['sections_data'])}),
        'chain': ctx['doc_chain'],
        'people': {'list': ctx['doc_people'], 'url': project_url,
                   'empty': f"Nobody on this project gets {'quotations' if t.key == 'quote' else 'proformas and invoices'} yet. "
                            "Set who gets what on the project page."} if project else None,
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
                       'options': url('projects_bp.picker_options', customer_id=invoice['customer_id'], exact=1)} if can_edit else None},
        'files': [file_row(f, url) for f in ctx['files']],
        'upload': {'action': url('projects_bp.upload_file')} if can_edit else None,
    })
