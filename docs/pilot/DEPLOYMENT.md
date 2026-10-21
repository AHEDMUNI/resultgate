# Lowest-cost pilot delivery — checked 2026-10-20 America/Chicago

Recommendation: distribute the reviewed Git commit as a local MCP pilot and accept public-only provider applications through this repository's already-enabled Issues. No runtime hosting bill, new account, server uptime promise or central task data. After explicit owner approval, merge and publish a versioned PyPI release plus accurate MCP Registry metadata for easier discovery. Keep brokerage opt-in and payments disabled. This is distribution of local software, not a shared online network.

| Option | Actual limits / fit | Decision |
|---|---|---|
| Existing public Git branch / immutable commit | No ResultGate hosting cost; user supplies Python/Git/local runtime. Mutable branch should be pinned to reviewed SHA. Unreleased features not present in old PyPI release. Operator-owned registry remains local. | Best immediate review pilot. Prepared instructions and isolated source-install CI. |
| New PyPI release + official MCP Registry | Package distribution/metadata, not hosted execution. Requires valid built artifact/version, publisher identity and matching package metadata; Trusted Publishing uses OIDC rather than stored API keys. Existing0.1.1 publishing workflow must be reviewed for version changes before any dispatch. | Best next distribution step **after approval**. No publish or version bump performed. |
| GitHub Pages | Static documentation only; no Python backend or secret handling. Public repositories eligible on GitHub Free. 1GB site, soft100GB/month bandwidth and10builds/hour (custom Actions build exception). Terms exclude running a commercial transaction/SaaS service. | Optional later documentation mirror, not broker runtime or commission portal. Pages is currently disabled; no deployment workflow or site activation added. Use repository docs now. |
| Render free web service | 750workspace hours/month; sleeps after15idle minutes, around1minute wakeup; local SQLite lost on sleep/restart/redeploy. No free persistent disk. Free Postgres1GB expires30days. Bandwidth/build excess can bill with a payment method, otherwise suspend. Provider discourages production use. | Unsuitable for this durable local-ledger design. No account/service created. Requires redesigned persistence/auth and explicit approval, not a drop-in free launch. |

Sources (official):
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://render.com/docs/free
- https://docs.pypi.org/trusted-publishers/
- https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository

Repository inspection confirmed public, Issues enabled, Pages disabled, main unchanged and PR draft. Issue templates are prepared on the feature branch and not in the default-branch chooser yet. Manual new-issue instructions work now; no application or usage report was fabricated.

Do not launch a public HTTP service using the existing loopback API: brokerage currently supports stdio only, and multi-tenant authentication, quotas, abuse management and production database operations have not been implemented. Do not treat an A2A declaration in provider metadata as an A2A endpoint.

Approval sequence: (1) review this local pilot and authorize main merge if accepted; (2) authorize a reviewed new package/Registry release with matching versions; (3) optional documentation-only Pages separately. Commercial outreach, partner enrollment and actual contracts remain separately owner-controlled. No hosting purchase is needed to test first independent local usage.
