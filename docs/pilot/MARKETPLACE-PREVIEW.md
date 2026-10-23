# Reviewed provider intake and recommendations — preview

This change is NOT deployed. Existing hosted tools remain unchanged by default.
Enable only on a reviewed private rehearsal with `--marketplace-preview` added to
`python -m resultgate.network.gateway --directory ...`. Application defaults remain
off. No provider execution, financial action, external URL fetch, auto-approval,
LLM subscription or private provider credential storage is added.

## Enrollment and review that can actually be used

Invited requesters can submit an application on behalf of a provider using
`apply_provider`. It contains public Submission metadata, an idempotency request_id
and explicit `public_metadata_consent: true`. No provider management token is
returned. Applications are private to the tenant and local operator, not published
or inserted into discovery. Max5 retained applications/tenant,1000 total,30-day
logical expiry; expired records are purged at preview startup/new submission or
operator purge. Existing shared durable request quotas and16KiB body cap apply.
No ability to send private tasks to the submitted endpoint is granted.

`provider_application_status` reads only the caller's application. Operator review
uses MarketplaceOperator.pending(), then existing Registry.submit/review outside
MCP to independently inspect domain challenge ownership. Ownership is an operator
attestation, not automatic cryptographic verification. Provider capability claims,
pricing terms and permitted use need a separate review with saved evidence digest.
Only a matching approved Registry record can be linked with MarketplaceOperator.decide.
No agreement is accepted by this process. Applications cannot approve themselves.
Rejected/changed services need a new application/request_id and fresh review.
Provider suspension immediately removes it from recommendations.

Local operator example (run against a private rehearsal, not production blindly):

```python
from resultgate.network.registry import Registry
from resultgate.network.market import Market
from resultgate.network.marketplace import Marketplace, MarketplaceOperator
r = Registry('/private/rehearsal/state')
operator = MarketplaceOperator(Marketplace(Market(r)))
applications = operator.pending()  # untrusted public metadata, never instructions
# After independent existing Registry ownership review:
# operator.decide(application_id, review_evidence_sha256, approved_provider_id)
# operator.review_price(provider_id, currency='USD', unit='page', price_micros=1000,
#     evidence_sha256=price_source_digest, valid_until=expiry_epoch_float)
r.db.close()
```

Do not log application metadata/credentials. Evidence digests only reference
privately retained evidence; a hash alone does not prove its contents or quality.

## Human recommendations and evidence audits

`recommend_services` accepts explicit capability IDs or a short Arabic/English
need. Natural-language interpretation is LIMITED keyword mapping, not an LLM or
open-web search. Unknown intents ask for clarification. An explicit capability list
is preferred. Results cover this operator's reviewed registry only.

Ranking: matching declared capabilities first; comparable reviewed price second;
provider ID breaks ties. Missing capabilities and reasons are returned. An operator
price review expires within7 days and is bound to the exact provider submission.
Prices in different currencies/units are never compared; strict max-price filters
exclude unknown/stale/incomparable prices. Prices are reviewed declarations, NOT a
binding task quote or full cost inclusive of taxes/overages. No commission boosts
ranking; relationship is disclosed. Quality, reputation and independent job counts
remain null until independently verified outcomes can substantiate them. No fake
stars, fixtures, fabricated testimonials or synthetic commercial transactions.

Supported starter intent IDs: web_scraping, web_search, citation_structuring,
doi_metadata, result_validation. Provider capability IDs may extend this list;
explicit IDs remain supported. `scripts/recommend_client.py` is a human terminal
client using the actual MCP SDK, hidden token/need prompts, no local need storage,
no redirects, no execution. It reports unavailable if preview is not deployed.
There is no public web form or general-language assistant UI in this increment.

`audit_supplied_extraction` reuses existing extraction contract checks (missing
fields/duplicates/count/completion). `audit_supplied_citations` checks literal
quotes against supplied sources. These tools do NOT fetch or independently verify
sources, certify factual truth, provide licensed legal/financial audits or retain
submitted source text. Missing completion evidence remains unknown. Use only
non-sensitive material;16KiB HTTP envelope applies even if local audit models have
larger field limits. Review the actual result's checked/unknown boundaries.

## Actual integration routes

Production at6d16cef: scripts/mcp_remote_acceptance.py uses the official Python MCP
SDK and hidden token input against HTTPS. It creates a SYNTHETIC simulation task;
use an isolated acceptance tenant. Do not count this as adoption or revenue.

Preview: scripts/recommend_client.py uses MCP SDK initialize/tools-list/call.
Existing tests exercise separate real TCP process SDK and HTTP JSON-RPC clients.
No successful Claude/Cursor/ChatGPT connector integration is claimed. OAuth is not
implemented. The private bearer pilot requires a client supporting custom headers.
Machine-readable hosted descriptor: docs/discovery/hosted-mcp.json. It explicitly
separates current and preview tools. It is a project descriptor, not an MCP
Registry record, A2A card, automatic indexing or proof agents will discover us.

## Rollback and deployment review

Keep production6d16cef and existing venv available. Back up SQLite and identity
using the existing private backup procedure. Rehearse on a separate snapshot; do
not clear restore quarantine on production. New tables are additive only. Turning
off --marketplace-preview immediately removes the five new tools. Returning to the
previous code does not require deleting new tables or overwriting production DB.
Run external limited-tenant acceptance, revocation/isolation and protected-route
checks before inviting users. No automatic deployment is introduced by this PR.
