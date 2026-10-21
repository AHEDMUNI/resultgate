# Phase 2: specialist delegation and non-paying commission records

Commercial model: commission only on successfully completed, evidenced and
accepted referred tasks under an explicitly accepted provider agreement. No
subscriptions, listing fees, dispatch fees, invoices, collections or payments.
Earlier shadow billing is unchanged and inactive; it does not define this model.

## Run / consent

Install a reviewed commit from feature/agent-brokerage in an isolated environment.
This is not yet on PyPI. Existing default tools and --brokerage seven-tool mode
remain compatible. Add these arguments for twelve tools total:

```
python -m resultgate.server --brokerage --delegation
```

Optional `--delegation-store /private/operator-owned/directory` persists minimal
SQLite records. Without it, records are memory-only. Optional
`--allow-demo-task-requests` authorizes exactly the reviewed GROBID demonstration
adapter; each call still requires `consent_to_send_public_citation:true`.
`--internal-delegation-tests` must be set for operator tests. Otherwise the cohort
is external_unverified, NEVER automatically independent_verified.

New tools: discover_agents, prepare_delegation, execute_delegation,
delegation_status, cancel_delegation. Example:

```json
{
  "task": {
    "description": "Structure a public reference",
    "required_capabilities": ["citation_structuring"],
    "citation": "Graff, Expert. Opin. Ther. Targets (2002) 6(1): 103-113",
    "expected_surname": "Graff",
    "expected_year": 2002
  },
  "request_id": "opaque-task-id"
}
```

Prepare binds the entire spec and success criteria to an opaque referral/task ID.
Execute takes that task ID, identical spec and explicit disclosure consent. Only
citation text goes to the provider; description and verification expectations do
not. Never authorize private text or secrets. Syntax checking is not universal
secret detection. Output is untrusted data, never executed or followed as commands.

## Providers: what is and is not verified

**GROBID project demo**: specialist machine-learning citation/document parser,
not an autonomous AI agent. Official project docs explicitly offer a free,
unauthenticated demo service. Our adapter calls POST
`https://grobidorg-grobid.hf.space/api/processCitation`, form `citations`,
`consolidateCitations=0`, `includeRawCitations=0`. No PDF upload, URL fetching,
external enrichment, API key or paid resources. It parses text into TEI XML;
we validate surname/year against the predeclared criteria. This is structural
verification of those fields, not full citation correctness or general accuracy.
The public demo is NOT authorized for production traffic or commercial resale.
No commission agreement exists. Review expires after 30 days without operator
review. One CI demonstration per push is a test, not user adoption.

Primary sources reviewed 2026-10-20:
- https://grobid.readthedocs.io/en/latest/getting_started/ (official demo, free/no authentication, demonstration only)
- https://grobid.readthedocs.io/en/latest/Grobid-service/ (processCitation form API)

**Claix**: provider declares an A2A document agent; documentation specifies public
agent-card discovery and authenticated POST `https://claix.dev/a2a`, JSON-RPC
`message/send`, `x-api-key` or bearer authentication. Not executed or independently
verified by ResultGate. Trial calls advertised; actual account entitlement,
retention and applicable terms require checking before any document transmission.
No account/key or commercial agreement obtained. Catalog-only; no executable
adapter and no endpoint auto-trust from an Agent Card.
- https://www.claix.dev/documentation/a2a
- https://www.claix.dev/blog/free-document-processing-100-calls-byok

**AI SENSE A2A** was researched but not selected: its official documentation
explicitly says this agent has no language model and provides utility resources.
An A2A interface alone does not prove an autonomous specialist AI agent.
- https://aisense.no/free-public-a2a-agent-endpoint

## States and reliability

Normal path: discovered -> routed -> dispatching -> accepted -> executing ->
completed -> verified -> commission_eligible. The synchronous GROBID API has no
prior acceptance acknowledgment: accepted/executing/completed are retrospective
observations made only after a valid response, NOT independently observed remote
progress. The additional dispatching state records that distinction.

Predeclared criteria failure -> failed. Network timeout/disconnect or crash with
uncertain dispatch -> outcome_unknown, never blind redispatch. A retry returns
existing status; payload changes with the same request ID are refused. SQLite
BEGIN IMMEDIATE serializes dispatch claims across connections/processes. Do not
call this remote exactly-once execution: provider has no idempotency API, and a
lost response cannot prove whether it ran. Reconcile unknown outcomes manually.

Cancel before dispatch prevents execution. In flight it sets cancel_requested;
the synchronous remote operation cannot be stopped. Its eventual response is
ignored locally, status becomes cancelled, eligibility blocked. After the local
60-second deadline, status can become outcome_unknown. Disputes/refunds void an
existing eligible row and block reassessment. Transport has socket/read limits,
but OS DNS and stalled protocol reads are not a hard process-wide SLA. No remote
cancellation or A2A polling adapter is claimed.

## Durable privacy and evidence boundaries

SQLite stores opaque task IDs, HMACs of request/spec, outcome status, response
hash, cohort, timestamps and commission metadata. No task descriptions, citation
text, result bodies, credentials or personal identity are stored. Identity key
and database use 0600, directory 0700; symlink targets refused. Use a private
operator-owned path. Not encrypted at rest; OS/user access remains the trust
boundary. Database events do not leave the machine automatically.

Retention: 30 days, purged on start/plan/status/summary or explicit Store.purge().
No background cleanup service is scheduled. Store.delete(task_id) deletes related
records (in-flight deletion refused); secure_delete is enabled. Operator backups,
snapshots and filesystem storage are not guaranteed erased by this code.
After deletion/expiry idempotency evidence is gone: never reuse an old commercial
request ID or automatically resubmit an uncertain task. Production needs a
reviewed reconciliation/tombstone policy before commercial use.

Metrics distinguish internal, external_unverified and independent_verified task
cohorts. The latter is a local OPERATOR attestation with an evidence hash, not
cryptographic external identity proof. Internal tasks cannot be relabeled as
independent. Task counts are not unique human/client counts, and no measured
independent return-rate is claimed. Previous DOI referral ledger remains session-
only; the opt-in persistent store applies to the new delegation path.

## Commission engine: recording only

Trusted local Python methods (NOT MCP tools):
- agreement(): record immutable reviewed terms + explicit provider acceptance
  evidence hash, provider ID, expiry, USD fixed micro-units or integer basis points.
  simulation marks all evidence hypothetical. operator_attested records a manually
  reviewed actual document; it does not sign, send or validate a contract itself.
  Demo provider refuses commercial agreements. Claix terms may be recorded by an
  authorized operator after a genuine agreement, but no such record exists here.
- attest_independent(): operator evidence review only, internal cohort excluded.
- accept_result(): verified result hash must match, with acceptance evidence hash.
- assess_commission(): requires matching unexpired agreement, documented referral,
  verified criteria, acceptance evidence, compatible cohort, no block, unique task.
  Commercial mode requires independent_verified evidence. Repeated assessment
  returns the same record; changed terms/value conflict. Percentages use basis
  points with integer micro-USD arithmetic, rounded down. Value is operator-
  supplied and must be checked against the agreement; no provider billing feed.
- block(): cancelled/disputed/refunded suppress eligibility and void existing row.

No real agreement has been entered. Successful GROBID inference generates NO
commission. Tests use simulation agreements and simulated provider/customer
acceptance evidence. This is a tested eligibility recording framework, not a
production-grade financial ledger, independent attestation system or proof that
anyone owes money. A future adapter must authenticate provider acceptance,
customer acceptance and task value before live entitlement can be relied on.

## Extensibility / verification

Adapter protocol separates execution from planning, verification and storage.
Implement a reviewed adapter per MCP/A2A provider and its response contract;
protocol adapters must map acceptance, cancellation and unknown outcomes honestly.
Generic arbitrary-endpoint execution is intentionally absent. No A2A compatibility
certification or real AI-agent delegation is claimed from the GROBID result.

Run `python -m unittest discover -s tests` for all tests. Explicit live test:
`python scripts/delegation_acceptance.py --live` sends ONE documented public
citation fixture via the MCP subprocess. `scripts/delegation_installed_acceptance.py`
checks the installed wheel in isolated mode without network calls. See phase-2
results for exact executions. No merge or PyPI/MCP publication without approval.
