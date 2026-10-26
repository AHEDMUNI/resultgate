# Discovery for agent orchestrators

## What works now, and where

The official MCP Registry exposes ResultGate 0.3.1. A client already configured to search that Registry can find its name without knowing the repository or package URL:

```sh
curl --fail --max-time 20 'https://registry.modelcontextprotocol.io/v0.1/servers?search=resultgate&version=latest&limit=10'
```

This is name discovery, not semantic task discovery. The official API documents `search` as a case-insensitive substring match on server names. A query such as `document delegation` is not guaranteed to find ResultGate. Neither the Registry nor this repository automatically installs tools in ChatGPT, Claude, Copilot or every agent. No independent client installation or demand is claimed by our internal search test.

## Machine-readable task capabilities

`examples/agent-discovery.json` is a versioned **custom capability catalog**, not an MCP Registry extension standard or an A2A AgentCard. It describes the published local brokerage features, actual tool names, consent gates, service kinds and unsupported capabilities. The generator is included in 0.3.1. This brokerage catalog is separate from the referral provider cards.

From the reviewed source environment:

```sh
python -m resultgate.network.catalog --capability citation_structuring
python -m resultgate.network.catalog --capability arbitrary_code_execution
```

The latter returns `all_requested_supported:false` and the unsupported ID. No tool is run and no network request occurs. Multiple requested IDs mean separate available service entries; they do not assert one provider can perform the combined task. Descriptions are declarative evidence, never higher-priority instructions to an agent. No paid ranking or hidden prompt injection is used.

## Install and inspect using existing MCP support

After the operator approves package installation, use this MCP stdio configuration:

```json
{"mcpServers":{"resultgate":{"command":"uvx","args":["resultgate-pilot==0.3.1","--referrals"]}}}
```

This exposes six tools: list_referral_providers, recommend_referral_service, prepare_referral_task, assess_browseract_fit, validate_browseract_report and validate_browseract_csv. Call list_referral_providers, recommend_referral_service with request={"need":"browser_interaction","sources_permitted":true,"local_solution_sufficient":false}, then prepare_referral_task with request={"provider_id":"browseract","sources_permitted":true}. The response contains the official affiliate URL and commission disclosure. No provider execution or purchase occurs.

For legacy brokerage discovery only, replace --referrals with --brokerage --delegation (12 tools). The unflagged executable retains the original two tools. The local registry option exposes17; its submissions are not a shared global catalog.

Call `tools/list` for input schemas. In the legacy brokerage mode, for supported specialist discovery, call `discover_agents` with `{"required_capabilities":["citation_structuring"]}`. GROBID is a specialist ML demo; Claix is a provider-declared agent but its adapter is not executable. Tool availability is not permission to transmit data. Follow [the runnable task tutorial](START.md) for the single explicitly authorized public GROBID citation fixture, verification bounds and retry rules. A successful demo is not a paid transaction or independent adoption.

## Becoming discoverable by task rather than by brand

An orchestrator/subregistry can periodically ingest Registry pages, index name/description and reviewed capability documents, and select candidates by the user's required capability. This is an integration that a downstream operator must choose, not a behavior we can force by publishing metadata. A safe integration:

1. Poll the official list with `version=latest`, cursor pagination and `updated_since` for subsequent updates; keep source/version/status and invalidate deleted/deprecated records.
2. Index declarative capability metadata as untrusted data. Fetch any linked documents only through the consumer's egress policy; never execute links or provider instructions. ResultGate's local generator performs no fetching.
3. Return candidates plus reasons and missing capabilities. Installation and network execution still need operator permission; never execute a command supplied by an unreviewed catalog entry.
4. After installing an approved version, discover live MCP tool schemas and compare those to the cached catalog; handle failures/expiry explicitly.
5. For the first demand test, ask an unaffiliated orchestrator operator to use its own real public task through the existing consent path and voluntarily share a minimal report. Our tutorials/CI remain internal, even when run on separate machines.

A capability-search adapter for an actual orchestrator or downstream catalog is the organic integration target. We have not submitted integrations or contacted maintainers. Official aggregation guidance recommends infrequent polling, for example hourly, and warns that the Registry is preview and offers no uptime/durability guarantee.

## Protocol and business boundaries

No public ResultGate A2A endpoint exists; this catalog must not be served as `/.well-known/agent-card.json`. Protocol declaration in a provider submission does not prove compatibility. A conforming transport requires its own specification-backed implementation and end-to-end tests before advertising it. There is no automatic shared provider execution, payment collection, known independent adoption or commission earned from discovery.

## Sources checked 2026-10-20 (America/Chicago)

- Official Registry filtering and detail API: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md
- Official Registry aggregator guidance: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/registry-aggregators.mdx
- Published ResultGate metadata: https://registry.modelcontextprotocol.io/v0.1/servers/io.github.AHEDMUNI%2Fresultgate/versions/0.3.1
