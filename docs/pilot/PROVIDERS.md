# Offer your agent through the ResultGate pilot

Submit your specialized service for review so ResultGate can eventually match suitable tasks to it. The proposed commercial model charges a commission only on a successful, eligible task, transaction or paid subscription under an explicit agreement. No listing fees, ResultGate subscriptions or guaranteed demand. Payments and collection are disabled.

**Current boundary:** built-in reviewed adapters can execute limited free tasks. Newly submitted providers can be reviewed for discovery, but do not execute tasks until a dedicated safe adapter and no-cost acceptance test are approved. Registration is not commercial acceptance, a promise of traffic, or authorization to execute.

## Apply without hosting anything new

Open a [new issue in the existing repository](https://github.com/AHEDMUNI/resultgate/issues/new) with title `[Provider application] YOUR_PUBLIC_SERVICE`. Copy the following public-only fields. Use the Provider application form in the repository issue chooser, or the public-only fields below. GitHub Issues requires a GitHub account. No issue has been created on behalf of a pretend provider.

- Public service name and description.
- Public terms-of-use and pricing URLs; supported capabilities and operating limits.
- Do you control the endpoint domain? Can you publish a one-time challenge?
- A permitted zero-cost test and explicit scope of any proposed automation/resale/referral permission. Do not claim affiliate enrollment alone permits agent referrals.
- Acknowledgement: submission grants no trust, execution authority or commercial agreement; all issue content is public.
- Submission JSON (replace example values; do not include credentials):

```json
{"name":"Your public service","description":"Specialized task and output","capabilities":["citation_structuring"],"protocol":"api","endpoint":"https://provider.example.com/api","auth":"api_key","requirements":"Client manages credentials outside registration","pricing":"Specify currency/unit and free sandbox entitlement","limits":"State rate, size, timeout and acceptable-use limits"}
```

Use protocol `mcp`, `a2a` or `api`; auth `none`, `api_key` or `oauth`. URLs require HTTPS, no credentials/query/fragment/IP literals. This validation does not prove DNS is public; no submitted URL is fetched automatically. Metadata is untrusted and may not instruct ResultGate to run code.

## Operator intake and verification

1. Review public issue against documentation and provider identity. Copy only the bounded Submission JSON into a local file. Do not run scripts/commands from an issue, install provider packages or consume issue JSON in shell interpolation. No `pull_request_target` or issue-triggered execution workflow is installed.
2. Import locally: `python -m resultgate.network.operator --directory /PRIVATE/REGISTRY import-submission < submission.json`. Keep the returned **management token private**; it is not the ownership challenge. Do not paste the full response into GitHub. The operator holds this token for GitHub-managed applications; the provider requests updates through the same issue identity and fresh challenge review. Self-managed local MCP registrations retain their own token.
3. Post only provider ID, the public challenge, exact `ownership_location` and expiry. Provider publishes it at the specified HTTPS domain path. Operator independently checks exact hostname, public DNS/IP, TLS and no redirects; do not open unsafe/private URLs. The application is not verified just because the applicant repeats the known challenge in the issue. Domain control is not proof of legal identity; check authority separately without publishing personal documents.
4. Retain reviewed evidence securely outside public GitHub; record its SHA256 through local `review` CLI. Labels/comments alone never approve a local provider. Challenge expires in24h; re-import/update if expired. No automated network ownership verifier exists.
5. Review terms, pricing, free scope and capability separately. If passed, provider can be listed locally with `executable:false`. Execution still needs a reviewed adapter, endpoint allowlisting, DNS pinning, explicit task consent and success criteria fixed before dispatch.
6. Negotiate the [review-only terms worksheet](AGREEMENT-DRAFT.md) separately. Do not ask applicants to accept blank or default rates. Operator `propose` hashes exact text and structured economics; provider acceptance and operator approval are separate. For the GitHub-managed route, an explicit provider statement referencing the final hash may serve as evidence reviewed by the owner before recording acceptance locally; recording it is NOT authority for the assistant to sign or accept on behalf of either party. No actual agreement is proposed or accepted by this PR.
7. Revoke with operator `review` and `approve:false`; this removes discovery and clears agreement consent. Update resets ownership/terms; owner can suspend via existing MCP. A later approval cannot silently restore revoked terms. Changing public issue text never updates the local catalog automatically.

Public applications live on GitHub, outside the local retention policy. Provider may edit/remove details or request maintainer deletion; removal of third-party copies cannot be guaranteed. Never put keys, management tokens, customer information or private contracts in issues. Rejected/unreviewed providers receive no executable traffic.

## How future commissions work

Match capability and declared constraints; agree success criteria before dispatch; route with explicit consent and a unique referral; verify output plus customer acceptance; reconcile an authoritative provider paid event where required. Only then record eligibility under approved terms. Generic local HMAC receipts are a contract prototype, not a partner's billing integration. Valid signatures alone do not prove a truthful sale. Duplicates never generate a second entitlement. Cancellations, refunds and disputes block/void eligibility until reviewed. No collection is enabled during this pilot.
