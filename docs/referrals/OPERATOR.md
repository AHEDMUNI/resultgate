# ResultGate: six-provider selection pilot

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

The 21-day experiment starts only after the catalog is verified deployed and an authorized acquisition channel is actually live. Days 1–7: observe independently documented setup failures and qualified handoffs. Days 8–10: one bounded fix to the most evidenced bottleneck. Days 11–21: hold scope stable. Decide using observed funnel and attribution coverage; missing data is not zero demand. No daily-sales target is promised.
