# Limited referral measurement — review before deployment

## Boundaries

No public MCP endpoint, authentication, provider account, payment configuration,
commission rate or catalog data changes. No JavaScript/cookies/fingerprints.
The existing catalog button uses `/go/browseract`, a fixed 302 to the already
approved `https://browseract.com?fpr=ahed-ddc97e`. No arbitrary destination or
query string is accepted. HEAD/POST requests do not count as handoffs. A GET
prefetch still can: call this a **redirect request**, not a human click.

The local `prepare_referral_task` response offers that measured handoff and the
unchanged direct affiliate alternative as `provider_url`. Direct visits bypass
ResultGate counting. The companion makes no network request when returning it.

Only `/referrals`, `/referrals.json` and `/go/browseract` get a new event log:
UTC-offset timestamp, fixed event, status, and a fixed origin bucket. No IP,
raw User-Agent, referrer, query, request body, token, cookie or identity is stored.
`ResultGate-Internal*` User-Agents are internal-declared; recognizable bot/crawler/
spider/preview/headless strings are bot-declared; all others are unknown.
These labels are spoofable and incomplete. Never rename unknown to independent.
All deployment/probe commands must use `ResultGate-Internal-...`. Browser-based
checks without this marker are unknown; record their time as internal evidence.
Original minimal access logging remains present on these routes.

## Local tool counts (optional, never transmitted)

In the MCP client's environment, set `RESULTGATE_LOCAL_METRICS_DB` to an absolute
private database path. Set `RESULTGATE_LOCAL_METRICS_ORIGIN=internal_declared`
for owner/test runs; otherwise it stays unknown. Only day, tool name, bucket and
completed-call count are saved. No inputs, outputs, need, URLs or model/user IDs.
Disabled by default; failures return `local_observation=unavailable` without
breaking recommendations. The OS user controls this database. Do not place it
in a repository or public/shared folder. Local counters do not reveal other
people's installations. No automatic report transfer is installed.

## Safe publication and rollback

After separate merge/deployment approval, use the existing reviewed pinned
checkout and `sudo python3 deploy/publish_business_site.py`. The publisher
requires the existing `/etc/logrotate.d/nginx` wildcard policy before changing
anything, preserves the MCP/auth block, backs up nginx config, checks `nginx -t`,
reloads, verifies public/private boundaries and exact redirect Location without
following it, then checks published bytes. On verification failure it restores
the previous config. No application restart or new service is needed.

Inspect actual rotation/retention before rollout; this PR does not silently alter
that policy. New event file is initially mode 0600, then follows existing nginx
rotation permissions. Missing rotation or unknown managed config stops deployment.
Nginx is not installed in the local review runtime; live syntax and permission
checks are explicit deployment gates, not claimed completed here.
For rollback restore the printed nginx backup, test and reload nginx; this also
restores the prior static release and direct link. The original publisher can
fail closed on new instrumentation; use the reviewed publisher for later upgrades.

## Daily operator report

Run privately on the host, after deployment, for each reporting date:

```sh
sudo python3 scripts/referral_path_report.py --day 2026-10-23
```

Optionally add `--local-db /absolute/private/counts.db` on the device that owns
that database. Dates use America/Chicago. Rotated compressed event logs are read.
Output contains aggregate counts only; missing/unreadable data is unavailable or
partial. Zero records is not proof of full-day coverage. Record rollout time,
log continuity, rotations and exclusions. The existing public Actions workflow
remains availability-only; never upload logs, private DBs or provider reports.

Read BrowserAct Reports/Commissions/Payouts manually via the authorized account.
Keep timestamp and reporting period with each private observation. No reporting
API exists according to support; never turn a ResultGate redirect into a
provider-confirmed click. Do not add synthetic registrations/purchases.
No provider numbers are embedded in source or filled with invented zeros.

## 72-hour decision

Do not start before merge, confirmed deployment, successful marked internal
catalog/redirect checks, and a timestamped provider dashboard baseline. Record
the real start in the private daily record only after those checks. This PR
starts no clock and creates no scheduled process.

These anonymous counts can show whether unknown traffic reached the catalog
and requested a handoff, but **cannot prove a unique independent person or join
that person's journey**. A provider-confirmed referral/purchase plus private
review excluding owner/test activity can corroborate a genuine conversion.
If proof of independent arrival before any registration is a strict prerequisite,
it remains unavailable: do not claim this anonymous design satisfies it. Choose
an explicitly consented independent pilot/evidence source before starting under
that stricter rule; no identity tracking or customer outreach is added here.
