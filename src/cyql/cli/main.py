# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Typer application for the ``cyql`` command — read-only Cyql access."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from itertools import islice
from typing import Annotated

import typer
from rich.console import Console

from cyql import __version__
from cyql.auth import build_auth
from cyql.cli import render
from cyql.client import CyqlClient
from cyql.config import Settings
from cyql.errors import CyqlError, MissingCredentialError
from cyql.resources.club import fetch_club_info, fetch_club_stats
from cyql.resources.events import fetch_events
from cyql.resources.members import fetch_members
from cyql.resources.news import fetch_news
from cyql.resources.rides import fetch_next_ride, fetch_rides

app = typer.Typer(
    name="cyql",
    help="Read-only client for the Cyql cycling-club API.",
    no_args_is_help=True,
)

_console = Console()

JsonOption = Annotated[bool, typer.Option("--json", help="Output raw JSON instead of a table.")]
CountOption = Annotated[int, typer.Option("--count", "-n", help="Maximum items to show.")]


def _build_client() -> CyqlClient:
    settings = Settings()
    try:
        auth = build_auth(settings)
    except MissingCredentialError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    return CyqlClient(auth, timeout=settings.timeout_seconds)


@contextmanager
def _client_session() -> Iterator[CyqlClient]:
    """Yield a client, turning Cyql errors into a clean CLI message."""
    client = _build_client()
    try:
        yield client
    except CyqlError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    finally:
        client.close()


@app.callback()
def main() -> None:
    """Read-only client for the Cyql cycling-club API."""


@app.command()
def version() -> None:
    """Print the installed cyql version."""
    typer.echo(__version__)


@app.command()
def nextride(json_output: JsonOption = False) -> None:
    """Show the next upcoming ride."""
    with _client_session() as client:
        ride = fetch_next_ride(client)
    if ride is None:
        typer.echo("No upcoming rides.")
        return
    render.render_ride_detail(_console, ride, json_output)


@app.command()
def rides(count: CountOption = 5, json_output: JsonOption = False) -> None:
    """List upcoming rides."""
    with _client_session() as client:
        items = list(islice(fetch_rides(client, is_upcoming=True), count))
    render.render_rides(_console, items, json_output)


@app.command()
def ride(
    search: Annotated[str, typer.Argument(help="Text to match against rides.")],
    json_output: JsonOption = False,
) -> None:
    """Show details of the first ride matching SEARCH."""
    with _client_session() as client:
        items = list(islice(fetch_rides(client, search=search), 1))
    if not items:
        typer.echo(f"No ride matching {search!r}.")
        return
    render.render_ride_detail(_console, items[0], json_output)


@app.command()
def stats(json_output: JsonOption = False) -> None:
    """Show club statistics."""
    with _client_session() as client:
        render.render_stats(_console, fetch_club_stats(client), json_output)


@app.command()
def members(count: CountOption = 25, json_output: JsonOption = False) -> None:
    """List club members (admin/local use)."""
    with _client_session() as client:
        items = list(islice(fetch_members(client), count))
    render.render_members(_console, items, json_output)


@app.command()
def events(count: CountOption = 10, json_output: JsonOption = False) -> None:
    """List club events."""
    with _client_session() as client:
        items = list(islice(fetch_events(client), count))
    render.render_events(_console, items, json_output)


@app.command()
def news(count: CountOption = 5, json_output: JsonOption = False) -> None:
    """List club news."""
    with _client_session() as client:
        items = list(islice(fetch_news(client), count))
    render.render_news(_console, items, json_output)


@app.command()
def club(json_output: JsonOption = False) -> None:
    """Show club information."""
    with _client_session() as client:
        render.render_club_info(_console, fetch_club_info(client), json_output)


if __name__ == "__main__":  # pragma: no cover
    app()
