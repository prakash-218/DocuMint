"""
Reading a costing out of a spreadsheet (.xlsx or .csv) someone already made.

The workbook is read once, nothing is kept: each sheet comes back as a grid of cell values
(the cached results of formulas, as Excel last saved them) with a guess at its heading row
and which column holds what. The editor shows the grid, the person corrects the guess, and
the rows become items or cost lines there.
"""

import csv
import io
import re
from datetime import date, datetime
from typing import Dict, List, Optional

MAX_SHEETS, MAX_ROWS, MAX_COLS = 20, 400, 20
MAX_BYTES = 5 * 1024 * 1024
HEADING_ROWS = 30                     # the heading row is looked for this far down

# What a heading says, for each thing the editor needs. The first match wins, so price is
# looked for before quantity ("Price in Rs/Qty" is a price) and amount ("Unit cost" isn't a total).
FIELDS = (
    ('price', r'\brate\b|price|unit\s*cost|cost\s*(per|/|each)|per\s*(unit|kg|no|pc)|/\s*(kg|no|nos|pc|qty)\b|\beach\b'),
    ('amount', r'amount|total|value|^cost$|^cost\s*\(|^cost\s*in\b'),
    ('qty', r'\bqty\b|quantity|^nos\.?$|^no\.?\s*of|^pcs?$'),            # "No" alone is the serial number
    ('unit', r'^(unit|units|uom|u\.?o\.?m\.?|per)$'),
    ('spec', r'spec|make|brand|model|grade|size|material\s*grade|remarks?'),
    ('name', r'item|descri|particulars?|^name$|material|component|part|work|activity|details?|scope'),
)


class SheetError(ValueError):
    pass


def _cell(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    text = str(value).strip()
    return text or None


def _trim(rows: List[List]) -> List[List]:
    """Drop the empty rows at the end and the empty columns on the right."""
    while rows and not any(v is not None for v in rows[-1]):
        rows.pop()
    width = max((max((i + 1 for i, v in enumerate(r) if v is not None), default=0) for r in rows), default=0)
    return [r[:width] + [None] * (width - len(r[:width])) for r in rows]


def guess_columns(rows: List[List]) -> Dict:
    """The heading row (0-based; None if there's none) and the column of each field it names."""
    best, best_cols = None, {}
    for i, row in enumerate(rows[:HEADING_ROWS]):
        cols: Dict[str, int] = {}
        for j, value in enumerate(row):
            if not isinstance(value, str) or len(value) > 60:
                continue
            label = re.sub(r'\s+', ' ', value.strip().lower())
            for field, pattern in FIELDS:
                if field not in cols and re.search(pattern, label):
                    cols[field] = j
                    break
        if len(cols) >= 2 and ('name' in cols or 'spec' in cols) and len(cols) > len(best_cols):
            best, best_cols = i, cols
    if best is not None and 'name' not in best_cols:             # "Description | Spec" sheets: spec is the name
        best_cols['name'] = best_cols.pop('spec')
    return {'header_row': best, 'columns': best_cols}


def _sheet(name: str, rows: List[List]) -> Dict:
    rows = _trim(rows)
    return {'name': name, 'rows': rows, **guess_columns(rows)}


def read(stream, filename: str) -> Dict:
    """{'file': name, 'sheets': [{'name', 'rows', 'header_row', 'columns'}]}, sheets with no data left out."""
    data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SheetError('That file is over 5 MB. Save just the costing sheet and try again.')
    lower = (filename or '').lower()
    if lower.endswith('.csv'):
        sheets = [_read_csv(data, filename)]
    elif lower.endswith(('.xlsx', '.xlsm')):
        sheets = _read_xlsx(data)
    elif lower.endswith('.xls'):
        raise SheetError('That is an old .xls workbook. Open it in Excel, save it as .xlsx, and try again.')
    else:
        raise SheetError('Choose an Excel workbook (.xlsx) or a .csv file.')
    sheets = [s for s in sheets if s['rows']]
    if not sheets:
        raise SheetError('There is nothing in that file to import.')
    return {'file': filename, 'sheets': sheets}


def _read_xlsx(data: bytes) -> List[Dict]:
    from zipfile import BadZipFile
    import openpyxl
    try:
        book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except (BadZipFile, KeyError, ValueError, OSError):
        raise SheetError("That file couldn't be read as an Excel workbook.")
    try:
        sheets = []
        for ws in book.worksheets[:MAX_SHEETS]:
            if getattr(ws, 'sheet_state', 'visible') != 'visible':
                continue
            rows = []
            for row in ws.iter_rows(max_row=MAX_ROWS, max_col=MAX_COLS, values_only=True):
                rows.append([_cell(v) for v in row])
            sheets.append(_sheet(ws.title, rows))
        return sheets
    finally:
        book.close()


def _read_csv(data: bytes, filename: str) -> Dict:
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if len(rows) >= MAX_ROWS:
            break
        rows.append([_number_or_text(v) for v in row[:MAX_COLS]])
    name = re.sub(r'\.csv$', '', filename or 'Sheet', flags=re.I)
    return _sheet(name, rows)


def _number_or_text(value: str):
    value = value.strip()
    if not value:
        return None
    plain = re.sub(r'[,\s₹$]', '', value)
    try:
        return float(plain) if re.fullmatch(r'-?\d+(\.\d+)?', plain) else value
    except ValueError:
        return value
