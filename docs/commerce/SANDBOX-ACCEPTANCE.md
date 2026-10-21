# Connect sandbox acceptance — 2026-10-21

## Evidence actually available

Operator reports the ALLUBI Yerba Mate LLC live account is **Review in progress**.
This is not verified Connect eligibility or approval. Commercial static site is public;
financial code remains an unmerged draft and is not deployed. No live keys used.

Validation: **296 tests passed**, including 12 new Connect tests and 18 existing
commerce tests. Database backup/restore followed by payment/refund replay passed.
New Connect tests use httpx.MockTransport, not Stripe's network. The tested lifecycle:

| Step | Eligible amount | Commission | Provider entitlement before costs |
|---|---:|---:|---:|
| Confirmed fixture payment | $100 | $5 | $95 |
| Refund $40 cumulatively | $60 | $3 | $57 |
| Refund $100 cumulatively | $0 | $0 | $0 |

Payment replay and refund retry do not duplicate the operation. Reconciliation checks
payment -> charge -> application fee + transfer + balance transaction bindings. It
flags webhook lag, rounding differences, missing reversals, pending/failed refunds,
ambiguous outcomes and disputes. A matched test report is NOT a bank settlement:
`settlement_confirmed=false`, `bank_payout_verified=false`, `real_revenue_cents=0`.
Original charge processor fees are recorded separately, not presented as final net
profit. Refund/dispute/Connect/payout fees still require complete reconciliation.

No usable `STRIPE_TEST_SECRET_KEY` or webhook secret is available in this workspace.
**A Stripe-hosted sandbox payment, refund and transfer have NOT been executed.**

## Run real Stripe test acceptance (no real money)

Use a separate sandbox registry and virtual environment, never the production DB.
Select a Stripe Sandbox; enable/configure Connect there, including test branding.
Do not accept live financial terms as a side effect. Only use test identity data.
Supply test secrets via a private environment or the hidden operator prompt; never
put keys in command arguments, git, email, screenshots or this conversation.

1. Follow README initialization and invited provider application. Record provider ID.
2. Run the local operator below with action `create-account PROVIDER_ID`. It creates
   one US Express TEST account, without submitting identity data or accepting terms.
   Repeated calls reuse the binding. Unknown account-creation outcomes stop after
   23 hours to avoid reusing a Stripe idempotency key beyond its retention window.
3. Run `onboarding-link PROVIDER_ID`. Open its private single-use URL only as the
   authenticated test provider. Do not publish/email/log that link. Complete Stripe's
   hosted test onboarding. Refresh an expired link through the same operator action.
   Return/cancel URLs are fixed by the operator. Returning does not approve anything.
4. Run `review-provider PROVIDER_ID EVIDENCE_SHA256` after reviewing authority and
   consent evidence. Stripe capability checks plus a separate operator review gate
   precede listing. This is test review, never a claim of real KYC or live agreement.
5. Register a $100 test service, create an order and approve its exact quote with a
   40-minute authorization using the existing owner CLI. Checkout requires at least
   30 minutes remaining and cannot expire after the owner's authorization.
6. Run the loopback commerce HTTP server with `--stripe-test`. Forward sandbox
   webhooks using Stripe CLI to `http://127.0.0.1:8776/commerce/webhook`, and configure
   the CLI-provided signing secret privately. Use a properly configured HTTPS sandbox
   return origin; the public commercial website does NOT host commerce return routes.
7. Create Checkout through authenticated POST `/commerce/orders/ORDER_ID/checkout`.
   Complete its Stripe-hosted page using Stripe's documented test card, never a real
   card. The success page is not payment proof; wait for the signed payment event.
8. Run `reconcile ORDER_ID`. It must report matched, fee 500 cents, provider 9500 cents
   before costs, and real revenue zero. Save the redacted IDs/report in private evidence.
9. Run `refund ORDER_ID 4000`, wait for refund completion and signed charge.refunded,
   then reconcile: fee 300 cents, provider 5700 cents. Repeat the same refund command:
   no second refund. Run `refund ORDER_ID 10000`: full cumulative refund, fee zero.
10. Replay signed events; verify ledger totals unchanged. Restore a private DB backup
    into a separate directory and replay again. Exercise failed/pending refunds and
    disputes without treating either as successful settlement. Test declined Checkout.

Operator syntax (all actions need these shared flags):

```sh
python -m resultgate.commerce.connect_operator --directory /absolute/private/sandbox --return-origin https://YOUR-APPROVED-SANDBOX-HOST --stripe-test create-account PROVIDER_ID
```

Replace only the final action/arguments for subsequent steps. `refund` takes the
**cumulative** target in cents, not an additional amount. The hidden prompt accepts
only `sk_test_` keys. All mutations are test-only and local-operator-only. No refund,
account approval, onboarding link or transfer tool is exposed through MCP/public HTTP.
No payouts or standalone transfer mutations exist. An ambiguous refund stops for
manual inspection; do not create a new order or refund target to bypass the stop.

## Security review performed / remaining

- Exact HTTP method/path allowlist replaces prefix-only account-path validation.
- Live secrets/responses rejected; test-only transport; fixed Stripe API host,
  bounded response sizes, TLS validation, no redirects/environment proxies.
- Approval expiry now bounds Checkout expiry. Short authorizations fail before network.
- Refund requests require a locally known signed payment plus Stripe object matching.
- Persistent idempotency journals, cumulative refund targets and ambiguous-outcome stops.
- Single-use onboarding URLs never persisted; identity/card objects not persisted.
- Provider account binding and capabilities checked; business authority is not inferred.
- Reports never assert bank settlement or real revenue; mismatch blocks acceptance.

Still required before production: independent financial/security review, actual Stripe
sandbox evidence, hosted owner/provider authentication and consent UX, full adjustment
and payout reconciliation, a recovery procedure for ambiguous operations, production
webhook replay/rotation/monitoring/runbook, verified backup restore, contractual costs,
tax and refund allocation, and explicit owner approval to deploy and collect money.
Approval of Stripe's business account alone does not satisfy these gates.

## Official references checked

- https://docs.stripe.com/connect/hosted-onboarding
- https://docs.stripe.com/api/accounts/create
- https://docs.stripe.com/api/account_links/create
- https://docs.stripe.com/connect/destination-charges
- https://docs.stripe.com/api/refunds/create

Destination charges debit the platform for Stripe fees/refunds/disputes. Application
fee refunds also require reversing the transfer. Failed refunds can require manual
fund recovery. Never equate the 5% gross commission with net profit.
