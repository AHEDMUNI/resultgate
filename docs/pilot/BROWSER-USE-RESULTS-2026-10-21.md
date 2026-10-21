# Browser Use actual single-task result — 2026-10-21

## Outcome and scope
One real hosted Browser Use AI browser-agent task completed through ResultGate's
opt-in Python trial adapter. A requesting-agent test harness invoked the adapter;
this was not a default MCP tool invocation or an independent customer's request.
The agent inspected https://httpbin.org/html and returned structured facts.
ResultGate independently fetched and parsed the public page before dispatch.
All three typed checks passed: empty document title, first heading
"Herman Melville - Moby-Dick", documentation-example flag false.

This proves a bounded real external-agent delegation, not a shared production
marketplace, broad agent reliability, independent adoption or commission entitlement.
No commercial agreement, payment or commission was created.

## Authorization and secrets
Owner explicitly confirmed $1.00 promotional credit, no card and no auto recharge,
and authorized exactly one task. Credential was supplied through repository Actions
secret BROWSER_USE_API_KEY, never task content or committed source.
No purchase, recharge, public hosting, release or PR merge occurred.

## Evidence and non-duplication
- Actual task workflow: https://github.com/AHEDMUNI/resultgate/actions/runs/39539183887
- Cleanup/reconciliation: https://github.com/AHEDMUNI/resultgate/actions/runs/39539621527
- Provider run: c73bb06a-6d66-407a-99a1-c949ad519932
- Agent session: f148cb66-d9ad-4718-8c6a-df41e552b858
- Client create_attempts = 1; provider session numRuns = 1 both before and after cleanup.
- Repeating the adapter call against the same journal returned the saved record
  with no additional create. Cleanup transport permitted only GET/PATCH and
  submitted zero tasks. The consumed one-shot workflow is now disabled.
- Earlier workflow 39538823191 failed the fixture precondition with zero create
  attempts: example.com had no H1. Public fixture was changed to httpbin /html.
  No agent task was executed in that failed setup attempt.
- These observations prove no duplicate in this authorized trial, not global
  deduplication across unrelated journals or accounts.

## Cleanup defect found and corrected
The live task output verified, but its workflow failed because browser cleanup
incorrectly used the agent session ID as the browser ID. The corrected code lists
browsers filtered by agentSessionId, validates every binding and pagination count,
uses actual browser IDs, and verifies stopped state. Tests now use distinct IDs.
Read/stop-only reconciliation confirmed browser_stopped=true, active_sessions=0.
It did not rerun the agent. The original red workflow remains part of the evidence;
it has not been relabeled as successful.

## Recorded usage after cleanup
Provider usage observed at 2026-10-21T03:37:54Z:

| Item | USD |
|---|---:|
| Model usage | 0.004661 |
| Browser | 0.001000 |
| Proxy | 0.000010 |
| Search | 0.000000 |
| Session total (provider rounded) | 0.005671 |
| Credit before | 1.0000000000 |
| Credit remaining | 0.9943291611 |
| Balance debit (higher precision) | 0.0056708389 |
| Cash purchased/paid by this test | 0 |

Earlier active-session snapshot was $0.084661 with $0.915339 credit; it was
provisional, not final settled usage. The later usage and credit debit agree to
the provider's six-decimal cost rounding. Usage is not a final invoice.
Although residential proxy was disabled, provider reported the small proxy charge
above; do not claim zero proxy cost. The model budget was not an all-in hard cap.

## Verification and limits
232 local unit/integration tests passed after the cleanup correction; focused
Bandit scan of the adapter found no issues. PR CI additionally builds/installs
the package and exercises existing tools without live Browser Use calls.
See the latest PR checks for their actual status.

No independent external user, commercial referral or revenue is established.
The one-task authorization is consumed. Any further hosted agent task requires
fresh authorization. Default MCP tools and published 0.2.0 remain unchanged.

