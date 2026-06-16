# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Rendering helpers for the CLI: rich tables or raw JSON.

Each ``render_*`` function emits either a rich table (human view) or the model's
JSON (``--json``); the branch lives once in :func:`_emit`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any

from rich.console import Console, RenderableType
from rich.table import Table

from cyql.models import ClubInfo, ClubStats, Event, Member, News, Ride

__all__ = [
    "render_club_info",
    "render_events",
    "render_members",
    "render_news",
    "render_ride_detail",
    "render_rides",
    "render_stats",
]


def _emit(
    console: Console,
    json_output: bool,
    payload: Any,
    build_table: Callable[[], RenderableType],
) -> None:
    if json_output:
        console.print_json(data=payload)
    else:
        console.print(build_table())


def _text(value: object) -> str:
    return "-" if value is None else str(value)


def _dt(value: datetime | None) -> str:
    return "-" if value is None else value.strftime("%Y-%m-%d %H:%M")


def _km(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f} km"


def _dump(items: Sequence[object]) -> list[Any]:
    return [item.model_dump(mode="json") for item in items]  # type: ignore[attr-defined]


def _ride_detail_table(ride: Ride) -> Table:
    table = Table(title=ride.title or "Ride", show_header=False)
    table.add_row("When", _dt(ride.start_time))
    table.add_row("Location", _text(ride.location))
    table.add_row("Distance", _km(ride.distance))
    table.add_row("Type", _text(ride.ride_type))
    table.add_row("Participants", _text(ride.participants_count))
    table.add_row("Link", _text(ride.share_url))
    return table


def render_ride_detail(console: Console, ride: Ride, json_output: bool) -> None:
    """Render a single ride's details."""
    _emit(console, json_output, ride.model_dump(mode="json"), lambda: _ride_detail_table(ride))


def _rides_table(rides: Sequence[Ride]) -> Table:
    table = Table(title="Upcoming rides")
    for column in ("Title", "When", "Distance", "Type", "Riders"):
        table.add_column(column)
    for ride in rides:
        table.add_row(
            _text(ride.title),
            _dt(ride.start_time),
            _km(ride.distance),
            _text(ride.ride_type),
            _text(ride.participants_count),
        )
    return table


def render_rides(console: Console, rides: Sequence[Ride], json_output: bool) -> None:
    """Render a list of rides as a table."""
    _emit(console, json_output, _dump(rides), lambda: _rides_table(rides))


def _stats_table(stats: ClubStats) -> Table:
    table = Table(title="Club statistics", show_header=False)
    table.add_row("Members", str(stats.member_count))
    table.add_row("Admins", str(stats.total_admins))
    table.add_row("Rides", str(stats.total_rides))
    table.add_row("Kilometres", f"{stats.total_kilometers:.1f}")
    return table


def render_stats(console: Console, stats: ClubStats, json_output: bool) -> None:
    """Render club statistics."""
    _emit(console, json_output, stats.model_dump(mode="json"), lambda: _stats_table(stats))


def _club_table(info: ClubInfo) -> Table:
    table = Table(title=info.title or "Club", show_header=False)
    table.add_row("City", _text(info.city))
    table.add_row("Contact", _text(info.contact))
    table.add_row("Email", _text(info.email))
    return table


def render_club_info(console: Console, info: ClubInfo, json_output: bool) -> None:
    """Render club profile information."""
    _emit(console, json_output, info.model_dump(mode="json"), lambda: _club_table(info))


def _members_table(members: Sequence[Member]) -> Table:
    table = Table(title="Members")
    for column in ("Name", "Email", "Status", "Admin"):
        table.add_column(column)
    for member in members:
        name = " ".join(part for part in (member.first_name, member.last_name) if part) or "-"
        admin = "yes" if member.is_admin else "no"
        table.add_row(name, _text(member.email), _text(member.status), admin)
    return table


def render_members(console: Console, members: Sequence[Member], json_output: bool) -> None:
    """Render a list of members (admin/local use)."""
    _emit(console, json_output, _dump(members), lambda: _members_table(members))


def _events_table(events: Sequence[Event]) -> Table:
    table = Table(title="Events")
    for column in ("Title", "When", "Location"):
        table.add_column(column)
    for event in events:
        table.add_row(_text(event.title), _dt(event.start_date_time), _text(event.location))
    return table


def render_events(console: Console, events: Sequence[Event], json_output: bool) -> None:
    """Render a list of events as a table."""
    _emit(console, json_output, _dump(events), lambda: _events_table(events))


def _news_table(news: Sequence[News]) -> Table:
    table = Table(title="News")
    for column in ("Title", "Date"):
        table.add_column(column)
    for article in news:
        table.add_row(_text(article.title), _dt(article.publication_date))
    return table


def render_news(console: Console, news: Sequence[News], json_output: bool) -> None:
    """Render a list of news articles as a table."""
    _emit(console, json_output, _dump(news), lambda: _news_table(news))
