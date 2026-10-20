# Public release verification — 2026-10-20

## Actual publication
- PyPI version 0.1.1: https://pypi.org/project/resultgate-pilot/0.1.1/
- Successful trusted-publishing run: https://github.com/AHEDMUNI/resultgate/actions/runs/39516288765
- Published wheel and source distribution, using GitHub OIDC and attestations; no stored API keys.
- Official MCP Registry: io.github.AHEDMUNI/resultgate, 0.1.1, active and latest.
- Registry publication run: https://github.com/AHEDMUNI/resultgate/actions/runs/39516521014
- Public registry lookup: https://registry.modelcontextprotocol.io/v0.1/servers/io.github.AHEDMUNI%2Fresultgate/versions/0.1.1
- Public UI search: https://registry.modelcontextprotocol.io/?q=io.github.AHEDMUNI%2Fresultgate

## Verification
- Release workflow completed unit tests, identity/license checks, wheel/sdist build, Twine strict checks and isolated MCP acceptance before upload.
- A new local Python 3.12 virtual environment installed resultgate-pilot==0.1.1 from https://pypi.org/simple with --no-cache-dir.
- Isolated MCP acceptance initialized the server, discovered check_extraction and check_citations, and exercised pass/fail/unknown behavior and privacy/deduplication. pip check passed.
- The installed resultgate-pilot executable responds to --help.
- Anonymous HTTP retrieval of the official registry entry confirmed the exact PyPI package/version, uvx runtime and stdio transport.
- The public registry UI showed ResultGate in search and as active.

These are internal verification activities, not independent adoption or production accuracy measurements.

## Privacy and adoption
Default: no measurement files and no network telemetry.
Opt-in: local counts, daily aggregates, random installation identifier, HMAC task deduplication, 30-date retention.
Real-task labels are caller declarations. Summaries alone cannot establish independence.
Test/demo/retry events are excluded; repeated exports must be reconciled.
External participants can voluntarily submit the repository usage-report issue after reviewing the privacy notice. Public reports expose their GitHub account; raw prompts, source data, task IDs and local identity files must not be posted.
At this check there were no GitHub issues/reports. Verified external real-task uses: 0; verified returning users: 0; revenue: $0.
No centralized collector or automatic monitoring is running. Unreported local usage is unobservable.

## Remaining
Glama Add Server requires account signup and acceptance of its terms; no account was created or terms accepted. glama.json is ready.
Independent discovery/use by someone outside the project is still unproven. Directory listing and package downloads are not proof of it.
No paid service, hosting subscription or payment integration was enabled.

This report supersedes the publication status in VERIFICATION-2026-10-20.md.
