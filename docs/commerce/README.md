# ResultGate general marketplace — 15% payment sandbox

Status: review-only branch, not deployed. Does not depend on PR #11. Existing
production MCP and discovery schedules are unchanged. No live payment switch exists.
No real provider, account, purchase, payout, message or contract was created by this change.
See SANDBOX-ACCEPTANCE.md for the new operator-only Connect test account, hosted
onboarding, cumulative refund and processor-object reconciliation workflow.

## What works

Invited tenants apply as providers and acknowledge versioned **sandbox** terms.
An operator reviews their test account/authority evidence before service listing.
Services have immutable USD prices and arbitrary bounded capability labels. Discovery
sorts exact capability matches by price and stable ID; no fabricated quality scores.
An order freezes service, provider, price, terms and 15% fee. Existing credentials
provide tenant isolation, revocation and quotas. No completion/quality field gates fees.

Owner approval binds the exact quote, amount and expiry. Alternatively an operator
records a pre-existing owner grant scoped to one service and cumulative budget. Each
order reserves budget atomically, including retries; revocation blocks new Checkout.
No agent tool can create grants, approve payments or approve providers.
**The operator must verify the account holder's authorization out of band.** A bearer
agent credential alone is deliberately insufficient. A hosted owner identity/consent UI
is not yet implemented. Revocation does not invalidate a Checkout session already
created at Stripe; expire that session in Stripe before promising cancellation.

Stripe test adapter creates a hosted one-time card Checkout Session using
`application_fee_amount` and `transfer_data[destination]`. It rejects live secrets,
checks US test account capabilities and uses a stable per-order idempotency key.
No cards or API keys enter the order store. No arbitrary payment/redirect destination
can be supplied by the requester. USD service price only; taxes, tips, discounts,
subscriptions and multiple sellers in one checkout are out of scope.

Signed raw-body webhooks establish payment. Returning from Checkout does not.
An unpaid completion produces no accrual. Payment intent and event uniqueness prevent
duplicate commissions. Unknown/out-of-order payment dependencies return retryable 503.
Refund totals are cumulative/monotonic. Disputes suspend the corresponding entitlement;
winning restores it, losing leaves it reversed. Adjustments produce balanced ledger
postings, never a second sale. Fees use integer cents, half-up rounding.

**All ledger entries are TEST entries. `real_revenue_cents` remains zero.**
The ledger tracks entitlement, not proven payout. The private Connect test operator can send sandbox refunds with
`reverse_transfer` and `refund_application_fee`. No public refund route, standalone
transfer mutation or payout mutation exists. Test application-fee/transfer/balance matching is implemented. Complete processing
cost, failed refund, dispute recovery and bank payout reconciliation remain live gates.
No proof of service completion is needed to accrue commission.

## Run safely in a separate sandbox directory

Install the reviewed branch into a virtual environment using `pip install .`.
Use the existing `resultgate.network.operator` workflow to initialize a separate
private registry and issue invitation credentials (never reuse production credentials).
Run without Stripe first:

```sh
python -m resultgate.commerce.run --directory /absolute/private/sandbox --port 8776
```

Routes (loopback only; authenticated unless noted):
- GET `/commerce`: minimal onboarding explanation, no credentials needed.
- GET `/commerce/terms`: exact terms and hash.
- POST `/commerce/providers/apply`: `name`, `terms_sha`, `authorized_signatory`.
- POST `/commerce/services`: `provider_id`, `service_id`, `title`, `capability`, `price_cents`.
- GET `/commerce/services`: ranked catalog for people or agents.
- POST `/commerce/orders`: `service_id`, `request_key`.
- GET `/commerce/orders/{order_id}`: tenant-scoped quote/status.
- POST `/commerce/orders/{order_id}/checkout`: no caller-supplied price/account.
- GET `/commerce/dashboard`: provider's orders and adjusted commission, JSON view.
- POST `/commerce/webhook`: raw Stripe signature authentication, not bearer auth.

Use `Authorization: Bearer ...` from a private environment variable. Do not place
credentials in URLs or commit them. Browser-origin API requests are currently rejected;
these are API paths, not a finished self-service browser dashboard.

Owner/reviewer CLI (local filesystem owner only):

```sh
python -m resultgate.commerce.operator --help
python -m resultgate.commerce.operator --directory /absolute/private/sandbox approve-order ORDER_ID OWNER_HASH QUOTE_SHA CAP_CENTS EXPIRY_UNIX
```

`review-provider` requires a test connected-account ID and reviewer evidence hash.
This does not claim real KYC completion or sign a live agreement. Use Stripe-hosted
onboarding and separately verify business authority/resale rights before live approval.
No identity documents should be stored in this repository.

## Independent MCP clients

Launch `python -m resultgate.commerce.mcp --directory /absolute/private/sandbox`
with `RESULTGATE_REQUESTER_TOKEN` passed privately by the host. Use a dedicated token
per tenant. Eight tools are discoverable through MCP `tools/list`; admin methods are
absent. The default stdio entry point has no Stripe transport configured. It prepares
orders but fails closed at Checkout. The local HTTP runner is the test Checkout path.
See discovery.json for explicit mode and endpoint status. Do not register these tools
as available at production `/mcp` before reviewed deployment. Registry publication,
external user adoption and third-party client certification are not claimed.

## Stripe-hosted sandbox acceptance (not yet executed)

1. Owner signs into Stripe and selects a sandbox; confirm Connect is available.
   Do not accept a live paid agreement as part of this test.
2. Create a TEST connected account through Stripe's dashboard/hosted onboarding.
   Supply test data only; finish capabilities. No real provider identity is simulated
   as if verified. Account must be US for this first limited adapter.
3. Supply `STRIPE_TEST_SECRET_KEY` and `STRIPE_TEST_WEBHOOK_SECRET` via private process
   environment, never chat or git. Start the runner with `--stripe-test` and an approved
   HTTPS `--return-origin`. No live keys are accepted.
4. Forward sandbox webhook events with Stripe CLI to local `/commerce/webhook`.
   Create an invited sandbox provider/service and approve a quote using the owner CLI.
5. Open the returned Stripe TEST Checkout URL. Use Stripe's documented test payment
   methods. Capture event/session IDs in a redacted acceptance report.
6. Confirm the signed payment creates exactly one 15% entry before any service completion.
   Trigger replay, partial/full refund and disputes in the sandbox. Reconcile actual
   Stripe test application fees/transfers against the internal ledger.
7. Restore a copied sandbox DB and replay an event to verify no duplicate accrual.

Tests today use `httpx.MockTransport`, signed fixtures and local HTTP integration.
They do not prove a transaction reached Stripe or an independent customer paid.

## Live activation: explicit human gate

Required: Stripe account eligibility for the operating entity, accepted Connect costs
and liability allocation, completed hosted KYC/capabilities, authorized provider's live
15% agreement and resale rights, customer terms/refund policy/tax treatment, verified
owner identity and consent, credential-safe hosted routes, security review, sandbox
end-to-end evidence, payment/fee/refund/dispute reconciliation, monitoring and tested
backup/rollback. Then obtain separate explicit approval for real collection and deployment.
**This implementation cannot enable live collection by changing an environment flag.**

Before any future migration take a private database backup and verify restore. Pilot
schema adds `commerce_*` tables only; never run on the production DB before review.
Rollback: stop sandbox process and restore previous code/isolated DB. Discovery and
production gateway are separate and need no restart. No automatic deploy configured.
