# Smallest external specialist-agent trial

Research checked 2026-10-21. This is a proposal, not a purchase authorization,
checkout quote, executed integration or commercial agreement. No account was
created, card added, task submitted or money spent for this research.

## Recommendation

Start with a **no-card free account**, not paid hosting or a subscription.
Browser Use is the clearest public-fixture experiment: a hosted browser agent
can inspect a public page and return a verifiable answer without connecting a
calendar, mailbox or private database. Andru is a useful A2A specialist candidate,
but its free generation tool can require account/calendar context. Check that
prerequisite before treating it as the primary execution experiment.

The immediate blocker is an owner-controlled account/API key and permission to
submit the specified public fixture. Provision credentials in a local secret
environment; do not paste them into issues, commits, reports or chat transcripts.
No payment is needed to determine whether the available free allowance works.

## Purchase and usage are different costs

| Option | Published entry cost | Recurring obligation | Decision |
| --- | --- | --- | --- |
| Browser Use eligible new signup | $1 promotional credit; no card | None; credit does not renew | First choice for public browsing task |
| Browser Use paid fallback | Minimum **$5 USD prepaid top-up** | No subscription; usage consumes credit | Only after separate approval of final checkout total and charge controls |
| Andru free account | $5 starter balance; eligible A2A daily allowance | No subscription | Prefer quota-covered tool, not wallet consumption |
| Andru paid fallback | Minimum **$25 USD wallet top-up** | Saved card can trigger $25 automatic top-ups | Not recommended for this first experiment |
| Claix retrieval | 100 successful free calls; managed retrieval €0.10/question afterward | Usage-dependent | Requires database/agent setup; unnecessary for first public task |

Browser Use [pricing](https://browser-use.com/pricing) gives a 20% model markup,
$0.02/browser-hour rounded to whole minutes, and traffic at $5/GB residential
(default) or $0.20/GB direct. Displayed V4 token prices already include markup.
The $5 is a credit purchase, **not the price or maximum cost of one task**.
Taxes, payment fees, balance exhaustion behavior and automatic recharge settings
have not been inspected in an authenticated checkout. Do not buy if the final
charge exceeds the specifically approved amount. A free-credit account is
preferable to assuming a prepaid wallet guarantees no overrun.

[Andru pricing](https://andru-ai.com/pricing) says adding a card enables automatic
$25 top-ups below $5, subject to a weekly limit (default $50); Billing can disable
this. Do not add a card for this trial. Public prices are $3/$12/$49 by asset
class. This is not evidence that every $3 operation is free: use the narrower
[A2A tool eligibility](https://andru-ai.com/docs/a2a), not the marketing summary.

[Claix's current homepage](https://www.claix.dev/) describes a controlled database
retrieval product, API/MCP/A2A agent endpoints, and €0.10 managed-AI/question or
€0.02 BYOK/question plus the model provider. Older document-processing articles
must not substitute for the current configured product's quote. No verified
minimum paid deposit or hard spending cap was found. It requires a configured
read-only database and agent; this is not an already provisioned independent
specialist accepting arbitrary tasks.

## Browser Use experiment: one public task

Proposed task: open `https://example.com`, return JSON containing the page title,
first heading, and whether it describes use in documentation. No login, form
submission, purchases, private URL, uploaded file or credential is needed.
Validate against independently fetched public page content, not the agent's
self-reported success. This tests actual remote agent execution with objective
criteria; it does not establish market demand or useful commercial performance.
A subsequent consented public-data task is necessary to test product value.

The [official V4 integration guide](https://github.com/browser-use/browser-use/blob/main/skills/cloud/references/api-v4.md)
uses `POST https://api.browser-use.com/api/v4/runs`, API-key authentication and
`maxCostUsd`. An eligible Google/GitHub/Microsoft signup gets the free credit;
email/password signup does not. Use the account's free-eligible model. A proposed
initial model budget is **$0.10**, one run, no follow-up queue, no automatic
resubmission. This is an experiment setting, not an all-in guaranteed price.

The [V4 OpenAPI](https://docs.browser-use.com/cloud/openapi/v4.json) exposes
`maxCostUsd`, but does not document it as a hard all-in spending ceiling. Its
monthly API-key limit is explicitly a soft stop. Run cost excludes session
browser/traffic charges; session costs can settle after completion. Therefore:

1. Reserve one durable local request before sending; never blindly retry an
   ambiguous create timeout. Reconcile remotely before deciding what happened.
2. Poll `/runs/{id}/status`; on abandonment call `POST /runs/{id}/cancel`.
3. Explicitly stop the session browser using `PATCH /browsers/{session_id}` with
   `{"action":"stop"}`; merely closing the client is insufficient.
4. Check `/sessions/{session_id}/cost` after cleanup and later settlement.
   Confirm cancellation/stop failures are resolved before another run.

These controls reduce risk; network loss and delayed accounting prevent calling
our client timer a guaranteed billing cap. Before paid execution, verify the
account's recharge settings and provider-enforced total limit. If unavailable,
request explicit approval for the documented residual risk rather than asserting
a hard $0.10 ceiling. Stop browser resources, revoke the trial key, and disable
recharge to end further access. Revoking a key alone is not evidence that existing
resources stopped.

Illustrative arithmetic only: 20,000 uncached input tokens and 2,000 output tokens
at the displayed GPT-5.6 Luna rates cost $0.00768. Two browser minutes cost about
$0.000667. 1 MB traffic adds approximately $0.0002 direct or $0.005 residential
(using decimal GB). Total roughly **$0.00855–$0.01335**. Real model availability,
tokens, traffic and duration are unknown; this is neither a measured task cost
nor a promised bound. Do not use benchmark task prices as Cloud quotations.

## Andru A2A alternative

The [A2A guide](https://andru-ai.com/docs/a2a) documents signed discovery and result
attestations, API-key access, `SendMessage` with `A2A-Version: 1.0`, or
`message/send` for 0.3. Reusing a message ID returns the original task without
rerunning or charging. Read remaining allowance via `/api/a2a/quota`. Cancel
through `CancelTask`; failure is reported without charging. Five daily A2A free
calls cover pre-meeting briefs; catalog assets remain paid.

[`get_pre_brief`](https://andru-ai.com/docs/mcp/tools/get_pre_brief) is listed at
$3 and explicitly covered by free daily calls. It accepts company/meeting
context and can look up calendar events. First check whether synthetic company
context works without attaching personal integrations. If it requests calendar
access or private contacts, stop that experiment and use Browser Use instead.
Do not invent a meeting, connect a personal calendar, or count an input-required
response as successful delegated work. A generated brief can establish execution
but its unsupported business claims must not be marked factually verified.

## Acceptance and financial boundary

Record internal experiment origin, provider identity, task ID, terminal state,
validated output hash, verification checks, and redacted usage/cost evidence.
Never store keys or default to storing task content. No internal experiment is
independent third-party usage. A free or paid provider call does not establish a
referral agreement, payment by a customer, commission eligibility or revenue.

Next owner action: choose/provision a no-card account and make its API key
available securely. If free access is unavailable, the smallest identified paid
fallback is Browser Use's **$5 one-time credit purchase**, subject to the final
checkout and cost-control checks above. Ask for that exact total before purchase.
No paid hosting is required for this proof; shared-network deployment is a
separate security and budget decision.
