# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Authentication strategies for the two Cyql GraphQL endpoints.

``ApiKeyAuth`` targets the official, read-only ``/api/graphql`` endpoint and is the
default. ``SessionTokenAuth`` targets the internal ``/graphql`` endpoint (Bearer JWT);
it is the only path that can perform writes, which are deferred, so it is kept as a
ready-to-use strategy but not yet wired to any mutation methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from cyql.config import AuthMode, Settings
from cyql.errors import MissingCredentialError

__all__ = ["ApiKeyAuth", "Auth", "SessionTokenAuth", "build_auth"]


@runtime_checkable
class Auth(Protocol):
    """An authentication strategy: a target endpoint plus request headers."""

    @property
    def endpoint(self) -> str: ...

    def headers(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class ApiKeyAuth:
    """Authenticate to the official endpoint with an ``X-Api-Key`` header."""

    api_key: str
    endpoint: str

    def headers(self) -> dict[str, str]:
        """Return the headers carrying the API key."""
        return {"X-Api-Key": self.api_key}


@dataclass(frozen=True)
class SessionTokenAuth:
    """Authenticate to the internal endpoint with a Bearer session token."""

    token: str
    endpoint: str

    def headers(self) -> dict[str, str]:
        """Return the headers carrying the bearer token."""
        return {"Authorization": f"Bearer {self.token}"}


def build_auth(settings: Settings) -> Auth:
    """Build the auth strategy selected by ``settings.auth_mode``.

    Raises:
        MissingCredentialError: if the credential required by the mode is absent.
    """
    if settings.auth_mode is AuthMode.SESSION_TOKEN:
        if not settings.session_token:
            raise MissingCredentialError(
                "CYQL_SESSION_TOKEN is required for session-token auth"
            )
        return SessionTokenAuth(
            token=settings.session_token, endpoint=settings.internal_endpoint
        )

    if not settings.api_key:
        raise MissingCredentialError("CYCQ_API_KEY is required for api-key auth")
    return ApiKeyAuth(api_key=settings.api_key, endpoint=settings.official_endpoint)
