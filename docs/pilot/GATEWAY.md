# Loopback shared-store simulation gateway

This optional development harness lets separately authenticated HTTP clients use
one durable local SQLite market store. **Every task, transaction and commission
remains simulation.** It dispatches no provider calls and performs no payments.
It is neither a hosted marketplace nor an A2A server nor an HTTP MCP transport.
The existing MCP defaults and published 0.2.0 package are unchanged.

## Local operator setup

Use the checked-out development branch and existing Python environment. Initialize
a private directory and issue credentials through trusted local Python, never via
HTTP. Keep the database, identity key and bearer tokens outside the repository:

```python
from pathlib import Path
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator

registry = Registry(Path.home() / ".resultgate-market-pilot")
operator = MarketOperator(Market(registry))
requester_token = operator.issue_credential("internal-pilot-requester")
# Hand this token directly to your local test client using a private channel.
# Do not print it in CI, put it in URLs, or commit it.
registry.db.close()
```

Start one local process (no additional dependencies):

```sh
python -m resultgate.network.gateway --directory "$HOME/.resultgate-market-pilot" --port 8765
```

The CLI only binds `127.0.0.1`, disables proxy-header trust and access logs, and
limits concurrent connections to 16. Do not add a tunnel, reverse proxy or public
listener. Loopback HTTP relies on the machine's existing trusted-user boundary;
it is unsuitable for sharing credentials across hosts or untrusted local users.
There is no browser UI or CORS support. Origin headers and query strings are
rejected. Use a native HTTP client with environment proxies disabled.

## API

| Request | Authentication and behavior |
|---|---|
| `GET /v1/capabilities` | Public local read-only catalog of ResultGate capabilities; not live global provider discovery |
| `POST /v1/tasks` | Requester bearer credential; create an idempotent simulation task |
| `GET /v1/tasks/{id}` | Authorized requester/provider only; tenant/provider isolation |
| `POST /v1/tasks/{id}/events` | Authorized requester/provider transitions only |
| `DELETE /v1/tasks/{id}` | Requester removes task metadata; deduplication tombstones remain |

Example using an already-issued `requester_token` variable:

```python
import hashlib
import httpx

headers = {"Authorization": "Bearer " + requester_token}
with httpx.Client(base_url="http://127.0.0.1:8765", trust_env=False, timeout=5) as client:
    capabilities = client.get("/v1/capabilities").json()
    response = client.post("/v1/tasks", headers=headers, json={
        "request_id": "internal-pilot-001",
        "task_sha256": hashlib.sha256(b"synthetic task").hexdigest(),
        "success_criteria_sha256": hashlib.sha256(b"synthetic criterion").hexdigest(),
    })
    response.raise_for_status()
    task_id = response.json()["id"]
    status = client.get("/v1/tasks/" + task_id, headers=headers).json()
    assert status["mode"] == "simulation"
```

Use the same `request_id` and identical hashes for retries. Changing the payload
under the same ID is rejected; reconnecting or reopening the process preserves
deduplication. Hashes can still reveal low-entropy content through guessing: use
synthetic inputs in this pilot and avoid secrets or personal data entirely.

Only `offered`, `accepted`, `executing`, `completed`, `transaction_proven`,
`failed`, and `cancelled` can be submitted through the event route. Market role
and state checks still apply. Acceptance requires explicit consent. Every event
needs an `event_id`; supporting evidence, when required, is a SHA-256 digest.
`max_cost_micros` can only be zero. Simulated transaction values cannot authorize
spending or establish debt. No administrative HTTP routes exist: provider review,
matching, delegation, verification, commission eligibility, disputes, refunds,
credential issuance/revocation and retention purges remain trusted local operator
operations. Registered providers do not automatically gain execution access.

## Boundaries and retention

- Strict JSON schemas reject unknown fields, duplicate keys, incorrect types and
  paid cost authorization. JSON bodies are bounded to 16 KiB, including chunked
  input, with a five-second total body-read deadline. Error responses do not echo submitted data or credentials.
- Loopback peer and Host validation, rejection of Origin/forwarding headers,
  bearer validation and query-string rejection protect the local boundary.
- A single process accepts at most 360 boundary-valid requests/minute, globally;
  rejected authenticated operations count too. This is a local test safeguard,
  not a distributed public-service rate limiter.
- Existing Market limits apply: 1,000 tasks/tenant, 10,000 total tasks and 1,000
  credentials. Credentials and task access expire after 30 days. The operator
  must run `MarketOperator.purge()` to physically purge expired market
  records; merely restarting does not delete them. Task deletion retains bounded
  deduplication tombstones until their retention expires.
- No new telemetry is transmitted. HTTP clients from our tests are **internal
  test clients**, not independent customers. Socket connectivity does not prove
  agent-to-agent provider execution, a commercial referral or revenue.

Before any shared/public deployment: separate approval, TLS and robust identity
lifecycle, distributed rate controls, store backup/recovery,
a deployment-specific security review, and a genuine authorized provider
integration are still needed. The harness deliberately does not implement these
public-service guarantees.

## Verification

```sh
python -m unittest tests.test_gateway -v
bandit -q resultgate/network/gateway.py
```

The focused suite includes a genuine loopback Uvicorn socket with two independent
HTTP client objects (internally operated), authentication, tenant isolation,
reopening the durable store, credential revocation, deletion tombstones,
idempotency, strict validation, streamed-body limits, Host/Origin/peer rejection,
no administrative routes and a local request-rate limit. External usage and
real commission totals remain zero/unproven.
