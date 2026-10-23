# ResultGate: six-provider selection pilot

## Current commercial gate (2026-10-23)

BrowserAct has explicitly permitted MCP recommendations followed by customer
registration through the issued affiliate link. Its landing page was checked
internally and retains the referral parameter. This is not provider confirmation
of a tracked click. Current membership, accepted terms and reporting/payout
readiness still need owner-account evidence. Do not retry login without approval.
The public catalog and companion continue to use untracked handoffs until that
review; the issued link is recorded in the card as inactive review evidence.

The existing Cursor topic 175684 is publicly readable and shows a Listed event.
Glama lists ResultGate and the MCP Registry lists version 0.2.0 as active. Those
registry/package entry points do not expose this companion. Install reviewed
source using this guide, not `uvx resultgate-pilot==0.2.0`, for referral tools.

No keys, purchase, account registration or provider run is required for the local demo. Execution and billing remain with each provider. The hosted `/mcp` has NOT acquired these companion tools. Do not paste provider credentials into ResultGate.

## Clean setup (Python 3.11+)

Clone this existing repository, use a reviewed release commit, then:

```sh
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m unittest discover -s tests -p 'test_referral_selector.py'
```
Windows uses `.venv\Scripts\python.exe`. Cursor Settings → MCP → add a local server using **absolute paths**:

```json
{
  "mcpServers": {
    "resultgate-selection": {
      "command": "/ABSOLUTE/resultgate/.venv/bin/python",
      "args": ["-m", "resultgate.browseract_demo"]
    }
  }
}
```

Restart/refresh MCP. Six tools should appear: the three existing BrowserAct assessment/CSV validation tools, plus `list_referral_providers`, `recommend_referral_service`, `prepare_referral_task`. This is a local stdio integration, not hosted authentication. This repository does not send local tool-call analytics.

## Ready prompt: no provider invocation

> Use ResultGate only. List its referral candidates. My need is web_to_markdown, sources_permitted=true, sensitive_or_login_required=false, existing_solution_sufficient=false, local_solution_sufficient=false, maximum_monthly_budget_usd=0. Recommend a service, then prepare_referral_task for firecrawl with sources_permitted=true and sensitive_data=false. Do not run another tool, create accounts, buy anything, or send credentials. Show the free alternative and eligibility gaps.

Expected: `prepare_free_evaluation`, Firecrawl capability match, an untracked official link, a bounded practice-page task and provider connection instructions. No sale or execution occurs. Set `local_solution_sufficient=true` to test the free/local recommendation; set `sources_permitted=false` to test rejection. Other needs: browser_interaction, search_results, document_extraction, app_workflow, specialized_actor.

## Existing evidence, without another external run

- BrowserAct: `examples/browseract/accepted/result.csv`, 20 fictional products, original values preserved. Owner-supplied internal run; not an independent user.
- Firecrawl: `examples/referrals/firecrawl-keyless.json`, actual no-key MCP response from the same practice homepage. `verification.json` records the hash, 20 URL checks and five title/price samples. This is not a full structured availability extractor.
- SearchApi, PDF.co, Make, Apify: task/instruction contracts tested locally. No account opened and no provider task executed. Free allowances do not constitute authorization to enroll.

For the BrowserAct result check, follow [the existing operator guide](../browseract/OPERATOR.md). For provider use, inspect the selected card's `integration.docs_url`, scopes and allowance in the provider's own account. Obtain the owner's approval there. Abort if a key, paid upgrade or broader scope is unexpectedly requested. Keep errors rather than fabricate values. ResultGate cannot automatically inspect external account balances or confirm task completion.

## Manual boundaries and measurement

Installation, Cursor configuration, permission review, provider connection, and returning results remain manual. Cursor GUI usability by an independent operator has not been established by our protocol test. No measured assisted-vs-direct setup-time benefit is claimed.

Owner may store evidence privately using `python -m resultgate.referral_measurement --db /PRIVATE/events.sqlite --event /PRIVATE/event.json`. Each event needs opaque `id`, `subject`, `evidence_ref`, `kind`, `origin`, plus `provider_id` and timezone-aware `occurred_at`. Never put email addresses, secrets, tokenized links or customer content in that file. Attribution and commissions require provider statements, payout requires an actual payment receipt; manual entry is not proof authentication.

`python -m resultgate.referral_daily --db /PRIVATE/events.sqlite --day YYYY-MM-DD` reads only. Missing feeds produce null totals. Internal/ALLUBI/unknown origins remain separate. Daily GitHub workflow probes public availability, NOT customer usage; repository variable `RESULTGATE_REFERRAL_MONITOR_DISABLED=true` stops it. It cannot receive or validate affiliate payments. A failed run is visible in Actions; no external alert channel is configured.

The owner's current experiment is **72 hours**, superseding the earlier 21-day
proposal. It has not started. Start only after (1) a provider-qualified active
referral path, (2) a verified external discovery path to that flow, and (3) real
measurement access are all ready. Record the actual start time then, never
backdate it to a code merge or internal probe. Hold scope steady throughout.

Daily private evidence report (existing database only):

```sh
python scripts/referral_daily_status.py --db /PRIVATE/events.sqlite --day YYYY-MM-DD --no-probe
```

The daily public Actions job has **no private evidence database**. Its null totals
are unavailable data, not a zero-user result. Keep it for availability checks; do
not put customer/provider evidence or credentials into public workflow artifacts.
Private evidence distinguishes `arrival`, `request`, `referral_handoff`,
`referral_click`, `registration_confirmed`, `attributed_transaction`,
`commission_pending`, `commission_approved`, `commission_reversed`, and
`payout_received`. A displayed link is not a click, a click is not a signup, and
a sale is not a commission or cash payout. Deduplicate opaque provider event IDs.
Unknown, owner/internal and ALLUBI origins stay separate. A forum's cumulative
view count cannot be assigned to today's independent arrivals. Even recorded
zero events leave total unknown until measurement coverage is actually complete.

After 72 hours, diagnose the earliest measurable drop: no qualified reach,
setup/fit failure, no provider handoff, signup/attribution failure, no paid need,
or commission hold/payout threshold. Missing data is a measurement blocker,
not evidence of no demand. Do not add providers or features to explain it away.
