"""
Settings, for the React app (frontend/src/islands/settings/): the settings page (its links, requests to join, the team
and your organizations), the organization's name and address, the audit log and the business profile. Their forms
post to the settings_bp routes as before, which save them.
"""

from typing import Callable, Dict, List

AUDIT_FILTERS = [('', 'All'), ('invoice', 'Documents'), ('payment', 'Payments'), ('user_organization', 'Team'),
                 ('customer', 'Customers'), ('template', 'Templates')]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November',
          'December']


def index(user: Dict, org_id, org_name: str, perms, url: Callable) -> Dict:
    """perms: the person's permissions (permissions.granted(), or a built-in role's name): the links are the ones they
    may open, and the team is there for those who manage it."""
    import permissions
    import roles_view
    from db import db
    manage = permissions.can('team.manage', perms=perms)
    requests, members, invites = [], [], []
    if manage:
        invites = db.execute_proc('sp_list_invites', (org_id,)) or []
        requests = db.execute_proc('sp_get_pending_members', (org_id,)) or []
        members = [m for m in db.execute_proc('sp_get_org_members', (org_id,)) or [] if m.get('status') in ('active', 'deactivated')]
    # each with what it shows of theirs, if anything (the organization's name)
    links = [('Business profile', '', 'business.write', url('settings_bp.business_profile')),
             ('Name & address', org_name or '', 'organization.write', url('settings_bp.edit_organization', org_id=org_id)),
             ('Roles', '', 'team.manage', url('settings_bp.roles')),
             ('Templates', '', 'templates.write', url('templates_bp.list_templates')),
             ('Audit log', '', 'audit.read', url('settings_bp.audit_log')),
             ('Help', '', None, url('settings_bp.help'))]                  # how the app works, for everyone
    me = str(user['user_id'])
    return {
        'title': 'Settings',
        'links': [{'title': title, 'sub': sub, 'href': href} for title, sub, need, href in links if not need or permissions.can(need, perms=perms)],
        'team': url('settings_bp.approve_member'),
        'roles': roles_view.choices(org_id, perms) if manage else [],
        'requests': [{'user_id': str(r['user_id']), 'email': r.get('email') or '', 'asked': r.get('joined_at')} for r in requests],
        'members': [{'user_id': str(m['user_id']), 'email': m.get('email') or '',
                     'role': str(m['role_id']) if m.get('role') == 'custom' else m.get('role') or '',
                     'role_label': permissions.role_label(m.get('role'), m.get('role_name')),
                     'status': m.get('status') or '', 'you': str(m['user_id']) == me,
                     'manage': str(m['user_id']) != me and permissions.may_give(m, perms),
                     'reset': url('api_bp.member_reset', user_id=m['user_id'])
                     if str(m['user_id']) != me and m.get('status') == 'active' and permissions.may_give(m, perms) else None}
                    for m in members],
        # invites not used yet (invites.py): the team's way in, a Gmail address's too
        'invite': url('api_bp.invite_create') if manage else None,
        'invites': [{'id': str(i['invite_id']), 'email': i['email'], 'role_label': permissions.role_label(i.get('role'), i.get('role_name')),
                     'sent': i.get('created_at'), 'expires': i.get('expires_at'), 'expired': bool(i.get('expired')),
                     'by': i.get('invited_by') or '', 'again': url('api_bp.invite_again', invite_id=i['invite_id']),
                     'cancel': url('api_bp.invite_cancel', invite_id=i['invite_id'])} for i in invites],
        'orgs': [{'id': str(o['org_id']), 'name': o.get('name') or '', 'domain': o.get('domain') or '',
                  'role': permissions.role_label(o.get('role'), o.get('role_name')),
                  'current': str(o['org_id']) == str(org_id)} for o in db.execute_proc('sp_get_user_organizations', (user['user_id'],)) or []],
        'switch': url('settings_bp.select_org'),
    }


ORG_FIELDS = ('name', 'street_address', 'city', 'state', 'zip_code', 'country')


def organization(org: Dict, url: Callable) -> Dict:
    return {'title': 'Name & address', 'action': url('settings_bp.edit_organization', org_id=org['org_id']),
            'cancel': url('settings_bp.index'), 'domain': org.get('domain') or '',
            'values': {k: org.get(k) or '' for k in ORG_FIELDS}}


def audit(org_id, table: str, url: Callable) -> Dict:
    from app_helpers import describe_audit
    from db import db
    from pagination import Page
    count = db.execute_proc_single('sp_count_audit_log', (org_id, table or None)) or {}
    page = Page.from_count(count.get('n'), per_page=50)
    rows = db.execute_proc('sp_get_audit_log', (org_id, table or None, page.per_page, page.offset)) or []
    docs = {d['invoice_id']: d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or []}
    entries = []
    for log in rows:
        e = describe_audit(log, docs)
        entries.append({'icon': e['icon'], 'title': e['title'], 'detail': e.get('detail') or '', 'sub': e.get('sub') or '',
                        'url': url('invoices_bp.view_invoice', invoice_id=e['invoice_id']) if e.get('invoice_id') else None,
                        'at': log['changed_at'].strftime('%d %b %Y, %H:%M') if log.get('changed_at') else ''})
    return {'title': 'Audit log',
            'filters': [{'label': label, 'href': url('settings_bp.audit_log', table_name=key or None), 'active': (table or '') == key}
                        for key, label in AUDIT_FILTERS],
            'entries': entries, 'page': page.json('entries')}


def _fields(rows: List[Dict], with_value: bool) -> List[Dict]:
    return [{'key': f.get('key') or '', 'label': f.get('label') or '', 'print': bool(f.get('print')),
             **({'value': f.get('value') or ''} if with_value else {})} for f in rows]


def profile(org_id, url: Callable) -> Dict:
    """The business profile's form: what's saved now. It posts (with its images) to settings_bp.business_profile."""
    from blueprints.settings_bp import CURRENCIES, PROFILE_IMAGES, PROFILE_TEXT_FIELDS
    from document_service import get_org_profile, series_status
    org, p = get_org_profile(org_id)
    values = {k: p.get(k) or '' for k in PROFILE_TEXT_FIELDS}
    rate = p.get('default_gst_rate')
    values.update({
        'team_addresses': ', '.join(p.get('team_addresses') or []),
        'default_currency': p.get('default_currency') or 'INR',
        'default_gst_rate': '%g' % (rate or 18),
        'fy_start_month': str(p.get('fy_start_month') or 4),
        'advance_basis': 'total' if p.get('advance_basis') == 'total' else 'pre_tax',
        'payment_days': '' if p.get('payment_days') is None else str(p['payment_days']),
        'letterhead_style': 'left' if p.get('letterhead_style') == 'left' else 'centred',
        'letterhead_color': p.get('letterhead_color') or '#1f2fd1',
        'letterhead_accent': p.get('letterhead_accent') or p.get('letterhead_color') or '#1f2fd1',
    })
    address = ', '.join(x for x in (org.get(k) for k in ('street_address', 'city', 'state', 'zip_code', 'country')) if x)
    return {
        'title': 'Business profile',
        'org': {'name': org.get('name') or '', 'address': address or 'No address yet',
                'edit': url('settings_bp.edit_organization', org_id=org['org_id'])},
        'action': url('settings_bp.business_profile'),
        'values': values,
        'checks': {'separate_export_series': bool(p.get('separate_export_series')), 'logo_has_name': bool(p.get('logo_has_name'))},
        'currencies': list(CURRENCIES),
        'months': [[str(i), m] for i, m in enumerate(MONTHS, start=1)],
        'series': [{'key': s['key'], 'label': s['label'], 'format': s.get('format') or '', 'next': s.get('next'),
                    'shared': bool(s.get('shared')), 'preview': s.get('preview') or ''} for s in series_status(org_id, p)],
        'custom_fields': _fields(p.get('custom_fields') or [], True),
        'customer_fields': _fields(p.get('customer_fields') or [], False),
        'images': {name: p.get(name) or None for name in PROFILE_IMAGES},
        'starter': url('settings_bp.starter_templates'),
    }
