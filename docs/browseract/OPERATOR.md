# BrowserAct referral demo — operator guide

Status: read-only local MCP companion; no BrowserAct execution by ResultGate, no live payments, an owner-issued affiliate link exists, but AI/MCP eligibility remains unconfirmed and the public handoff remains untracked. Existing hosted `/mcp` remains simulation. Do not expect the new tools on that endpoint. Use this companion via stdio now; publication of the static guide is separate from a runtime update.

## Start here: no purchase, provider account or API key

Prerequisites: Git, Python 3.11 or newer, and Cursor for the interactive step. Cursor's own model access may have its own usage limits; the offline check below needs no model account. This example reuses the original internal CSV; it does NOT run BrowserAct or fetch product pages.

In a terminal clone this repository, then install:

```sh
git clone https://github.com/AHEDMUNI/resultgate.git
cd resultgate
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe scripts/browseract_demo_check.py
(Resolve-Path .\.venv\Scripts\python.exe).Path
```

macOS/Linux:

```sh
.venv/bin/python -m pip install .
.venv/bin/python scripts/browseract_demo_check.py
pwd
```

Expected: `status: passed`, `rows: 20`, `decision: free_first`, `origin: internal`, `provider_run_started: false`. The command launches and closes a real local MCP process. It does not certify current prices or independently verify the old provider run.

Configuration follows https://cursor.com/docs/mcp (checked 2026-10-22). Open the cloned folder in Cursor. Create `.cursor/mcp.json` in that folder (merge this entry if the file already exists). Replace the command with your absolute Python path from above; Windows JSON paths must use `/` or escaped `\\`:

```json
{"mcpServers":{"resultgate-browseract":{"type":"stdio","command":"C:/Users/YOU/resultgate/.venv/Scripts/python.exe","args":["-m","resultgate.browseract_demo"]}}}
```

macOS/Linux command example: `/Users/YOU/resultgate/.venv/bin/python`. Enable this server in Cursor's MCP settings and verify these three tools appear: `assess_browseract_fit`, `validate_browseract_csv`, `validate_browseract_report`. Do not run the server manually in a terminal: stdio waits silently for its client.

Paste this into Cursor Agent chat, allowing the local tool calls when prompted:

> Read examples/browseract/accepted/mcp-input.json. This is archived INTERNAL practice data, not a fresh scrape. Call assess_browseract_fit with request.product_urls equal to payload.expected_urls, sources_permitted=true and local_execution_sufficient=true. Then call validate_browseract_csv using the entire JSON object from the file as the tool arguments (including its payload wrapper). Do not open BrowserAct, fetch sites, request keys or run a paid task. Show the decision, expected and received counts, missing/errors, original first price, preserved timestamp and provenance limits. Do not claim a new extraction, customer or commission.

The example has 20 fictional books, all accounted for, original first price `£51.77`, and recorded time `2026-10-22T00:39:41Z`. That is the saved run's timestamp, not today. Values are preserved alongside normalized fields. No automatic telemetry is sent.

Troubleshooting: if tools are absent, check the absolute executable path and reload the MCP server; if `ModuleNotFoundError` appears, reinstall with that exact interpreter. If Cursor cannot read the fixture, open the cloned repository as the project. If the call fails, save the error with secrets removed; do not buy credits to repair this offline demo.

## Complete one task

1. User supplies up to 20 public HTTPS product pages and confirms permission. Prefer an authorized existing API/export when available. This pilot excludes login, sensitive data, purchase actions and bypassing access controls.
2. Ask `assess_browseract_fit` with `request.product_urls`, `sources_permitted:true`, and truthful flags `existing_api_or_export`, `local_execution_sufficient`, `recurring_cloud_need`. A rejection/API recommendation ends the BrowserAct path. Free-first is a real outcome, not a forced upsell.
3. Review returned price, recurring billing, limits and disclosure. Follow the official link. **It is currently untracked.** No affiliate commission is implied. Free credits do not guarantee completion of 20 products.
4. Customer connects BrowserAct to their own agent through https://www.browseract.com/integrations or uses https://www.browseract.com/docs-api . Credentials stay with that customer. In BrowserAct create a workflow from the returned task; review estimated credit use. Owner approves one run and maximum credits, separately from any subscription approval. No scheduled runs.
5. Run via official integration. BrowserAct API supports workflow execution using the provider workflow ID and input parameters; follow current official request schema rather than inventing an ID. Stop using its official stop control if the budget cannot be enforced. Do not run when a spending cap cannot be assured.
6. Export one JSON row per URL with `source_url, product, price, currency, availability, checked_at, error`. Price is a decimal string; availability is `in_stock`, `out_of_stock`, `preorder`, or `unknown`. Missing values are null with an error, not guessed values.
7. Inspect completeness of **all** 20 rows with `validate_browseract_report`: expected URLs + rows + five separately observed samples (positions 1,5,10,15,20). Include `origin:independent_unverified`, `engine:browseract` only if actually run. Tool does not verify the claimed engine or caller identity. Save the provider run ID and execution evidence privately; don't upload private keys, cookies or customer data to GitHub.
8. User sees a source-linked price/stock report with UTC timestamps, missing/failed rows and sample mismatches. A pass checks structure and supplied observations, not universal factual correctness.

## Reproducible internal reference

`python scripts/browseract_reference_run.py examples/browseract/reference`

Only fetches `books.toscrape.com`, a public scraping practice site. Its fictional books/prices are **test data**, not commercial offers. Saved HTML hashes preserve observations. Engine is direct HTTP, not BrowserAct. Fixed five-page re-fetch checks parser consistency; an independent person still needs to compare those pages visually. No cost or referral conversion is produced.

## Fair timing comparison (not yet measured)

Use two equivalent permitted 20-URL sets. Same operator, clean configuration, same BrowserAct plan and client. Randomize direct-first vs ResultGate-first across operators to reduce learning bias. Start clock before reading/setup; stop at a usable validated report. Record setup seconds, execution seconds, repair seconds, manual interventions, completeness, errors, credits consumed and consent interruptions. Direct baseline gets official docs but not ResultGate task/schema. Assisted path gets this tool. Don't count internal script runtime as human setup or claim savings from unmeasured times. Acceptance: no reduction in accuracy, all 20 accounted for, five matched samples, assisted setup no slower than direct; otherwise revise task/instructions once.

## Evidence-only measurement

`python -m resultgate.referral_measurement --db /PRIVATE/events.sqlite`

Optional operator-import event file via `--event /PRIVATE/event.json`. Each event requires unique stable `id`, `kind`, `origin`, opaque `subject`, and `evidence_ref`. Example internal event:

```json
{"id":"internal-run-1","kind":"usage","origin":"internal","subject":"operator-test","evidence_ref":"run-report-1"}
```

Kinds separate arrival/request/usage/referral_handoff/registration_confirmed/commission_approved/commission_reversed/payout_received. Default uncertain visitors are unknown, never independent. ALLUBI stays allubi. Operator must review provenance before independent_verified. Access logs prove requests, not people or agent independence; exclude bots, probes, internal IPs/identifiers using private records. Approval requires provider statement; payout requires remittance/receipt. Deduplicate using provider event IDs. Never expose this import command as a public endpoint. Retain minimal private evidence 30 days unless legally required; delete obsolete evidence and its local DB together. No automatic external telemetry is enabled.

## Accepted BrowserAct CSV workflow

The original owner-supplied export is `examples/browseract/accepted/result.csv`; validation and evidence limits are in the adjacent `validation.json`. Use `validate_browseract_csv` with `payload.csv_text` (unmodified CSV), `payload.expected_urls` (from the approved task, not inferred from results), and `payload.origin` (`internal` for this experiment). The adapter keeps all original strings and a SHA-256, maps field names, parses unambiguous decimal price text, and maps explicit stock labels. Displayed £ remains £ with `currency_iso:null`; it must not be used as payment currency. Unknown values become errors rather than guesses.

A stdio client invocation after initialization:

```python
result = await session.call_tool("validate_browseract_csv", {"payload": {
    "csv_text": original_csv_text,
    "expected_urls": approved_product_urls,
    "origin": "internal"
}})
```

Install the merged version, not an older PyPI release. New local checkout:

```sh
git clone https://github.com/AHEDMUNI/resultgate.git
cd resultgate
git rev-parse HEAD
python -m venv .venv
.venv/bin/python -m pip install .
```

On Windows replace `.venv/bin/python` with `.venv\\Scripts\\python.exe`. Use that absolute executable path in MCP configuration above. Do not run an unbounded paid workflow. The actual accepted experiment covered 20 cards on ONE homepage, not 20 page visits. Existing reference timing is not a fair direct-vs-assisted setup comparison. No rerun is required to validate this accepted CSV.
