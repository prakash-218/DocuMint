"""
Revisions of quotations and proforma invoices.

Revising a sent quotation or proforma copies it into a new draft whose source_invoice_id points at the
version it revises, and marks that version 'revised' (imported quotes such as Q/029 and Q/029R1 are
linked the same way). A document and its revisions are one document in several versions: lists show
it once, as its latest version, with the earlier ones folded under it, and its page has a version bar
and what changed from the version before.
"""

from typing import Dict, Iterable, List, Optional

REVISED_TYPES = ('quote', 'proforma')


def chains(docs: Iterable[Dict]) -> Dict[str, List[Dict]]:
    """invoice_id -> every version of its document, oldest first; only documents that were revised.
    A revision is a document whose source is of its own type (a proforma made from a quote isn't one)."""
    quotes = {d['invoice_id']: d for d in docs if d.get('doc_type') in REVISED_TYPES}

    def source(d):
        up = quotes.get(d.get('source_invoice_id'))
        return up if up and up.get('doc_type') == d.get('doc_type') else None

    def ancestors(d) -> List[str]:
        seen = []
        while source(d) and d['source_invoice_id'] not in seen and len(seen) < 100:
            seen.append(d['source_invoice_id'])
            d = quotes[d['source_invoice_id']]
        return seen

    lineage = {i: ancestors(d) for i, d in quotes.items()}
    groups: Dict[str, List[Dict]] = {}
    for i, d in quotes.items():
        groups.setdefault(lineage[i][-1] if lineage[i] else i, []).append(d)
    out = {}
    for versions in groups.values():
        if len(versions) < 2:
            continue
        versions.sort(key=lambda d: (len(lineage[d['invoice_id']]), str(d.get('issue_date') or ''), d.get('doc_number') or ''))
        for d in versions:
            out[d['invoice_id']] = versions
    return out


def collapse(docs: List[Dict]) -> List[Dict]:
    """The documents with each revised one once, where its latest version is. That row gets
    'versions' (the earlier ones, newest first); the others go."""
    by_id = chains(docs)
    out = []
    for d in docs:
        versions = by_id.get(d['invoice_id'])
        if not versions:
            out.append(d)
        elif versions[-1]['invoice_id'] == d['invoice_id']:
            out.append(dict(d, versions=list(reversed(versions[:-1]))))
    return out


def matches(doc: Dict, test) -> bool:
    """test(document) for a collapsed row or any of its earlier versions (a search for an old number finds it)."""
    return test(doc) or any(test(v) for v in doc.get('versions') or [])


# ---------------------------------------------------------------- What changed

def _key(text: str) -> str:
    first = next((line for line in (text or '').splitlines() if line.strip()), '')
    return ' '.join(first.lower().split())


def _price(line: Dict) -> float:
    return round(line['amount'] / line['qty'], 2) if line['qty'] else line['amount']


def compare(before: Dict, after: Dict) -> Dict:
    """What changed from one version to the next. before / after: {'header', 'lines' (invoice_service.item_lines),
    'details', 'total'}. Items are matched by the first line of their description."""
    old = {}
    for line in before['lines']:
        old.setdefault(_key(line['description']), []).append(line)
    items = []
    for line in after['lines']:
        same = old.get(_key(line['description']))
        match = same.pop(0) if same else None
        if not match:
            items.append({'change': 'added', 'description': line['description'], 'after': line})
            continue
        changes = []
        if abs(match['qty'] - line['qty']) > 1e-9:
            changes.append('qty')
        if abs(_price(match) - _price(line)) > 0.004:
            changes.append('price')
        if (match['description'] or '').strip() != (line['description'] or '').strip():
            changes.append('description')
        if changes:
            items.append({'change': 'changed', 'description': line['description'], 'before': match, 'after': line,
                          'what': changes, 'price_before': _price(match), 'price_after': _price(line)})
    for rest in old.values():
        items += [{'change': 'removed', 'description': line['description'], 'before': line} for line in rest]

    fields = []
    b, a = before['details'], after['details']
    for key, label in (('subject', 'Subject'), ('reference', 'Reference'), ('kind_attn', 'Kind attn.')):
        if (b.get(key) or '').strip() != (a.get(key) or '').strip():
            fields.append({'label': label, 'before': b.get(key) or '', 'after': a.get(key) or ''})
    if str(before['header'].get('due_date') or '') != str(after['header'].get('due_date') or ''):
        fields.append({'label': 'Valid until', 'before': before['header'].get('due_date'), 'after': after['header'].get('due_date'),
                       'dates': True})
    old_terms = [t.strip() for t in (b.get('terms') or '').splitlines() if t.strip()]
    new_terms = [t.strip() for t in (a.get('terms') or '').splitlines() if t.strip()]
    terms = {'added': [t for t in new_terms if t not in old_terms], 'removed': [t for t in old_terms if t not in new_terms]}
    notes = (b.get('notes') or '').strip() != (a.get('notes') or '').strip()
    total_before, total_after = float(before['total'] or 0), float(after['total'] or 0)
    return {'items': items, 'fields': fields, 'terms': terms if terms['added'] or terms['removed'] else None,
            'notes_changed': notes, 'total_before': total_before, 'total_after': total_after,
            'total_change': round(total_after - total_before, 2),
            'nothing': not (items or fields or terms['added'] or terms['removed'] or notes or abs(total_after - total_before) > 0.004)}


def previous(versions: List[Dict], invoice_id: str) -> Optional[Dict]:
    ids = [v['invoice_id'] for v in versions]
    at = ids.index(invoice_id) if invoice_id in ids else -1
    return versions[at - 1] if at > 0 else None
