# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""End-to-end CLI tests: real stack with the HTTP boundary mocked by respx."""

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
import respx
from typer.testing import CliRunner

from cyql.cli.main import app

URL = "https://api.cyql.app/api/graphql"
runner = CliRunner()


@pytest.fixture
def cli_env(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # chdir away from the real .env, supply a dummy key via the environment.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CYCQ_API_KEY", "test-key")
    yield


def _data(payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(200, json={"data": payload})


def _paged(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": items,
        "totalCount": len(items),
        "page": 1,
        "pageSize": 50,
        "hasNextPage": False,
    }


_STATS = {"totalRides": 3, "memberCount": 42, "totalKilometers": 100.5, "totalAdmins": 2}


@respx.mock
def test_stats_command_renders_member_count(cli_env: None) -> None:
    respx.post(URL).mock(return_value=_data({"clubStats": _STATS}))

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0
    assert "42" in result.output


@respx.mock
def test_stats_command_json_emits_snake_case_keys(cli_env: None) -> None:
    respx.post(URL).mock(return_value=_data({"clubStats": _STATS}))

    result = runner.invoke(app, ["stats", "--json"])

    assert result.exit_code == 0
    assert "member_count" in result.output


@respx.mock
def test_nextride_renders_title(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=_data({"rides": {"items": [{"id": "r1", "title": "Dawn Patrol"}]}})
    )

    result = runner.invoke(app, ["nextride"])

    assert result.exit_code == 0
    assert "Dawn Patrol" in result.output


@respx.mock
def test_nextride_reports_when_no_upcoming(cli_env: None) -> None:
    respx.post(URL).mock(return_value=_data({"rides": {"items": []}}))

    result = runner.invoke(app, ["nextride"])

    assert result.exit_code == 0
    assert "No upcoming rides" in result.output


@respx.mock
def test_rides_lists_titles(cli_env: None) -> None:
    respx.post(URL).mock(return_value=_data({"rides": _paged([{"id": "r1", "title": "Loop A"}])}))

    result = runner.invoke(app, ["rides", "-n", "3"])

    assert result.exit_code == 0
    assert "Loop A" in result.output


@respx.mock
def test_ride_search_renders_match(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=_data({"rides": _paged([{"id": "r1", "title": "Gravel Grind"}])})
    )

    result = runner.invoke(app, ["ride", "gravel"])

    assert result.exit_code == 0
    assert "Gravel Grind" in result.output


@respx.mock
def test_ride_search_reports_no_match(cli_env: None) -> None:
    respx.post(URL).mock(return_value=_data({"rides": _paged([])}))

    result = runner.invoke(app, ["ride", "nope"])

    assert result.exit_code == 0
    assert "No ride matching" in result.output


@respx.mock
def test_members_lists_names(cli_env: None) -> None:
    member = {"id": "m1", "firstName": "Ada", "lastName": "L", "isAdmin": True}
    respx.post(URL).mock(return_value=_data({"members": _paged([member])}))

    result = runner.invoke(app, ["members"])

    assert result.exit_code == 0
    assert "Ada" in result.output


@respx.mock
def test_events_lists_titles(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=_data({"events": _paged([{"id": "e1", "title": "EPIC Festival"}])})
    )

    result = runner.invoke(app, ["events"])

    assert result.exit_code == 0
    assert "EPIC Festival" in result.output


@respx.mock
def test_news_lists_titles(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=_data({"news": _paged([{"id": "n1", "title": "Trail Day"}])})
    )

    result = runner.invoke(app, ["news"])

    assert result.exit_code == 0
    assert "Trail Day" in result.output


@respx.mock
def test_club_renders_name(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=_data({"clubInfo": {"title": "GORBA", "city": "Guelph", "email": "e@g.ca"}})
    )

    result = runner.invoke(app, ["club"])

    assert result.exit_code == 0
    assert "GORBA" in result.output


@respx.mock
def test_nextride_localizes_time_to_configured_timezone(
    cli_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CYQL_TIMEZONE", "America/Toronto")
    ride = {"id": "r1", "title": "Dawn", "startTime": "2026-06-16T23:00:00Z"}
    respx.post(URL).mock(return_value=_data({"rides": {"items": [ride]}}))

    result = runner.invoke(app, ["nextride"])

    assert result.exit_code == 0
    assert "19:00" in result.output  # 23:00 UTC -> 19:00 EDT


@respx.mock
def test_unknown_timezone_falls_back_to_local(
    cli_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CYQL_TIMEZONE", "Not/AZone")
    ride = {"id": "r1", "title": "Dawn", "startTime": "2026-06-16T23:00:00Z"}
    respx.post(URL).mock(return_value=_data({"rides": {"items": [ride]}}))

    result = runner.invoke(app, ["nextride"])

    assert result.exit_code == 0
    assert "Dawn" in result.output


@respx.mock
def test_api_error_exits_nonzero(cli_env: None) -> None:
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"errors": [{"message": "ApiKeyInvalid"}]})
    )

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 1


def test_missing_credentials_exits_nonzero(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CYCQ_API_KEY", raising=False)

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 1
