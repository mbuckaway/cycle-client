# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""News read accessors (official ``news``)."""

from __future__ import annotations

from collections.abc import Iterator

from cyql.client import CyqlClient
from cyql.models import News
from cyql.resources._pagination import DEFAULT_PAGE_SIZE, fetch_paginated

__all__ = ["fetch_news"]

_NEWS_FIELDS = "id title description publicationDate"

NEWS_QUERY = f"""
query News($page: Int, $pageSize: Int, $search: String) {{
  news(page: $page, pageSize: $pageSize, search: $search) {{
    items {{ {_NEWS_FIELDS} }}
    totalCount
    page
    pageSize
    hasNextPage
  }}
}}
"""


def fetch_news(
    client: CyqlClient,
    *,
    search: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Iterator[News]:
    """Yield club news articles, optionally filtered by a search term."""
    return fetch_paginated(
        client, NEWS_QUERY, "news", News, {"search": search}, page_size=page_size
    )
