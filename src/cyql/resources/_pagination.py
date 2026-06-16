# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Shared helper to page through an official ``PagedResultOf*Dto`` list query.

The official wrapper is ``{ items, totalCount, page, pageSize, hasNextPage }`` and
``pageSize`` may not exceed 100.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel

from cyql.client import CyqlClient
from cyql.paginate import Page, paginate

__all__ = ["DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "fetch_paginated"]

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def fetch_paginated[M: BaseModel](
    client: CyqlClient,
    query: str,
    root_field: str,
    model: type[M],
    variables: dict[str, Any],
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Iterator[M]:
    """Yield every item of ``query`` across pages, parsed into ``model``."""
    effective_size = min(page_size, MAX_PAGE_SIZE)

    def fetch(page: int) -> Page[M]:
        data = client.execute(query, {**variables, "page": page, "pageSize": effective_size})
        result = data[root_field]
        items = [model.model_validate(item) for item in result["items"]]
        return Page(items=items, has_next=bool(result["hasNextPage"]))

    return paginate(fetch)
