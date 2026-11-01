"""What the document editor posts, read once for saving and for the live preview (invoice_service.form_values)."""
from werkzeug.datastructures import MultiDict

from invoice_service import form_values

FIELDS = [
    {'field_id': 'd', 'section_id': 'S-items', 'section_type': 'line_item', 'data_type': 'string'},
    {'field_id': 'q', 'section_id': 'S-items', 'section_type': 'line_item', 'data_type': 'number'},
    {'field_id': 'r', 'section_id': 'S-items', 'section_type': 'line_item', 'data_type': 'number'},
    {'field_id': 'po', 'section_id': 'S-ref', 'section_type': 'normal', 'data_type': 'string'},
    {'field_id': 'on', 'section_id': 'S-ref', 'section_type': 'normal', 'data_type': 'date'},
    {'field_id': 'ok', 'section_id': 'S-ref', 'section_type': 'normal', 'data_type': 'boolean'},
]


def test_lines_by_row_and_every_field_of_a_section():
    form = MultiDict({'line_item_S-items_2_field_d': ' Hob arbor ', 'line_item_S-items_2_field_q': '2', 'line_item_S-items_2_field_r': '9500',
                      'line_item_S-items_1_field_d': 'Drill jig', 'line_item_S-items_1_field_q': '', 'line_item_S-items_1_field_r': 'abc',
                      'line_item_S-other_1_field_d': 'not this template\'s', 'field_po': 'PO 4411', 'field_on': '2026-11-01', 'field_ok': 'on'})
    got = {(v['field_id'], v['value_ordinal']): (v['val_string'], v['val_number'], v['val_date'], v['val_boolean']) for v in form_values(form, FIELDS)}
    assert got == {
        ('d', 1): ('Drill jig', None, None, None), ('q', 1): (None, None, None, None), ('r', 1): (None, None, None, None),
        ('d', 2): ('Hob arbor', None, None, None), ('q', 2): (None, 2.0, None, None), ('r', 2): (None, 9500.0, None, None),
        # every field of a section that isn't a table, not only its last one
        ('po', None): ('PO 4411', None, None, None), ('on', None): (None, None, '2026-11-01', None), ('ok', None): (None, None, None, 1),
    }


def test_a_field_left_empty_is_cleared():
    got = form_values(MultiDict({'field_po': ''}), FIELDS[3:4])
    assert got == [{'field_id': 'po', 'value_ordinal': None, 'val_string': None, 'val_number': None, 'val_date': None, 'val_boolean': None}]
