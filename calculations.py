"""
Calculation engine for invoice field calculations.

Supports:
- Field references: field_label or section.field_label
  - Field names with spaces: "field name" or 'field name' or [field name]
  - Examples: "Unit Price" * Quantity, Subtotal + "Sales Tax"
- Line item aggregations: sum(line_items.field_label), count(line_items.field_label), avg(line_items.field_label)
  - Supports quoted field names: sum(line_items."field name")
- Row-level calculations: this.field_label (within same line item row)
  - Supports quoted field names: this."field name"
- Basic math: +, -, *, /, (, )
"""

import re
from typing import Dict, List, Any, Optional


def evaluate_calculation(formula: str, context: Dict[str, Any]) -> Optional[float]:
    """
    Evaluate a calculation formula.

    Args:
        formula: Calculation formula string (e.g., "sum(line_items.amount)", "this.price * this.qty", "total * 0.1")
        context: Dictionary containing:
            - 'invoice_values': List of all invoice values
            - 'sections_data': Organized sections data
            - 'current_section': Current section title
            - 'current_row': Current row ordinal (for line items)

    Returns:
        Calculated value (float) or None if calculation fails
    """
    if not formula or not formula.strip():
        return None

    formula = formula.strip()

    try:


        aggregation_match = re.match(r'^(sum|count|avg)\(([^)]+)\)$', formula, re.IGNORECASE)
        if aggregation_match:
            func_name = aggregation_match.group(1).lower()
            field_ref = aggregation_match.group(2).strip()

            field_label = None
            section_name = None

            quoted_section_quoted_field = re.match(r'^["\']([^"\']+)["\']\.["\']([^"\']+)["\']$|^\[([^\]]+)\]\.\[([^\]]+)\]$|^["\']([^"\']+)["\']\.\[([^\]]+)\]$|^\[([^\]]+)\]\.["\']([^"\']+)["\']$', field_ref)
            if quoted_section_quoted_field:
                if quoted_section_quoted_field.group(1) and quoted_section_quoted_field.group(2):
                    section_name = quoted_section_quoted_field.group(1).strip()
                    field_label = quoted_section_quoted_field.group(2).strip()
                elif quoted_section_quoted_field.group(3) and quoted_section_quoted_field.group(4):
                    section_name = quoted_section_quoted_field.group(3).strip()
                    field_label = quoted_section_quoted_field.group(4).strip()
                elif quoted_section_quoted_field.group(5) and quoted_section_quoted_field.group(6):
                    section_name = quoted_section_quoted_field.group(5).strip()
                    field_label = quoted_section_quoted_field.group(6).strip()
                elif quoted_section_quoted_field.group(7) and quoted_section_quoted_field.group(8):
                    section_name = quoted_section_quoted_field.group(7).strip()
                    field_label = quoted_section_quoted_field.group(8).strip()

            if field_label is None:
                quoted_section_match = re.match(r'^["\']([^"\']+)["\']\.([^.]+)$|^\[([^\]]+)\]\.([^.]+)$', field_ref)
                if quoted_section_match:
                    if quoted_section_match.group(1) and quoted_section_match.group(2):
                        section_name = quoted_section_match.group(1).strip()
                        field_label = quoted_section_match.group(2).strip()
                    elif quoted_section_match.group(3) and quoted_section_match.group(4):
                        section_name = quoted_section_match.group(3).strip()
                        field_label = quoted_section_match.group(4).strip()

            if field_label is None:
                quoted_field_match = re.match(r'^([^."\'\[\]]+)\.?["\']([^"\']+)["\']|^([^."\'\[\]]+)\.?\[([^\]]+)\]', field_ref)
                if quoted_field_match:
                    if quoted_field_match.group(1) and quoted_field_match.group(2):
                        section_name = quoted_field_match.group(1).strip()
                        field_label = quoted_field_match.group(2).strip()
                    elif quoted_field_match.group(3) and quoted_field_match.group(4):
                        section_name = quoted_field_match.group(3).strip()
                        field_label = quoted_field_match.group(4).strip()

            if field_label is None:
                quoted_only_match = re.match(r'^["\']([^"\']+)["\']$|^\[([^\]]+)\]$', field_ref)
                if quoted_only_match:
                    field_label = quoted_only_match.group(1) or quoted_only_match.group(2)
                    if field_label:
                        field_label = field_label.strip()

            if field_label is None:
                if '.' in field_ref:
                    section_name, field_label = field_ref.split('.', 1)
                    section_name = section_name.strip()
                    field_label = field_label.strip()
                else:
                    section_name = 'line_items'
                    field_label = field_ref.strip()

            return _evaluate_aggregation(func_name, section_name, field_label, context)


        if 'this.' in formula.lower():
            return _evaluate_row_calculation(formula, context)



        formula_processed = formula



        quoted_fields = []
        field_placeholder_map = {}

        def replace_quoted_field(match):
            """Replace quoted/bracketed field with placeholder and store mapping"""

            field_name = match.group(1) if match.group(1) else match.group(2)
            if not field_name:
                return match.group(0)
            placeholder = f"__FIELD_{len(quoted_fields)}__"
            quoted_fields.append(field_name)
            field_placeholder_map[placeholder] = field_name
            return placeholder


        formula_processed = re.sub(r'["\']([^"\']+)["\']|\[([^\]]+)\]',
                                   replace_quoted_field,
                                   formula_processed)


        for placeholder, field_name in field_placeholder_map.items():
            value = _get_field_value(None, field_name, context)
            if value is not None:
                print(f"DEBUG CALC: Found quoted field '{field_name}' = {value}")
                formula_processed = formula_processed.replace(placeholder, str(value))
            else:
                print(f"DEBUG CALC: Quoted field '{field_name}' not found or has no value")
                formula_processed = formula_processed.replace(placeholder, '0')



        field_names = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula_processed)
        print(f"DEBUG CALC: Processing formula '{formula}', found unquoted field names: {field_names}")
        for field_name in field_names:

            if field_name.lower() in ['sum', 'count', 'avg', 'this'] or field_name.startswith('__FIELD_'):
                continue

            value = _get_field_value(None, field_name, context)
            if value is not None:
                print(f"DEBUG CALC: Found field '{field_name}' = {value}")

                formula_processed = re.sub(r'\b' + re.escape(field_name) + r'\b', str(value), formula_processed, flags=re.IGNORECASE)
            else:
                print(f"DEBUG CALC: Field '{field_name}' not found or has no value")

        print(f"DEBUG CALC: Formula after field replacement: '{formula_processed}'")



        allowed_chars = set('0123456789.+-*/() ')
        if all(c in allowed_chars for c in formula_processed.replace(' ', '')):
            try:
                print(f"DEBUG CALC: Evaluating: '{formula_processed}'")
                result = eval(formula_processed)
                print(f"DEBUG CALC: Result: {result}")
                return float(result) if result is not None else None
            except Exception as e:
                print(f"Error evaluating formula '{formula_processed}': {str(e)}")
                import traceback
                traceback.print_exc()
                pass


        if '.' in formula:
            section_name, field_label = formula.split('.', 1)
            return _get_field_value(section_name.strip(), field_label.strip(), context)
        else:

            return _get_field_value(None, formula.strip(), context)

    except Exception as e:
        print(f"Error evaluating calculation '{formula}': {str(e)}")
        return None


def _evaluate_aggregation(func_name: str, section_name: str, field_label: str, context: Dict) -> Optional[float]:
    """Evaluate aggregation functions (sum, count, avg)"""
    sections_data = context.get('sections_data', {})
    invoice_values = context.get('invoice_values', [])
    calculated_values = context.get('calculated_values', {})

    print(f"DEBUG CALC: _evaluate_aggregation - func={func_name}, section='{section_name}', field='{field_label}'")
    print(f"DEBUG CALC: Available sections: {list(sections_data.keys())}")


    section_data = None
    for title, data in sections_data.items():
        if title and section_name and isinstance(title, str) and isinstance(section_name, str):
            if title.lower() == section_name.lower():
                section_data = data
                print(f"DEBUG CALC: Found section by name match: '{title}' == '{section_name}'")
                break
        elif section_name == 'line_items' and data.get('type') == 'line_item':
            section_data = data
            print(f"DEBUG CALC: Found section by line_items fallback: '{title}'")
            break

    if not section_data or section_data.get('type') != 'line_item':
        print(f"DEBUG CALC: Section not found or not a line_item section")
        return None


    values = []
    line_item_rows = section_data.get('line_item_rows', {})

    print(f"DEBUG CALC: Line item rows type: {type(line_item_rows)}, length: {len(line_item_rows) if isinstance(line_item_rows, (list, dict)) else 'N/A'}")


    if isinstance(line_item_rows, dict):

        for ordinal, row in line_item_rows.items():
            if isinstance(row, list):
                for value in row:
                    if value and value.get('field_label'):
                        field_label_lower = value.get('field_label', '').lower()
                        search_label_lower = field_label.lower()
                        print(f"DEBUG CALC: Comparing field '{field_label_lower}' with search '{search_label_lower}'")
                        if field_label_lower == search_label_lower:
                            print(f"DEBUG CALC: Field match! Value structure: data_type={value.get('data_type')}, val_number={value.get('val_number')}, val_string={value.get('val_string')}, has_field_id={bool(value.get('field_id'))}, formula={value.get('calculation_formula')}")

                            field_id = value.get('field_id')
                            if field_id:
                                calc_key = (field_id, ordinal)
                                if calc_key in calculated_values:
                                    calc_val = float(calculated_values[calc_key])
                                    print(f"DEBUG CALC: Found calculated value for '{field_label}': {calc_val}")
                                    values.append(calc_val)
                                    continue
                                
                                formula = value.get('calculation_formula')
                                if formula:
                                    print(f"DEBUG CALC: Field '{field_label}' has formula '{formula}' but not in calculated_values yet. Attempting to calculate...")
                                    try:
                                        context = {
                                            'sections_data': sections_data,
                                            'invoice_values': invoice_values,
                                            'calculated_values': calculated_values.copy(),
                                            'current_section': section_name,
                                            'current_row': row,
                                            'current_row_index': ordinal
                                        }
                                        calc_val = evaluate_calculation(formula, context)
                                        if calc_val is not None:
                                            print(f"DEBUG CALC: Calculated value on-the-fly for '{field_label}': {calc_val}")
                                            values.append(float(calc_val))
                                            continue
                                    except Exception as e:
                                        print(f"DEBUG CALC: Error calculating field on-the-fly: {e}")

                            data_type = value.get('data_type')
                            val_number = value.get('val_number')
                            print(f"DEBUG CALC: Checking value - data_type='{data_type}', val_number={val_number}, type(val_number)={type(val_number)}")
                            
                            if data_type == 'number' and val_number is not None:
                                try:
                                    stored_val = float(val_number)
                                    print(f"DEBUG CALC: Found stored value for '{field_label}': {stored_val}")
                                    values.append(stored_val)
                                except (ValueError, TypeError) as e:
                                    print(f"DEBUG CALC: Error converting val_number to float: {e}, val_number={val_number}")
                            else:
                                print(f"DEBUG CALC: Value not added - data_type='{data_type}' (expected 'number'), val_number={val_number} (expected not None)")
    elif isinstance(line_item_rows, list):

        for row_idx, row in enumerate(line_item_rows):
            if isinstance(row, list):
                for value in row:
                    if value and value.get('field_label'):
                        field_label_lower = value.get('field_label', '').lower()
                        search_label_lower = field_label.lower()
                        print(f"DEBUG CALC: Comparing field '{field_label_lower}' with search '{search_label_lower}'")
                        if field_label_lower == search_label_lower:
                            print(f"DEBUG CALC: Field match! Value structure: data_type={value.get('data_type')}, val_number={value.get('val_number')}, val_string={value.get('val_string')}, has_field_id={bool(value.get('field_id'))}, formula={value.get('calculation_formula')}")

                            field_id = value.get('field_id')
                            ordinal = value.get('value_ordinal', 0) or 0
                            
                            if field_id:
                                calc_key = (field_id, ordinal)
                                if calc_key in calculated_values:
                                    calc_val = float(calculated_values[calc_key])
                                    print(f"DEBUG CALC: Found calculated value for '{field_label}': {calc_val}")
                                    values.append(calc_val)
                                    continue
                                
                                formula = value.get('calculation_formula')
                                if formula:
                                    print(f"DEBUG CALC: Field '{field_label}' has formula '{formula}' but not in calculated_values yet. Attempting to calculate...")
                                    try:
                                        context = {
                                            'sections_data': sections_data,
                                            'invoice_values': invoice_values,
                                            'calculated_values': calculated_values.copy(),
                                            'current_section': section_name,
                                            'current_row': row,
                                            'current_row_index': row_idx
                                        }
                                        calc_val = evaluate_calculation(formula, context)
                                        if calc_val is not None:
                                            print(f"DEBUG CALC: Calculated value on-the-fly for '{field_label}': {calc_val}")
                                            values.append(float(calc_val))
                                            continue
                                    except Exception as e:
                                        print(f"DEBUG CALC: Error calculating field on-the-fly: {e}")

                            data_type = value.get('data_type')
                            val_number = value.get('val_number')
                            print(f"DEBUG CALC: Checking value - data_type='{data_type}', val_number={val_number}, type(val_number)={type(val_number)}")
                            
                            if data_type == 'number' and val_number is not None:
                                try:
                                    stored_val = float(val_number)
                                    print(f"DEBUG CALC: Found stored value for '{field_label}': {stored_val}")
                                    values.append(stored_val)
                                except (ValueError, TypeError) as e:
                                    print(f"DEBUG CALC: Error converting val_number to float: {e}, val_number={val_number}")
                            else:
                                print(f"DEBUG CALC: Value not added - data_type='{data_type}' (expected 'number'), val_number={val_number} (expected not None)")

    print(f"DEBUG CALC: Collected {len(values)} values: {values}")

    if not values:
        print(f"DEBUG CALC: No values found for field '{field_label}' in section '{section_name}'")
        return 0.0

    if func_name == 'sum':
        result = sum(values)
        print(f"DEBUG CALC: Sum result: {result}")
        return result
    elif func_name == 'count':
        result = float(len(values))
        print(f"DEBUG CALC: Count result: {result}")
        return result
    elif func_name == 'avg':
        result = sum(values) / len(values) if values else 0.0
        print(f"DEBUG CALC: Avg result: {result}")
        return result

    return None


def _evaluate_row_calculation(formula: str, context: Dict) -> Optional[float]:
    """Evaluate row-level calculations using 'this.field_label'"""
    current_row = context.get('current_row', [])
    current_section = context.get('current_section')



    def replace_this_ref_quoted(match):

        field_label = match.group(1) if match.group(1) else match.group(2)
        if not field_label:
            return match.group(0)

        for value in current_row:
            if value and value.get('field_label', '').lower() == field_label.lower():
                if value.get('data_type') == 'number':
                    return str(value.get('val_number', 0))
        return '0'

    def replace_this_ref_unquoted(match):
        field_label = match.group(1)
        if not field_label:
            return match.group(0)

        for value in current_row:
            if value and value.get('field_label', '').lower() == field_label.lower():
                if value.get('data_type') == 'number':
                    return str(value.get('val_number', 0))
        return '0'


    formula = re.sub(r'this\.["\']([^"\']+)["\']|this\.\[([^\]]+)\]',
                     replace_this_ref_quoted,
                     formula, flags=re.IGNORECASE)


    pattern = r'this\.([a-zA-Z_][a-zA-Z0-9_]*)'
    formula = re.sub(pattern, replace_this_ref_unquoted, formula, flags=re.IGNORECASE)


    try:

        allowed_chars = set('0123456789.+-*/() ')
        if all(c in allowed_chars for c in formula.replace(' ', '')):
            result = eval(formula)
            return float(result) if result is not None else None
    except:
        pass

    return None


def _get_field_value(section_name: Optional[str], field_label: str, context: Dict) -> Optional[float]:
    """Get a field value by section and label"""
    sections_data = context.get('sections_data', {})
    invoice_values = context.get('invoice_values', [])
    calculated_values = context.get('calculated_values', {})


    if section_name:
        for title, data in sections_data.items():
            if title.lower() == section_name.lower():

                if data.get('type') == 'line_item':

                    line_item_rows = data.get('line_item_rows', [])
                    values = []
                    if isinstance(line_item_rows, list):
                        for row in line_item_rows:
                            if isinstance(row, list):
                                for value in row:
                                    if value and value.get('field_label', '').lower() == field_label.lower():
                                        if value.get('data_type') == 'number' and value.get('val_number') is not None:
                                            values.append(float(value.get('val_number')))
                    elif isinstance(line_item_rows, dict):

                        for ordinal, row_values in line_item_rows.items():
                            for value in row_values:
                                if value and value.get('field_label', '').lower() == field_label.lower():
                                    if value.get('data_type') == 'number' and value.get('val_number') is not None:
                                        values.append(float(value.get('val_number')))
                    return sum(values) if values else None
                else:

                    for value in data.get('fields', []):
                        if value and value.get('field_label', '').lower() == field_label.lower():

                            field_id = value.get('field_id')
                            if field_id:
                                calc_key = (field_id, 0)
                                if calc_key in calculated_values:
                                    return float(calculated_values[calc_key])

                            if value.get('data_type') == 'number':
                                val = value.get('val_number')
                                if val is not None:
                                    return float(val)
    else:

        for title, data in sections_data.items():
            if data.get('type') != 'line_item':
                for value in data.get('fields', []):
                    if value and value.get('field_label', '').lower() == field_label.lower():

                        field_id = value.get('field_id')
                        if field_id:
                            calc_key = (field_id, 0)
                            if calc_key in calculated_values:
                                print(f"DEBUG CALC: Found '{field_label}' in calculated_values: {calculated_values[calc_key]}")
                                return float(calculated_values[calc_key])

                        if value.get('data_type') == 'number':
                            val = value.get('val_number')
                            if val is not None:
                                print(f"DEBUG CALC: Found '{field_label}' in stored value: {val}")
                                return float(val)

    print(f"DEBUG CALC: Field '{field_label}' not found in any section")
    return None


def calculate_invoice_fields(invoice_values: List[Dict], sections_data: Dict) -> Dict[str, Dict[str, float]]:
    """
    Calculate all calculated fields for an invoice.

    Returns:
        Dictionary mapping (field_id, ordinal) tuple to calculated value
        Format: {(field_id, ordinal): value}
    """
    calculated_values = {}
    base_context = {
        'invoice_values': invoice_values,
        'sections_data': sections_data
    }



    max_passes = 10
    for pass_num in range(max_passes):
        new_values = {}
        values_changed = False

        print(f"DEBUG CALC: Starting pass {pass_num + 1}")


        for section_title, section_info in sections_data.items():
            section_type = section_info.get('type')

            if section_type == 'line_item':

                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value:
                                formula = value.get('calculation_formula')
                                field_id = value.get('field_id')
                                field_label = value.get('field_label', '')

                                if formula:
                                    ordinal = value.get('value_ordinal', 0) or 0
                                    key = (field_id, ordinal)



                                    context = base_context.copy()
                                    context['current_section'] = section_title
                                    context['current_row'] = row
                                    context['current_row_index'] = row_idx
                                    context['calculated_values'] = calculated_values.copy()

                                    calculated_value = evaluate_calculation(formula, context)


                                    old_value = calculated_values.get(key)
                                    if calculated_value is not None:
                                        if old_value is None or abs(float(calculated_value) - float(old_value)) > 0.0001:
                                            new_values[key] = calculated_value
                                            values_changed = True
                                            print(f"DEBUG CALC: Pass {pass_num + 1}: Field '{field_label}' (id: {field_id}) = {calculated_value} (was: {old_value})")
                                        else:

                                            new_values[key] = calculated_value
                                    elif old_value is not None:

                                        values_changed = True
            else:

                for value in section_info.get('fields', []):
                    if value:
                        formula = value.get('calculation_formula')
                        field_id = value.get('field_id')
                        field_label = value.get('field_label', '')

                        if formula:
                            key = (field_id, 0)


                            context = base_context.copy()
                            context['current_section'] = section_title
                            context['current_row'] = []
                            context['calculated_values'] = calculated_values.copy()

                            calculated_value = evaluate_calculation(formula, context)


                            old_value = calculated_values.get(key)
                            if calculated_value is not None:
                                if old_value is None or abs(float(calculated_value) - float(old_value)) > 0.0001:
                                    new_values[key] = calculated_value
                                    values_changed = True
                                    print(f"DEBUG CALC: Pass {pass_num + 1}: Field '{field_label}' (id: {field_id}) = {calculated_value} (was: {old_value})")
                                else:

                                    new_values[key] = calculated_value
                            elif old_value is not None:

                                values_changed = True


        calculated_values.update(new_values)


        if not values_changed:
            print(f"DEBUG CALC: No values changed in pass {pass_num + 1}, calculation complete")
            break

    print(f"DEBUG CALC: Completed after {pass_num + 1} passes, calculated {len(calculated_values)} values")
    return calculated_values

