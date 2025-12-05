"""
Calculation engine for invoice field calculations using simpleeval (AST-based).

Supports:
- Field references: field_name or section_name.field_name
  - Field names should use underscores (no spaces) as they are stored in the database
  - Examples: Quantity * Unit_Price, Subtotal + Tax_Amount
- Line item aggregations: SUM(section_name.field_name), AVG(), COUNT()
  - Examples: SUM(Line_Items.Amount), AVG(Line_Items.Rate)
- Row-level calculations: this.field_name (within same line item row)
  - Examples: this.Quantity * this.Unit_Price
- Basic math: +, -, *, /, (, )
- Custom functions: SUM(), AVG(), COUNT(), GET()
"""

from simpleeval import SimpleEval, NameNotDefined, FunctionNotDefined
from typing import Dict, List, Any, Optional
import re


class InvoiceEvaluator(SimpleEval):
    """Custom evaluator for invoice calculations"""
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__()
        self.context = context
        self.names = {}
        self.functions = {
            'SUM': self._sum_function,
            'AVG': self._avg_function,
            'COUNT': self._count_function,
            'GET': self._get_function,
        }
        
        self._build_namespace()
    
    def _build_namespace(self):
        """Build namespace with field values and row context"""
        sections_data = self.context.get('sections_data', {})
        current_section = self.context.get('current_section')
        current_row = self.context.get('current_row', [])
        calculated_values = self.context.get('calculated_values', {})
        
        if current_row:
            for value in current_row:
                if value:
                    # Use field_name (no spaces) for formulas, fallback to display_name or label
                    field_name = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
                    if field_name:
                        # Convert to formula-friendly name (no spaces, lowercase)
                        field_name_normalized = field_name.replace(' ', '_').lower()
                        field_id = value.get('field_id')
                        ordinal = value.get('value_ordinal', 0) or 0
                        
                        if field_id:
                            calc_key = (field_id, ordinal)
                            if calc_key in calculated_values:
                                self.names[field_name_normalized] = float(calculated_values[calc_key])
                                continue
                        
                        val_number = value.get('val_number')
                        if val_number is not None:
                            self.names[field_name_normalized] = float(val_number)
                        
                        # Also add the original field_name if it's different (for backward compatibility)
                        if field_name != field_name_normalized:
                            if field_id:
                                calc_key = (field_id, ordinal)
                                if calc_key in calculated_values:
                                    self.names[field_name] = float(calculated_values[calc_key])
                                else:
                                    val_number = value.get('val_number')
                                    if val_number is not None:
                                        self.names[field_name] = float(val_number)
        
        # Add all normal section fields to namespace (not just current section)
        # This allows formulas like "total * 0.1" to reference fields from other normal sections
        for section_title, section_data in sections_data.items():
            if section_data.get('type') == 'normal':
                for field in section_data.get('fields', []):
                    # Use field_name (no spaces) for formulas
                    field_name = field.get('field_name') or field.get('field_display_name') or field.get('field_label', '')
                    if field_name:
                        # Convert to formula-friendly name (no spaces, lowercase)
                        field_name = field_name.replace(' ', '_').lower()
                        field_id = field.get('field_id')
                        if field_id:
                            calc_key = (field_id, 0)
                            # First check calculated values
                            if calc_key in calculated_values:
                                self.names[field_name] = float(calculated_values[calc_key])
                            else:
                                # Try to get value from invoice_values
                                found = False
                                invoice_values = self.context.get('invoice_values', [])
                                for value in invoice_values:
                                    if value.get('field_id') == field_id:
                                        val_number = value.get('val_number')
                                        if val_number is not None:
                                            self.names[field_name] = float(val_number)
                                            found = True
                                        break
                                # If not found, initialize to 0 so it can be referenced in formulas
                                # It will be updated when calculated
                                if not found and field_name not in self.names:
                                    self.names[field_name] = 0.0
    
    def _get_field_value(self, section_name: Optional[str], field_name: str) -> Optional[float]:
        """Get field value by section and field name (supports both field_name and field_label for backward compatibility)"""
        sections_data = self.context.get('sections_data', {})
        invoice_values = self.context.get('invoice_values', [])
        calculated_values = self.context.get('calculated_values', {})
        current_section = self.context.get('current_section')
        
        # Normalize field name (no spaces, lowercase)
        field_name = field_name.replace(' ', '_').lower()
        
        def get_field_name(value):
            # Use field_name (no spaces) for formulas, fallback to display_name or label
            name = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
            return name.replace(' ', '_').lower() if name else ''
        
        def get_section_name(value):
            # Use section name (no spaces) for formulas, fallback to display_name or title
            name = value.get('section_name') or value.get('section_display_name') or value.get('section_title', '')
            return name.replace(' ', '_').lower() if name else ''
        
        if section_name:
            # Normalize section name
            section_name = section_name.replace(' ', '_').lower()
            
            section_data = sections_data.get(section_name)
            if not section_data:
                for title, data in sections_data.items():
                    # Try to match by name (no spaces) or display_name
                    title_name = data.get('name') or title
                    if title_name:
                        title_name = title_name.replace(' ', '_').lower()
                        if title_name == section_name:
                            section_data = data
                            break
            
            if section_data:
                if section_data.get('type') == 'line_item':
                    line_item_rows = section_data.get('line_item_rows', {})
                    values = []
                    
                    if isinstance(line_item_rows, dict):
                        for ordinal, row in line_item_rows.items():
                            if isinstance(row, list):
                                for value in row:
                                    field_name_val = get_field_name(value)
                                    if value and field_name_val == field_name:
                                        field_id = value.get('field_id')
                                        ordinal_val = value.get('value_ordinal', 0) or 0
                                        
                                        if field_id:
                                            calc_key = (field_id, ordinal_val)
                                            if calc_key in calculated_values:
                                                values.append(float(calculated_values[calc_key]))
                                                continue
                                        
                                        val_number = value.get('val_number')
                                        if val_number is not None:
                                            values.append(float(val_number))
                    
                    if values:
                        return sum(values) if len(values) > 1 else values[0]
                else:
                    for value in invoice_values:
                        section_name_val = get_section_name(value)
                        field_name_val = get_field_name(value)
                        if (section_name_val == section_name and
                            field_name_val == field_name):
                            field_id = value.get('field_id')
                            if field_id:
                                calc_key = (field_id, 0)
                                if calc_key in calculated_values:
                                    return float(calculated_values[calc_key])
                            
                            val_number = value.get('val_number')
                            if val_number is not None:
                                return float(val_number)
        else:
            if current_section:
                section_data = sections_data.get(current_section, {})
                if section_data.get('type') == 'normal':
                    for field in section_data.get('fields', []):
                        field_name_val = get_field_name(field)
                        if field_name_val == field_name:
                            field_id = field.get('field_id')
                            if field_id:
                                calc_key = (field_id, 0)
                                if calc_key in calculated_values:
                                    return float(calculated_values[calc_key])
                            
                            val_number = field.get('val_number')
                            if val_number is not None:
                                return float(val_number)
            
            for value in invoice_values:
                field_name_val = get_field_name(value)
                if field_name_val == field_name:
                    field_id = value.get('field_id')
                    if field_id:
                        calc_key = (field_id, value.get('value_ordinal', 0) or 0)
                        if calc_key in calculated_values:
                            return float(calculated_values[calc_key])
                    
                    val_number = value.get('val_number')
                    if val_number is not None:
                        return float(val_number)
        
        return None
    
    def _sum_function(self, section_field_ref) -> float:
        """SUM(section_name.field_name) - sum all values in a line item section"""
        # Handle string arguments (quoted) or variable references
        if isinstance(section_field_ref, str):
            # Remove quotes if present
            if section_field_ref.startswith('"') and section_field_ref.endswith('"'):
                section_field_ref = section_field_ref[1:-1]
            elif section_field_ref.startswith("'") and section_field_ref.endswith("'"):
                section_field_ref = section_field_ref[1:-1]
        else:
            # Convert to string if it's not already
            section_field_ref = str(section_field_ref)
        
        section_name, field_name = self._parse_section_field(section_field_ref)
        # Normalize names (no spaces, lowercase)
        section_name = section_name.replace(' ', '_').lower()
        field_name = field_name.replace(' ', '_').lower()
        
        sections_data = self.context.get('sections_data', {})
        calculated_values = self.context.get('calculated_values', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                # Try to match by name (no spaces) or display_name
                title_name = data.get('name') or title
                if title_name:
                    title_name = title_name.replace(' ', '_').lower()
                    if title_name == section_name:
                        section_data = data
                        break
        
        if not section_data or section_data.get('type') != 'line_item':
            print(f"DEBUG CALC SUM: Section '{section_name}' not found or not a line_item. Available sections: {list(sections_data.keys())}")
            return 0.0
        
        print(f"DEBUG CALC SUM: Found section '{section_name}', looking for field '{field_name}'")
        
        line_item_rows = section_data.get('line_item_rows', {})
        values = []
        
        # Handle both dict and list formats
        if isinstance(line_item_rows, dict):
            for ordinal, row in line_item_rows.items():
                if isinstance(row, list):
                    for value in row:
                        # Use field_name (no spaces) for formulas
                        field_name_val = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
                        if field_name_val:
                            field_name_val = field_name_val.replace(' ', '_').lower()
                            if value and field_name_val == field_name:
                                field_id = value.get('field_id')
                                if field_id:
                                    calc_key = (field_id, ordinal)
                                    if calc_key in calculated_values:
                                        values.append(float(calculated_values[calc_key]))
                                        continue
                                
                                val_number = value.get('val_number')
                                if val_number is not None:
                                    values.append(float(val_number))
        elif isinstance(line_item_rows, list):
            # Handle list format (rows are already ordered by ordinal)
            print(f"DEBUG CALC SUM: Processing {len(line_item_rows)} rows in list format")
            for row_idx, row in enumerate(line_item_rows):
                if isinstance(row, list):
                    for value in row:
                        # Use field_name (no spaces) for formulas
                        field_name_val = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
                        if field_name_val:
                            field_name_val = field_name_val.replace(' ', '_').lower()
                            if value and field_name_val == field_name:
                                field_id = value.get('field_id')
                                ordinal = value.get('value_ordinal', row_idx)  # Use value_ordinal if available, otherwise use row_idx
                                if field_id:
                                    calc_key = (field_id, ordinal)
                                    print(f"DEBUG CALC SUM: Checking calc_key {calc_key} in calculated_values (has {len(calculated_values)} values)")
                                    if calc_key in calculated_values:
                                        val = float(calculated_values[calc_key])
                                        print(f"DEBUG CALC SUM: Found calculated value {val} for {calc_key}")
                                        values.append(val)
                                        continue
                                
                                val_number = value.get('val_number')
                                if val_number is not None:
                                    print(f"DEBUG CALC SUM: Using val_number {val_number} for field {field_name_val}")
                                    values.append(float(val_number))
        
        print(f"DEBUG CALC SUM: Collected {len(values)} values: {values}, sum = {sum(values) if values else 0.0}")
        
        return sum(values) if values else 0.0
    
    def _avg_function(self, section_field_ref) -> float:
        """AVG(section_name.field_name) - average of values in a line item section"""
        # Handle string arguments (quoted) or variable references
        if isinstance(section_field_ref, str):
            if section_field_ref.startswith('"') and section_field_ref.endswith('"'):
                section_field_ref = section_field_ref[1:-1]
            elif section_field_ref.startswith("'") and section_field_ref.endswith("'"):
                section_field_ref = section_field_ref[1:-1]
        else:
            section_field_ref = str(section_field_ref)
        
        values_sum = self._sum_function(section_field_ref)
        section_name, field_name = self._parse_section_field(section_field_ref)
        # Normalize names
        section_name = section_name.replace(' ', '_').lower()
        field_name = field_name.replace(' ', '_').lower()
        
        sections_data = self.context.get('sections_data', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                title_name = data.get('name') or title
                if title_name:
                    title_name = title_name.replace(' ', '_').lower()
                    if title_name == section_name:
                        section_data = data
                        break
        
        if not section_data or section_data.get('type') != 'line_item':
            return 0.0
        
        line_item_rows = section_data.get('line_item_rows', {})
        count = 0
        
        if isinstance(line_item_rows, dict):
            for ordinal, row in line_item_rows.items():
                if isinstance(row, list):
                    for value in row:
                        field_name_val = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
                        if field_name_val:
                            field_name_val = field_name_val.replace(' ', '_').lower()
                            if value and field_name_val == field_name:
                                count += 1
                                break
        
        return values_sum / count if count > 0 else 0.0
    
    def _count_function(self, section_field_ref) -> float:
        """COUNT(section_name) - count rows in a line item section"""
        # Handle string arguments (quoted) or variable references
        if isinstance(section_field_ref, str):
            if section_field_ref.startswith('"') and section_field_ref.endswith('"'):
                section_field_ref = section_field_ref[1:-1]
            elif section_field_ref.startswith("'") and section_field_ref.endswith("'"):
                section_field_ref = section_field_ref[1:-1]
        else:
            section_field_ref = str(section_field_ref)
        
        section_name = section_field_ref.split('.')[0] if '.' in section_field_ref else section_field_ref
        # Normalize section name
        section_name = section_name.replace(' ', '_').lower()
        
        sections_data = self.context.get('sections_data', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                title_name = data.get('name') or title
                if title_name:
                    title_name = title_name.replace(' ', '_').lower()
                    if title_name == section_name:
                        section_data = data
                        break
        
        if not section_data or section_data.get('type') != 'line_item':
            return 0.0
        
        line_item_rows = section_data.get('line_item_rows', {})
        if isinstance(line_item_rows, dict):
            return float(len(line_item_rows))
        
        return 0.0
    
    def _get_function(self, field_ref) -> float:
        """GET(field_name) or GET(section_name.field_name) - get a field value"""
        # Handle string arguments (quoted) or variable references
        if isinstance(field_ref, str):
            # Remove quotes if present
            if field_ref.startswith('"') and field_ref.endswith('"'):
                field_ref = field_ref[1:-1]
            elif field_ref.startswith("'") and field_ref.endswith("'"):
                field_ref = field_ref[1:-1]
        else:
            # Convert to string if it's not already
            field_ref = str(field_ref)
        
        if '.' in field_ref:
            section_name, field_name = field_ref.split('.', 1)
            value = self._get_field_value(section_name.strip(), field_name.strip())
        else:
            value = self._get_field_value(None, field_ref.strip())
        
        return float(value) if value is not None else 0.0
    
    def _parse_section_field(self, ref: str) -> tuple:
        """Parse 'section_name.field_name' into tuple"""
        if '.' in ref:
            parts = ref.split('.', 1)
            return parts[0].strip(), parts[1].strip()
        return 'line_items', ref.strip()


def evaluate_calculation(formula: str, context: Dict[str, Any]) -> Optional[float]:
    """
    Evaluate a calculation formula using AST-based evaluation.
    
    Args:
        formula: Calculation formula string (e.g., "SUM(Line_Items.Amount)", "this.Quantity * this.Unit_Price")
        context: Dictionary containing:
            - 'invoice_values': List of all invoice values
            - 'sections_data': Organized sections data
            - 'current_section': Current section name
            - 'current_row': Current row (for line items)
            - 'calculated_values': Already calculated values
    
    Returns:
        Calculated value (float) or None if calculation fails
    """
    if not formula or not formula.strip():
        return None
    
    formula = formula.strip()
    
    try:
        # Process this. references first (before building evaluator namespace)
        if 'this.' in formula.lower():
            formula = _process_this_references(formula, context)
        
        evaluator = InvoiceEvaluator(context)
        
        # Process section.field references
        formula = _process_section_field_references(formula, evaluator)
        
        # Also add current row fields to namespace for direct field name access (in case this. was already processed)
        current_row = context.get('current_row', [])
        calculated_values = context.get('calculated_values', {})
        if current_row:
            for value in current_row:
                if value:
                    field_name = value.get('field_name') or value.get('field_display_name') or value.get('field_label', '')
                    if field_name:
                        field_name_norm = field_name.replace(' ', '_').lower()
                        field_id = value.get('field_id')
                        ordinal = value.get('value_ordinal', 0) or 0
                        
                        if field_id:
                            calc_key = (field_id, ordinal)
                            if calc_key in calculated_values:
                                evaluator.names[field_name_norm] = float(calculated_values[calc_key])
                                continue
                        
                        val_number = value.get('val_number')
                        if val_number is not None:
                            evaluator.names[field_name_norm] = float(val_number)
        
        result = evaluator.eval(formula)
        return float(result) if result is not None else None
        
    except (NameNotDefined, FunctionNotDefined, SyntaxError, ValueError, TypeError) as e:
        print(f"Error evaluating calculation '{formula}': {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error evaluating calculation '{formula}': {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def _process_this_references(formula: str, context: Dict) -> str:
    """Replace 'this.field_name' with actual values from current row"""
    current_row = context.get('current_row', [])
    calculated_values = context.get('calculated_values', {})
    
    def replace_this(match):
        field_name_from_formula = match.group(1)
        # Normalize field name from formula (no spaces, lowercase)
        field_name_normalized = field_name_from_formula.replace(' ', '_').lower()
        
        # Build a map of all possible field name variations to values
        field_value_map = {}
        available_fields = []
        
        for value in current_row:
            if value:
                # Try multiple field name sources
                field_name = value.get('field_name', '')
                field_display_name = value.get('field_display_name', '')
                field_label = value.get('field_label', '')
                
                # Normalize all variants and add to map
                if field_name:
                    field_name_norm = field_name.replace(' ', '_').lower()
                    field_value_map[field_name_norm] = value
                    available_fields.append(field_name_norm)
                if field_display_name:
                    field_display_name_norm = field_display_name.replace(' ', '_').lower()
                    field_value_map[field_display_name_norm] = value
                    if field_display_name_norm not in available_fields:
                        available_fields.append(field_display_name_norm)
                if field_label:
                    field_label_norm = field_label.replace(' ', '_').lower()
                    field_value_map[field_label_norm] = value
                    if field_label_norm not in available_fields:
                        available_fields.append(field_label_norm)
        
        # Check if normalized name matches any variant
        if field_name_normalized in field_value_map:
            value = field_value_map[field_name_normalized]
            field_id = value.get('field_id')
            ordinal = value.get('value_ordinal', 0) or 0
            
            if field_id:
                calc_key = (field_id, ordinal)
                if calc_key in calculated_values:
                    return str(calculated_values[calc_key])
            
            val_number = value.get('val_number')
            if val_number is not None:
                return str(val_number)
        
        # If not found, return 0 but log for debugging
        print(f"DEBUG CALC: Field '{field_name_normalized}' not found in current row.")
        print(f"DEBUG CALC: Available fields: {available_fields}")
        print(f"DEBUG CALC: Current row data: {[(v.get('field_name') or v.get('field_display_name') or v.get('field_label', ''), v.get('val_number')) for v in current_row if v]}")
        return '0'
    
    # Match this.field_name where field_name can contain underscores
    pattern = r'this\.([a-zA-Z_][a-zA-Z0-9_]*)'
    return re.sub(pattern, replace_this, formula, flags=re.IGNORECASE)


def _process_section_field_references(formula: str, evaluator: InvoiceEvaluator) -> str:
    """Replace 'section_name.field_name' with GET() function calls, but preserve inside SUM/AVG/COUNT"""
    # Quote section.field arguments in SUM/AVG/COUNT so they're passed as strings
    # Pattern: SUM(items.total) -> SUM("items.total")
    # Other section.field references become GET("section.field")
    
    # First, protect SUM/AVG/COUNT function calls by replacing them with placeholders
    protected_formula = formula
    protected_refs = {}
    protected_counter = [0]
    
    def protect_sum_avg_count(match):
        func_name = match.group(1)
        arg = match.group(2)
        # If the argument contains a dot, it's likely section.field - protect the entire function call
        if '.' in arg and func_name.upper() in ['SUM', 'AVG', 'COUNT']:
            # Quote the argument
            quoted_arg = f'"{arg}"' if not (arg.startswith('"') and arg.endswith('"')) else arg
            key = f"__PROTECTED_{protected_counter[0]}__"
            protected_counter[0] += 1
            protected_refs[key] = f'{func_name}({quoted_arg})'
            return key
        return match.group(0)
    
    # Protect SUM/AVG/COUNT function calls
    protected_formula = re.sub(r'(SUM|AVG|COUNT)\(([^)]+)\)', protect_sum_avg_count, protected_formula, flags=re.IGNORECASE)
    
    # Now convert remaining section.field references to GET() calls with quoted strings
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
    
    def replace_ref(match):
        section_name = match.group(1)
        field_name = match.group(2)
        if section_name.lower() not in ['sum', 'avg', 'count', 'get', 'this']:
            return f'GET("{section_name}.{field_name}")'
        return match.group(0)
    
    result = re.sub(pattern, replace_ref, protected_formula)
    
    # Restore protected function calls
    for key, value in protected_refs.items():
        result = result.replace(key, value)
    
    return result


def calculate_invoice_fields(invoice_values: List[Dict], sections_data: Dict) -> Dict:
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
        
        for section_title, section_info in sections_data.items():
            if section_title is None:
                print(f"DEBUG CALC: Skipping section with None title")
                continue
                
            section_type = section_info.get('type')
            
            if section_type == 'line_item':
                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        if not isinstance(row, list):
                            print(f"DEBUG CALC: Row {row_idx} is not a list, it's {type(row)}")
                            continue
                        for value in row:
                            if value:
                                formula = value.get('calculation_formula')
                                field_id = value.get('field_id')
                                
                                if formula and field_id:
                                    ordinal = value.get('value_ordinal', 0) or 0
                                    key = (field_id, ordinal)
                                    
                                    context = base_context.copy()
                                    context['current_section'] = section_title
                                    context['current_row'] = row
                                    context['current_row_index'] = row_idx
                                    context['calculated_values'] = calculated_values.copy()
                                    
                                    print(f"DEBUG CALC: Evaluating formula '{formula}' for field_id {field_id}, ordinal {ordinal} in section '{section_title}', row {row_idx}")
                                    calculated_value = evaluate_calculation(formula, context)
                                    print(f"DEBUG CALC: Result: {calculated_value}")
                                    
                                    old_value = calculated_values.get(key)
                                    if calculated_value is not None:
                                        if old_value is None or abs(float(calculated_value) - float(old_value)) > 0.0001:
                                            new_values[key] = calculated_value
                                            values_changed = True
                                            print(f"DEBUG CALC: Updated value for {key}: {old_value} -> {calculated_value}")
                                    elif old_value is not None:
                                        values_changed = True
            else:
                for value in section_info.get('fields', []):
                    if value:
                        formula = value.get('calculation_formula')
                        field_id = value.get('field_id')
                        
                        if formula:
                            key = (field_id, 0)
                            
                            context = base_context.copy()
                            context['current_section'] = section_title
                            context['calculated_values'] = calculated_values.copy()
                            
                            calculated_value = evaluate_calculation(formula, context)
                            
                            old_value = calculated_values.get(key)
                            if calculated_value is not None:
                                if old_value is None or abs(float(calculated_value) - float(old_value)) > 0.0001:
                                    new_values[key] = calculated_value
                                    values_changed = True
                            elif old_value is not None:
                                values_changed = True
        
        calculated_values.update(new_values)
        
        if not values_changed:
            break
    
    return calculated_values
