# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Exception types raised by the Cyql client."""

from __future__ import annotations

__all__ = [
    "CyqlAPIError",
    "CyqlError",
    "CyqlHTTPError",
    "MissingCredentialError",
    "PaginationError",
]


class CyqlError(Exception):
    """Base class for all errors raised by this package."""


class MissingCredentialError(CyqlError):
    """Raised when a required authentication credential is not configured."""


class CyqlHTTPError(CyqlError):
    """Raised when the Cyql API returns a non-success HTTP status (or fails to respond)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class CyqlAPIError(CyqlError):
    """Raised when a GraphQL response carries an ``errors`` array."""

    def __init__(self, message: str, *, messages: list[str] | None = None) -> None:
        super().__init__(message)
        self.messages = messages if messages is not None else []


class PaginationError(CyqlError):
    """Raised when pagination exceeds its safety bound on the number of pages."""
