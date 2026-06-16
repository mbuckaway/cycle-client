# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Generic page/pageSize pagination over the official Cyql API.

The official API paginates with ``page``/``pageSize``. This module owns the pure
looping logic so resource code only has to describe how to fetch a single page.
It yields lazily (a generator) so large result sets are never materialised at once.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from cyql.errors import PaginationError

__all__ = ["DEFAULT_MAX_PAGES", "Page", "paginate"]

DEFAULT_MAX_PAGES = 1000


@dataclass(frozen=True)
class Page[T]:
    """One page of results plus whether a further page exists."""

    items: list[T]
    has_next: bool


def paginate[T](
    fetch: Callable[[int], Page[T]],
    *,
    start_page: int = 1,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Iterator[T]:
    """Yield every item across pages, calling ``fetch(page)`` one page at a time.

    Raises:
        PaginationError: if more than ``max_pages`` pages are requested (a guard
            against an endpoint that never reports ``has_next == False``).
    """
    page = start_page
    pages_fetched = 0
    while pages_fetched < max_pages:
        result = fetch(page)
        pages_fetched += 1
        yield from result.items
        if not result.has_next:
            return
        page += 1
    raise PaginationError(f"pagination exceeded {max_pages} pages")
