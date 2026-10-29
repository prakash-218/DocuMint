"""Reading the React app's page (templates/spa.html) in tests."""
import json
import re


def boot_of(page: str):
    """The app's boot data (nav.boot) on an app page, or None when the page isn't the app."""
    found = re.search(r'<script type="application/json" id="boot">(.*?)</script>', page, re.S)
    return json.loads(found.group(1)) if found else None


def badge(boot: dict, key: str) -> int:
    """The number on a sidebar link (notifications), from the boot data."""
    return next(i for s in boot['sidebar'] for i in s['items'] if i['key'] == key)['badge']
