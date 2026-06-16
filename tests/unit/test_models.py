# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for :mod:`cyql.models` parsing and alias mapping."""

from cyql.models import ClubStats, Member, Ride


def test_club_stats_parses_api_payload() -> None:
    stats = ClubStats.model_validate(
        {"totalRides": 10, "memberCount": 5, "totalKilometers": 123.5, "totalAdmins": 2}
    )

    assert stats.total_rides == 10
    assert stats.member_count == 5
    assert stats.total_kilometers == 123.5
    assert stats.total_admins == 2


def test_ride_maps_camel_aliases_and_parses_datetime() -> None:
    ride = Ride.model_validate(
        {
            "id": "r1",
            "title": "Morning loop",
            "startTime": "2026-06-20T08:00:00Z",
            "rideType": "RACE",
            "averageSpeed": 25.0,
            "participantsCount": 7,
        }
    )

    assert ride.start_time is not None
    assert ride.start_time.year == 2026
    assert ride.average_speed == 25.0
    assert ride.participants_count == 7


def test_member_parses_admin_flags() -> None:
    member = Member.model_validate(
        {"id": "m1", "firstName": "Ada", "lastName": "Byron", "isAdmin": True}
    )

    assert member.first_name == "Ada"
    assert member.is_admin is True
    assert member.is_road_captain is False
