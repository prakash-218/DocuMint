"""Reading the React app's pages in tests: its page (templates/spa.html), a document's page (GET /api/document/<id>),
the editor (GET /api/editor/...) and a document's packing (GET /api/packing/<id>)."""
import json
import re
from urllib.parse import urlsplit


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


def editor(client, path: str) -> dict:
    """A new document's step or the editor, as the app gets it (editor_page.py), for /quotes/create?... and
    /quotes/<id>/edit?correct=1 and the like."""
    url = urlsplit(path)
    parts = url.path.strip('/').split('/')
    api = f'/api/editor/new/{parts[0]}' if parts[-1] == 'create' else f'/api/editor/{parts[1]}'
    response = client.get(api + (f'?{url.query}' if url.query else ''))
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return response.get_json()


def editor_form(data: dict, **changes) -> dict:
    """The form the editor posts, as it stands (frontend/src/islands/editor/Editor.tsx), with changes."""
    form = dict(data['hidden'])
    if data['customer']['fixed'] and data['customer']['fixed']['id']:
        form['customer_id'] = data['customer']['fixed']['id']
    form.update(doc_number=data['number']['value'], issue_date=data['issue_date'], due_date=data['due_date'])
    for s in data['sections']:
        for row in s.get('rows') or []:
            for f in s['fields']:
                value = '' if f['formula'] else row['values'].get(f['id'], '')
                if value is True:
                    value = 'true'
                if value is not False:
                    form[f"line_item_{s['id']}_{row['row']}_field_{f['id']}"] = value
        for f in s['fields'] if s['type'] != 'line_item' else []:
            value = '' if f['formula'] else (s.get('values') or {}).get(f['id'], '')
            if value is not False:
                form[f"field_{f['id']}"] = 'true' if value is True else value
    for f in data['details']['fields']:
        form[f"detail_{f['key']}"] = data['details']['values'].get(f['key'], '')
    settings = data['settings']
    form.update(currency=settings['currency'], tax_mode=settings['tax_mode'], tax_rate=settings['tax_rate'])
    if data['type']['proforma']:
        form.update(advance_percent=settings['advance_percent'], advance_basis=settings['advance_basis'])
    form.update(changes)
    return form


def packing(client, invoice_id: str) -> dict:
    """A document's packing, box by box, as the app gets it (packing_page.py)."""
    response = client.get(f'/api/packing/{invoice_id}')
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    return response.get_json()


def screen(client, path: str) -> dict:
    """Any screen's JSON from the API (/api/customers?q=, /api/settings/profile and the like), checked it loaded."""
    response = client.get(path)
    assert response.status_code == 200, (path, response.get_data(as_text=True)[:300])
    return response.get_json()


def builder_form(data: dict, **changes) -> dict:
    """The form the template builder posts, as it stands (frontend/src/islands/templates/Builder.tsx), with changes."""
    form = {'section_count': str(len(data['sections'])), 'total': data['total']}
    for i, s in enumerate(data['sections'], 1):
        form.update({f's{i}_present': '1', f's{i}_title': s['title'], f's{i}_name': s['name'], f's{i}_type': s['type'],
                     f's{i}_field_count': str(len(s['fields']))})
        for j, f in enumerate(s['fields'], 1):
            q = f's{i}_f{j}_'
            form.update({q + 'present': '1', q + 'label': f['label'], q + 'name': f['name'], q + 'type': f['type']})
            if f['type'] == 'number':                 # the app disables formula and money for other types
                form[q + 'formula'] = f['formula']
                if f['currency']:
                    form[q + 'currency'] = 'on'
            if f['required']:
                form[q + 'required'] = 'on'
    form.update(changes)
    return form
