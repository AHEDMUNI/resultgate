# BrowserAct referral demo — operator guide

Status: read-only local MCP companion; no BrowserAct execution by ResultGate, no live payments, no affiliate enrollment. Existing hosted `/mcp` remains simulation. Do not expect the new tools on that endpoint. Use this companion via stdio now; publication of the static guide is separate from a runtime update.

## Install and connect

Use Python 3.11+ and the reviewed revision of this repository. From its root:

```sh
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m resultgate.browseract_demo
```

The last process speaks MCP stdio and waits for an MCP client, not keyboard input. Configure Cursor / a compatible MCP client using **absolute paths** (Windows: `.venv\\Scripts\\python.exe`):

```json
{"mcpServers":{"resultgate-browseract":{"command":"/ABSOLUTE/resultgate/.venv/bin/python","args":["-m","resultgate.browseract_demo"]}}}
```

No token is required for this local process; it has no network listener. Tools: `assess_browseract_fit`, `validate_browseract_csv`, and `validate_browseract_report`. Never paste provider API keys into either tool. Public production `/mcp` authorization is unchanged.

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
