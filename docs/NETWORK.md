# Local provider onboarding and outcome receipts (unreleased PR)

This is an opt-in local pilot, not a public marketplace, not an A2A server and not a payment service. Default tools remain 2; brokerage 7; delegation 12. Adding `--provider-registry /private/path` enables 5 more tools (17 total with delegation). Published PyPI 0.1.1 does not contain these PR features. Shadow billing is unchanged.

## Install and discover

Use a reviewed immutable commit from PR #1 for reproducibility:

```sh
python -m venv client
client/bin/python -m pip install 'resultgate-pilot @ git+https://github.com/AHEDMUNI/resultgate.git@feature/agent-brokerage'
client/bin/python -m resultgate.server --brokerage --delegation --provider-registry /private/resultgate-providers
```

For independent MCP clients, configure `command` as the absolute `client/bin/python`, and `args` as `["-m", "resultgate.server", "--brokerage", "--delegation", "--provider-registry", "/private/resultgate-providers"]`. Call `tools/list` after initialization. Do not use the public released package expecting brokerage. Pin the commit you inspected instead of the mutable branch for regular use.

Capabilities exposed in tool descriptions: discovery, matching, explicit public-citation delegation, result checks, task tracking, provider submission. `discover_registered_providers` lists locally approved submissions; `discover_agents` lists built-in reviewed execution adapters. These remain separate: a reviewed domain is not a reviewed executable adapter. Submissions never cause HTTP requests or commands. MCP/A2A/API are declared provider protocols, not automatic protocol support. All provider prose and output are untrusted data.

## Provider self-submission

Call `submit_provider` with `submission`:

```json
{"name":"My citation processor","description":"Structures public citations","capabilities":["citation_structuring"],"protocol":"api","endpoint":"https://provider.example.com/api","auth":"api_key","requirements":"User supplies credential directly to provider; do not submit it here","pricing":"USD 0 for sandbox only","limits":"10 sandbox tasks/day"}
```

This is an illustrative endpoint, not a real catalog entry. Never put API keys, private user data or secrets in public metadata, URLs or terms. Authentication is an enum describing requirements, not credential storage. The response gives a private management token (store it securely; hashed in SQLite), an ownership challenge and domain challenge location. Publish the challenge there; request local operator review. No unattended fetch of submitted endpoints occurs. The initial review uses an operator's independently obtained evidence: challenge match alone is not identity proof. It establishes domain control only, not legal identity or execution quality.

Provider tools: submit, update, suspend, accept exact proposed terms, discover reviewed submissions. Updating anything resets ownership and all term acceptance. There is no self-approval tool. The provider receives proposed terms through the operator during this local pilot. Tokens cannot approve providers or agreements. An administrator with filesystem access is the trust boundary and can always alter local records; this is not a multi-tenant hosted security boundary.

## Operator review (local CLI only)

Use `python -m resultgate.network.operator --directory /private/resultgate-providers ACTION`, JSON on stdin. Actions:

- `inspect`: `{"provider_id":"..."}`
- `review`: provider_id, approve (boolean), observed_challenge, evidence_sha256. Independently verify the exact HTTPS domain challenge within 24h, identity/contact/terms, service safety, capability and costs; retain source evidence outside this limited-data database. SHA256 references evidence, it does not itself authenticate it. Approve false rejects. Never fetch private/reserved DNS addresses or follow redirects while reviewing.
- `propose`: provider_id, terms (specific complete text), kind (`task`, `subscription`, `transaction`), rule (`fixed`, `basis_points`), amount (integer microUSD or basis points). Exact text plus structured economics are hashed. Specify success/acceptance/refund/dispute/expiry conditions. No proposals for real businesses have been entered.
- Provider calls `accept_provider_terms` with management_token, exact terms_sha256 and explicit_acceptance=true.
- `approve-agreement`: provider_id, evidence_sha256. Only after separate operator review of provider consent and authority. This tool does not sign a contract on anyone's behalf.

Changes to terms invalidate acceptance. Review rejects/suspension prevent commission assessment. There is no automatic execution for submitted providers: each needs a reviewed adapter with endpoint allowlisting, DNS/public IP checks, consent, bounded I/O and outcome verification before integration.

## Receipts / future attribution

`resultgate.network.receipts.Receipts` is a local library, not an HTTP webhook endpoint. It defines an illustrative HMAC SHA256 contract, **not** an implementation of Apify, Dub, FirstPromoter or BrowserAct webhooks. No partner has agreed to this format. The operator binds a provider to an out-of-band 32+ byte key; no MCP method accepts keys or administrative receipts. Keys remain outside SQLite and may never come from untrusted webhook payloads.

`refer` freezes an approved provider/agreement, request evidence hash, exact agreed rule and outcome type, expiry <=30 days, and random referral ID. Only one outcome is attributed to each referral in this pilot (no subscription renewals ledger yet). Caller-generated IDs are not economic evidence. `ingest` checks HMAC of `timestamp + '.' + raw_body`, ±300s window, bounded strict schema, provider/referral binding, unique event IDs and unique provider/outcome IDs. Raw customer/outcome IDs are keyed hashes. Same event/body is idempotent; changed body or reuse of an outcome on another referral is rejected transactionally.

Success receipt -> completed; local independently reviewed acceptance -> verified; valid approved agreement + acceptance + independent-use evidence (or explicit internal simulation) -> commission_eligible. HTTP success alone does not qualify. Explicit failure/cancel/refund/dispute blocks reassessment and voids recorded eligibility. An authentic signature proves origin only, not truthful economic success: production needs partner-side transaction reconciliation, acceptance review and refund maturity before claims. Operator attestations are not autonomous proofs. The earlier delegation ledger remains intact; this receipt ledger links by `request_sha256`/evidence references, with an explicit reviewed handoff rather than fabricating a built-in provider's commercial agreement.

No invoices, subscriptions sold by ResultGate, payment calls, money collection or commission claims occur. Real earning eligibility has not been demonstrated. Locally tested fixtures use simulation only.

## Privacy and retention

Private directory 0700, database/key 0600; no encryption. Submissions are intended public metadata. Tasks/results/customer identities/API keys are not stored in this network module. Only hashes, IDs, bounded terms and states. Provider records expire after 30 days without updates; network referrals, event/outcome hash tombstones and audit records expire after 30 days (lazy on access/start, no background daemon). Local `Registry.delete(id,token)` deletes a provider and its audit. `Receipts.delete(id)` deletes referral details, retaining keyed dedup tombstones until retention expiry. Deleting/expiring data removes dedup protection: commercial reconciliation must never reuse old outcomes blindly. Backup deletion is the operator's responsibility. State restoration is tested; power-loss backups/enterprise recovery are not provided.

Metrics separate internal / external_unverified / independent_verified. Provider registration, package installs, GitHub stars and our CI are not verified independent use. Independent attestation requires evidence reviewed outside the tool; self-declared cohort alone is insufficient. No central telemetry/upload, no tracking cookies.

## Repeatable acceptance

CI builds the checked-out public commit to a wheel, installs in a separate venv, and runs from a temporary directory with Python `-I` (no source imports). Existing 2/7/12-tool acceptance remains. `scripts/network_acceptance.py --live` discovers 17 tools, finds GROBID, explicitly delegates the public documentation citation, verifies surname/year, checks duplicate execution suppression and status after process restart. Running this script requires installed wheel and intentionally enables a single free GROBID demo request. It is internal testing even on a separate runner. GROBID is ML document processing, not an autonomous agent and not a production/commercial provider.

## Protocol boundaries

Official references checked 2026-10-21:
- https://modelcontextprotocol.io/specification/latest/server/tools (resolved to 2026-07-28): descriptions and tools/list discovery. Runtime uses pinned MCP SDK 1.30.0; compatibility is tested with its client, not claimed for every newest protocol feature.
- https://a2a-protocol.org/latest/specification/ : current AgentCard requires real supported interfaces and operations. No deployed A2A interface exists here. We intentionally publish no fake `/.well-known/agent-card.json`. Preparation consists of the discovery manifest and documented mapping: skills -> reviewed capabilities; send/get/cancel -> delegation lifecycle. A conforming transport, auth, error semantics and protocol conformance tests remain required before advertising A2A.
