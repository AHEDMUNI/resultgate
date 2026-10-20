# ResultGate

<!-- mcp-name: io.github.AHEDMUNI/resultgate -->

Local MCP tools for extraction-contract checks and literal citation integrity. Version 0.1.1 is published on [PyPI](https://pypi.org/project/resultgate-pilot/0.1.1/).

**A pass is not a truth guarantee.** ResultGate evaluates the evidence you supply; it does not fetch sources, detect every missing fact, verify source authenticity, or judge semantic support. Incomplete completion evidence returns `unknown`.

## Install from PyPI (Python 3.11+)

```sh
python3 -m venv .venv
.venv/bin/python -m pip install resultgate-pilot==0.1.1
.venv/bin/resultgate-pilot --help
```

For MCP clients with uv installed: `uvx resultgate-pilot==0.1.1`.

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
.venv/bin/python -m pip install ./resultgate_pilot-0.1.1-py3-none-any.whl
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

Unit and clean-install tests are internal. Synthetic benchmark fixtures measure rule coverage, not production accuracy or superiority over complete competing products. Tests use no paid models, browsers or APIs. Python 3.12/Linux is the tested clean-install environment. There is no payment code, hosted endpoint, or external customer count.

License: MIT, included in LICENSE. See SECURITY.md for security scope and THIRD_PARTY.md for dependencies.
