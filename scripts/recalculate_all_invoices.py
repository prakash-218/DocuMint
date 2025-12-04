
"""
Recalculate all invoice totals by:
1. Fetching invoice values
2. Recalculating all calculated fields
3. Saving the calculated values
4. Updating invoice.total_amount
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db, DatabaseError
from calculations import calculate_invoice_fields

def recalculate_all_invoices():
    """Recalculate totals for all invoices"""


    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.invoice_id, i.template_id, i.template_version, i.org_id
            FROM invoice i
            ORDER BY i.issue_date DESC
        """)
        invoices = cursor.fetchall()

        print(f"Found {len(invoices)} invoices to recalculate\n")

        success_count = 0
        error_count = 0

        for inv in invoices:
            invoice_id = inv.get('invoice_id') or inv.get('INVOICE_ID')
            template_id = inv.get('template_id') or inv.get('TEMPLATE_ID')
            template_version = inv.get('template_version') or inv.get('TEMPLATE_VERSION')
            org_id = inv.get('org_id') or inv.get('ORG_ID')

            try:
                print(f"Processing invoice {str(invoice_id)[:8]}...")


                result = db.execute_proc('sp_get_invoice_details', (invoice_id,))

                if not result or not isinstance(result, list) or len(result) < 2:
                    print(f"  [WARN] No data returned for invoice")
                    error_count += 1
                    continue


                invoice_header = result[0] if isinstance(result[0], dict) else {}


                invoice_values = result[1] if isinstance(result[1], list) else []


                fields = result[2] if len(result) > 2 and isinstance(result[2], list) else []

                if not fields:

                    fields_result = db.execute_proc('sp_get_template_fields', (template_id,))
                    if fields_result and isinstance(fields_result, list):
                        fields = fields_result

                if not fields:
                    print(f"  [WARN] No fields found for template")
                    error_count += 1
                    continue


                sections_for_calc = {}
                field_map = {}

                for field in fields:
                    field_id = field.get('field_id')
                    if field_id:
                        field_map[field_id] = field

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
                    if section_info['type'] != 'line_item':

                        if 'field_metadata' not in section_info:
                            section_info['field_metadata'] = section_info['fields'].copy()
                        section_info['fields'] = []


                for value in invoice_values:
                    section_title = value.get('section_title', '')
                    if section_title in sections_for_calc:
                        section_info = sections_for_calc[section_title]
                        field_id = value.get('field_id')


                        if field_id and field_id in field_map:
                            field_meta = field_map[field_id]
                            value['calculation_formula'] = field_meta.get('calculation_formula')
                            value['field_label'] = field_meta.get('label', value.get('field_label', ''))
                            value['data_type'] = field_meta.get('data_type', value.get('data_type', 'string'))

                        if section_info['type'] == 'line_item':
                            ordinal = value.get('value_ordinal', 0) or 0
                            if section_info['line_item_rows'] is None:
                                section_info['line_item_rows'] = {}
                            if ordinal not in section_info['line_item_rows']:
                                section_info['line_item_rows'][ordinal] = []
                            section_info['line_item_rows'][ordinal].append(value)
                        else:
                            section_info['fields'].append(value)


                for section_title, section_info in sections_for_calc.items():
                    if section_info['type'] != 'line_item':
                        field_metadata = section_info.get('field_metadata', [])

                        existing_field_ids = {f.get('field_id') for f in section_info['fields'] if f.get('field_id')}

                        for field_meta in field_metadata:
                            field_id = field_meta.get('field_id')
                            if field_id and field_id not in existing_field_ids:
                                section_info['fields'].append({
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


                for section_title, section_info in sections_for_calc.items():
                    if section_info['type'] == 'line_item' and section_info['line_item_rows']:
                        rows_list = []
                        for ordinal in sorted(section_info['line_item_rows'].keys()):
                            row = section_info['line_item_rows'][ordinal]
                            rows_list.append(row)
                        section_info['line_item_rows'] = rows_list
                    else:

                        field_metadata = section_info.get('field_metadata', [])

                        existing_field_ids = {f.get('field_id') for f in section_info['fields'] if f.get('field_id')}

                        for field_meta in field_metadata:
                            field_id = field_meta.get('field_id')
                            if field_id and field_id not in existing_field_ids:
                                section_info['fields'].append({
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


                calculated_values = calculate_invoice_fields(invoice_values, sections_for_calc)


                saved_count = 0
                for (field_id, ordinal), calc_value in calculated_values.items():
                    if calc_value is not None:
                        try:
                            db.execute_proc('sp_save_invoice_value',
                                          (invoice_id, field_id, None, float(calc_value), None, None, ordinal),
                                          fetch=False)
                            saved_count += 1
                        except Exception as e:
                            print(f"    [WARN] Error saving calculated value: {e}")


                db.execute_proc('sp_update_invoice_total', (invoice_id,), fetch=False)


                cursor.execute("SELECT total_amount FROM invoice WHERE invoice_id = %s", (invoice_id,))
                total_row = cursor.fetchone()
                total = total_row.get('total_amount', 0) if total_row else 0

                print(f"  [OK] Saved {saved_count} calculated values, total_amount = {total}")
                success_count += 1

            except Exception as e:
                print(f"  [ERROR] Error: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1

        cursor.close()

        print(f"\n{'='*60}")
        print(f"Summary: {success_count} successful, {error_count} errors")
        print(f"{'='*60}")

if __name__ == '__main__':
    recalculate_all_invoices()

