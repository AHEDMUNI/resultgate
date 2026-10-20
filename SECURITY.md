# Security scope

ResultGate is a local tool. It treats inputs as data, does not execute code, fetch URLs, load remote schemas or call LLM providers. `pass` is limited to the caller-supplied contract; a malicious caller can supply fabricated evidence and receive a pass. Never use this as a standalone safety, truth, compliance or payment authorization system.

HTTP is an optional loopback-only machine API with bearer authentication, Host filtering, Origin rejection, body/read limits and no access logs. Keep the token outside the repository and rotate it if exposed. Do not expose this development service publicly. No multi-tenant quotas, production TLS ingress or public service security review exists.

Bounded validator work is tested. MCP SDK transport may parse the incoming frame before our per-tool limits apply; use only a trusted local client and apply OS process limits for adversarial stress testing. OS users who control the process or measurement directory are outside the protection boundary. The program does not protect other software from injected content they choose to interpret.

Dependency/advisory checks report only issues known to their data source on the audit date, not proof of security. Re-run before release. Private vulnerability reporting is not yet configured. Do not disclose vulnerability details publicly; a confidential reporting channel must be established before collecting such reports. Do not put secrets or confidential payloads into public issues.
