# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for :mod:`cyql.auth`."""

import pytest

from cyql.auth import ApiKeyAuth, SessionTokenAuth, build_auth
from cyql.config import AuthMode, Settings
from cyql.errors import MissingCredentialError


def test_build_auth_api_key_uses_official_endpoint_and_header() -> None:
    settings = Settings(api_key="k-123", auth_mode=AuthMode.API_KEY, _env_file=None)

    auth = build_auth(settings)

    assert isinstance(auth, ApiKeyAuth)
    assert auth.endpoint == "https://api.cyql.app/api/graphql"
    assert auth.headers() == {"X-Api-Key": "k-123"}


def test_build_auth_api_key_missing_key_raises_missing_credential() -> None:
    settings = Settings(api_key=None, auth_mode=AuthMode.API_KEY, _env_file=None)

    with pytest.raises(MissingCredentialError, match="CYCQ_API_KEY"):
        build_auth(settings)


def test_build_auth_session_token_uses_internal_endpoint_and_bearer() -> None:
    settings = Settings(
        session_token="t-456", auth_mode=AuthMode.SESSION_TOKEN, _env_file=None
    )

    auth = build_auth(settings)

    assert isinstance(auth, SessionTokenAuth)
    assert auth.endpoint == "https://api.cyql.app/graphql"
    assert auth.headers() == {"Authorization": "Bearer t-456"}


def test_build_auth_session_token_missing_token_raises_missing_credential() -> None:
    settings = Settings(
        session_token=None, auth_mode=AuthMode.SESSION_TOKEN, _env_file=None
    )

    with pytest.raises(MissingCredentialError, match="CYQL_SESSION_TOKEN"):
        build_auth(settings)
