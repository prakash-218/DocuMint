"""
Calculation engine for invoice field calculations.

Supports:
- Field references: field_label or section.field_label
- Line item aggregations: sum(line_items.field_label), count(line_items.field_label), avg(line_items.field_label)
- Row-level calculations: this.field_label (within same line item row)
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
        # Handle line item aggregations: sum(line_items.field_label), count(...), avg(...)
        aggregation_match = re.match(r'^(sum|count|avg)\(([^)]+)\)$', formula, re.IGNORECASE)
        if aggregation_match:
            func_name = aggregation_match.group(1).lower()
            field_ref = aggregation_match.group(2).strip()
            
            # Parse section.field_label or just field_label
            if '.' in field_ref:
                section_name, field_label = field_ref.split('.', 1)
                section_name = section_name.strip()
                field_label = field_label.strip()
            else:
                # Default to line_items section if not specified
                section_name = 'line_items'
                field_label = field_ref.strip()
            
            return _evaluate_aggregation(func_name, section_name, field_label, context)
        
        # Handle row-level calculations with "this." prefix
        if 'this.' in formula.lower():
            return _evaluate_row_calculation(formula, context)
        
        # Handle formulas with field references and math operations (e.g., "total * 0.1", "subtotal + tax")
        # Replace field references with their numeric values
        formula_processed = formula
        
        # Find all potential field names (words that aren't keywords or numbers)
        # Match words that could be field names
        field_names = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)
        print(f"DEBUG CALC: Processing formula '{formula}', found field names: {field_names}")
        for field_name in field_names:
            # Skip if it's a math keyword
            if field_name.lower() in ['sum', 'count', 'avg', 'this']:
                continue
            # Get the field value by label
            value = _get_field_value(None, field_name, context)
            if value is not None:
                print(f"DEBUG CALC: Found field '{field_name}' = {value}")
                # Replace the field name with its value (use word boundaries to avoid partial matches)
                formula_processed = re.sub(r'\b' + re.escape(field_name) + r'\b', str(value), formula_processed, flags=re.IGNORECASE)
            else:
                print(f"DEBUG CALC: Field '{field_name}' not found or has no value")
        
        print(f"DEBUG CALC: Formula after field replacement: '{formula_processed}'")
        
        # Now evaluate the formula as a math expression
        # Only allow safe operations
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
        
        # Fallback: try field reference
        if '.' in formula:
            section_name, field_label = formula.split('.', 1)
            return _get_field_value(section_name.strip(), field_label.strip(), context)
        else:
            # Try to find field in current section or any section
            return _get_field_value(None, formula.strip(), context)
    
    except Exception as e:
        print(f"Error evaluating calculation '{formula}': {str(e)}")
        return None


def _evaluate_aggregation(func_name: str, section_name: str, field_label: str, context: Dict) -> Optional[float]:
    """Evaluate aggregation functions (sum, count, avg)"""
    sections_data = context.get('sections_data', {})
    invoice_values = context.get('invoice_values', [])
    
    # Find the section
    section_data = None
    for title, data in sections_data.items():
        if title.lower() == section_name.lower() or (section_name == 'line_items' and data.get('type') == 'line_item'):
            section_data = data
            break
    
    if not section_data or section_data.get('type') != 'line_item':
        return None
    
    # Get all values for this field across all rows
    values = []
    line_item_rows = section_data.get('line_item_rows', [])
    
    for row in line_item_rows:
        for value in row:
            if value and value.get('field_label', '').lower() == field_label.lower():
                if value.get('data_type') == 'number' and value.get('val_number') is not None:
                    values.append(float(value.get('val_number')))
    
    if not values:
        return 0.0
    
    if func_name == 'sum':
        return sum(values)
    elif func_name == 'count':
        return float(len(values))
    elif func_name == 'avg':
        return sum(values) / len(values) if values else 0.0
    
    return None


def _evaluate_row_calculation(formula: str, context: Dict) -> Optional[float]:
    """Evaluate row-level calculations using 'this.field_label'"""
    current_row = context.get('current_row', [])
    current_section = context.get('current_section')
    
    # Replace this.field_label with actual values
    def replace_this_ref(match):
        field_label = match.group(1)
        # Find value in current row
        for value in current_row:
            if value and value.get('field_label', '').lower() == field_label.lower():
                if value.get('data_type') == 'number':
                    return str(value.get('val_number', 0))
        return '0'
    
    # Replace all this.field_label references
    pattern = r'this\.([a-zA-Z_][a-zA-Z0-9_]*)'
    formula = re.sub(pattern, replace_this_ref, formula, flags=re.IGNORECASE)
    
    # Evaluate the formula as Python expression
    try:
        # Only allow safe operations
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
    
    # If section specified, look in that section
    if section_name:
        for title, data in sections_data.items():
            if title.lower() == section_name.lower():
                # Look in fields or line items
                if data.get('type') == 'line_item':
                    # For line items, sum all values (or could return first/last)
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
                        # Handle dict format {ordinal: [values]}
                        for ordinal, row_values in line_item_rows.items():
                            for value in row_values:
                                if value and value.get('field_label', '').lower() == field_label.lower():
                                    if value.get('data_type') == 'number' and value.get('val_number') is not None:
                                        values.append(float(value.get('val_number')))
                    return sum(values) if values else None
                else:
                    # Normal section
                    for value in data.get('fields', []):
                        if value and value.get('field_label', '').lower() == field_label.lower():
                            # First check if this field has a calculated value (prioritize calculated values)
                            field_id = value.get('field_id')
                            if field_id:
                                calc_key = (field_id, 0)
                                if calc_key in calculated_values:
                                    return float(calculated_values[calc_key])
                            # Then check stored value
                            if value.get('data_type') == 'number':
                                val = value.get('val_number')
                                if val is not None:
                                    return float(val)
    else:
        # Search all sections (prioritize normal sections for field lookups)
        for title, data in sections_data.items():
            if data.get('type') != 'line_item':
                for value in data.get('fields', []):
                    if value and value.get('field_label', '').lower() == field_label.lower():
                        # First check if this field has a calculated value (prioritize calculated values)
                        field_id = value.get('field_id')
                        if field_id:
                            calc_key = (field_id, 0)
                            if calc_key in calculated_values:
                                print(f"DEBUG CALC: Found '{field_label}' in calculated_values: {calculated_values[calc_key]}")
                                return float(calculated_values[calc_key])
                        # Then check stored value
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
    
    # Multiple passes to handle dependencies between calculated fields
    max_passes = 5  # Safety limit
    for pass_num in range(max_passes):
        new_values = {}
        
        # Process each section
        for section_title, section_info in sections_data.items():
            section_type = section_info.get('type')
            
            if section_type == 'line_item':
                # Process line item rows
                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value:
                                formula = value.get('calculation_formula')
                                field_id = value.get('field_id')
                                field_label = value.get('field_label', '')
                                
                                if formula:
                                    print(f"DEBUG CALC: Found formula for field '{field_label}' (id: {field_id}): {formula}")
                                    # Skip if already calculated
                                    ordinal = value.get('value_ordinal', 0) or 0
                                    key = (field_id, ordinal)
                                    if key in calculated_values:
                                        print(f"DEBUG CALC: Already calculated for {key}")
                                        continue
                                    
                                    context = base_context.copy()
                                    context['current_section'] = section_title
                                    context['current_row'] = row
                                    context['current_row_index'] = row_idx
                                    context['calculated_values'] = calculated_values
                                    
                                    calculated_value = evaluate_calculation(formula, context)
                                    print(f"DEBUG CALC: Evaluated '{formula}' = {calculated_value}")
                                    if calculated_value is not None:
                                        new_values[key] = calculated_value
                                        if ordinal != row_idx:
                                            new_values[(field_id, row_idx)] = calculated_value
                                else:
                                    print(f"DEBUG CALC: No formula for field '{field_label}' (id: {field_id})")
            else:
                # Process normal section fields
                for value in section_info.get('fields', []):
                    if value:
                        formula = value.get('calculation_formula')
                        field_id = value.get('field_id')
                        field_label = value.get('field_label', '')
                        
                        if formula:
                            print(f"DEBUG CALC: Found formula for field '{field_label}' (id: {field_id}): {formula}")
                            # Skip if already calculated
                            key = (field_id, 0)
                            if key in calculated_values:
                                print(f"DEBUG CALC: Already calculated for {key}")
                                continue
                            
                            context = base_context.copy()
                            context['current_section'] = section_title
                            context['current_row'] = []
                            context['calculated_values'] = calculated_values
                            
                            calculated_value = evaluate_calculation(formula, context)
                            print(f"DEBUG CALC: Evaluated '{formula}' = {calculated_value}")
                            if calculated_value is not None:
                                new_values[key] = calculated_value
                        else:
                            print(f"DEBUG CALC: No formula for field '{field_label}' (id: {field_id})")
        
        # Update calculated_values with new values
        calculated_values.update(new_values)
        
        # If no new values were calculated, we're done
        if not new_values:
            break
    
    return calculated_values

