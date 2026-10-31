"""
A shared document, for whoever has its private link (sharing.py): a small page with what it is, what's due, the UPI
QR code to pay it, and its PDF. No signing in: the link's long random token is the key, until someone turns it off.
Drawn on the server so it opens quickly in WhatsApp's browser, and kept out of search engines.
"""

import re

from flask import Blueprint, abort, make_response, render_template, request

from db import db

shared_bp = Blueprint('shared_bp', __name__)

TOKEN = re.compile(r'[A-Za-z0-9_-]{32,64}')
# What fetches a link to draw its preview (WhatsApp, Telegram, Slack...): not someone opening it
PREVIEWS = re.compile(r'WhatsApp|facebookexternalhit|TelegramBot|Slackbot|Twitterbot|LinkedInBot|Googlebot|bingbot|Discordbot', re.I)


def _private(response):
    """Kept out of search engines, caches and other sites' logs (the address is the key)."""
    response = make_response(response)
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'private, no-store'
    return response


def _document(token):
    """(link, header, values) for a link that's on, or None."""
    from access import fetch_invoice
    if not TOKEN.fullmatch(token or ''):
        return None
    link = (db.execute_proc('sp_find_share_link', (token,)) or [None])[0]
    if not link:
        return None
    header, values = fetch_invoice(link['invoice_id'])
    if not header or str(header.get('org_id')) != str(link['org_id']):
        return None
    return link, header, values


def _gone():
    return _private(render_template('shared.html', gone=True)), 404


@shared_bp.route('/<token>')
def page(token):
    """The document's page: its number, for whom, its total and what's due, the UPI QR code, and its PDF."""
    from documents import display_number, get_type, load_json
    from invoice_service import build_sections, invoice_summary
    from payment_terms import due_on, usual_days
    import upi
    found = _document(token)
    if not found:
        return _gone()
    link, header, values = found
    if not PREVIEWS.search(request.headers.get('User-Agent', '')):
        db.execute_proc('sp_touch_share_link', (link['link_id'],), fetch=False)
    payments = db.execute_proc('sp_get_invoice_payments', (header['invoice_id'],)) or []
    summary = invoice_summary(header, build_sections(header, values), payments)
    profile = load_json(header.get('organization_profile'))
    kind = get_type(header.get('doc_type'))
    pay = upi.payment(header, summary, profile)
    owed = pay['amount'] if pay else upi.due(header, summary)
    return _private(render_template(
        'shared.html', gone=False, header=header, kind=kind, number=display_number(header), summary=summary, pay=pay,
        owed=owed, due=due_on(header, usual_days(profile)) if kind.takes_payments and owed else None,
        currency=header.get('currency_code') or 'INR', token=token))


@shared_bp.route('/<token>/pdf')
def pdf(token):
    """The document's PDF, as it goes by email: the original copy, sealed. ?download=1 saves it."""
    from invoice_service import PdfUnavailable, render_invoice_pdf
    found = _document(token)
    if not found:
        return _gone()
    _, header, values = found
    try:
        response = render_invoice_pdf(header, values, copies=1)
    except PdfUnavailable:
        abort(503)
    if request.args.get('download'):
        response.headers['Content-Disposition'] = response.headers['Content-Disposition'].replace('inline;', 'attachment;')
    return _private(response)
