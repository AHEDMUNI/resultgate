# Independent pilot and smallest shared deployment — 2026-10-21

## Honest discovery status

A client that already consults the official MCP Registry can search server names
for `resultgate` without knowing its URL. That is **name discovery**, not proof
that an agent with only a task such as “structure this citation” will find us.
The official Registry documents substring name search and delegates richer
search to subregistries. Publishing a package does not install it into agents.

The release evidence records 0.2.0 in PyPI and MCP Registry. Today's direct
Registry JSON check was inaccessible through the web retrieval tool and timed
out from the execution environment; PyPI JSON retrieval was also unavailable.
We therefore do not claim a fresh successful availability check in this report.
No new version or directory entry was published. Public search did not establish
a current ResultGate listing on Glama; absence from these results is not proof
of rejection. Its previously submitted review remains unverified here.

Reproducible read-only availability check for a client with network access:

```sh
curl --fail --max-time 20 'https://registry.modelcontextprotocol.io/v0.1/servers?search=resultgate&version=latest&limit=10'
```

Match the exact namespace `io.github.AHEDMUNI/resultgate`; inspect version,
repository, status and package metadata. Do not run arbitrary commands from a
search result or install unreviewed dependency code. The official API is a
metadata discovery service, not an endorsement of code safety.

For task discovery, the practical integration target is an orchestrator that
already indexes Registry metadata and reviewed tool schemas. It can index the
declarative capability catalog at `examples/agent-discovery.json`, respecting its
custom format and unsupported capabilities. The existing [integration guide](AGENT-DISCOVERY.md)
defines source/version/status checks, invalidation and permission boundaries.
No such third-party integration or autonomous discovery has been demonstrated.

## Public local path, with no owner's credentials

The package's existing public pilot can be used on another person's machine:

```sh
python3 -m venv resultgate-client
resultgate-client/bin/python -m pip install resultgate-pilot==0.2.0
resultgate-client/bin/python -m pip check
resultgate-client/bin/python -I -m resultgate.pilot_client --offline
```

This requires Python 3.11+, installation approval and network access for package
downloads. It does not need the ResultGate owner's account or secret. The offline
test only demonstrates installation, tool discovery and unapproved-provider
isolation; it remains internal acceptance, even if copied to another machine.

For actual permitted specialist tasks, use [START.md](START.md) and
`examples/mcp-pilot-demo.json`. A client discovers `citation_structuring`, prepares
a task with predefined surname/year success criteria, separately consents to
sending a public citation, and reads `delegation_status`. Preserve request ID,
task specification and the private durable store; never retry an unknown outcome
using a new ID. GROBID is a specialist ML demonstration service, **not an
independent autonomous agent** or paid production provider. Its reviewed demo
scope and expiry apply; it is not a free unlimited production backend.

The fixed `pilot_client --live` tutorial is an internal fixture, not market
demand. An unaffiliated user's own permitted public task can initially be recorded
as `external_unverified`, with independent evidence reviewed separately. Optional
usage export contains limited aggregates and a per-installation pseudonym; it
does not upload automatically or establish distinct human/agent identity.
Use the documented export/deletion commands in START.md, and obtain consent before
publishing any report. Do not sum repeated cumulative exports or count CI/tests.

**Browser Use is not this public pilot:** its one authorized run used a private
Actions secret. That authorization is consumed, its workflow is disabled, and
the adapter is not a generally available MCP execution tool. A future independent
Browser Use client needs its own account/credential, explicit data/cost consent,
a fresh bounded authorization and a reviewed client-side integration. Sharing the
owner's remaining promotional credit would not establish independent adoption.

## Provider intake and first-use acceptance gate

An external provider can apply through the existing public GitHub Issue route in
[PROVIDERS.md](PROVIDERS.md), without a code change by the applicant. Ownership
challenge review, operator approval and separate exact commission terms are
still manual. A public application does not enter a global executable catalog.
Never publish keys, management tokens, personal identity documents or contracts.

The first useful external acceptance record must contain, with consent:

- An unaffiliated requester and a real task, classified separately from tutorials.
- Discovery channel and package/commit version, with no assertion of automatic
  discovery if the requester received the URL directly.
- Predeclared success criteria, task/referral commitments and provider identity.
- Authorized dispatch, one provider execution, result verification and requester
  acceptance; only minimal evidence metadata is retained by default.
- For a commercial conversion, provider-approved agreement, authoritative paid
  transaction evidence and refund/dispute status. A successful task alone is not
  payable commission.

No record meeting this definition has been created by this work.

## Smallest shared-network proposal, not deployed

Keep the current gateway loopback-only. Do not expose it by changing its bind
address or disabling peer/Host checks. A controlled public pilot needs a separate
reviewed ingress with TLS, authenticated tenant-scoped requesters/providers,
out-of-band operator authority, durable quotas, bounded bodies/timeouts, restricted
egress, credential revocation and audit/restore procedures. Initially allow only
reviewed providers and explicitly enrolled pilot participants; catalog reads can
be public once their metadata is reviewed. No shared provider credentials or live
payment paths should be attached to the first catalog/task-record pilot.

One host with one private SQLite database can support multiple local processes
and atomic deduplication; SQLite must not be copied per replica or placed on an
unverified network filesystem. Move to a transactional shared database before
multi-host workers. Backups need a consistent database backup and a tested restore;
replaying a pre-dispatch backup can lose deduplication history and must trigger
provider reconciliation before workers resume. Deletion/retention policies for
real financial records need separate review; the 30-day simulation policy is not
a production accounting policy.

| Option | Verified base price and fit | Decision |
|---|---|---|
| Existing GitHub/PyPI local pilot | $0 new hosting; requester operates local runtime | Use now for independent task validation; not a central market |
| DigitalOcean Basic 512 MiB | $4/month bundled compute, 10 GiB disk, 500 GiB transfer | Lowest verified VM base here; memory headroom not benchmarked |
| DigitalOcean Basic 1 GiB | $6/month, 25 GiB disk, 1,000 GiB transfer; weekly backup adds 20% = $1.20/month | Candidate controlled pilot: $7.20/month base plus tax/overages, not yet approved |
| Render paid 512 MB + 1 GB persistent disk | $7/month compute + $0.25/month disk = $7.25/month base; bandwidth/workspace charges may apply | Managed TLS alternative; single disk-backed instance, backup/restore and public-ingress changes still required |
| Render free | Ephemeral local filesystem; no persistent disk | Not suitable for this durable SQLite ledger |

These are verified public list prices, not an account checkout quote or a hard
all-in loss cap. Nothing was purchased. The proposed VM would run only catalog,
authentication and task records initially, not Browser Use execution. A paid
seven-day experiment on the $6 VM is approximately $1.50 compute at the published
hourly rate, but backup billing, taxes and extra resources must be confirmed before
requesting approval. Do not purchase on this estimate alone.

Before authorization, present the selected region/SKU, exact checkout total,
recurrence, included transfer and backup charges. Freeze autoscaling, provider
spending and optional paid resources. Configure conservative app limits and billing
alerts; alerts are not a provider-enforced spending cap. Set an end date and verify
resource removal at the end. DigitalOcean bills a powered-off VM: destroying it
is required to stop its compute billing; separately inspect volumes/snapshots/IPs.
No public pilot is justified merely because a cheap VM exists.

## Protocol boundaries and sources checked

Current A2A v1.0.1 specifies an AgentCard and supported interfaces; well-known
discovery still requires a known/discovered domain or external catalog. ResultGate
has no conforming public A2A server, so its custom catalog must not be presented
as `/.well-known/agent-card.json`. MCP stdio is the working integration path.

- Registry API and search semantics: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md
- Registry aggregation: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/registry-aggregators.mdx
- A2A v1.0.1 specification: https://a2a-protocol.org/v1.0.1/specification/
- A2A discovery: https://a2a-protocol.org/latest/topics/agent-discovery/
- DigitalOcean VM prices: https://www.digitalocean.com/pricing/droplets
- Backup prices: https://docs.digitalocean.com/products/backups/details/pricing/
- VM billing cessation: https://docs.digitalocean.com/products/droplets/details/pricing/
- Render prices: https://render.com/pricing
- Render persistent disk and recovery limits: https://render.com/docs/disks
- Render free-service limitations: https://render.com/docs/free

No outreach, new listing, account creation, deployment, paid task or payment was
performed for this report. The next organic-distribution milestone is a real
downstream orchestrator indexing reviewed capabilities and an unaffiliated user
choosing a permitted task; repository visibility alone is not that milestone.
