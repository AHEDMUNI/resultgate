# Phase 2 results — October 20, 2026 (America/Chicago)

PR #1 / feature/agent-brokerage, no main merge or registry/PyPI release.
This report supplements BROKERAGE-RESULTS-2026-10-20.md. Commercial model now is
success-only task commissions under explicit provider agreements; payment is off.

## Actual results

**A first delegation to an autonomous specialist AI agent has NOT been proved.**
We did prove a real remote specialist ML processing task, beyond data retrieval:
GROBID's official free demo parsed the public citation example into author,
journal and year. GROBID is a machine-learning service, not an autonomous agent.

The actual MCP client discovered the provider, prepared a task with fixed criteria,
consented to sending the public citation, dispatched a POST to the provider,
validated surname Graff + year 2002 and obtained state verified. A new MCP process
restored the persisted state, and duplicate execution did not send a second task.
The returned title was Expert. Opin. Ther. Targets. No personal document was sent.

Source run: https://github.com/AHEDMUNI/resultgate/actions/runs/39523054395
Code tested there: b3edf63c5731c186df52dcca13b57b4482b20a97
UTC timestamp: 2026-10-21T00:44:13.009055+00:00
Normalized response SHA256:
1a063a9d58eb47293b700f4bb92d9ced8a3d9fa8836ef9cfbc5559518b8de30c
Machine-readable receipt: delegation-live-evidence.json, copied from actual logs.
This is internal integration evidence, not provider-signed financial evidence.

Crossref and DataCite live integration also passed in this run. Original seven
tools still work; five optional delegation tools make twelve only with --delegation.
Default mode still exposes the original two tools. Shadow billing unchanged.

## Verification

- Baseline 114 tests rerun successfully before changes.
- 134 tests passed after changes, locally and in GitHub Actions.
- New cases: persistent restart and private content exclusion, cross-connection
  dedup, consent/conflict, cancellation before/during dispatch, timeout/unknown
  outcome, failure and criteria mismatch, crash recovery, fixed/percentage
  simulated commission, agreement/acceptance omissions, duplicate assessment,
  expiry, dispute/refund/void, cohort attestation and internal exclusion, deletion,
  XML/input safety, twelve-tool MCP compatibility.
- Commission fixture: fixed 250,000 micro-USD ($0.25) recorded once across three
  assessments; percentage 1,250 basis points of $20 = $2.50. All terms, acceptance
  and work in those cases are SIMULATED. No actual agreement or debt was created.
- Bandit final local scan: no findings. Replaced standard XML parser with pinned
  defusedxml 0.7.1 and removed dynamic SQL construction flagged during review.
- pip-audit of updated tested dependencies: no known vulnerabilities.
- Wheel build, Twine strict and fresh-venv pip check passed. Isolated installed
  acceptance passed in original two-tool, seven-tool and twelve-tool modes;
  persistence across two processes and disabled-network behavior verified.

## Commission readiness

Eligibility recording mechanics work under controlled tests: reviewed agreement
record, referral link, predetermined verification, result acceptance evidence,
unique task and absence of dispute/cancellation/refund are required. API success
alone creates no commission. Live GROBID result generated zero eligibility.

Only local trusted operator methods can attest independent use, record explicit
agreement evidence, accept results or assess commission. MCP cannot self-award
these statuses. Operator evidence hashes reference documents reviewed outside
this system; hashes do not themselves prove authenticity. All real commission
agreements and real eligible commission balances remain empty.

This is not ready for unattended commercial accrual: real provider/customer
acknowledgment verification, agreement review, task-value reconciliation and a
retention/idempotency policy for commercial records remain prerequisites. Claix
operator-attested agreement schema exists for future genuine evidence, but no
Claix account, key, adapter execution or agreement exists in this project.

## Discovery and blockers

An independent caller can install the public feature branch and use the tools.
Our installed client tests are not independent adoption. PyPI/MCP Registry still
contain the old release, and no autonomous discovery of this new feature has
been observed. The GROBID endpoint permits demonstrations only, so do not launch
it as a production commercial service or imply provider partnership.

Claix documents an A2A document agent and API-key-required execution, with trial
calls advertised. A user-controlled account, safe key provisioning and confirmed
free entitlement/terms are needed before trying it. No account was created or
terms accepted. AI SENSE's A2A utility endpoint explicitly has no language model;
it was not counted as a specialist autonomous AI agent. See DELEGATION.md sources.

Storage is opt-in, local, minimal and retained 30 days with lazy/explicit purge;
no background task was scheduled. Task content and results are not stored.
External_unverified is not independent_verified; operator evidence is required.
Counts are tasks, not unique people, and no independent repeat-use rate is claimed.
DOI legacy tracking remains session-only; the new delegation records persist.

## Next practical step

Obtain a user-controlled free provider trial (Claix is a documented candidate),
verify its account entitlement and data terms, implement that reviewed A2A adapter,
and run a synthetic document task. Then obtain approval for a free public release
and observe an external initiated task. A commercial referral additionally needs
an explicitly accepted success-commission agreement and independently checked
completion/customer acceptance. No subscription, listing fee or send fee is part
of the chosen model. Nothing has been billed, demanded or collected.

Independent uses: 0. Real commercial referrals: 0. Actual commissions: $0.
Revenue: $0. Money spent by this work: $0. All test traffic is internal.
