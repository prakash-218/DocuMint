"""
Pages of a list: ?page=N on any list page, 25 rows a page.

Lists that are filtered and counted in Python (documents, projects, customers) are cut
after filtering with paginate(); lists that only grow (emails, notifications, the audit
log) ask the database for one page with Page.from_count() and offset.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from urllib.parse import urlencode

PER_PAGE = 25


def requested_page() -> int:
    from flask import request
    try:
        return max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        return 1


@dataclass
class Page:
    total: int
    page: int = 1
    per_page: int = PER_PAGE
    items: List[Any] = field(default_factory=list)

    def __post_init__(self):
        self.page = min(max(1, self.page), self.pages)      # past the end: the last page

    @classmethod
    def from_count(cls, total: int, page: Optional[int] = None, per_page: int = PER_PAGE) -> 'Page':
        """A page whose items the caller fetches with LIMIT per_page OFFSET offset."""
        return cls(total=int(total or 0), page=page or requested_page(), per_page=per_page)

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.per_page))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def first(self) -> int:
        return self.offset + 1 if self.total else 0

    @property
    def last(self) -> int:
        return min(self.offset + self.per_page, self.total)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    def json(self, noun: str = '') -> dict:
        """For the React app's pager (frontend/src/app/ui.tsx): it links ?page=n on the address it's on."""
        return {'page': self.page, 'pages': self.pages, 'first': self.first, 'last': self.last, 'total': self.total,
                'numbers': self.numbers(), 'noun': noun}

    def numbers(self, around: int = 2) -> List[Optional[int]]:
        """Page numbers to link, None for a gap: 1 … 4 5 [6] 7 8 … 20."""
        keep = {1, self.pages} | set(range(self.page - around, self.page + around + 1))
        out, prev = [], 0
        for n in sorted(k for k in keep if 1 <= k <= self.pages):
            if n - prev > 1:
                out.append(None)
            out.append(n)
            prev = n
        return out


def paginate(items: List[Any], page: Optional[int] = None, per_page: int = PER_PAGE) -> Page:
    p = Page(total=len(items), page=page or requested_page(), per_page=per_page)
    p.items = items[p.offset:p.offset + p.per_page]
    return p


def page_url(n: int) -> str:
    """This page's URL with ?page=n (other query arguments kept)."""
    from flask import request
    args = [(k, v) for k, v in request.args.items(multi=True) if k != 'page']
    if n > 1:
        args.append(('page', n))
    return request.path + (('?' + urlencode(args)) if args else '')
