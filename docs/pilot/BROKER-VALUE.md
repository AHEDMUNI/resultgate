# ResultGate value benchmark — internal offline simulation

**Finding: no measured reliability or request-count advantage over a competent
bespoke direct integration on these five fixtures.** ResultGate adds local
journal/metadata overhead. Its proposed value is reusable safeguards and eventually
reviewed multi-provider discovery; unknown-provider discovery and integration labor
have not been measured. Do not justify a commission by claiming automatic superiority.

## Reproduce without credentials or network

From the source checkout and installed project dependencies:

```sh
python -m scripts.broker_value_benchmark --samples 15
python -m unittest discover -s tests -p test_value_benchmark.py -v
```

The script uses only a fixed in-memory provider, temporary SQLite databases and
public-fixture strings. It never constructs the real HTTP transport and blocks
DNS/socket connection helpers defensively. No API key is read, no live Browser
Use call occurs, and real cost is zero. Both arms receive the same fixture.
`docs/pilot/broker-value-evidence.json` records the observed run, 15 samples per
arm/scenario; subsequent timings vary with hardware, filesystem and load.

A = a narrow competent direct client with SQLite reservation before create,
restart-safe refusal to retry, preflight, result verification and browser cleanup.
B = ResultGate's actual `Trial` class with the same fake transport. A reuses the
HTML parser and ownership-safe cleanup helper so it is not deliberately weakened.
It does not invoke Trial. A is a benchmark fixture, not a production competitor
or SDK: network timeout/polling, malformed inputs and broader failure behavior
are not exhaustively compared. B additionally stores bounded hashes and state
metadata. Both requesting clients make one high-level run call, then a restart
replay call to test idempotence; this is not an LLM token or planning-step count.

## Results

| Fixture | Simulated transport calls A / B | Correct behavior in both | Median local ms A / B |
|---|---:|---|---:|
| Successful result | 9 / 9 | Verified and stopped | 4.652 / 10.648 |
| Wrong result | 9 / 9 | Rejected; browser stopped | 5.782 / 8.688 |
| Provider failure | 8 / 8 | Not verified; browser stopped | 4.905 / 7.772 |
| Ambiguous create response | 3 / 3 | Slot consumed; no retry; cleanup unconfirmed | 2.701 / 4.646 |
| Cleanup failure | 8 / 8 | Result verified but cleanup explicitly unconfirmed | 4.740 / 7.062 |

Every case made exactly one **simulated** create attempt and zero requests on
restart replay. The nine successful-path operations are billing preflight, public
fixture fetch, create, status, result, browser list, stop, stop verification and
session cost. The ambiguous-create scenario models a request whose completion is
unknown; one client attempt is not proof of exactly-once provider execution.
Both implementations require manual provider reconciliation in that case.

Timing includes local SQLite creation/writes and wrapper execution, but excludes
restart replay, temporary-directory cleanup, remote network latency and actual
agent/model execution. It is not a latency/capacity claim for the public market.
Five injected scenarios are not a statistical reliability estimate or uptime SLA.
Provider discovery is deliberately not scored: both clients already know the
provider, and no independent orchestrator discovery has been demonstrated.

## Full-cost accounting boundary

The historical internal task cost $0.005671 is evidence for that one task only,
not a retail quote or forecast. A separate hypothetical $1 retail task with an
agreed 10% provider-funded share illustrates route A:

| Party / route | Hypothetical USD |
|---|---:|
| Customer directly to provider | 1.00 |
| Customer via ResultGate at same retail price | 1.00 |
| Provider pays ResultGate share | 0.10 |
| Provider retains before its own costs | 0.90 |
| ResultGate gross before hosting/tax/settlement expenses | 0.10 |

Do not add the $0.10 a second time to the customer's $1 if it is funded from the
provider's existing receipt. If the provider adds a fixed $0.10 surcharge, customer
cost becomes $1.10 instead; if it grosses up a percentage to preserve its net,
use the actual contract formula rather than this fixed-surcharge illustration.
No party has agreed this fixture rate. Model/API usage, hosting, support, taxes,
FX, payment fees and loss/refund costs remain unmeasured, not zero. Thus no
measured full-cost saving, profit margin or positive willingness to pay is claimed.

## Practical improvement and commercial gate

Before charging anything, integrate a second reviewed execution provider behind
the same consent/task/result interface and measure a real independent developer's
integration effort and task completion against their own robust direct baseline.
Predeclare the task, correctness checks, full cost and timeout policy. Record
steps/calls and independently measured completion time. Report failures as well
as successes. The immediate discovery improvement is reviewed capability/price
search in the shared catalog; it still needs an authorized public deployment and
an actual independent client. Do not run another paid task merely for a benchmark.

Until that evidence exists, position ResultGate as reusable, inspectable safety
and routing code, with the broker's value hypothesis still being tested. A
successful synthetic test is not demand, a paid transaction or a commission.
