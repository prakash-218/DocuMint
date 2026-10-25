"""
Data access for PostgreSQL, one function per operation.

These replace the MySQL stored procedures. Each keeps the old name, arguments and
returned columns, so callers using db.execute_proc('sp_...', args) work
unchanged. A function gets an open connection (inside a transaction) and returns a
list of result sets, each a list of row dicts. db.py turns that into the shape the
old driver returned.

Raise ProcError(message) for a business rule; the message is what the user sees.
"""

import json
import uuid
from datetime import date
from typing import Callable, Dict, List

from sqlalchemy import text

PROCS: Dict[str, Callable] = {}


class ProcError(Exception):
    pass


def proc(name):
    def register(fn):
        PROCS[name] = fn
        return fn
    return register


def _rows(conn, sql, **params) -> List[dict]:
    return [dict(r._mapping) for r in conn.execute(text(sql), params)]


def _one(conn, sql, **params):
    rows = _rows(conn, sql, **params)
    return rows[0] if rows else None


def _exec(conn, sql, **params) -> int:
    return conn.execute(text(sql), params).rowcount


def _new_id() -> str:
    return str(uuid.uuid4())


def _json(value):
    if value is None or value == '':
        return None
    return value if isinstance(value, str) else json.dumps(value)


def _require(conn, sql, message, **params):
    if not _one(conn, sql, **params):
        raise ProcError(message)


def _audit(conn, org_id, table, record_id, action, field=None, old=None, new=None, info=None):
    _exec(conn, """INSERT INTO audit_log (org_id, table_name, record_id, action_type, field_name, old_value,
                                          new_value, additional_info)
                   VALUES (:org, :t, :r, :a, :f, :o, :n, :i)""",
          org=org_id, t=table, r=str(record_id), a=action, f=field,
          o=None if old is None else str(old), n=None if new is None else str(new), i=info)


# Currency of a document: its own (details.currency) or its template's
CURRENCY = "COALESCE(i.details->>'currency', t.currency_code)"
TEMPLATE_JOIN = "LEFT JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version"
PAID = "(SELECT COALESCE(SUM(amount), 0) FROM payment WHERE payment.invoice_id = i.invoice_id)"

# ================================================================ Users and organizations


@proc('sp_get_user_by_email')
def get_user_by_email(conn, email):
    return [_rows(conn, "SELECT user_id, email, password_hash FROM users WHERE lower(email) = lower(:e)", e=email)]


@proc('sp_create_user')
def create_user(conn, email, password_hash, _out=None):
    if _one(conn, "SELECT 1 FROM users WHERE lower(email) = lower(:e)", e=email):
        raise ProcError('Email already exists')
    uid = _new_id()
    _exec(conn, "INSERT INTO users (user_id, email, password_hash) VALUES (:u, :e, :p)", u=uid, e=email, p=password_hash)
    return [[{'user_id': uid}]]


@proc('sp_get_user_organizations')
def get_user_organizations(conn, user_id):
    return [_rows(conn, """SELECT uo.org_id, o.name, o.domain, uo.role, uo.status
                           FROM user_organization uo JOIN organization o ON uo.org_id = o.org_id
                           WHERE uo.user_id = :u ORDER BY uo.created_at DESC, o.name""", u=user_id)]


@proc('sp_find_organizations_by_domain')
def find_organizations_by_domain(conn, domain):
    return [_rows(conn, """SELECT org_id, name, domain, created_at FROM organization
                           WHERE lower(domain) = lower(:d) ORDER BY created_at DESC""", d=domain)]


@proc('sp_create_organization')
def create_organization(conn, name, domain, street, city, state, zip_code, country, _out=None):
    oid = _new_id()
    _exec(conn, """INSERT INTO organization (org_id, domain, name, street_address, city, state, zip_code, country)
                   VALUES (:o, :d, :n, :s, :c, :st, :z, :co)""",
          o=oid, d=domain, n=name, s=street, c=city, st=state, z=zip_code, co=country)
    return [[{'org_id': oid}]]


@proc('sp_get_organization_details')
def get_organization_details(conn, org_id):
    return [_rows(conn, """SELECT org_id, name, domain, street_address, city, state, zip_code, country, created_at
                           FROM organization WHERE org_id = :o""", o=org_id)]


@proc('sp_get_organization_profile')
def get_organization_profile(conn, org_id):
    return [_rows(conn, """SELECT org_id, name, domain, street_address, city, state, zip_code, country, profile
                           FROM organization WHERE org_id = :o""", o=org_id)]


@proc('sp_update_organization')
def update_organization(conn, org_id, name, street, city, state, zip_code, country):
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    n = _exec(conn, """UPDATE organization SET name = COALESCE(:n, name), street_address = :s, city = :c,
                       state = :st, zip_code = :z, country = :co WHERE org_id = :o""",
              o=org_id, n=name, s=street, c=city, st=state, z=zip_code, co=country)
    return [[{'rows_affected': n}]]


@proc('sp_update_organization_profile')
def update_organization_profile(conn, org_id, profile):
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    _exec(conn, "UPDATE organization SET profile = CAST(:p AS jsonb) WHERE org_id = :o", o=org_id, p=_json(profile) or '{}')
    return []


@proc('sp_assign_user_to_org')
def assign_user_to_org(conn, user_id, org_id, role, status):
    _require(conn, "SELECT 1 FROM users WHERE user_id = :u", 'User does not exist', u=user_id)
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    _exec(conn, """INSERT INTO user_organization (user_id, org_id, role, status)
                   VALUES (:u, :o, COALESCE(:r, 'member'), COALESCE(:s, 'pending'))
                   ON CONFLICT (user_id, org_id) DO UPDATE SET role = COALESCE(:r, user_organization.role)""",
          u=user_id, o=org_id, r=role, s=status)
    return []


def _active_owners(conn, org_id, except_user=None):
    row = _one(conn, """SELECT COUNT(*) AS n FROM user_organization WHERE org_id = :o AND role = 'owner'
                        AND status = 'active' AND (CAST(:u AS uuid) IS NULL OR user_id <> CAST(:u AS uuid))""",
               o=org_id, u=except_user)
    return row['n']


@proc('sp_update_member_status')
def update_member_status(conn, org_id, user_id, status, role):
    _require(conn, "SELECT 1 FROM users WHERE user_id = :u", 'User does not exist', u=user_id)
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    current = _one(conn, "SELECT role, status FROM user_organization WHERE org_id = :o AND user_id = :u", o=org_id, u=user_id)
    if not current:
        return []
    losing_owner = current['role'] == 'owner' and current['status'] == 'active' and (
        status in ('rejected', 'deactivated', 'pending') or (role and role != 'owner'))
    if losing_owner and _active_owners(conn, org_id, except_user=user_id) == 0:
        raise ProcError('Cannot change role: Organization must have at least one active owner')
    email = (_one(conn, "SELECT email FROM users WHERE user_id = :u", u=user_id) or {}).get('email')
    info = f'User: {email}'
    if status == 'rejected':
        _exec(conn, "DELETE FROM user_organization WHERE org_id = :o AND user_id = :u", o=org_id, u=user_id)
    else:
        _exec(conn, """UPDATE user_organization SET status = :s, role = COALESCE(:r, role)
                       WHERE org_id = :o AND user_id = :u""", o=org_id, u=user_id, s=status, r=role)
        if role and role != current['role']:
            _audit(conn, org_id, 'user_organization', f'{user_id}:{org_id}', 'UPDATE', 'role', current['role'], role, info)
        if status != current['status']:
            _audit(conn, org_id, 'user_organization', f'{user_id}:{org_id}', 'UPDATE', 'status', current['status'], status, info)
    return []


@proc('sp_get_pending_members')
def get_pending_members(conn, org_id):
    return [_rows(conn, """SELECT u.user_id, u.email, uo.role, uo.created_at AS joined_at
                           FROM user_organization uo JOIN users u ON uo.user_id = u.user_id
                           WHERE uo.org_id = :o AND uo.status = 'pending' ORDER BY uo.created_at DESC""", o=org_id)]


@proc('sp_get_org_members')
def get_org_members(conn, org_id):
    return [_rows(conn, """SELECT u.user_id, u.email, uo.role, uo.status, uo.created_at AS joined_at
                           FROM user_organization uo JOIN users u ON uo.user_id = u.user_id
                           WHERE uo.org_id = :o AND uo.status IN ('active', 'deactivated')
                           ORDER BY uo.role, u.email""", o=org_id)]


@proc('sp_get_audit_log')
def get_audit_log(conn, org_id, table_name, limit, offset):
    return [_rows(conn, """SELECT audit_id, table_name, record_id, action_type, field_name, old_value, new_value,
                                  changed_by, changed_at, additional_info
                           FROM audit_log WHERE org_id = :o AND (CAST(:t AS text) IS NULL OR table_name = :t)
                           ORDER BY changed_at DESC LIMIT :l OFFSET :off""",
                  o=org_id, t=table_name, l=limit or 100, off=offset or 0)]


# ================================================================ Customers


# How a site is told apart from its siblings: its site name, else its city
CUSTOMER_SITE = "COALESCE(c.site_name, CASE WHEN c.parent_id IS NOT NULL THEN c.city END)"


@proc('sp_list_customers')
def list_customers(conn, org_id, include_archived):
    return [_rows(conn, f"""SELECT c.customer_id, c.name, c.tax_id, c.street_address, c.city, c.state, c.zip_code,
                                   c.country, c.is_archived, c.created_at, c.email_domains, c.parent_id, c.site_name,
                                   {CUSTOMER_SITE} AS site, parent.name AS parent_name,
                                   (SELECT COUNT(*) FROM invoice i WHERE i.customer_id = c.customer_id) AS invoice_count,
                                   (SELECT COUNT(*) FROM customer s WHERE s.parent_id = c.customer_id) AS site_count
                            FROM customer c LEFT JOIN customer parent ON parent.customer_id = c.parent_id
                            WHERE c.org_id = :o AND (:a OR NOT c.is_archived)
                            ORDER BY c.is_archived, c.created_at DESC""", o=org_id, a=bool(include_archived))]


@proc('sp_create_customer')
def create_customer(conn, org_id, name, tax_id, street, city, state, zip_code, country, _out=None):
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    cid = _new_id()
    _exec(conn, """INSERT INTO customer (customer_id, org_id, name, tax_id, street_address, city, state, zip_code, country)
                   VALUES (:c, :o, :n, :t, :s, :ci, :st, :z, :co)""",
          c=cid, o=org_id, n=name, t=tax_id, s=street, ci=city, st=state, z=zip_code, co=country)
    return [[{'customer_id': cid}]]


@proc('sp_get_customer_details')
def get_customer_details(conn, customer_id):
    customer = _rows(conn, f"""SELECT c.customer_id, c.org_id, c.name, c.tax_id, c.street_address, c.city, c.state,
                                      c.zip_code, c.country, c.custom, c.email_domains, c.is_archived, c.created_at,
                                      c.parent_id, c.site_name, {CUSTOMER_SITE} AS site, parent.name AS parent_name,
                                      parent.email_domains AS parent_email_domains
                               FROM customer c LEFT JOIN customer parent ON parent.customer_id = c.parent_id
                               WHERE c.customer_id = :c""", c=customer_id)
    contacts = _rows(conn, """SELECT p.person_id, p.email, p.full_name, cca.role
                              FROM customer_contact_assignment cca JOIN person p ON cca.person_id = p.person_id
                              WHERE cca.customer_id = :c""", c=customer_id)
    return [customer, contacts]


@proc('sp_update_customer')
def update_customer(conn, customer_id, name, tax_id, street, city, state, zip_code, country):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c", 'Customer does not exist', c=customer_id)
    _exec(conn, """UPDATE customer SET name = COALESCE(:n, name), tax_id = :t, street_address = :s, city = :ci,
                   state = :st, zip_code = :z, country = :co WHERE customer_id = :c""",
          c=customer_id, n=name, t=tax_id, s=street, ci=city, st=state, z=zip_code, co=country)
    return []


@proc('sp_set_customer_parent')
def set_customer_parent(conn, customer_id, org_id, parent_id, site_name):
    """Make the customer a site of parent_id (or a customer of its own when parent_id is empty). One level deep."""
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o", 'Customer does not exist',
             c=customer_id, o=org_id)
    parent_id = parent_id or None
    if parent_id:
        if str(parent_id) == str(customer_id):
            raise ProcError('A customer cannot be a site of itself')
        parent = _one(conn, "SELECT parent_id FROM customer WHERE customer_id = CAST(:p AS uuid) AND org_id = :o",
                      p=_as_uuid(parent_id), o=org_id)
        if not parent:
            raise ProcError('The parent customer does not exist')
        if parent['parent_id']:
            raise ProcError('That customer is itself a site; choose its parent instead')
        if _one(conn, "SELECT 1 FROM customer WHERE parent_id = :c LIMIT 1", c=customer_id):
            raise ProcError('This customer has sites of its own, so it cannot be a site')
    _exec(conn, "UPDATE customer SET parent_id = CAST(:p AS uuid), site_name = NULLIF(:s, '') WHERE customer_id = :c",
          c=customer_id, p=parent_id, s=(site_name or '').strip()[:100])
    return []


@proc('sp_list_customer_sites')
def list_customer_sites(conn, org_id, parent_id):
    return [_rows(conn, f"""SELECT c.customer_id, c.name, c.tax_id, c.city, c.state, c.country, c.site_name,
                                   {CUSTOMER_SITE} AS site, c.is_archived, c.parent_id,
                                   (SELECT COUNT(*) FROM invoice i WHERE i.customer_id = c.customer_id) AS invoice_count
                            FROM customer c WHERE c.org_id = :o AND c.parent_id = :p
                            ORDER BY c.is_archived, lower({CUSTOMER_SITE}), lower(c.name)""", o=org_id, p=parent_id)]


@proc('sp_update_customer_custom')
def update_customer_custom(conn, customer_id, org_id, custom):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o", 'Customer does not exist',
             c=customer_id, o=org_id)
    _exec(conn, "UPDATE customer SET custom = CAST(:j AS jsonb) WHERE customer_id = :c", c=customer_id, j=_json(custom) or '{}')
    return []


@proc('sp_update_customer_email_domains')
def update_customer_email_domains(conn, customer_id, org_id, domains):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o", 'Customer does not exist',
             c=customer_id, o=org_id)
    _exec(conn, "UPDATE customer SET email_domains = :d WHERE customer_id = :c", c=customer_id, d=domains or None)
    return []


def _set_archived(conn, customer_id, org_id, archived):
    row = _one(conn, """SELECT c.name, c.is_archived, o.name AS org_name FROM customer c JOIN organization o
                        ON o.org_id = c.org_id WHERE c.customer_id = :c AND c.org_id = :o""", c=customer_id, o=org_id)
    if not row:
        raise ProcError('Customer does not exist or does not belong to organization')
    n = _exec(conn, "UPDATE customer SET is_archived = :a WHERE customer_id = :c", c=customer_id, a=archived)
    if row['is_archived'] != archived:
        _audit(conn, org_id, 'customer', customer_id, 'UPDATE', 'is_archived', int(row['is_archived']), int(archived),
               f"Customer: {row['name']}")
    return [[{'rows_affected': n}]]


@proc('sp_archive_customer')
def archive_customer(conn, customer_id, org_id):
    return _set_archived(conn, customer_id, org_id, True)


@proc('sp_unarchive_customer')
def unarchive_customer(conn, customer_id, org_id):
    return _set_archived(conn, customer_id, org_id, False)


@proc('sp_delete_customer')
def delete_customer(conn, customer_id, org_id):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o",
             'Customer does not exist or does not belong to organization', c=customer_id, o=org_id)
    if _one(conn, "SELECT 1 FROM invoice WHERE customer_id = :c LIMIT 1", c=customer_id):
        raise ProcError('Cannot delete customer with existing invoices. Delete invoices first.')
    if _one(conn, "SELECT 1 FROM customer WHERE parent_id = :c LIMIT 1", c=customer_id):
        raise ProcError('Cannot delete a customer that has sites. Move or delete its sites first.')
    _exec(conn, "DELETE FROM customer WHERE customer_id = :c", c=customer_id)
    return []


@proc('sp_get_customer_users')
def get_customer_users(conn, customer_id):
    return [_rows(conn, """SELECT customer_user_id, customer_id, email, created_at FROM customer_user
                           WHERE customer_id = :c ORDER BY created_at DESC""", c=customer_id)]


@proc('sp_create_customer_user')
def create_customer_user(conn, customer_id, email, password_hash, _out=None):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c", 'Customer does not exist', c=customer_id)
    if _one(conn, "SELECT 1 FROM customer_user WHERE lower(email) = lower(:e)", e=email):
        raise ProcError('Email already exists')
    cuid = _new_id()
    _exec(conn, "INSERT INTO customer_user (customer_user_id, customer_id, email, password_hash) VALUES (:i, :c, :e, :p)",
          i=cuid, c=customer_id, e=email, p=password_hash)
    return [[{'customer_user_id': cuid}]]


@proc('sp_get_customer_user_by_email')
def get_customer_user_by_email(conn, email):
    return [_rows(conn, """SELECT cu.customer_user_id, cu.customer_id, cu.email, cu.password_hash,
                                  c.name AS customer_name, c.org_id
                           FROM customer_user cu JOIN customer c ON cu.customer_id = c.customer_id
                           WHERE lower(cu.email) = lower(:e)""", e=email)]


@proc('sp_get_customer_invoices')
def get_customer_invoices(conn, customer_id):
    return [_rows(conn, f"""SELECT i.invoice_id, i.doc_type, i.doc_number, i.template_id, t.name AS template_name,
                                   {CURRENCY} AS currency_code, i.issue_date, i.due_date, i.status,
                                   {PAID} AS paid_amount, i.total_amount
                            FROM invoice i {TEMPLATE_JOIN}
                            WHERE i.customer_id = :c AND i.status <> 'draft'
                            ORDER BY i.issue_date DESC NULLS LAST, i.invoice_id DESC""", c=customer_id)]


# ================================================================ Templates


@proc('sp_list_templates')
def list_templates(conn, org_id, include_archived):
    return [_rows(conn, """SELECT t.template_id, t.version, t.name, t.currency_code, t.is_archived, t.created_at,
                                  (SELECT MAX(version) FROM template x WHERE x.template_id = t.template_id) AS latest_version
                           FROM template t
                           WHERE t.org_id = :o AND (:a OR NOT t.is_archived)
                           ORDER BY t.is_archived, t.created_at DESC, t.version DESC""", o=org_id, a=bool(include_archived))]


@proc('sp_create_template')
def create_template(conn, org_id, name, currency_code, _out1=None, _out2=None):
    _require(conn, "SELECT 1 FROM organization WHERE org_id = :o", 'Organization does not exist', o=org_id)
    tid = _new_id()
    _exec(conn, "INSERT INTO template (template_id, version, org_id, name, currency_code) VALUES (:t, 1, :o, :n, :c)",
          t=tid, o=org_id, n=name, c=currency_code)
    return [[{'template_id': tid, 'version': 1}]]


def _latest_version(conn, template_id, org_id=None):
    row = _one(conn, """SELECT MAX(version) AS v FROM template WHERE template_id = :t
                        AND (CAST(:o AS uuid) IS NULL OR org_id = CAST(:o AS uuid))""", t=template_id, o=org_id)
    return row['v'] if row else None


@proc('sp_create_template_version')
def create_template_version(conn, template_id, org_id, _out=None):
    """Copy the latest version (sections, fields, document total) as version N+1."""
    latest = _latest_version(conn, template_id, org_id)
    if latest is None:
        raise ProcError('Template does not exist or does not belong to organization')
    old = _one(conn, "SELECT name, currency_code, total_field_id FROM template WHERE template_id = :t AND version = :v",
               t=template_id, v=latest)
    new = latest + 1
    _exec(conn, "INSERT INTO template (template_id, version, org_id, name, currency_code) VALUES (:t, :v, :o, :n, :c)",
          t=template_id, v=new, o=org_id, n=old['name'], c=old['currency_code'])
    new_total = None
    for s in _rows(conn, """SELECT section_id, name, display_name, ordinal, section_type FROM section
                            WHERE template_id = :t AND template_version = :v ORDER BY ordinal""", t=template_id, v=latest):
        sid = _new_id()
        _exec(conn, """INSERT INTO section (section_id, template_id, template_version, name, display_name, ordinal, section_type)
                       VALUES (:s, :t, :v, :n, :d, :o, :ty)""",
              s=sid, t=template_id, v=new, n=s['name'], d=s['display_name'], o=s['ordinal'], ty=s['section_type'])
        for f in _rows(conn, """SELECT * FROM field WHERE section_id = :s ORDER BY ordinal""", s=s['section_id']):
            fid = _new_id()
            _exec(conn, """INSERT INTO field (field_id, section_id, name, display_name, data_type, is_required,
                                              is_currency, ordinal, calculation_formula)
                           VALUES (:f, :s, :n, :d, :ty, :r, :c, :o, :calc)""",
                  f=fid, s=sid, n=f['name'], d=f['display_name'], ty=f['data_type'], r=f['is_required'],
                  c=f['is_currency'], o=f['ordinal'], calc=f['calculation_formula'])
            if str(f['field_id']) == str(old['total_field_id']):
                new_total = fid
    if new_total:
        _exec(conn, "UPDATE template SET total_field_id = :f WHERE template_id = :t AND version = :v", f=new_total, t=template_id, v=new)
    return [[{'new_version': new}]]


@proc('sp_check_template_version_has_invoices')
def check_template_version_has_invoices(conn, template_id, version, org_id):
    n = _one(conn, """SELECT COUNT(*) AS n FROM invoice WHERE template_id = :t AND template_version = :v AND org_id = :o""",
             t=template_id, v=version, o=org_id)['n']
    return [[{'has_invoices': n > 0, 'invoice_count': n}]]


FIELD_COLUMNS = """s.section_id, s.name AS section_name, s.display_name AS section_display_name,
                   s.display_name AS section_title, s.ordinal AS section_ordinal, s.section_type, f.field_id,
                   f.name AS field_name, f.display_name AS field_display_name, f.data_type, f.is_required,
                   f.is_currency, f.ordinal AS field_ordinal, f.calculation_formula"""


@proc('sp_get_template_fields')
def get_template_fields(conn, template_id):
    latest = _latest_version(conn, template_id)
    if latest is None:
        raise ProcError('Template does not exist')
    return get_template_fields_by_version(conn, template_id, latest)


@proc('sp_get_template_fields_by_version')
def get_template_fields_by_version(conn, template_id, version):
    return [_rows(conn, f"""SELECT {FIELD_COLUMNS}, f.display_name AS label
                            FROM section s JOIN field f ON s.section_id = f.section_id
                            WHERE s.template_id = :t AND s.template_version = :v
                            ORDER BY s.ordinal, f.ordinal""", t=template_id, v=version)]


@proc('sp_create_section')
def create_section(conn, template_id, version, name, display_name, ordinal, section_type, _out=None):
    _require(conn, "SELECT 1 FROM template WHERE template_id = :t AND version = :v", 'Template version does not exist',
             t=template_id, v=version)
    if not name or ' ' in name:
        raise ProcError('Section name is required and cannot contain spaces')
    sid = _new_id()
    _exec(conn, """INSERT INTO section (section_id, template_id, template_version, name, display_name, ordinal, section_type)
                   VALUES (:s, :t, :v, :n, :d, :o, :ty)""",
          s=sid, t=template_id, v=version, n=name, d=display_name, o=ordinal or 0,
          ty=section_type if section_type in ('normal', 'line_item') else 'normal')
    return [[{'section_id': sid}]]


@proc('sp_delete_section')
def delete_section(conn, section_id):
    if not _exec(conn, "DELETE FROM section WHERE section_id = :s", s=section_id):
        raise ProcError('Section does not exist')
    return []


@proc('sp_add_template_field')
def add_template_field(conn, section_id, name, display_name, data_type, is_required, is_currency, ordinal, formula, _out=None):
    _require(conn, "SELECT 1 FROM section WHERE section_id = :s", 'Section does not exist', s=section_id)
    if data_type not in ('string', 'number', 'date', 'boolean'):
        raise ProcError('Invalid data type. Must be: string, number, date, or boolean')
    if not name or ' ' in name:
        raise ProcError('Field name is required and cannot contain spaces')
    fid = _new_id()
    _exec(conn, """INSERT INTO field (field_id, section_id, name, display_name, data_type, is_required, is_currency,
                                      ordinal, calculation_formula)
                   VALUES (:f, :s, :n, :d, :ty, :r, :c, :o, :calc)""",
          f=fid, s=section_id, n=name, d=display_name, ty=data_type, r=bool(is_required), c=bool(is_currency),
          o=ordinal or 0, calc=formula)
    return [[{'field_id': fid}]]


@proc('sp_delete_field')
def delete_field(conn, field_id):
    if not _exec(conn, "DELETE FROM field WHERE field_id = :f", f=field_id):
        raise ProcError('Field does not exist')
    return []


@proc('sp_get_template_total_field')
def get_template_total_field(conn, template_id, version):
    return [_rows(conn, "SELECT total_field_id FROM template WHERE template_id = :t AND version = :v", t=template_id, v=version)]


@proc('sp_set_template_total_field')
def set_template_total_field(conn, template_id, version, field_id):
    _require(conn, "SELECT 1 FROM template WHERE template_id = :t AND version = :v", 'Template version does not exist',
             t=template_id, v=version)
    if field_id:
        _require(conn, """SELECT 1 FROM field f JOIN section s ON f.section_id = s.section_id
                          WHERE f.field_id = :f AND s.template_id = :t AND s.template_version = :v""",
                 'Field does not belong to this template', f=field_id, t=template_id, v=version)
    _exec(conn, "UPDATE template SET total_field_id = :f WHERE template_id = :t AND version = :v",
          f=field_id or None, t=template_id, v=version)
    return []


def _template_archived(conn, template_id, org_id, archived):
    rows = _rows(conn, "SELECT version, name, is_archived FROM template WHERE template_id = :t AND org_id = :o",
                 t=template_id, o=org_id)
    if not rows:
        raise ProcError('Template does not exist or does not belong to organization')
    n = _exec(conn, "UPDATE template SET is_archived = :a WHERE template_id = :t", t=template_id, a=archived)
    for r in rows:
        if r['is_archived'] != archived:
            _audit(conn, org_id, 'template', f"{template_id}:{r['version']}", 'UPDATE', 'is_archived',
                   int(r['is_archived']), int(archived), f"Template: {r['name']} v{r['version']}")
    return [[{'rows_affected': n}]]


@proc('sp_archive_template')
def archive_template(conn, template_id, org_id):
    return _template_archived(conn, template_id, org_id, True)


@proc('sp_unarchive_template')
def unarchive_template(conn, template_id, org_id):
    return _template_archived(conn, template_id, org_id, False)


@proc('sp_get_template_layout')
def get_template_layout(conn, template_id, org_id):
    return [_rows(conn, "SELECT layout FROM template_layout WHERE template_id = :t AND org_id = :o", t=template_id, o=org_id)]


@proc('sp_save_template_layout')
def save_template_layout(conn, template_id, org_id, layout):
    _require(conn, "SELECT 1 FROM template WHERE template_id = :t AND org_id = :o", 'Template does not exist',
             t=template_id, o=org_id)
    _exec(conn, """INSERT INTO template_layout (template_id, org_id, layout) VALUES (:t, :o, CAST(:l AS jsonb))
                   ON CONFLICT (template_id) DO UPDATE SET layout = EXCLUDED.layout, updated_at = now()""",
          t=template_id, o=org_id, l=_json(layout))
    return []


# ================================================================ Documents


@proc('sp_create_invoice')
def create_invoice(conn, org_id, customer_id, template_id, _out1=None, _out2=None):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o",
             'Customer does not exist or does not belong to organization', c=customer_id, o=org_id)
    version = _latest_version(conn, template_id, org_id)
    if version is None:
        raise ProcError('Template does not exist or does not belong to organization')
    iid = _new_id()
    _exec(conn, """INSERT INTO invoice (invoice_id, org_id, customer_id, template_id, template_version, status)
                   VALUES (:i, :o, :c, :t, :v, 'draft')""", i=iid, o=org_id, c=customer_id, t=template_id, v=version)
    return [[{'invoice_id': iid, 'template_version': version}]]


@proc('sp_init_document')
def init_document(conn, invoice_id, org_id, doc_type, doc_number, fiscal_year, source_invoice_id):
    if doc_type not in ('quote', 'proforma', 'invoice', 'export_invoice'):
        raise ProcError('Unknown document type')
    _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i AND org_id = :o", 'Document does not exist',
             i=invoice_id, o=org_id)
    _exec(conn, """UPDATE invoice SET doc_type = :t, doc_number = :n, fiscal_year = :fy, source_invoice_id = :s
                   WHERE invoice_id = :i""", i=invoice_id, t=doc_type, n=doc_number, fy=fiscal_year, s=source_invoice_id)
    return []


@proc('sp_update_document_settings')
def update_document_settings(conn, invoice_id, org_id, doc_number, tax_mode, tax_rate, advance_percent, advance_basis, details):
    if tax_mode not in ('none', 'cgst_sgst', 'igst', 'lut'):
        raise ProcError('Unknown tax mode')
    if advance_basis not in ('pre_tax', 'total'):
        raise ProcError('Unknown advance basis')
    _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i AND org_id = :o", 'Document does not exist',
             i=invoice_id, o=org_id)
    _exec(conn, """UPDATE invoice SET doc_number = :n, tax_mode = :tm, tax_rate = COALESCE(:tr, 0),
                   advance_percent = :ap, advance_basis = :ab, details = CAST(:d AS jsonb) WHERE invoice_id = :i""",
          i=invoice_id, n=doc_number, tm=tax_mode, tr=tax_rate, ap=advance_percent, ab=advance_basis,
          d=_json(details) or '{}')
    return []


@proc('sp_update_invoice_dates')
def update_invoice_dates(conn, invoice_id, issue_date, due_date):
    _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i", 'Invoice does not exist', i=invoice_id)
    _exec(conn, """UPDATE invoice SET issue_date = COALESCE(CAST(:a AS date), issue_date),
                   due_date = COALESCE(CAST(:b AS date), due_date) WHERE invoice_id = :i""",
          i=invoice_id, a=issue_date or None, b=due_date or None)
    return []


def _status_change(conn, invoice_id, new_status, where=''):
    row = _one(conn, """SELECT i.org_id, i.status, i.total_amount, c.name FROM invoice i
                        JOIN customer c ON c.customer_id = i.customer_id WHERE i.invoice_id = :i""", i=invoice_id)
    if not row:
        raise ProcError('Invoice does not exist')
    if row['status'] == new_status:
        return
    if _exec(conn, f"UPDATE invoice SET status = :s WHERE invoice_id = :i {where}", i=invoice_id, s=new_status):
        _audit(conn, row['org_id'], 'invoice', invoice_id, 'UPDATE', 'status', row['status'], new_status,
               f"Customer: {row['name']} | Amount: {row['total_amount']}")


@proc('sp_update_invoice_status')
def update_invoice_status(conn, invoice_id, status):
    _status_change(conn, invoice_id, status)
    return []


@proc('sp_set_invoice_total')
def set_invoice_total(conn, invoice_id, total):
    _exec(conn, "UPDATE invoice SET total_amount = COALESCE(:t, 0) WHERE invoice_id = :i", i=invoice_id, t=total)
    return []


TOTAL_LABELS = {'total': 1, 'grand total': 2, 'grand_total': 2, 'invoice total': 3, 'invoice_total': 3, 'amount': 4}


@proc('sp_update_invoice_total')
def update_invoice_total(conn, invoice_id):
    """Stored total from the template's total field (or the best-guess total field)."""
    total_field = (_one(conn, f"""SELECT t.total_field_id FROM invoice i {TEMPLATE_JOIN.replace('LEFT ', '')}
                                  WHERE i.invoice_id = :i""", i=invoice_id) or {}).get('total_field_id')
    if not total_field:
        fields = _rows(conn, """SELECT f.field_id, lower(f.display_name) AS label FROM invoice i
                                JOIN section s ON s.template_id = i.template_id AND s.template_version = i.template_version
                                JOIN field f ON f.section_id = s.section_id
                                WHERE i.invoice_id = :i AND f.data_type = 'number' AND s.section_type = 'normal'""",
                       i=invoice_id)
        ranked = sorted((TOTAL_LABELS[f['label']], f['field_id']) for f in fields if f['label'] in TOTAL_LABELS)
        total_field = ranked[0][1] if ranked else None
    if total_field:
        total = _one(conn, """SELECT COALESCE(SUM(val_number), 0) AS t FROM invoice_value
                              WHERE invoice_id = :i AND field_id = :f AND ordinal = 0""", i=invoice_id, f=total_field)['t']
    else:
        total = _one(conn, """SELECT COALESCE(SUM(iv.val_number), 0) AS t FROM invoice_value iv
                              JOIN field f ON iv.field_id = f.field_id JOIN section s ON f.section_id = s.section_id
                              WHERE iv.invoice_id = :i AND f.data_type = 'number' AND s.section_type = 'normal'
                                AND iv.ordinal = 0""", i=invoice_id)['t']
    _exec(conn, "UPDATE invoice SET total_amount = :t WHERE invoice_id = :i", i=invoice_id, t=total)
    return []


@proc('sp_save_invoice_value')
def save_invoice_value(conn, invoice_id, field_id, val_string, val_number, val_date, val_boolean, ordinal):
    _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i", 'Invoice does not exist', i=invoice_id)
    ordinal = ordinal or 0
    params = dict(i=invoice_id, f=field_id, s=val_string, n=val_number, d=val_date or None,
                  b=None if val_boolean is None else bool(val_boolean), o=ordinal)
    updated = _exec(conn, """UPDATE invoice_value SET val_string = :s, val_number = :n, val_date = CAST(:d AS date),
                             val_boolean = :b WHERE invoice_id = :i AND field_id = :f AND ordinal = :o""", **params)
    if not updated:
        _exec(conn, """INSERT INTO invoice_value (invoice_id, field_id, val_string, val_number, val_date, val_boolean, ordinal)
                       VALUES (:i, :f, :s, :n, CAST(:d AS date), :b, :o)""", **params)
    return []


@proc('sp_delete_invoice_values_by_fields')
def delete_invoice_values_by_fields(conn, invoice_id, field_ids):
    """field_ids: a list, or the old comma-separated quoted string."""
    if isinstance(field_ids, str):
        field_ids = [f.strip().strip("'") for f in field_ids.split(',') if f.strip()]
    if not field_ids:
        return [[{'rows_deleted': 0}]]
    n = _exec(conn, "DELETE FROM invoice_value WHERE invoice_id = :i AND field_id = ANY(CAST(:f AS uuid[]))",
              i=invoice_id, f=list(field_ids))
    return [[{'rows_deleted': n}]]


@proc('sp_delete_invoice')
def delete_invoice(conn, invoice_id):
    _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i", 'Invoice does not exist', i=invoice_id)
    _exec(conn, "DELETE FROM payment WHERE invoice_id = :i", i=invoice_id)
    _exec(conn, "DELETE FROM invoice WHERE invoice_id = :i", i=invoice_id)
    return []


@proc('sp_get_invoice_details')
def get_invoice_details(conn, invoice_id):
    header = _rows(conn, f"""SELECT i.invoice_id, i.org_id, i.doc_type, i.doc_number, i.fiscal_year, i.source_invoice_id,
                                    i.project_id, i.tax_mode, i.tax_rate, i.advance_percent, i.advance_basis, i.details,
                                    i.total_amount,
                                    o.name AS organization_name, o.street_address AS organization_street_address,
                                    o.city AS organization_city, o.state AS organization_state,
                                    o.zip_code AS organization_zip_code, o.country AS organization_country,
                                    o.profile AS organization_profile,
                                    i.customer_id, c.name AS customer_name, c.tax_id AS customer_tax_id,
                                    c.custom AS customer_custom, c.street_address AS customer_street_address,
                                    c.city AS customer_city, c.state AS customer_state, c.zip_code AS customer_zip_code,
                                    c.country AS customer_country,
                                    i.template_id, i.template_version, t.name AS template_name,
                                    {CURRENCY} AS currency_code, i.issue_date, i.due_date, i.status
                             FROM invoice i JOIN organization o ON i.org_id = o.org_id
                             JOIN customer c ON i.customer_id = c.customer_id {TEMPLATE_JOIN}
                             WHERE i.invoice_id = CAST(:i AS uuid)""", i=_as_uuid(invoice_id))
    if not header:
        return []
    values = _rows(conn, """SELECT iv.value_id, iv.field_id, f.name AS field_name, f.display_name AS field_display_name,
                                   f.display_name AS field_label, f.data_type, f.calculation_formula, f.is_currency,
                                   s.name AS section_name, s.display_name AS section_display_name,
                                   s.display_name AS section_title, s.ordinal AS section_ordinal, s.section_type,
                                   f.ordinal AS field_ordinal, iv.ordinal AS value_ordinal,
                                   iv.val_string, iv.val_number, iv.val_date, iv.val_boolean
                            FROM invoice_value iv LEFT JOIN field f ON iv.field_id = f.field_id
                            LEFT JOIN section s ON f.section_id = s.section_id
                            WHERE iv.invoice_id = :i
                            ORDER BY s.ordinal, s.section_type, iv.ordinal, f.ordinal""", i=invoice_id)
    return [header, values]


def _as_uuid(value):
    """None for ids that aren't UUIDs (old links, typos), so lookups find nothing instead of erroring."""
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError):
        return None


@proc('sp_get_document_type')
def get_document_type(conn, invoice_id):
    return [_rows(conn, "SELECT invoice_id, doc_type FROM invoice WHERE invoice_id = CAST(:i AS uuid)", i=_as_uuid(invoice_id))]


DOC_LIST = f"""SELECT i.invoice_id, i.doc_type, i.doc_number, i.source_invoice_id, i.customer_id, c.name AS customer_name,
                     {CUSTOMER_SITE} AS customer_site,
                      i.template_id, t.name AS template_name, {CURRENCY} AS currency_code, i.issue_date, i.due_date,
                      i.status, {PAID} AS paid_amount, i.total_amount, i.project_id
               FROM invoice i JOIN customer c ON i.customer_id = c.customer_id {TEMPLATE_JOIN}"""


@proc('sp_list_invoices')
def list_invoices(conn, org_id, status, limit, offset):
    return [_rows(conn, f"""{DOC_LIST} WHERE i.org_id = :o AND (CAST(:s AS text) IS NULL OR i.status = :s)
                            ORDER BY i.issue_date DESC NULLS LAST, i.invoice_id DESC LIMIT :l OFFSET :off""",
                  o=org_id, s=status, l=limit or 50, off=offset or 0)]


@proc('sp_get_invoice_payments')
def get_invoice_payments(conn, invoice_id):
    return [_rows(conn, """SELECT payment_id, amount, method, reference_number, payment_date, received_amount, received_currency
                           FROM payment WHERE invoice_id = :i ORDER BY payment_date DESC""", i=invoice_id)]


@proc('sp_record_payment')
def record_payment(conn, invoice_id, amount, method, reference, _out=None):
    row = _one(conn, "SELECT org_id FROM invoice WHERE invoice_id = :i", i=invoice_id)
    if not row:
        raise ProcError('Invoice does not exist')
    if amount is None or float(amount) <= 0:
        raise ProcError('Payment amount must be greater than zero')
    pid = _new_id()
    _exec(conn, "INSERT INTO payment (payment_id, invoice_id, amount, method, reference_number) VALUES (:p, :i, :a, :m, :r)",
          p=pid, i=invoice_id, a=amount, m=method, r=reference)
    _audit(conn, row['org_id'], 'payment', pid, 'INSERT', 'amount', None, amount,
           f"Invoice: {invoice_id} | Method: {method or 'N/A'} | Reference: {reference or 'N/A'}")
    update_invoice_total(conn, invoice_id)
    paid_up = _one(conn, f"SELECT {PAID} >= i.total_amount AS ok FROM invoice i WHERE i.invoice_id = :i", i=invoice_id)
    if paid_up and paid_up['ok']:
        _status_change(conn, invoice_id, 'paid')
    return [[{'payment_id': pid}]]


@proc('sp_set_payment_details')
def set_payment_details(conn, payment_id, invoice_id, payment_date, received_amount, received_currency):
    _require(conn, "SELECT 1 FROM payment WHERE payment_id = :p AND invoice_id = :i", 'Payment does not exist',
             p=payment_id, i=invoice_id)
    _exec(conn, """UPDATE payment SET payment_date = COALESCE(CAST(:d AS timestamptz), payment_date),
                   received_amount = :a, received_currency = :c WHERE payment_id = :p""",
          p=payment_id, d=payment_date or None, a=received_amount, c=received_currency)
    return []


@proc('sp_list_org_payments')
def list_org_payments(conn, org_id, since):
    return [_rows(conn, f"""SELECT p.payment_id, p.invoice_id, p.amount, p.payment_date, p.received_amount,
                                   p.received_currency, i.doc_type, i.doc_number, c.name AS customer_name,
                                   {CURRENCY} AS currency_code
                            FROM payment p JOIN invoice i ON p.invoice_id = i.invoice_id
                            JOIN customer c ON i.customer_id = c.customer_id {TEMPLATE_JOIN}
                            WHERE i.org_id = :o AND (CAST(:s AS date) IS NULL OR p.payment_date >= CAST(:s AS date))
                            ORDER BY p.payment_date DESC""", o=org_id, s=since)]


@proc('sp_get_revenue_timeseries')
def get_revenue_timeseries(conn, org_id):
    return [_rows(conn, """SELECT to_char(COALESCE(issue_date, current_date), 'YYYY-MM') AS month,
                                  to_char(COALESCE(issue_date, current_date), 'Mon YYYY') AS month_label,
                                  CAST(SUM(total_amount) AS NUMERIC(15, 2)) AS revenue
                           FROM invoice WHERE org_id = :o AND status IN ('paid', 'pending') AND total_amount > 0
                           GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 12""", o=org_id)]


@proc('sp_get_dashboard_stats')
def get_dashboard_stats(conn, org_id):
    return [_rows(conn, """SELECT
        COALESCE(SUM(total_amount) FILTER (WHERE status IN ('paid', 'pending')), 0) AS total_revenue,
        COUNT(*) FILTER (WHERE status = 'pending') AS pending_count,
        COUNT(*) FILTER (WHERE status = 'paid') AS paid_count,
        COUNT(*) FILTER (WHERE status IN ('pending', 'draft') AND due_date < current_date) AS overdue_count,
        COUNT(*) AS total_invoices,
        COALESCE(SUM(total_amount) FILTER (WHERE status IN ('paid', 'pending')
                 AND date_trunc('month', issue_date) = date_trunc('month', current_date)), 0) AS revenue_this_month,
        COALESCE(SUM(total_amount) FILTER (WHERE status IN ('paid', 'pending')
                 AND date_trunc('month', issue_date) = date_trunc('month', current_date - interval '1 month')), 0)
                 AS revenue_last_month,
        COUNT(*) FILTER (WHERE date_trunc('month', issue_date) = date_trunc('month', current_date)) AS invoices_created_this_month,
        (SELECT COALESCE(SUM(p.amount), 0) FROM payment p JOIN invoice x ON x.invoice_id = p.invoice_id
         WHERE x.org_id = :o AND date_trunc('month', p.payment_date) = date_trunc('month', now())) AS money_received_this_month,
        COALESCE(SUM(total_amount) FILTER (WHERE status = 'pending'
                 AND date_trunc('month', issue_date) = date_trunc('month', current_date)), 0) AS pending_money_this_month
        FROM invoice WHERE org_id = :o""", o=org_id)]


# ---------------------------------------------------------------- Numbering


@proc('sp_peek_document_number')
def peek_document_number(conn, org_id, doc_type, fy):
    row = _one(conn, "SELECT next_number FROM document_series WHERE org_id = :o AND doc_type = :t AND fiscal_year = :f",
               o=org_id, t=doc_type, f=fy)
    return [[{'number': row['next_number'] if row else 1}]]


@proc('sp_next_document_number')
def next_document_number(conn, org_id, doc_type, fy):
    """Hand out the next number and advance the series, atomically (row lock via UPDATE ... RETURNING)."""
    _exec(conn, """INSERT INTO document_series (org_id, doc_type, fiscal_year, next_number) VALUES (:o, :t, :f, 1)
                   ON CONFLICT DO NOTHING""", o=org_id, t=doc_type, f=fy)
    row = _one(conn, """UPDATE document_series SET next_number = next_number + 1
                        WHERE org_id = :o AND doc_type = :t AND fiscal_year = :f RETURNING next_number - 1 AS number""",
               o=org_id, t=doc_type, f=fy)
    return [[row]]


@proc('sp_set_document_series')
def set_document_series(conn, org_id, doc_type, fy, next_number):
    if not next_number or int(next_number) < 1:
        raise ProcError('Next number must be 1 or more')
    _exec(conn, """INSERT INTO document_series (org_id, doc_type, fiscal_year, next_number) VALUES (:o, :t, :f, :n)
                   ON CONFLICT (org_id, doc_type, fiscal_year) DO UPDATE SET next_number = EXCLUDED.next_number""",
          o=org_id, t=doc_type, f=fy, n=int(next_number))
    return []


# ================================================================ Projects


@proc('sp_create_project')
def create_project(conn, org_id, customer_id, title, reference, notes, user_id):
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o", 'Customer does not exist',
             c=customer_id, o=org_id)
    conn.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {'k': f'project_no:{org_id}'})
    no = _one(conn, "SELECT COALESCE(MAX(project_no), 0) + 1 AS n FROM project WHERE org_id = :o", o=org_id)['n']
    pid = _new_id()
    _exec(conn, """INSERT INTO project (project_id, org_id, customer_id, project_no, title, reference, notes, created_by)
                   VALUES (:p, :o, :c, :n, :t, NULLIF(:r, ''), NULLIF(:no, ''), :u)""",
          p=pid, o=org_id, c=customer_id, n=no, t=title, r=reference or '', no=notes or '', u=user_id)
    return [[{'project_id': pid, 'project_no': no}]]


@proc('sp_update_project')
def update_project(conn, project_id, org_id, title, reference, status, notes):
    if status not in ('open', 'completed', 'cancelled'):
        raise ProcError('Unknown project status')
    _exec(conn, """UPDATE project SET title = :t, reference = NULLIF(:r, ''), status = :s, notes = NULLIF(:n, ''),
                   updated_at = now() WHERE project_id = :p AND org_id = :o""",
          p=project_id, o=org_id, t=title, r=reference or '', s=status, n=notes or '')
    return []


@proc('sp_get_project')
def get_project(conn, project_id, org_id):
    return [_rows(conn, f"""SELECT p.*, c.name AS customer_name, {CUSTOMER_SITE} AS customer_site
                            FROM project p JOIN customer c ON c.customer_id = p.customer_id
                           WHERE p.project_id = CAST(:p AS uuid) AND p.org_id = :o""", p=_as_uuid(project_id), o=org_id)]


@proc('sp_list_projects')
def list_projects(conn, org_id, customer_id, status):
    return [_rows(conn, f"""SELECT p.project_id, p.project_no, p.title, p.reference, p.status, p.customer_id,
                                  c.name AS customer_name, {CUSTOMER_SITE} AS customer_site, p.created_at, p.updated_at,
                                  (SELECT COUNT(*) FROM invoice i WHERE i.project_id = p.project_id) AS document_count,
                                  (SELECT COUNT(*) FROM attachment a WHERE a.project_id = p.project_id) AS file_count,
                                  (SELECT COUNT(*) FROM email_thread e WHERE e.project_id = p.project_id) AS thread_count,
                                  (SELECT MAX(i.issue_date) FROM invoice i WHERE i.project_id = p.project_id) AS last_issue_date
                           FROM project p JOIN customer c ON c.customer_id = p.customer_id
                           WHERE p.org_id = :o AND (CAST(:c AS uuid) IS NULL OR p.customer_id = CAST(:c AS uuid)
                                                    OR c.parent_id = CAST(:c AS uuid))      -- and its sites'
                             AND (CAST(:s AS text) IS NULL OR p.status = :s)
                           ORDER BY p.project_no DESC""", o=org_id, c=customer_id, s=status)]


@proc('sp_delete_project')
def delete_project(conn, project_id, org_id):
    _exec(conn, "DELETE FROM project WHERE project_id = :p AND org_id = :o", p=project_id, o=org_id)
    return []


@proc('sp_set_invoice_project')
def set_invoice_project(conn, invoice_id, org_id, project_id):
    if project_id:
        _require(conn, """SELECT 1 FROM project p JOIN invoice i ON i.customer_id = p.customer_id AND i.org_id = p.org_id
                          WHERE p.project_id = :p AND i.invoice_id = :i AND p.org_id = :o""",
                 'The project must belong to the same customer', p=project_id, i=invoice_id, o=org_id)
    _exec(conn, "UPDATE invoice SET project_id = :p WHERE invoice_id = :i AND org_id = :o",
          p=project_id or None, i=invoice_id, o=org_id)
    return []


@proc('sp_get_invoice_project')
def get_invoice_project(conn, invoice_id, org_id):
    return [_rows(conn, "SELECT project_id FROM invoice WHERE invoice_id = :i AND org_id = :o", i=invoice_id, o=org_id)]


@proc('sp_list_org_document_links')
def list_org_document_links(conn, org_id):
    return [_rows(conn, """SELECT invoice_id, doc_type, doc_number, source_invoice_id, customer_id, project_id,
                                  issue_date, status, details->>'base_number' AS base_number, details->>'subject' AS subject
                           FROM invoice WHERE org_id = :o""", o=org_id)]


# ================================================================ Attachments (files)

ATTACHMENT_LIST = """SELECT a.attachment_id, a.customer_id, c.name AS customer_name, a.project_id, p.project_no,
                            a.invoice_id, i.doc_number, i.doc_type, a.email_message_id, a.kind, a.title, a.reference_no,
                            a.doc_date, a.amount, a.currency, a.notes, a.file_name, a.content_type, a.file_size,
                            a.storage_key, a.content_hash, a.created_at, em.thread_id AS email_thread_id
                     FROM attachment a JOIN customer c ON c.customer_id = a.customer_id
                     LEFT JOIN project p ON p.project_id = a.project_id
                     LEFT JOIN invoice i ON i.invoice_id = a.invoice_id
                     LEFT JOIN email_message em ON em.message_id = a.email_message_id"""


def sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data or b'').hexdigest()


@proc('sp_add_attachment')
def add_attachment(conn, org_id, customer_id, project_id, invoice_id, kind, title, reference_no, doc_date, amount,
                   currency, notes, file_name, content_type, data, user_id, email_message_id=None):
    """Store the bytes in object storage, then the record."""
    import storage
    _require(conn, "SELECT 1 FROM customer WHERE customer_id = :c AND org_id = :o", 'Customer does not exist',
             c=customer_id, o=org_id)
    if project_id:
        _require(conn, "SELECT 1 FROM project WHERE project_id = :p AND org_id = :o AND customer_id = :c",
                 'The project must belong to the same customer', p=project_id, o=org_id, c=customer_id)
    if invoice_id:
        _require(conn, "SELECT 1 FROM invoice WHERE invoice_id = :i AND org_id = :o AND customer_id = :c",
                 'The document must belong to the same customer', i=invoice_id, o=org_id, c=customer_id)
    aid = _new_id()
    key = storage.put(f'{org_id}/{aid}/{file_name}', data, content_type)
    _exec(conn, """INSERT INTO attachment (attachment_id, org_id, customer_id, project_id, invoice_id, email_message_id,
                                           kind, title, reference_no, doc_date, amount, currency, notes, file_name,
                                           content_type, file_size, storage_key, content_hash, uploaded_by)
                   VALUES (:a, :o, :c, :p, :i, :m, :k, :t, NULLIF(:r, ''), CAST(:d AS date), :am, NULLIF(:cur, ''),
                           NULLIF(:n, ''), :fn, :ct, :sz, :key, :h, :u)""",
          a=aid, o=org_id, c=customer_id, p=project_id or None, i=invoice_id or None, m=email_message_id, k=kind,
          t=title, r=reference_no or '', d=doc_date or None, am=amount, cur=currency or '', n=notes or '',
          fn=file_name, ct=content_type, sz=len(data), key=key, h=sha256(data), u=user_id)
    return [[{'attachment_id': aid}]]


@proc('sp_list_attachments')
def list_attachments(conn, org_id, customer_id, project_id, invoice_id):
    return [_rows(conn, f"""{ATTACHMENT_LIST}
                            WHERE a.org_id = :o AND (CAST(:c AS uuid) IS NULL OR a.customer_id = CAST(:c AS uuid))
                              AND (CAST(:p AS uuid) IS NULL OR a.project_id = CAST(:p AS uuid))
                              AND (CAST(:i AS uuid) IS NULL OR a.invoice_id = CAST(:i AS uuid))
                            ORDER BY COALESCE(a.doc_date, CAST(a.created_at AS date)) DESC, a.created_at DESC""",
                  o=org_id, c=customer_id, p=project_id, i=invoice_id)]


@proc('sp_get_attachment')
def get_attachment(conn, attachment_id, org_id):
    """The record plus its bytes (data) from object storage."""
    import storage
    rows = _rows(conn, f"{ATTACHMENT_LIST} WHERE a.attachment_id = CAST(:a AS uuid) AND a.org_id = :o",
                 a=_as_uuid(attachment_id), o=org_id)
    for r in rows:
        r['data'] = storage.get(r['storage_key'])
    return [rows]


@proc('sp_link_attachment')
def link_attachment(conn, attachment_id, org_id, project_id):
    if project_id:
        _require(conn, """SELECT 1 FROM project p JOIN attachment a ON a.customer_id = p.customer_id AND a.org_id = p.org_id
                          WHERE p.project_id = :p AND a.attachment_id = :a AND p.org_id = :o""",
                 'The project must belong to the same customer', p=project_id, a=attachment_id, o=org_id)
    _exec(conn, "UPDATE attachment SET project_id = :p WHERE attachment_id = :a AND org_id = :o",
          p=project_id or None, a=attachment_id, o=org_id)
    return []


@proc('sp_delete_attachment')
def delete_attachment(conn, attachment_id, org_id):
    import storage
    row = _one(conn, "DELETE FROM attachment WHERE attachment_id = :a AND org_id = :o RETURNING storage_key",
               a=attachment_id, o=org_id)
    if row:
        storage.delete(row['storage_key'])
    return []


# ================================================================ Events and notifications


@proc('sp_record_event')
def record_event(conn, org_id, project_id, kind, title, body, link, actor_user_id, notify=True):
    """An event, plus (unless notify is False) an unread notification for each active owner
    and admin, except whoever did it."""
    eid = _new_id()
    _exec(conn, """INSERT INTO event (event_id, org_id, project_id, actor_user_id, kind, title, body, link)
                   VALUES (:e, :o, :p, :a, :k, :t, :b, :l)""",
          e=eid, o=org_id, p=project_id or None, a=actor_user_id or None, k=kind, t=title[:300], b=body, l=link)
    if not notify:
        return [[{'event_id': eid}]]
    _exec(conn, """INSERT INTO notification (event_id, user_id)
                   SELECT :e, uo.user_id FROM user_organization uo
                   WHERE uo.org_id = :o AND uo.status = 'active' AND uo.role IN ('owner', 'admin')
                     AND (CAST(:a AS uuid) IS NULL OR uo.user_id <> CAST(:a AS uuid))""",
          e=eid, o=org_id, a=actor_user_id or None)
    return [[{'event_id': eid}]]


@proc('sp_list_notifications')
def list_notifications(conn, user_id, org_id, limit, unread_only):
    return [_rows(conn, """SELECT n.notification_id, n.read_at, e.event_id, e.kind, e.title, e.body, e.link, e.created_at,
                                  e.project_id, p.project_no, p.title AS project_title, u.email AS actor_email
                           FROM notification n JOIN event e ON e.event_id = n.event_id
                           LEFT JOIN project p ON p.project_id = e.project_id
                           LEFT JOIN users u ON u.user_id = e.actor_user_id
                           WHERE n.user_id = :u AND e.org_id = :o AND (NOT :unread OR n.read_at IS NULL)
                           ORDER BY e.created_at DESC LIMIT :l""",
                  u=user_id, o=org_id, l=limit or 50, unread=bool(unread_only))]


@proc('sp_count_unread_notifications')
def count_unread_notifications(conn, user_id, org_id):
    return [[_one(conn, """SELECT COUNT(*) AS n FROM notification n JOIN event e ON e.event_id = n.event_id
                           WHERE n.user_id = :u AND e.org_id = :o AND n.read_at IS NULL""", u=user_id, o=org_id)]]


@proc('sp_mark_notifications_read')
def mark_notifications_read(conn, user_id, org_id, notification_id):
    """One notification, or all of the user's in the org when notification_id is None."""
    _exec(conn, """UPDATE notification n SET read_at = now() FROM event e
                   WHERE e.event_id = n.event_id AND n.user_id = :u AND e.org_id = :o AND n.read_at IS NULL
                     AND (CAST(:n AS uuid) IS NULL OR n.notification_id = CAST(:n AS uuid))""",
          u=user_id, o=org_id, n=_as_uuid(notification_id) if notification_id else None)
    return []


@proc('sp_get_notification')
def get_notification(conn, notification_id, user_id):
    return [_rows(conn, """SELECT n.notification_id, e.org_id, e.link FROM notification n JOIN event e ON e.event_id = n.event_id
                           WHERE n.notification_id = CAST(:n AS uuid) AND n.user_id = :u""",
                  n=_as_uuid(notification_id), u=user_id)]


@proc('sp_list_project_events')
def list_project_events(conn, project_id, org_id, limit):
    return [_rows(conn, """SELECT e.event_id, e.kind, e.title, e.body, e.link, e.created_at, u.email AS actor_email
                           FROM event e LEFT JOIN users u ON u.user_id = e.actor_user_id
                           WHERE e.project_id = :p AND e.org_id = :o ORDER BY e.created_at DESC LIMIT :l""",
                  p=project_id, o=org_id, l=limit or 50)]


# ================================================================ Email


@proc('sp_upsert_email_account')
def upsert_email_account(conn, org_id, address, env_prefix):
    return [_rows(conn, """INSERT INTO email_account (org_id, address, env_prefix) VALUES (:o, lower(:a), :p)
                           ON CONFLICT (org_id, address) DO UPDATE SET env_prefix = EXCLUDED.env_prefix
                           RETURNING account_id, org_id, address, env_prefix, folder_state, last_synced_at, last_error""",
                  o=org_id, a=address, p=env_prefix)]


@proc('sp_list_email_accounts')
def list_email_accounts(conn, org_id):
    return [_rows(conn, """SELECT account_id, org_id, address, env_prefix, folder_state, last_synced_at, last_error,
                                  (SELECT COUNT(*) FROM email_message m WHERE m.account_id = a.account_id) AS message_count
                           FROM email_account a WHERE CAST(:o AS uuid) IS NULL OR org_id = CAST(:o AS uuid)
                           ORDER BY address""", o=org_id)]


@proc('sp_save_email_account_state')
def save_email_account_state(conn, account_id, folder_state, error):
    _exec(conn, """UPDATE email_account SET folder_state = CAST(:s AS jsonb), last_error = CAST(:e AS text),
                   last_synced_at = CASE WHEN CAST(:e AS text) IS NULL THEN now() ELSE last_synced_at END
                   WHERE account_id = :a""",
          a=account_id, s=_json(folder_state) or '{}', e=error)
    return []


@proc('sp_find_threads_by_headers')
def find_threads_by_headers(conn, org_id, headers):
    if not headers:
        return []
    return [_rows(conn, """SELECT DISTINCT m.thread_id, t.project_id, t.customer_id FROM email_message m
                           JOIN email_thread t ON t.thread_id = m.thread_id
                           WHERE m.org_id = :o AND m.message_id_header = ANY(:h)""", o=org_id, h=list(headers))]


@proc('sp_email_message_exists')
def email_message_exists(conn, org_id, header):
    return [_rows(conn, "SELECT message_id, thread_id FROM email_message WHERE org_id = :o AND message_id_header = :h",
                  o=org_id, h=header)]


@proc('sp_find_thread_by_subject')
def find_thread_by_subject(conn, org_id, subject, customer_id, since):
    """A recent thread with the same (normalized) subject and customer."""
    return [_rows(conn, """SELECT thread_id, project_id, customer_id FROM email_thread
                           WHERE org_id = :o AND lower(subject) = lower(:s)
                             AND customer_id IS NOT DISTINCT FROM CAST(:c AS uuid)
                             AND COALESCE(last_message_at, created_at) >= CAST(:since AS timestamptz)
                           ORDER BY last_message_at DESC NULLS LAST LIMIT 1""",
                  o=org_id, s=subject, c=customer_id, since=since)]


@proc('sp_create_email_thread')
def create_email_thread(conn, org_id, subject, project_id, customer_id, linked_by):
    tid = _new_id()
    _exec(conn, """INSERT INTO email_thread (thread_id, org_id, subject, project_id, customer_id, linked_by)
                   VALUES (:t, :o, :s, :p, :c, :l)""",
          t=tid, o=org_id, s=(subject or '(no subject)')[:500], p=project_id, c=customer_id,
          l=linked_by if project_id else None)
    return [[{'thread_id': tid}]]


@proc('sp_add_email_message')
def add_email_message(conn, org_id, account_id, thread_id, m):
    """m: dict from emailsync.parse_message. Returns the new message_id, or nothing if it was already stored."""
    row = _one(conn, """INSERT INTO email_message (org_id, account_id, thread_id, message_id_header, in_reply_to,
                                                   references_header, uid, from_address, from_name, to_addresses,
                                                   cc_addresses, subject, sent_at, body_text, direction)
                        VALUES (:o, :a, :t, :mid, :irt, :refs, :uid, :fa, :fn, :to, :cc, :s, :at, :body, :dir)
                        ON CONFLICT (org_id, message_id_header) DO NOTHING RETURNING message_id""",
               o=org_id, a=account_id, t=thread_id, mid=m['message_id'], irt=m.get('in_reply_to'),
               refs=' '.join(m.get('references') or []) or None, uid=m.get('uid'), fa=m.get('from_address'),
               fn=m.get('from_name'), to=', '.join(m.get('to') or []), cc=', '.join(m.get('cc') or []),
               s=(m.get('subject') or '')[:500], at=m.get('sent_at'), body=m.get('body_text'),
               dir=m.get('direction', 'in'))
    if not row:
        return []
    _exec(conn, """UPDATE email_thread SET message_count = message_count + 1,
                   last_message_at = GREATEST(COALESCE(last_message_at, CAST(:at AS timestamptz)), CAST(:at AS timestamptz))
                   WHERE thread_id = :t""", t=thread_id, at=m.get('sent_at'))
    return [[row]]


@proc('sp_add_email_file')
def add_email_file(conn, org_id, message_id, file_name, content_type, data):
    import storage
    fid = _new_id()
    key = storage.put(f'{org_id}/email/{fid}/{file_name}', data, content_type)
    _exec(conn, """INSERT INTO email_file (file_id, org_id, message_id, file_name, content_type, file_size, storage_key,
                                           content_hash)
                   VALUES (:f, :o, :m, :n, :c, :s, :k, :h)""",
          f=fid, o=org_id, m=message_id, n=file_name[:255], c=(content_type or 'application/octet-stream')[:100],
          s=len(data), k=key, h=sha256(data))
    return [[{'file_id': fid}]]


@proc('sp_list_thread_files')
def list_thread_files(conn, org_id, thread_id, message_id=None):
    """A thread's email files (or one message's), with the message they came in, oldest first."""
    return [_rows(conn, """SELECT f.file_id, f.file_name, f.content_type, f.file_size, f.storage_key, f.content_hash,
                                  m.message_id, m.subject, m.sent_at, m.direction, m.from_name, m.from_address
                           FROM email_file f JOIN email_message m ON m.message_id = f.message_id
                           WHERE f.org_id = :o AND m.thread_id = CAST(:t AS uuid)
                             AND (CAST(:m AS uuid) IS NULL OR m.message_id = CAST(:m AS uuid))
                           ORDER BY m.sent_at NULLS LAST, m.created_at, f.file_name""",
                  o=org_id, t=_as_uuid(thread_id), m=message_id)]


@proc('sp_project_file_hashes')
def project_file_hashes(conn, org_id, project_id):
    """Content hashes of a project's files, filling in any missing ones (files from before hashes) from storage."""
    import storage
    rows = _rows(conn, "SELECT attachment_id, content_hash, storage_key FROM attachment WHERE org_id = :o AND project_id = :p",
                 o=org_id, p=project_id)
    for r in rows:
        if not r['content_hash']:
            r['content_hash'] = sha256(storage.get(r['storage_key']))
            _exec(conn, "UPDATE attachment SET content_hash = :h WHERE attachment_id = :a", h=r['content_hash'],
                  a=r['attachment_id'])
    return [[{'content_hash': r['content_hash']} for r in rows]]


@proc('sp_set_email_file_hash')
def set_email_file_hash(conn, file_id, content_hash):
    _exec(conn, "UPDATE email_file SET content_hash = :h WHERE file_id = :f", f=file_id, h=content_hash)
    return []


@proc('sp_remove_thread_files_from_project')
def remove_thread_files_from_project(conn, org_id, project_id, thread_id):
    """Delete the project files that were copied from this thread's emails (the emails keep theirs)."""
    import storage
    rows = _rows(conn, """DELETE FROM attachment a USING email_message m
                          WHERE a.email_message_id = m.message_id AND m.thread_id = :t
                            AND a.org_id = :o AND a.project_id = :p RETURNING a.storage_key""",
                 o=org_id, p=project_id, t=thread_id)
    for r in rows:
        storage.delete(r['storage_key'])
    return [[{'removed': len(rows)}]]


@proc('sp_get_email_file')
def get_email_file(conn, file_id, org_id):
    import storage
    rows = _rows(conn, "SELECT * FROM email_file WHERE file_id = CAST(:f AS uuid) AND org_id = :o",
                 f=_as_uuid(file_id), o=org_id)
    for r in rows:
        r['data'] = storage.get(r['storage_key'])
    return [rows]


@proc('sp_set_thread_project')
def set_thread_project(conn, thread_id, org_id, project_id, linked_by):
    if project_id:
        _require(conn, "SELECT 1 FROM project WHERE project_id = :p AND org_id = :o", 'Project not found',
                 p=project_id, o=org_id)
    _exec(conn, """UPDATE email_thread SET project_id = CAST(:p AS uuid), linked_by = :l,
                   customer_id = COALESCE((SELECT customer_id FROM project WHERE project_id = CAST(:p AS uuid)), customer_id)
                   WHERE thread_id = :t AND org_id = :o""",
          t=thread_id, o=org_id, p=project_id or None, l=linked_by if project_id else None)
    return []


THREAD_LIST = """SELECT t.thread_id, t.subject, t.project_id, p.project_no, p.title AS project_title, t.customer_id,
                        c.name AS customer_name, t.message_count, t.last_message_at, t.linked_by,
                        (SELECT m.from_name FROM email_message m WHERE m.thread_id = t.thread_id
                         ORDER BY m.sent_at DESC NULLS LAST LIMIT 1) AS last_from_name,
                        (SELECT m.from_address FROM email_message m WHERE m.thread_id = t.thread_id
                         ORDER BY m.sent_at DESC NULLS LAST LIMIT 1) AS last_from_address,
                        (SELECT left(m.body_text, 200) FROM email_message m WHERE m.thread_id = t.thread_id
                         ORDER BY m.sent_at DESC NULLS LAST LIMIT 1) AS snippet,
                        (SELECT COUNT(*) FROM email_file f JOIN email_message m ON m.message_id = f.message_id
                         WHERE m.thread_id = t.thread_id) AS file_count
                 FROM email_thread t LEFT JOIN project p ON p.project_id = t.project_id
                 LEFT JOIN customer c ON c.customer_id = t.customer_id"""


@proc('sp_list_email_threads')
def list_email_threads(conn, org_id, project_id, customer_id, unlinked_only, limit):
    return [_rows(conn, f"""{THREAD_LIST}
                            WHERE t.org_id = :o AND (CAST(:p AS uuid) IS NULL OR t.project_id = CAST(:p AS uuid))
                              AND (CAST(:c AS uuid) IS NULL OR t.customer_id = CAST(:c AS uuid))
                              AND (NOT :u OR t.project_id IS NULL)
                            ORDER BY t.last_message_at DESC NULLS LAST LIMIT :l""",
                  o=org_id, p=project_id, c=customer_id, u=bool(unlinked_only), l=limit or 100)]


@proc('sp_get_email_thread')
def get_email_thread(conn, thread_id, org_id):
    thread = _rows(conn, f"{THREAD_LIST} WHERE t.thread_id = CAST(:t AS uuid) AND t.org_id = :o",
                   t=_as_uuid(thread_id), o=org_id)
    if not thread:
        return []
    messages = _rows(conn, """SELECT m.message_id, m.from_address, m.from_name, m.to_addresses, m.cc_addresses, m.subject,
                                     m.sent_at, m.body_text, m.direction, a.address AS mailbox
                              FROM email_message m JOIN email_account a ON a.account_id = m.account_id
                              WHERE m.thread_id = :t ORDER BY m.sent_at NULLS LAST, m.created_at""", t=thread_id)
    files = _rows(conn, """SELECT f.file_id, f.message_id, f.file_name, f.content_type, f.file_size FROM email_file f
                           JOIN email_message m ON m.message_id = f.message_id WHERE m.thread_id = :t
                           ORDER BY f.file_name""", t=thread_id)
    return [thread, messages, files]


@proc('sp_match_customers_by_email')
def match_customers_by_email(conn, org_id, addresses):
    """Customers whose email domains, portal logins or contacts match any of these addresses."""
    addresses = [a.lower() for a in addresses if a and '@' in a]
    if not addresses:
        return []
    domains = list({a.split('@', 1)[1] for a in addresses})
    return [_rows(conn, """SELECT DISTINCT c.customer_id, c.name, c.parent_id FROM customer c
                           WHERE c.org_id = :o AND NOT c.is_archived AND (
                             EXISTS (SELECT 1 FROM unnest(string_to_array(lower(COALESCE(c.email_domains, '')), ',')) AS d(x)
                                     WHERE trim(d.x) <> '' AND trim(leading '@' from trim(d.x)) = ANY(:d))
                             OR EXISTS (SELECT 1 FROM customer_user cu WHERE cu.customer_id = c.customer_id
                                        AND lower(cu.email) = ANY(:a))
                             OR EXISTS (SELECT 1 FROM customer_contact_assignment cca JOIN person p USING (person_id)
                                        WHERE cca.customer_id = c.customer_id AND lower(p.email) = ANY(:a)))""",
                  o=org_id, d=domains, a=addresses)]


@proc('sp_find_project_by_number')
def find_project_by_number(conn, org_id, number):
    return [_rows(conn, "SELECT project_id, customer_id, status FROM project WHERE org_id = :o AND project_no = :n",
                  o=org_id, n=int(number))]


@proc('sp_list_document_numbers')
def list_document_numbers(conn, org_id):
    """Numbers to look for in email subjects (longer ones only: '037' would match too much)."""
    return [_rows(conn, """SELECT doc_number, project_id, customer_id FROM invoice
                           WHERE org_id = :o AND doc_number IS NOT NULL AND length(doc_number) >= 6
                           ORDER BY length(doc_number) DESC""", o=org_id)]
