"""Contacts: who in a project's emails could be one (and their phone numbers), and who may change contacts."""

from datetime import datetime, timezone

import pytest

import contacts
from tests.fakedb import ORG_A

OWN = ['ourworks.example']


def _mail(sender, name='', to='desk@ourworks.example', cc='', body='', day=20, direction='in'):
    return {'from_address': sender, 'from_name': name, 'to_addresses': to, 'cc_addresses': cc, 'direction': direction,
            'sent_at': datetime(2026, 10, day, 10, 0, tzinfo=timezone.utc), 'body_text': body}


def test_people_who_wrote_or_were_copied_are_suggested():
    messages = [_mail('ravi.k@gearco.example', 'Ravi Kumar', cc='arun.s@gearco.example, boss@ourworks.example', day=21),
                _mail('ravi.k@gearco.example', 'Ravi Kumar', day=12),
                _mail('noreply@portal.example', 'Portal'),
                _mail('desk@ourworks.example', 'Us', to='buyer@gearco.example', direction='out', day=15)]
    found = contacts.suggestions(messages, [], [], OWN)['people']
    assert [(p['email'], p['name'], p['seen']) for p in found] == [
        ('ravi.k@gearco.example', 'Ravi Kumar', 'Wrote 2 emails, last 21 Oct'),     # writers first
        ('arun.s@gearco.example', 'Arun S', 'Copied on an email, 21 Oct'),           # a name made from the address
        ('buyer@gearco.example', 'Buyer', 'We emailed them, 15 Oct'),
    ]


def test_contacts_ignored_and_own_addresses_are_not_suggested():
    messages = [_mail('ravi.k@gearco.example', 'Ravi Kumar', cc='arun.s@gearco.example, MD@OurWorks.example')]
    known = [{'contact_id': 'K1', 'name': 'Ravi Kumar', 'email': 'ravi.k@gearco.example', 'phone': None}]
    assert contacts.suggestions(messages, known, ['arun.s@gearco.example'], OWN)['people'] == []


SIGNATURE = """Please find our PO attached.

Regards,
Ravi Kumar | Purchase
Mob: +91-98765 43210
Office: 044-2345 6789

On Tue, 14 Oct 2026, Desk <desk@ourworks.example> wrote:
> Our quotation, call us on 99887 76655
"""


def test_a_phone_in_a_contacts_signature_is_offered_for_their_contact():
    known = [{'contact_id': 'K1', 'name': 'Ravi Kumar', 'email': 'ravi.k@gearco.example', 'phone': None}]
    phones = contacts.suggestions([_mail('ravi.k@gearco.example', 'Ravi Kumar', body=SIGNATURE)], known, [], OWN)['phones']
    assert [(p['contact_id'], p['phone'], p['value']) for p in phones] == [('K1', '+91 98765 43210', 'tel:9876543210')]


def test_phones_already_saved_ignored_ours_or_quoted_are_not_offered():
    mail = [_mail('ravi.k@gearco.example', 'Ravi Kumar', body=SIGNATURE)]
    saved = [{'contact_id': 'K1', 'name': 'Ravi Kumar', 'email': 'ravi.k@gearco.example', 'phone': '9876543210'}]
    assert contacts.suggestions(mail, saved, [], OWN)['phones'] == []
    unsaved = [{**saved[0], 'phone': None}]
    assert contacts.suggestions(mail, unsaved, ['tel:9876543210'], OWN)['phones'][0]['phone'] == '044-2345 6789'
    assert contacts.suggestions(mail, unsaved, ['tel:9876543210'], OWN, own_phones='044 2345 6789')['phones'] == []
    # the number in the quoted mail below is never picked up
    assert '99887 76655' not in contacts.new_part(SIGNATURE)


def test_a_new_persons_phone_comes_with_their_suggestion():
    found = contacts.suggestions([_mail('ravi.k@gearco.example', 'Ravi Kumar', body=SIGNATURE)], [], [], OWN)
    assert found['people'][0]['phone'] == '+91 98765 43210' and found['phones'] == []


@pytest.mark.parametrize('raw, tidy', [('+91-98765 43210', '+91 98765 43210'), ('09876543210', '+91 98765 43210'),
                                       ('9876543210', '+91 98765 43210'), ('044-2345 6789', '044-2345 6789')])
def test_phone_numbers_are_tidied(raw, tidy):
    assert contacts.tidy_phone(raw) == tidy


@pytest.mark.parametrize('name, initials', [('Mr. K. Arun Kumar', 'AK'), ('Ms. Divya', 'D'), ('purchase', 'P'), ('', '?')])
def test_initials(name, initials):
    assert contacts.initials(name) == initials


@pytest.fixture
def owner(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    return client


def test_viewers_cannot_change_contacts(owner, fake_db):
    fake_db.members['U-A'][0]['role'] = 'viewer'
    response = owner.post('/customers/C-A/contacts', data={'name': 'Ravi Kumar', 'email': 'ravi.k@gearco.example'})
    assert response.headers['Location'].endswith('/customers/C-A#contacts')
    assert not [c for c in fake_db.calls if c[0] in ('sp_save_contact', 'sp_delete_contact')]


@pytest.mark.parametrize('role', ['owner', 'member', 'sales'])
def test_editors_add_contacts(owner, fake_db, role):
    fake_db.members['U-A'][0]['role'] = role
    owner.post('/customers/C-A/contacts', data={'name': ' Ravi Kumar ', 'email': 'Ravi.K@GearCo.example', 'gets': 'billing'})
    assert ('sp_save_contact', (ORG_A, None, 'C-A', 'Ravi Kumar', 'ravi.k@gearco.example', None, None, 'billing')) in fake_db.calls


@pytest.mark.parametrize('form, problem', [({'name': '', 'email': ''}, 'Give the contact a name'),
                                           ({'name': 'Ravi', 'email': 'ravi at gearco'}, "doesn't look like an email")])
def test_contact_form_problems(owner, fake_db, form, problem):
    page = owner.post('/customers/C-A/contacts', data=form, follow_redirects=True).get_data(as_text=True)
    assert problem in page.replace('&#39;', "'")
    assert not [c for c in fake_db.calls if c[0] == 'sp_save_contact']


def test_sales_cannot_ignore_suggestions(owner, fake_db):
    fake_db.members['U-A'][0]['role'] = 'sales'
    owner.post('/customers/C-A/ignore-suggestion', data={'value': 'arun.s@gearco.example'})
    assert not [c for c in fake_db.calls if c[0] == 'sp_ignore_contact_suggestion']
