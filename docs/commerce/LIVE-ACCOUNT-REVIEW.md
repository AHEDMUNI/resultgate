# Production readiness — 2026-10-21

Status: NOT ready for live collection. The owner authorized preparation and account
review, but requires a separate final confirmation before real Checkout opens.
No live key or API call, financial deployment, contract acceptance or expenditure
has been made in this preparation step. Existing Sandbox acceptance is retained.

## Read-only account inspection added

`python -m resultgate.commerce.account_readiness --key-file PRIVATE_PATH`
reads the platform account. An optional `--account-id` reads an existing live
connected account. The existing Sandbox Express account must not be assumed to
exist in Live or reused as a verified live seller.

The helper accepts only a restricted live key already securely provisioned with
Accounts read permission; it cannot establish the key's configured permissions
from its prefix. Do not create/provision one until the operator reviews the file
location and permissions. Prefer authenticated Dashboard review first. No key
is accepted via stdin, environment or command arguments. Only the file path is
passed. The file must be owned by the process user, owner-only, regular, not a
symlink or hard-linked file, under an operator-controlled private directory.
No key provisioning command is provided and no existing secret is read by tests.

Only fixed Stripe account GET endpoints are implemented; redirects and environment
proxies are disabled. Output contains booleans, capability states, requirement
counts and allowlisted fee/liability settings. It excludes identity documents,
addresses, emails, bank information, raw API errors and secrets. Missing fields
stay unknown. Account flags alone never confirm Connect eligibility, merchant
contract approval or permission to take money. This is an inspection utility,
not a live payments adapter. Eight isolated boundary tests pass; no repeated
hosted payment/refund test was performed.

## Cost decision before activation

Official sources checked on 2026-10-21:
- https://stripe.com/pricing — US domestic card standard rate 2.9% + $0.30.
- https://stripe.com/connect/pricing — when the platform handles pricing,
  $2 per monthly active connected account and 0.25% + $0.25 per payout;
  an active account is one receiving a bank/debit-card payout that month.
- https://docs.stripe.com/connect/destination-charges — destination-charge
  processing fees, refunds and chargebacks debit the platform balance.

At the standard domestic card rate, a $100 destination charge with a $5 application
fee leaves $1.80 before Connect fees, hosting, refunds, disputes and taxes.
This is illustrative arithmetic, not verified account-specific pricing or profit.
The 95% provider entitlement is before agreed costs; automatically taking an extra
processing fee from the provider is NOT authorized. Fixed costs can make a first
small transaction unprofitable. The owner and provider must agree cost allocation,
loss responsibility, settlement timing and tax treatment before activation.
Do not silently change from destination charges to direct charges: that changes
the tested flow and the risk allocation and needs separate review.

## Remaining implementation/review boundaries

The current commerce engine, hosted onboarding operator, webhook route and ledger
are test-only. No live-key switch is added. Production still needs:

1. Authenticated owner/provider sessions and step-up confirmation bound to an
   immutable quote, amount, currency, merchant, expiry and revocable delegation.
   A tenant bearer token or Stripe customer email is not proof of owner consent.
2. A genuine provider: verified service control and contracting authority, explicit
   marketplace rights, signed 5% agreement, price/scope/support/refund terms and
   live connected-account binding. A provider application is not acceptance.
3. Separately reviewed live adapter and private production storage; durable signed
   webhook ingestion, bounded retries and operational alerting. Never interpret
   return-page navigation as successful payment or replay a financially ambiguous
   operation under a new idempotency key.
4. Production refunds, dispute recovery, fees and payout reconciliation, including
   pending/failed payouts; a transfer is not bank settlement. Backup/restore and
   rollback validation for the financial store are required before deployment.
5. Independent security/financial review and final owner authorization. The
   existing manifest is review evidence, not an enforcement mechanism.

Glama submission requires an authenticated session. The public notice must say
prelaunch/simulation and voluntary provider applications; there are no verified
commercial sellers or live offers at this checkpoint. No external submission is
claimed without a Glama confirmation.
