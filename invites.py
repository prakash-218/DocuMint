"""
Getting into DocuMint is by invitation only. An owner or admin invites one address into their organization with a
role; the operator (scripts/dbtool.py invite-org) invites someone to start a new organization. The invite's link is
emailed from the organization's mailbox when it has one, and shown once so it can be sent another way (WhatsApp):
that's how someone with only a Gmail address gets in, since a public provider's domain (gmail.com) is never an
organization's. The link works once and expires; only its token's hash is kept, as for password resets, which are
emailed when someone forgot their password or made by an owner or admin for a member.
"""

import hashlib
import re
import secrets
from typing import Dict, Optional

INVITE_DAYS = 7
RESET_MINUTES = 120
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[A-Za-z]{2,}')


def new_token() -> str:
    """43 random characters: the link's key."""
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """What's kept of a token: its SHA-256, so the table alone opens nothing."""
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


def clean_email(text) -> Optional[str]:
    """The address in lower case, or None when it isn't one."""
    found = (text or '').strip().lower()
    return found if EMAIL.fullmatch(found) else None


def own_domain(email: str) -> Optional[str]:
    """An address's domain when it can be an organization's: never a public provider's (gmail.com, yahoo.com...)."""
    from contacts import FREE_MAIL
    domain = (email or '').rpartition('@')[2].lower()
    return domain if domain and domain not in FREE_MAIL else None


def state(invite: Optional[Dict]) -> str:
    """'ok', or why the invite can't be used: 'missing', 'used', 'cancelled' or 'expired'."""
    if not invite:
        return 'missing'
    if invite.get('used_at'):
        return 'used'
    if invite.get('cancelled_at'):
        return 'cancelled'
    if invite.get('expired'):
        return 'expired'
    return 'ok'


def invite_message(org_name: Optional[str], role_label: str, link: str, invited_by: Optional[str]) -> Dict[str, str]:
    """{subject, body} of the email an invite goes in."""
    if org_name:
        subject = f'Join {org_name} on DocuMint'
        what = f"{invited_by or 'Someone'} invited you to join {org_name} on DocuMint, as {role_label.lower()}."
    else:
        subject = 'Start your organization on DocuMint'
        what = "You're invited to start your organization on DocuMint: quotations, proformas and GST invoices."
    return {'subject': subject,
            'body': f"Hello,\n\n{what}\n\nOpen this link to set your password and get started:\n{link}\n\n"
                    f"It works once, for {INVITE_DAYS} days. If you weren't expecting it, ignore this email.\n"}


def reset_message(link: str) -> Dict[str, str]:
    return {'subject': 'Set a new DocuMint password',
            'body': f"Hello,\n\nSomeone asked to set a new password for your DocuMint account. Open this link to choose "
                    f"one:\n{link}\n\nIt works once, for {RESET_MINUTES // 60} hours. If it wasn't you, ignore this email: "
                    f"your password stays as it is.\n"}


def send(org_id, to: str, message: Dict[str, str], sender_name: str) -> bool:
    """Email it from the organization's mailbox; False when it has none or it couldn't go (the link is shown anyway)."""
    import logging
    import mailsend
    cfg = mailsend.sender_for(org_id) if org_id else None
    if not cfg:
        return False
    try:
        mailsend.send(cfg, mailsend.build_message(sender_name, cfg['from_address'], [to], [], message['subject'], message['body']), [to])
        return True
    except Exception:                                                    # noqa: BLE001: the link still works
        logging.getLogger(__name__).exception('Could not email an invite or reset to %s', to)
        return False
