# OWASP Top 10:2025 Mapping

> **Version note**: This maps to the OWASP Top 10 **2025** edition, final since 2025-12-24 (the release-candidate label was dropped in the OWASP/Top10 repository that day). Source: [top10.owasp.org/2025](https://top10.owasp.org/2025/) (where [owasp.org/Top10](https://owasp.org/Top10/) redirects), checked 2026-10-03. 2025 renumbered most categories: Injection is **A05**, not A03; SSRF is folded into **A01**; **A03** is Software Supply Chain Failures; **A10** is Mishandling of Exceptional Conditions. Placements below follow the CWE lists on each category page. A permissive CORS policy (CWE-942) is **A02** Misconfiguration; the missing server-side authorization behind it is **A01**.

- **A01** Broken Access Control → missing server-side authz, client-only permission checks, capability-token leakage, open redirects, credentials sent to untrusted origins (SEC-3 for redirects, SEC-12, SEC-15, RT-2)
- **A02** Security Misconfiguration → production source maps, permissive CORS, secrets in `VITE_` env vars, exposed debug surfaces (SEC-11, SEC-15, SEC-16)
- **A03** Software Supply Chain Failures → known CVEs, unpinned or unaudited packages, untrusted CDN scripts (SEC-17)
- **A04** Cryptographic Failures → IV reuse, `Math.random` for secrets, extractable keys, weak or unauthenticated encryption (SEC-5--7, SEC-9, RT-7)
- **A05** Injection → XSS via `dangerouslySetInnerHTML`/`innerHTML`/unsafe sinks, `javascript:`/`data:` URLs, template injection (SEC-1--4)
- **A06** Insecure Design → client-side enforcement of server-side security, trust-boundary violations, missing rate or size limits, secrets in query strings (SEC-12, SEC-13, RT-1, RT-3)
- **A07** Authentication Failures → hardcoded credentials, weak session handling, trusting connection state for identity (SEC-10, RT-2)
- **A08** Software or Data Integrity Failures → unvalidated data from network/WebSocket/`postMessage`/`localStorage`, scripts without integrity checks (SEC-13, SEC-17, RT-1)
- **A09** Security Logging and Alerting Failures → secrets/PII/tokens in client logs or telemetry (SEC-8, SEC-14)
- **A10** Mishandling of Exceptional Conditions → malformed input crashing a handler, failing open on error, sensitive detail in error messages (RT-1)

When writing a SEC- or RT-prefixed security finding, note the OWASP category in the task body.
