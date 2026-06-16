# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Club-level read accessors (official ``clubStats`` / ``clubInfo``)."""

from __future__ import annotations

from cyql.client import CyqlClient
from cyql.models import ClubInfo, ClubStats

__all__ = ["fetch_club_info", "fetch_club_stats"]

CLUB_STATS_QUERY = """
query ClubStats {
  clubStats { totalRides memberCount totalKilometers totalAdmins }
}
"""

CLUB_INFO_QUERY = """
query ClubInfo {
  clubInfo { title city description address postalCode contact email createdAt }
}
"""


def fetch_club_stats(client: CyqlClient) -> ClubStats:
    """Return aggregate club statistics."""
    data = client.execute(CLUB_STATS_QUERY)
    return ClubStats.model_validate(data["clubStats"])


def fetch_club_info(client: CyqlClient) -> ClubInfo:
    """Return the club profile."""
    data = client.execute(CLUB_INFO_QUERY)
    return ClubInfo.model_validate(data["clubInfo"])
