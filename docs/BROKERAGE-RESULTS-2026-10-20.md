# Brokerage execution report — 2026-10-20 (America/Chicago)

Later work: see [Phase 2 delegation results](DELEGATION-RESULTS-2026-10-20.md). This report preserves the phase-1 evidence; its storage limitations are superseded only for the new delegation path.

PR: https://github.com/AHEDMUNI/resultgate/pull/1
Branch: feature/agent-brokerage
Implementation tested: 12162da9b8d6dfd06d219e08348f22a133349822
Live CI: https://github.com/AHEDMUNI/resultgate/actions/runs/39521126825
UTC test time: 2026-10-21T00:24:45.500953+00:00 (October 20 in Chicago).

## Completed

- Reviewed both original PR files/commits; ran baseline 99 tests successfully.
- Preserved the original two tools and unchanged shadow billing experiment.
- Added five opt-in MCP tools for catalog discovery, exact capability matching,
  preparing handoffs, explicit execution, and read-only referral tracking.
- Four documented real providers: Crossref, DataCite, Firecrawl and Tavily.
  Only Crossref and DataCite have execution adapters. Others are catalog-only.
- 114 tests passed locally and on GitHub Actions (83 original + 12 shadow +
  5 legacy routing + 14 brokerage). Original pytest routing cases now participate
  in the project's unittest runner. No new runtime dependencies.
- Bandit scan of resultgate: no findings. pip-audit of requirements-tested.txt:
  no known vulnerabilities. Neither is a guarantee against all vulnerabilities.
- Built wheel; Twine strict check passed. Fresh venv installed it; pip check
  passed; isolated original tool acceptance and 7-tool brokerage acceptance passed.
  This is an unreleased wheel built locally, not a PyPI publication.

## Real external integration — succeeded

A real MCP client initialized ResultGate, discovered providers, matched capability,
prepared routes and executed exactly two free public DOI requests from the GitHub
runner. Both responses passed provider-specific identity/title validation:

| Provider | Public fixture DOI | Observed title | Status |
|---|---|---|---|
| Crossref | 10.1038/nphys1170 | Measured measurement | succeeded |
| DataCite | 10.6084/m9.figshare.21545982 | A modified thickened flame model for simulating extinction | succeeded |

Both statuses were queried through track_referral. Repeated execute_route calls
returned duplicate status without another external request. Machine-readable
receipts copied from the actual CI log are in brokerage-live-evidence.json.
These receipts are internal evidence, not provider-signed attestations.

The first attempt from the local workspace failed because DNS resolution for
both API hosts was unavailable. Those attempts were recorded as failed; no
success was fabricated. GitHub's public runner subsequently succeeded with the
same implementation and network restrictions, without weakening TLS/SSRF checks.

These are calls to external services, **not independent third-party use**.
Verified independent users, independent referrals, revenue and commissions: zero.
No money spent, no paid services enabled, no provider accounts created.

## Limits / readiness

An independent agent can install the public feature branch, enable brokerage,
discover the tools and execute an approved public DOI lookup if its environment
can access the two hosts. We proved installation and protocol behavior using our
own isolated client, not an independently recruited agent.

Published ResultGate 0.1.1 and the current MCP Registry entry still expose the
previous free tools. There was no merge to main and no PyPI/registry publication.
The code on the feature branch also retains version 0.1.1: it MUST receive a new
version/release review before any future publication. The old publishing workflow
is not a release plan for this feature branch.

This is a curated service broker foundation, not yet agent-to-agent delegation,
a global agent registry or a source of proven referral income. DOI metadata
retrieval has no demonstrated commission opportunity. Firecrawl advertises a
subscription affiliate program, but ResultGate is not enrolled, and automated
agent attribution/resale eligibility has not been verified. Payment work remains
paused.

Session ledger has no durable storage and expires after one hour/restart. It does
not provide cross-day return metrics or verified external cohort identities. No
hosted multi-tenant endpoint, distributed retry protection or persistent referral
claims. Current catalog entries expire after 30 days without operator re-review.
Do not interpret free API documentation as unlimited use or a production SLA.

## Closest practical next step

For a downloadable free pilot, request owner approval to merge and publish a new
version that documents opt-in brokerage; update registry metadata and installation
instructions only after approval. Make a natural-discovery example for the specific
job of retrieving missing DOI metadata. An externally initiated execution with
consented, pseudonymous evidence would be our first actual independent referral;
our CI runs never qualify.

Before measuring repeat external usage, implement an opt-in durable minimal event
store and operator-managed test/external cohort separation with retention/deletion.
Before broader task delegation, add a reviewed specialist execution adapter and
provider-specific permission/price controls. Before any commission claim, obtain
an actual eligible agreement and provider attribution evidence. No account or
payment approval is required to inspect this PR; merge/publication still requires
explicit owner approval.
