# First independent order: public HTML page → Markdown + evidence report

Status (2026-10-21): **request-preparation pilot, not a live paid marketplace**.
This adds opt-in code to the existing ResultGate repository. Production `/mcp`
still runs the simulation gateway. No deployments, account registrations, purchases,
provider calls, payment collection, affiliate enrollment or new outreach occur here.

## The offer and the economic test

For a permitted public HTML page, prepare a native Firecrawl markdown request and
check the returned source URL, HTTP status, error flags and nonempty content.
Return a digest and explicit unknowns. A passing response shape does not establish
source authenticity, factual accuracy, completeness, payment or earned commission.
No PDFs, login sessions, private data, anti-bot circumvention or recursive crawls.

Firecrawl is the first technical candidate: native Markdown, $19 monthly Hobby
subscription (5,000 credits) or eligible free tier. This is the **whole subscription
price**, not a $19 one-page service or an invented per-request cash price.
ScraperAPI is a $49 monthly raw-HTML alternative requiring another conversion step.
Compare suitability and full commitment first, not potential commission. Existing
free allowance should be considered before recommending any paid subscription.
ResultGate currently charges $0. A new customer fee needs separate approval and terms.

Sources checked 2026-10-21:
- https://www.firecrawl.dev/pricing
- https://docs.firecrawl.dev/api-reference/endpoint/scrape
- https://www.scraperapi.com/pricing/
- https://www.firecrawl.dev/affiliates — advertises 25% first 12 months, then 15%.
  Approval wording on this page is inconsistent; AI referral eligibility, attribution,
  refunds and payout must be confirmed. No ResultGate agreement exists.
- https://www.scraperapi.com/affiliates/ — advertises 50%, while
  https://www.scraperapi.com/affiliate-terms/ makes the written rate controlling:
  qualifying link, $50 PayPal/$500 ACH minimums, $3,000/customer cap, refund clawback.
  AI referral eligibility remains unconfirmed. No enrollment/acceptance performed.

Evidence of need, **not ResultGate customers**:
- https://www.upwork.com/freelance-jobs/apply/Web-Scraping-and-Data-Extraction_~022100113085086479242/
  Public request mentions HTML-to-Markdown conversion and extraction failure handling.
  Search-index evidence only (direct page retrieval returned HTTP 403); current availability and buyer fit need review; broader project than this pilot.
  No application or message sent; no automation permission assumed.
- https://github.com/firecrawl/firecrawl/issues/4729 — reported export limitation.
  This is a user pain signal, not a paid lead or an independently reproduced defect.

## Use from a person or an independent agent

Install this reviewed branch in a virtual environment with `python -m pip install .`.
Use a new private directory; **one OS account/owner per store**. Do not share it
between untrusted agents or tenants. The local operator is the trust boundary;
this pilot is not protection against a process with that owner's filesystem access.

Human CLI comparison:

```sh
python -m resultgate.first_order.cli
```

Human request (substitute a page you have permission to collect):

```sh
python -m resultgate.first_order.cli --directory "$HOME/resultgate-first-order" --request-key my-order-001 --url https://example.com --permission-confirmed
```

MCP stdio command, usable by clients supporting custom stdio MCP servers:

```json
{"mcpServers":{"resultgate-first-order":{"command":"/absolute/path/to/venv/bin/python","args":["-m","resultgate.first_order.mcp","--directory","/absolute/private/path/first-order"]}}}
```

Claude Desktop-style clients can use the JSON above. For a Python MCP SDK client,
use `StdioServerParameters` and `ClientSession` as in `tests/test_first_order.py`.
Only the SDK process integration was executed here; no claim that every client
configuration was independently tested. Discover the five tools using `tools/list`.
No secret belongs in command arguments, JSON configuration committed to git, or intake.

## Approval and limits

The request defaults to the free plan. `--plan hobby_monthly` / MCP `plan` explicitly selects the recurring paid plan; changing plans requires a new request key and approval. The request returns a quote hash and expiry. The owner may inspect it with:

```sh
python -m resultgate.first_order.owner --directory /absolute/private/path/first-order show REQUEST_ID
```

Owner-only `approve` requires `--quote-sha256`, `--max-cost-micros` and
`--expires-at`. `revoke REQUEST_ID` clears it. A current approval for the same quote
is respected on status checks; expired, changed, under-budget or stale-price quotes
are rejected. There is no broad unattended spending grant and no automatic renewal
approval. No MCP tool can approve a quote. Approval is local intent only, not proof
that a third-party account holder authorized payment. A hosted consent identity flow
and cumulative reservations are required before a paid executor is introduced.

Every operation returns `execution_enabled: false`, even after owner approval.
`prepare_firecrawl_request` builds the documented request body; it NEVER sends it.
Future execution must revalidate DNS/redirects, permissions, actual credit cost and
remaining authorized budget at dispatch. Current hostname checks are not SSRF protection
for a future executor. No raw response is stored. Store capacity is 1,000 requests;
retention/deletion/export tooling is needed before broader hosted intake.

## Activation gates and rollback

1. Review this PR, security-sensitive consent design, and authenticated tenant wiring.
2. Confirm affiliate agreement/AI eligibility, attribution and refund/settlement evidence.
3. Obtain operator-approved deployment and a real customer's quote-scoped permission.
4. Implement and test bounded official transport, cancellation, ambiguous timeout handling,
   payment-proof verification and idempotent settlement before enabling paid execution.
5. Publish the reviewed tools through the existing authenticated gateway; update discovery
   metadata only after deployment. No open signup or unreviewed public write endpoint.

Rollback for this local pilot: stop its stdio process and return to prior checkout.
Do not remove the existing gateway or discovery timer. No migrations touch their stores.

The daily GitHub job and server discovery timer remain independent. This PR does not
claim autonomous sales, public deployment, payment proof, or revenue.
