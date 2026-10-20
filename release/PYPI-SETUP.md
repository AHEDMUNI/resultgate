# PyPI Trusted Publishing setup

Package: resultgate-pilot, version 0.1.1. No passwords or API tokens are used.

The owner must add a **pending publisher** under https://pypi.org/manage/account/publishing/ using the GitHub Actions form:

| Field | Exact value |
| --- | --- |
| PyPI Project Name | resultgate-pilot |
| Owner | AHEDMUNI |
| Repository name | resultgate |
| Workflow name / filename | publish-pypi.yml |
| Environment name | pypi |

Workflow path in this repository: .github/workflows/publish-pypi.yml. Enter only the filename on PyPI, not the path.
Pending publishers do not reserve package names. Account email verification and PyPI account security requirements must be completed by the owner.

## Execution
The initial workflow push runs build/tests only. Manual runs default to publish=false.
After pending publisher setup, open GitHub Actions > Build and publish to PyPI > Run workflow, select main and enable publish only for an approved release.
The workflow tests the source, builds sdist and wheel, checks package metadata with Twine, installs the wheel in a fresh environment and exercises both MCP tools before allowing publication.
The publish job uses the pypi GitHub environment, OIDC id-token:write and PyPA's publish action with attestations. It does not check out or execute project code with the OIDC permission.
All third-party actions are pinned to reviewed resolved commit IDs. No self-hosted or larger paid runner is configured.

Configure the GitHub pypi environment to allow deployments from main only and, if desired, a required reviewer. These protection settings have NOT been configured by this workflow file; naming an environment does not enable protection rules.

After publication, verify the PyPI version/artifacts, install from PyPI in a fresh environment, run scripts/acceptance.py and then submit server.json to the official MCP registry.
Internal CI and acceptance runs count as zero external usage.
