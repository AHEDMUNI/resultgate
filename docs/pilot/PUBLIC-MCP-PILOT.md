# ResultGate: staged authenticated MCP pilot

## Actual state and review of PR4–7

Owner reports systemd service on 64.227.3.178 with local health 200 after reboot.
This supersedes PR7's historical deployment uncertainty but is not an independent
remote observation. SSH here reached the host, then failed public-key authentication;
no private key was requested, read, generated or copied. No server mutations occurred.

PR4 supplies tenant/provider scope, task commitments, consent and replay protection;
PR5 adds durable shared tenant/role quotas and simulation settlement;
PR6 supplies approved registry search and restore quarantine;
PR7 supplies private systemd deployment and bounded backups. They remain stacked
open PRs, not four independent changes to merge blindly. Review baseline is PR7
bd73a5dad3b4d093f30899cb98ad32ecb4d9913f. Local health is not commercial readiness.

## Prepared addition

Authenticated /mcp supports stateless JSON responses for initialize, ping,
tools/list, tools/call and initialized/cancelled notifications. GET and DELETE
return 405 after authentication. No SSE, sessions, OAuth discovery, browser clients,
dynamic client registration or provider execution. Protocol versions 2025-03-26,
2025-06-18 and 2025-11-25. It is an invite-only bearer-token pilot, not a claim of
general MCP authorization interoperability or ChatGPT connector compatibility.
Reference: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports

Three tools: search_providers, create_simulation_task, get_simulation_task.
No MarketOperator, registration, acceptance, matching, verification, settlement,
network fetch or payment is exposed. Every MCP request authenticates and consumes
the durable 120/minute tenant/role allowance, shared across credentials/restarts.
Existing capacity: 1000 tasks/tenant, 10000 total, 1000 credentials, 30-day expiry.
Body cap 16KiB / five seconds; bounded concurrency remains 16. Spend cap is exactly
zero enforced by the market; sending a positive cost is not an authorization.

Only /mcp is staged for TLS proxying. /healthz and /v1 stay private. nginx template
overwrites forwarding headers, fixes upstream Host, preserves Origin rejection,
limits ingress and writes only timestamp/status/duration. Configure logrotate and
disk monitoring before enabling; nginx error logs can contain request metadata.
Do not use credentials in URL queries. Keep access restricted to invited clients.
Bearer secrets remain outside chat/repo/logs, distributed through an approved
secret channel. They expire in 30 days; local operator revocation is immediate.

## Agent enrollment and first independent pilot

1. Choose one provider with ownership evidence and one unrelated customer with a
   concrete public-data task. Firecrawl is a candidate only; prior inquiry is not
   an agreement, response, integration or approved commission entitlement.
2. Operator reviews provider metadata, endpoint ownership, capability, privacy,
   limits and price. Existing Registry submission/review methods remain local.
   Never fetch an arbitrary registered endpoint; live adapters need allowlisted
   destinations, TLS checks, SSRF defenses, timeouts and response size limits.
3. Issue separate MarketOperator credentials for the customer's tenant and the
   approved provider ID. Never reuse a provider management token as an API token.
   An agent is a credential-bound client, not a new privileged role. Agents acting
   for one customer share that customer's tenant budget, not separate allowances.
4. Customer tests initialize/list/search/create/get on /mcp using a compatible
   bearer-capable MCP client. Define one success criterion before execution.
   Record opaque task ID, timestamps, outcome, manual effort and direct-client cost.
5. First real task remains BLOCKED until a reviewed adapter and per-task consent,
   provider price/currency, atomic spend reservation, timeout ambiguity handling,
   independent verification and authenticated payment evidence exist. A configured
   nonzero number must never silently enable execution. No live budget is approved.
6. Compare against the customer's direct provider path. Count only independently
   completed useful tasks as adoption. Do not claim a call-count or reliability
   improvement from the existing synthetic benchmark.

## Proposed direct-provider commission model (unsigned)

Customer pays the provider in the provider's checkout/account; ResultGate holds no
customer funds and stores no payment credentials. Provider owes ResultGate only
under a separately approved agreement, never because simulation says eligible.
Proposed negotiating baseline: 10% of attributable net service revenue actually
collected, excluding tax, refunds, chargebacks and agreed pass-through costs.
Example only: $20 eligible net collection gives $2 commission. These are neither
agreed terms nor a debt. Provider acceptance and owner's approval are still required.

Agree attribution window, currency, refund window, invoice cadence, minimum payout,
dispute process, data sharing and cancellation before launch. Bind task/offer and
agreement version to a provider-side reference. Verify signed provider webhooks
with timestamp/replay checks and server-side reconciliation; never trust screenshots
or client success redirects as payment proof. Unique provider transaction identity
prevents double attribution. Refunds create compensating reversals. Commission
collection starts as a reconciled provider invoice, no automatic debit or transfer.
The current settlement ledger is simulation only and cannot book actual receivables.

## Minimal next operator action

No repeated manual health/reboot checks are requested. Establish the existing
trusted SSH/DO-console session once. On the trusted computer, use the existing key:

    ssh -o StrictHostKeyChecking=yes resultgateadmin@64.227.3.178

If its known-host record is absent, compare the host fingerprint with the DO console
before adding it; never disable host verification. Do not upload private keys.
With that session available, deployment can use a reviewed immutable commit,
existing private state and an offline rehearsal before changing the service.

Before PUBLIC activation owner must specifically authorize domain/TLS configuration
and inbound 443 in host/cloud firewalls. No port80, public DB, paid certificate,
Droplet upgrade, outbound provider call, agreement or payment is implied.
Actual public activation also needs reviewed nginx syntax/certificate, token
revocation/isolation rehearsal through TLS, and monitoring/backup retention ownership.
Current backup script stops after seven snapshots; assign rotation responsibility
or it will stop producing new snapshots. Do not open public ingress with an
unresolved restore quarantine or missing backup owner.
