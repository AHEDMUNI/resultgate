> Historical 5% acceptance evidence, retained unchanged below. New orders now require 15% terms v2; this record does not prove a hosted 15% payment.

# Stripe Sandbox acceptance evidence — 2026-10-21

## Provenance and scope

Operator-supplied screenshots of the authorized DigitalOcean server run at commit
`1a561afe27d62116e681ce15057c842174384aa7`. This document records the displayed
report; the reviewer did not independently query Stripe from this workspace.
No live keys, real payments, bank payouts or commercial revenue are evidenced.
Financial code remains a draft, without a production financial deployment.

- Existing connected account: `acct_1UT33gDkMsAxFBbN` (reused, no duplicate).
- Original order: `221cd119a961589f91a51d188b54d1b4` (resumed after repair).
- Mode: `test`.

| Stage | Payment | Cumulative refunded | Net commission | Provider before costs | Matched |
|---|---:|---:|---:|---:|---|
| Paid | $100.00 | $0.00 | $5.00 | $95.00 | true |
| Partial refund | $100.00 | $40.00 | $3.00 | $57.00 | true |
| Full refund | $100.00 | $100.00 | $0.00 | $0.00 | true |

The second refund returned the remaining $60, rather than another $100.
Both refund results displayed `succeeded`; all stages displayed `findings: []`.
Ledger postings matched: (10000, -9500, -500), then (6000, -5700, -300),
then (0, 0, 0) cents across clearing, provider entitlement and commission.

## Signed events and duplicate protection

One `checkout.session.completed` and two `charge.refunded` events displayed
`signature_verified: true` and `duplicate_replay_verified: true`.
The completed program reached its normal close-session prompt.

Exact Stripe object/event identifiers are in the server's private safe report:
`~/.local/state/resultgate-stripe-sandbox-acceptance/report.json`.
Do not reconstruct ambiguous object IDs from screenshot glyphs. Do not publish the
Checkout URL, keys, signing secret, registry or run.json credentials.

## Financial limits

The original charge processing fee displayed $3.20 separately. Provider amounts
above are before costs; the 5% gross fee is not net profit. Balance status remained
`pending`; `bank_payout_verified` and `settlement_confirmed` remained false.
`real_revenue_cents` remained 0. Refunds reduced the test commission to zero.
This acceptance establishes test object/ledger matching, not bank settlement,
production readiness, a provider contract, a customer sale or recurring income.

## Release gates still open

Independent financial/security review; production owner/provider authentication
and consent UX; verified provider authority and agreed 5% terms, costs and
refund/dispute allocation; production webhook and recovery/monitoring/backup/rollback
review; Stripe live eligibility; explicit owner approval before live deployment,
keys or collection. Do not rerun Checkout or create another order for this evidence.
