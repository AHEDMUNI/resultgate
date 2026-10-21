# ResultGate commercial information site

Operator: ALLUBI Yerba Mate LLC, as supplied by owner. Public contacts use existing
support@allubiyerbamate.com and admin@allubiyerbamate.com. No invented phone, physical
address, customer figures, provider approvals, payment availability or PCI certification.

Nine static pages, one CSS asset and five text/JSON/XML discovery assets, no JavaScript, trackers, card fields, forms,
external fonts or browser storage. Provider interest goes through email, not an assumed
contract. Commission is 15% on eligible paid transactions and adjusted for refunds/disputes.
Digital fulfillment/provider responsibilities and current prelaunch status are explicit.

Owner requested publication on agents.allubiyerbamate.com only. The deploy script
identifies the existing dedicated TLS vhost, replaces only its default root-404 stanza or an exactly recognized generated static block,
adds fifteen exact public routes and preserves the MCP block. Unknown/shared configurations
stop without modifications. Existing private routes stay 404. No app restart or live
payment enablement. Previous nginx config backed up; validation failure triggers rollback.
Run `sudo python3 deploy/publish_business_site.py` from this pinned reviewed checkout.
Nginx must already be serving the hostname with its valid certificate.

Tests: test_business_site.py checks internal links, absent active content and unchanged
MCP stanza. Host `nginx -t` and HTTP status checks occur during deployment, not before.
After success, independently request `/`, `/terms`, `/privacy`, `/refunds`, `/providers`,
`/contact` and `/mcp` from outside the host. Expected 200 for pages and 401 for anonymous MCP.
No claim of deployment until these checks are observed.

Stripe checklist reviewed: https://docs.stripe.com/get-started/checklist/website
The site explains the business and policies; Stripe acceptance is not guaranteed.
There is no published physical address or telephone because none was supplied for
ResultGate publication. Stripe may request additional contact information or operational
proof. Policy text should be reviewed against the final live order/provider agreements
before payments launch. Website publication is not consent to Stripe's financial terms.

Launch update: /services is an honest empty catalog; /request offers email/public
GitHub interest submission (not a purchase); /agents documents manually provisioned
simulation access. /catalog.json, /resultgate.json, /llms.txt, /robots.txt and
/sitemap.xml aid discovery but do not prove indexing, traffic or adoption.

Existing sites can run the same pinned publisher: it recognizes only its exact
legacy/current generated block, preserves every byte outside that block, verifies
all returned asset bytes and rolls back on failure. No MCP or app update.
`python3 deploy/launch_host_status.py` returns a safe installed-package/service report.
See docs/launch/LAUNCH-AUDIT.md for remaining commercial gates and 72-hour rules.
