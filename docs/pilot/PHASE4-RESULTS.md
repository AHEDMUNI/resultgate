# Phase 4 — local pilot launch review

Review date: 2026-10-20 America/Chicago (CI receipts use UTC2026-10-21). Continued from48b8a479f3f4254c8d4b98e2a1beb7046497eae9 on existing PR#1; no new repository/project. Main remains unchanged; no release, hosting, payments, outreach or commercial acceptance.

## Delivered

- GitHub provider application and voluntary pilot-feedback issue forms prepared, with public-data warnings and no self-approval or commercial consent checkbox. Issues already enabled. Until approved default-branch merge, applicants can follow the documented manual new-issue path; forms are not claimed live in the chooser.
- Local operator import of strict public Submission JSON; separate expiring domain-challenge review, identity/terms review, explicit agreed terms and execution-adapter gate. Revocation now clears agreement consent, preventing silent restoration on reapproval. No automatic issue execution or URL fetch.
- One start guide, ready-to-copy safe/demo MCP configs, packaged runnable offline/live client example. Existing17-tools maximum unchanged; original2/7/12 modes preserved. A2A explicitly incomplete.
- Optional consented local aggregate usage export and task-deletion CLI. Installation pseudonym enables comparing repeat voluntary snapshots, but cannot prove identity/independence. No upload. Reports default self-reported/unverified; internal tutorial/CI never adoption. Public issue retention distinguished from local30days.
- Provider-facing offer, review-only commission worksheet (no signed/accepted terms), security review and official-source free deployment comparison.

## Validation

Local full suite: **168 passed**, including the164 prior tests and4 new checks for consent/minimal export/scoped pseudonyms/revoked agreements. Bandit: no findings. pip-audit tested requirements: no known vulnerabilities. Wheel/sdist build and strict Twine passed; fresh installed environment pip check passed. JSON MCP configs and YAML issue forms parsed locally. Installed offline17-tool client passed. Installed consent CLI refused export without consent before creating a store; consented output contained aggregate counts only and no independent-use claim.

CI: **success** on source83e730aef7c7479dda6da4304f896df8769d94f1. [Push run39526772040](https://github.com/AHEDMUNI/resultgate/actions/runs/39526772040) passed all168 tests, Crossref/DataCite/GROBID live calls, wheel acceptance and direct public-source installation. PR run39526777298 also passed. The final public-source client returned GROBID state verified at2026-10-21T01:21:53Z, discovered17 tools, restored state after restart and suppressed duplicate dispatch. [Receipt](acceptance-evidence.json). New CI installs the exact public Git commit into a separate venv, changes cwd to /tmp and runs packaged offline/live examples with Python -I. No imported development tree. Existing DOI/GROBID and wheel acceptance remain. These are internal tests, regardless of remote runner.

## Blockers ordered by impact

1. **Discoverable reviewed distribution:** brokerage remains in draft PR, not published package/default docs. Source installation is usable now; owner-approved merge/versioned release improves discoverability. No hosted service needed for local independent evaluation.
2. **No confirmed independent real task:** repository issue inspection found no non-PR submissions at review time. Local installations are not centrally observable. Need an unaffiliated user voluntarily supplying evidence of a real permitted task; do not count our tutorial, download totals, CI or invented applicants.
3. **No commercial provider agreement:** candidate programs do not establish permitted agent-origin attribution. Owner/provider must explicitly approve complete terms and paid-event reconciliation before any commercial claim. No outreach authorized/performed.
4. **New-provider execution:** provider application/review is operational locally but does not install an adapter. A reviewed adapter, free entitlement and execution acceptance test are still necessary. Existing GROBID demo is not a production autonomous agent.
5. **Shared service:** tenant auth, quotas, durable hosted storage, safe automated ownership verification and operational policy remain absent. Do not expose the current local server as production. Reviews expire30days after2026-10-20 and must be renewed with evidence before subsequent execution.

## Release recommendation and decisions

Approve a **local-source pilot first**, using existing public GitHub repo/docs and Issues, with user-owned runtime and no central processing bill. Then authorize merge and a separately reviewed versioned PyPI/MCP publication if desired. Optional Pages only as documentation; not necessary now. Render free is unsuitable for persistent SQLite and production reliability (see DEPLOYMENT.md).

Owner decisions: (1) whether to merge this reviewed PR into main; (2) whether to publish a newly versioned local package and updated Registry metadata; (3) whether to authorize a specific provider partnership inquiry later. No approval for payment/contract acceptance is inferred. No need to purchase hosting, create a paid account or provide a key for the existing free demo.

Verified independent use0; real commissions0; revenue$0; spending$0. Tests use public fixtures and simulated agreements only. No background monitoring has been scheduled. Prepared materials do not themselves generate demand or establish a functioning public marketplace.
