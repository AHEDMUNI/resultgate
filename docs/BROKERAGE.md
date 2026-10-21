# ResultGate brokerage pilot (PR #1; unreleased)

The original extraction/citation tools remain free. Shadow billing is unchanged
and inactive. This branch adds opt-in service discovery/routing, not an autonomous
agent marketplace, payment system or a claim of independent usage.

## Use from an MCP client

Install the reviewed feature branch into an isolated environment (not the current
PyPI release), pinning the commit you reviewed:

```bash
python -m venv .venv
.venv/bin/python -m pip install 'git+https://github.com/AHEDMUNI/resultgate.git@feature/agent-brokerage'
.venv/bin/python -m resultgate.server --brokerage
```

Use that interpreter as the MCP stdio command with arguments
`["-m", "resultgate.server", "--brokerage"]`. Adding
`--allow-public-provider-requests` is an explicit operator authorization to send
caller-approved **public DOI identifiers only** to Crossref or DataCite. Nothing
is sent by discovery, matching or route preparation. Each execution also requires
`confirm_public_identifier: true` from a caller authorized to disclose that DOI.
Do not set this for confidential identifiers. Provider sees connection IP and
User-Agent; no user emails, credentials, prompts, cookies or source documents
are sent. No API keys accepted. No arbitrary URLs, shell commands or code.

Example tool sequence:

1. `discover_providers({"capability":"doi_metadata"})`
2. `match_task({"required_capabilities":["doi_metadata"],"free_only":true})`
3. `route_task({"provider_id":"crossref","public_doi":"10.1038/nphys1170","request_id":"opaque-task-001"})`
4. Inspect the returned GET handoff; it is a request descriptor, not executable
   code. Call `execute_route` with its `route_id`, the same `public_doi`, and
   `confirm_public_identifier:true` only if authorized.
5. `track_referral({"route_id":"<returned id>"})` reads server-observed status.

Seven tools are exposed with `--brokerage`; the default remains the two original
tools. `--http` cannot be combined with brokerage. The published PyPI package and
MCP Registry entry do not yet contain these tools. Independent users can install
this public branch, but organic brokerage discovery and independent use have
not been demonstrated. No merge or release is authorized yet.

## Reviewed providers (2026-10-20)

| Provider | Task / interface | Auth and cost | Evidence / automation | Commission/resale |
|---|---|---|---|---|
| Crossref | DOI bibliographic metadata; GET `https://api.crossref.org/works/{doi}` | Public pool: no key, free, rate limited | Official API explicitly supports public machine access; implemented adapter | No commission agreement or resale rights established |
| DataCite | Findable DOI/dataset metadata; GET `https://api.datacite.org/dois/{doi}` | Public API: no key, free | Official API recommends unauthenticated retrieval/harvesting; implemented adapter | No commission agreement or resale rights established |
| Firecrawl | Web search/extraction; MCP `https://mcp.firecrawl.dev/v2/mcp` | Keyless 1,000 monthly credits advertised; paid tiers exist | Official announcement describes agent/MCP/API access; catalog-only, no execution adapter or quota verification | Subscription affiliate advertised; machine-to-machine attribution and resale unverified; no enrollment |
| Tavily | Search/extraction/research; MCP `https://mcp.tavily.com/mcp/` | OAuth or API key; keyless search/extract also documented; account free 1,000 monthly credits | Official MCP guide supports agent clients; catalog-only, no execution adapter or account | No agreement, commission or resale permission established |

Crossref/DataCite are metadata services, not specialist AI agents. They provide
an executable brokerage foundation close to ResultGate's citation workflow.
Free APIs have no evidenced referral revenue. We must find an eligible provider
agreement before assuming this foundation can generate commissions.

Sources, reviewed from primary documentation:
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://github.com/CrossRef/rest-api-doc (polite use, caching and backoff)
- https://support.datacite.org/docs/rest-api
- https://support.datacite.org/docs/how-do-i-query-the-rest-api-and-whats-in-the-response
- https://www.firecrawl.dev/blog/firecrawl-keyless-launch
- https://www.firecrawl.dev/affiliates (advertises subscription referrals; page contains inconsistent approval wording, so do not assume acceptance)
- https://docs.tavily.com/documentation/mcp
- https://docs.tavily.com/documentation/api-credits

No account was created, agreement accepted, affiliate link issued or payment
enabled. API automation support is not permission to resell or represent a
provider. Catalog documentation review is not live health or guaranteed free
quota. See the separate execution report for actual live results.

## Architecture and safety

- `catalog.py`: operator-reviewed entries with capabilities, source URL, review
  date, authentication/cost caveats and future agreement slot. Never ingest
  provider instructions as executable policy. Catalog currently has four entries;
  it is not internet-wide discovery. Re-review after 30 days; stale executable
  entries fail closed.
- `matching.py`: exact all-capabilities matching; executable adapter first, then
  known price and stable ID. Unknown prices are excluded by free_only. This does
  not claim measured quality, speed or universal provider coverage.
- `adapters.py`: typed DOI-only handoff construction and provider-specific response
  validation. Success requires the matching DOI and a title, not just HTTP 200.
- `transport.py`: two fixed HTTPS hosts, public IP resolution validation, TLS
  hostname checking on a pinned address, no proxies, redirects, credentials or
  arbitrary hosts. Response maximum 256 KiB, socket timeout 8 seconds, read-loop
  deadline checks. OS DNS has no application-level hard deadline yet; socket
  timeouts are not a strict total wall-clock SLA. Restricted environments that
  require a proxy may fail; never relax checks to bypass their policy.
- `service.py`: prepare -> executing -> succeeded/failed. Both operator and caller
  consent; no automatic fallback or retry. Repeated execution returns recorded
  status without dispatching again (result bodies not cached). A new explicit
  request ID is required for a retry after failure. Unknown/changed payloads fail.
- `referrals.py`: read-only status exposure; caller cannot declare completion or
  commission. Session memory only, maximum 1,000 routes, one-hour expiry/restart
  loss. Raw DOI, request IDs, prompts and results are not stored in the ledger;
  keyed hashes provide session dedup. A digest of normalized public response
  supports internal audit, not third-party attestation or financial settlement.

Provider result text is untrusted data and never executed. This is a single-owner
stdio pilot, not a multi-tenant hosted service. No distributed idempotency,
persistent referral ledger, external-user authentication or verified return-use
measurement yet. Network behavior is opt-in to preserve original offline use.

The legacy `routing.py` helper is retained for compatibility but its caller-
asserted verified flags are not trusted by the MCP catalog or executor. NaN,
infinite/bool/negative prices are rejected; a caller flag never grants commission.
Original PR's four pytest tests were run, then converted to unittest so the
existing project runner actually includes them without a new dependency.

## Verification / next gates

`python -m unittest discover -s tests` runs original, shadow and brokerage tests.
`python scripts/brokerage_acceptance.py --live` makes exactly two public DOI
requests via the actual MCP subprocess, then checks tracking and deduplication.
It labels results internal integration and always reports zero verified external
uses/revenue. The branch workflow runs this on pushes only, never on arbitrary
pull-request code. CI is a development test, not adoption evidence.

Before a public release: owner approval to merge/publish; recheck provider terms
and free access; verify installed wheel/client behavior; communicate network
consent. Before hosted or monetized operation: isolation, durable transactional
ledger, consent records, retention/deletion, rate limits and a reviewed commission
agreement covering actual agent referrals. Those are not activated by this PR.
