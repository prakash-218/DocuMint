"""
Projects and customer documents.

A project groups one customer's documents for a piece of work: the quotation and
its revisions, the proforma, the tax / export invoice. Converting or revising a
document keeps it in the source's project (starting one if needed), so a project builds
itself as the work moves along.

Customer documents are files from or about the customer - their PO, drawings,
specs - attached to the customer and optionally to a project or one document. A PO
uploaded to a project fills "Buyer's order no. / date" on the project's drafts.
Attachments of the email threads in a project are copied into its files, once each.
"""

import logging
import os
import re
import unicodedata
from datetime import date
from typing import Dict, Iterable, List, Optional, Set

from db import db, DatabaseError

logger = logging.getLogger(__name__)

PROJECT_STATUSES = {'open': 'Open', 'completed': 'Completed', 'cancelled': 'Cancelled'}

DOCUMENT_KINDS = {
    'po': 'Purchase order',
    'drawing': 'Drawing',
    'specification': 'Specification',
    'enquiry': 'Enquiry / RFQ',
    'correspondence': 'Correspondence',
    'report': 'Inspection / test report',
    'our_quote': 'Our quotation (made earlier)',
    'our_proforma': 'Our proforma (made earlier)',
    'our_invoice': 'Our invoice (made earlier)',
    'other': 'Other',
}

# Our own documents from before DocuMint, uploaded as files: which project stage they belong to
EARLIER_KINDS = {'our_quote': 'quote', 'our_proforma': 'proforma', 'our_invoice': 'invoice'}
NOT_QUOTATIONS = {k for k, t in EARLIER_KINDS.items() if t != 'quote'}     # files Sales don't see

MAX_FILE_BYTES = 10 * 1024 * 1024

# Extension -> the content type we serve it as (never the browser-supplied one)
FILE_TYPES = {
    'pdf': 'application/pdf',
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'csv': 'text/csv', 'txt': 'text/plain',
    'dwg': 'application/acad', 'dxf': 'application/dxf',
    'step': 'application/step', 'stp': 'application/step', 'igs': 'application/iges', 'iges': 'application/iges',
    'zip': 'application/zip',
    'eml': 'message/rfc822', 'msg': 'application/vnd.ms-outlook',
}
INLINE_TYPES = {'application/pdf', 'image/png', 'image/jpeg', 'image/webp'}   # opened in the browser
_MAGIC = {'pdf': (b'%PDF',), 'png': (b'\x89PNG',), 'jpg': (b'\xff\xd8',), 'jpeg': (b'\xff\xd8',),
          'webp': (b'RIFF',), 'zip': (b'PK',), 'docx': (b'PK',), 'xlsx': (b'PK',)}


class UploadError(ValueError):
    pass


def project_label(project) -> str:
    no = project.get('project_no') if isinstance(project, dict) else project
    return f'PRJ-{int(no):03}' if no else ''


# ---------------------------------------------------------------- Grouping

def document_families(rows: Iterable[Dict]) -> List[Set[str]]:
    """
    Split documents into families of related ones: linked by conversion
    (source_invoice_id) or being revisions of one quotation (same base number),
    and always for the same customer. Pure; rows from sp_list_org_document_links.
    """
    rows = list(rows)
    parent = {r['invoice_id']: r['invoice_id'] for r in rows}
    customer = {r['invoice_id']: r.get('customer_id') for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        if a in parent and b in parent and customer[a] == customer[b]:
            parent[find(a)] = find(b)

    by_quote_base: Dict[tuple, str] = {}
    for r in rows:
        if r.get('source_invoice_id'):
            union(r['invoice_id'], r['source_invoice_id'])
        if r.get('doc_type') == 'quote':
            base = r.get('base_number') or r.get('doc_number')
            if base:
                key = (r.get('customer_id'), base)
                if key in by_quote_base:
                    union(r['invoice_id'], by_quote_base[key])
                else:
                    by_quote_base[key] = r['invoice_id']

    groups: Dict[str, Set[str]] = {}
    for r in rows:
        groups.setdefault(find(r['invoice_id']), set()).add(r['invoice_id'])
    return list(groups.values())


def suggest_title(docs: List[Dict]) -> str:
    """A project title from its documents: the quotation's subject, else the first document's number."""
    order = {'quote': 0, 'proforma': 1, 'invoice': 2, 'export_invoice': 2}
    docs = sorted(docs, key=lambda d: (order.get(d.get('doc_type'), 3), str(d.get('issue_date') or '')))
    for d in docs:
        subject = (d.get('subject') or '').strip()
        if subject and subject.lower() != 'null':
            return subject[:200]
    first = docs[0] if docs else {}
    number = first.get('base_number') or first.get('doc_number')
    return f'Work from {number}' if number else 'New project'


def _links(org_id) -> List[Dict]:
    return db.execute_proc('sp_list_org_document_links', (org_id,)) or []


def current_fiscal_year(org_id) -> str:
    """This financial year in the organization's terms ('26-27'), for a project started today."""
    from document_service import get_org_profile
    from documents import fiscal_year, fy_start_month
    return fiscal_year(date.today(), fy_start_month(get_org_profile(org_id)[1]))


def fiscal_year_of(docs: Iterable[Dict]) -> Optional[str]:
    """The year of the earliest document: a project started from documents belongs to that year."""
    dated = sorted((d for d in docs if d.get('fiscal_year')), key=lambda d: str(d.get('issue_date') or '9999'))
    return dated[0]['fiscal_year'] if dated else None


def recent_fiscal_years(org_id, count=3) -> List[str]:
    """This financial year and the ones before it ('26-27', '25-26', ...), to pick a project's year from."""
    this = current_fiscal_year(org_id)
    if '-' not in this:
        return [str(int(this) - n) for n in range(count)]
    first = int(this[:2])
    return [f'{(first - n) % 100:02d}-{(first - n + 1) % 100:02d}' for n in range(count)]


def create_project(org_id, customer_id, title, reference=None, notes=None, user_id=None, fiscal_year=None) -> str:
    row = db.execute_proc_single('sp_create_project', (org_id, customer_id, (title or 'New project').strip()[:200],
                                                   (reference or '').strip()[:100], (notes or '').strip(), user_id,
                                                   fiscal_year or current_fiscal_year(org_id)))
    return row['project_id']


def get_project(project_id, org_id) -> Optional[Dict]:
    if not project_id:
        return None
    try:
        return db.execute_proc_single('sp_get_project', (project_id, org_id))
    except DatabaseError:
        return None


def project_of(invoice_id, org_id) -> Optional[str]:
    row = db.execute_proc_single('sp_get_invoice_project', (invoice_id, org_id))
    return (row or {}).get('project_id')


def set_project(invoice_id, org_id, project_id):
    db.execute_proc('sp_set_invoice_project', (invoice_id, org_id, project_id), fetch=False)


def group_family(invoice_id, org_id, user_id=None, title=None) -> str:
    """Put a document and everything related to it into one project (the family's existing project, or a new one)."""
    rows = _links(org_id)
    by_id = {r['invoice_id']: r for r in rows}
    family = next((f for f in document_families(rows) if invoice_id in f), {invoice_id})
    members = [by_id[i] for i in family if i in by_id]
    project_id = next((m['project_id'] for m in members if m.get('project_id')), None)
    if not project_id:
        project_id = create_project(org_id, by_id[invoice_id]['customer_id'], title or suggest_title(members), user_id=user_id,
                                    fiscal_year=fiscal_year_of(members))
    for m in members:
        if not m.get('project_id'):
            set_project(m['invoice_id'], org_id, project_id)
    return project_id


def group_all(org_id, user_id=None) -> int:
    """Start projects for every family of linked documents (2 or more) that isn't fully in a project. Returns projects created."""
    rows = _links(org_id)
    by_id = {r['invoice_id']: r for r in rows}
    created = 0
    for family in document_families(rows):
        members = [by_id[i] for i in family]
        if len(members) < 2 or all(m.get('project_id') for m in members):
            continue
        project_id = next((m['project_id'] for m in members if m.get('project_id')), None)
        if not project_id:
            project_id = create_project(org_id, members[0]['customer_id'], suggest_title(members), user_id=user_id,
                                        fiscal_year=fiscal_year_of(members))
            created += 1
        for m in members:
            if not m.get('project_id'):
                set_project(m['invoice_id'], org_id, project_id)
    return created


def ungrouped_families(org_id) -> int:
    """How many sets of linked documents (2 or more) still have a document outside a project."""
    rows = _links(org_id)
    in_project = {r['invoice_id'] for r in rows if r.get('project_id')}
    return sum(1 for f in document_families(rows) if len(f) > 1 and f - in_project)


def follow_source(source: Dict, new_id: str, org_id) -> Optional[str]:
    """A converted / revised document joins its source's project; one is started if the source had none."""
    try:
        # the new document's source_invoice_id already ties it into the source's family
        return group_family(source['invoice_id'], org_id)
    except DatabaseError:
        logger.exception("Could not add %s to the project of %s", new_id, source.get('invoice_id'))
        return None


def project_documents(project_id, org_id) -> List[Dict]:
    """The project's documents (list rows, same shape as sp_list_invoices), in workflow order."""
    ids = {r['invoice_id'] for r in _links(org_id) if r.get('project_id') == project_id}
    if not ids:
        return []
    docs = [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [] if d['invoice_id'] in ids]
    order = {'quote': 0, 'proforma': 1, 'invoice': 2, 'export_invoice': 2}
    return sorted(docs, key=lambda d: (order.get(d.get('doc_type'), 3), str(d.get('issue_date') or ''),
                                       d.get('doc_number') or ''))


def project_stages(docs: List[Dict], files: Optional[List[Dict]] = None) -> List[Dict]:
    """Documents by stage for the project page: quotations, proforma invoices, invoices -
    with any made before DocuMint and uploaded as files."""
    from documents import DOC_TYPES
    stages = [('quote', ('quote',)), ('proforma', ('proforma',)), ('invoice', ('invoice', 'export_invoice'))]
    out = []
    for key, types in stages:
        out.append({'key': key, 'label': DOC_TYPES[key].plural,
                    'docs': [d for d in docs if d.get('doc_type') in types],
                    'uploads': [f for f in files or [] if EARLIER_KINDS.get(f.get('kind')) == key]})
    return out


def project_money(docs: List[Dict], files: Optional[List[Dict]] = None) -> Dict:
    """Quoted (latest live quotation, or an uploaded earlier one), invoiced, received and due - per currency."""
    from documents import balance_of, sum_by_currency
    live_quotes = [d for d in docs if d.get('doc_type') == 'quote' and d.get('status') not in ('revised', 'declined')]
    if not live_quotes:
        live_quotes = [{'total_amount': f['amount'], 'currency_code': f.get('currency')} for f in reversed(files or [])
                       if f.get('kind') == 'our_quote' and f.get('amount')]
    invoices = [d for d in docs if d.get('doc_type') in ('invoice', 'export_invoice') and d.get('status') != 'draft']
    proformas = [d for d in docs if d.get('doc_type') == 'proforma']
    return {
        'quoted': sum_by_currency(live_quotes[-1:], lambda d: d.get('total_amount')),
        'invoiced': sum_by_currency(invoices, lambda d: d.get('total_amount')),
        'received': sum_by_currency(invoices, lambda d: d.get('paid_amount')),
        'due': sum_by_currency(invoices, balance_of),
        'advances': sum_by_currency(proformas, lambda d: d.get('paid_amount')),   # not applied to an invoice yet
    }


def unassigned_documents(org_id, customer_id) -> List[Dict]:
    """This customer's documents that aren't in any project (to add to one)."""
    free = {r['invoice_id'] for r in _links(org_id) if r.get('customer_id') == customer_id and not r.get('project_id')}
    return [d for d in db.execute_proc('sp_list_invoices', (org_id, None, 100000, 0)) or [] if d['invoice_id'] in free]


def list_projects(org_id, customer_id=None, status=None) -> List[Dict]:
    return db.execute_proc('sp_list_projects', (org_id, customer_id, status)) or []


# ---------------------------------------------------------------- Finding a project
# The same matching runs in the browser, in static/js/fuzzy.js and project-picker.js: keep them alike.

def _words(text) -> List[str]:
    plain = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode().lower()
    return re.findall(r'[a-z0-9]+', plain)


def _one_edit_apart(a: str, b: str) -> bool:
    """a and b differ by one letter added, dropped, changed, or two neighbours swapped."""
    if a == b or abs(len(a) - len(b)) > 1:
        return a == b
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        return len(diff) == 1 or (len(diff) == 2 and diff[1] == diff[0] + 1
                                  and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]])
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    i = next((i for i in range(len(short)) if short[i] != long_[i]), len(short))
    return short[i:] == long_[i + 1:]


def _in_order(token: str, word: str) -> bool:
    """'trq' in 'torque': the letters appear in order."""
    it = iter(word)
    return all(ch in it for ch in token)


def _word_score(token: str, words: List[str]) -> int:
    best = 0
    for w in words:
        if w == token:
            return 10
        if w.startswith(token):
            score = 8
        elif token in w:
            score = 5
        elif len(token) >= 4 and (_one_edit_apart(token, w) or _one_edit_apart(token, w[:len(token)])):
            score = 4
        elif len(token) >= 2 and w[:1] == token[:1] and _in_order(token, w):
            score = 3
        else:
            continue
        best = max(best, score)
    return best


def match_score(project: Dict, query: str) -> Optional[int]:
    """How well a project matches a search such as 'piston torqe', 'prj 47' or 'wipro a22'; None when it
    doesn't. Each word of the search has to match a word of the project's name, number, customer, site or
    reference: exactly, as its start, inside it, with one typo, or as an abbreviation ('trq' for torque).
    The project's own number ('47', 'PRJ-047') counts most, then matches in the name."""
    tokens = _words(query)
    if not tokens:
        return 0
    no = int(project.get('project_no') or 0)
    title = _words(project.get('title'))
    other = _words(' '.join(str(project.get(k) or '') for k in ('customer_name', 'customer_site', 'reference'))) + ['prj']
    total = 0
    for token in tokens:
        if token.removeprefix('prj').lstrip('0') == str(no) and token.removeprefix('prj').isdigit():
            total += 15
            continue
        in_title = _word_score(token, title)
        score = max(in_title + 2 if in_title else 0, _word_score(token, other))
        if not score:
            return None
        total += score
    return total


def search_projects(projects: List[Dict], query: str) -> List[Dict]:
    """The projects that match, best first (open ones, then the most recent, on a tie)."""
    scored = [(match_score(p, query), p) for p in projects]
    hits = [(s, p) for s, p in scored if s is not None]
    hits.sort(key=lambda sp: (-sp[0], sp[1].get('status') != 'open', -(sp[1].get('project_no') or 0)))
    return [p for _, p in hits]


def picker_rows(projects: List[Dict]) -> List[Dict]:
    """What the project picker needs of each project (JSON)."""
    return [{'id': p['project_id'], 'no': project_label(p), 'project_no': p.get('project_no') or 0,
             'customer_id': str(p.get('customer_id') or ''),
             'title': p.get('title') or '', 'customer': p.get('customer_name') or '', 'site': p.get('customer_site') or '',
             'reference': p.get('reference') or '', 'fy': p.get('fiscal_year') or '', 'status': p.get('status') or 'open',
             'docs': p.get('document_count') or 0, 'last': str(p.get('last_issue_date') or '')}
            for p in projects]


# ---------------------------------------------------------------- Customer documents

def read_upload(upload) -> tuple:
    """(file name, content type, bytes) for an allowed file; raises UploadError."""
    if not upload or not upload.filename:
        raise UploadError('Choose a file to upload')
    name = os.path.basename(upload.filename.replace('\\', '/')).strip()
    name = re.sub(r'[\x00-\x1f"]', '', name)[:200] or 'file'
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if ext not in FILE_TYPES:
        raise UploadError(f'{name}: that kind of file isn\'t supported. Use PDF, images, Office files, CAD (DWG/DXF/STEP) or ZIP.')
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise UploadError(f'{name}: files must be under {MAX_FILE_BYTES // (1024 * 1024)} MB')
    if not data:
        raise UploadError(f'{name} is empty')
    magic = _MAGIC.get(ext)
    if magic and not data.startswith(magic):
        raise UploadError(f"{name} doesn't look like a real .{ext} file")
    return name, FILE_TYPES[ext], data


def _date_or_none(value):
    try:
        return date.fromisoformat((value or '').strip()).isoformat()
    except ValueError:
        return None


def _amount_or_none(value):
    try:
        return round(float(str(value).replace(',', '')), 2) if str(value or '').strip() else None
    except ValueError:
        return None


def add_attachment(org_id, customer_id, form, upload, user_id=None, project_id=None, invoice_id=None) -> Dict:
    """Store an uploaded customer document. Returns {'attachment_id', 'filled': [doc numbers given the PO no.]}."""
    name, content_type, data = read_upload(upload)
    chosen = form.get('kind') in DOCUMENT_KINDS
    kind = form.get('kind') if chosen else guess_kind(name)        # dropped in: what its name suggests
    title = (form.get('title') or '').strip()[:200] or (DOCUMENT_KINDS[kind] if chosen and kind != 'other' else name)
    reference = (form.get('reference_no') or '').strip()[:100]
    doc_date = _date_or_none(form.get('doc_date'))
    amount = _amount_or_none(form.get('amount'))
    currency = (form.get('currency') or '').upper()[:3]
    if amount is not None and not currency:
        from document_service import get_org_profile
        currency = get_org_profile(org_id)[1].get('default_currency') or 'INR'
    row = db.execute_proc_single('sp_add_attachment', (
        org_id, customer_id, project_id or None, invoice_id or None, kind, title, reference, doc_date,
        amount, currency,
        (form.get('notes') or '').strip()[:2000], name, content_type, data, user_id))
    filled = []
    if kind == 'po' and reference and project_id and form.get('fill_po', 'on'):
        filled = fill_purchase_order(org_id, project_id, reference, doc_date)
    return {'attachment_id': row['attachment_id'], 'filled': filled}


def update_attachment(org_id, attachment: Dict, kind: str, reference_no: str = '') -> List[str]:
    """Say what a file is and its number after it was dropped in. A PO's number goes onto the project's documents,
    as when it's uploaded with one; returns those documents' numbers."""
    if kind not in DOCUMENT_KINDS:
        raise UploadError("That isn't a kind of document.")
    reference = (reference_no or '').strip()[:100]
    title = attachment.get('title') or ''
    if not title or title == DOCUMENT_KINDS.get(attachment.get('kind')):      # titled by its old type: by its name
        title = attachment.get('file_name') or ''
    db.execute_proc('sp_update_attachment', (attachment['attachment_id'], org_id, kind, title, reference), fetch=False)
    if kind == 'po' and reference and attachment.get('project_id'):
        return fill_purchase_order(org_id, attachment['project_id'], reference, attachment.get('doc_date'))
    return []


def list_attachments(org_id, customer_id=None, project_id=None, invoice_id=None) -> List[Dict]:
    return db.execute_proc('sp_list_attachments', (org_id, customer_id, project_id, invoice_id)) or []


# ---------------------------------------------------------------- Files from email

CAD_EXTS = {'dwg', 'dxf', 'step', 'stp', 'igs', 'iges'}
MIN_EMAIL_IMAGE_BYTES = 30_000          # smaller images in mail are logos and signatures


def _word(pattern):
    """A pattern that isn't part of a longer word ("PO 4500" and "po_4500" yes, "report" no)."""
    return re.compile(rf'(?<![a-z]){pattern}(?![a-z])')


KIND_PATTERNS = [
    ('drawing', _word(r'(?:drg|drgs|drawings?|dwg)')),
    ('po', re.compile(r'(?<![a-z])p\.?o(?![a-z])|purchase[\s_-]*order')),
    ('enquiry', re.compile(r'(?<![a-z])rfq(?![a-z])|enquiry|inquiry')),
    ('report', re.compile(r'inspection|test[\s_-]*report|(?<![a-z])report(?![a-z])')),
    ('specification', re.compile(r'(?<![a-z])spec(?:s|ification)?(?![a-z])')),
]
# Only for files we sent: our own quotation / proforma / invoice from before DocuMint
OUR_KIND_PATTERNS = [
    ('our_proforma', re.compile(r'proforma|(?<![a-z])pi(?![a-z])')),
    ('our_invoice', re.compile(r'invoice|(?<![a-z])inv(?![a-z])')),
    ('our_quote', re.compile(r'quot|(?<![a-z])q\s*0*\d')),
]


def guess_kind(file_name: str, outgoing: bool = False) -> str:
    """The document kind a file name suggests ("PO 4500123.pdf" -> po, "KKR Q020(26-27).pdf" we sent -> our_quote)."""
    name = (file_name or '').lower()
    if name.rsplit('.', 1)[-1] in CAD_EXTS:
        return 'drawing'
    for kind, pattern in (OUR_KIND_PATTERNS if outgoing else []) + KIND_PATTERNS:
        if pattern.search(name):
            return kind
    return 'other'


def email_file_wanted(f: Dict, data: bytes) -> bool:
    """A real document: an allowed type whose bytes match it, and not a logo or signature image."""
    name = f.get('file_name') or ''
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if ext not in FILE_TYPES or not data:
        return False
    if FILE_TYPES[ext].startswith('image/') and len(data) < MIN_EMAIL_IMAGE_BYTES:
        return False
    magic = _MAGIC.get(ext)
    return not magic or data.startswith(magic)


def add_email_files(org_id, project_id, thread_id, message_id=None) -> Dict:
    """Copy an email thread's attachments (or one message's) into the project's files, once each:
    a file whose bytes the project already has - the same drawing in every reply - is skipped.
    Returns {'added': n, 'duplicates': n, 'skipped': n} (skipped: logos, signatures, unsupported types)."""
    import storage
    from store.procs import sha256
    project = get_project(project_id, org_id)
    counts = {'added': 0, 'duplicates': 0, 'skipped': 0}
    if not project:
        return counts
    have = {r['content_hash'] for r in db.execute_proc('sp_project_file_hashes', (org_id, project_id)) or []}
    for f in db.execute_proc('sp_list_thread_files', (org_id, thread_id, message_id)) or []:
        data = storage.get(f['storage_key'])
        digest = f.get('content_hash') or sha256(data)
        if not f.get('content_hash'):
            db.execute_proc('sp_set_email_file_hash', (f['file_id'], digest), fetch=False)
        if digest in have:
            counts['duplicates'] += 1
            continue
        if not email_file_wanted(f, data):
            counts['skipped'] += 1
            continue
        name = f['file_name']
        kind = guess_kind(name, outgoing=f.get('direction') == 'out')
        who = f.get('from_name') or f.get('from_address') or ''
        db.execute_proc('sp_add_attachment', (
            org_id, project['customer_id'], project_id, None, kind, os.path.splitext(name)[0][:200] or name, '',
            f['sent_at'].date().isoformat() if f.get('sent_at') else None, None, '',
            f"From email: {f.get('subject') or ''}" + (f' ({who})' if who else ''), name[:200],
            FILE_TYPES[name.rsplit('.', 1)[-1].lower()], data, None, f['message_id']))
        have.add(digest)
        counts['added'] += 1
    return counts


def remove_email_files(org_id, project_id, thread_id) -> int:
    """Take the files copied from a thread back out of a project."""
    row = db.execute_proc_single('sp_remove_thread_files_from_project', (org_id, project_id, thread_id))
    return (row or {}).get('removed', 0)


def get_attachment(attachment_id, org_id) -> Optional[Dict]:
    try:
        return db.execute_proc_single('sp_get_attachment', (attachment_id, org_id))
    except DatabaseError:
        return None


def latest_purchase_order(org_id, project_id) -> Optional[Dict]:
    pos = [d for d in list_attachments(org_id, project_id=project_id) if d.get('kind') == 'po' and d.get('reference_no')]
    return pos[0] if pos else None


def po_details(po: Optional[Dict]) -> Dict:
    """detail_* values a PO gives a new document."""
    if not po:
        return {}
    out = {'buyer_order_no': po['reference_no']}
    if po.get('doc_date'):
        out['buyer_order_date'] = str(po['doc_date'])
    return out


def fill_purchase_order(org_id, project_id, number, po_date) -> List[str]:
    """Write the PO no./date onto the project's draft documents that have the field and leave it blank."""
    from access import get_org_invoice
    from document_service import save_details
    from documents import get_type, load_json
    filled = []
    for d in project_documents(project_id, org_id):
        if (d.get('status') or 'draft') != 'draft':
            continue
        if 'buyer_order_no' not in {f.key for f in get_type(d.get('doc_type')).details}:
            continue
        header, _ = get_org_invoice(d['invoice_id'], org_id)
        details = load_json(header.get('details'))
        if details.get('buyer_order_no'):
            continue
        details['buyer_order_no'] = number
        if po_date:
            details['buyer_order_date'] = po_date
        save_details(header, org_id, details)
        filled.append(d.get('doc_number') or 'a draft')
    return filled


def human_size(n) -> str:
    n = int(n or 0)
    if n < 1024:
        return f'{n} B'
    if n < 1024 * 1024:
        return f'{n / 1024:.0f} KB'
    return f'{n / (1024 * 1024):.1f} MB'
