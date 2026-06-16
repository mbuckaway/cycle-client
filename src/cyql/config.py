# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Runtime configuration loaded from the environment / ``.env``.

Endpoints have sensible defaults but remain overridable (e.g. to point the client
at the local mock GraphQL server during functional tests). Secrets are never
hard-coded; they are read from the environment.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["AuthMode", "Settings"]

OFFICIAL_ENDPOINT = "https://api.cyql.app/api/graphql"
INTERNAL_ENDPOINT = "https://api.cyql.app/graphql"


class AuthMode(StrEnum):
    """Which Cyql endpoint and credential the client authenticates with."""

    API_KEY = "api-key"
    SESSION_TOKEN = "session-token"


class Settings(BaseSettings):
    """Configuration for the Cyql client, populated from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        case_sensitive=False,
        extra="ignore",
    )

    api_key: str | None = Field(default=None, validation_alias="CYCQ_API_KEY")
    session_token: str | None = Field(default=None, validation_alias="CYQL_SESSION_TOKEN")
    auth_mode: AuthMode = Field(default=AuthMode.API_KEY, validation_alias="CYQL_AUTH_MODE")
    official_endpoint: str = Field(
        default=OFFICIAL_ENDPOINT, validation_alias="CYQL_OFFICIAL_ENDPOINT"
    )
    internal_endpoint: str = Field(
        default=INTERNAL_ENDPOINT, validation_alias="CYQL_INTERNAL_ENDPOINT"
    )
    timeout_seconds: float = Field(default=10.0, validation_alias="CYQL_TIMEOUT_SECONDS")
