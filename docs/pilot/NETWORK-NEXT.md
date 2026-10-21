# Network track: executable agents, direct partnerships and shared-registry design

Checked 2026-10-20 America/Chicago. This document records research and a proposed implementation sequence, not a deployed shared service or a signed partnership. No outreach, signup, credentials, paid calls or provider agreement acceptance occurred. No new real autonomous-agent execution has been demonstrated by this research.

## First direct-provider candidates

| Candidate | What is actually documented | Calling / cost boundary | Direct commission status |
|---|---|---|---|
| **Claix** — first proposed direct discussion | Provider describes an A2A document agent with extraction/schema/document-question skills. The official terms identify an operator trading as Claix. This is a provider-declared specialized agent, not an independently executed ResultGate integration. | Public Agent Card; authenticated JSON-RPC `message/send` at `https://claix.dev/a2a`, API-key header or Bearer. Docs state60requests/minute. Advertises100trial calls, subject to configuration; BYOK can incur third-party model charges. Need owner-created account/key and confirmed zero-cost entitlement before one permitted test. | No documented acceptance of ResultGate commissions or agent-origin paid attribution. Claix terms section6 require prior written authorization to commercialize direct API access, while permitting compliant embedded-backend use subject to plan restrictions. A direct agreement is a **proposal**, not an existing program. Best fit by narrow document workflow and current ResultGate verification experience; not a prediction that the operator will agree. |
| **Browser Use hosted web agents** — technical fallback | Official product accepts a natural-language task, runs a hosted browser agent, returns structured/text output and run lifecycle. Distinct from renting browser infrastructure, which alone is not an agent. | Current developer page documents API V4 with `X-Browser-Use-API-Key`; MCP uses OAuth PKCE. Pricing lists a one-time$1 eligible-signup credit, model cost+20% plus browser/traffic, with proxy charges possible. Account, confirmed spend cap/entitlement and bounded read-only task needed. No account or execution here. | No direct ResultGate revenue-share agreement or automation referral permission verified. A provider-approved task-level or paid-conversion agreement and settlement evidence are necessary. Do not use benchmark headline price as total task cost. |
| **Independent builders on Relevance AI** — sourcing channel, not a selected provider | Platform supports agent conversations/triggers via API. Official partner program advertises commissions/discounts, approval and certification. It is a platform, not proof that a particular builder's agent is independently executable or for sale. | Each builder must submit their actual agent endpoint, owner authority, service constraints, free sandbox and credentials scheme. Platform account/API credentials and usage terms need confirmation. | No public fixed rate or ResultGate-specific agent-referral permission established. Prefer a builder's explicit service agreement over assuming platform affiliate terms apply. No builder contacted or enrolled. |

Sources (primary):
1. https://www.claix.dev/documentation/a2a
2. https://www.claix.dev/terms
3. https://www.claix.dev/blog/free-document-processing-100-calls-byok
4. https://browser-use.com/web-agent-api
5. https://browser-use.com/developers
6. https://browser-use.com/pricing
7. https://relevanceai.com/partners
8. https://relevanceai.com/docs/build/agents/extend-your-agent/conversation

API capability is not commercial permission. A public Agent Card is not authentication of the business or proof of protocol conformance. Protocol versions must be negotiated/tested against the provider; Claix's documented message/send shape must not be advertised as proof of ResultGate supporting all current A2A operations. GROBID remains an existing specialized ML demo, not an autonomous agent and not a commission partner.

### The first authorized integration experiment

Candidate: Claix, conditional on owner-supplied credentials and verified100-call trial eligibility without charging or BYOK. Use a synthetic/public short document, a fixed extraction schema and predeclared field values. Disclose only that fixture with explicit consent. Require:

1. Review current Agent Card and official terms, endpoint identity and API version; allowlist one exact HTTPS origin, prohibit provider-selected URLs, redirects and arbitrary code.
2. Implement a narrow disabled-by-default adapter in a new PR, with mock transport tests first: authentication stays in secret storage/environment, never task payload/registry metadata/logs. HTTP headers are redacted.
3. Bind request ID, provider ID, task payload hash and expected schema before send. Poll only a documented status operation; distinguish input-required/working/completed/failed/unknown. Do not assume JSON-RPC request IDs provide provider-side idempotency. If a sent request times out, reconcile by documented task ID or stop; never silently repeat it.
4. At most one live trial operation after entitlement/consent; validate task artifacts and declared output fields, record hashes and internal-test classification. An unsuccessful trial or API200 without accepted output is not success.
5. Do not mint commission on trial success. Production traffic and commission reporting require a separate complete agreement, production permission, user acceptance and provider-side economic reconciliation.

No adapter should fetch untrusted document URLs on the user's behalf. Prefer bounded inline public fixture bytes for the first test. Claix trial and Browser Use credits are advertised offers, not verified account balances. Obtaining keys/account acceptance is the external blocker; offline adapter/schema design can continue without them.

## Shared registry: practical next architecture

A local registry cannot synchronize independent installations by itself. Keep the current local mode usable; develop the following behind a disabled configuration and loopback-only tests, not an insecure public deployment.

| Component | Design and trust boundary | Required acceptance test |
|---|---|---|
| Identity | OIDC login for provider operators; validate issuer/audience/signature/expiry; map `(issuer, subject)` to server-assigned tenant. No client-supplied tenant override. Operator/admin identities separate from provider roles. | Wrong issuer/audience/expired token, foreign tenant ID and provider-to-admin escalation rejected. |
| Authorization | Scoped service tokens for agent clients (`catalog:read`, `task:submit`, `task:read-own`); provider-owner capabilities only on own records. Admin review endpoints separate and unavailable in public MCP. No shared all-powerful token. | Two tenants cannot read, mutate, delete or receive each other's tasks, secrets, agreements or receipts, including guessed IDs. |
| Persistence | PostgreSQL migration rather than shared SQLite files; tenant keys on private tables, row-level policies plus application checks; unique `(provider, event)` and economic outcome indexes; transactions/outbox for dispatch. Restricted worker database role; encryption/backups and restore policy. | Cross-tenant queries denied, concurrency dedup, restart/restore retains attribution, outbox replay never duplicates dispatch. |
| Public catalog | Sanitized approved public metadata only; explicit `verified_at`, expiry/revocation and executable-adapter identifier. Read-only cache/static export may be shared first, but is not an execution service. Signed/revisioned operator publication only; providers cannot self-publish approved status. | Revoked/expired entries disappear; tampered snapshot rejected; untrusted descriptions stay data, not instructions. |
| Ownership | Server-issued expiring one-time challenge bound to tenant+exact origin+submission revision. Controlled HTTPS or DNS proof; bounded public-address resolution/TLS pinning, no redirects or private networks. Domain control and legal authority reviewed separately. | DNS rebinding/private IP/redirect, replayed proof, changed endpoint and expired challenge fail closed. |
| Execution | Only vetted adapter IDs, not arbitrary submitted MCP commands or remote code. Explicit per-task disclosure consent, server-side quotas/deadline/budget, fixed allowed destinations, isolated workers. | Missing consent, unknown adapter, oversized payload, timeout/cancel, duplicate dispatch and forbidden network access rejected. |
| Receipt ingestion | Provider-specific verifier with key-ID rotation, exact raw-body signature rules, timestamp/replay controls, agreement/tenant/referral binding. Authenticated receipts prove origin, not a truthful sale; reconcile to provider transaction records. | Cross-provider signing key, stale/replayed/conflicting event, disputed/refunded outcome or terms mismatch cannot qualify. |
| Data lifecycle | Opt-in minimal events, retention and tenant deletion job; backups with separately documented expiry. No task bodies by default. Audit of privileged review; no raw credentials in audit. | Delete across private tables, retained dedup tombstones policy, no confidential data in public export. |

This is a design proposal; these multi-tenant controls are not implemented or deployed by the current local pilot. First implementation should be authorization/schema contracts and cross-tenant tests in a new PR, followed by local containers with no cloud account. Public activation remains an explicit security/owner gate. Free ephemeral hosting is not a durable registry solution.

## Organic path to the first independent request

1. Publish the reviewed package and truthful MCP metadata only after release checks; verify the actual public install and listed tool flags. Link one clear start guide, actual acceptance receipt and provider application form from README/registry documentation. These are discovery artifacts, not claims of existing network traffic.
2. Keep the original useful extraction/citation checks accessible without onboarding or telemetry; opt-in brokerage points to reviewed capabilities. Demonstrate exactly what works, what sends data, what is demo-only and what requires an account. A developer must be able to install/run without operator help on every call.
3. An unaffiliated evaluator chooses their own permitted public task and predeclared criteria. The canned acceptance tutorial remains a test, even if an outsider runs it. A useful independently chosen demonstration may evidence independent evaluation, but is not automatically a production customer job or commercial conversion.
4. Offer optional aggregate self-report with consent and a pseudonymous installation ID; no mandatory signup, tracking pixel or task-content upload. Treat every received report as unverified until independence, real task, outcome and permission are reviewed. Compare snapshots for recurrence, never sum duplicate reports. Allow deletion and explain GitHub public retention.
5. First provider application: public metadata -> challenge -> operator review -> explicitly negotiated terms -> reviewed adapter/free test -> production authorization. Neither application count nor an approved listing is a completed referral.
6. First commercial referral: a real external user authorizes a task/paid conversion, provider accepts a documented referral, successful accepted outcome and provider economic evidence are reconciled under the exact active agreement, refund/dispute maturity clears, then record eligibility once. Payments remain off. No trial, internal test, free user or success HTTP response is booked as revenue.

No ads, unsolicited commercial messages, paid listings or artificial issue submissions are necessary for this path. Discovery alone cannot guarantee visitors; the first externally submitted evidence is the measurable gate. Do not schedule background claims without an actual monitoring job.

## Recheck and integration gates

The official Claix A2A page, Claix terms section 6 and trial page, Browser Use developer/pricing pages, and Relevance AI partner/conversation pages were re-opened during this continuation. Their published capabilities and approval boundaries support the comparison above; no authenticated task was sent. Relevance AI's conversation quickstart asks for an Admin-role key. Do not ask an external builder to disclose that broad project credential to ResultGate: require a provider-controlled relay or a demonstrated least-privilege credential before an executable adapter is reviewed.

Before any direct commission partnership, obtain explicit written answers covering **agent-origin referrals**, identity/authority of both parties, attribution registration and expiry, the qualifying paid event, exact rate and currency/base, eligible accounts, refunds/disputes and maturity, and provider reconciliation/export or signed callback rules. An ordinary API account or permissive technical integration does not answer these questions. No candidate currently satisfies this commercial gate.

The narrow next user decision is whether to create a Claix trial account personally and provide a scoped secret through an appropriate secret mechanism, after confirming no billing instrument or paid/BYOK usage is enabled. That would authorize a bounded technical trial only. Commercial outreach, acceptance of a negotiated agreement, public shared hosting, and collection remain separate decisions. While those are pending, local adapter contract tests, tenant-isolation tests and reviewable reporting improvements require no external account.
