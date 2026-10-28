"""The quotation letterhead (centred, or the logo on the left), its colours, and logos printed at their own proportions."""

import base64
import io

import pytest


def _png(width, height):
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGBA', (width, height), (40, 40, 40, 255)).save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


WIDE = _png(4, 1)            # a lockup: symbol and name side by side
SQUARE = _png(3, 3)          # the symbol alone


def _render(app, fake_db, template, doc_type, profile):
    from flask import render_template
    from invoice_service import build_sections, invoice_summary, pdf_fonts
    header = {**fake_db.invoices['INV-A'], 'doc_type': doc_type, 'doc_number': 'TF/Q/031/26-27', 'currency_code': 'INR',
              'organization_name': 'Bolt Works', 'organization_street_address': '12, Lathe Lane, Guindy',
              'organization_city': 'Chennai', 'organization_zip_code': '600032', 'organization_country': 'India',
              'details': '{"subject": "Ring gauges"}'}
    with app.test_request_context():
        sections = build_sections(header, fake_db._values_for('INV-A'))
        return render_template(template, invoice=header, sections_data=sections, payments=[], fonts=pdf_fonts(),
                               profile=profile, copy='', header_height=90, summary=invoice_summary(header, sections, []))


def test_logos_print_at_their_own_proportions(app):
    from app_helpers import image_ratio
    width = app.jinja_env.filters['image_width']
    assert image_ratio(WIDE) == 4 and width(WIDE, 46) == 184 and width(SQUARE, 28) == 28
    assert width('data:image/png;base64,bm90IGFuIGltYWdl', 28) == 28          # unreadable: printed square, not an error


def test_centred_letterhead_is_unchanged_by_default(app, fake_db):
    html = _render(app, fake_db, 'pdf/quote.html', 'quote', {'gstin': '33ABCDE1234F1Z5'})
    assert 'class="name">BOLT WORKS<' in html and '12, LATHE LANE, GUINDY' in html
    assert 'background-color: #1f2fd1' in html and 'split-name' not in html.split('</style>')[1]


def test_logo_on_the_left_with_the_name_in_it(app, fake_db):
    profile = {'gstin': '33ABCDE1234F1Z5', 'letterhead_style': 'left', 'letterhead_color': '#2b3138',
               'letterhead_accent': '#e2620f', 'logo': WIDE, 'logo_has_name': True}
    html = _render(app, fake_db, 'pdf/quote.html', 'quote', profile).split('</style>')[1]
    assert f'src="{WIDE}" style="height: 46pt; width: 184.0pt;"' in html
    assert 'BOLT WORKS' not in html and 'class="name"' not in html               # the logo says the name
    assert '12, Lathe Lane, Guindy' in html and 'Chennai 600032, India' in html and '<b>GSTIN</b>&nbsp; 33ABCDE1234F1Z5' in html
    assert 'background-color: #e2620f' in html and 'background-color: #2b3138' in html and '#1f2fd1' not in html


def test_left_letterhead_without_a_logo_types_the_name(app, fake_db):
    html = _render(app, fake_db, 'pdf/quote.html', 'quote', {'letterhead_style': 'left'}).split('</style>')[1]
    assert 'class="split-name">BOLT WORKS<' in html and '<img' not in html


@pytest.mark.parametrize('profile, printed', [
    ({'logo': SQUARE}, SQUARE),                                          # the logo, as before
    ({'logo': WIDE, 'logo_small': SQUARE, 'logo_has_name': True}, SQUARE),
    ({'logo': WIDE, 'logo_has_name': True}, None),                       # it would repeat the name printed below it
])
def test_invoices_print_the_small_logo(app, fake_db, profile, printed):
    html = _render(app, fake_db, 'pdf/grid.html', 'invoice', profile).split('</style>')[1]
    if printed:
        assert f'src="{printed}" style="height: 28pt; width: 28.0pt;"' in html
    else:
        assert '<img' not in html.split('Consignee')[0]


def test_left_letterhead_prints(app, fake_db):
    """The PDF itself: the letterhead is measured and repeated like the centred one."""
    from pypdf import PdfReader
    import invoice_service
    from invoice_service import build_sections, invoice_summary, pdf_fonts
    header = {**fake_db.invoices['INV-A'], 'doc_type': 'quote', 'doc_number': 'TF/Q/031/26-27', 'currency_code': 'INR',
              'organization_name': 'Bolt Works', 'organization_city': 'Chennai', 'details': '{"subject": "Ring gauges"}'}
    profile = {'gstin': '33ABCDE1234F1Z5', 'letterhead_style': 'left', 'logo': WIDE, 'logo_has_name': True}
    with app.test_request_context():
        sections = build_sections(header, fake_db._values_for('INV-A'))
        pdf = invoice_service._document_pdf('pdf/quote.html', invoice=header, sections_data=sections, payments=[],
                                            fonts=pdf_fonts(), profile=profile, page={},
                                            summary=invoice_summary(header, sections, []))
    text = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
    assert 'GSTIN' in text and '33ABCDE1234F1Z5' in text and 'TF/Q/031/26-27' in text
