# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Functional tests: the real client/CLI against a running local GraphQL server.

No client-side mocks — every call is real HTTP to the mock service (see conftest).
Run separately: ``uv run pytest tests/functional -m functional --no-cov``.
"""

import pytest
from typer.testing import CliRunner

from cyql.auth import ApiKeyAuth, build_auth
from cyql.cli.main import app
from cyql.client import CyqlClient
from cyql.config import Settings
from cyql.errors import CyqlAPIError
from cyql.resources.club import fetch_club_stats
from cyql.resources.members import fetch_members
from cyql.resources.rides import fetch_next_ride, fetch_ride_by_id, fetch_rides

pytestmark = pytest.mark.functional
runner = CliRunner()


def _client() -> CyqlClient:
    # Endpoint + key come from the env vars set by the mock_server fixture.
    return CyqlClient(build_auth(Settings(_env_file=None)))


def test_fetch_club_stats_over_http(mock_server: str) -> None:
    with _client() as client:
        stats = fetch_club_stats(client)

    assert stats.member_count == 167
    assert stats.total_rides == 78


def test_fetch_rides_paginates_over_http(mock_server: str) -> None:
    with _client() as client:
        rides = list(fetch_rides(client, page_size=2))

    assert [ride.title for ride in rides] == [
        "Tuesday Night Ride",
        "Gravel Grind",
        "Sunday Spin",
    ]


def test_fetch_next_ride_over_http(mock_server: str) -> None:
    with _client() as client:
        ride = fetch_next_ride(client)

    assert ride is not None
    assert ride.title == "Tuesday Night Ride"
    assert ride.distance == 16.0


def test_fetch_ride_by_id_over_http(mock_server: str) -> None:
    with _client() as client:
        ride = fetch_ride_by_id(client, "22222222-2222-2222-2222-222222222222")

    assert ride is not None
    assert ride.title == "Gravel Grind"


def test_fetch_members_over_http(mock_server: str) -> None:
    with _client() as client:
        members = list(fetch_members(client))

    assert {member.first_name for member in members} == {"Ada", "Grace"}


def test_cli_stats_over_http(mock_server: str) -> None:
    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0
    assert "167" in result.output


def test_invalid_api_key_is_rejected_over_http(mock_server: str) -> None:
    bad_client = CyqlClient(ApiKeyAuth(api_key="wrong-key", endpoint=mock_server))

    with bad_client, pytest.raises(CyqlAPIError, match="ApiKeyInvalid"):
        fetch_club_stats(bad_client)
