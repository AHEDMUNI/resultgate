# First commercial transaction: decision record

Reviewed 2026-10-20 (America/Chicago). Research only: no enrollment, account creation, outreach, agreement acceptance, provisioning, spending, invoice or collection. None of these candidates has accepted ResultGate or authorized its agent-origin commission model. Technical API permission is not referral entitlement. All current commercial fixtures remain simulations.

## 2026-10-21 qualification update

The current Claix homepage describes database retrieval with configured read-only database/agent setup. The older document-processing materials below are historical research, not a verified ready-to-call current trial or current price. Reconfirm the exact product, entitlement and commercial permission before shortlisting it. For the first specialist execution test, see [the current external-trial quote](EXTERNAL-TRIAL-QUOTE.md): Browser Use no-card promotional credit is a more direct public-fixture candidate; neither it nor Andru has agreed to commissions. Firecrawl Standard remains the strongest documented platform revenue-share lead, subject to approval and agent-origin attribution confirmation.

## Three candidates, ranked in the original research

| Candidate | Fit and commercial evidence | Actual blocker / next authorized decision |
|---|---|---|
| **Firecrawl for Platforms — Standard** | Strongest documented automated platform integration plus separately approved revenue sharing. A web capability provider; do not label every Firecrawl endpoint an independent agent. | Owner-approved account/agreement and partner application; written AI-origin attribution, exact rate, refund and settlement rules. No free execution entitlement for an unverified platform. |
| **Claix direct document-agent partnership** | Best narrow specialist-agent candidate for the product vision: documented A2A document tasks. A proposed direct agreement could bind a referral to one successful paid document task. | No published commission offer or agreement. API key and confirmed no-charge testing required; direct access commercialization needs written permission. Commercial outreach needs separate owner approval. |
| **Apify affiliate / open-source route** | Existing API/MCP ecosystem and documented paid-customer referral economics; easier existing program, weaker fit for a task-level broker. Actors are not automatically autonomous agents. | Owner enrollment/terms plus written approval of agent-generated referrals and attribution outside browser cookies. Thresholds can delay first cash even after a commission accrues. |

### Firecrawl: distinguish platform revenue share from affiliate links

The [official Platforms page](https://www.firecrawl.dev/firecrawl-for-platforms) documents Standard (users pay Firecrawl directly) versus Gateway (our organization funds eligible usage). Prefer Standard; Gateway conflicts with the present zero-spend scope. Revenue share is a separate reviewed application: only new paying customers referred **after approval**, first year on self-serve plans; Scale and Enterprise excluded. Public rate, settlement timing/fees and refund/chargeback treatment were not established. The page requests linked attribution branding. Automated provisioning support does not explicitly establish ResultGate's agent-origin commission eligibility.

The [API reference](https://docs.firecrawl.dev/firecrawl-for-platforms) documents server-side platform keys and `POST https://integrations.firecrawl.dev/partner/v1/accounts`, identified by a user's receivable email. User terms acceptance is required before provisioning. Critically, accounts have **no free included credits until platform verification or a signed agreement**; Standard users otherwise must fund usage, while Gateway charges the organization. Repeated requests return an existing integration account, but this is not a paid-conversion receipt. The page does not establish a partner-accessible signed billing webhook or settlement export; obtain that contract before connecting commission eligibility. Do not distribute platform keys through the local package.

The [affiliate page](https://www.firecrawl.dev/affiliates) advertises 25% for 12 months then15%, while the linked [Dub portal](https://partners.dub.co/firecrawl) advertises15% lifetime. These conflict; neither is a safe default for a ResultGate agreement. The affiliate page includes an automation FAQ heading but retrieved content did not establish its answer. No cookie window, payout minimum, fee or reversal rule was verified here. Do not substitute affiliate headline rates for Platforms revenue sharing.

### Claix: direct agreement candidate, not an existing partner

[Claix A2A docs](https://www.claix.dev/documentation/a2a) describe authenticated `message/send` and document-processing task results. This is stronger agent-to-agent protocol evidence than a generic data API, but no successful ResultGate execution or commercial agreement is asserted. [Terms](https://www.claix.dev/terms) identify the operator and restrict commercialization of direct API access without prior written authorization, while describing permitted embedded-backend use subject to conditions. The [trial article](https://www.claix.dev/blog/free-document-processing-100-calls-byok) advertises100 calls; available entitlement and configuration must be checked in an owner-controlled account. BYOK is not proof of zero cost at the model provider. Commission rate, conversion proof, refund window, settlement mechanism and fees are entirely **to be negotiated**, not zero or agreed.

### Apify: documented economics, unresolved agent attribution

[Official terms](https://docs.apify.com/legal/affiliate-program-terms-and-conditions), updated September15,2026: 20% of payments for the first3 paying months, then30%; standard caps $2,500/$5,000 depend on tier. Attribution uses a45-day cookie; missing attribution may be reviewed at Apify's discretion. General payout conditions require3 referred customers and$100 accrued, with written waivers possible. Open-source GitHub/Actor provisions remove the3-customer threshold but retain$100 and the$2,500 cap. Payment is monthly within15 business days after month-end, via PayPal/bank/Wise and valid invoicing through FirstPromoter. Self/related referrals are prohibited. Agent-origin referrals, server-to-server conversion evidence, refund reversals and payout fees are not sufficiently established for our model. Enrollment itself accepts terms and may enable automatic invoices; do not enroll during the present no-invoice phase. A successful Actor run is not proof of a qualifying paid referral.

## Smallest legitimate first-dollar path

Recommendation is an inference from the above evidence, not promised partner acceptance:

1. Seek approval to contact **one** candidate: Firecrawl Standard for the fastest existing automated commercial channel; Claix if a genuine specialist-agent task is the strict first objective. Do not send anything before owner authorization.
2. Agree explicitly that an owner-authorized requesting agent may originate referrals; specify payer, eligible outcome, rate/currency, tax/fee base, attribution lifetime, refund hold, cancellation/dispute handling and settlement minimum. Avoid funding users' services ourselves.
3. Require provider-authenticated conversion evidence containing ResultGate referral ID, unique provider conversion ID, amount/currency, paid status/time, agreement version, and later refund/chargeback references. Generic HMAC support in ResultGate is not proof that a partner implements it. Signed settlement files can be an initial manual alternative.
4. Test a public harmless task with confirmed zero-charge entitlement, then validate exact success criteria and replay/reversal behavior. Provider tests and our own purchases never count as independent demand or qualified referrals.
5. Obtain one genuinely unaffiliated, consented task from an organically discovered integration; the human/account owner separately authorizes any paid purchase. Verify provider payment, task success and acceptance before recording eligibility. Commission recorded, invoice issued, cash received and net profit remain separate milestones.

**Main blocker:** no provider-approved commercial attribution/evidence arrangement and no independently verified customer task. More MCP tools or infrastructure cannot resolve that. A directory listing is distribution, not proof that orchestration systems will choose us. Measure an actual task funnel before widening scope.

## Shared infrastructure: budget envelope, not a deployment claim

A small common control plane can serve the reviewed catalog, authenticated onboarding, tenant-scoped referral/state records and signed receipt intake; providers perform inference. Keep original Python/MCP clients local. Do not assume the existing Python package runs unchanged on an edge runtime: a Workers control-plane implementation/port and security tests are separate engineering work. No public runtime has been deployed or funded here.

[Workers official pricing](https://developers.cloudflare.com/workers/platform/pricing/): Free has100,000 requests/day and10ms CPU/invocation. Paid minimum$5/month includes10million requests and30million CPU-ms/month; excess costs$0.30/million requests and$0.02/million CPU-ms. Network waiting is not CPU, but authentication/validation and serialization must fit CPU bounds. No egress charge is listed. This is the standard Workers product, not Workers for Platforms.

[D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/): Free allows5million rows read/day,100,000 rows written/day and5GB total storage. Paid includes25billion reads/month,50million writes/month and5GB; overage is$0.001/million reads,$1/million writes and$0.75/GB-month. Index maintenance adds writes and unindexed scans add reads. [Limits](https://developers.cloudflare.com/d1/platform/limits/) cap each free database at500MB and recovery at7days (paid10GB/database and30days recovery). [D1 FAQ](https://developers.cloudflare.com/d1/reference/faq/) says free limits cause query errors, not unlimited availability.

Illustrative workload assumptions:6 HTTP requests,100 indexed row reads and20 row/index writes per task;10ms CPU/request;2KB retained metadata/task. These are planning assumptions, **not measured benchmarks**; retries, catalog searches, abuse and backups add load.

| Monthly tasks, evenly distributed | HTTP / row reads / row writes | Metadata growth before deletion | Control-plane estimate |
|---|---|---|---|
| 1,000 | 6,000 /100,000 /20,000 | ~2MB | $0 within free limits if CPU also fits |
| 100,000 | 600,000 /10million /2million | ~200MB | Potentially$0 by average quotas; ~66,667 writes/day leaves little burst/index margin. A single free DB fills in ~2.5 months at this retention rate. |
| 1million | 6million /100million /20million | ~2GB | Paid illustrative$5.60/month: $5 base +30million excess CPU-ms ×$0.02/million; within included request/D1 allowances. Requires approval. |

Excluded: specialist inference/API charges, legal/accounting, payment fees, custom domain, email, external backup storage, logs, queue/coordination services and human review. These estimates are **not** whole-business cost or guaranteed production sufficiency. No paid plan was activated. Free-tier prototyping should have hard quotas, per-tenant budgets, bounded request sizes, replay keys in durable SQL uniqueness constraints, retry/backoff and fail-closed execution. Durable state does not itself provide tenant isolation; every query and authorization path requires tests. Do not use eventually consistent cache as the execution/commission dedup authority.

## Evidence needed before deployment or real commercial operation

- Security-reviewed authentication, tenant isolation, operator roles and provider ownership verification; persistent cross-process idempotency and tested recovery.
- A specific hosting decision approved by the owner, with free-tier failure behavior and explicit spend limits; no automatic paid upgrade.
- Partner-accepted exact terms, authorized representatives and validated proof protocol. Current30-day pilot retention is insufficient for many commercial refund/dispute cycles; negotiate and implement retention before real accrual.
- A real independent task. No equivalent has been established by internal CI, package installs, synthetic events or research.
