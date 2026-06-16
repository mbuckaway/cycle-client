# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for :mod:`cyql.config`."""

import pytest

from cyql.config import AuthMode, Settings


def test_settings_reads_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CYCQ_API_KEY", "secret-key-123")

    settings = Settings(_env_file=None)

    assert settings.api_key == "secret-key-123"


def test_settings_defaults_auth_mode_to_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CYQL_AUTH_MODE", raising=False)

    settings = Settings(_env_file=None)

    assert settings.auth_mode is AuthMode.API_KEY


def test_settings_defaults_official_and_internal_endpoints() -> None:
    settings = Settings(_env_file=None)

    assert settings.official_endpoint == "https://api.cyql.app/api/graphql"
    assert settings.internal_endpoint == "https://api.cyql.app/graphql"


def test_settings_session_token_defaults_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CYQL_SESSION_TOKEN", raising=False)

    settings = Settings(_env_file=None)

    assert settings.session_token is None


def test_settings_auth_mode_reads_session_token_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CYQL_AUTH_MODE", "session-token")

    settings = Settings(_env_file=None)

    assert settings.auth_mode is AuthMode.SESSION_TOKEN
