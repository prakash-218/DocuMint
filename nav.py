"""
The app's frame: the sidebar's sections and links for this person's role, the header's "New" menu, and the single-page
app's boot data, which the React app (frontend/src/app/) draws from.

A link is active when its prefix is the longest one the current path starts with: /settings/audit-log lights Audit
log, not Settings. frontend/src/app/nav.ts does the same in the browser.

The app's screens are pages that call spa(): Flask still checks access for the address, then sends the app's one HTML
page, and the app's router draws the screen. Pages outside the app (signing in, registering, choosing an organization)
call public(); the customer portal calls portal(). PDFs and the error pages are still drawn on the server.
"""

from typing import Dict, List, Optional

from flask import get_flashed_messages, render_template, request, session, url_for

DOCUMENT_LINKS = (('quote', 'Quotations', 'file-pen-line', '/quotes'), ('proforma', 'Proformas', 'file-clock', '/proformas'),
                  ('invoices', 'Invoices', 'file-text', '/invoices'))


# Other addresses a link lights up for: a credit or debit note is listed inside Invoices
ALSO = {'invoices': ['/credit-notes', '/debit-notes']}


def _item(key, label, icon, href, prefix, badge=0) -> Dict:
    return {'key': key, 'label': label, 'icon': icon, 'href': href, 'prefix': prefix, 'badge': badge,
            **({'also': ALSO[key]} if key in ALSO else {})}


def sidebar(perms, unread: int = 0) -> List[Dict]:
    """[{title, items: [{key, label, icon, href, prefix, badge}]}]: the links someone with these permissions may open
    (permissions.granted(), or a built-in role's name), grouped as the prototype has them: Home and Projects, then Sales,
    People, Library and Organization. A group with nothing in it is left out."""
    import permissions
    perms = permissions.of(perms)

    def opens(endpoint, doc_type=None):
        return permissions.allows(endpoint, doc_type, perms)

    main, sales, purchases, people, library = [], [], [], [], []
    if opens('dashboard_bp.index'):
        main.append(_item('home', 'Home', 'house', url_for('dashboard_bp.index'), '/dashboard'))
    if opens('notifications_bp.index'):
        main.append(_item('notifications', 'Notifications', 'bell', url_for('notifications_bp.index'), '/notifications', unread))
    if opens('projects_bp.list_projects'):
        main.append(_item('projects', 'Projects', 'briefcase', url_for('projects_bp.list_projects'), '/projects'))
    for key, label, icon, prefix in DOCUMENT_LINKS:
        if opens('invoices_bp.list_invoices', 'invoice' if key == 'invoices' else key):
            sales.append(_item(key, label, icon, url_for('invoices_bp.list_invoices', type=None if key == 'invoices' else key), prefix))
    if opens('payments_bp.index'):
        sales.append(_item('payments', 'Payments', 'wallet', url_for('payments_bp.index'), '/payments'))
    if opens('invoices_bp.list_invoices', 'purchase_order'):
        purchases.append(_item('purchase_orders', 'Purchase orders', 'shopping-cart', url_for('invoices_bp.list_invoices', type='purchase_order'),
                               '/purchase-orders'))
    if opens('suppliers_bp.list_suppliers') and purchases:       # with purchase orders: Sales don't buy
        purchases.append(_item('suppliers', 'Suppliers', 'truck', url_for('suppliers_bp.list_suppliers'), '/suppliers'))
    if opens('customers_bp.list_customers'):
        people.append(_item('customers', 'Customers', 'users', url_for('customers_bp.list_customers'), '/customers'))
    if opens('emails_bp.inbox'):
        people.append(_item('emails', 'Emails', 'mail', url_for('emails_bp.inbox'), '/emails'))
    if opens('templates_bp.list_templates'):
        library.append(_item('templates', 'Templates', 'layout-template', url_for('templates_bp.list_templates'), '/templates'))
    if opens('costings_bp.rates'):
        library.append(_item('rates', 'Rates', 'list', url_for('costings_bp.rates'), '/costings/rates'))
    org = [_item('settings', 'Settings', 'settings', url_for('settings_bp.index'), '/settings')]
    if opens('settings_bp.audit_log'):
        org.append(_item('audit', 'Audit log', 'history', url_for('settings_bp.audit_log'), '/settings/audit-log'))
    groups = [(None, main), ('Sales', sales), ('Purchases', purchases), ('People', people), ('Library', library), ('Organization', org)]
    return [{'title': title, 'items': items} for title, items in groups if items]


def active(sections: List[Dict], path: str) -> Optional[str]:
    """The key of the link whose prefix is the longest one path starts with."""
    best, length = None, -1
    for section in sections:
        for item in section['items']:
            for prefix in (item['prefix'], *item.get('also', ())):
                if (path == prefix or path.startswith(prefix.rstrip('/') + '/')) and len(prefix) > length:
                    best, length = item['key'], len(prefix)
    return best


def new_menu(perms, with_project: bool = True) -> List[Dict]:
    """The header's "New" menu, for those who make invoices: each kind of document they may make, and a project."""
    import permissions
    from documents import get_type
    perms = permissions.of(perms)
    if not permissions.can('invoices.write', perms=perms):
        return []
    items = [{'label': get_type(k).label, 'icon': get_type(k).icon, 'href': url_for('invoices_bp.create_invoice', doc_type=k)}
             for k in ('quote', 'proforma', 'invoice', 'purchase_order') if permissions.can_doc('write', k, perms)]
    if with_project and permissions.can('projects.write', perms=perms):
        items.append({'label': 'Project', 'icon': 'briefcase', 'href': url_for('projects_bp.create_project'), 'divider': True})
    return items


def boot(role: Optional[str], unread: int, posted: Optional[Dict] = None) -> Dict:
    """What the React app starts with: who's signed in, the sidebar, the links it needs, and the page's messages.
    posted: a form that didn't save (spa(posted=...)), so its screen starts from what was typed."""
    import permissions
    from auth import get_current_membership
    perms = permissions.granted()
    orgs = session.get('user_organizations') or []
    membership = get_current_membership() or {}
    return {
        'me': {'email': session.get('email'), 'role': role,
               'role_label': permissions.role_label(role, membership.get('role_name')),
               'org': {'id': str(session.get('org_id') or ''), 'name': session.get('org_name') or ''},
               'permissions': sorted(perms), 'can': permissions.flags(perms)},
        'sidebar': sidebar(perms, unread),
        'orgs': [{'id': str(o.get('org_id')), 'name': o.get('name')} for o in orgs] if len(orgs) > 1 else [],
        'links': {'home': permissions.home(perms),
                  'logout': url_for('auth_bp.logout'), 'select_org': url_for('settings_bp.select_org'),
                  'search': url_for('search_bp.items'), 'new': new_menu(perms)},
        'flashes': [{'category': 'info' if c == 'message' else c, 'text': m} for c, m in get_flashed_messages(with_categories=True)],
        'posted': posted,
    }


def spa(title: str, skeleton: str = 'page', posted: bool = False):
    """The React app's page for this address: the frame drawn as it will look, with the screen's grey shapes in it until
    the app arrives and takes over. title and skeleton (list, page, home) are only for that first moment. posted: this
    answers a form that didn't save, so the screen starts from what was typed (boot's posted) and its message."""
    form = {'path': request.path, 'values': request.form.to_dict()} if posted else None
    return render_template('spa.html', title=title, skeleton=skeleton, path=request.path, posted=form)


def public(screen: str, title: str, **props):
    """A page outside the app: signing in, registering, choosing or making an organization, the portal's login. The
    sign-in frame and the page's messages come from templates/public.html; frontend/src/public/ draws the screen's form
    from props, which posts to the same route as before. Never pass a password in props."""
    return render_template('public.html', title=title, boot={'screen': screen, 'props': props})


def portal(title: str, skeleton: str = 'list'):
    """The customer portal's React app (frontend/src/portal/) for this address: its frame with the page's messages until
    the app takes over. skeleton (list, doc) is only for that first moment."""
    from auth import get_current_customer
    customer = get_current_customer() or {}
    boot = {'customer': {'name': customer.get('customer_name') or '', 'email': customer.get('email') or ''},
            'links': {'dashboard': url_for('customer_portal_bp.dashboard'), 'logout': url_for('customer_portal_bp.logout')},
            'flashes': [{'category': 'info' if c == 'message' else c, 'text': m} for c, m in get_flashed_messages(with_categories=True)]}
    return render_template('portal.html', title=title, skeleton=skeleton, boot=boot)

