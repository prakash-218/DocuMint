"""
Calculation engine for invoice field formulas (AST-based, via simpleeval).

Formula syntax (names are case-insensitive; spaces in names become underscores):
- Field references:      qty * price, subtotal + tax
- Section.field:         summary.subtotal  (a line-item field here is the sum of its column)
- Row-level references:  this.qty * this.unit_price  (inside a line-item section)
- Aggregates:            SUM(items.amount), AVG(items.rate), COUNT(items), MIN(...), MAX(...)
- Helpers:               ROUND(x, 2), ABS(x), GET("section.field")
- Basic math:            + - * / ( ) and numeric literals

Bare names resolve in this order: field in the current line-item row, field in a
normal section, line-item column (summed), then line-item section (for COUNT).

The engine is pure: it takes the template's fields plus the invoice's stored
values and returns {(field_id, ordinal): value} for every formula cell. It never
touches the database.
"""

import logging
import re
from typing import Dict, Iterable, List, Optional, Tuple

from simpleeval import SimpleEval, NameNotDefined

logger = logging.getLogger(__name__)

CellKey = Tuple[str, int]

FUNCTION_NAMES = ('SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'ROUND', 'ABS', 'GET')
_REF_FUNC = 'REF__'


class FormulaError(Exception):
    """A formula could not be evaluated (bad syntax, unknown name, divide by zero...)"""


def normalize_name(name: Optional[str]) -> str:
    return (name or '').strip().replace(' ', '_').lower()


class Column(float):
    """A line-item column. Behaves as the column's sum in arithmetic, and keeps
    the individual row values for SUM/AVG/COUNT/MIN/MAX."""

    def __new__(cls, values: List[float]):
        obj = super().__new__(cls, sum(values))
        obj.values = values
        return obj


class SectionRef:
    """A bare reference to a line-item section, e.g. COUNT(items)."""

    def __init__(self, row_count: int):
        self.row_count = row_count


def _as_number(value) -> float:
    if value is None or value == '':
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class _Field:
    __slots__ = ('field_id', 'name', 'aliases', 'section', 'formula')

    def __init__(self, field_id, name, aliases, section, formula):
        self.field_id = field_id
        self.name = name
        self.aliases = aliases
        self.section = section
        self.formula = formula


class _Section:
    __slots__ = ('name', 'aliases', 'type', 'fields', 'rows')

    def __init__(self, name, aliases, section_type):
        self.name = name
        self.aliases = aliases
        self.type = section_type
        self.fields: List[_Field] = []
        self.rows: List[int] = []  # ordinals, line-item sections only

    def field(self, name) -> Optional[_Field]:
        return next((f for f in self.fields if name in f.aliases), None)


class InvoiceModel:
    """Template structure plus current cell values for one invoice."""

    def __init__(self, fields: Iterable[Dict], values: Iterable[Dict]):
        self.sections: Dict[str, _Section] = {}
        self.fields: Dict[str, _Field] = {}
        self.cells: Dict[CellKey, float] = {}

        for row in fields:
            self._add_field(row)

        for value in values:
            field_id = value.get('field_id')
            if not field_id:
                continue
            if field_id not in self.fields:
                # Value rows carry their field's metadata, so a value whose field
                # wasn't passed in still contributes to the model
                self._add_field(value)
            field = self.fields[field_id]
            ordinal = (value.get('value_ordinal') or 0) if field.section.type == 'line_item' else 0
            self.cells[(field_id, ordinal)] = _as_number(value.get('val_number'))
            if field.section.type == 'line_item' and ordinal not in field.section.rows:
                field.section.rows.append(ordinal)

        for section in self.sections.values():
            section.rows.sort()

    def _add_field(self, row: Dict):
        field_id = row.get('field_id')
        if not field_id or field_id in self.fields:
            return
        section_name = normalize_name(row.get('section_name') or row.get('section_display_name')
                                      or row.get('section_title'))
        section = self.sections.get(section_name)
        if section is None:
            aliases = {section_name, normalize_name(row.get('section_display_name')),
                       normalize_name(row.get('section_title'))} - {''}
            section = _Section(section_name, aliases, row.get('section_type') or 'normal')
            self.sections[section_name] = section
        name = normalize_name(row.get('field_name') or row.get('name') or row.get('field_display_name'))
        aliases = {name, normalize_name(row.get('field_display_name')), normalize_name(row.get('label')),
                   normalize_name(row.get('field_label'))} - {''}
        formula = (row.get('calculation_formula') or '').strip()
        if formula.lower() == 'none':
            formula = ''
        field = _Field(field_id, name, aliases, section, formula or None)
        section.fields.append(field)
        self.fields[field_id] = field

    def find_section(self, name) -> Optional[_Section]:
        return next((s for s in self.sections.values() if name in s.aliases), None)

    def formula_cells(self) -> List[Tuple[CellKey, _Field]]:
        cells = []
        for section in self.sections.values():
            ordinals = section.rows if section.type == 'line_item' else [0]
            for ordinal in ordinals:
                for field in section.fields:
                    if field.formula:
                        cells.append(((field.field_id, ordinal), field))
        return cells


def _prepare(formula: str) -> str:
    """Rewrite dotted references into REF__ calls and normalise function names."""
    # Older formulas quote references: SUM("items.total") -> SUM(items.total)
    formula = re.sub(r'["\']([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)["\']', r'\1', formula)
    formula = re.sub(r'(?<![\w.])([A-Za-z_]\w*)\.([A-Za-z_]\w*)',
                     lambda m: f'{_REF_FUNC}("{m.group(1).lower()}", "{m.group(2).lower()}")', formula)
    formula = re.sub(r'\b(' + '|'.join(FUNCTION_NAMES) + r')\s*\(',
                     lambda m: m.group(1).upper() + '(', formula, flags=re.IGNORECASE)
    return formula


class _Evaluator:
    """Evaluates one formula in the context of a section and (for line items) a row."""

    def __init__(self, model: InvoiceModel, section: _Section, ordinal: int):
        self.model = model
        self.section = section
        self.ordinal = ordinal if section.type == 'line_item' else None
        self.engine = SimpleEval(
            names=self._resolve_name,
            functions={
                _REF_FUNC: self._ref,
                'SUM': self._sum, 'AVG': self._avg, 'COUNT': self._count,
                'MIN': self._min, 'MAX': self._max,
                'ROUND': lambda x, n=0: round(float(x), int(n)),
                'ABS': lambda x: abs(float(x)),
                'GET': self._get,
            },
        )

    def evaluate(self, formula: str) -> float:
        try:
            result = self.engine.eval(_prepare(formula))
        except ZeroDivisionError:
            raise FormulaError('division by zero')
        except FormulaError:
            raise
        except Exception as e:
            raise FormulaError(str(e) or e.__class__.__name__)
        if isinstance(result, SectionRef):
            raise FormulaError('a section is not a number')
        return float(result)

    # -- name resolution -------------------------------------------------

    def _cell(self, field: _Field, ordinal: int = 0) -> float:
        return self.model.cells.get((field.field_id, ordinal), 0.0)

    def _column(self, section: _Section, field: _Field) -> Column:
        return Column([self._cell(field, o) for o in section.rows])

    def _lookup(self, name: str):
        if self.ordinal is not None:
            field = self.section.field(name)
            if field:
                return self._cell(field, self.ordinal)
        for section in self.model.sections.values():
            if section.type != 'line_item':
                field = section.field(name)
                if field:
                    return self._cell(field)
        for section in self.model.sections.values():
            if section.type == 'line_item':
                field = section.field(name)
                if field:
                    return self._column(section, field)
        section = self.model.find_section(name)
        if section and section.type == 'line_item':
            return SectionRef(len(section.rows))
        return None

    def _resolve_name(self, node):
        value = self._lookup(node.id.lower())
        if value is None:
            raise NameNotDefined(node.id, '')
        return value

    def _ref(self, owner: str, name: str):
        if owner == 'this':
            if self.ordinal is None:
                raise FormulaError('this.%s used outside a line-item section' % name)
            field = self.section.field(name)
            if not field:
                raise FormulaError('unknown field this.%s' % name)
            return self._cell(field, self.ordinal)
        section = self.model.find_section(owner)
        if not section:
            raise FormulaError('unknown section %s' % owner)
        field = section.field(name)
        if not field:
            raise FormulaError('unknown field %s.%s' % (owner, name))
        if section.type == 'line_item':
            return self._column(section, field)
        return self._cell(field)

    def _get(self, ref):
        if isinstance(ref, str):
            ref = normalize_name(ref)
            if '.' in ref:
                return self._ref(*ref.split('.', 1))
            value = self._lookup(ref)
            if value is None:
                raise FormulaError('unknown field %s' % ref)
            return value
        return ref

    # -- aggregates --------------------------------------------------------

    def _values(self, args) -> List[float]:
        values = []
        for arg in args:
            arg = self._get(arg)
            if isinstance(arg, Column):
                values.extend(arg.values)
            elif isinstance(arg, SectionRef):
                raise FormulaError('aggregate needs a field, e.g. SUM(section.field)')
            else:
                values.append(float(arg))
        return values

    def _sum(self, *args):
        return sum(self._values(args))

    def _avg(self, *args):
        values = self._values(args)
        return sum(values) / len(values) if values else 0.0

    def _count(self, *args):
        total = 0
        for arg in args:
            arg = self._get(arg) if isinstance(arg, str) else arg
            if isinstance(arg, SectionRef):
                total += arg.row_count
            elif isinstance(arg, Column):
                total += len(arg.values)
            else:
                total += 1
        return float(total)

    def _min(self, *args):
        values = self._values(args)
        return min(values) if values else 0.0

    def _max(self, *args):
        values = self._values(args)
        return max(values) if values else 0.0


def calculate(fields: Iterable[Dict], values: Iterable[Dict]) -> Dict[CellKey, float]:
    """
    Evaluate every formula cell of an invoice.

    Args:
        fields: template field rows for the invoice's template version
                (sp_get_template_fields_by_version). May be empty, in which case
                the field metadata on the value rows is used.
        values: invoice value rows (sp_get_invoice_details, second result set)

    Returns:
        {(field_id, ordinal): value} for each formula cell that evaluated.
        Normal-section cells use ordinal 0.
    """
    model = InvoiceModel(fields, values)
    formula_cells = model.formula_cells()
    results: Dict[CellKey, float] = {}

    # Re-evaluate until nothing changes, so formulas can depend on each other
    # in any order. Acyclic formulas settle within len(formula_cells) passes;
    # anything still changing after that is a cycle and is left as computed.
    for _ in range(len(formula_cells) + 1):
        changed = False
        for key, field in formula_cells:
            try:
                value = _Evaluator(model, field.section, key[1]).evaluate(field.formula)
            except FormulaError as e:
                if key in results:
                    del results[key]
                    changed = True
                logger.debug("Formula %r for field %s failed: %s", field.formula, field.name, e)
                continue
            if key not in results or abs(results[key] - value) > 1e-9:
                results[key] = value
                model.cells[key] = value
                changed = True
        if not changed:
            break

    return results


def validate_formula(formula: str, fields: Iterable[Dict], section_name: str) -> Optional[str]:
    """Check a formula against a template's fields. Returns an error message, or None if valid."""
    model = InvoiceModel(fields, [])
    section = model.find_section(normalize_name(section_name))
    if section is None:
        section = _Section(normalize_name(section_name), {normalize_name(section_name)}, 'normal')
    if section.type == 'line_item' and not section.rows:
        section.rows.append(0)
    try:
        _Evaluator(model, section, 0).evaluate(formula)
    except FormulaError as e:
        # Every cell is empty during validation, so dividing by a field is expected
        if str(e) == 'division by zero':
            return None
        return str(e)
    return None


def calculate_invoice_fields(invoice_values: List[Dict], sections_data: Dict = None) -> Dict[CellKey, float]:
    """Backward-compatible wrapper used by the data scripts: value rows carry
    their field metadata, so sections_data is no longer needed."""
    return calculate([], invoice_values)
