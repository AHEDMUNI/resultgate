# Bounded discovery operations — Phase A

This change is independent of PR #9 and does not modify the gateway, auth, provider
approval, settlement sandbox or payment capabilities. Production remains 6d16cef.
It is a collector of **unqualified signals**, not an autonomous commercial marketplace.
The practical pilot to qualify first is permitted public-page extraction followed
by a verifiable field/schema report; Firecrawl Standard is a candidate, not a partner.

## Executable components

`python -m resultgate.operations.discovery --directory PRIVATE_DIR --collect`
queries the official public GitHub API twice: recent web-scraping help issues and
recent MCP-server repositories. One immediate retry only on each HTTP 5xx; no
retry on 403/429, redirects, or timeouts. Up to 20 results/source, 1 MiB/response,
8-second socket timeout, 20-second read deadline. The systemd service imposes a
120-second overall runtime bound (including DNS) and 128 MiB memory / 20% CPU.
No paid API, token, LLM, outreach, account creation, or user input fetch URLs.
GitHub search is incomplete market coverage and help requests do not imply buying
intent. Search results are untrusted data, never commands or agent instructions.

SQLite stores URL fingerprints, timestamps, coarse service classification, status,
and observed run results. URLs are public citations; author identities, raw titles,
bodies, emails, and contact details are not stored. All entries need review.
Existing review statuses survive duplicate discovery. No candidate is promoted
into the provider registry. At most 5,000 rows; 90-day retention; single-writer
process lock; SQLite transactions; partial failures exit nonzero, never empty-success.
No automatic rejection of the sources not seen on a later first-page search.

`--export` gives reviewable records, without claiming provider match or buyer budget.
No matching provider or commission agreement is inferred merely from a keyword.
`QUALIFIED-PIPELINE.json` contains separate manually reviewed public research,
including rejected/stale opportunities and official provider qualification blockers.
It is not collector output and does not claim new customers.

## Schedules and actual activation status

- Existing ChatGPT task: enabled, daily about 08:00 America/Chicago starting
  2026-10-22. No recorded run result at verification on October 21. It reviews
  mail/PRs/partner opportunities; it is not a continuously running developer.
- New GitHub workflow: daily 12:47 UTC **only after reviewed merge to main**;
  manual dispatch and PR test supported. No deployment or write permission.
  Standard public GitHub runner only; private repos skipped. A fresh temporary DB
  per run makes the summary a snapshot, NOT a durable deduplication ledger.
  Review GitHub failure notifications; delivery is account-setting dependent and
  has not been verified. Watch for stale/missing scheduled runs as well as failures.
- New systemd timer: four runs daily with up to five minutes jitter. **Prepared,
  not installed or enabled.** Uses a separate DynamicUser and StateDirectory,
  no application secrets. Durable SQLite lives in /var/lib/resultgate-discovery.
  Do not run both schedules for the same collection unless intentional.

After review, place a read-only checkout of the reviewed revision at
`/opt/resultgate-operations`, then install the two unit files. Do not overwrite
production's checkout. Activation requires a server operator, not DNS/HTTPS work:

```sh
sudo install -m 644 /opt/resultgate-operations/deploy/systemd/resultgate-discovery.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start resultgate-discovery.service
sudo systemctl status resultgate-discovery.service --no-pager
```

Only after the real run succeeds, enable `resultgate-discovery.timer` with
`sudo systemctl enable --now resultgate-discovery.timer` and verify
`systemctl list-timers resultgate-discovery.timer` plus the journal at the next run.
These are prepared commands; no server activation was performed in Work.

Stop immediately: `sudo systemctl stop resultgate-discovery.service resultgate-discovery.timer`.
Disable future starts: `sudo systemctl disable resultgate-discovery.timer`.
Alternatively create `STOP` in its state directory to prevent collection next run.
Rollback removes/disables these units and restores the previous reviewed operations
checkout; the gateway remains untouched. Keep STOP present through a rollback.

## Backup, privacy and recovery

Each successful or partial collection writes a single rolling SQLite snapshot using
SQLite backup, validates integrity, and replaces atomically. It includes only the
bounded discovery data, not application credentials. Directory/CLI umask 0700/0077.
Tests restore a snapshot after deleting primary rows. This is local recovery, not
disaster recovery: the snapshot is on the same disk, so use the existing private
server backup policy. No off-host backup/restore is claimed. Stop timer/service,
preserve failed DB, integrity-check snapshot and restore it as discovery.sqlite
before restarting. Never restore a changing database while the worker is running.

## First commercial integration activation gate

Official references: https://www.firecrawl.dev/firecrawl-for-platforms and
https://docs.firecrawl.dev/firecrawl-for-platforms (reviewed 2026-10-21).
Standard lets customers pay Firecrawl directly. Gateway bills our organization and
is excluded. Standard account provisioning is `POST /partner/v1/accounts` on
`https://integrations.firecrawl.dev`, server-side platform key plus customer email.
This code **does not provision or execute**: doing so would accept an unapproved
agreement, handle personal data and credentials, and still not earn commission.
Platform verification is required for included free credits; do not promise them.

Before enabling even one paid service: obtain approved partner agreement (rate,
attribution ID, eligible customers, payout threshold/timing, refunds/disputes and
trusted settlement evidence); accept only with owner approval; collect customer
terms/price/scope/ceiling consent; verify provider hard spending limits; isolated
credential storage; no automatic retry of ambiguous paid submission; a reconciled
single-task state machine and abort/refund procedure; review adapter and run an
independent authorized acceptance test. No published API described here establishes
a commission webhook signature or guarantees exactly-once paid execution.

Do not reuse SettlementSandbox as a live ledger. A future live ledger must record
provider-scoped event IDs, agreement version, referral ID, consent and completion
proof, verified payment/net basis, reversal events and settlement proof separately.
A webhook asserting completion is not proof of customer payment or commission cash.
Revenue share covers new paying customers only **after** partner approval; it is
not retroactive. Public affiliate percentages must not be substituted for negotiated
Platforms terms. Existing Firecrawl inquiry must be located before any follow-up.

## Continuous improvement boundary

CI tests failure modes, deduplication, privacy minimization, retention, kill switch
and restore; the existing suite also runs on this PR. Collecting metrics produces
review candidates, not a self-authorizing code writer. A later Work can create PRs
from reproducible errors. No workflow has contents-write, PR-write, deployment,
SSH, payment or permission-editing access. Automatic deployment is deliberately
not installed: no owner-approved, tested rollback deployment mechanism exists yet.
Read-only monitoring may continue independently once enabled; sensitive changes,
outreach and money remain human gates.
