# Discord bot (read-only) — design & hosting

A Discord bot that surfaces **read-only** Cyql data for the GORBA club, built on the shared
`cyql` core. The bot holds **its own server-side Cyql API key**; Discord users never need Cyql
accounts.

> **Scope (current):** slash commands only, read-only. **Push notifications are deferred** (see the
> bottom of this doc for what's required).

## Slash commands (distinct top-level commands)

| Command | Cyql source (official, read-only) | Output |
|---|---|---|
| `/nextride` | `rides(isUpcoming: true, pageSize: 1)` | the next ride: title, when, location, distance, type, riders |
| `/rides [count]` | `rides(isUpcoming: true, pageSize: count)` | upcoming rides list (default 5) |
| `/ride <search>` | `rides(search: …)` | the first matching ride's details |
| `/stats` | `clubStats` | members, admins, rides, total km |
| `/news [count]` | `news(pageSize: count)` | latest club news headlines |
| `/events` | `events` | upcoming calendar events |
| `/members` | `clubStats` (member-count field only) | **total member count ONLY** — see guardrail |
| `/club` | `clubInfo` | club name, city, contact |

**Not implemented** (Mark doesn't use them): GPX library, For Sale & Wanted, Activities, Locations,
Challenges.

### Privacy guardrail (hard requirement)

Discord users must **never** be able to query other members. Enforced structurally: the bot's Cyql
client **excludes `members`/`memberById` entirely** and can only call `clubStats`, so `/members`
returns only the total count. There is no code path that can leak a member's name/email/phone to
Discord. Per-member detail stays in the CLI (admin use).

## Hosting — a bot needs *some* compute (no zero-infrastructure option)

A custom bot that calls the Cyql API must run *somewhere*. Discord offers two connection models, and
the realistic "no hosting bill" choices follow from them:

| Option | What it is | Fits "no external hosting"? | Reuses Python core? | Caveats |
|---|---|---|---|---|
| **Run locally (gateway)** | `discord.py` on your machine / Raspberry Pi; dials *out* to Discord over WebSocket | **Yes** — no cloud account, no public endpoint, no tunnel | **Yes** | Only responds while the machine is on |
| **Cloudflare Workers (free)** | Discord's official host-free serverless; HTTP Interactions Endpoint at the edge | Managed/free, but is external infra | No (JS/TS; reimplements API calls) | Slash-commands only; Ed25519 verify; no gateway events |
| AWS Lambda + API Gateway | Serverless HTTP interactions | Free tier, but an AWS account/infra | No (or via Lambda Python) | Same HTTP-interactions constraints |

**Recommendation:** for "no external hosting" **and** reuse of the Python core, **run `discord.py`
locally** (gateway). It uniquely needs no cloud, no public endpoint, and no tunnel — it connects out
to Discord. The only tradeoff is that the bot is online only while the host machine runs. If
always-on availability matters more than reusing the Python core, **Cloudflare Workers (free)** is
Discord's recommended host-free path. **(Final choice pending Mark.)**

Sources: Discord [Interactions overview](https://docs.discord.com/developers/interactions/overview),
[Hosting on Cloudflare Workers](https://docs.discord.com/developers/tutorials/hosting-on-cloudflare-workers).

## Setup (any model)

1. Discord Developer Portal → create application → add a **Bot** → copy the **bot token** (and, for
   HTTP models, the **application public key** + **application id**) — store as secrets in `.env`.
2. Invite to the GORBA server with OAuth2 scopes **`bot` + `applications.commands`**, minimal
   send-message permission. (GORBA's Discord is members-only; a server admin with **Manage Server**
   adds the bot — the public invite link is not needed for that.)
3. Register slash commands to the **GORBA guild** (guild commands appear instantly; global commands
   take up to ~1 h to propagate).

## DEFERRED — push notifications ("ride canceled → Discord")

Not built yet (Mark's decision). What it will require when revisited:

- **A scheduler + state store** (Cyql has **no webhooks/subscriptions** — confirmed
  `subscriptionType: null` — so push must be *polled*): on a schedule, read `rides`(+`clubStats`),
  **diff against last-known state**, and post only the changes.
- **A Discord channel incoming webhook** (a webhook URL) to post announcement embeds — no gateway
  needed for outbound posts.
- **Budget awareness:** the official key has a **weekly complexity budget of 5,000**; poll
  infrequently (e.g. hourly) and request minimal fields.
- **Cancellation caveat:** the official `RideDto` has **no `isCanceled` field**, so a true
  "ride canceled" signal would require the unsupported internal API (Bearer JWT). A poller on the
  official API can only detect a ride *disappearing* from the upcoming feed, not an explicit cancel.
- Hosting: the local-gateway model would use a local timer; a serverless model would use a scheduler
  (e.g. Cloudflare Cron Triggers / EventBridge) — chosen alongside the bot hosting decision above.
