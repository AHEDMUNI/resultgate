# ResultGate: shadow billing experiment

Unreleased local experiment, 2026-10-20. No real payments, wallets, provider
accounts, outbound payment requests, or commercial deployment. The MIT local
package and its two original tools remain free and unchanged. Experiments are
excluded from the PyPI wheel. Glama is pending review, as reported by the owner.

## Decision

Test a hosted convenience service with 100 free trial units and **shadow-only**
pricing of $0.001 per completed operation ($1/1,000). This is a price hypothesis,
not demonstrated willingness to pay. An eventual $20 prepaid balance amortizes
card fees. Agent operators authorize funding once, then agents use API keys and
hard budgets without a checkout at each call. x402 could later fund a balance or
pay for larger batches; do not implement a production settlement path yet.

Managed availability, quotas and a privacy-conscious usage ledger are potential
paid value. The existing validator is cheap to self-host and does not verify
semantic truth. We have no evidence yet that hosting alone warrants payment.

| Option | Agent behavior | Main trade-off |
|---|---|---|
| Prepaid usage balance | Authorized key consumes units; stop at zero | Simple hard cap; initial operator funding; needs durable transactional ledger |
| Monthly metered billing | Key consumes units; aggregate monthly invoice | Credit exposure, billing webhooks, collection failures and subscription management |
| x402 per request | Compatible client signs approved USDC payment and retries | Wallet funding, facilitator, settlement/replay handling; costly for tiny checks |
| x402 balance top-up/batch | One settlement covers many operations | Lower fees but still requires wallet, durable ledger and refund policy |

MCP is a tool transport, not billing or payment authorization by itself. The
current MCP x402 specification signals payment-required using isError plus
structuredContent/content, payment in _meta["x402/payment"], and settlement in
_meta["x402/payment-response"]. An ordinary MCP client will not automatically pay.
This experiment does NOT claim x402 compatibility: it tests metering with no
payment protocol. No testnet transaction or signature verification was tested.

## Costs and explicit assumptions

Official sources checked 2026-10-20:
- [Coinbase CDP facilitator announcement](https://www.coinbase.com/developer-platform/discover/launches/x402facilitator-polygon): 1,000 free transactions/month, then $0.001 each; gas sponsorship described. Protocol fees and facilitator fees are different. Confirm current chain/provider contract before launch; currency conversion, withdrawal and tax are excluded.
- [Stripe pricing](https://stripe.com/pricing): US domestic cards 2.9% + $0.30; Billing pay-as-you-go 0.7% additional. These are US illustrative rates, not a quote for the owner's unknown merchant jurisdiction. Cross-border, FX, disputes, refunds and taxes can add costs. Prepaid row assumes direct one-time Payments without Billing/Invoicing; adding those products adds fees.
- [Render pricing](https://render.com/pricing): smallest listed paid web compute $7/month, Postgres $6/month; extra storage/bandwidth can apply. Not purchased or configured.
- [Render free limitations](https://render.com/docs/free): 750 instance hours/month, idle shutdown after 15 minutes, ephemeral files, free Postgres expires after 30 days. Suitable only for a disposable demo, never a real-money ledger. Without a payment method, excess usage suspends services rather than purchasing more capacity.
- [MCP x402 transport specification](https://github.com/x402-foundation/x402/blob/main/specs/transports-v2/mcp.md).
- [Bazaar MCP](https://docs.cdp.coinbase.com/api-reference/v2/rest-api/x402-facilitator/bazaar-mcp-server) supports discovering/consuming paid endpoints; listing is not evidence of paying demand.

The cheapest experiment is **local: $0 incremental cloud/payment fees**, with
existing computer resources. No LLM API calls are required. For a later small
hosted pilot, $15/month fixed operations is a planning allowance based on $7
compute + $6 database + $2 reserve, NOT a guaranteed sufficient deployment.
An additional $0.00002/call is a deliberately assumed variable reserve, not a
measured provider cost. At large scale replace it with measured CPU, database,
egress, support, observability, abuse and backup costs; $15 fixed will not
necessarily support those volumes.

Illustration at $0.001/call, all funded credits consumed in the same month:

| Calls/month | Gross | Assumed operations | x402 fee / contribution | $20 prepaid card fee / contribution | Monthly usage fee / contribution |
|---|---:|---:|---:|---:|---:|
| 100,000 | $100 | $17 | $99 / -$16 | $4.40 / $78.60 | $5.10 / $77.90 |
| 1,000,000 | $1,000 | $35 | $999 / -$34 | $44 / $921 | $51 / $914 |

Prepaid and monthly rows assume respectively 5 or 50 collections of $20.
A $1 card collection costs $0.329 (32.9%); $20 costs $0.88 (4.4%). Monthly
Billing makes a $20 collection $1.02 (5.1%). x402 at scale costs approximately
100% of a $0.001 call, but 10% of a $0.01 batch; a $1 top-up approximately 0.1%
before other expenses, assuming the paid facilitator tier. Implementing top-ups
requires confirmed settlement and no duplicate grants; it is not built here.

These are contribution scenarios, **not net profit**. Owner labor, tax,
refunds, FX and costs not yet established are excluded. Even with prepaid cards,
$20,000 monthly contribution would require roughly 21 million calls/month under
these optimistic assumptions; real net profit needs more. This is arithmetic,
not a demand forecast. Run `python -m experiments.metered.economics` to reproduce.

## Run locally

From a checkout with the project's dependencies installed:

```bash
export RESULTGATE_TRIAL_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m experiments.metered.server --http
```

POST JSON to `http://127.0.0.1:8766/v1/extraction` or `/v1/citations`, with
`Authorization: Bearer <token>`, `Content-Type: application/json`, and an opaque
`Idempotency-Key`. Payloads are the same as the free tool contracts. `/health`
reports `shadow_only` and `payments_enabled: false`. No public bind option.

For MCP, launch `python -m experiments.metered.server` with the same environment
variable. Discover `check_extraction` and `check_citations`; each accepts `payload`
and `request_id`. No token in tool arguments. This is an stdio trial adapter,
not a hosted remote MCP service. HTTP and MCP use the same service class but
separate CLI processes have separate balances; no shared durable ledger yet.

## Metering and privacy contract

- One completed tool operation consumes one trial unit, including fail/unknown
  results: detecting a problem is the service. Invalid/auth-rejected/server-error
  requests consume none. This is separate from unique-task adoption metrics.
- Same request ID + same tool/payload consumes no additional unit; changed payload
  or tool with that ID fails with 409. Lock serializes concurrent operations;
  hard cap prevents overdraft. Retry recomputes the deterministic result.
- Memory holds only keyed hashes, tool and outcome; no stored raw payload, raw
  task ID, sources or results. No telemetry export or filesystem writes. Summary
  excludes even the keyed hashes. Payload must still transit the service and
  briefly exist in memory; an eventual hosted service requires disclosure.
- All events are server-classified **internal**. No caller can label an event
  external or grant credits. No external use or money is recorded.
- Memory-only balance resets on restart. Maximum 10,000 unique operations;
  trial defaults to 100. NOT safe for real money, multi-tenant or multi-worker use.
- Future external pilot: issue distinct operator-verified pseudonymous accounts,
  consent to coarse daily counters, retain at most 30 days, exclude internal keys,
  health checks and retries, track return on different days. Accounts/wallets are
  not proof of distinct humans. Do not log sources or publicize individual use.
  Cross-day retention and verified external cohort support are NOT implemented
  in this internal experiment. Existing free local telemetry stays opt-in/local.

## Actual verification

95 tests passed on Python 3.12: original 83 plus 12 shadow tests. Actual MCP
subprocess initializes, discovers and invokes both tools, repeats calls without
extra units and rejects conflicting IDs. HTTP tests cover both tools, auth,
origin/host, strict JSON, size limit and dedup. Threaded tests cover 40 concurrent
retries and oversubscription. Injected execution failure consumes no unit.
Bandit found no issues in the experimental server/service at verification time.

Synthetic in-process run: 1,000 extraction calls, 100 records each, p50 0.201 ms,
p95 0.343 ms, total 0.235 s. This excludes network, TLS, persistent storage and
payment processing; it is NOT a hosted SLA/capacity measurement. Reproduce with
`python -m experiments.metered.benchmark`. All are internal uses.

## Commercial launch gates

Before launch: demonstrate independent repeated demand; validate price via
nonbinding opt-in; identify eligible merchant jurisdiction/payment provider;
implement durable atomic accounts/reservations/idempotency and signed webhook
reconciliation; test restart, timeout, refund and settlement failures; add HTTPS,
rate limiting, tenant isolation, retention, backups and spend caps; test a real
remote MCP integration. Obtain explicit approval before real payment activation
or any paid infrastructure. No accounts or paid services were activated here.
