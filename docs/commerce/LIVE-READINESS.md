# Stripe Connect live readiness — human gate

Updated 2026-10-21 after owner reported completion of company/identity details for ALLUBI Yerba Mate LLC. This is owner-reported progress, not a verified Stripe approval. Do not infer account eligibility or live charge permission.

## Separation
- Commercial website may be published separately; it does not enable payments.
- PR #12 remains test-only. `sk_live_` and live webhook events remain rejected.
- Do not reuse ALLUBI Shopify payment configuration or credentials.
- Do not press Agree and submit on the owner's behalf or accept financial terms.

## Before requesting final authorization
1. Owner completes Stripe onboarding and reviews charges, Connect model, liability and restrictions.
2. Confirm approved platform/account identity privately; no account secrets in code or chat.
3. Complete a genuine Stripe Sandbox Checkout, signed webhook, replay, refund and dispute round trip; reconcile application fee and destination transfer.
4. Review provider identity/contracting authority, accepted 5% terms and right to offer services. No service-completion condition on fee entitlement.
5. Complete hosted owner consent identity, price/terms binding, grant limits, session cancellation and immutable payment/order mapping.
6. Complete ledger reconciliation for processing costs, refunds, application-fee reversals, failed refunds, disputes and transfers. Do not mark payout confirmed merely on Checkout success.
7. Review live adapter separately: platform and connected account allowlists, secrets outside git, live/test data separation, signature/version validation, kill switch, alerts, backup/restore, rollback and concurrency tests.
8. Present final deployment diff, tested rollback and actual fee schedule to owner for explicit production collection approval.

## Required evidence before enabling
Stripe sandbox acceptance report; reviewed provider agreement; reviewed privacy/refund/fulfillment text consistent with public website; security review results; account eligibility/capabilities; documented processor cost allocation; explicit owner approval for live collection and deployment.

No live adapter or live toggle is introduced by this document. Existing test-mode code remains the safety boundary. Readiness must not be reported as completed until the above evidence exists.
