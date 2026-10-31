"""
The organization's roles, for the React app (frontend/src/islands/settings/Roles.tsx): the built-in roles and the
organization's own, and the editor for one of its own (the permissions it grants, by area). Saving goes through the
JSON API (api_bp.create_role, update_role, delete_role).
"""

from collections import Counter
from typing import Callable, Dict, List, Optional

BUILT_IN = ('owner', 'admin', 'member', 'sales', 'viewer')


def catalog(perms) -> List[Dict]:
    """The permissions a custom role can grant, by area: what each lets someone do, what it needs, and whether the
    person editing may give it (only what they have themselves)."""
    import permissions as P
    have = P.of(perms)
    return [{'key': key, 'label': label,
             'permissions': [{'name': n, 'label': P.PERMISSIONS[n], 'needs': sorted(P.IMPLIES.get(n, ())), 'yours': n in have}
                             for n in P.PERMISSIONS if n.split('.')[0] == key and n in P.GRANTABLE]}
            for key, label in P.AREAS]


def _custom(row: Dict) -> Dict:
    return {'role': 'custom', 'role_permissions': row.get('permissions') or []}


def listing(org_id, perms, url: Callable) -> Dict:
    """The built-in roles (how many permissions, who has it) and the organization's own, each editable by someone whose
    permissions cover it."""
    import permissions as P
    from db import db
    members = db.execute_proc('sp_get_org_members', (org_id,)) or []
    counts = Counter(m.get('role') for m in members)
    own = db.execute_proc('sp_list_roles', (org_id,)) or []
    return {
        'title': 'Roles',
        'built_in': [{'key': r, 'name': P.ROLE_LABELS[r], 'members': counts.get(r, 0),
                      'permissions': len(P.ROLES[r]),
                      'copy': url('settings_bp.new_role', **{'from': r}) if r != 'owner' else None}
                     for r in BUILT_IN],
        'custom': [{'id': str(r['role_id']), 'name': r['name'], 'description': r.get('description') or '',
                    'members': int(r.get('members') or 0), 'permissions': len(P.of(_custom(r))),
                    'url': url('settings_bp.role', role_id=r['role_id']), 'editable': P.may_give(_custom(r), perms)}
                   for r in own],
        'new': url('settings_bp.new_role'),
        'back': url('settings_bp.index'),
    }


def editor(org_id, role_id: Optional[str], base: Optional[str], perms, url: Callable) -> Optional[Dict]:
    """A role of the organization's own to edit (None when it isn't theirs), or a new one: empty, or starting from a
    built-in role's permissions (base), as far as the person editing may give them."""
    import permissions as P
    from db import db
    if role_id:
        row = db.execute_proc_single('sp_get_role', (org_id, role_id))
        if not row:
            return None
        chosen = sorted(P.of(_custom(row)))
        role = {'id': str(row['role_id']), 'name': row['name'], 'description': row.get('description') or '',
                'permissions': chosen, 'members': int(row.get('members') or 0)}
        editable = P.may_give(chosen, perms)
    else:
        start = P.ROLES.get(base or '', frozenset()) & P.GRANTABLE & P.of(perms)
        role = {'id': None, 'name': f"{P.ROLE_LABELS[base].split(' (')[0]} (copy)" if start else '', 'description': '',
                'permissions': sorted(start), 'members': 0}
        editable = True
    return {
        'title': role['name'] if role_id else 'New role',
        'role': role,
        'catalog': catalog(perms),
        'editable': editable,
        'save': url('api_bp.update_role', role_id=role_id) if role_id else url('api_bp.create_role'),
        'method': 'PATCH' if role_id else 'POST',
        'delete': url('api_bp.delete_role', role_id=role_id) if role_id and editable else None,
        'back': url('settings_bp.roles'),
    }


def choices(org_id, perms) -> List[List[str]]:
    """The roles they may give someone, as [value, label]: the built-in ones (by name) and the organization's own (by
    id), each only if it's within their own permissions."""
    import permissions as P
    from db import db
    out = [[r, P.ROLE_LABELS[r]] for r in ('viewer', 'sales', 'member', 'admin', 'owner') if P.may_give(r, perms)]
    out += [[str(r['role_id']), r['name']] for r in db.execute_proc('sp_list_roles', (org_id,)) or []
            if P.may_give(_custom(r), perms)]
    return out
