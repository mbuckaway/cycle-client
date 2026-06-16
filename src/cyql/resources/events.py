# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Event read accessors (official ``events``)."""

from __future__ import annotations

from collections.abc import Iterator

from cyql.client import CyqlClient
from cyql.models import Event
from cyql.resources._pagination import DEFAULT_PAGE_SIZE, fetch_paginated

__all__ = ["fetch_events"]

_EVENT_FIELDS = "id title description startDateTime endTime location"

EVENTS_QUERY = f"""
query Events($page: Int, $pageSize: Int, $search: String) {{
  events(page: $page, pageSize: $pageSize, search: $search) {{
    items {{ {_EVENT_FIELDS} }}
    totalCount
    page
    pageSize
    hasNextPage
  }}
}}
"""


def fetch_events(
    client: CyqlClient,
    *,
    search: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Iterator[Event]:
    """Yield club events, optionally filtered by a search term."""
    return fetch_paginated(
        client, EVENTS_QUERY, "events", Event, {"search": search}, page_size=page_size
    )
