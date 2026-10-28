"""
Letterhead settings through the business profile form, against real PostgreSQL (same opt-in as test_app_db.py).
"""

import base64
import io

from tests.integration.test_documents_db import PROFILE, _create, _customer, app, client, gst_org  # noqa: F401
from tests.integration.test_app_db import pytestmark  # noqa: F401


def _png(width, height):
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGBA', (width, height), (40, 40, 40, 255)).save(buf, 'PNG')
    return buf.getvalue()


def test_letterhead_settings_are_saved_and_printed(client, gst_org):
    from document_service import get_org_profile
    org_id = gst_org
    response = client.post('/settings/profile', content_type='multipart/form-data', data={
        **PROFILE, 'letterhead_style': 'left', 'letterhead_color': '#2B3138', 'letterhead_accent': 'orange',
        'logo_has_name': 'on', 'logo': (io.BytesIO(_png(8, 2)), 'lockup.png'), 'logo_small': (io.BytesIO(_png(2, 2)), 'mark.png')})
    assert response.status_code == 302
    profile = get_org_profile(org_id)[1]
    assert profile['letterhead_style'] == 'left' and profile['letterhead_color'] == '#2b3138'
    assert 'letterhead_accent' not in profile                       # "orange" isn't a colour the form sends
    assert profile['logo_has_name'] is True
    assert base64.b64decode(profile['logo_small'].split(',', 1)[1]) == _png(2, 2)

    page = client.get('/settings/profile').get_data(as_text=True)
    assert 'value="left" checked' in page and 'value="#2b3138"' in page and 'name="logo_has_name" class="form-checkbox" checked' in page

    customer = _customer(org_id, 'Bolt Works Pvt Ltd', 'Tamil Nadu', 'India')
    quote_id, _ = _create(client, org_id, 'quote', 'Quotation', customer, [{'description': 'Ring gauge', 'price': 1500, 'qty': 2}],
                          tax_mode='none', detail_subject='Ring gauges')
    pdf = client.get(f'/invoices/{quote_id}/pdf', follow_redirects=True)
    assert pdf.headers['Content-Type'] == 'application/pdf' and pdf.data.startswith(b'%PDF')

    # Back to today's letterhead for the tests after this one
    client.post('/settings/profile', content_type='multipart/form-data',
                data={**PROFILE, 'remove_logo': 'on', 'remove_logo_small': 'on'})
    profile = get_org_profile(org_id)[1]
    assert profile['letterhead_style'] == 'centred' and 'logo' not in profile and 'logo_small' not in profile
