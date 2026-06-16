# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for :mod:`cyql.paginate`."""

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cyql.errors import PaginationError
from cyql.paginate import Page, paginate


def _slicer(items: list[int], page_size: int) -> Callable[[int], Page[int]]:
    """Build a fetch callback that serves ``items`` in ``page_size`` chunks."""

    def fetch(page: int) -> Page[int]:
        start = (page - 1) * page_size
        chunk = items[start : start + page_size]
        return Page(items=chunk, has_next=start + page_size < len(items))

    return fetch


@given(
    items=st.lists(st.integers(), max_size=50),
    page_size=st.integers(min_value=1, max_value=7),
)
def test_paginate_roundtrips_all_items_in_order(items: list[int], page_size: int) -> None:
    assert list(paginate(_slicer(items, page_size))) == items


@pytest.mark.parametrize(
    "items",
    [[], [42], [1, 2, 3, 4, 5]],
    ids=["empty", "single", "many"],
)
def test_paginate_yields_each_collection_size(items: list[int]) -> None:
    assert list(paginate(_slicer(items, page_size=2))) == items


def test_paginate_stops_on_first_page_when_no_next() -> None:
    calls: list[int] = []

    def fetch(page: int) -> Page[int]:
        calls.append(page)
        return Page(items=[1, 2], has_next=False)

    assert list(paginate(fetch)) == [1, 2]
    assert calls == [1]


def test_paginate_raises_when_exceeding_max_pages() -> None:
    def fetch(page: int) -> Page[int]:
        return Page(items=[page], has_next=True)

    with pytest.raises(PaginationError, match="exceeded 3 pages"):
        list(paginate(fetch, max_pages=3))
