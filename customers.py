"""
Customers and their sites.

A customer can have sites - plants, branches, divisions or sister companies - one level
deep: a maker with its Gears Division, Madurai and Dindigul plants; a group with its Chennai
company, its US company and a sister firm. Each site is a customer
of its own for billing (name, GSTIN, address on the documents); the parent groups them,
and its email domains cover them all.
"""

from typing import Dict, List


def label(row: Dict) -> str:
    """'Farm Gear Works · Madurai' for a site, the name otherwise. Takes a customer row or any row with
    customer_name / customer_site (projects, documents)."""
    if 'customer_name' in row:
        name, site = row.get('customer_name'), row.get('customer_site')
    else:
        name, site = row.get('name'), row.get('site')
    return f'{name} · {site}' if site else (name or '')


def _name_key(c: Dict):
    return (c.get('name') or '').lower()


def _site_key(c: Dict):
    return ((c.get('site') or '').lower(), (c.get('name') or '').lower())


def group(customers: List[Dict]) -> List[Dict]:
    """[{'customer': parent or standalone, 'sites': [...]}] sorted by name. A site whose parent isn't
    in the list (archived, filtered out) stands on its own."""
    present = {c['customer_id'] for c in customers}
    sites: Dict[str, List[Dict]] = {}
    for c in customers:
        if c.get('parent_id') in present:
            sites.setdefault(c['parent_id'], []).append(c)
    return [{'customer': c, 'sites': sorted(sites.get(c['customer_id'], []), key=_site_key)}
            for c in sorted(customers, key=_name_key) if c.get('parent_id') not in present]


def search(customers: List[Dict], query: str) -> List[Dict]:
    """Customers matching the query, plus the parent of a matching site and the sites of a matching parent."""
    q = (query or '').strip().lower()
    if not q:
        return customers
    hit = {c['customer_id'] for c in customers
           if any(q in (c.get(k) or '').lower() for k in ('name', 'site', 'city', 'country', 'tax_id'))}
    return [c for c in customers
            if c['customer_id'] in hit or c.get('parent_id') in hit
            or any(s.get('parent_id') == c['customer_id'] and s['customer_id'] in hit for s in customers)]


def parent_choices(customers: List[Dict], customer_id=None) -> List[Dict]:
    """Customers that can be a parent: top-level ones other than this one."""
    return sorted([c for c in customers if not c.get('parent_id') and c['customer_id'] != customer_id
                   and not c.get('is_archived')], key=_name_key)
