# Settlement sandbox: no money, no invoices

`resultgate.network.settlement.SettlementSandbox` is a local operator-only
accounting experiment built on the existing simulation Market. It makes no
network requests and contains no Stripe, wallet, x402 or payment credentials.
It must not be exposed through MCP or the gateway.

Only a simulated task in `commission_eligible` with a still-approved provider and
unchanged separately accepted agreement can create entries. The existing task
state machine requires prior matching, offer, data-send acceptance, delegation,
completion, verification and a simulated transaction identity. None of these
simulation records is proof of an actual paid transaction.

```python
from resultgate.network.settlement import SettlementSandbox

# market is the operator's existing local Market, task_id an eligible simulation.
ledger = SettlementSandbox(market)
ledger.accrue(task_id, route="direct")
report = ledger.report()
assert report["balanced"] and not report["real_debt_created"]
```

For a separate fixture, `route="marketplace", fee_micros=300000` models a
$0.30 fee deducted from the provider's share. Fees are explicit hypothetical
inputs, not live processor quotations. USD amounts are integer microdollars.
The direct route models only a commission receivable/income pair. Marketplace
models customer clearing, provider share, commission and processor fee. Entries
balance to zero. No charge, payout, withdrawal, invoice or debt is created.

Replay with identical economics is a no-op; changed economics for the same task
are rejected. SQLite `BEGIN IMMEDIATE` plus the task/kind unique key provides
single-database atomicity. A reviewed refunded/disputed/failed/cancelled state
permits one exact compensating entry; repeated reversal adds nothing. History is
retained. Changed agreements, suspension or deletion are flagged for review in
the report, never silently treated as current entitlement. This is not a
tamper-proof ledger against its filesystem-owning administrator.

The full-reversal fixture also reverses the hypothetical processor allocation;
actual processors may retain fees. Partial refunds, nonrefundable fee expenses,
taxes, FX, reconciliation of external statements and real settlement remain
unimplemented. Such events must block live use until provider-specific rules
and evidence are integrated. An expired/deleted task cannot be reversed through
this API; it remains flagged for operator review until sandbox retention purge.
Explicit `ledger.purge()` removes entries after 30 days measured from accrual.
This is a sandbox privacy policy, not a suitable real accounting retention rule.

Run the free tests from the source checkout:

```sh
python -m unittest discover -s tests -p test_settlement.py -v
```

These cover direct and marketplace allocations, duplicate/conflicting events,
invalid fees, missing eligibility, revoked agreements, reversals and retention.
No payment-provider sandbox was contacted. Actual Stripe test mode requires a
separately supplied test account/key; x402 testnet requires an approved wallet
setup. Neither is needed for the first provider agreement inquiry.
