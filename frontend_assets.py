"""
The React app on a page: the script (and styles) Vite built from frontend/ into static/app, found through the manifest
it writes. spa.html, public.html and portal.html put it in; frontend/src/main.tsx starts the part whose root the page
has (#app, #public or #portal). Without a build (unit tests, a checkout that never ran npm) pages simply have none.
"""

import json
import os
from functools import lru_cache

from flask import current_app, url_for
from markupsafe import Markup

ENTRY = 'src/main.tsx'


@lru_cache(maxsize=4)
def _manifest(path: str, mtime: float) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def frontend_assets() -> Markup:
    path = os.path.join(current_app.static_folder, 'app', '.vite', 'manifest.json')
    try:
        entry = _manifest(path, os.path.getmtime(path)).get(ENTRY)
    except (OSError, ValueError):
        return Markup('')
    if not entry:
        return Markup('')
    tags = [Markup('<link rel="stylesheet" href="{}">').format(url_for('static', filename='app/' + css))
            for css in entry.get('css', [])]
    tags.append(Markup('<script type="module" src="{}"></script>').format(url_for('static', filename='app/' + entry['file'])))
    return Markup('\n    ').join(tags)
