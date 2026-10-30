"""
Who may do what. Every check asks for a permission, never for a role, so a custom role, or an API key limited to some
permissions, works everywhere the built-in roles do.

Permissions are <area>.<action>. Documents are permissioned by type: quotes, proformas and invoices (tax and export),
each with read, write (create, edit, send, revise, reopen) and delete (drafts). The built-in roles are sets of them:

    owner   everything
    admin   everything but the organization's name and address, and making or changing owners
    member  every document, payments, projects and files, reading customers and the mailbox, sending email
    sales   projects and their files, quotations and customers; nothing about money beyond what's quoted
    viewer  reads documents, projects, files, customers and templates, and changes nothing

ENDPOINTS says what each page and API endpoint needs, and auth.require_org checks it before the view runs (check()).
An endpoint missing from it is refused, so a new page stays closed until it's listed (tests/test_permissions.py checks
that every route is). Views still ask can() for what they show: a button for what you may do, and no more.
"""

from typing import Dict, FrozenSet, Iterable, Optional, Tuple, Union
from urllib.parse import urlparse

from flask import g, redirect, request, url_for

DOC_GROUPS = {'quote': 'quotes', 'proforma': 'proformas', 'invoice': 'invoices', 'export_invoice': 'invoices'}

# Every permission, with what it lets someone do: the words a custom role's editor shows
PERMISSIONS: Dict[str, str] = {
    'quotes.read': 'See quotations',
    'quotes.write': 'Make, edit and send quotations',
    'quotes.delete': 'Delete draft quotations',
    'proformas.read': 'See proforma invoices',
    'proformas.write': 'Make, edit and send proforma invoices',
    'proformas.delete': 'Delete draft proforma invoices',
    'invoices.read': 'See invoices, and what customers owe',
    'invoices.write': 'Make, edit and finalize invoices',
    'invoices.delete': 'Delete draft invoices',
    'documents.delete_sent': 'Delete documents that were sent',
    'payments.write': 'Record payments and apply advances',
    'projects.read': 'See projects',
    'projects.write': 'Make and change projects, their notes and people',
    'projects.delete': 'Take documents out of a project and delete it',
    'files.read': 'See and download files',
    'files.write': 'Add, change and remove files',
    'customers.read': 'See customers',
    'customers.write': 'Add and edit customers',
    'customers.manage': 'Archive and delete customers, and give them portal logins',
    'contacts.write': "Add and edit customers' contacts",
    'emails.read': "Read the company's mailboxes",
    'emails.send': 'Email documents and statements',
    'emails.sync': 'Sync the mailboxes now',
    'notifications.read': 'Get notified of what happens on projects',
    'costings.read': 'See costings and the rates list',
    'costings.write': 'Make and change costings and the rates list',
    'templates.read': 'See templates',
    'templates.write': 'Make and change templates',
    'business.write': 'Change the business profile: tax registrations, bank, numbering, letterhead',
    'organization.write': "Change the organization's name and address",
    'team.manage': 'Approve, change and deactivate members',
    'team.owners': 'Make or change owners',
    'audit.read': 'See the audit log',
}

_ALL = frozenset(PERMISSIONS)
_READ = frozenset({'quotes.read', 'proformas.read', 'invoices.read', 'projects.read', 'files.read', 'customers.read',
                   'templates.read'})
ROLES: Dict[str, FrozenSet[str]] = {
    'owner': _ALL,
    'admin': _ALL - {'organization.write', 'team.owners'},
    'member': _READ | {'quotes.write', 'proformas.write', 'invoices.write', 'payments.write', 'projects.write', 'files.write',
                       'contacts.write', 'emails.read', 'emails.send'},
    'sales': frozenset({'quotes.read', 'quotes.write', 'quotes.delete', 'projects.read', 'projects.write', 'projects.delete',
                        'files.read', 'files.write', 'customers.read', 'customers.write', 'contacts.write', 'emails.send'}),
    'viewer': _READ,
}
ROLE_LABELS = {'owner': 'Owner', 'admin': 'Admin', 'member': 'Member', 'sales': 'Sales (projects and quotations)',
               'viewer': 'Viewer'}

Perms = Union[str, None, Iterable[str]]
CURRENT = 'current person'      # perms=CURRENT (the default): the current person's, from the request


def of(role_or_perms: Perms) -> FrozenSet[str]:
    """A role's permissions (a built-in role's name), or the permissions themselves; CURRENT: the current person's."""
    if role_or_perms is CURRENT:
        return granted()
    if role_or_perms is None:
        return frozenset()
    if isinstance(role_or_perms, str):
        return ROLES.get(role_or_perms, frozenset())
    return frozenset(role_or_perms)


def granted() -> FrozenSet[str]:
    """The current person's permissions in the organization they're in (cached for the request)."""
    if 'permissions' not in g:
        from auth import get_current_org_role
        g.permissions = of(get_current_org_role())
    return g.permissions


def can(*names: str, perms: Perms = CURRENT) -> bool:
    """Whether they have every one of these permissions (perms: someone's, a built-in role's name, or CURRENT)."""
    have = of(perms)
    return all(n in have for n in names)


def doc_permission(action: str, doc_type: Optional[str]) -> str:
    return f"{DOC_GROUPS.get(doc_type or 'invoice', 'invoices')}.{action}"


def can_doc(action: str, doc_type: Optional[str], perms: Perms = CURRENT) -> bool:
    """read, write or delete a document of this type (quote, proforma, invoice, export_invoice)."""
    return can(doc_permission(action, doc_type), perms=perms)


def doc_types(action: str = 'read', perms: Perms = CURRENT) -> Tuple[str, ...]:
    """The document types they may read (or write, delete)."""
    return tuple(t for t in DOC_GROUPS if can_doc(action, t, perms))


def quotations_only(perms: Perms = CURRENT) -> bool:
    """Reads quotations but no other documents (as Sales does): money beyond what was quoted stays hidden."""
    return can_doc('read', 'quote', perms) and not can_doc('read', 'proforma', perms) and not can_doc('read', 'invoice', perms)


def flags(perms: Perms = CURRENT) -> Dict[str, bool]:
    """The app's shorthand for what they may do (its pages show buttons by these): edit projects and documents, add and
    edit customers, manage the organization, read the mailboxes, and quotations only."""
    return {'edit': can('projects.write', perms=perms), 'edit_customers': can('customers.write', perms=perms),
            'manage': can('team.manage', perms=perms), 'read_mail': can('emails.read', perms=perms),
            'quotations_only': quotations_only(perms)}


def may_delete(doc: Dict, perms: Perms = CURRENT) -> bool:
    """Delete this document: a draft with its type's delete permission, a sent one also with documents.delete_sent."""
    if not doc or not can_doc('delete', doc.get('doc_type'), perms):
        return False
    return (doc.get('status') or 'draft') == 'draft' or can('documents.delete_sent', perms=perms)


def file_kind_allowed(kind: Optional[str], perms: Perms = CURRENT) -> bool:
    """Files that are an earlier proforma or invoice of ours need that document type's read permission."""
    from projects import EARLIER_KINDS
    doc_type = EARLIER_KINDS.get(kind or '')
    return doc_type is None or can_doc('read', doc_type, perms)


# ---------------------------------------------------------------- What each endpoint needs

class Doc:
    """An endpoint about a document: needs read, write or delete on its type, which comes from the request (the
    document's id, or a create page's doc_type and address). target: a form field naming another type that's needed too
    (converting a quotation into an invoice needs invoices.write; with none named, an invoice's)."""

    def __init__(self, action: str, target: Optional[str] = None, also: Tuple[str, ...] = ()):
        self.action, self.target, self.also = action, target, also

    def needs(self, doc_type: Optional[str]) -> Tuple[str, ...]:
        names = [doc_permission(self.action, doc_type), *self.also]
        if self.target:
            names.append(doc_permission('write', request.form.get(self.target)))
        return tuple(names)


ANYONE = ()            # any member of the organization
Rule = Union[Tuple[str, ...], str, Doc]

ENDPOINTS: Dict[str, Rule] = {
    # The documents
    'invoices_bp.list_invoices': Doc('read'),
    'invoices_bp.create_invoice': Doc('write'),
    'invoices_bp.view_invoice': Doc('read'),
    'invoices_bp.view_invoice_new': Doc('read'),
    'invoices_bp.export_pdf': Doc('read'),
    'invoices_bp.finalize_invoice': Doc('write'),
    'invoices_bp.set_status': Doc('write'),
    'invoices_bp.convert': Doc('read', target='target'),
    'invoices_bp.revise': Doc('write'),
    'invoices_bp.packing': Doc('write', also=('invoices.write',)),   # packing lists are for invoices
    'invoices_bp.edit_invoice': Doc('write'),
    'invoices_bp.reopen': Doc('write'),
    'invoices_bp.delete_invoice': Doc('delete'),
    'invoices_bp.add_payment': Doc('read', also=('payments.write',)),
    'invoices_bp.apply_advances': Doc('read', also=('payments.write',)),
    'invoices_bp.remove_advance': Doc('read', also=('payments.write',)),
    # Home: what's owed and what's next
    'dashboard_bp.index': 'invoices.read',
    'dashboard_bp.index_new': 'invoices.read',
    # Projects and their files
    'projects_bp.picker_options': 'projects.read',
    'projects_bp.create_project': 'projects.write',
    'projects_bp.list_projects': 'projects.read',
    'projects_bp.board': 'projects.read',
    'projects_bp.view_project': 'projects.read',
    'projects_bp.view_project_new': 'projects.read',
    'projects_bp.edit_project': 'projects.write',
    'projects_bp.set_person': 'projects.write',
    'projects_bp.delete_project': 'projects.delete',
    'projects_bp.project_document': 'projects.write',
    'projects_bp.document_project': 'projects.write',
    'projects_bp.upload_file': 'files.write',
    'projects_bp.download_file': 'files.read',
    'projects_bp.link_file': 'files.write',
    'projects_bp.delete_file': 'files.write',
    # Customers
    'customers_bp.list_customers': 'customers.read',
    'customers_bp.create_customer': 'customers.write',
    'customers_bp.statement_pdf': ('customers.read', 'invoices.read'),
    'customers_bp.view_customer_new': 'customers.read',
    'customers_bp.view_customer': 'customers.read',
    'customers_bp.save_contact': 'contacts.write',
    'customers_bp.delete_contact': 'contacts.write',
    'customers_bp.ignore_contact': ('contacts.write', 'emails.read'),
    'customers_bp.create_portal_account': 'customers.manage',
    'customers_bp.edit_customer': 'customers.write',
    'customers_bp.delete_customer': 'customers.manage',
    'customers_bp.archive_customer': 'customers.manage',
    'customers_bp.unarchive_customer': 'customers.manage',
    # The mailboxes
    'emails_bp.inbox': 'emails.read',
    'emails_bp.thread': 'emails.read',
    'emails_bp.link_project': ('emails.read', 'projects.write'),
    'emails_bp.download': 'emails.read',
    'emails_bp.sync_now': 'emails.sync',
    'notifications_bp.index': 'notifications.read',
    'notifications_bp.open_notification': 'notifications.read',
    'notifications_bp.mark_all_read': 'notifications.read',
    # Costings: owners and admins
    'costings_bp.create': 'costings.write',
    'costings_bp.edit': 'costings.read',
    'costings_bp.preview': 'costings.read',
    'costings_bp.save': 'costings.write',
    'costings_bp.library': 'costings.read',
    'costings_bp.items': 'costings.read',
    'costings_bp.read_spreadsheet': 'costings.write',
    'costings_bp.rates': 'costings.read',               # saving the rates (POST) needs costings.write: checked in the view
    'costings_bp.delete': 'costings.write',
    # Templates
    'templates_bp.list_templates': 'templates.read',
    'templates_bp.create_template': 'templates.write',
    'templates_bp.view_template': 'templates.read',
    'templates_bp.edit_layout': 'templates.write',
    'templates_bp.create_template_version': 'templates.write',
    'templates_bp.edit_template': 'templates.write',
    'templates_bp.delete_section': 'templates.write',
    'templates_bp.delete_field': 'templates.write',
    'templates_bp.archive_template': 'templates.write',
    'templates_bp.unarchive_template': 'templates.write',
    # Settings
    'settings_bp.index': ANYONE,
    'settings_bp.edit_organization': 'organization.write',
    'settings_bp.approve_member': 'team.manage',
    'settings_bp.audit_log': 'audit.read',
    'settings_bp.business_profile': 'business.write',
    'settings_bp.starter_templates': 'templates.write',
    'search_bp.items': ANYONE,                          # finds only what they may open (search.palette_items)
    # The app's JSON (blueprints/api_bp.py)
    'api_bp.me': ANYONE,
    'api_bp.compose': 'emails.send',
    'api_bp.send_email': 'emails.send',
    'api_bp.home': 'invoices.read',
    'api_bp.document_page': Doc('read'),
    'api_bp.new_document': Doc('write'),
    'api_bp.edit_document': Doc('write'),
    'api_bp.packing': Doc('write', also=('invoices.write',)),
    'api_bp.documents': Doc('read'),
    'api_bp.list_projects': 'projects.read',
    'api_bp.project': 'projects.read',
    'api_bp.update_project': 'projects.write',
    'api_bp.add_note': 'projects.write',
    'api_bp.set_person': 'projects.write',
    'api_bp.save_person': 'contacts.write',
    'api_bp.ignore_person': ('contacts.write', 'emails.read'),
    'api_bp.customer': 'customers.read',
    'api_bp.statement_compose': ('emails.send', 'invoices.read'),
    'api_bp.send_statement': ('emails.send', 'invoices.read'),
    'api_bp.save_customer_contact': 'contacts.write',
    'api_bp.delete_customer_contact': 'contacts.write',
    'api_bp.update_file': 'files.write',
    'api_bp.customers': 'customers.read',
    'api_bp.new_customer': 'customers.write',
    'api_bp.customer_form': 'customers.write',
    'api_bp.new_project': 'projects.write',
    'api_bp.emails': 'emails.read',
    'api_bp.email_thread': 'emails.read',
    'api_bp.notifications': 'notifications.read',
    'api_bp.settings': ANYONE,
    'api_bp.organization': 'organization.write',
    'api_bp.audit_log': 'audit.read',
    'api_bp.business_profile': 'business.write',
    'api_bp.costing_rates': 'costings.read',
    'api_bp.costing': 'costings.read',
    'api_bp.templates': 'templates.read',
    'api_bp.new_template': 'templates.write',
    'api_bp.template': 'templates.read',
    'api_bp.template_layout': 'templates.write',
    'api_bp.template_fields': 'templates.write',
}

# Endpoints that need no organization (signing in, choosing one, the customer portal): require_org isn't on them
OUTSIDE = {'static', 'index', 'healthz', 'settings_bp.select_org', 'settings_bp.create_organization',
           'settings_bp.join_organization'}
OUTSIDE_BLUEPRINTS = {'auth_bp', 'customer_portal_bp'}
# Refused with a plain 403, as if there were nothing there: costs and margins, and the mailboxes
QUIET = {'costings_bp', 'emails_bp'}


def request_doc_type(endpoint: Optional[str] = None) -> Optional[str]:
    """The type of document a request is about: the one its id names (in the address or form), or for the document
    pages the type their address or form names (/quotes/create, doc_type=proforma, /api/documents/quotes)."""
    import doc_urls
    endpoint = endpoint or request.endpoint or ''
    args = request.view_args or {}
    invoice_id = args.get('invoice_id') or request.form.get('invoice_id')
    if invoice_id:
        return doc_urls.doc_type_of(invoice_id)
    if args.get('group'):
        return request.values.get('doc_type') or doc_urls.PATH_TYPES.get(args['group'], 'invoice')
    if endpoint.startswith('invoices_bp.'):
        return (request.values.get('doc_type') or request.values.get('type')
                or doc_urls.PATH_TYPES.get(getattr(g, 'doc_path', None), 'invoice'))
    return None


def needs(endpoint: Optional[str], doc_type: Optional[str] = None) -> Optional[Tuple[str, ...]]:
    """The permissions an endpoint needs (about a document of this type); None when it isn't listed (refused). A request
    about a document always needs reading its type: Sales adding a proforma to a project are refused."""
    rule = ENDPOINTS.get(endpoint or '')
    if rule is None:
        return None
    if isinstance(rule, Doc):
        return rule.needs(doc_type)
    names = (rule,) if isinstance(rule, str) else tuple(rule)
    return names + ((doc_permission('read', doc_type),) if doc_type else ())


def allows(endpoint: str, doc_type: Optional[str] = None, perms: Perms = CURRENT) -> bool:
    """Whether they may open this endpoint (for a document of this type): the sidebar and the search show only these."""
    rule = ENDPOINTS.get(endpoint)
    names = (doc_permission(rule.action, doc_type), *rule.also) if isinstance(rule, Doc) else needs(endpoint, doc_type)
    return names is not None and can(*names, perms=perms)


def home(perms: Perms = CURRENT) -> str:
    """Where they start: Home when they may see what's owed, else the projects, else the settings."""
    if can('invoices.read', perms=perms):
        return url_for('dashboard_bp.index')
    if can('projects.read', perms=perms):
        return url_for('projects_bp.list_projects')
    return url_for('settings_bp.index')


def check():
    """For auth.require_org, before the view: None when the request is allowed; otherwise the refusal (JSON for the
    app's API, a plain 403 for costings and the mailboxes, a message and their start page otherwise)."""
    from flask import abort, flash, jsonify
    from auth import wants_json
    names = needs(request.endpoint, request_doc_type())
    if names is not None and can(*names):
        return None
    if request.endpoint in ('dashboard_bp.index', 'dashboard_bp.index_new'):
        return redirect(home())                       # Home without the money: their start page, without a fuss
    if request.blueprint in QUIET:
        abort(403)
    missing = [PERMISSIONS.get(n, n) for n in (names or ()) if n not in granted()]
    message = f"Your role doesn't allow that ({missing[0][0].lower() + missing[0][1:]})." if missing else "That isn't open to your role."
    if wants_json():
        return jsonify(error=message), 403
    flash(message, 'error')
    back = request.referrer if request.method == 'POST' else None       # a refused form: back to its page
    return redirect(back if back and urlparse(back).netloc in ('', request.host) else home())
