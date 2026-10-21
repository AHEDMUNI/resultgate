# Local commission review and future settlement operations

This addition supplies a read-only local dashboard for the **network receipt ledger**, not a hosted billing service. It does not create invoices, debts, payment requests or transactions. The existing delegation commission experiment is a separate ledger and is deliberately not summed into this report, avoiding accidental double counting of the same underlying task across experiments.

## Generate a private report

After the local Registry/Receipts ledger has been initialized through the existing pilot workflow:

```sh
python -m resultgate.network.reporting --directory /PRIVATE/REGISTRY --consent-export
python -m resultgate.network.reporting --directory /PRIVATE/REGISTRY --consent-export --format html --output /PRIVATE/commission-review.html
```

Open the HTML file locally. No web server, JavaScript, remote assets or outbound requests are used. Output files are new-only with 0600 permissions; existing files/symlinks are not overwritten. Stdout export is explicit and must not be pasted into public issues without review. Missing stores are refused, not created.

The report reads a consistent SQLite read-only snapshot and performs no schema initialization, retention deletion, commission assessment or state transition. It excludes records older than 30 days without deleting them. No provider names, endpoints, customer/task IDs, agreement text, tokens, evidence hashes or raw content are exported. Only aggregates are presented.

Cohorts are separate: internal simulation, external unverified, and independent-use evidence **attested by the local operator**. Recorded routed/completed/verified/commission_eligible/failed/cancelled/refunded/disputed states are shown separately. A verified result is not a commission until assessment occurs.

Previously recorded eligibility is rechecked against current provider approval, accepted/approved exact agreement, expiry, success/acceptance/independence evidence, mode, agreed economics and recorded amount. Revoked/expired/changed agreements do not remain in the currently-eligible amount. The historical state is retained, with a separate blocked count/reason. Refunded/disputed/cancelled entries are excluded. All money values are integer microUSD, explicitly **not collected revenue or legal amounts due**. Operator-controlled database records can be falsified by the filesystem owner; this report is not independent audit proof.

## Direct agreement evidence bundle (not executed)

For each prospective provider, customize the existing AGREEMENT-DRAFT.md worksheet. Before enabling any real eligibility, retain outside the minimal-data database:

1. Authorized legal/business identities and authority to accept terms; separately verified domain/account control. Domain challenge alone is insufficient authority.
2. Exact full terms and immutable content hash, structured outcome type/amount/currency, allowed machine-origin referrals, scope/endpoints, validity window, exclusions, refund maturity and dispute handling.
3. Explicit acceptance by **both** authorized parties of that exact version, time and authority reference. A provider registration or an operator's unilateral checkbox is not bilateral consent. Prefer provider-controlled authenticated acceptance or an independently verifiable signature; store only minimal references locally.
4. Attribution contract: unique ResultGate referral ID bound to provider-issued customer/transaction/subscription reference. No secrets/customer details in public issues. One outcome per referral in current pilot; subscription renewals require separate design and explicit agreement.
5. Authoritative success/paid-event evidence and customer acceptance. Provider signature authenticates origin, not truthful success; reconcile against provider account/settlement records. A 200 response, free plan signup, page click or test account does not establish a paid conversion.

No candidate provider has accepted this bundle, and no actual terms were signed or accepted during development. Current local attestation APIs are an engineering prototype, not proof that the bundle exists.

## Provider integration gates

A real partner adapter must bind verification keys to a reviewed provider configuration outside incoming request data. Verify the provider's **actual** documented signature algorithm over raw bytes, timestamp tolerance, key rotation and replay IDs. The generic HMAC contract in receipts.py is not claimed compatible with any partner. Never accept a key from the webhook payload or trust a self-declared provider ID. Signed events may arrive duplicated or out of order; unknown/missing references must go into reconciliation, not automatic entitlement.

Fetch or import authoritative settlement records only through an authorized provider account/interface. Match immutable provider transaction IDs, referral attribution, amount/currency, actual settled status and reversals; quarantine discrepancies. Reconcile refund/chargeback events even after a prior success. Do not issue a commission solely because the local task result passed verification. Current USD-only and bounded retention constraints require a durable commercial retention/reconciliation design before production; never allow expired dedup tombstones to cause re-attribution.

## Future settlement operation (disabled)

Proposed review flow: received evidence -> verified attribution -> accepted successful outcome -> refund maturity hold -> reconciled eligible statement -> owner/provider review -> separately authorized settlement. Failures, disputes and refunds stop or reverse eligibility. Keep simulations entirely outside financial statements. Version every rule; retain independent audit records with access controls and a deletion/retention policy agreed with the parties.

Before any future invoice, legal debt assertion or collection: owner approval, complete reviewed contract, authentic accepted outcome/settlement evidence, correct tax/currency/accounting treatment, authorized payment destination and explicit payment authorization are required. This change contains none of those payment actions and does not calculate an amount due. Current dashboard supports reviewing the evidence pipeline while those external prerequisites remain unresolved.

## Verification

15 focused tests cover simulation separation, verified-vs-assessed distinction, reversal exclusion, stale eligibility after suspension/terms change/expiry, amount mismatch, read-only retention behavior, minimal output, HTML escaping, private exclusive file creation, missing-store refusal, explicit CLI export consent, external-unverified success and signed duplicate receipt/assessment counted once. Bandit on the new reporting module returned no findings. All fixture agreements and events are simulations; no revenue or independent use was generated.
