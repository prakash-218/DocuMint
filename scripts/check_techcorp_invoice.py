
"""Check a TechCorp invoice to see why totals are 0"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
from calculations import calculate_invoice_fields
import json


with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.invoice_id
        FROM invoice i
        JOIN organization o ON i.org_id = o.org_id
        WHERE o.name LIKE '%TechCorp%'
        LIMIT 1
    """)
    row = cursor.fetchone()
    invoice_id = row.get('invoice_id') if row else None

    if not invoice_id:
        print("No TechCorp invoices found")
        sys.exit(1)

    print(f"Checking invoice: {invoice_id[:8]}...\n")


    result = db.execute_proc('sp_get_invoice_details', (invoice_id,))
    invoice_header = result[0] if result and isinstance(result[0], dict) else (result[0][0] if result and isinstance(result[0], list) and len(result[0]) > 0 else {})
    invoice_values = result[1] if result and len(result) > 1 else []


    template_id = invoice_header.get('template_id') if isinstance(invoice_header, dict) else None
    if not template_id:
        print("Could not get template_id")
        sys.exit(1)
    fields_result = db.execute_proc('sp_get_template_fields', (template_id,))


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


    line_item_ordinals = set()
    for value in invoice_values:
        section_title = value.get('section_title', '')
        if section_title in sections_for_calc:
            section_info = sections_for_calc[section_title]
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
                    for inv_value in invoice_values:
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
                            'value_ordinal': ordinal,
                            'section_title': section_title
                        })
                if row:
                    section_info['line_item_rows'][ordinal] = row


    for section_title, section_info in sections_for_calc.items():
        if section_info['type'] == 'line_item' and section_info['line_item_rows']:
            rows_list = []
            for ordinal in sorted(section_info['line_item_rows'].keys()):
                rows_list.append(section_info['line_item_rows'][ordinal])
            section_info['line_item_rows'] = rows_list


    print("Line Item Rows Structure:")
    for section_title, section_info in sections_for_calc.items():
        if section_info['type'] == 'line_item':
            print(f"\nSection: {section_title}")
            rows = section_info.get('line_item_rows', [])
            print(f"  Number of rows: {len(rows)}")
            for i, row in enumerate(rows):
                print(f"  Row {i+1}:")
                for value in row:
                    label = value.get('field_label', '')
                    formula = value.get('calculation_formula', '')
                    val = value.get('val_number')
                    print(f"    - {label}: value={val}, formula={formula}")


    print("\n\nRunning calculations...")
    calculated_values = calculate_invoice_fields(invoice_values, sections_for_calc)

    print(f"\nCalculated {len(calculated_values)} values:")
    for (field_id, ordinal), value in calculated_values.items():

        label = "Unknown"
        for field in fields_result:
            if field.get('field_id') == field_id:
                label = field.get('label', 'Unknown')
                break
        print(f"  {label} (ordinal {ordinal}): {value}")

