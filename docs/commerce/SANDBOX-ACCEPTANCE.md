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

## Existing Express account selected by operator

The owner supplied `acct_1UT33gDkMsAxFBbN` as their existing Sandbox Express account.
Its reported pending capabilities have not yet been read through the API. Reuse it;
do not run create-account for this onboarding flow.

`scripts/stripe_sandbox_onboarding.py --account acct_1UT33gDkMsAxFBbN` has no package
dependencies, requires an interactive terminal and prompts invisibly for a Sandbox
`sk_test_` key. It makes only GET account and POST account_links requests. It never
creates accounts, changes account details, saves keys, or attempts payments. It prints
a shareable requirements/status section followed by a PRIVATE single-use link. Do not
share or capture the link. Complete the hosted flow using Stripe test data. Re-run
with `--status-only` to retrieve the actual updated requirements/capabilities.
The existing public /providers page is only an informational return/refresh destination;
regenerate expired links with the operator command. No automatic verification implied.

For subsequent ResultGate binding, the private Connect operator now supports
`adopt-account PROVIDER_ID acct_1UT33gDkMsAxFBbN`. It binds the existing API-validated
US Express test account, rejects conflicting assignments and leaves provider approval
pending. Empty Stripe metadata is permitted only for this explicit local import;
foreign provider metadata is rejected. No Stripe account mutation is needed. Then use
hosted onboarding and the separate review-provider gate as documented above.


## Private resumable acceptance runner (2026-10-21)

The operator's account-read screenshot shows the EXISTING account above has
`charges_enabled=true`, `payouts_enabled=true`, `details_submitted=true`, active
card_payments/transfers, and no pending requirements. It has `type=none` with
Express dashboard, Stripe requirement collection, and application fee/loss payer.
This supported controller combination is now accepted; no new account or repeat
onboarding is required. This screenshot is account readiness, NOT payment evidence.

`scripts/stripe_sandbox_acceptance.py --exec-session` orchestrates ONE actual
Stripe-hosted $100 test Checkout, waits for Stripe CLI-forwarded signed events,
reconciles $5 commission/$95 provider before costs, refunds $40, then the remaining
$60 (cumulative $100), and reconciles $3/$57 then $0/$0. It replays each actual signed
event through the ledger to check duplicate handling. No synthetic event is generated
by the runner, and success pages are not treated as payment confirmation.

Run via `exec /opt/resultgate/venv/bin/python` in the helper checkout: it imports the
reviewed source explicitly and only READS existing runtime dependencies. It does not
install into or change production Python, Nginx, systemd, MCP or any public route.
It binds only 127.0.0.1:18776, not the MCP port. Return/cancel go to the existing public
homepage and have no authority to change transaction state.

The runner downloads official Stripe CLI 1.54.1 into the operator's private state and
checks the archive SHA256 from the release asset metadata:
`59ac00af3ca11a02f76232642d6d534c5c0e9e433889b86006f5046d33baf657`.
It fails before requesting a key if download/integrity/dependencies/port checks fail.
No sudo, purchases or public ingress are needed. Only Linux x86_64 is supported.

Input uses the already PTY-tested no-echo /dev/tty reader. Echo remains disabled
throughout the run, and queued input is flushed before restoring terminal settings.
No Stripe key is written to disk or shell argv/history. Stripe CLI receives the test
key via its child-only environment, with stdin disabled and isolated ephemeral HOME/
config. Same-UID processes and root can inspect process environments: run only under
the trusted operator account. CLI raw output/signing secret are captured in memory,
never printed or saved. Checkout URLs are private and must not be screenshotted.

State and the isolated registry live under
`~/.local/state/resultgate-stripe-sandbox-acceptance`, mode 0700 (files 0600 via umask).
The private run state contains LOCAL sandbox buyer/seller credentials, never a Stripe
API key or webhook signing secret. Report JSON contains test object IDs, amounts,
ledger totals, event signature/replay evidence and refund IDs. Never copy run.json,
registry identity.key or the sessions table into a report. A process lock prevents
concurrent runs. Completed runs print their saved report without new mutations.

On interruption, preserve that exact directory and rerun the SAME command. It reuses
the same order, Checkout and cumulative refund journal. Unknown refund outcomes stop
for manual Stripe inspection, not a new refund/order. Expired unpaid Checkout also
requires review; do not delete state to bypass the gate. Reports never claim bank
settlement, net profit or real revenue. A match requires actual Stripe object amounts
and locally balanced ledger postings at all three stages.

New runner boundary tests are necessary code verification, not Stripe transaction
proof. Actual cs_test_/pi_/ch_/fee_/tr_/re_/evt_ IDs remain pending until the operator
runs this on the authorized server and completes the hosted test-card Checkout.

Sources: official stripe/stripe-cli v1.54.1 release asset digest and source config
(`STRIPE_API_KEY`, `STRIPE_DEVICE_NAME`); Stripe Accounts object controller/type docs;
Stripe destination charges and proportional application-fee refund documentation.


## Checkout compatibility fix — 2026-10-21

Owner supplied Workbench HTTP400 invalid_request_error for API version
2026-09-30.endive: payment_method_types is no longer supported in Checkout Session
creation. Removed the field entirely from the payload; Dashboard-managed dynamic
payment methods are used. $100 amount, application_fee_amount=500, current existing
connected account and order reference are unchanged. No replacement random key/order
is created. Validation failures do not start endpoint execution and therefore are not
saved in Stripe's idempotency cache (official API idempotency docs).

A durable Checkout journal now freezes payload digest, original creation time and
response state before POST, retains rg-test-ORDER_ID, blocks changed parameters and
stops retries beyond 23 hours instead of risking a pruned Stripe key. Existing bound
sessions are reused. The owner-verified earlier validation rejection predates this
journal; the corrected first attempt records the current payload before network I/O.
No expired owner authorization is renewed automatically. Asynchronous success events
are also forwarded and verified; unpaid completion events do not accrue commission.

New regression coverage asserts the obsolete parameter is absent from the actual
form request and checks $100/500-cent fee/destination, stable keys after timeout and
HTTP400, changed-payload rejection and aged retry refusal. These remain code tests;
actual Checkout IDs and signed paid/refund evidence must come from the server run.

## Confirmed rejection recovery

A subsequent operator screenshot established HTTP400 idempotency_error after removing
payment_method_types. The initial rejected request's parameter set conflicts with the
original key. Do not repeatedly edit the payload, delete the run, or choose random keys.

The private runner accepts --repair-dynamic-methods-rejection ONLY for this owner-
confirmed deprecated-field rejection. It requires a persisted HTTP400 attempt and no
local session/payment, then audits every Stripe Sandbox Checkout since before the
original order creation. Pagination is bounded at 20 pages; malformed/truncated/live
results fail closed. ANY session with the original client reference or metadata order
ID blocks the replacement. A network failure is not treated as evidence of absence.

Only a successful complete no-match audit records a permanent repair journal with the
original digest/key/status, scan lower bound/count and timestamp. The replacement key
is deterministic: rg-test-dynamic-v1-ORIGINAL_ORDER_ID. Subsequent runs reuse it with
frozen parameters and the same 23-hour retention guard. No second order is generated.
The current owner's request to retry the same $100 Sandbox acceptance permits renewing
an approval only within the ORIGINAL order lifetime after that audit; price, fee,
provider account, quote and original order ID remain unchanged. An order with less
than 30 minutes left stops for explicit review. No financial production deployment.

Focused validation after recovery change: 43 tests (25 commerce, 14 Connect, 4 runner).
Added checks for a single deterministic repair, refusal when an existing Stripe
session is found, refusal for unknown outcomes and refusal of incomplete pagination.
Actual repaired Checkout and payment evidence still await the authorized server run.

## First signed paid event observed; reconciliation not yet complete

The operator screenshot shows the reused Checkout produced a signature-verified
checkout.session.completed event and reached the paid reconciliation stage. The
trace passed payment binding checks, then failed validating charge.application_fee
as an object ID. This is paid Sandbox evidence, not a completed $5 fee/transfer or
refund reconciliation. No refund stage was reached in that run.

Support expanded references and resolve absent fee references through the official
GET application_fees?charge=CHARGE_ID&limit=100 endpoint. Require exactly one fee
bound to the platform charge/originating transaction and selected connected account,
then retrieve and validate the test fee itself. Missing fees are pending, not assumed
collected; retry only missing-reference cases read-only for a bounded interval.
All original amount/currency/fee/transfer/refund/ledger checks remain mandatory.
Added tests cover missing references, empty/pending fee lookup and destination fee
origin binding. Focused verification: 17 Connect + 4 runner tests passed.
Resume the existing directory/order/payment; never request a second Checkout payment.
