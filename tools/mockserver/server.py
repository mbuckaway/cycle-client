# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""A real (local) GraphQL service mirroring the official Cyql read API.

Schema-first via ariadne, served on stdlib ``wsgiref``. It returns fixture data,
implements page/pageSize pagination like ``PagedResultOf*Dto``, and rejects
requests whose ``X-Api-Key`` header does not match the expected key — so
functional tests exercise the full client stack over real HTTP, no mocks.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from typing import Any

from ariadne import QueryType, ScalarType, make_executable_schema
from ariadne.wsgi import GraphQL

SDL = """
scalar UUID
scalar DateTime

type ClubStatsDto { totalRides: Int! memberCount: Int! totalKilometers: Float! totalAdmins: Int! }
type ClubInfoDto {
  title: String city: String description: String address: String
  postalCode: String contact: String email: String createdAt: DateTime
}
type RideDto {
  id: UUID title: String description: String startTime: DateTime rideType: String
  location: String distance: Float altitude: Float averageSpeed: Float duration: Int
  isPublic: Boolean maxGroupSize: Int participantsCount: Int shareUrl: String gpxUrl: String
}
type PagedResultOfRideDto {
  items: [RideDto!]! totalCount: Int! page: Int! pageSize: Int! hasNextPage: Boolean!
}
type MemberDto {
  id: UUID! firstName: String lastName: String email: String status: String
  memberSinceUtc: DateTime isAdmin: Boolean! isRoadCaptain: Boolean!
}
type PagedResultOfMemberDto {
  items: [MemberDto!]! totalCount: Int! page: Int! pageSize: Int! hasNextPage: Boolean!
}
type EventDto {
  id: UUID title: String description: String
  startDateTime: DateTime endTime: DateTime location: String
}
type PagedResultOfEventDto {
  items: [EventDto!]! totalCount: Int! page: Int! pageSize: Int! hasNextPage: Boolean!
}
type NewsDto { id: UUID title: String description: String publicationDate: DateTime }
type PagedResultOfNewsDto {
  items: [NewsDto!]! totalCount: Int! page: Int! pageSize: Int! hasNextPage: Boolean!
}

type Query {
  clubStats: ClubStatsDto!
  clubInfo: ClubInfoDto!
  rides(page: Int, pageSize: Int, isUpcoming: Boolean, search: String): PagedResultOfRideDto!
  rideById(rideId: UUID!): RideDto
  members(page: Int, pageSize: Int, search: String): PagedResultOfMemberDto!
  events(page: Int, pageSize: Int, search: String): PagedResultOfEventDto!
  news(page: Int, pageSize: Int, search: String): PagedResultOfNewsDto!
}
"""

CLUB_STATS = {"totalRides": 78, "memberCount": 167, "totalKilometers": 991.0, "totalAdmins": 5}
CLUB_INFO = {
    "title": "GORBA",
    "city": "Guelph",
    "description": "Guelph Off-Road Bicycling Association",
    "address": "42 Carden St",
    "postalCode": "N1H 3A2",
    "contact": "Mark Buckaway",
    "email": "info@gorba.ca",
    "createdAt": "2010-01-01T00:00:00Z",
}
RIDES = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": "Tuesday Night Ride",
        "description": "Weekly social ride",
        "startTime": "2026-06-16T23:00:00Z",
        "rideType": "ATB",
        "location": "Riverside Park",
        "distance": 16.0,
        "altitude": 50.0,
        "averageSpeed": 22.0,
        "duration": 120,
        "isPublic": True,
        "maxGroupSize": 20,
        "participantsCount": 6,
        "shareUrl": "https://cyqlapp.app.link/ride1",
        "gpxUrl": None,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "title": "Gravel Grind",
        "description": "Long gravel route",
        "startTime": "2026-06-20T13:00:00Z",
        "rideType": "GRAVEL",
        "location": "Arkell Springs",
        "distance": 60.0,
        "altitude": 400.0,
        "averageSpeed": 25.0,
        "duration": 180,
        "isPublic": True,
        "maxGroupSize": 15,
        "participantsCount": 3,
        "shareUrl": "https://cyqlapp.app.link/ride2",
        "gpxUrl": None,
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "title": "Sunday Spin",
        "description": "Easy recovery spin",
        "startTime": "2026-06-21T14:00:00Z",
        "rideType": "ROAD",
        "location": "Hydrocut",
        "distance": 30.0,
        "altitude": 150.0,
        "averageSpeed": 28.0,
        "duration": 90,
        "isPublic": True,
        "maxGroupSize": 10,
        "participantsCount": 1,
        "shareUrl": "https://cyqlapp.app.link/ride3",
        "gpxUrl": None,
    },
]
MEMBERS = [
    {
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "firstName": "Ada",
        "lastName": "Byron",
        "email": "ada@example.org",
        "status": "APPROVED",
        "memberSinceUtc": "2024-03-01T00:00:00Z",
        "isAdmin": True,
        "isRoadCaptain": False,
    },
    {
        "id": "aaaaaaaa-0000-0000-0000-000000000002",
        "firstName": "Grace",
        "lastName": "Hopper",
        "email": "grace@example.org",
        "status": "APPROVED",
        "memberSinceUtc": "2025-05-01T00:00:00Z",
        "isAdmin": False,
        "isRoadCaptain": True,
    },
]
EVENTS = [
    {
        "id": "eeeeeeee-0000-0000-0000-000000000001",
        "title": "GORBA EPIC Festival",
        "description": "Annual festival",
        "startDateTime": "2026-09-14T08:00:00Z",
        "endTime": "2026-09-14T17:00:00Z",
        "location": "Guelph Lake",
    },
]
NEWS = [
    {
        "id": "ffffffff-0000-0000-0000-000000000001",
        "title": "Trails are open",
        "description": "Spring trails now open",
        "publicationDate": "2026-04-01T00:00:00Z",
    },
]

query = QueryType()
uuid_scalar = ScalarType("UUID", serializer=str, value_parser=str)
datetime_scalar = ScalarType("DateTime", serializer=str, value_parser=str)


def _paginate(rows: list[dict[str, Any]], kwargs: dict[str, Any]) -> dict[str, Any]:
    page = kwargs.get("page") or 1
    page_size = kwargs.get("pageSize") or 50
    search = kwargs.get("search")
    if search:
        needle = search.lower()
        rows = [row for row in rows if needle in (row.get("title") or "").lower()]
    start = (page - 1) * page_size
    chunk = rows[start : start + page_size]
    return {
        "items": chunk,
        "totalCount": len(rows),
        "page": page,
        "pageSize": page_size,
        "hasNextPage": start + page_size < len(rows),
    }


@query.field("clubStats")
def resolve_club_stats(*_: Any) -> dict[str, Any]:
    return CLUB_STATS


@query.field("clubInfo")
def resolve_club_info(*_: Any) -> dict[str, Any]:
    return CLUB_INFO


@query.field("rides")
def resolve_rides(_: Any, __: Any, **kwargs: Any) -> dict[str, Any]:
    return _paginate(RIDES, kwargs)


@query.field("rideById")
def resolve_ride_by_id(_: Any, __: Any, rideId: str) -> dict[str, Any] | None:
    return next((ride for ride in RIDES if ride["id"] == rideId), None)


@query.field("members")
def resolve_members(_: Any, __: Any, **kwargs: Any) -> dict[str, Any]:
    return _paginate(MEMBERS, kwargs)


@query.field("events")
def resolve_events(_: Any, __: Any, **kwargs: Any) -> dict[str, Any]:
    return _paginate(EVENTS, kwargs)


@query.field("news")
def resolve_news(_: Any, __: Any, **kwargs: Any) -> dict[str, Any]:
    return _paginate(NEWS, kwargs)


schema = make_executable_schema(SDL, query, uuid_scalar, datetime_scalar)

WsgiApp = Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]


def make_app(expected_key: str | None = None) -> WsgiApp:
    """Build the WSGI app, rejecting requests without the expected ``X-Api-Key``."""
    key = expected_key if expected_key is not None else os.environ.get(
        "MOCK_EXPECTED_API_KEY", "functional-test-key"
    )
    graphql_app = GraphQL(schema)

    def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        if environ.get("REQUEST_METHOD") == "POST" and environ.get("HTTP_X_API_KEY") != key:
            body = json.dumps({"data": None, "errors": [{"message": "ApiKeyInvalid"}]}).encode()
            start_response(
                "200 OK",
                [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
            )
            return [body]
        return graphql_app(environ, start_response)

    return app


def serve(host: str = "127.0.0.1", port: int = 8888) -> None:  # pragma: no cover - manual use
    """Run the mock server (for manual exploration)."""
    from wsgiref.simple_server import make_server

    with make_server(host, port, make_app()) as server:  # type: ignore[arg-type]
        server.serve_forever()


if __name__ == "__main__":  # pragma: no cover - manual use
    serve()
