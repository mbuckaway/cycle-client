# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for the read-only resource accessors (respx-mocked official API)."""

import json
from typing import Any

import httpx
import respx

from cyql.auth import ApiKeyAuth
from cyql.client import CyqlClient
from cyql.resources.club import fetch_club_info, fetch_club_stats
from cyql.resources.events import fetch_events
from cyql.resources.members import fetch_members
from cyql.resources.news import fetch_news
from cyql.resources.rides import fetch_next_ride, fetch_ride_by_id, fetch_rides

URL = "https://api.cyql.app/api/graphql"


def _client() -> CyqlClient:
    return CyqlClient(ApiKeyAuth(api_key="k", endpoint=URL), sleep=lambda _seconds: None)


def _page(items: list[dict[str, Any]], *, has_next: bool) -> dict[str, Any]:
    return {
        "items": items,
        "totalCount": 99,
        "page": 1,
        "pageSize": 50,
        "hasNextPage": has_next,
    }


@respx.mock
def test_fetch_club_stats_parses_payload() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "clubStats": {
                        "totalRides": 3,
                        "memberCount": 42,
                        "totalKilometers": 100.5,
                        "totalAdmins": 2,
                    }
                }
            },
        )
    )

    with _client() as client:
        stats = fetch_club_stats(client)

    assert stats.member_count == 42
    assert stats.total_kilometers == 100.5


@respx.mock
def test_fetch_club_info_parses_payload() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200, json={"data": {"clubInfo": {"title": "GORBA", "city": "Guelph"}}}
        )
    )

    with _client() as client:
        info = fetch_club_info(client)

    assert info.title == "GORBA"
    assert info.city == "Guelph"


@respx.mock
def test_fetch_rides_paginates_across_pages() -> None:
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(200, json={"data": {"rides": _page([{"id": "r1"}], has_next=True)}}),
            httpx.Response(200, json={"data": {"rides": _page([{"id": "r2"}], has_next=False)}}),
        ]
    )

    with _client() as client:
        rides = list(fetch_rides(client))

    assert [ride.id for ride in rides] == ["r1", "r2"]
    assert route.call_count == 2
    assert json.loads(route.calls.last.request.content)["variables"]["page"] == 2


@respx.mock
def test_fetch_rides_caps_page_size_at_100() -> None:
    route = respx.post(URL).mock(
        return_value=httpx.Response(200, json={"data": {"rides": _page([], has_next=False)}})
    )

    with _client() as client:
        list(fetch_rides(client, page_size=500))

    assert json.loads(route.calls.last.request.content)["variables"]["pageSize"] == 100


@respx.mock
def test_fetch_next_ride_returns_first_item() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200, json={"data": {"rides": {"items": [{"id": "r1", "title": "Next"}]}}}
        )
    )

    with _client() as client:
        ride = fetch_next_ride(client)

    assert ride is not None
    assert ride.id == "r1"


@respx.mock
def test_fetch_next_ride_returns_none_when_empty() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"data": {"rides": {"items": []}}})
    )

    with _client() as client:
        ride = fetch_next_ride(client)

    assert ride is None


@respx.mock
def test_fetch_ride_by_id_returns_ride() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"data": {"rideById": {"id": "r9", "title": "X"}}})
    )

    with _client() as client:
        ride = fetch_ride_by_id(client, "r9")

    assert ride is not None
    assert ride.id == "r9"


@respx.mock
def test_fetch_ride_by_id_returns_none_when_missing() -> None:
    respx.post(URL).mock(return_value=httpx.Response(200, json={"data": {"rideById": None}}))

    with _client() as client:
        ride = fetch_ride_by_id(client, "missing")

    assert ride is None


@respx.mock
def test_fetch_members_yields_members() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "members": _page(
                        [{"id": "m1", "firstName": "Ada", "isAdmin": True}], has_next=False
                    )
                }
            },
        )
    )

    with _client() as client:
        members = list(fetch_members(client))

    assert members[0].id == "m1"
    assert members[0].is_admin is True


@respx.mock
def test_fetch_events_yields_events() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"events": _page([{"id": "e1", "title": "Festival"}], has_next=False)}
            },
        )
    )

    with _client() as client:
        events = list(fetch_events(client))

    assert events[0].title == "Festival"


@respx.mock
def test_fetch_news_yields_news() -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"news": _page([{"id": "n1", "title": "Trail open"}], has_next=False)}},
        )
    )

    with _client() as client:
        news = list(fetch_news(client))

    assert news[0].title == "Trail open"
