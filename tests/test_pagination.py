from flask import Flask

from pagination import Page, page_url, paginate


def test_pages_and_numbers():
    p = paginate(list(range(130)), page=3)
    assert (p.items[0], len(p.items), p.first, p.last, p.pages) == (50, 25, 51, 75, 6)
    assert p.has_prev and p.has_next and p.numbers() == [1, 2, 3, 4, 5, 6]
    assert Page(total=500, page=10).numbers() == [1, None, 8, 9, 10, 11, 12, None, 20]
    last = paginate(list(range(30)), page=99)                   # past the end: the last page
    assert (last.page, last.items, last.has_next) == (2, list(range(25, 30)), False)
    empty = paginate([], page=4)
    assert (empty.page, empty.pages, empty.first, empty.last, empty.items) == (1, 1, 0, 0, [])
    db_page = Page.from_count(61, page=3, per_page=25)
    assert (db_page.offset, db_page.first, db_page.last) == (50, 51, 61)


def test_page_links_keep_the_other_arguments():
    app = Flask(__name__)
    with app.test_request_context('/quotes/?status=sent&q=wipro&page=4'):
        assert page_url(5) == '/quotes/?status=sent&q=wipro&page=5'
        assert page_url(1) == '/quotes/?status=sent&q=wipro'
    with app.test_request_context('/emails/?page=2'):
        assert page_url(1) == '/emails/'
    with app.test_request_context('/emails/?page=abc'):
        assert paginate(list(range(40))).page == 1
