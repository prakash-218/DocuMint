"""Reading the React app's pages in tests: its page (templates/spa.html) and a document's page (GET /api/document/<id>)."""
import json
import re


def boot_of(page: str):
    """The app's boot data (nav.boot) on an app page, or None when the page isn't the app."""
    found = re.search(r'<script type="application/json" id="boot">(.*?)</script>', page, re.S)
    return json.loads(found.group(1)) if found else None


def badge(boot: dict, key: str) -> int:
    """The number on a sidebar link (notifications), from the boot data."""
    return next(i for s in boot['sidebar'] for i in s['items'] if i['key'] == key)['badge']


def document(client, path: str) -> dict:
    """A document's page as the app gets it (document_page.py), for /quotes/<id> and the like."""
    doc_id = path.split('?')[0].rstrip('/').split('/')[-1]
    response = client.get(f'/api/document/{doc_id}')
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return response.get_json()


def document_text(client, path: str) -> str:
    """Everything a document's page says, as text: the document and its versions (server HTML) and the words of the
    rest, for checks that the page says something."""
    data = document(client, path)
    return '\n'.join([data.get('document_html') or '', data.get('versions_html') or '', json.dumps(data, ensure_ascii=False)])
