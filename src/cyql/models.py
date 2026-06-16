# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Typed models mirroring the official Cyql API DTOs (introspected).

Field aliases map the API's camelCase names onto snake_case attributes. Models
ignore unknown fields so the client keeps working if the API adds attributes.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ClubInfo", "ClubStats", "Event", "Member", "News", "Ride"]


class _ApiModel(BaseModel):
    """Base for API models: populate by field name or alias, ignore extras."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ClubStats(_ApiModel):
    """Aggregate club statistics (``clubStats``)."""

    total_rides: int = Field(alias="totalRides")
    member_count: int = Field(alias="memberCount")
    total_kilometers: float = Field(alias="totalKilometers")
    total_admins: int = Field(alias="totalAdmins")


class ClubInfo(_ApiModel):
    """Club profile (``clubInfo``)."""

    title: str | None = None
    city: str | None = None
    description: str | None = None
    address: str | None = None
    postal_code: str | None = Field(default=None, alias="postalCode")
    contact: str | None = None
    email: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")


class Ride(_ApiModel):
    """A planned or past ride (``RideDto``)."""

    id: str | None = None
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = Field(default=None, alias="startTime")
    ride_type: str | None = Field(default=None, alias="rideType")
    location: str | None = None
    distance: float | None = None
    altitude: float | None = None
    average_speed: float | None = Field(default=None, alias="averageSpeed")
    duration: int | None = None
    is_public: bool | None = Field(default=None, alias="isPublic")
    max_group_size: int | None = Field(default=None, alias="maxGroupSize")
    participants_count: int | None = Field(default=None, alias="participantsCount")
    share_url: str | None = Field(default=None, alias="shareUrl")
    gpx_url: str | None = Field(default=None, alias="gpxUrl")


class Member(_ApiModel):
    """A club member (``MemberDto``). Only the CLI surfaces per-member detail."""

    id: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    email: str | None = None
    status: str | None = None
    member_since: datetime | None = Field(default=None, alias="memberSinceUtc")
    is_admin: bool = Field(default=False, alias="isAdmin")
    is_road_captain: bool = Field(default=False, alias="isRoadCaptain")


class Event(_ApiModel):
    """A calendar event (``EventDto``)."""

    id: str | None = None
    title: str | None = None
    description: str | None = None
    start_date_time: datetime | None = Field(default=None, alias="startDateTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    location: str | None = None


class News(_ApiModel):
    """A club news article (``NewsDto``)."""

    id: str | None = None
    title: str | None = None
    description: str | None = None
    publication_date: datetime | None = Field(default=None, alias="publicationDate")
