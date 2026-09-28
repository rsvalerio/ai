# OWASP Top 10:2021 Mapping

> **Version note**: This maps to the OWASP Top 10 2021 release, which remains the current published edition as of 2026-04-16. OWASP has signalled work on a 2025 edition (release-candidate drafts circulating) but no final ranking has been published — continue mapping to 2021 categories until a final 2025 release is announced at [owasp.org/Top10](https://owasp.org/Top10/). When the 2025 list is finalized, revisit SEC rule mappings for category renames or splits (historically e.g. 2017 A07 Cross-Site Scripting was folded into A03 Injection in 2021).

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
