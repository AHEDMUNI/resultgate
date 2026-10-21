# Specialist-agent integration diligence and actual probe

Reviewed 2026-10-20 America/Chicago (2026-10-21 UTC). Internal technical research only; no independent customer use, commercial agreement, payment or commission.

## Result

**No new successful end-to-end specialist AI-agent delegation is proved.** Three public Agent Cards were retrieved successfully. One provider explicitly advertising a free no-key canned self-test received a single bounded A2A request and returned HTTP429. It was not retried. A2A-shaped APIs, a public card, or a provider calling itself an agent do not establish actual autonomous reasoning or successful work.

No registration, signup, account, API key, payment credential or provider agreement was created. No private documents or user data were sent. No provider instructions or returned commands were executed. No dynamic provider was added to ResultGate's executable allowlist.

## Actual requests performed

| Request | Observed result | What it proves |
|---|---|---|
| GET `https://authenticated-llm-agent.getvda.ai/.well-known/agent-card.json` | HTTP200, 3,705 bytes; name Authenticated LLM Agent; advertised A2A endpoint `https://authenticated-llm-agent.getvda.ai/a2a/`; `selftest` describes free canned capability exercise without credentials | Provider publishes discovery metadata; not capability validation |
| GET `https://api.andru-ai.com/.well-known/agent-card.json` | HTTP200, 10,310 bytes; JSONRPC1.0 and0.3 interfaces; API-key authentication declared | A reachable card and documented delegated-task interface, not an authorized task execution |
| GET `https://claix.dev/.well-known/agent-card.json` | HTTP200, 42,098 bytes; document-processing skills; live card points to `https://www.claix.dev/a2a`; API-key security declared | Real discovery works; documentation and live origin must be reconciled before an allowlisted adapter |
| GET `https://agentrxi.com/llms.txt` | HTTP503 | Documentation fetch unsuccessful; no paid or free task called |
| POST `https://authenticated-llm-agent.getvda.ai/a2a/` | HTTP429 Too Many Requests | A failed internal protocol probe, no execution result or success evidence |

The single POST used HTTPS certificate validation, no redirect following, a30-second timeout, a128KiB response limit, and fixed public text. Payload:

```json
{"jsonrpc":"2.0","id":"resultgate-internal-selftest-20261021","method":"message/send","params":{"message":{"kind":"message","messageId":"resultgate-internal-selftest-20261021","role":"user","parts":[{"kind":"text","text":"Run your self-test and show me the result."}]}}}
```

This probe was direct diagnostic code, **not a ResultGate adapter or a completed ResultGate routing journey**. Provider rate limiting was respected. We did not infer task completion, commission eligibility or LLM execution from the advertised skill. The underlying VDA card describes library capabilities, so even a later self-test success must be inspected to distinguish library healthchecks from actual AI work. A signed provider assertion also does not independently establish truth.

## Shortlist and exclusions

### Andru — a new realistic candidate, credential blocked

[Primary A2A documentation](https://andru-ai.com/docs/a2a) documents hosted domain agents/tools, signed result artifacts, A2A1.0/0.3, GetTask/CancelTask and messageId dedup. An API key is required. Some lookups are free; five daily A2A calls cover specified pre-meeting briefs, while catalog assets are paid. This is not a blanket free allowance for all skills. Actual account quota, least-privilege scope, no-autocharge configuration and terms need approval before using an owner-created key. No account was created. No commission permission is established. The service's sales-specialist domain is a poorer first product fit than document extraction, despite useful protocol and receipt support.

A bounded next trial would use synthetic public company context, select a specifically free advertised skill, read quota/price before execution, bind consent to exact arguments/zero maximum cost, send a stable messageId once, verify the signed artifact and task state, and independently check a narrow expected property. Do not use AP2 purchase or paid assets.

### Claix — best document-specialist fit, still credential blocked

[Primary A2A documentation](https://www.claix.dev/documentation/a2a) and the observed card expose schema-based document extraction and task results. [Terms](https://www.claix.dev/terms) require separate review for commercialized direct API access; no commission agreement follows from technical API availability. The advertised trial is configuration dependent. Need an owner-created account/key, confirmed zero-charge trial, and explicit data-transfer scope. No live authenticated task ran.

### VDA Authenticated LLM Agent — attempted but unverified

The primary live card explicitly permits a no-key free canned self-test. The actual POST returned429, so this is a failed probe. [VDA's primary site](https://getvda.ai/) describes governance services, not proof that this particular legacy card's self-test performs an LLM task. Do not list it as a verified executable supplier.

### NetShow — keyed task API, no free unattended handoff established

[Primary page](https://app.netshow.ai/multi-agent-dialogue/a2a) states that discovery is public but task calls require owner tokens/per-agent keys. It also explicitly says autonomous handoffs are not switched on yet. Its recorded demo is not our successful integration. Not called.

### AI SENSE — useful protocol test surface, not the requested AI specialist

[Primary MCP/A2A documentation](https://www.aisense.no/free-public-mcp-server) offers a no-key A2A surface but explicitly states it has no language model and does not interpret free text. Its queues, wake tasks and approvals are deterministic workflow infrastructure. Excluded as proof of AI-to-AI specialist work; no resources were created merely to inflate integration counts.

### Registry utility agents — tools, not independent specialist AI

[Primary registry documentation](https://www.a2a-registry.org/api-docs) describes authenticated tool primitives/reference implementations. Public listing is not authorization to execute, and semantic search requires a free account token. No account or task call was made. Its top-level generic public-search wording conflicts with the detailed authenticated-query section; follow the specific endpoint requirements.

### Local mock/sample agents — internal protocol testing only

[Official A2A samples](https://github.com/a2aproject/a2a-samples) and [Inference Gateway mock-agent documentation](https://docs.inference-gateway.com/mock-agent/) can exercise lifecycle handling. The latter explicitly uses a mock LLM. Hosting a sample ourselves cannot be counted as an independently operated external provider or independent customer use. No model download or mock deployment was added in this investigation.

## Next gate

The fastest credible path remains a small permissioned specialist pilot: owner provides a zero-cost sandbox/account with bounded authority for Claix (document fit), or Andru (stronger documented receipt/dedup details). Before production routing, add a fixed-host reviewed adapter, exact task/cost consent, idempotent task mapping, bounded input/output, explicit accepted/working/failed/cancelled states, result checks and signature-key pinning where supported. Never turn an arbitrary submitted Agent Card endpoint into executable trust.

A commercial referral further requires a separately accepted commission agreement and authoritative paid-conversion proof. None of this research supplies those prerequisites. Independent use0; successful new specialist delegations0; paid transactions0; commissions0.
