# agents.allubiyerbamate.com — approved staged activation

Owner approved the hostname, sequential PR4–8 merges and one BrowserAct inquiry
on 2026-10-21. No additional service purchase is approved. This is configuration
preparation, not evidence that DNS, TLS, public ingress or deployment is complete.

## DNS: one additive record

At the authoritative DNS provider (owner reports Registered Agents Inc), add:

| Type | Name | Value | TTL |
|---|---|---|---|
| A | agents | 64.227.3.178 | 300, or provider default |

If the UI requires an absolute name, use agents.allubiyerbamate.com. Inspect the
existing agents name first: do not overwrite an existing A/AAAA/CNAME service.
Do not change nameservers, apex/@, www, MX, TXT, Shopify, mail, or global CAA records.
Do not add AAAA without a separately validated IPv6 path. If inherited CAA blocks
Let's Encrypt, stop and review a narrowly scoped solution; do not alter other services.
Local DNS resolution in the assistant runtime failed for BOTH apex and subdomain,
so it provides no evidence that the public record is absent. Validate from public
DNS and authoritative nameservers after the owner adds it.

## Read-only host prerequisite

No reinstallation or reboot requested. In the existing server console run:

```sh
sudo sh -c 'systemctl show resultgate -p User -p WorkingDirectory -p FragmentPath; ss -lntp; command -v nginx || true; test ! -d /etc/letsencrypt/live || find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d; ufw status'
```

Return the output, not credentials. We need actual source/venv/proxy/certificate
paths before selecting upgrade commands. Never upload the SSH private key. This
runtime has no authenticated server connection.

## Prepared files and deployment gates

- nginx-acme-agents.conf.staged: port80 serves only ACME challenge files, otherwise404.
- nginx-agents.conf.staged: TLS1.2/1.3, fixed hostname, only /mcp proxied to loopback,
  body/rate/connection limits, no query/token logging, hostile Origin rejected.
- Existing resultgate systemd service continues to bind127.0.0.1:8765.

Inspect existing nginx configurations first. Install isolated new vhost files only;
never overwrite an existing default or another service's vhost. The files are not
included/activated automatically by this repository or by merges.

Use free Let's Encrypt certificate via Certbot webroot after DNS resolves to this
server. This requires port80 reachable for challenge issuance/renewal, but does NOT
expose MCP there. Keep443 closed or restricted to the tester until proxy security
checks pass. Verify DO cloud firewall as well as UFW; retain SSH access unchanged.
Use `certbot certonly --webroot -w /var/lib/resultgate-acme -d agents.allubiyerbamate.com`
interactively after the ACME-only vhost is installed and `nginx -t` succeeds. Let
the owner review any certificate authority terms; do not pass automatic acceptance.
No paid certificate, new domain, DNS provider migration or wildcard is needed.

Actual server validation is mandatory: certificate hostname/chain/expiry, nginx -t,
local HTTPS (curl --resolve, no -k), denied anonymous access, approved limited
requester success, cross-tenant rejection and immediate revocation, hostile
Host/Origin and query rejection, /healthz and /v1 inaccessible externally.
Configure certbot renewal timer and test `certbot renew --dry-run`; deploy hook
must validate nginx then reload it. Check logrotate and backup retention/monitoring.
No assertion of actual nginx validation: nginx was unavailable in this runtime.

Only after local TLS/security validation, open443 and run the supplied
scripts/mcp_remote_acceptance.py from another machine with an isolated test tenant.
Token entry is hidden. Never place tokens in command arguments, chat or URLs.
Record this as synthetic external acceptance, not independent customer adoption.
Once verified, the intended endpoint is https://agents.allubiyerbamate.com/mcp.
Do not advertise it as active before evidence exists.

Real paid execution remains disabled. First independent commercial use additionally
requires provider agreement, attributable customer payment, reviewed live adapter,
explicit per-task consent/budget and verifiable provider result/payment evidence.

References (reviewed 2026-10-21):
https://eff-certbot.readthedocs.io/en/stable/using.html
https://nginx.org/en/docs/http/ngx_http_ssl_module.html
