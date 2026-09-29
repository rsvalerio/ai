# OWASP Top 10:2021 Mapping

> **Version note**: This maps to the OWASP Top 10 2021 release. As of 2026-09-29 [owasp.org/Top10](https://owasp.org/Top10/) redirects to the published 2025 list (A01–A10:2025, with A03 now Software Supply Chain Failures), so this mapping is **pending migration** to 2025 — tracked in the skills repo's backlog. Until then keep citing the 2021 categories below consistently rather than mixing editions; when migrating, revisit SEC rule mappings for category renames or splits (historically e.g. 2017 A07 Cross-Site Scripting was folded into A03 Injection in 2021).

- **A01** Broken Access Control → missing authz, IDOR, privilege escalation
- **A02** Crypto Failures → weak crypto, hardcoded secrets
- **A03** Injection → SQL, command, path traversal
- **A04** Insecure Design → missing security controls
- **A05** Misconfiguration → insecure defaults
- **A06** Vulnerable Components → CVEs in dependencies
- **A07** Auth Failures → weak auth, session issues
- **A08** Software and Data Integrity Failures → insecure deserialization, unsigned updates, CI/CD pipeline integrity
- **A09** Security Logging and Monitoring Failures → insufficient logging of security events, sensitive data in logs
- **A10** SSRF → unvalidated URLs

Map each finding to the most relevant OWASP category when writing SEC-prefixed findings.
