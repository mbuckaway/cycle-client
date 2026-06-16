# cyql

A read-only Python client and command-line tool for the [Cyql](https://cyql.app) cycling-club
platform, built for the **GORBA** club (Guelph Off-Road Bicycling Association). It talks to Cyql's
official GraphQL API and surfaces club data — rides, statistics, members, news, events, and club
info — from your terminal.

The code is layered so a future **Discord bot** can reuse the same core (see
[`docs/DISCORD_CHATBOX.md`](docs/DISCORD_CHATBOX.md)).

## Status

- **v1 — read-only.** The official Cyql API key is read-only (it exposes no mutations), so creating,
  updating, or cancelling rides is **deferred**; it would require Cyql's unsupported internal API.
- **Discord bot — designed, not built.** Push/notification polling is deferred. See the design doc.

## Features

- Typed GraphQL client over `httpx` with retry/backoff and clear error handling
- `page`/`pageSize` pagination, typed [pydantic](https://docs.pydantic.dev) models
- A [Typer](https://typer.tiangolo.com) CLI with rich tables and a `--json` mode
- Ride/event/news times shown in a configurable timezone (defaults to your system local zone)

## Requirements

- Python **3.14+**
- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- A Cyql **API key** (Cyql dashboard → Settings → API)

## Setup

```bash
uv sync                 # create .venv and install runtime + dev dependencies
cp .env.example .env     # then add your Cyql API key (CYCQ_API_KEY=...)
```

`.env` is git-ignored. The API key is read from the `CYCQ_API_KEY` environment variable (or `.env`).

## Configuration

All settings are environment variables (or lines in `.env`):

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `CYCQ_API_KEY` | yes | — | Official API key, sent as the `X-Api-Key` header |
| `CYQL_TIMEZONE` | no | system local | IANA zone for displaying times, e.g. `America/Toronto` |
| `CYQL_TIMEOUT_SECONDS` | no | `10` | HTTP timeout |
| `CYQL_OFFICIAL_ENDPOINT` | no | `https://api.cyql.app/api/graphql` | Read API endpoint |
| `CYQL_AUTH_MODE` | no | `api-key` | `api-key` or `session-token` (the latter is for the deferred internal API) |

## Usage

```bash
uv run cyql --help
uv run cyql nextride                 # the next upcoming ride
uv run cyql rides -n 5               # upcoming rides (default 5)
uv run cyql ride "tuesday"           # first ride matching a search term
uv run cyql stats                    # club statistics
uv run cyql members -n 25            # members (admin/local use)
uv run cyql news                     # latest club news
uv run cyql events                   # upcoming events
uv run cyql club                     # club information
```

Every data command also accepts `--json` for machine-readable output:

```console
$ uv run cyql stats --json
{
  "total_rides": 78,
  "member_count": 167,
  "total_kilometers": 991.0,
  "total_admins": 5
}
```

To display ride times in your club's timezone:

```bash
CYQL_TIMEZONE=America/Toronto uv run cyql nextride
```

## Development

```bash
uv run ruff check .                                        # lint (ruff, target py314)
uv run mypy                                                # type-check (strict)
uv run pytest                                              # unit tests + 90% branch-coverage gate
uv run pytest tests/functional -m functional --no-cov     # functional tests (local GraphQL server)
```

Tests follow TDD. Unit tests mock only the HTTP boundary (via `respx`) and use Hypothesis for pure
helpers; functional tests run against a real local GraphQL server (`tools/mockserver`, ariadne over
`wsgiref`) with no client-side mocks.

## Project layout

```
src/cyql/
  config.py            # settings (pydantic-settings)
  auth.py              # X-Api-Key / Bearer auth strategies
  client.py            # httpx GraphQL client (retry, error mapping)
  paginate.py          # page/pageSize pagination
  models.py            # typed API models
  resources/           # rides, club, members, events, news accessors
  cli/                 # Typer app + rich/JSON rendering
tools/mockserver/      # local GraphQL server for functional tests
docs/DISCORD_CHATBOX.md # Discord bot design + hosting notes
```

## License

Copyright (c) 2026 Mark Buckaway. All rights reserved. This project is proprietary
(`SPDX-License-Identifier: LicenseRef-Proprietary`); no license to use, copy, or distribute is
granted without the author's express written permission.
