# Operational trial preparation — 2026-10-21

Scope: PR #4, not a release or public deployment. No accounts, subscriptions,
card entry, payments, agreement acceptance or commercial messages were performed.
Owner willingness to fund a useful test is not permission to charge an unspecified amount.

## Implemented and checked

- Added an optional loopback HTTP harness over the existing durable market store.
  Requester/provider credentials remain locally issued; no administrative HTTP API.
- Clients can create/read/delete simulated tasks and submit role-permitted events.
  Existing state machine, explicit consent, canonical transaction deduplication,
  revocation and simulation-only commission boundaries remain in force.
- Strict input schemas, 16 KiB streamed-body limit, five-second body deadline,
  generic errors, loopback peer/Host validation, no browser Origins/proxy forwarding,
  and local rate/concurrency bounds. No outbound provider execution.
- 217 tests passed locally, including 12 gateway tests. A real local Uvicorn socket
  served two separately instantiated HTTP clients; tenant and assigned-provider
  isolation, restart persistence, replay and consent were tested. These are internal
  tests, not independent adoption or an external specialist-agent trial.
- Full resultgate Bandit scan returned no findings. Wheel and sdist built;
  Twine strict checks passed. No dependencies, published version, default MCP tools
  or billing experiment changed. Security review found and closed the missing
  body-read deadline before this result.
- GitHub Actions is triggered by the PR code/test update; consult its run for the
  remote result. Local success alone is not represented as CI success.

## Next experiment and expenditure decision

See EXTERNAL-TRIAL-QUOTE.md for sources, prices and stop controls. Recommended:
owner-controlled Browser Use eligible no-card promotional account, one harmless
public-page task, separate objective verification and resource cleanup. This is
an agent-runtime integration via API, not an A2A-conformance claim. Andru is the
A2A alternative, subject to useful free-tool prerequisites.

No API key/account was available in this session and no external agent job was
submitted. Minimum identified paid fallback is a $5 USD Browser Use prepaid
credit purchase, not a guaranteed per-task cost. Checkout taxes/fees, recharge
and provider-enforced all-in stop behavior must be inspected before asking for
approval of the exact charge. Do not treat model-budget settings as total-cost caps.
No paid hosting is required to establish this first execution proof.

## Commercial and independent-use gates

The strongest documented automated revenue-share lead remains Firecrawl for
Platforms Standard: users pay the provider, approved partners may share revenue.
ResultGate is not approved; exact rate, machine-origin attribution, signed paid
conversion evidence, refunds and settlement need written confirmation. This is
a service partnership lead, not proof of an independent specialist-agent network.
Claix's current product scope needs requalification; older document-agent material
is not a current configured trial. No independent agent operator has agreed to
ResultGate commission terms.

An external provider can apply through the existing GitHub provider application
form. An external requester can install the published local package and follow
START.md; neither action adds them to a live common registry automatically.
For one real trial, request a narrow public-data task with predeclared acceptance
criteria through the existing pilot instructions. Keep voluntarily supplied
redacted evidence separate from internal fixtures; self-reports remain unverified
until reviewed. No fabricated issue, customer or outreach was created.

Next commercial action requiring separate permission: contact exactly one
candidate about agent-origin referrals, attribution/evidence and negotiated
commission terms. Signing/enrollment remains a separate owner decision. A free
execution or our own paid test never establishes a qualifying commercial referral.

## Remaining deployment gap

This is a shared store for trusted clients on one host, not a public shared market.
Before public hosting: select and approve a specific service/budget, implement TLS
and production identity lifecycle, remote operator/provider authorization,
distributed abuse limits, backup/recovery and commercial-grade retention. Current
30-day simulation tombstones are not adequate for arbitrary real refund windows.
Do not expose this harness through a tunnel as a shortcut.

Real independent usage: unproven. New successful specialist-agent execution:
not achieved in this session. Actual commissions and collected revenue: none
verified. Money spent by this work: $0.
