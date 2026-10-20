# Privacy and measurement

Default operation records no usage, sends no telemetry, fetches no sources, and does not write submitted records/quotes to disk. MCP callers receive audit findings containing their own indexes, field paths or source IDs. Your MCP host may separately log your conversations/tool inputs; ResultGate cannot control that host's policies. Package installation contacts the package registry; this is distinct from tool execution.

Optional measurement requires explicitly starting MCP with `--usage-dir` and supplying a usage context per task. This creates a random installation identifier, a private HMAC key and a local SQLite database in the chosen directory. Only a keyed hash of an opaque task identifier, UTC day, tool name and pass/fail/unknown outcome are stored. No text, quote, URL, prompt, IP, email, raw task ID or response body is saved by this measurement feature. One task counts once across tools/retries. Protect this directory like other local application data.

Rows older than the latest 30 UTC dates are purged on startup, recording and export, not by a background scheduler. Export contains the random installation identifier and daily counts by tool/outcome. It excludes task hashes and the private key. The identifier is pseudonymous, not proof of anonymity or a distinct person. Dates/counts may reveal activity patterns, so review before sharing. Nothing is uploaded by the application.

Stop passing --usage-dir to disable measurement. Delete the chosen directory to remove measurement data and reset the identifier; previously shared summaries remain with their recipients. There is no remote deletion endpoint because there is no central collector yet.

A declared real_task is a self-report. Fake counters/new installation IDs are possible. Operator-reviewed independence and usefulness are required before reported usage enters the external-adoption ledger. Our own tests, audit fixtures, package downloads, registry scans and health checks do not qualify. Daily summaries must not be summed repeatedly: reconcile by installation/day/tool/outcome and retain the latest revision, never append duplicates.

A voluntary pilot review should ask only for the summary plus confirmation that the installation is operated independently and used in an actual workflow. Do not request confidential task content. Use a separate consented minimal record for independence review; do not embed identities in the package. No collection/sharing has occurred in this release review.
