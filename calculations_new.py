"""
Calculation engine for invoice field calculations using simpleeval (AST-based).

Supports:
- Field references: field_name or section_name.field_name
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
                    field_name = value.get('field_name') or value.get('field_label', '')
                    if field_name:
                        field_id = value.get('field_id')
                        ordinal = value.get('value_ordinal', 0) or 0
                        
                        if field_id:
                            calc_key = (field_id, ordinal)
                            if calc_key in calculated_values:
                                self.names[field_name] = float(calculated_values[calc_key])
                                continue
                        
                        val_number = value.get('val_number')
                        if val_number is not None:
                            self.names[field_name] = float(val_number)
        
        if current_section:
            section_data = sections_data.get(current_section, {})
            if section_data.get('type') == 'normal':
                for field in section_data.get('fields', []):
                    field_name = field.get('field_name') or field.get('field_label', '')
                    if field_name:
                        field_id = field.get('field_id')
                        if field_id:
                            calc_key = (field_id, 0)
                            if calc_key in calculated_values:
                                self.names[field_name] = float(calculated_values[calc_key])
                            else:
                                val_number = field.get('val_number')
                                if val_number is not None:
                                    self.names[field_name] = float(val_number)
    
    def _get_field_value(self, section_name: Optional[str], field_name: str) -> Optional[float]:
        """Get field value by section and field name (supports both field_name and field_label for backward compatibility)"""
        sections_data = self.context.get('sections_data', {})
        invoice_values = self.context.get('invoice_values', [])
        calculated_values = self.context.get('calculated_values', {})
        current_section = self.context.get('current_section')
        
        def get_field_name(value):
            return value.get('field_name') or value.get('field_label', '')
        
        def get_section_name(value):
            return value.get('section_name') or value.get('section_title', '')
        
        if section_name:
            section_data = sections_data.get(section_name)
            if not section_data:
                for title, data in sections_data.items():
                    title_name = data.get('name') or title
                    if title_name and isinstance(title_name, str) and title_name.lower() == section_name.lower():
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
                                    if value and field_name_val.lower() == field_name.lower():
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
                        if (section_name_val.lower() == section_name.lower() and
                            field_name_val.lower() == field_name.lower()):
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
                        if field_name_val.lower() == field_name.lower():
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
                if field_name_val.lower() == field_name.lower():
                    field_id = value.get('field_id')
                    if field_id:
                        calc_key = (field_id, value.get('value_ordinal', 0) or 0)
                        if calc_key in calculated_values:
                            return float(calculated_values[calc_key])
                    
                    val_number = value.get('val_number')
                    if val_number is not None:
                        return float(val_number)
        
        return None
    
    def _sum_function(self, section_field_ref: str) -> float:
        """SUM(section_name.field_name) - sum all values in a line item section"""
        section_name, field_name = self._parse_section_field(section_field_ref)
        sections_data = self.context.get('sections_data', {})
        calculated_values = self.context.get('calculated_values', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                if title and isinstance(title, str) and title.lower() == section_name.lower():
                    section_data = data
                    break
        
        if not section_data or section_data.get('type') != 'line_item':
            return 0.0
        
        line_item_rows = section_data.get('line_item_rows', {})
        values = []
        
        if isinstance(line_item_rows, dict):
            for ordinal, row in line_item_rows.items():
                if isinstance(row, list):
                    for value in row:
                        field_name_val = value.get('field_name') or value.get('field_label', '')
                        if value and field_name_val.lower() == field_name.lower():
                            field_id = value.get('field_id')
                            if field_id:
                                calc_key = (field_id, ordinal)
                                if calc_key in calculated_values:
                                    values.append(float(calculated_values[calc_key]))
                                    continue
                            
                            val_number = value.get('val_number')
                            if val_number is not None:
                                values.append(float(val_number))
        
        return sum(values) if values else 0.0
    
    def _avg_function(self, section_field_ref: str) -> float:
        """AVG(section_name.field_name) - average of values in a line item section"""
        values_sum = self._sum_function(section_field_ref)
        section_name, field_name = self._parse_section_field(section_field_ref)
        sections_data = self.context.get('sections_data', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                if title and isinstance(title, str) and title.lower() == section_name.lower():
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
                        field_name_val = value.get('field_name') or value.get('field_label', '')
                        if value and field_name_val.lower() == field_name.lower():
                            count += 1
                            break
        
        return values_sum / count if count > 0 else 0.0
    
    def _count_function(self, section_field_ref: str) -> float:
        """COUNT(section_name) - count rows in a line item section"""
        section_name = section_field_ref.split('.')[0] if '.' in section_field_ref else section_field_ref
        sections_data = self.context.get('sections_data', {})
        
        section_data = sections_data.get(section_name)
        if not section_data:
            for title, data in sections_data.items():
                if title and isinstance(title, str) and title.lower() == section_name.lower():
                    section_data = data
                    break
        
        if not section_data or section_data.get('type') != 'line_item':
            return 0.0
        
        line_item_rows = section_data.get('line_item_rows', {})
        if isinstance(line_item_rows, dict):
            return float(len(line_item_rows))
        
        return 0.0
    
    def _get_function(self, field_ref: str) -> float:
        """GET(field_name) or GET(section_name.field_name) - get a field value"""
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
        evaluator = InvoiceEvaluator(context)
        
        if 'this.' in formula.lower():
            formula = _process_this_references(formula, context)
        
        formula = _process_section_field_references(formula, evaluator)
        
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
        field_name = match.group(1)
        for value in current_row:
            if value:
                field_name_val = value.get('field_name') or value.get('field_label', '')
                if field_name_val.lower() == field_name.lower():
                    field_id = value.get('field_id')
                    ordinal = value.get('value_ordinal', 0) or 0
                    
                    if field_id:
                        calc_key = (field_id, ordinal)
                        if calc_key in calculated_values:
                            return str(calculated_values[calc_key])
                    
                    val_number = value.get('val_number')
                    if val_number is not None:
                        return str(val_number)
        return '0'
    
    pattern = r'this\.([a-zA-Z_][a-zA-Z0-9_]*)'
    return re.sub(pattern, replace_this, formula, flags=re.IGNORECASE)


def _process_section_field_references(formula: str, evaluator: InvoiceEvaluator) -> str:
    """Replace 'section_name.field_name' with GET() function calls"""
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
    
    def replace_ref(match):
        section_name = match.group(1)
        field_name = match.group(2)
        if section_name.lower() not in ['sum', 'avg', 'count', 'get', 'this']:
            return f'GET({section_name}.{field_name})'
        return match.group(0)
    
    return re.sub(pattern, replace_ref, formula)


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
            section_type = section_info.get('type')
            
            if section_type == 'line_item':
                line_item_rows = section_info.get('line_item_rows', [])
                if isinstance(line_item_rows, list):
                    for row_idx, row in enumerate(line_item_rows):
                        for value in row:
                            if value:
                                formula = value.get('calculation_formula')
                                field_id = value.get('field_id')
                                field_name = value.get('field_name', '')
                                
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
                                    elif old_value is not None:
                                        values_changed = True
            else:
                for value in section_info.get('fields', []):
                    if value:
                        formula = value.get('calculation_formula')
                        field_id = value.get('field_id')
                        field_name = value.get('field_name', '')
                        
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

