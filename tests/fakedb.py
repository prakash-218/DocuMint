"""
In-memory stand-in for the stored procedures the web routes call, so route
tests run without MySQL. Only the procedures the tests exercise are modelled.
"""

import copy

from auth import hash_password

ORG_A, ORG_B = 'a' * 36, 'b' * 36
PASSWORD = 'secret123'
_HASH = hash_password(PASSWORD)


def _field(fid, section_id, section, name, formula=None, section_type='normal', ordinal=0, data_type='number', currency=True):
    return {
        'section_id': section_id, 'section_name': section, 'section_display_name': section.title(),
        'section_title': section.title(), 'section_ordinal': 1 if section_type == 'line_item' else 2,
        'section_type': section_type, 'field_id': fid, 'field_name': name,
        'field_display_name': name.replace('_', ' ').title(), 'label': name.replace('_', ' ').title(),
        'data_type': data_type, 'is_required': 0, 'is_currency': int(currency), 'field_ordinal': ordinal,
        'calculation_formula': formula,
    }


TEMPLATE_FIELDS = [
    _field('F-NAME', 'S-ITEMS', 'items', 'name', section_type='line_item', ordinal=1, data_type='string'),
    _field('F-QTY', 'S-ITEMS', 'items', 'qty', section_type='line_item', ordinal=2, currency=False),
    _field('F-PRICE', 'S-ITEMS', 'items', 'price', section_type='line_item', ordinal=3),
    _field('F-LINE', 'S-ITEMS', 'items', 'total', 'this.price * this.qty', section_type='line_item', ordinal=4),
    _field('F-TOTAL', 'S-TOTAL', 'total', 'total', 'SUM(items.total)', ordinal=1),
    _field('F-TAX', 'S-TOTAL', 'total', 'tax', 'total * 0.1', ordinal=2),
    _field('F-GRAND', 'S-TOTAL', 'total', 'grand_total', 'total + tax', ordinal=3),
]


class FakeDB:
    def __init__(self):
        self.calls = []
        self.total_field = 'F-GRAND'
        self.users = {'alice@a.com': {'user_id': 'U-A', 'email': 'alice@a.com', 'password_hash': _HASH}}
        self.members = {
            'U-A': [{'org_id': ORG_A, 'name': 'Org A', 'domain': 'a.com', 'role': 'owner', 'status': 'active'}],
            'U-B': [{'org_id': ORG_B, 'name': 'Org B', 'domain': 'b.com', 'role': 'owner', 'status': 'active'}],
        }
        self.invoices = {
            'INV-A': {'invoice_id': 'INV-A', 'org_id': ORG_A, 'customer_id': 'C-A', 'status': 'pending',
                      'template_id': 'T-A', 'template_version': 1, 'customer_name': 'Acme',
                      'organization_name': 'Org A', 'issue_date': None, 'due_date': None},
        }
        # (invoice_id, field_id, ordinal) -> val_number; line_total/total deliberately stale
        self.values = {
            ('INV-A', 'F-QTY', 1): 2, ('INV-A', 'F-PRICE', 1): 10, ('INV-A', 'F-LINE', 1): 999,
            ('INV-A', 'F-QTY', 2): 3, ('INV-A', 'F-PRICE', 2): 5,
            ('INV-A', 'F-TOTAL', 0): 999,
        }
        self.payments = {'INV-A': [{'amount': 10, 'payment_date': '2026-01-01', 'method': 'card',
                                    'reference_number': 'R1'}]}

    def written(self):
        writes = ('sp_save_invoice_value', 'sp_update_invoice_total', 'sp_update_invoice_status',
                  'sp_record_payment', 'sp_delete_section', 'sp_delete_field', 'sp_update_member_status')
        return [c for c in self.calls if c[0] in writes]

    def _values_for(self, invoice_id):
        meta = {f['field_id']: f for f in TEMPLATE_FIELDS}
        rows = []
        for (inv, fid, ordinal), number in self.values.items():
            if inv == invoice_id:
                rows.append({**meta[fid], 'field_label': meta[fid]['field_display_name'],
                             'value_ordinal': ordinal, 'val_number': number,
                             'val_string': None, 'val_date': None, 'val_boolean': None})
        return rows

    def execute_proc(self, proc, args=None, fetch=True):
        self.calls.append((proc, args))
        args = args or ()
        if proc == 'sp_get_user_by_email':
            user = self.users.get(args[0])
            return [user] if user else None
        if proc == 'sp_get_user_organizations':
            return copy.deepcopy(self.members.get(args[0], []))
        if proc == 'sp_find_organizations_by_domain':
            return [o for m in self.members.values() for o in m if o['domain'] == args[0]]
        if proc == 'sp_get_invoice_details':
            header = self.invoices.get(args[0])
            return [[dict(header)], self._values_for(args[0])] if header else None
        if proc == 'sp_get_invoice_payments':
            return self.payments.get(args[0], [])
        if proc == 'sp_list_templates':
            return [{'template_id': 'T-A', 'latest_version': 1, 'version': 1}] if args[0] == ORG_A else []
        if proc in ('sp_get_template_fields', 'sp_get_template_fields_by_version'):
            return copy.deepcopy(TEMPLATE_FIELDS) if args[0] == 'T-A' else []
        if proc == 'sp_get_template_total_field':
            return [{'total_field_id': self.total_field}]
        if proc in ('sp_list_invoices', 'sp_get_customer_invoices'):
            owner = 'org_id' if proc == 'sp_list_invoices' else 'customer_id'
            return [{'template_name': 'Standard Invoice', 'total_amount': 38.5, 'paid_amount': 10,
                     'doc_type': 'invoice', **inv}
                    for inv in self.invoices.values() if inv[owner] == args[0]]
        if proc == 'sp_get_document_type':
            inv = self.invoices.get(args[0])
            return [{'invoice_id': args[0], 'doc_type': inv.get('doc_type', 'invoice')}] if inv else None
        if proc == 'sp_list_search_documents':
            return [{'doc_type': 'invoice', 'total_amount': 38.5, 'currency_code': 'USD', **inv}
                    for inv in self.invoices.values() if inv['org_id'] == args[0]]
        if proc == 'sp_get_dashboard_stats':
            return [{'revenue_this_month': 38.5, 'revenue_last_month': 20, 'invoices_created_this_month': 1,
                     'money_received_this_month': 10, 'pending_money_this_month': 28.5}]
        if proc == 'sp_list_org_payments':
            out = []
            for inv_id, pays in self.payments.items():
                inv = self.invoices.get(inv_id)
                if inv and inv['org_id'] == args[0]:
                    out += [{**p, 'invoice_id': inv_id, 'currency_code': inv.get('currency_code', 'USD'),
                             'received_amount': p.get('received_amount'), 'received_currency': p.get('received_currency')}
                            for p in pays if not args[1] or str(p.get('payment_date', ''))[:10] >= args[1]]
            return out
        if proc == 'sp_get_revenue_timeseries':
            return [{'month': '2026-01', 'month_label': 'Jan 2026', 'revenue': 38.5}]
        if proc == 'sp_list_customers':
            return [{'customer_id': 'C-A', 'name': 'Acme', 'tax_id': None, 'city': 'Boston', 'country': 'US',
                     'is_archived': 0, 'created_at': None}] if args[0] == ORG_A else []
        if proc == 'sp_get_customer_details':
            return [[{'customer_id': 'C-A', 'org_id': ORG_A, 'name': 'Acme', 'tax_id': None, 'street_address': None,
                      'city': 'Boston', 'state': 'MA', 'zip_code': None, 'country': 'US', 'created_at': None}], []] \
                if args[0] == 'C-A' else None
        if proc in ('sp_get_customer_users', 'sp_get_pending_members', 'sp_get_audit_log', 'sp_get_org_members'):
            return []
        if proc == 'sp_get_organization_details':
            return [{'org_id': ORG_A, 'name': 'Org A', 'domain': 'a.com'}]
        if proc == 'sp_check_template_version_has_invoices':
            return [{'has_invoices': 0, 'invoice_count': 0}]
        if proc == 'sp_save_invoice_value':
            invoice_id, field_id, _, number, _, _, ordinal = args
            self.values[(invoice_id, field_id, ordinal or 0)] = number
        return None

    def execute_proc_single(self, proc, args=None):
        result = self.execute_proc(proc, args)
        return result[0] if result else None
