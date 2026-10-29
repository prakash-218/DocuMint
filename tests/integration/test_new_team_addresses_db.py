"""
The team's other email addresses against real PostgreSQL (same opt-in as test_app_db.py): kept in the business
profile from Settings, a typo refused, and the addresses counted as ours when finding a customer's people in emails.
"""

from tests.integration.test_app_db import pytestmark  # noqa: F401
from tests.integration.test_documents_db import PROFILE, app, client, gst_org  # noqa: F401
from tests.integration.test_revise_and_correct_db import _flashes


def test_the_teams_other_addresses_are_kept_and_count_as_ours(client, gst_org):
    import contacts
    from document_service import get_org_profile
    try:
        assert client.post('/settings/profile', data={**PROFILE, 'team_addresses': 'Ravi.Home@Gmail.com\ndesk.two@yahoo.example'}).status_code == 302
        assert get_org_profile(gst_org)[1]['team_addresses'] == ['ravi.home@gmail.com', 'desk.two@yahoo.example']
        assert 'ravi.home@gmail.com, desk.two@yahoo.example' in client.get('/settings/profile').get_data(as_text=True)
        assert {'ravi.home@gmail.com', 'desk.two@yahoo.example'} <= set(contacts.own_domains(gst_org))

        _flashes(client)
        client.post('/settings/profile', data={**PROFILE, 'team_addresses': 'ravi.home@gmail.com, ravi at home'})
        assert any('Not an email address: ravi, at, home' in f for f in _flashes(client))
        assert get_org_profile(gst_org)[1]['team_addresses'] == ['ravi.home@gmail.com', 'desk.two@yahoo.example']   # unchanged
    finally:
        client.post('/settings/profile', data=PROFILE)
    assert 'team_addresses' not in get_org_profile(gst_org)[1]
