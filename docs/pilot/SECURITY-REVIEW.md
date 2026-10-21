# Pilot launch security review — 2026-10-20 America/Chicago

Scope: feature branch, local stdio pilot plus public GitHub application instructions. This is a code/test review, not a third-party penetration-test certificate. Shared hosted operation is **not approved by this review**.

| Area | Existing or verified control | Limit / pilot decision |
|---|---|---|
| Provider trust | Strict submission schema; pending state; owner token cannot approve; expiring domain challenge + distinct local administrative review | Manual domain observation is an operator attestation, not automatic identity proof. Submitted endpoints never executed. |
| Revocation | Reject removes discovery | Found that old accepted terms could survive reject/re-approval. Fixed rejection to clear agreement entirely; regression test added. |
| Keys | No credential field in metadata; URL credentials/query blocked; random management token stored as keyed hash | Public text cannot magically redact a secret someone pastes. Clear public-only form notice; never paste full import response in an issue. |
| SSRF / code execution | No fetch on registration; execution only built-in fixed endpoints, public DNS check and TLS pinning, no redirects or provider scripts | Manual reviewer must independently refuse internal/reserved DNS. No arbitrary A2A/MCP adapter execution added. |
| Delegation | Operator network flag + per-task consent; predeclared criteria; request binding/dedup; ambiguous outcome not auto-retried | Demo only, no hard DNS total deadline or remote cancellation guarantee. |
| Result / commission forgery | Safe XML, bounded output, untrusted result; signed bounded receipts, time window, event/outcome dedup, agreed economics + acceptance evidence | HMAC local contract not provider billing integration; operator controls local evidence. Signature alone is not sale proof; commercial reconciliation/maturity still required. |
| Retention | Optional private local SQLite, permission restrictions, keyed identifiers, lazy30day purge, deletion CLI | Not encrypted; public GitHub applications/reports have GitHub retention, not30days. Backups/copies need separate removal. |
| Usage proof | Explicit consent before aggregate export; pseudonym scoped to installation; internal cohort excluded | Self-reports are unverified and forgeable; no autonomous promotion to independent adoption. Compare snapshots, do not sum repeated reports. |
| Request/cost limits | Submission cap1000; delegation cap10000; citation2000chars; response128KiB; socket12s/read-loop20s checks; receipts8KiB; no paid adapters | No public rate limiting/tenant quotas. Don't expose local tools as a shared service. Existing shadow billing unchanged. |
| CI | Read-only repository permission, pinned checkout/setup actions, no publish/issue-triggered actions; external fixtures only on owner-repo pushes | GitHub Actions counts as internal use. No issue content interpolated into shell. |

Checks run: full unittest suite, installed client, wheel/sdist + strict Twine, pip check, Bandit and pip-audit pinned requirements. Exact counts/results and CI evidence are recorded in PHASE4-RESULTS.md after execution. No additional security subscription activated. Manual inspection of added files found no real credentials; sample endpoints/tokens are fixtures only.

Release gates: local pilot can be reviewed; hosted network requires tenant authentication/authorization, abuse throttles, durable database/backups, safe automated ownership verifier and production provider adapter. Real commissions require a separately authorized complete agreement and authentic economic evidence with reversal handling. Existing GROBID demo must not be offered as production processing.
