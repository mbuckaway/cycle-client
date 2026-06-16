# cyql

Read-only Python client and CLI for the [Cyql](https://cyql.app) cycling-club API, built for the
**GORBA** club. It talks to Cyql's official GraphQL API (`https://api.cyql.app/api/graphql`) using an
`X-Api-Key`, and surfaces club data — rides, stats, news, events, club info — from the command line.
A Discord bot (read-only + push notifications) is planned on top of the same core.

> **Scope:** v1 is **read-only**. The official API key cannot write; creating/updating/cancelling rides
> is deferred (see the project plan).

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Setup

```bash
uv sync                     # create .venv and install runtime + dev dependencies
cp .env.example .env        # then put your Cyql API key in .env (CYCQ_API_KEY=...)
```

The API key is read from the `CYCQ_API_KEY` environment variable (or `.env`, which is git-ignored).

## Usage

```bash
uv run cyql --help
uv run cyql nextride        # next upcoming ride (highlights a cancelled ride in red)
uv run cyql rides           # upcoming rides
uv run cyql stats           # club statistics
```

## Development

```bash
uv run ruff check .                 # lint (ruff, target py314)
uv run mypy                         # type check
uv run pytest                       # unit tests + 90% branch-coverage gate
uv run pytest tests/functional -m functional --no-cov   # functional tests (local mock server)
```

Tests follow TDD; unit tests mock only the HTTP boundary, functional tests run against a local
GraphQL mock server (no client-side mocks).
