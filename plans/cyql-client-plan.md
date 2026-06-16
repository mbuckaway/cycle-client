# Plan: Cyql API client (Python CLI → reusable core → Discord bot)

## Context

Mark uses Cyql (cyql.app) to run the **GORBA** cycling club. The goal is to understand
Cyql's API and build read-only automation: first a **Python command-line app**, later a
**Discord bot**, to pull club data (members, rides, stats, etc.). This plan starts from a
live, read-only reconnaissance of the logged-in dashboard plus the public docs/marketing,
then designs the tool. **No writes** to Cyql at any point.

This document records the API review (the first deliverable Mark asked for) and the build plan.

---

## Part 1 — API review (all findings directly observed, no guesses)

### Two GraphQL endpoints exist on `api.cyql.app`

| | Official / public API | Internal dashboard API |
|---|---|---|
| URL | `POST https://api.cyql.app/api/graphql` | `POST https://api.cyql.app/graphql` |
| Auth | `X-Api-Key: <key>` header | `Authorization: Bearer <JWT>` header |
| Introspection | Enabled (query builder at `api.cyql.app/docs`) | **Disabled** (`HC0046`) |
| Backend | GraphQL (HotChocolate / .NET) | Same server |
| Cookies sent? | n/a | **No** — `credentials:'omit'` works; `'include'` fails CORS |
| Stability | Documented, supported | Undocumented, may change / ToS-gray |
| Rate limit | Weekly **complexity budget** (per plan) | Unknown/undocumented |

**Evidence:** Network capture on `dashboard.cyql.app` shows 8 POSTs to `/graphql`. A live
probe proved auth = **Bearer token, no cookies** — `credentials:'omit'` + `Authorization: Bearer`
returned `{"data":{"__typename":"Query"}}`; `credentials:'include'` failed CORS. The JWT lives
in the readable (non-HttpOnly) `token` cookie (also `refreshToken`, `refreshTokenExpires`,
`clubId`, `context`). The official endpoint/auth (`/api/graphql`, `X-Api-Key`) is from Cyql's
own blog: [cyql-api-cycling-club-new-feature](https://cyql.app/blog/cyql-api-cycling-club-new-feature).

### Capability matrix — reads vs writes vs push (introspection-confirmed with the live key)

| Capability | Official `/api/graphql` (`X-Api-Key`) | Internal `/graphql` (`Bearer` JWT) |
|---|---|---|
| Reads | ✅ Supported | ✅ (what the dashboard uses) |
| Writes (create/update/cancel/delete rides, members, news…) | ❌ **None** — `mutationType: null` | ✅ **101 mutations** incl. `saveRideItem`, `cancelRideItem`, `reactivateRideItem`, `deleteRideItem` |
| Realtime / push | ❌ `subscriptionType: null` | ❌ none |
| Constraints | depth ≤5, complexity ≤200/query, **weekly budget 5,000** | undocumented; unsupported / ToS-gray; JWT expires |

**Consequences (drive the whole design):**
1. The API key can **read** but **cannot write**. Create/update/cancel rides is only possible via the
   **internal Bearer** mutations (`saveRideItem` = create when `$id` is null / update when set;
   `cancelRideItem`, `reactivateRideItem`, `deleteRideItem`).
2. There are **no webhooks or subscriptions** anywhere → "push to Discord" must be **poll-based**.

**Official read surface (exact fields + args, introspected with your key):**
- `rides(page, pageSize, isUpcoming, search)` · `rideById(rideId)` · `rideParticipants(rideId, page, pageSize, search)`
- `members(page, pageSize, search, memberStatus)` · `memberById(memberId)`
- `clubStats` · `clubInfo` (no args)
- `events(page, pageSize, fetchType, search)` · `eventById(eventId)`
- `news(page, pageSize, search)` · `newsById(newsId)`
- `challenges(page, pageSize, search)` · `challengeScores(challengeId, …)` · `challengeById(challengeId)`
- `gpxRoutes(page, pageSize, search)` · `gpxRouteById(gpxRouteId)`
- Pagination is **page/pageSize** here (vs the internal API's skip/take). **`rides.isUpcoming`** directly
  powers `/nextride`.

### Confirmed read operations (captured live from the dashboard, internal API)

All list queries follow one pattern: args `clubId: UUID!`, `skip: Int`, `take: Int`,
`search: String`, `order: [...SortInput]`, plus resource filters → return
`{ totalCount, pageInfo { hasNextPage hasPreviousPage }, items { ... } }` (offset pagination).

| Operation | Root field | Returns (key fields observed) |
|---|---|---|
| `getUserItems` | `fetchClubMembers` | `DashboardMember`: id, firstName, lastName, gender, email, phone, dateOfBirth, city, picture, stravaId, labels, status, memberSinceUtc, subscriptionStart/End/Number, isAdmin, isRoadCaptain, permissions, customFields, emergency contact |
| `getRideItems` | `fetchRides` | `BaseRide`: id, title, description, startTimeUtc, rideType, address, gpx, distanceKm, averageSpeedKm, altitude, participantsCount, commentsCount, photosCount, organizer, roadCaptains, isPublic/Active/Canceled, shareUrl |
| `getClubItemStats` | `fetchClubStats` | approvedUsersCount, pendingUsersCount, adminCount, expiredUsersCount, ridesCount, ridesTotalCount, cycledKm, gpx/challenge counts |
| `getClubItems` / `getClubItem` | `fetchClubs` / `fetchClub` (+`fetchClubRoles`) | `Club`: id, title, description, address, branding, settings, usersCount, plan, userIsAdmin |
| `getNewsItems` | `fetchNews` | News: id, title, description, created/updated, image, presentedBy |
| `getEventItems` | `fetchEvents` | Event: id, title, startTimeUtc, endTimeUtc, address, image |
| `getGpxItems` | `fetchGpxFiles` | GpxFile: id, title, distanceKm, altitude, lat/lon, rideTypes, labels, file url |
| `getAddressItems` | `fetchAddresses` | Address: id, name, street, city, lat, lon (the "Locations" list) |
| `getGroupItems` | `fetchGroups` | Group: id, title, groupTypes, labels |

The **official** API (per the blog) exposes the same resource families — Rides, Members,
Statistics, Club info, News, Events, GPX routes, **Challenges** — with pagination. Its exact
field/query names differ from the internal ones and will be confirmed by **introspecting
`/api/graphql` once an API key exists** (introspection is enabled there). We will **not**
guess the public field names.

### Plan / API-availability — RESOLVED

Mark has **generated a working API key** (stored locally in `.env`). The official path on
`/api/graphql` (`X-Api-Key`) is therefore **confirmed available** and is the **default** auth
method for the tool.

For the record, the two sources that initially disagreed:
- **Marketing** ([cyql.app/pricing](https://cyql.app/pricing)): plans = Free, Starter, Pro,
  Elite; "API Integration" listed only under Elite; no "Club Pro" on the page.
- **GORBA's dashboard** (authoritative): plan = **`Club Pro`**, with an active API page allowing
  1 key (depth 5, complexity 200/query, weekly budget 5,000) — which the generated key confirms.

The earlier dashboard reading was correct; the public pricing matrix simply doesn't list the
`Club Pro` plan.

---

## Part 2 — Decisions (confirmed with Mark)

- **Auth, split by capability:**
  - **Reads → official `X-Api-Key`** on `/api/graphql` (default; supported; key in **`.env`**, git-ignored,
    loaded via config — never hardcoded/committed). Subject to depth ≤5 / weekly budget 5,000.
  - **Writes → DEFERRED (Mark's decision).** Not built in v1. When revisited, the only path is the internal
    `Bearer` mutations on `/graphql` (`saveRideItem`/`cancelRideItem`/`reactivateRideItem`/`deleteRideItem`) —
    unsupported / ToS-gray, session-token auth. The design keeps a `SessionTokenAuth` strategy stub so writes
    can be added later without rework.
- **Eventual bot:** **Discord** (Phase 3). Phase 1–2 build a platform-agnostic core so Discord drops on top.
- **Copyright header (all source files):**
  ```python
  # Copyright (c) 2026 Mark Buckaway.
  # SPDX-License-Identifier: LicenseRef-Proprietary
  # All rights reserved.
  ```
- **Read-only scope for v1.** Reads via the official key (CLI + Discord). Ride writes are **deferred** per
  Mark — no mutations in v1. The Discord bot is **strictly read-only + push** regardless.

---

## Part 3 — Architecture

Greenfield project at `/Users/markbuckaway/src/cyqlapi`. Layered so the CLI and a future Discord
bot share one core.

```
cyqlapi/
  pyproject.toml              # deps + ruff(py314) + pytest(--cov-branch --cov-fail-under=90); console_script: cyql
  README.md
  .gitignore                  # .venv/, *.pyc, .pytest_cache, secrets
  src/cyql/
    __init__.py
    config.py                 # pydantic-settings; endpoints + auth mode; secrets via env/keyring, NEVER hardcoded
    auth.py                   # Auth strategy: ApiKeyAuth (X-Api-Key, /api/graphql) | SessionTokenAuth (Bearer, /graphql)
    client.py                 # CyqlClient: httpx POST, error mapping, retry/backoff, complexity-aware
    paginate.py               # pure skip/take iterator over {totalCount,pageInfo} (Hypothesis target)
    queries.py                # GraphQL query strings (confirmed internal ops now; official ops added post-introspection)
    models.py                 # typed models: Member, Ride, ClubStats, Club, News, Event, GpxFile, Address
    resources/                # one short module per resource: members, rides, stats, clubs, news, events, gpx, locations
    cli/main.py               # Typer app -> `cyql members list`, `cyql rides list`, `cyql stats`, ... (--json | rich table)
  tests/
    unit/                     # mock ONLY the httpx boundary (respx); Hypothesis for pure fns
    functional/              # run against a LOCAL GraphQL server (real process, no client mocks)
    conftest.py
  tools/mockserver/           # local GraphQL service (ariadne or strawberry + uvicorn) mirroring confirmed schema + fixtures
```

**Auth design (covers the unresolved plan question):**
- `ApiKeyAuth` → header `X-Api-Key`, endpoint `/api/graphql`. Used when `CYQL_API_KEY` is set.
- `SessionTokenAuth` → header `Authorization: Bearer <token>`, endpoint `/graphql`. Token supplied
  by Mark (pasted from the `token` cookie, or via `CYQL_SESSION_TOKEN`). **Confirmed working live.**
  Auto-refresh via `refreshToken` is a stretch goal (login/refresh endpoint not yet captured); v1
  treats an expired token as a clear error telling the user to refresh it.
- Client picks the strategy from config; identical query layer behind both. If the official key
  works, switching is a one-line config change.

**Tech (all standard, well-documented — no invented APIs):** `httpx` (HTTP), raw GraphQL query
strings (no heavy client dep; full control of the complexity budget), `Typer` (CLI), `rich`
(tables), `pydantic`/`pydantic-settings` (models + config), `pytest`+`pytest-cov`+`respx`+
`hypothesis` (tests), `ariadne`/`strawberry`+`uvicorn` (local functional-test server).

**Standards compliance (from ~/.claude global standards):** TDD red-green-refactor; Python 3.14
syntax; PEP 8; copyright header on every `.py`; **90% branch coverage hard gate**
(`--cov-branch --cov-fail-under=90`); short single-purpose functions; config system, no hardcoded
endpoints; **functional tests run as a separate process against the local GraphQL service, never
mocked**; unit tests mock only the httpx I/O boundary; Hypothesis property tests for pure helpers
(pagination, query building); no Makefile (pyproject console-script + `python -m` tasks); `.venv`.

---

## Part 4 — Build order (each step: tests first, then code)

0. **Repo + secret hygiene (do first):** `git init`; write `.gitignore` excluding **`.env`**, `.venv/`,
   `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`.
   Verify `git check-ignore .env` reports it ignored before any `git add`. Commit only when Mark asks.
1. **Scaffold:** pyproject (deps, ruff py314, pytest cov gate), `.venv`, headers, README, `.env.example`
   documenting `CYQL_API_KEY` (and optional `CYQL_SESSION_TOKEN`).
2. **config.py + auth.py:** typed settings; two auth strategies; tests for header/endpoint selection per mode (incl. missing-secret 401-style negative paths).
3. **client.py + paginate.py:** httpx POST, GraphQL-error mapping, retry/backoff; pure pagination iterator (Hypothesis: full-page round-trip, empty, single, many). Unit tests via `respx`.
4. **Read client (official key):** introspect `/api/graphql` server-side to lock exact field selections,
   then `models.py` + one resource module per official query (`rides`, `rideById`, `members`, `clubStats`,
   `clubInfo`, `events`, `news`, `challenges`, `gpxRoutes`) using **page/pageSize** pagination.
5. **CLI reads:** Typer commands — `cyql nextride`, `cyql rides`, `cyql ride <id|search>`, `cyql stats`,
   `cyql members` (full detail, admin/local use), `cyql news`, `cyql events`, `cyql club` — `--json` + `rich`.
   (Cancelled-ride banner deferred: official `RideDto` exposes no cancellation field.)
6. **Local functional service:** `tools/mockserver` GraphQL server mirroring the introspected schema with
   fixtures; functional suite runs as a separate process against it (no client mocks).
7. **CLI writes — DEFERRED (Mark's decision).** Not in this build. The design keeps a `SessionTokenAuth`
   stub and documents the internal ride mutations (`saveRideItem`/`cancelRideItem`/`reactivateRideItem`/
   `deleteRideItem`) as a ready-to-add later phase — no rework needed when revisited.
8. **(Phase 3) Discord bot — read-only + push** on the shared core; see **Part 5**: the distinct slash
   commands and the scheduled **poller → Discord incoming-webhook** push. Authored as `docs/DISCORD_CHATBOX.md`
   (created on approval; embedded above while planning).

---

## Part 5 — Discord bot design (`DISCORD_CHATBOX.md`)

> Researched against discord.py docs, Discord's developer docs (interactions), and AWS serverless
> Discord references (sources cited in chat). The bot is **read-only**, sits on the shared `cyql`
> core, and authenticates to Cyql with **its own server-side API key** — Discord users never need
> Cyql accounts.

### Discord offers two connection models — this is the crux of the hosting question

| | A. Gateway (WebSocket) | B. HTTP Interactions Endpoint |
|---|---|---|
| How | Bot holds a persistent WebSocket to Discord | Discord POSTs each command to your HTTPS URL |
| Library | **discord.py 2.x** (`commands.Bot`, `app_commands.CommandTree`, `tree.sync()`, `Interaction`, `interaction.response.send_message`/`.defer()`, `followup.send()`, `ephemeral=True`) | **No discord.py** — verify Ed25519 yourself (PyNaCl) + a thin web handler (FastAPI / lib like `interactions.py`) |
| Hosting | **Always-on process required** (cannot run on Lambda) | **Fits serverless** (API Gateway → Lambda), or any web host |
| Security | Bot token only | Must verify `X-Signature-Ed25519` + `X-Signature-Timestamp` against the app **public key**; answer PING(type `1`)→PONG(type `1`) |

### Is AWS Lambda required? — No. Two viable models (your explicit question)

- **Model A — always-on gateway (discord.py).** Simplest to build; richest library support. But it needs
  a process that never sleeps: small EC2/VM, **ECS Fargate**, Fly.io/Railway, or even a Raspberry Pi.
  **Lambda cannot host it** (Lambda is request/response; no persistent gateway socket). Always-on = a
  small but constant cost, plus process supervision.
- **Model B — serverless on Lambda (HTTP interactions).** Discord sends an HTTPS POST per slash command
  to **API Gateway → Lambda**. Pay-per-use (literally pennies/month for a club), scales to zero — this
  matches your global standards (serverless, PAY_PER_REQUEST, cost-optimized, Pulumi/AWS).
  - **3-second deadline pattern:** the interaction Lambda verifies the signature and **immediately
    returns response type `5` `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`** (user sees "thinking…"), then a
    **worker Lambda** (async invoke) calls Cyql and edits the reply via
    `PATCH /webhooks/{application_id}/{interaction_token}/messages/@original` (token valid 15 min).
    This makes Cyql latency / Lambda cold-starts a non-issue for the 3s rule.
  - Cost of this model: it is **not** discord.py — more plumbing (Ed25519 verify, register commands via
    Discord REST, build followups), Pulumi infra (API Gateway, 2 Lambdas, Secrets Manager/SSM).
- **Updated direction (Mark, Phase 3):** the bot should need **no external hosting** if possible, and the
  **push feature is dropped/deferred**. A custom bot still needs *some* compute, so the realistic
  no-hosting-bill options are: **(1) run `discord.py` locally** (gateway; no cloud/endpoint/tunnel; reuses
  the Python core; online only while the machine runs) — **recommended**; or **(2) Cloudflare Workers free
  tier** (Discord's official host-free serverless; always-on; but JS/TS, HTTP-interactions only). See the
  authoritative **`docs/DISCORD_CHATBOX.md`** in the repo. Final hosting choice pending Mark.

### Setup & registration (both models)

1. Create an application in the Discord Developer Portal → add a **Bot** → copy the **bot token** and the
   app **public key** + **application id** (secrets).
2. Invite to the GORBA server with OAuth2 scopes **`bot` + `applications.commands`**, minimal send-message permission.
3. Register slash commands to the **GORBA guild** (guild commands appear instantly; global commands take
   up to ~1 h to propagate) — single-club bot → guild registration.
4. Secrets in **`.env`** for local dev (git-ignored); in **AWS SSM Parameter Store / Secrets Manager** for
   Model B (per your Pulumi standards). Stored: Discord bot token, app public key, app id, Cyql API key.

> **GORBA server access (verified on gorba.ca):** GORBA = *Guelph Off-Road Bicycling Association*.
> Its Discord is **members-only**; the invite link is **deliberately not public** — sent via the
> membership receipt email / newsletter, with moderator verification of new joiners. The public
> invite is **not needed to add the bot**: a server admin with **Manage Server** on the GORBA guild
> adds the bot via its OAuth2 authorize URL and supplies the **guild ID** for command registration.
> Mark to confirm he holds that admin/moderator access on the GORBA guild before Phase 3.

### Slash commands — distinct top-level commands (read-only; official API key)

Per Mark: **distinct** commands (not one grouped `/cyql …`), e.g. `/nextride`.

| Command | Official query | Output |
|---|---|---|
| `/nextride` | `rides(isUpcoming: true, pageSize: 1)` | the next ride: title, date/time, start location, distance, type, organizer. **If cancelled → red banner (see below)** |
| `/rides [count]` | `rides(isUpcoming: true, pageSize: count)` | upcoming rides list (default 5) |
| `/ride <search>` | `rides(search: …)` → `rideById` | one ride's details + participant count |
| `/stats` | `clubStats` | members, admins, rides, total km |
| `/news [count]` | `news(pageSize: count)` | latest club news headlines |
| `/events` | `events(fetchType: upcoming)` | upcoming calendar events |
| `/members` | `clubStats` (member-count field only) | **total member count ONLY** — see guardrail |
| `/club` | `clubInfo` | club name, city, contact summary |

**Explicitly NOT in Discord** (Mark doesn't use them): **GPX library, For Sale & Wanted, Activities**,
plus Locations and Challenges. Trivial to add later if that changes.

**Cancelled-ride highlight — DEFERRED (Mark's decision).** Introspection of the official API shows
**`RideDto` has no cancellation field** (`isCanceled` exists only on the internal `BaseRide`, whose
Bearer token expires quickly). So a cancelled banner cannot be driven by the supported read-only API
and is deferred with writes/internal-reads. Design retained for when an internal read path is added:
when a ride is cancelled, the next-ride output should lead with a prominent **bright-red, bold banner**:
- **CLI (`cyql nextride`):** a `rich` red `Panel` / bold-red text, e.g. `🚫 THIS RIDE IS CANCELLED` above
  the ride details — `rich` renders true bright-red bold in the terminal.
- **Discord (`/nextride`):** Discord can't color arbitrary message text, so the equivalent is a **red embed**
  (color `0xFF0000`) whose **title/first field is bold `🚫 CANCELLED`** (+ reason), shown above the details.
  (A red ANSI code block is a fallback if literal red text in the body is wanted.)

### Privacy guardrail (hard requirement from Mark)

**Discord users must never be able to query other Cyql members.** Enforcement is structural, not just
policy: the bot's Cyql client **excludes the `members`/`memberById` methods entirely** — it can only call
`clubStats`. So `/members` returns **only the total member count**; there is no code path that can return a
member's name, email, phone, or any per-person record to Discord. (Per-member data stays in the CLI, for
admin use.)

### Push notifications — DEFERRED (Mark's decision; documented in `docs/DISCORD_CHATBOX.md`)

Dropped from the initial bot. When revisited it must be poll-based (Cyql has **no** webhooks/subscriptions,
`subscriptionType: null`) — a scheduler diffs `rides`/`clubStats` vs stored state and posts to a Discord
channel webhook; note the official `RideDto` has no `isCanceled`, so an explicit "canceled" signal needs the
internal API. Original design retained below for reference:
- A **scheduled poller** (EventBridge→Lambda for Model B; cron/timer for Model A) reads
  `rides(isUpcoming: true)` (+ `clubStats`), **diffs against last-known state** (DynamoDB+TTL for Model B;
  local SQLite/JSON for Model A), and posts only the deltas.
- **Outbound to Discord** uses a channel **Incoming Webhook** URL (POST an embed) — no gateway needed for
  announcements.
- **Events detected → one embed each:** ride **canceled** (`isCanceled`→true), ride **reactivated**, **new**
  upcoming ride, ride **time/location changed**.
- **Budget reality:** official weekly budget is **5,000 complexity**. ~15-min polling (~670/wk) risks
  exhausting it; **start hourly (~168/wk)** with minimal fields, or run the poller on the internal Bearer
  API (no documented budget). Cadence is configurable.

### Rate-limit / caching strategy

Cyql's official API has a **weekly complexity budget (5,000)**, ≤200 complexity/query, depth ≤5. A bot that
hits Cyql on every command could exhaust it. **Cache** results with a short TTL (in-memory for Model A; a
small DynamoDB table with TTL for Model B), request only needed fields, and honor Discord's own rate limits.

### Testing

Unit-test the Ed25519 verify (valid / tampered / stale-timestamp → reject), command→embed formatting, and
the defer→followup flow (mock the Discord + Cyql I/O boundaries). Functional tests run against the local
Cyql GraphQL mock server (Part 3). Branch-coverage gate applies as elsewhere.

---

## Verification

- **Unit:** `pytest tests/unit --cov=src/cyql --cov-branch --cov-fail-under=90` (httpx mocked via respx; Hypothesis on pure fns).
- **Functional (separate process):** start `tools/mockserver`, run `pytest tests/functional` pointing the client at the local server — no client-side mocks.
- **Lint/type:** `ruff check .` (target-version py314), `mypy src/cyql`.
- **Live smoke (read-only, Mark-run):** `cyql --auth session-token members list` and `cyql stats`
  against the real API using Mark's token — confirms the confirmed queries against production data.
- **Official-key smoke:** once a key exists, `cyql --auth api-key stats` against `/api/graphql`.

---

## Confidence: ~95%

**High-confidence (directly observed):** both endpoints, the Bearer-no-cookies auth mechanism
(live-proven), the full internal read-query surface and field names, GORBA's plan name (`Club Pro`),
and that a live query succeeded. The **official API key now exists** (in `.env`), so the default
`X-Api-Key` path is confirmed. The Discord facts (two connection models, slash-command mechanics,
3s/defer, Ed25519, Lambda serverless pattern) are sourced from discord.py + Discord developer docs.
The standard Python/AWS stack is well-documented.

**Decisions locked (Mark):** ride writes are **deferred** (read-only v1 — no mutations); Discord **hosting
is chosen at Phase 3** (core stays platform-agnostic, so it doesn't block Phases 1–2). No open blockers
remain for the read-only CLI + read-only/push Discord bot.
