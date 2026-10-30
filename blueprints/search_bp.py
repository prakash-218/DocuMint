"""The Ctrl+K search: what it can find, for the browser to search as people type (static/js/palette.js)."""

from flask import Blueprint, g, jsonify

from auth import require_org
import permissions
import search

search_bp = Blueprint('search_bp', __name__)


@search_bp.route('/items')
@require_org
def items():
    response = jsonify(items=search.palette_items(g.current_org_id, permissions.granted()))
    response.headers['Cache-Control'] = 'no-store'      # a document made a moment ago is found
    return response
