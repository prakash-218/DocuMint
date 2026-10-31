"""Invite-only (invites.py): the pieces that need no database."""
import pytest

import invites


def test_a_token_is_kept_only_as_its_hash():
    token = invites.new_token()
    assert len(token) == 43 and token != invites.new_token()
    assert len(invites.token_hash(token)) == 64 and invites.token_hash(token) == invites.token_hash(token) != token


@pytest.mark.parametrize('text,email', [(' Ravi.K@Gmail.com ', 'ravi.k@gmail.com'), ('owner@gearcutters.example', 'owner@gearcutters.example'),
                                        ('not an address', None), ('a@b', None), ('', None), (None, None)])
def test_an_address(text, email):
    assert invites.clean_email(text) == email


def test_a_public_providers_domain_is_nobodys():
    assert invites.own_domain('ravi@gmail.com') is None and invites.own_domain('ravi@yahoo.co.in') is None
    assert invites.own_domain('owner@gearcutters.example') == 'gearcutters.example'


def test_why_an_invite_cant_be_used():
    assert invites.state(None) == 'missing'
    assert invites.state({'used_at': 'x'}) == 'used' and invites.state({'cancelled_at': 'x'}) == 'cancelled'
    assert invites.state({'expired': True}) == 'expired' and invites.state({'expired': False}) == 'ok'


def test_the_emails_say_what_the_link_is_for():
    join = invites.invite_message('Gear Cutters', 'Member', 'https://x/auth/invite/T', 'owner@gearcutters.example')
    assert join['subject'] == 'Join Gear Cutters on DocuMint'
    assert 'owner@gearcutters.example invited you to join Gear Cutters on DocuMint, as member.' in join['body']
    assert 'https://x/auth/invite/T' in join['body'] and '7 days' in join['body']
    assert invites.invite_message(None, 'Owner', 'L', None)['subject'] == 'Start your organization on DocuMint'
    reset = invites.reset_message('https://x/auth/reset/T')
    assert 'https://x/auth/reset/T' in reset['body'] and '2 hours' in reset['body']


def test_nothing_is_emailed_without_a_mailbox(app):
    with app.app_context():
        assert invites.send(None, 'ravi@gmail.com', {'subject': 's', 'body': 'b'}, 'Org') is False
