
"""
Generate realistic demo data for DocuMint invoice system.

This script creates:
- 2 users with known passwords
- 2 organizations
- Users assigned to organizations
- Templates with sections and fields
- Customers with addresses
- Invoices spanning July 2025 - December 2025
- Some payments

Passwords:
- user1@acme.com: demo123
- user2@techcorp.com: demo123
"""

import sys
import os
from datetime import datetime, timedelta
import random
from decimal import Decimal


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db, DatabaseError
from calculations import calculate_invoice_fields
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


USERS = [
    {
        'email': 'user1@acme.com',
        'password': 'demo123',
        'name': 'John Smith'
    },
    {
        'email': 'user2@techcorp.com',
        'password': 'demo123',
        'name': 'Sarah Johnson'
    }
]

ORGANIZATIONS = [
    {
        'name': 'Acme Corporation',
        'domain': 'acme.com'
    },
    {
        'name': 'TechCorp Solutions',
        'domain': 'techcorp.com'
    }
]


USER_ORG_ASSIGNMENTS = [
    (0, 0, 'owner'),
    (0, 1, 'member'),
    (1, 0, 'member'),
]

CUSTOMERS = {
    'acme.com': [
        {
            'name': 'Global Manufacturing Inc',
            'tax_id': 'TAX-123456',
            'street_address': '123 Industrial Blvd',
            'city': 'Chicago',
            'state': 'IL',
            'zip_code': '60601',
            'country': 'USA'
        },
        {
            'name': 'Digital Services LLC',
            'tax_id': 'TAX-789012',
            'street_address': '456 Tech Park Drive',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78701',
            'country': 'USA'
        },
        {
            'name': 'Retail Partners Co',
            'tax_id': 'TAX-345678',
            'street_address': '789 Commerce Street',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'country': 'USA'
        }
    ],
    'techcorp.com': [
        {
            'name': 'Enterprise Systems Ltd',
            'tax_id': 'TAX-901234',
            'street_address': '321 Business Center',
            'city': 'San Francisco',
            'state': 'CA',
            'zip_code': '94102',
            'country': 'USA'
        },
        {
            'name': 'Cloud Solutions Group',
            'tax_id': 'TAX-567890',
            'street_address': '654 Innovation Way',
            'city': 'Seattle',
            'state': 'WA',
            'zip_code': '98101',
            'country': 'USA'
        }
    ]
}

TEMPLATES = {
    'acme.com': [
        {
            'name': 'Standard Invoice',
            'currency_code': 'USD',
            'sections': [
                {
                    'title': 'Invoice Details',
                    'ordinal': 1,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Invoice Number', 'data_type': 'string', 'is_required': 1, 'ordinal': 1},
                        {'label': 'PO Number', 'data_type': 'string', 'is_required': 0, 'ordinal': 2},
                        {'label': 'Project Description', 'data_type': 'string', 'is_required': 0, 'ordinal': 3},
                    ]
                },
                {
                    'title': 'Line Items',
                    'ordinal': 2,
                    'section_type': 'line_item',
                    'fields': [
                        {'label': 'Description', 'data_type': 'string', 'is_required': 1, 'ordinal': 1},
                        {'label': 'Quantity', 'data_type': 'number', 'is_required': 1, 'ordinal': 2},
                        {'label': 'Unit Price', 'data_type': 'number', 'is_required': 1, 'ordinal': 3},
                        {'label': 'Amount', 'data_type': 'number', 'is_required': 0, 'ordinal': 4, 'calculation_formula': 'this.Quantity * this.Unit Price'},
                    ]
                },
                {
                    'title': 'Totals',
                    'ordinal': 3,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Subtotal', 'data_type': 'number', 'is_required': 0, 'ordinal': 1, 'calculation_formula': 'sum("Line Items".Amount)'},
                        {'label': 'Tax Rate', 'data_type': 'number', 'is_required': 0, 'ordinal': 2},
                        {'label': 'Tax Amount', 'data_type': 'number', 'is_required': 0, 'ordinal': 3, 'calculation_formula': 'this.Subtotal * this."Tax Rate" / 100'},
                        {'label': 'Total', 'data_type': 'number', 'is_required': 0, 'ordinal': 4, 'calculation_formula': 'this.Subtotal + this."Tax Amount"'},
                    ]
                }
            ]
        },
        {
            'name': 'Service Invoice',
            'currency_code': 'USD',
            'sections': [
                {
                    'title': 'Service Details',
                    'ordinal': 1,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Service Period', 'data_type': 'string', 'is_required': 1, 'ordinal': 1},
                        {'label': 'Service Type', 'data_type': 'string', 'is_required': 1, 'ordinal': 2},
                    ]
                },
                {
                    'title': 'Services',
                    'ordinal': 2,
                    'section_type': 'line_item',
                    'fields': [
                        {'label': 'Service Name', 'data_type': 'string', 'is_required': 1, 'ordinal': 1},
                        {'label': 'Hours', 'data_type': 'number', 'is_required': 1, 'ordinal': 2},
                        {'label': 'Rate', 'data_type': 'number', 'is_required': 1, 'ordinal': 3},
                        {'label': 'Total', 'data_type': 'number', 'is_required': 0, 'ordinal': 4, 'calculation_formula': 'this.Hours * this.Rate'},
                    ]
                },
                {
                    'title': 'Summary',
                    'ordinal': 3,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Total Hours', 'data_type': 'number', 'is_required': 0, 'ordinal': 1, 'calculation_formula': 'sum("Services".Hours)'},
                        {'label': 'Total Amount', 'data_type': 'number', 'is_required': 0, 'ordinal': 2, 'calculation_formula': 'sum("Services".Total)'},
                    ]
                }
            ]
        }
    ],
    'techcorp.com': [
        {
            'name': 'Consulting Invoice',
            'currency_code': 'USD',
            'sections': [
                {
                    'title': 'Project Information',
                    'ordinal': 1,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Project Code', 'data_type': 'string', 'is_required': 1, 'ordinal': 1},
                        {'label': 'Project Name', 'data_type': 'string', 'is_required': 1, 'ordinal': 2},
                    ]
                },
                {
                    'title': 'Time Entries',
                    'ordinal': 2,
                    'section_type': 'line_item',
                    'fields': [
                        {'label': 'Date', 'data_type': 'date', 'is_required': 1, 'ordinal': 1},
                        {'label': 'Description', 'data_type': 'string', 'is_required': 1, 'ordinal': 2},
                        {'label': 'Hours', 'data_type': 'number', 'is_required': 1, 'ordinal': 3},
                        {'label': 'Rate', 'data_type': 'number', 'is_required': 1, 'ordinal': 4},
                        {'label': 'Amount', 'data_type': 'number', 'is_required': 0, 'ordinal': 5, 'calculation_formula': 'this.Hours * this.Rate'},
                    ]
                },
                {
                    'title': 'Billing Summary',
                    'ordinal': 3,
                    'section_type': 'normal',
                    'fields': [
                        {'label': 'Total Hours', 'data_type': 'number', 'is_required': 0, 'ordinal': 1, 'calculation_formula': 'sum("Time Entries".Hours)'},
                        {'label': 'Subtotal', 'data_type': 'number', 'is_required': 0, 'ordinal': 2, 'calculation_formula': 'sum("Time Entries".Amount)'},
                        {'label': 'Discount', 'data_type': 'number', 'is_required': 0, 'ordinal': 3},
                        {'label': 'Final Total', 'data_type': 'number', 'is_required': 0, 'ordinal': 4, 'calculation_formula': 'Subtotal - Discount'},
                    ]
                }
            ]
        }
    ]
}


INVOICE_DESCRIPTIONS = [
    'Monthly consulting services',
    'Software development services',
    'Project implementation phase 1',
    'Technical support and maintenance',
    'System integration services',
    'Custom development work',
    'Training and documentation',
    'Quality assurance services',
    'Project management services',
    'Infrastructure setup',
]

LINE_ITEM_DESCRIPTIONS = [
    'Development hours',
    'Consulting services',
    'System configuration',
    'Testing and QA',
    'Documentation',
    'Training sessions',
    'Support services',
    'Custom features',
    'Integration work',
    'Maintenance',
]

def ensure_migration_applied():
    """Check if customer address fields exist, and add them if not"""
    print("Checking database schema...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT DATABASE() as db_name")
            db_name_result = cursor.fetchone()
            db_name = db_name_result.get('db_name') if db_name_result else None

            if not db_name:
                print("  [ERROR] Could not determine database name")
                return


            cursor.execute("""
                SELECT COUNT(*) as col_count
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'customer'
                  AND COLUMN_NAME = 'street_address'
            """, (db_name,))
            result = cursor.fetchone()

            if result and result.get('col_count', 0) == 0:
                print("  -> Address fields missing, applying migration...")
                try:
                    cursor.execute("""
                        ALTER TABLE customer
                        ADD COLUMN street_address VARCHAR(255) NULL AFTER tax_id,
                        ADD COLUMN city VARCHAR(100) NULL AFTER street_address,
                        ADD COLUMN state VARCHAR(100) NULL AFTER city,
                        ADD COLUMN zip_code VARCHAR(20) NULL AFTER state,
                        ADD COLUMN country VARCHAR(100) NULL AFTER zip_code
                    """)
                    conn.commit()
                    print("  [OK] Migration applied successfully")
                except Exception as e:
                    conn.rollback()
                    error_str = str(e)
                    if 'Duplicate column name' in error_str or '1060' in error_str:
                        print("  -> Address fields already exist")
                    else:
                        print(f"  [ERROR] Error applying migration: {e}")
                        raise
            else:
                print("  [OK] Address fields already exist")
            cursor.close()
    except Exception as e:
        print(f"  [ERROR] Error checking schema: {e}")
        print("  -> Continuing anyway (migration may need to be run manually)")

def create_users():
    """Create users and return their IDs"""
    print("Creating users...")
    user_ids = []

    for user_data in USERS:
        try:
            password_hash = hash_password(user_data['password'])
            result = db.execute_proc('sp_create_user', (user_data['email'], password_hash, None))
            if result and len(result) > 0:
                user_id = result[0].get('user_id')
                user_ids.append(user_id)
                print(f"  [OK] Created user: {user_data['email']} (password: {user_data['password']})")
            else:
                print(f"  [ERROR] Failed to create user: {user_data['email']}")
        except DatabaseError as e:
            if 'already exists' in str(e).lower():

                result = db.execute_proc('sp_get_user_by_email', (user_data['email'],))
                if result and len(result) > 0:
                    user_id = result[0].get('user_id')
                    user_ids.append(user_id)
                    print(f"  -> User already exists: {user_data['email']}")
            else:
                print(f"  [ERROR] Error creating user {user_data['email']}: {e}")
                raise

    return user_ids

def create_organizations():
    """Create organizations and return their IDs"""
    print("\nCreating organizations...")
    org_ids = []

    for org_data in ORGANIZATIONS:
        try:
            result = db.execute_proc('sp_create_organization', (org_data['name'], org_data['domain'], None))
            if result and len(result) > 0:
                org_id = result[0].get('org_id')
                org_ids.append(org_id)
                print(f"  [OK] Created organization: {org_data['name']} ({org_data['domain']})")
            else:
                print(f"  [ERROR] Failed to create organization: {org_data['name']}")
        except DatabaseError as e:
            if 'duplicate' in str(e).lower() or '1062' in str(e):

                result = db.execute_proc('sp_find_organizations_by_domain', (org_data['domain'],))
                if result:
                    for org in result:
                        if org.get('name') == org_data['name']:
                            org_id = org.get('org_id')
                            org_ids.append(org_id)
                            print(f"  -> Organization already exists: {org_data['name']}")
                            break
            else:
                print(f"  [ERROR] Error creating organization {org_data['name']}: {e}")
                raise

    return org_ids

def assign_users_to_orgs(user_ids, org_ids):
    """Assign users to organizations"""
    print("\nAssigning users to organizations...")

    for user_idx, org_idx, role in USER_ORG_ASSIGNMENTS:
        try:
            user_id = user_ids[user_idx]
            org_id = org_ids[org_idx]
            db.execute_proc('sp_assign_user_to_org', (user_id, org_id, role), fetch=False)
            print(f"  [OK] Assigned {USERS[user_idx]['email']} to {ORGANIZATIONS[org_idx]['name']} as {role}")
        except DatabaseError as e:
            if 'duplicate' in str(e).lower():
                print(f"  -> User already assigned: {USERS[user_idx]['email']} to {ORGANIZATIONS[org_idx]['name']}")
            else:
                print(f"  [ERROR] Error assigning user: {e}")

def create_templates(org_ids):
    """Create templates with sections and fields"""
    print("\nCreating templates...")
    template_data = {}

    for idx, org in enumerate(ORGANIZATIONS):
        org_id = org_ids[idx]
        domain = org['domain']
        templates_for_org = TEMPLATES.get(domain, [])
        template_data[domain] = []

        for template_def in templates_for_org:
            try:

                result = db.execute_proc('sp_create_template', (
                    org_id,
                    template_def['name'],
                    template_def['currency_code'],
                    None,
                    None
                ))

                if not result or len(result) == 0:
                    print(f"  [ERROR] Failed to create template: {template_def['name']}")
                    continue

                template_id = result[0].get('template_id')
                template_version = result[0].get('version')
                template_data[domain].append(template_id)
                print(f"  [OK] Created template: {template_def['name']} (v{template_version})")


                for section_def in template_def['sections']:
                    section_result = db.execute_proc('sp_create_section', (
                        template_id,
                        template_version,
                        section_def['title'],
                        section_def['ordinal'],
                        section_def['section_type'],
                        None
                    ))

                    if not section_result or len(section_result) == 0:
                        print(f"    [ERROR] Failed to create section: {section_def['title']}")
                        continue

                    section_id = section_result[0].get('section_id')


                    total_field_id = None
                    total_field_label = None
                    for field_def in section_def['fields']:
                        field_result = db.execute_proc('sp_add_template_field', (
                            section_id,
                            field_def['label'],
                            field_def['data_type'],
                            field_def.get('is_required', 0),
                            field_def['ordinal'],
                            field_def.get('calculation_formula'),
                            None
                        ))

                        if field_result and len(field_result) > 0:
                            field_id = field_result[0].get('field_id')
                            label_lower = field_def['label'].lower()


                            if section_def['section_type'] == 'normal' and field_def['data_type'] == 'number':

                                if label_lower in ['grand total', 'grand_total']:
                                    total_field_id = field_id
                                    total_field_label = field_def['label']
                                elif label_lower in ['total amount', 'total_amount'] and total_field_id is None:
                                    total_field_id = field_id
                                    total_field_label = field_def['label']
                                elif label_lower in ['final total', 'final_total'] and total_field_id is None:
                                    total_field_id = field_id
                                    total_field_label = field_def['label']
                                elif label_lower == 'total' and total_field_id is None:
                                    total_field_id = field_id
                                    total_field_label = field_def['label']


                    if total_field_id:
                        try:
                            db.execute_proc('sp_set_template_total_field', (
                                template_id,
                                template_version,
                                total_field_id
                            ), fetch=False)
                            print(f"    -> Set total field to: '{total_field_label}'")
                        except Exception as e:
                            print(f"    [WARN] Warning: Could not set total field: {e}")

            except DatabaseError as e:
                print(f"  [ERROR] Error creating template {template_def['name']}: {e}")

    return template_data

def create_customers(org_ids):
    """Create customers for each organization"""
    print("\nCreating customers...")
    customer_data = {}

    for idx, org in enumerate(ORGANIZATIONS):
        org_id = org_ids[idx]
        domain = org['domain']
        customers_for_org = CUSTOMERS.get(domain, [])
        customer_data[domain] = []

        for customer_def in customers_for_org:
            try:
                result = db.execute_proc('sp_create_customer', (
                    org_id,
                    customer_def['name'],
                    customer_def.get('tax_id'),
                    customer_def.get('street_address'),
                    customer_def.get('city'),
                    customer_def.get('state'),
                    customer_def.get('zip_code'),
                    customer_def.get('country'),
                    None
                ))

                if result and len(result) > 0:
                    customer_id = result[0].get('customer_id')
                    customer_data[domain].append(customer_id)
                    print(f"  [OK] Created customer: {customer_def['name']}")
            except DatabaseError as e:
                print(f"  [ERROR] Error creating customer {customer_def['name']}: {e}")

    return customer_data

def create_one_test_invoice(template_data, customer_data, org_ids):
    """Create ONE test invoice to verify calculations work"""
    print("\nCreating ONE test invoice to verify calculations...")


    first_org_domain = list(template_data.keys())[0]
    first_template_id = template_data[first_org_domain][0]
    first_customer_id = customer_data[first_org_domain][0]
    first_org_id = org_ids[0]

    print(f"  Using org: {first_org_domain}, template: {first_template_id}, customer: {first_customer_id}")

    try:

        result = db.execute_proc('sp_create_invoice', (first_org_id, first_customer_id, first_template_id, None, None))
        if not result or len(result) == 0:
            print("  [ERROR] Failed to create invoice")
            return None

        invoice_id = result[0].get('invoice_id')
        print(f"  [OK] Created invoice: {invoice_id}")


        fields_result = db.execute_proc('sp_get_template_fields', (first_template_id,))
        if not fields_result:
            print("  [ERROR] No fields found for template")
            return None


        issue_date = datetime(2025, 7, 15)
        due_date = datetime(2025, 8, 15)
        db.execute_proc('sp_update_invoice_dates', (invoice_id, issue_date.date(), due_date.date()), fetch=False)


        sections = {}
        for field in fields_result:
            section_id = field['section_id']
            if section_id not in sections:
                sections[section_id] = {
                    'type': field.get('section_type', 'normal'),
                    'fields': []
                }
            sections[section_id]['fields'].append(field)


        for section_id, section_info in sections.items():
            if section_info['type'] == 'line_item':

                for row in range(1, 3):
                    for field in section_info['fields']:
                        field_id = field['field_id']
                        label = field.get('label', '').lower()
                        data_type = field.get('data_type', 'string')

                        if 'description' in label:
                            val_string = f"Test Item {row}"
                            db.execute_proc('sp_save_invoice_value', (
                                invoice_id, field_id, val_string, None, None, None, row
                            ), fetch=False)
                        elif 'quantity' in label or 'hours' in label:
                            val_number = Decimal('10') if row == 1 else Decimal('20')
                            db.execute_proc('sp_save_invoice_value', (
                                invoice_id, field_id, None, val_number, None, None, row
                            ), fetch=False)
                        elif 'rate' in label or 'price' in label or 'unit price' in label:
                            val_number = Decimal('100')
                            db.execute_proc('sp_save_invoice_value', (
                                invoice_id, field_id, None, val_number, None, None, row
                            ), fetch=False)
            else:

                for field in section_info['fields']:
                    field_id = field['field_id']
                    label = field.get('label', '').lower()
                    data_type = field.get('data_type', 'string')

                    if 'tax rate' in label:
                        val_number = Decimal('8.5')
                        db.execute_proc('sp_save_invoice_value', (
                            invoice_id, field_id, None, val_number, None, None, 0
                        ), fetch=False)


        invoice_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
        current_invoice_values = []
        if invoice_values_result and isinstance(invoice_values_result, list):
            if len(invoice_values_result) >= 2:
                if isinstance(invoice_values_result[1], list):
                    current_invoice_values = invoice_values_result[1]
                else:
                    current_invoice_values = invoice_values_result[1:]


        sections_for_calc = {}
        for field in fields_result:
            section_title = field.get('section_title', '')
            section_type = field.get('section_type', 'normal')
            if section_title not in sections_for_calc:
                sections_for_calc[section_title] = {
                    'type': section_type,
                    'fields': [],
                    'line_item_rows': {} if section_type == 'line_item' else None
                }
            sections_for_calc[section_title]['fields'].append(field)


        for section_title, section_info in sections_for_calc.items():
            if section_info['type'] == 'line_item':
                section_info['line_item_rows'] = {}
                for value in current_invoice_values:
                    if value.get('section_title') == section_title:
                        ordinal = value.get('value_ordinal', 0) or 0
                        if ordinal not in section_info['line_item_rows']:
                            section_info['line_item_rows'][ordinal] = []
                        section_info['line_item_rows'][ordinal].append(value)


        for section_title, section_info in sections_for_calc.items():
            if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                rows_list = []
                for ordinal in sorted(section_info['line_item_rows'].keys()):
                    row = section_info['line_item_rows'][ordinal]
                    rows_list.append(row)
                section_info['line_item_rows'] = rows_list

        print(f"  DEBUG: Sections for calc: {list(sections_for_calc.keys())}")
        for sec_name, sec_info in sections_for_calc.items():
            print(f"  DEBUG: Section '{sec_name}': type={sec_info.get('type')}, fields={len(sec_info.get('fields', []))}")
            if sec_info.get('type') == 'line_item':
                rows = sec_info.get('line_item_rows', [])
                print(f"  DEBUG:   Line item rows: {len(rows)} rows")
                for i, row in enumerate(rows):
                    print(f"  DEBUG:     Row {i}: {len(row)} values")


        try:
            calculated_values = calculate_invoice_fields(current_invoice_values, sections_for_calc)
            print(f"  DEBUG: Calculated {len(calculated_values)} values")


            for (field_id, ordinal), calc_value in calculated_values.items():
                if calc_value is not None:
                    print(f"  DEBUG: Saving calculated value: field_id={field_id}, ordinal={ordinal}, value={calc_value}")
                    db.execute_proc('sp_save_invoice_value',
                                  (invoice_id, field_id, None, float(calc_value), None, None, ordinal),
                                  fetch=False)
        except Exception as e:
            print(f"  [ERROR] Error calculating: {e}")
            import traceback
            traceback.print_exc()


        db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)


        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_amount FROM invoice WHERE invoice_id = %s", (invoice_id,))
            invoice_row = cursor.fetchone()
            cursor.close()
            total = invoice_row.get('total_amount', 0) if invoice_row else 0
            print(f"  [OK] Invoice total: {total}")

        return invoice_id

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_invoice_data(template_data, customer_data, org_ids):
    """Generate invoices from July 2025 to December 2025"""
    print("\nCreating invoices...")


    start_date = datetime(2025, 7, 1)
    end_date = datetime(2025, 12, 31)
    current_date = start_date

    invoice_count = 0

    while current_date <= end_date:

        invoices_this_month = random.randint(2, 4)

        for _ in range(invoices_this_month):

            org_idx = random.randint(0, len(ORGANIZATIONS) - 1)
            org = ORGANIZATIONS[org_idx]
            org_id = org_ids[org_idx]
            domain = org['domain']


            templates = template_data.get(domain, [])
            customers = customer_data.get(domain, [])

            if not templates or not customers:
                continue

            template_id = random.choice(templates)
            customer_id = random.choice(customers)


            days_in_month = (current_date.replace(month=current_date.month % 12 + 1, day=1) - timedelta(days=1)).day if current_date.month < 12 else 31
            issue_day = random.randint(1, min(days_in_month, 28))
            issue_date = current_date.replace(day=issue_day)
            due_date = issue_date + timedelta(days=random.randint(15, 45))

            try:

                result = db.execute_proc('sp_create_invoice', (
                    org_id,
                    customer_id,
                    template_id,
                    None,
                    None
                ))

                if not result or len(result) > 0:
                    invoice_id = result[0].get('invoice_id')
                    template_version = result[0].get('template_version')


                    db.execute_proc('sp_update_invoice_dates', (
                        invoice_id,
                        issue_date.date(),
                        due_date.date()
                    ), fetch=False)


                    fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                    if not fields_result:
                        continue


                    sections = {}
                    for field in fields_result:
                        section_id = field['section_id']
                        if section_id not in sections:
                            sections[section_id] = {
                                'type': field.get('section_type', 'normal'),
                                'fields': []
                            }
                        sections[section_id]['fields'].append(field)


                    for section_id, section_info in sections.items():
                        if section_info['type'] == 'line_item':

                            num_items = random.randint(2, 5)
                            for row in range(1, num_items + 1):
                                for field in section_info['fields']:
                                    field_id = field['field_id']
                                    label = field.get('label', '')
                                    data_type = field.get('data_type', 'string')

                                    if 'description' in label.lower() or 'name' in label.lower():
                                        val_string = random.choice(LINE_ITEM_DESCRIPTIONS)
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, val_string, None, None, None, row
                                        ), fetch=False)
                                    elif 'quantity' in label.lower() or 'hours' in label.lower():
                                        val_number = Decimal(str(random.randint(1, 40)))
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, None, val_number, None, None, row
                                        ), fetch=False)
                                    elif 'rate' in label.lower() or 'price' in label.lower():
                                        val_number = Decimal(str(random.randint(50, 200)))
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, None, val_number, None, None, row
                                        ), fetch=False)
                                    elif 'date' in label.lower():
                                        val_date = (issue_date - timedelta(days=random.randint(0, 30))).date()
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, None, None, val_date, None, row
                                        ), fetch=False)
                        else:

                            for field in section_info['fields']:
                                field_id = field['field_id']
                                label = field.get('label', '')
                                data_type = field.get('data_type', 'string')

                                if 'invoice number' in label.lower():
                                    val_string = f"INV-{issue_date.strftime('%Y%m%d')}-{random.randint(100, 999)}"
                                    db.execute_proc('sp_save_invoice_value', (
                                        invoice_id, field_id, val_string, None, None, None, 0
                                    ), fetch=False)
                                elif 'po number' in label.lower():
                                    if random.random() > 0.3:
                                        val_string = f"PO-{random.randint(10000, 99999)}"
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, val_string, None, None, None, 0
                                        ), fetch=False)
                                elif 'description' in label.lower() or 'project' in label.lower():
                                    val_string = random.choice(INVOICE_DESCRIPTIONS)
                                    db.execute_proc('sp_save_invoice_value', (
                                        invoice_id, field_id, val_string, None, None, None, 0
                                    ), fetch=False)
                                elif 'tax rate' in label.lower():
                                    val_number = Decimal('8.5')
                                    db.execute_proc('sp_save_invoice_value', (
                                        invoice_id, field_id, None, val_number, None, None, 0
                                    ), fetch=False)
                                elif 'discount' in label.lower():
                                    if random.random() > 0.7:
                                        val_number = Decimal(str(random.randint(50, 500)))
                                        db.execute_proc('sp_save_invoice_value', (
                                            invoice_id, field_id, None, val_number, None, None, 0
                                        ), fetch=False)



                    invoice_values_result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
                    current_invoice_values = []
                    if invoice_values_result and isinstance(invoice_values_result, list):
                        if len(invoice_values_result) >= 2:
                            if isinstance(invoice_values_result[1], list):
                                current_invoice_values = invoice_values_result[1]
                            else:
                                current_invoice_values = invoice_values_result[1:]


                    sections_for_calc = {}
                    field_map = {}
                    for field in fields_result:
                        field_id = field.get('field_id')
                        if field_id:
                            field_map[field_id] = field
                        section_title = field.get('section_title', '')
                        section_type = field.get('section_type', 'normal')
                        if section_title not in sections_for_calc:
                            sections_for_calc[section_title] = {
                                'type': section_type,
                                'fields': [],
                                'line_item_rows': {} if section_type == 'line_item' else None,
                                'field_metadata': []
                            }
                        sections_for_calc[section_title]['fields'].append(field)
                        if section_type == 'normal':
                            sections_for_calc[section_title]['field_metadata'].append(field)


                    for section_title, section_info in sections_for_calc.items():
                        if section_info['type'] != 'line_item':
                            section_info['fields'] = []



                    line_item_ordinals = set()
                    for value in current_invoice_values:
                        if value.get('section_title') in sections_for_calc:
                            section_info = sections_for_calc[value.get('section_title')]
                            if section_info.get('type') == 'line_item':
                                ordinal = value.get('value_ordinal', 0) or 0
                                if ordinal > 0:
                                    line_item_ordinals.add(ordinal)

                    for section_title, section_info in sections_for_calc.items():
                        if section_info['type'] == 'line_item':
                            section_info['line_item_rows'] = {}


                            for ordinal in line_item_ordinals:
                                row = []

                                for field_meta in section_info['fields']:
                                    field_id = field_meta.get('field_id')

                                    value = None
                                    for inv_value in current_invoice_values:
                                        if (inv_value.get('field_id') == field_id and
                                            inv_value.get('section_title') == section_title and
                                            (inv_value.get('value_ordinal', 0) or 0) == ordinal):
                                            value = inv_value.copy()
                                            break


                                    if value:
                                        value['field_label'] = field_meta.get('label', '')
                                        value['calculation_formula'] = field_meta.get('calculation_formula')
                                        value['data_type'] = field_meta.get('data_type', 'string')
                                        row.append(value)
                                    else:


                                        row.append({
                                            'field_id': field_id,
                                            'field_label': field_meta.get('label', ''),
                                            'calculation_formula': field_meta.get('calculation_formula'),
                                            'data_type': field_meta.get('data_type', 'string'),
                                            'val_number': None,
                                            'val_string': None,
                                            'val_date': None,
                                            'val_boolean': None,
                                            'value_ordinal': ordinal,
                                            'section_title': section_title
                                        })

                                if row:
                                    section_info['line_item_rows'][ordinal] = row


                    for section_title, section_info in sections_for_calc.items():
                        if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                            rows_list = []
                            for ordinal in sorted(section_info['line_item_rows'].keys()):
                                row = section_info['line_item_rows'][ordinal]
                                rows_list.append(row)
                            section_info['line_item_rows'] = rows_list
                        else:

                            merged_fields = []

                            field_metadata = section_info.get('field_metadata', section_info.get('fields', []))
                            for field_meta in field_metadata:
                                field_id = field_meta.get('field_id')

                                field_value = None
                                for value in current_invoice_values:
                                    if value.get('field_id') == field_id and (value.get('value_ordinal', 0) or 0) == 0:
                                        field_value = value.copy()
                                        break


                                if field_value:
                                    field_value['field_label'] = field_meta.get('label', '')
                                    field_value['calculation_formula'] = field_meta.get('calculation_formula')
                                    field_value['data_type'] = field_meta.get('data_type', 'string')
                                    merged_fields.append(field_value)
                                else:

                                    merged_fields.append({
                                        'field_id': field_id,
                                        'field_label': field_meta.get('label', ''),
                                        'calculation_formula': field_meta.get('calculation_formula'),
                                        'data_type': field_meta.get('data_type', 'string'),
                                        'val_number': None,
                                        'val_string': None,
                                        'val_date': None,
                                        'val_boolean': None,
                                        'value_ordinal': 0
                                    })
                            section_info['fields'] = merged_fields


                    try:
                        calculated_values = calculate_invoice_fields(current_invoice_values, sections_for_calc)


                        for (field_id, ordinal), calc_value in calculated_values.items():
                            if calc_value is not None:
                                db.execute_proc('sp_save_invoice_value',
                                              (invoice_id, field_id, None, float(calc_value), None, None, ordinal),
                                              fetch=False)
                    except Exception as e:
                        print(f"    [WARN] Warning: Could not calculate fields: {e}")
                        import traceback
                        traceback.print_exc()


                    db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)



                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT total_amount FROM invoice WHERE invoice_id = %s", (invoice_id,))
                        invoice_row = cursor.fetchone()
                        cursor.close()
                        invoice_total = Decimal(str(invoice_row.get('total_amount', 0) or 0)) if invoice_row else Decimal('0')


                    status_roll = random.random()
                    if status_roll < 0.3 and invoice_total > 0:

                        payment_amount = invoice_total
                        try:
                            db.execute_proc('sp_record_payment', (
                                invoice_id,
                                payment_amount,
                                random.choice(['Bank Transfer', 'Credit Card', 'Check']),
                                f"REF-{random.randint(100000, 999999)}",
                                None
                            ), fetch=False)

                        except DatabaseError as e:
                            print(f"    [WARN] Could not add payment: {e}")
                    elif status_roll < 0.7:
                        db.execute_proc('sp_update_invoice_status', (invoice_id, 'pending'), fetch=False)


                    invoice_count += 1
                    if invoice_count % 10 == 0:
                        print(f"  Created {invoice_count} invoices...")

            except DatabaseError as e:
                print(f"  [ERROR] Error creating invoice: {e}")
                continue


        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    print(f"  [OK] Created {invoice_count} invoices total")

def delete_all_data():
    """Delete all existing data from the database"""
    print("\nDeleting all existing data...")

    def safe_delete(cursor, table_name, description):
        """Safely delete from a table, handling if it doesn't exist"""
        try:
            cursor.execute(f"DELETE FROM {table_name}")
            count = cursor.rowcount
            print(f"  [OK] Deleted {count} {description}")
            return count
        except Exception as e:
            error_str = str(e)
            if "doesn't exist" in error_str or "1146" in error_str:
                print(f"  -> Table '{table_name}' doesn't exist, skipping")
                return 0
            else:
                print(f"  [WARN] Warning deleting from {table_name}: {e}")
                return 0

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()



            safe_delete(cursor, "payment", "payments")


            safe_delete(cursor, "invoice_value", "invoice values")


            safe_delete(cursor, "invoice", "invoices")


            safe_delete(cursor, "field", "fields")


            safe_delete(cursor, "section", "sections")


            safe_delete(cursor, "template", "templates")


            safe_delete(cursor, "customer", "customers")


            safe_delete(cursor, "user_organization", "user-organization assignments")


            safe_delete(cursor, "organization", "organizations")


            safe_delete(cursor, "users", "users")

            conn.commit()
            cursor.close()

            print(f"\n  [OK] Successfully deleted all data")

    except Exception as e:
        print(f"  [ERROR] Error deleting data: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main function to generate all demo data"""
    print("=" * 60)
    print("DocuMint Demo Data Generator")
    print("=" * 60)

    try:

        delete_all_data()


        ensure_migration_applied()
        print()


        user_ids = create_users()


        org_ids = create_organizations()


        assign_users_to_orgs(user_ids, org_ids)


        template_data = create_templates(org_ids)


        customer_data = create_customers(org_ids)


        generate_invoice_data(template_data, customer_data, org_ids)

        print("\n" + "=" * 60)
        print("Demo data generation complete!")
        print("=" * 60)
        print("\nLogin credentials:")
        print("  User 1: user1@acme.com / demo123")
        print("  User 2: user2@techcorp.com / demo123")
        print("\n")

    except Exception as e:
        print(f"\n[ERROR] Error generating demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

