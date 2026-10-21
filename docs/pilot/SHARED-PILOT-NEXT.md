# Shared pilot checkpoint

Reviewed October 20, 2026, America/Chicago. No public deployment or spending.
The owner reports the Firecrawl inquiry was sent; no duplicate inquiry was sent.

## Reviewed changes and release boundary

PR #4 head `07d97153e89f2e14d1478ee2bae918d14c0f5eca` and PR #5 head
`3da6020d4f738c060e5e3eada95831c95dfb4cf8` both have successful CI. Browser Use
evidence still records one task, cost $0.005671 and a stopped browser. The one-shot
workflow remains disabled. No live account/balance check or new task was needed.
The current security review recommends PR #4 only as a local/simulation foundation.
Owner approval is required to merge it. Then retarget PR #5 to main and re-run
checks before a separate merge approval. No package version change is proposed.

## Shared catalog operation

The loopback gateway now accepts authenticated `POST /v1/providers/search` with:

```json
{"capability":"citation_structuring","offset":0,"limit":25}
```

Use a requester/provider bearer credential issued by the local operator, not the
provider's management token. Do not place credentials in URLs, public examples,
shell arguments or issue reports. Search reads the same operator SQLite Registry
used by other clients/processes. It returns reviewed metadata including declared
prices and limits, filters pending/rejected/suspended entries, and never makes
provider endpoints executable. Prices are declarations, not binding live quotes.
Limits are 50 results/page and the durable tenant request budget. IDs determine
stable ordering; concurrent catalog changes can move offsets, so consumers should
deduplicate IDs rather than treating pagination as a frozen snapshot.

This is an internal HTTP contract, not a new MCP tool or A2A implementation.
The server retains loopback, Host, Origin, body-size and authentication boundaries.
Do not expose it directly or use a reverse proxy to bypass those restrictions.
No incoming endpoint can review ownership, approve an agreement or dispatch an
arbitrary submitted provider. Existing GitHub/MCP submission plus local operator
ownership review remains the onboarding route. Shared remote enrollment is pending.

## Readiness gates before the first controlled public host

1. Separate reviewed TLS ingress with trusted proxy handling, private operator
   administration and explicit enrollment/revocation for requester and provider
   identities. Existing bearer roles are local-issued, not a finished signup flow.
2. Fixed single-host durable database; owner-only files, bounded logs, private
   backups, tested recovery and dispatch reconciliation. See [RECOVERY.md](RECOVERY.md).
   Recovery is now locally testable but no scheduled/off-host encrypted backup
   service or production monitoring has been deployed.
3. Reviewed provider-specific execution adapter with each user's own authorization,
   frozen offer/price, spending reservation, timeout/cancel/status reconciliation
   and no retries for ambiguous dispatch. Existing market task records remain
   simulations; the historical Browser Use trial is not this public executor.
4. Run load/abuse tests against the exact deployment artifact under its memory
   limit; validate tenant isolation and restoration before enabling public access.
5. Commission rights require an actual accepted contract and authoritative paid
   event. The local settlement sandbox is not a payment-provider integration.

These are unresolved engineering gates, not requests to buy hosting now. A single
central database and backed-up identity key are prepared locally, but a publicly
available safe multi-tenant execution market is not yet delivered.

## Value and commercial evidence

The [offline A/B benchmark](BROKER-VALUE.md) did not establish a reliability,
request-count or full-cost advantage over a competent direct integration. Its
measurements cover only local overhead and injected failure handling. Next test
the same approved task across two providers using one interface, then measure an
independent developer's integration effort. Do not invent adoption or infer that
a provider-funded commission automatically saves customer money.

[FIRST-TRANSACTION-NEXT.md](FIRST-TRANSACTION-NEXT.md) records the pending Firecrawl
route, another specialist-agent inquiry, documented referral alternatives and
hosting costs/limits. No qualifying commercial partner or independent paid task
has been established. Keep external usage voluntary, minimal and separately
classified; synthetic fixtures and our CI always remain internal.
