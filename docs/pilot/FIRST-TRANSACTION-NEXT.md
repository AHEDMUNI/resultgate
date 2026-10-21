# First transaction: partner and hosting decision

Reviewed October 20, 2026 (America/Chicago). Research only; no outreach, enrollment,
agreement, paid task, server or payment was activated. The owner reports that the
Firecrawl inquiry has already been sent. Do not resend it or infer acceptance.

## Commercial decision

Firecrawl Standard remains the first active prospect, with its pending answer as
the next commercial evidence. API integration and account provisioning do not
establish commission rights. The owner's message asks for the right questions;
wait for explicit terms, identity/authority and conversion evidence before enabling
any commercial claim. ResultGate still has zero verified commercial partners.

A newly checked fallback is **BrowserAct**, with more concrete published referral
economics than Andru. **Andru** remains the closer direct specialist-agent fit,
but fails our current paid-customer/commission evidence gate. Neither qualifies
as an approved partner or a reason to run another test now.

| Candidate | Verified public fact | Missing evidence and decision |
|---|---|---|
| BrowserAct | Public affiliate program; published cloud Bots can be invoked through API/MCP | Machine-origin attribution, direct contract and authenticated financial evidence unconfirmed. Cloud workflows are not proof of an independently reasoning agent. Candidate commercial inquiry only. |
| Andru | Account-bound MCP/A2A task execution, priced outputs and named creator | No commission program/offer or independently verified paying-customer evidence found. Prioritize only if operator can supply these and accept a small direct deal. |
| Browser Use | ResultGate has one actual delegated-task proof; vendor publishes customer case studies | No public commission rate or partner acceptance found. Customer stories prove claimed deployment, not accessible payment evidence. Reuse existing technical proof; no new credit spend. |

### BrowserAct terms we can actually state

The [official affiliate page](https://www.browseract.com/affiliate) advertises 30%
on the first qualified order and 20% for subsequent purchases during six months.
Attribution is last valid referral-link click before signup. Qualifying categories
include subscriptions, renewals, credit purchases and upgrades. Confirmed earnings
must reach $50; monthly payments are described as processed by the following
month's 15th after validation. Refunds/reversals/disputes cancel or offset commissions.
The payment rail and a signed conversion feed were not established. Thus the first
accrued dollar is not necessarily the first collectible payment.

[Integration documentation](https://www.browseract.com/integrations) distinguishes
cloud Bots invoked via MCP from local Agent CLI browser control. Result callbacks
are task evidence, not payment evidence. [General terms](https://www.browseract.com/terms-of-service)
identify Hongkong Ziniao Technology Co., Limited and describe restrictions on
commercial uses outside permitted scope; get written confirmation for brokerage.
A listed price and program claims do not verify a particular customer's payment.
No enrollment occurred.

### Andru: direct specialist agreement questions

[Pricing](https://andru-ai.com/pricing) lists $3/$12/$49 outputs and MCP/A2A use.
[API documentation](https://andru-ai.com/docs/api) documents account-bound keys,
task/status/cancel and usage/quota endpoints. [About](https://andru-ai.com/about)
names Brandon Geter and Humus & Shore. These are provider assertions, not an
identity check or proof of commercial traction. No public case found established
that a particular customer paid for an agent task.

[Terms](https://andru-ai.com/terms) describe $25 automatic wallet top-ups after
saving a card and error-charge refund requests within 30 days. Do not save a card.
Do not assume all $3 catalog assets qualify for free calls: the more detailed
[MCP guide](https://andru-ai.com/docs/mcp) excludes catalog assets, consultations
and Deal Prep from that allowance. No account, key or task was created here.

Before allocating integration effort, require: contracting identity; evidence of
an existing paid workflow (redacted provider invoice/settlement, not a testimonial);
an agreed percentage/fixed amount and base; authorization for AI-origin referrals;
server-side referral attribution; signed paid/accepted/refunded/disputed events;
maturity and payout minimum/rail; and customer permission boundaries.

## Draft second-provider inquiry — NOT SENT

Candidate recipient: geter@andru-ai.com, published in Andru's support/terms pages.
Reverify recipient before any eventual send. Owner approval is required.

Subject: ResultGate — one verified agent task and direct outcome-based commission

Hello Brandon,

I am AHED MUNI, building ResultGate, an open-source broker for owner-authorized AI
agents. We have completed one internal external-agent browser task with independent
result checks; we do not yet have verified independent customers or revenue.

Your MCP/A2A task interfaces appear relevant. Would you consider a small direct
agreement where a customer pays Andru, their agent requests one clearly scoped
specialist task, and ResultGate earns a commission only after payment, successful
work and customer acceptance? We would not charge for listing or send private data
without permission.

Before integration, could you confirm your contracting entity, a currently used
paid workflow suitable for predefined output checks, the proposed rate/base,
AI-origin referral attribution, and whether signed payment/result/refund events or
a settlement export are available? Please also specify payout minimum, timing,
method, disputes and refund maturity. A redacted example of the commercial event
sequence would help; no customer personal data is needed.

This is an inquiry, not acceptance of terms or authorization to charge. If there
is a fit, please provide a draft agreement and a no-charge integration route for
review. Repository: https://github.com/AHEDMUNI/resultgate

AHED MUNI

## Smallest host: budget proposal, not a purchase instruction

A bundled DigitalOcean Basic **1 GiB / 1 vCPU / 25 GiB disk** is $6/month with
1,000 GiB monthly outbound allowance. Percentage-based weekly backups add 20%,
so **$7.20/month before tax and overages** is the proposed base. Included disk
means no separate volume is required initially. No paid load balancer, managed DB,
object store, domain purchase or hosted agent execution is included.

Inbound bandwidth is free; extra outbound costs $0.01/GiB. Allowance accrues with
runtime and is pooled per team: a short pilot does not receive a full month's
allowance immediately. Snapshots/extra volumes and off-host exports may add cost.
Do not substitute newer configurable v5 pricing: its billing differs from this
bundled SKU. An account-specific region/checkout quote and tax are still required.

Controls before approval: fixed one instance/no autoscaling; provider execution
and payments disabled; restricted egress; application quotas; log/storage rotation;
billing alerts plus an agreed end date; destroy the VM to stop compute billing,
then inspect remaining volumes/snapshots/addresses. Powering off alone is billed.
Alerts are not a hard spending cap. The maximum all-in loss is not established
until exact account options and deletion procedure are reviewed.

### Capacity and what the money buys

Do not turn a RAM price into an operations-per-second claim. No DigitalOcean host
has been purchased or benchmarked. The initial **policy target**, not a capacity
measurement, is 10 enrolled requesters, 100 tasks/day total and 10,000 HTTP requests/day.
At an assumed 10 KiB average response this is about 2.9 GiB/month of response
payload, before headers, TLS, logs and backups. It is a planning calculation,
not proof the CPU/database meets latency or reliability targets. Provider agent
execution cost is separate and remains disabled.

Acceptance before opening ingress: load test the exact artifact under a 1 GiB
limit; measure peak RSS, p50/p95 latency, lock errors and file growth; sustain the
policy target with zero duplicate task dispatch; restore a private snapshot;
reconcile uncertain tasks before enabling dispatch; verify token revocation,
tenant isolation, request limits, TLS and backup access. A single host has a
single failure domain and no high-availability promise.

The host would buy a shared catalog and durable authenticated task records, not
customers, partner permission, full A2A support or guaranteed agent performance.
Today the local gateway must remain loopback-only; a reviewed public ingress and
credential onboarding are still missing. Do not buy until these gates are met.

## Sources

- https://www.browseract.com/affiliate
- https://www.browseract.com/integrations
- https://www.browseract.com/terms-of-service
- https://andru-ai.com/pricing
- https://andru-ai.com/docs/api
- https://andru-ai.com/docs/mcp
- https://andru-ai.com/about
- https://andru-ai.com/terms
- https://browser-use.com/case-studies
- https://www.digitalocean.com/pricing/droplets
- https://docs.digitalocean.com/products/backups/details/pricing/
- https://docs.digitalocean.com/platform/billing/bandwidth/
- https://docs.digitalocean.com/products/droplets/details/pricing/
