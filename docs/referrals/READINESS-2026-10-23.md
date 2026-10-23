# First referral readiness — 2026-10-23

Reviewed main `96ff7318ef3b82cbacc8f4b77f93c123af687799` (PRs 16–19 merged).
All 239 source blobs in the isolated baseline match that remote tree. No prior
work was repeated or overwritten. This change is review code, not deployment.

## Commercial path

- Existing issued URL: `https://browseract.com?fpr=ahed-ddc97e`.
- One internal browser navigation reached `https://www.browseract.com/?fpr=ahed-ddc97e`.
  The retained query parameter proves a navigable landing URL, **not** a provider
  tracked click, current affiliate status, attributed registration, or commission.
- BrowserAct support's 2026-10-23 reply explicitly permits recommendations to
  authorized agents through MCP. Customers must register through the affiliate
  link. API usage or recommendation alone does not create attribution.
- Support confirms refunded-order commission deductions and dashboard reporting;
  an affiliate-reporting API is not supported.
- [Public program FAQ](https://www.browseract.com/affiliate): last valid click
  before signup; 30% first eligible paid order; 20% eligible purchases during six
  months from first payment; $50 confirmed balance; monthly payout by the 15th of
  the following month after validation and clearing refunds/disputes. This is
  published program information, not proof of the account's accepted agreement.
- Current membership, accepted terms, cookie lifetime, hold duration, account rate
  duration and payout readiness/fees remain unverified. No login retried, terms
  accepted, payout settings changed, customer enrolled or purchase made.
- The issued URL is preserved as **inactive review evidence** in the shared card.
  Active MCP/static handoffs remain ordinary provider URLs pending account review.

## Discovery, actually observed

| Surface | Observed state | Referral-tool limitation |
|---|---|---|
| [Cursor topic 175684](https://forum.cursor.com/t/resultgate-helping-useful-agents-get-discovered-starting-with-a-small-mcp-demo/175684) | Public web retrieval succeeded. Browser showed Listed event one day earlier and 13 cumulative views. | Links to the working BrowserAct guide and source setup. Views include unknown/internal traffic; not daily independent users. No new post or reply made. |
| [Glama](https://glama.ai/mcp/servers/AHEDMUNI/resultgate) | Public listing visible, maintainer verification indicator, two inspected checking tools. | Old 0.2.0 entry, no referral tools in its inspected schema. README source bridge prepared; no listing edit or redeploy made. |
| [MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=resultgate&version=latest&limit=10) | One active latest record, `io.github.AHEDMUNI/resultgate`, PyPI 0.2.0, stdio, brokerage/delegation arguments. | Does not launch the referral companion. No new package or registry version published. |
| [Public catalog](https://agents.allubiyerbamate.com/referrals) | All six providers rendered, source setup linked. | Static guide; handoffs untracked. Not a public MCP tools endpoint. |
| Hosted `/mcp` | Unauthenticated browser request returned `request_rejected`. | No claim that referral tools are published there. No auth/security change made. |

An isolated installed-source MCP client, invoked outside the checkout, discovered
all six companion tools and called list → recommend → prepare for BrowserAct.
Returned the current permission status, unresolved commercial gates and untracked
handoff. This is an **internal protocol test**, not an independent operator or
Cursor/Windows usability test. 302 local tests passed, including stage separation,
timezone boundaries, deduplication, private read-only DB, and static/MCP consistency.

## Real daily baseline

The existing [scheduled run](https://github.com/AHEDMUNI/resultgate/actions/runs/39957308328)
completed successfully on October 23 at 12:57 UTC. Its downloaded artifact reports
October 22: `/browseract`, `/referrals`, `/referrals.json` returned HTTP 200 during
the current internal probe. All customer/financial totals were null because no
web analytics or provider evidence feed was connected. Its in-memory empty log is
**not evidence of zero users**. The schedule already exists; no duplicate scheduled
task is needed.

The corrected reporter adds distinct click and registration stages and can read
an existing private evidence DB. Public Actions remains availability-only. Do
not upload private provider exports or customer evidence to public GitHub.

| Required metric | Actual available evidence today |
|---|---|
| Reach | Cursor displayed 13 cumulative views, origin/date breakdown unavailable. Site independent arrivals unavailable. |
| Recommendation request | Internal installed-client test passed; independent requests unavailable. |
| Click | One internal landing-URL test; provider-recognized and independent click totals unavailable. |
| Registration | Provider evidence unavailable. |
| Attributed purchase | Provider evidence unavailable. |
| Approved commission | Provider evidence unavailable; no amount claimed. |
| Actual payout | Payment receipt unavailable; no cash claimed. |

## Existing provider correspondence

Apify and SearchApi: inquiries sent, no substantive answer in current connected
mailbox search. PDF.co: receipt ticket 148126884, no substantive answer. Firecrawl:
original inquiry located in the second connected mailbox, no reply found. Make:
previous inquiry remains unsent; no verified direct affiliate address available.
No duplicate messages or applications sent. BrowserAct flow eligibility no longer
needs another question; unresolved account/contract details are separate.

## One owner action batch, after reviewing this change

1. **Read-only BrowserAct review:** approve reopening the existing
   [FirstPromoter account](https://browseract.firstpromoter.com/) and signing in
   if needed, or supply redacted status/terms/report screenshots yourself. Scope:
   membership, issued link, accepted agreement, reporting and payout readiness.
   Stop at any new agreement. No account creation, spending, changing recipient,
   payment details or secret sharing. The owner previously stopped login retries;
   this approval is required by that explicit instruction.
2. **Publish reviewed source/static correction:** review the draft PR before
   merge/deployment. It fixes discovery wording, permission status and daily
   reporting only; no runtime/auth/payment changes. Verify the live static output
   after publication. Commercial activation is still conditional on item 1.
3. **Measurement access:** supply a redacted date-bounded affiliate report and
   authorized site access-log/analytics export, or authorize read-only access on
   the existing server. Keep raw records private. Local MCP has no central
   telemetry; independent recommendation use requires a consented operator log.
   Provider dashboard totals alone cannot prove which visitor used ResultGate.

No new contract approval is requested before its exact text is visible. Missing
cookie/hold/fee terms are unknown, not invented. Do not request new provider API
keys: BrowserAct says affiliate reporting has no API.

## 72-hour gate

**Not started.** External discovery is verified; commercial qualification and
measurement access remain blocked. Start only after all three pass, with actual
start/end timestamps and a frozen reviewed version. At 72 hours diagnose the
earliest measured break. Missing data cannot establish absence of demand; a
commission awaiting threshold/hold cannot be reported as a cash payout. No
feature expansion, Stripe Connect work, advertising, outreach or artificial sales.
