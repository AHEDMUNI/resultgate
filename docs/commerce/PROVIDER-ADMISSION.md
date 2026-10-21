# Private provider admission — 15%

The operator-only ProviderAdmission store is preparation, not a public onboarding endpoint or payment gate wired into production. It never creates Stripe accounts, makes network requests, signs an agreement, proves identity, publishes listings or enables Checkout. No provider has been admitted.

Before recording a live offer, the reviewer must privately obtain and verify:
- A signed 15% agreement accepting the current POLICY_SHA and exact commercial terms.
- Identity and authority of the actual signatory; service ownership or explicit marketplace rights.
- The provider-owned Live connected account, separately from any Sandbox account.
- A service version, fixed USD price, scope, delivery, refund and support terms.
- Explicit processing-cost allocation, settlement timing, reserves and dispute liability.

Only evidence digests and opaque identifiers enter this store. Original agreements and documents remain in a restricted evidence repository, never public GitHub issues. A hash is a reference, not proof; the operator must review originals. Use an operator-only database with permissions and backups. Do not expose record/revoke through MCP or unauthenticated HTTP. A modified or expired record is rejected; revocation persists through repeated insertion. A changed service, price, account or terms requires a separately accepted and reviewed record. Reviews expire within 30 days.

The future production checkout must check the exact admission digest and offer binding on each request, current Stripe capabilities, verified customer identity and consent, and the global production gates. This helper has no live adapter and is not sufficient to activate payments.

Validation: seven isolated tests cover missing evidence, wrong rate, price/account binding, time bounds, replay after revocation, record tampering and extra sensitive-data fields. No real provider agreement or Stripe transaction was created.
