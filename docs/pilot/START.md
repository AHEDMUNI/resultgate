# ResultGate local pilot: start here

Unreleased PR #1. No hosted network, payments or complete A2A transport. You can try the public source without waiting for a PyPI release. Python 3.11+ and Git required; Linux/macOS commands below (Windows: use `client\Scripts\python.exe`). Package installation downloads dependencies; runtime has no external calls by default.

## Install in a new environment

```sh
git clone --branch feature/agent-brokerage --single-branch https://github.com/AHEDMUNI/resultgate.git
cd resultgate
git rev-parse HEAD
python3 -m venv client
client/bin/python -m pip install .
client/bin/python -m pip check
client/bin/python -I -m resultgate.pilot_client --offline
```

Tested source snapshot for this guide: `83e730aef7c7479dda6da4304f896df8769d94f1`. Record and review the printed SHA. The branch is mutable; repeat with `git checkout YOUR_REVIEWED_SHA` before installing when reproducibility matters. Do not use `pip install resultgate-pilot` expecting this pilot: the published release is older. CI also installs the exact pushed Git commit directly into a separate environment and runs this packaged command. The offline tutorial discovers17 tools and verifies that a fixture submission remains pending; it sends nothing to providers and counts as internal testing.

## Connect an independent MCP client

Copy [safe default configuration](../../examples/mcp-pilot.json); replace the absolute Python path. It exposes12 tools (2 original, 5 brokerage, 5 delegation). `tools/list` discovers descriptions and input schemas. No operator interaction is needed for each built-in permitted task. Optional provider submission tools need `--provider-registry /YOUR/PRIVATE/DIRECTORY` (17 total); the registry belongs to that local installation, not a shared hosted network.

1. Call `discover_agents` with `{"required_capabilities":["citation_structuring"]}`. GROBID is a specialist ML demo, not an autonomous AI agent. Claix is listed as unexecuted and cannot be routed.
2. To try exactly one free public-citation task, use [demo configuration](../../examples/mcp-pilot-demo.json). The operator flag permits external execution; each call still requires explicit consent. This example is classified internal. Do not provide private documents, keys or personal data.
3. Call `prepare_delegation` with:

```json
{"request_id":"my-public-demo-001","task":{"description":"Structure the public GROBID documentation example","required_capabilities":["citation_structuring"],"citation":"Graff, Expert. Opin. Ther. Targets (2002) 6(1): 103-113","expected_surname":"Graff","expected_year":2002}}
```

4. Save the returned `id`. Call `execute_delegation` with that `task_id`, exactly the same `task` object, and `consent_to_send_public_citation:true`. No content is sent by preparation alone.
5. Call `delegation_status` with `{"task_id":"RETURNED_ID"}`. `verified` means surname/year checks passed, not full semantic correctness. Output remains untrusted. `failed` or `outcome_unknown` is not success; do not automatically retry with new IDs. Reuse the same request ID/spec to avoid unintended duplicate execution. `cancel_delegation` cancels locally; remote synchronous work cannot be interrupted.

For the complete reproducible tutorial from the installed package:

```sh
client/bin/python -I -m resultgate.pilot_client --live
```

This opts into a public demo request and reports verified/error state, response hash, restart recovery and dedup. It is **internal acceptance even when run by another person**; it is not itself a real independent customer task. GROBID permits demonstration only, may sleep/fail, and is not production infrastructure. Provider reviews expire after30days from2026-10-20; expired reviews intentionally block execution until re-reviewed. No auto renewal.

## Optional records, feedback and deletion

Default task state is in memory. For your own real permitted tasks, opt in with `--delegation-store /YOUR/PRIVATE/DIRECTORY`; omit `--internal-delegation-tests` only for real non-test work. This produces `external_unverified`, never automatic independent verification. Private directory/file permissions are restricted; no upload and no raw task text in the store. Records expire lazily after30days. No claim of automatic adoption monitoring.

```sh
client/bin/python -I -m resultgate.pilot_usage --directory /YOUR/PRIVATE/DIRECTORY --export --consent
client/bin/python -I -m resultgate.pilot_usage --directory /YOUR/PRIVATE/DIRECTORY --delete-task TASK_ID
```

Export is opt-in stdout only: aggregate cohort counts, a stable per-installation pseudonym and no task content/IDs. Inspect it before sharing. If you redirect it to a file, protect/delete that file yourself. Pseudonyms permit comparing voluntary repeat reports from one installation, **not proving identity or independent use**; reports are not additive, and copied/replayed reports must never be summed. Verified independent use requires separately reviewed evidence of an unaffiliated user's real task and consent. Internal tutorials/CI must remain excluded. An empty store export is not usage. Different installations may belong to the same person.

Optional feedback: open a [new GitHub issue](https://github.com/AHEDMUNI/resultgate/issues/new) titled `[Pilot feedback]`, state internal tutorial / unaffiliated installation / unaffiliated real task, and share only an aggregate report or non-sensitive problem. No submission is required to use the package. Issues are public and linked to your GitHub account; this is not anonymous telemetry. Do not post secrets or task content. Edit/remove content or request issue deletion from the maintainer; GitHub/backups/third-party copies are outside local30day retention. Templates are prepared in PR and will enter the chooser only after the default-branch merge is approved. No automatic harvesting of issues is enabled.

A2A: declared provider protocol fields and custom discovery metadata are preparation only; ResultGate does not implement a conforming public A2A AgentCard/transport. Use MCP stdio.
