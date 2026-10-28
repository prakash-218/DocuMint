from layout import (DEFAULT_PAGES, defs_from_form, normalize, packing_page, pages_for, printed_customer_fields,
                    printed_org_fields)


def test_empty_layout_gets_defaults():
    layout = normalize(None)
    assert [p['key'] for p in layout['pages']] == ['document', 'packing']
    assert layout == normalize({'pages': []})


def test_document_page_is_always_first_and_unique():
    layout = normalize({'pages': [
        {'kind': 'annexure', 'title': 'Terms'},
        {'kind': 'document', 'with_document': False},
        {'kind': 'document'},
    ]})
    assert [p['kind'] for p in layout['pages']] == ['document', 'annexure']
    assert layout['pages'][0]['with_document'] is True


def test_bad_values_are_cleaned():
    layout = normalize({'pages': [
        {'kind': 'document'},
        {'kind': 'packing', 'title': 'Shipping list', 'doc_types': ['export_invoice', 'nonsense'],
         'box_fields': [{'label': 'Pallet no.'}, {'label': ''}, {'label': 'Net Wt', 'sum': 1}]},
        {'kind': 'weird', 'title': 'Annex A', 'sections': ['breakup', 'breakup']},
    ]})
    pack = layout['pages'][1]
    assert pack['key'] == 'shipping_list' and pack['doc_types'] == ['export_invoice']
    assert pack['box_fields'] == [{'key': 'pallet_no', 'label': 'Pallet no.', 'sum': False},
                                  {'key': 'net_wt', 'label': 'Net Wt', 'sum': True}]
    annex = layout['pages'][2]
    assert annex['kind'] == 'annexure' and annex['sections'] == ['breakup']


def test_pages_apply_by_document_type():
    layout = normalize(None)
    assert [p['key'] for p in pages_for(layout, 'invoice')] == ['document']
    assert [p['key'] for p in pages_for(layout, 'export_invoice')] == ['document', 'packing']
    assert packing_page(layout, 'export_invoice')['box_fields'] == DEFAULT_PAGES[1]['box_fields']
    assert packing_page(layout, 'quote') is None


def test_custom_field_rows_from_form():
    form = {'org_label_1': 'MSME No.', 'org_value_1': 'UDYAM-TN-02-0001', 'org_print_1': 'on',
            'org_label_2': '', 'org_value_2': 'ignored',
            'org_label_3': 'CIN', 'org_value_3': 'U123', 'org_key_3': 'cin'}
    rows = defs_from_form(form, 'org', with_value=True)
    assert rows == [{'key': 'msme_no', 'label': 'MSME No.', 'print': True, 'value': 'UDYAM-TN-02-0001'},
                    {'key': 'cin', 'label': 'CIN', 'print': False, 'value': 'U123'}]
    profile = {'custom_fields': rows, 'customer_fields': [{'key': 'vendor_code', 'label': 'Vendor code', 'print': True},
                                                          {'key': 'plant', 'label': 'Plant', 'print': False}]}
    assert [f['label'] for f in printed_org_fields(profile)] == ['MSME No.']
    assert printed_customer_fields(profile, '{"vendor_code": "V-77", "plant": "Hosur"}') == [
        {'label': 'Vendor code', 'value': 'V-77'}]


def test_layout_from_form():
    from werkzeug.datastructures import MultiDict
    from layout import layout_from_form
    form = MultiDict([
        ('page_count', '3'),
        ('page_1_present', '1'), ('page_1_kind', 'document'), ('page_1_copies', 'Original\nDuplicate\n'),
        ('page_2_present', '1'), ('page_2_kind', 'packing'), ('page_2_title', 'Shipping list'),
        ('page_2_doc_types', 'export_invoice'), ('page_2_columns', 'description'), ('page_2_columns', 'qty'),
        ('page_2_box_label_1', 'Dimensions'), ('page_2_box_key_1', 'dimensions'),
        ('page_2_box_label_2', 'Pallet no.'), ('page_2_box_label_3', 'Net Wt (kg)'), ('page_2_box_sum_3', 'on'),
        ('page_3_kind', 'annexure'),            # removed in the editor (no _present)
    ])
    layout = layout_from_form(form)
    doc, pack = layout['pages']
    assert doc['copies'] == ['Original', 'Duplicate']
    assert pack['key'] == 'shipping_list' and pack['columns'] == ['description', 'qty']
    assert [(f['key'], f['sum']) for f in pack['box_fields']] == [('dimensions', False), ('pallet_no', False),
                                                                 ('net_wt_kg', True)]


def test_what_a_template_is_for():
    from layout import template_types
    assert template_types('Proforma Invoice', {}) == ['proforma']
    assert template_types('Quotation with cost break-up', {}) == ['quote']
    assert template_types('Export Invoice', {}) == ['invoice']
    assert template_types('Job card', {}) == ['quote', 'proforma', 'invoice']          # says nothing: any type
    assert template_types('Quotation', normalize({'used_for': ['quote', 'invoice', 'export_invoice']})) == ['quote', 'invoice']
    assert template_types('Quotation', normalize({'used_for': []})) == ['quote', 'proforma', 'invoice']
    assert normalize({})['used_for'] is None and normalize({'used_for': ['quote']})['used_for'] == ['quote']
