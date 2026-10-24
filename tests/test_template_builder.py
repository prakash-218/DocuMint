from werkzeug.datastructures import MultiDict

from template_builder import sections_from_form


def test_builder_form_parsing():
    form = MultiDict({
        'section_count': '3',
        's1_present': '1', 's1_title': 'Items', 's1_type': 'line_item', 's1_field_count': '4',
        's1_f1_present': '1', 's1_f1_label': 'Description', 's1_f1_type': 'string',
        's1_f2_present': '1', 's1_f2_label': 'Quantity', 's1_f2_name': 'qty', 's1_f2_type': 'number',   # renamed label keeps its name
        's1_f3_present': '1', 's1_f3_label': 'Rate', 's1_f3_type': 'number', 's1_f3_currency': 'on',
        's1_f4_present': '', 's1_f4_label': 'Removed', 's1_f4_type': 'string',
        's2_present': '', 's2_title': 'Gone', 's2_field_count': '1', 's2_f1_present': '1', 's2_f1_label': 'x',
        's3_present': '1', 's3_title': 'Totals', 's3_type': 'normal', 's3_field_count': '2',
        's3_f1_present': '1', 's3_f1_label': 'Notes', 's3_f1_type': 'string', 's3_f1_currency': 'on', 's3_f1_formula': 'x',
        's3_f2_present': '1', 's3_f2_label': 'Grand Total', 's3_f2_type': 'number', 's3_f2_currency': 'on',
        's3_f2_formula': 'SUM(items.amount)', 's3_f2_required': 'on',
        'total': '3:2',
    })
    sections, total = sections_from_form(form)
    assert [s['name'] for s in sections] == ['items', 'totals']
    assert [f['name'] for f in sections[0]['fields']] == ['description', 'qty', 'rate']
    assert sections[0]['fields'][1]['label'] == 'Quantity' and sections[0]['fields'][2]['currency']
    notes, grand = sections[1]['fields']
    assert not notes['currency'] and notes['formula'] == ''           # only numbers are money / calculated
    assert grand['name'] == 'grand_total' and not grand['required']   # calculated fields aren't typed in
    assert total == (1, 1)
