# Shared-market foundation: local simulation, not a deployed market

`resultgate.network.market` adds a reusable durable transaction journey on the existing reviewed provider Registry. It does not expose a new MCP tool, run an HTTP listener, send a task, hold a credential for an external service, spend money, or establish commercial entitlement. Every record has `mode: simulation`, `external_dispatch: false`, `payments_enabled: false` and `actual_commission_micros: 0`. This is deliberately not connected to the real receipt/commission ledger.

## What works now

A trusted local operator initializes `Registry(private_directory)` once, then creates `Market(registry)` and `MarketOperator(market)`. Other processes on the same protected persistent filesystem can open that initialized registry. A two-process test verifies one request ID creates exactly one task. `BEGIN IMMEDIATE` and a unique tenant/request constraint serialize mutations; SQLite timeout fails closed. This does not deduplicate across different files, replicas, servers or installations.

The existing provider application, ownership review and separately accepted commission terms are reused; no new parallel provider catalog. `MarketOperator.issue_credential(opaque_tenant_id)` issues a requester token. `issue_credential(opaque_owner_id, 'provider', approved_provider_id)` issues a provider token only after review. Returned tokens are secrets shown once; only keyed hashes are stored. Registry management tokens cannot be used as market credentials. `MarketOperator` is trusted local code and must NEVER be exposed directly as an HTTP/MCP surface. Anyone with the local OS/database access remains trusted; this is not a security boundary against the local operator.

Requester tokens see their own tenant's tasks only. Provider tokens see only tasks assigned to their reviewed provider, across requesting tenants as necessary to perform the assignment. Credentials expire after30days and can be revoked. No self-registration can mint credentials or operator privilege. At most1000 credentials,1000 tasks per tenant and10000 tasks total are admitted for this local pilot.

## Protocol exercised by tests

1. `market.create(requester_token, request_id, task_sha256, success_criteria_sha256)` records a content-free `discovered` simulation. The task/criteria commitments are fixed before matching. Reusing tenant/request ID with a changed commitment fails; exact retry returns the original task.
2. `operator.match(task_id, approved_provider_id, event_id)` binds the provider and accepted agreement hash once. Matching is explicit operator selection, not an implemented ranking engine.
3. Provider `market.advance(..., 'offered', evidence_sha256=offer_hash)` commits the offer. The price is zero actual cost; paid quotes are unsupported. Offers cannot be replaced after acceptance.
4. Requester `market.advance(..., 'accepted', consent_to_send=True, max_cost_micros=0)` records explicit data-send consent. Nonzero cost is rejected, not authorized. Nothing is actually sent. Provider views also hide task/criteria commitments until this acceptance; a future transport must never send task content during matching.
5. Operator records `delegated`; assigned provider records `executing` then `completed` with a result commitment. These are simulated records, not claimed execution evidence.
6. Operator records `verified` with a verification commitment. This does not semantically verify arbitrary outputs; production adapters must evaluate the preregistered criteria.
7. Provider records `transaction_proven` with a positive **simulated** transaction value, evidence commitment and separate `simulated_transaction_id_sha256` commitment to a canonical provider transaction identifier. Changing the receipt/evidence hash cannot attribute the same transaction identity twice. This is not a signed provider payment proof. A public requester cannot perform this transition.
8. Operator records `commission_eligible` only if the same separately accepted and operator-approved Registry agreement still applies. The agreed fixed amount or basis-point rule calculates `simulated_commission_micros`; actual commission stays0.

Requester/provider can cancel before completion. Provider/operator can record failure. Operator-reviewed refund or dispute after completion clears the simulated commission and blocks revival. Completed work cannot be disguised as a pre-execution cancellation. Provider/canonical transaction-identity commitments have a separate unique attribution table, surviving task deletion until30day purge. A simulated transaction identity commitment cannot credit two tasks from the same provider. This conservative fixture contract is not a real partner transaction ID verifier. Event IDs are hashed and unique per task; exact retries do not duplicate transitions or commissions, conflicting retries fail. Terminal outcomes need a separate reviewed reconciliation process, which is not implemented.

No raw task, offer, result, user name or API key belongs in this API. Hash commitments do not themselves prove identity, successful work, payment or legal agreement. Input fields accept bounded opaque IDs and SHA256 strings, never executable instructions or URLs. There are no outbound calls, so this module creates no SSRF surface.

## Privacy, durability and limitations

`market.delete(requester_token, task_id)` removes task evidence commitments and events while retaining a content-free dedup tombstone until retention expires. `operator.purge()` explicitly removes credentials/tasks/events older than30days. Call it in the host's maintenance process; no background scheduler is installed. Replays are prevented only within retention. Persist the private Registry directory on durable storage; backups require separate protection and deletion policy. Existing SQLite directory/file permissions apply.

This 30day simulation store is NOT a commercial accounting system. Real settlement requires a retention window covering partner attribution, refund and dispute deadlines, plus tombstones surviving permissible payload deletion. The existing receipt ledger is not automatically bridged to this journey. No commercial record can be promoted from simulation to real use.

## Smallest actual shared deployment still needed

Use one authenticated service and one durable database as authoritative writer. Keep public discovery separate from authenticated writes. Authenticate requester/provider principals through scoped credentials or OAuth; bind each database operation to the server-resolved principal, never a caller-supplied tenant ID. Keep administrator approval and agreement signing out of provider credentials. PostgreSQL tenant constraints/row-level controls or another transactional shared database should replace local SQLite when multiple hosts are needed. A centralized single-host SQLite pilot can work only with a durable volume, backups and one trusted service boundary; free ephemeral hosting cannot supply durability by assumption.

Before deployment: implement TLS/auth middleware, rate and size limits, provider ownership renewals, immutable accepted quotes and price limits, adapter allowlists/DNS pinning, explicit send authorization, provider-specific signed receipts, provider-origin outcome IDs, replay-safe dispatch workers and reconciliation for uncertain results. Bind agreement acceptance to authorized party evidence. Define success criteria and refund/attribution windows per partner. Add cross-process credential bootstrap locking before concurrent first-time initialization; the current test starts workers only after trusted initialization.

No host has been selected or activated. Shared database services, availability, backups, usage limits and running costs must be confirmed before launch. The current artifact is a tested local foundation for these boundaries, not a publicly reachable multi-tenant marketplace.

## Runnable internal fixture (no external service)

Run from a checkout containing this module with tested dependencies installed. This creates a temporary simulation and deletes it on exit. Its `.example.com` provider and acceptance commitments are fixtures, never a real provider or agreement.

```python
import hashlib
import tempfile
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator

proof = hashlib.sha256(b"INTERNAL SIMULATION ONLY").hexdigest()
with tempfile.TemporaryDirectory() as directory:
    registry = Registry(directory)
    submitted = registry.submit({
        "name": "Internal fixture", "description": "No executable provider",
        "capabilities": ["citation_structuring"], "protocol": "api",
        "endpoint": "https://provider.example.com/api", "auth": "none",
        "requirements": "Simulation", "pricing": "Zero actual cost", "limits": "No dispatch"
    })
    provider = submitted["provider"]
    registry.review(provider["id"], provider["challenge"], proof, True)
    market = Market(registry)
    operator = MarketOperator(market)
    requester = operator.issue_credential("fixture-tenant")
    supplier = operator.issue_credential("fixture-owner", "provider", provider["id"])
    task = market.create(requester, "fixture-request", proof, proof)
    operator.match(task["id"], provider["id"], "fixture-match")
    market.advance(supplier, task["id"], "fixture-offer", "offered", evidence_sha256=proof)
    market.advance(requester, task["id"], "fixture-accept", "accepted", consent_to_send=True)
    print(market.get(requester, task["id"]))  # accepted simulation; no task sent
    registry.db.close()
```

The full simulated journey and signed-ledger separation are tested with `python -m unittest discover -s tests -p test_market.py -v`. No test result is independent adoption.
