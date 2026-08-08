# OWASP Top 10:2025 Mapping

> **Version note**: This maps to the OWASP Top 10 **2025** edition. Notable change from 2021: CORS / misconfigured cross-origin access is folded under **A01 Broken Access Control**, and Software Supply Chain concerns are elevated. If the project standardizes on the 2021 edition, re-map accordingly. Verify the current ranking at [owasp.org/Top10](https://owasp.org/Top10/) when auditing — categories occasionally rename or split between editions.

Map each SEC (and security-relevant RT) finding to the most relevant category:

- **A01** Broken Access Control → missing/ineffective authz, client-only permission checks, CORS misconfiguration, capability-token leakage (SEC-12, SEC-15, RT-2)
- **A02** Cryptographic Failures → IV reuse, `Math.random` for secrets, extractable keys, weak/unauthenticated encryption, secrets in logs (SEC-5--9, SEC-8, RT-7)
- **A03** Injection → XSS via `dangerouslySetInnerHTML`/`innerHTML`/unsafe sinks, `javascript:`/`data:` URLs, template injection (SEC-1--4)
- **A04** Insecure Design → missing security controls by design (no input validation boundary, no rate/size limits) (SEC-13, RT-1, RT-3)
- **A05** Security Misconfiguration → production source maps, insecure defaults, exposed debug surfaces (SEC-16)
- **A06** Vulnerable & Outdated Components → known CVEs in dependencies, unpinned/unaudited packages (SEC-17)
- **A07** Identification & Authentication Failures → weak auth/session handling on the client, trusting connection state for identity (RT-2, SEC-15)
- **A08** Software & Data Integrity Failures → unvalidated data from network/WebSocket/`postMessage`/`localStorage`, supply-chain integrity (SEC-13, SEC-17, RT-1)
- **A09** Security Logging & Monitoring Failures → secrets/PII/tokens in client logs or telemetry, insufficient error visibility (SEC-8, SEC-14)
- **A10** Server-Side Request Forgery / Mishandled URLs → unvalidated user-controlled URLs used in requests or navigation (SEC-3)

When writing a SEC- or RT-prefixed security finding, note the OWASP category in the task body.
