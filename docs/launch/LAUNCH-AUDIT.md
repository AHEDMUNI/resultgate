# Launch audit — October 21, 2026

## Proven state

- main: `1f96ac880aef0131a3914d9ddcec390880899d5f` at audit time.
- PR #9: open, provider/recommendation preview, head `1477485`. Not deployed.
- PR #12: draft, financial TEST implementation, head `e0fbad1` before this task.
  Actual Stripe Sandbox acceptance is documented there. No live adapter or production
  owner/financial HTTP flow exists; a live key is not a missing activation toggle.
- PR #13: static site. Before this task its head was `cbfe5dc`. All six public pages and
  CSS fetched over verified HTTPS matched those repository files byte for byte.
  `/mcp` returned 401 anonymously. New services/request/agents/catalog and discovery
  files returned 404 before this change.
- Running application commit `6d16cef` is operator-reported, not newly proven by these
  public responses. No SSH session is available from this workspace. A read-only
  `deploy/launch_host_status.py` reads service status and installed VCS metadata/hash
  without printing command lines, environment or secrets. Null VCS metadata means
  a precise installed commit cannot be established from package metadata alone.

## Branch reconciliation

Local `git merge-tree --write-tree` checks found no textual conflict between current
main and the audited PR #9 or #12 heads. That is not permission to deploy them.
PR #9's preview `Marketplace` and PR #12's `Commerce` both implement provider intake
with different tables and approval semantics. Do not enable both or maintain two
commercial catalogs. Keep the hosted gateway unchanged; use PR #12's Commerce as
future commercial system of record after review. Public issues/email are applications
for manual review, never automatic provider records or agreement acceptance.
PR #11's older single-service brokerage is not a dependency.

## This release scope

Static availability/catalog (currently empty), service-interest route, provider
application links, agent documentation, robots/sitemap/plain-text descriptor. No
purchasable offer or synthetic checkout button. Existing MCP remains simulation.
Guarded publisher updates only an exactly recognized generated static block;
unknown edits fail closed. Nginx validation and every route/body are checked, with
config backup and rollback. No application restart or payment key is needed.

A read-only launch observer checks routes and existing public GitHub intake. All
observations are marked internal; unknown visitors, authenticated agents, orders and
financial metrics stay null when no reliable source is available. GitHub submissions
remain unverified signals; author/bot/internal-test exclusions and deduplication apply.
The prepared six-hour workflow becomes scheduled only when on main; GitHub scheduling
can be delayed and is not a promise of uninterrupted execution. Its run summary is
the evidence record. It cannot change code, approve providers, send mail or charge.

## Necessary launch gates

1. One provider agrees to a clearly priced, authorized offer and the 15% commercial
   terms, including processing/refund/dispute cost allocation and fulfillment.
2. Independently reviewed production owner/provider identity and consent path,
   Stripe Connect eligibility, live financial adapter, durable webhook/refund recovery,
   monitoring, backup and rollback; explicit owner live authorization.
3. Deployed offer and request path plus an approved public acquisition placement.

Before any code accepts live keys, review minimum charge economics: gross 15% is not
net income. Processor fees were $3.20 on the observed $100 test payment; do not assume
that applies to every transaction, account, payment method or country.

## 72-hour protocol

`docs/launch/readiness.json` stays blocked. An operator must verify the approved offer,
public reach channel and independent order path, record evidence digests and the
actual UTC start time. This file does not enable payment. Record both start and end;
America/Chicago presentation is appropriate for the owner. Never backdate the start.

Visit counts require a trustworthy dedicated server log/analytics source; HTTP probes
are not visits, IPs are not customers, and user agents cannot prove independence.
Independent MCP use requires successful authenticated tool calls from separately
reviewed requester credentials. Request, payment and fee counts must come from their
actual durable records with internal/test actors excluded. Missing data is unknown.
Public issue counts alone cannot supply these metrics.

At 72h: no verified reach -> distribution measurement gap; reach but no relevant
interest -> offer/fit question; accepted independent orders but no Checkout -> approval
or conversion blocker; successful Checkout without eligible fee -> financial incident.
Zero alone is not conclusive market failure and does not authorize unrelated features.

## Validation in this task

62 focused tests passed on PR #12 source: commerce, Connect, signed-event acceptance
runner, gateway and MCP gateway. 10 tests passed for static-site update boundaries,
links/discovery truthfulness, measurement gates and internal/bot deduplication.
Bytecode compile and git diff --check passed. GitHub checks on the three audited
pre-change PR heads were successful; new-head CI must be observed before merge.
No additional Stripe payment was created, and previous Sandbox evidence was reused.
