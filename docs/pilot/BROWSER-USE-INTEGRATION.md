# Browser Use one-shot integration — executed once

This PR adds a narrow Python agent-callable trial adapter, not a new default MCP
tool, public server, A2A implementation or commercial integration. Browser Use
provides a hosted browser agent via its documented API; the adapter delegates a
fixed task, it does not itself browse the target in place of that agent.

## Credential input and read-only preflight

Revoke any key pasted into chat. Generate a replacement in Browser Use, then
enter it yourself in GitHub repository Settings → Secrets and variables → Actions
→ New repository secret, name `BROWSER_USE_API_KEY`. Do not send it in chat, commit
it, screenshot it, use it as a URL parameter, or include it in a command argument.
Only explicitly reviewed trial workflows read the key. The separate `browser-use-preflight.yml` runs
only on the dedicated `trial/browser-use-preflight` branch and makes one billing
GET; it cannot dispatch a task. Logs show eligibility booleans, not names, project
IDs, keys or exact balances. Creating a secret does not itself trigger execution.
Only trusted, reviewed workflow code may receive this secret. Delete the secret
and revoke the key after testing if no longer needed. No repository secret was
created by the assistant in preparing these files.

For a local operator instead, set the same environment variable through a secret
manager or an interactive non-echoing terminal prompt. Never use shell tracing.
Do not export the key to any requesting agent's prompt or provider task body.

Official sources checked: [V4 OpenAPI](https://docs.browser-use.com/cloud/openapi/v4.json),
[V2 billing schema](https://docs.browser-use.com/cloud/openapi/v2.json),
[pricing](https://browser-use.com/pricing), and
[V4 guide](https://github.com/browser-use/browser-use/blob/main/skills/cloud/references/api-v4.md).
The current guide advertises eligible social signup promotional credit; some
older documentation advertises different amounts. Account eligibility and actual
balance must be checked, not inferred from signup. Billing API free-tier/balance
fields do NOT establish credit origin, absence of a saved card or recharge status.
Owner/account review must establish those separately. Stop if unconfirmed.

## Execution after account review only

```sh
python -m resultgate.delegation.browser_use_trial preview
python -m resultgate.delegation.browser_use_trial preflight --directory /PRIVATE/browser-use-trial
python -m resultgate.delegation.browser_use_trial run --directory /PRIVATE/browser-use-trial --consent-public-task --confirm-free-no-card-no-recharge
```

The confirmation flags represent a genuine prior account review; do not set them
merely to get past a guard. The free-tier API must report at least $0.50 credit
and no active browser sessions. Neither this threshold nor `maxCostUsd=0.10` is
a guaranteed all-in billing cap. No paid balance, card, automatic top-up, payment
integration or personal profile is authorized. The guide's free-eligible model
`gpt-5.6-luna` is explicitly selected instead of the newer default; do not upgrade
a rejected model automatically.

The fixed task requests only httpbin.org/html's title, first heading and whether it
is for documentation examples. No private task input is accepted. ResultGate
independently fetches the same fixed public page without credentials, fixes the
success criteria before dispatch, delegates the task to Browser Use, polls,
checks run/session identity, and compares typed output fields. It stores hashes
and checks instead of the result body. This establishes agreement with a public
fixture if run successfully; it does not establish absence of hallucinations in
general or market demand. No credentials, email, uploaded files, browser profile,
wallets or integrations are attached; residential proxy and recording are off.

A private SQLite journal reserves one dispatch slot atomically BEFORE POST.
Repeated calls, process restart and ambiguous create failures never issue another
POST from that journal. Do not delete/copy journals or use a new directory/machine
to retry: this is local durability, not global account-wide deduplication. If a
create response is lost, inspect the provider account and cancel any orphan before
proceeding. There is no automatic API create retry or unauthenticated x402 fallback.
The local journal intentionally does not expire: deleting it destroys replay safety.
It contains internal task IDs, timestamps, hashes and usage records, no API key.

```sh
python -m resultgate.delegation.browser_use_trial reconcile --directory /PRIVATE/browser-use-trial
```

Reconcile never creates a task. On a bounded polling timeout or connection failure,
it requests cancellation; it explicitly stops the session browser and checks its
state. Cleanup failure remains visible and requires intervention. A killed process
or total network loss can still leave provider resources alive; resume reconciliation
or stop them in the provider UI. A client timer cannot guarantee billing cessation.
Read session cost again after settlement: recorded usage is not an invoice, the
free-credit debit or cash paid. `verified` means output checks passed; it does not
imply the browser stopped, costs finalized or a commission exists.

## Current evidence

One authorized task completed and all three independent output checks passed.
Browser cleanup was corrected and verified separately, with zero active sessions.
See [the actual execution report](BROWSER-USE-RESULTS-2026-10-21.md) for cost,
non-duplication evidence, workflow links and limitations. This was an internal
external-agent integration, not independent adoption. The authorization has been
consumed; do not execute the run commands again without fresh authorization.

## Authenticated preflight update

The read-only GitHub Actions preflight run 39537374520, retry job 119020447273,
succeeded after the owner saved the repository secret. The authenticated provider
response established free-tier status, at least $0.50 credit and no active sessions.
The account dashboard separately displayed $1.00 credit and no prior runs.
No secret value was read or exported. No agent task was submitted.

The API cannot establish promotional origin or recharge configuration. The Billing
page showed Tier 0 and first-purchase checkout information but did not expose an
explicit no-card/no-auto-recharge status. Invoice-page observation was blocked by
browser credential protection. The owner subsequently explicitly confirmed promotional credit, no card and no
auto recharge, and authorized the single task documented in the result report.

Evidence: https://github.com/AHEDMUNI/resultgate/actions/runs/39537374520
This is a genuine authenticated API check, not agent execution or independent use.
