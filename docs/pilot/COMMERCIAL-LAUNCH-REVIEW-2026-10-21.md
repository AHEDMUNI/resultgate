# Commercial launch review — 2026-10-21

## Verified state

PRs 4–8 are open, not merged. Exact reviewed heads and successful CI runs:

| PR | Head | CI run |
|---|---|---|
| 4 | 07d97153e89f2e14d1478ee2bae918d14c0f5eca | 39541144984 |
| 5 | 3da6020d4f738c060e5e3eada95831c95dfb4cf8 | 39541273140 |
| 6 | db92d33358450efa7fd25242a44e3a3d16f3a258 | 39542634087 |
| 7 | bd73a5dad3b4d093f30899cb98ad32ecb4d9913f | 39551509973 |
| 8 baseline | 32a0e90522c517a866c915f895a6ff5429efc658 | 39555175052 |

Merge order: 4 -> 5 -> 6 -> 7 -> 8. Owner previously required separate
merge authorization; none has been given. Prefer merge commits to preserve the
stack ancestry. After each approved merge retarget the next PR to main, inspect
its resulting diff, rerun checks on that updated base, then request its separate
approval. Do not release PyPI or update the official MCP Registry as a side effect.

Baseline Linux suite: 254 tests passed. Updated suite: 257 tests passed; Bandit
found zero source findings; installed dependency compatibility check passed.
Secret-pattern scan found no candidate files in source/deploy/scripts (not a
guarantee covering git history). Browser Use evidence remains tracked and its
one-trial workflow remains disabled with `if: ${{ false }}`. Added a real MCP SDK client communicating
with a separate gateway process over TCP; initialization, tool enumeration,
search, task create/get and dedup passed. This is internal interoperability, NOT
an independent customer or an Internet/TLS test. Additional checks cover shared
credential quota after app restart, tenant isolation, expiry, revocation, duplicate
Authorization/JSON keys, oversized body, hostile Host/Origin and query rejection.
Nginx now rejects mismatched Host explicitly and avoids body/proxy temporary files.
Actual nginx syntax/TLS/host resource validation remains pending on the server.

User reports successful server reboot, HTTP200 and backups. This session could
not connect to ports22/443 from its runtime; that does not establish server outage.
No private keys accessed, host modifications, firewall openings or paid API calls.
Current app is simulation-only. Publishing /mcp will not by itself enable a
commercial transaction. No independent provider/customer has been enrolled.

## One operator inspection, no secrets and no changes

Run this in the existing authenticated server console and return the output:

```sh
sudo sh -c 'systemctl show resultgate -p User -p WorkingDirectory -p FragmentPath; ss -lntp; command -v nginx || true; test ! -d /etc/letsencrypt/live || find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d; ufw status'
```

Also identify the hostname you control for this service. No domain purchase is
requested. A certificate/hostname must be configured and verified before providing
an HTTPS URL. Do not blindly rerun the old installation or expose port8765.
These observations allow a pinned upgrade/proxy command to use actual existing
paths/certificates rather than guesses. Keep the current SSH session open.

Activation gate: backup retention ownership, reviewed/pinned upgrade, nginx -t,
loopback TLS rehearsal, separate limited test tenants, cross-tenant/revocation
checks through proxy, THEN authorized ingress443 and outside-host acceptance.
No administration, /v1 or /healthz should route publicly. Probe each before approval.
Use scripts/mcp_remote_acceptance.py from an external computer with the pinned
project dependencies. It accepts only HTTPS /mcp, prompts secretly for a token,
disables redirects/environment proxies, and reports no tokens or task contents.
It creates synthetic simulation records in a dedicated acceptance tenant only.

## Provider qualification (primary sources checked 2026-10-21)

Firecrawl Standard: customer pays Firecrawl directly. Partner revenue share needs
approval, only new paying referrals AFTER approval qualify; no retroactive share.
Public Platforms page does not specify our rate, agent eligibility, settlement or
refund terms. Its separate affiliate page advertises25% first12 months,15% ongoing;
that is NOT a Platforms quote or accepted ResultGate agreement. Existing inquiry
must be retrieved from its actual sending mailbox before any follow-up. Connected
Gmail search returned no Firecrawl messages; no conclusion about other mailboxes.
Sources: https://www.firecrawl.dev/firecrawl-for-platforms
https://www.firecrawl.dev/affiliates

BrowserAct:30% first paid order,20% eligible purchases for6 months; subscriptions,
credits, renewals/upgrades covered. Last valid referral click before signup;
monthly payment by15th once confirmed balance reaches$50. Refund/dispute cancels
or offsets commission. No explicit headless AI referral eligibility or signed
transaction reporting commitment found. Best second inquiry; NOT approved partner.
Source: https://www.browseract.com/affiliate

Apify:20% first3 months then30%, starter cap$2,500/customer.45-day cookies;
missing attribution requires evidence and discretionary approval. Normally both
3 referred customers and$100 accrued commission are needed for payout, waivable
in writing. Open-source referral provisions can waive the3-customer threshold,
but retain$100. AI referral eligibility and refund reconciliation need confirmation.
Source: https://docs.apify.com/legal/affiliate-program-terms-and-conditions

These programs pay for eligible customer acquisition, not merely executing a task
for an existing customer. Do not infer a commission on every routed API call.
No agreement accepted, referral link fabricated, invoice issued or funds collected.

## BrowserAct inquiry — DRAFT, owner approval required before sending

To: support@browseract.com (published on their affiliate page; ask for partner team)
Subject: ResultGate — authorized AI-agent referrals and verifiable commissions

Hello BrowserAct team,

I am AHED MUNI, founder of ResultGate, an early-stage gateway helping authorized
AI agents discover specialized providers. We are preparing a controlled pilot;
we do not yet have independent paid transactions or an approved partner agreement.

Could your partnership team confirm whether referrals initiated by an AI agent
acting with its customer's explicit authorization qualify for your affiliate
program? Customers would pay BrowserAct directly; ResultGate would hold no funds.

We understand your published rates are 30% on the first paid order and 20% on
eligible purchases for six months, with a $50 payout threshold. Please confirm
which terms would apply to this integration, whether existing users qualify,
and whether API/headless referrals can be attributed without browser cookies.

Can you provide provider-side transaction IDs and signed webhooks or verified
reports covering paid conversions, refunds, disputes and commission settlements?
Please also confirm attribution windows, refund holding periods and payout timing.
Could you waive the minimum payout for one genuine pilot customer so we can verify
settlement? No self-referrals or artificial purchases would be used.

Our proposed first task is extraction of a small, customer-selected public page
into an agreed JSON schema, with explicit consent and acceptance criteria. We
would validate fields against the source and compare integration effort with
direct API use. We will not send live traffic until terms and authorization are clear.

This is an inquiry only, not acceptance of terms or a spending commitment.

Best regards,
AHED MUNI
ResultGate
https://github.com/AHEDMUNI/resultgate

## Actual first-dollar blockers

1. No publicly verified HTTPS MCP endpoint or outside-host limited-client proof.
2. No approved commission agreement/attribution mechanism; payout thresholds matter.
3. No live provider adapter with per-task authorization, bounded spend reservation,
   ambiguous-timeout reconciliation and independent result verification.
4. No unrelated customer with a real task; neither automated tests nor founder
   purchases count. Do not solicit externally until outreach approval.
5. Payment evidence and provider settlement must be verified before reporting cash.

Next commercial gate is provider written eligibility + a customer with genuine
need, not a simulated commission. Prepare the first task only against an accepted
provider contract; customer may pay provider directly, but must authorize the cost.
