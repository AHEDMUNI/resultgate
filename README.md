# ResultGate

<!-- mcp-name: io.github.AHEDMUNI/resultgate -->

Local MCP service recommendations for BrowserAct, SearchApi, PDF.co, Make, Apify and Firecrawl, with disclosed referral links and evidence checks. Release 0.3.0: [PyPI](https://pypi.org/project/resultgate-pilot/0.3.0/).

## Looking for service recommendations?

Install the versioned package through uv (Python 3.11+; no Git required):

```json
{"mcpServers":{"resultgate-referrals":{"command":"uvx","args":["resultgate-pilot==0.3.0","--referrals"]}}}
```

This local stdio entry exposes exactly six tools:
`list_referral_providers`, `recommend_referral_service`, `prepare_referral_task`,
`assess_browseract_fit`, `validate_browseract_report`, `validate_browseract_csv`.
The first three cover all six providers. No keys, registration or purchases are
needed; installing dependencies needs network access, but tool calls do not
execute providers or upload telemetry. Existing/local/free solutions take priority;
commission never affects capability matching.

Example journey: call `list_referral_providers`, then `recommend_referral_service`
with `request={"need":"browser_interaction","sources_permitted":true,
"local_solution_sufficient":false}`, then `prepare_referral_task` with
`request={"provider_id":"browseract","sources_permitted":true}`.
The response includes the official affiliate URL
`https://browseract.com?fpr=ahed-ddc97e`, the measured `/go/browseract` alternative
and commission disclosure. A handoff is not a registration, sale or commission.

After `pip install resultgate-pilot==0.3.0`, `resultgate-referrals` is an equivalent
standalone entry; `resultgate-pilot --referrals` is the Registry entry.
The original `resultgate` / `resultgate-pilot` defaults and brokerage flags remain
available for existing clients. The old 0.2.0 release lacks referral tools.

The [public catalog](https://agents.allubiyerbamate.com/referrals) is readable
without an account. Hosted `/mcp` is a separate authenticated gateway, not this
local companion. An unauthenticated 401 there does not mean this local server is
down. Never disable gateway authentication to satisfy a directory health check.
Glama schema refresh and MCP Registry publication are separate from package publication.

[Examples and permission flags](docs/referrals/OPERATOR.md) ·
[Privacy and counters](docs/referrals/MEASUREMENT.md) ·
[0.3.0 release/migration notes](release/0.3.0.md).

**A pass is not a truth guarantee.** The original checking tools evaluate the evidence you supply; they do not fetch sources, detect every missing fact, verify source authenticity, or judge semantic support. Incomplete completion evidence returns `unknown`.

## Install from PyPI (Python 3.11+)

```sh
python3 -m venv .venv
.venv/bin/python -m pip install resultgate-pilot==0.3.0
.venv/bin/resultgate-pilot --help
```

For MCP clients with uv installed: `uvx resultgate-pilot==0.3.0`.

## Install from GitHub (Python 3.11+ and Git)

```sh
python3 -m venv .venv
.venv/bin/python -m pip install git+https://github.com/AHEDMUNI/resultgate.git
.venv/bin/resultgate --help
```

For reproducible deployments, append `@<reviewed-commit-sha>` to the Git URL.

## Install from a locally built wheel

On Linux/macOS, after reviewing the artifact and its SHA-256:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install ./resultgate_pilot-0.3.0-py3-none-any.whl
.venv/bin/resultgate --help
```

On Windows use `py -m venv .venv` and `.venv\Scripts\python.exe -m pip install <wheel>`; the executable is `.venv\Scripts\resultgate.exe`. Windows/macOS execution has not yet been tested in this release review.

The public package exposes both `resultgate` and `resultgate-pilot` executables.

## Connect an MCP client

Configure the absolute installed executable; it runs locally over stdio, without API credentials:

```json
{"mcpServers":{"resultgate":{"command":"/ABSOLUTE/PATH/.venv/bin/resultgate"}}}
```

Discoverable tools: `check_extraction` and `check_citations`. Each accepts `payload` and an optional `usage` object. Tool input/output schemas are exposed by the official Python MCP SDK. The default makes no network requests and records no usage. This local server trusts the invoking OS user; it is not a sandbox for untrusted processes.

### Enable brokerage and delegation

```json
{"mcpServers":{"resultgate":{"command":"/ABSOLUTE/PATH/.venv/bin/resultgate","args":["--brokerage","--delegation"]}}}
```

This exposes 12 tools while keeping external execution disabled. The 0.3.0 Registry configuration instead launches the standalone `--referrals` mode. Local provider onboarding adds 5 tools with an explicit private registry directory. See the [installed-client tutorial](https://github.com/AHEDMUNI/resultgate/blob/main/docs/pilot/START.md) and [provider application process](https://github.com/AHEDMUNI/resultgate/blob/main/docs/pilot/PROVIDERS.md). No shared hosted network, conforming A2A transport, automatic provider execution or payments. GROBID is an opt-in ML demo, not an autonomous agent.

### Extraction example

```json
{"payload":{"records":[{"id":"a","name":"Example"}],"required_fields":["/name"],"unique_fields":["/id"],"expected_count":1,"job_status":"completed","next_cursor":null,"truncated":false}}
```

Expected status: `pass`, scoped to `caller_supplied_contract_only`.

Fields use RFC6901 JSON pointers; `unique_fields` forms a composite key. Missing/null/blank required fields fail; zero and false are valid. Counts refer to the entire supplied dataset, not pages or provider jobs. An expected total must come from an appropriate external contract, not simply `len(records)`. Known failure, scraping-in-progress, pending cursor, repeated cursor, explicit truncation, count mismatch and duplicate keys fail. Missing expected count, completion state, next-cursor evidence or truncation evidence yields unknown when there is no definite failure. Null is allowed only for `next_cursor`; omit unknown expected_count/truncated instead.

Limits: 1 MiB serialized input, 100,000 JSON nodes, depth 32, 5,000 records and 64 pointers per field list. Up to 100 findings are returned, with total count.

### Citation example

```json
{"payload":{"sources":[{"id":"s1","text":"The launch was postponed."}],"citations":[{"source_id":"s1","quote":"The launch was postponed.","start":0,"end":25}]}}
```

Exact literal Unicode matching only. Optional offsets must be paired and count code points, not bytes or UTF-16 units. A matching quote may still be misleading or used to support a false claim. Empty citations produce unknown. Duplicate source IDs are rejected. Search work is limited to 20 million source characters across searches without offsets; split larger requests or supply exact offsets. No URLs are fetched or instructions in source text executed.

## Optional authenticated local HTTP API

```sh
export RESULTGATE_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
.venv/bin/resultgate --http
curl -H "Authorization: Bearer $RESULTGATE_API_TOKEN" -H 'Content-Type: application/json' --data-binary @examples/extraction.json http://127.0.0.1:8765/v1/extraction
```

POST `/v1/extraction` and `/v1/citations` accept the payload itself, without the MCP `payload` wrapper. GET `/health` is informational. HTTP mode binds to loopback, requires a configured secret for audits, rejects browser Origins/unrecognized Hosts, limits body size and read time, and disables access logs. It is not a public hosted API or a remote MCP endpoint. Do not publish it through a tunnel or reverse proxy. HTTP usage measurement is not implemented.

## Privacy-preserving, opt-in local measurement

No analytics by default. To opt in for a voluntary pilot, add `--usage-dir /YOUR/PRIVATE/DIRECTORY` to the MCP command, then pass `usage:{"task_id":"opaque-task-identifier","purpose":"real_task"}` when a real task uses a check. Reuse task IDs on retries. Test/demo/retry purposes and calls without a usage context are excluded. See [PRIVACY.md](PRIVACY.md).

Export for your own review with `.venv/bin/python -m resultgate.local_usage /YOUR/PRIVATE/DIRECTORY --export`. Nothing uploads automatically. Shared summaries are self-reports; they are not automatically counted as independent adoption or revenue.

## Development and limitations

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python benchmark.py
```

Unit and clean-install tests are internal. Synthetic benchmark fixtures measure rule coverage, not production accuracy or superiority over complete competing products. Tests use no paid models, browsers or APIs. Python 3.12/Linux is the tested clean-install environment. The referral entry does not start a hosted endpoint or payments; these tests do not establish external customers.

License: MIT, included in LICENSE. See SECURITY.md for security scope and THIRD_PARTY.md for dependencies.

Optional local pilot: [provider onboarding, discovery and commission receipt pilot](docs/NETWORK.md). Optional 17-tool configuration; no hosted network, A2A endpoint or payments. [Partner diligence](docs/COMMISSION-PARTNERS-2026-10-21.md).

Local pilot: [start/install/MCP examples](docs/pilot/START.md) · [provider application](docs/pilot/PROVIDERS.md) · [review-only commission worksheet](docs/pilot/AGREEMENT-DRAFT.md). No public shared runtime or automatic provider approval.

## Optional marketplace simulation

ResultGate aims to broker authorized work between requesting and specialist agents. The published local pilot is not a shared marketplace. Current source includes read-only commission reports; new development must distinguish simulations, operator attestations, verified paid events and actual collected revenue. No subscriptions or listing fees are planned; commissions require explicit bilateral terms and qualifying outcomes.

See [agent integration and capability discovery](docs/pilot/AGENT-DISCOVERY.md), [shared-market prototype boundaries](docs/pilot/SHARED-MARKET.md), and [first commercial transaction gates](docs/pilot/COMMERCIAL-PATH.md). The 0.3.0 package includes these modules, but the referral entry never activates them.

A [loopback-only shared-store HTTP harness](docs/pilot/GATEWAY.md) is available on this development branch for isolated client tests. It records simulations, never executes provider tasks or payments, and must not be publicly exposed. [External specialist trial and cost controls](docs/pilot/EXTERNAL-TRIAL-QUOTE.md) identify a no-card first experiment and a separately approved paid fallback.
