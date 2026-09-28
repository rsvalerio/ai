# NATS Security Patterns

NATS-specific instantiation of SEC rules. Each row maps to the owning SEC rule — do not create separate findings; file under the SEC rule ID.

> **Severity escalation**: NATS deployments typically carry message-loss and data-exposure risk that justifies escalating certain findings above the "typical severity" listed in the SEC rules. Missing TLS or auth on a message bus can expose every connected service, so these are Critical rather than the default High for generic configuration issues. Adjust downward for isolated internal networks.

| SEC Rule | What to find (NATS-specific) | OWASP | Severity |
|----------|------------------------------|-------|----------|
| **SEC-8** (hardcoded secrets) | NATS URLs with embedded credentials (`nats://user:pass@host`); hardcoded NKey seeds or NKeys committed to VCS | A02, A05 | Critical |
| **SEC-21** (secrets in logs/errors) | Connection errors logged with full URL containing secrets; JWT tokens logged or in error messages | A02, A09 | High |
| **SEC-29** (secure defaults) | `connect()` without `.require_tls()` in production; missing `.user_and_password()`, `.token()`, or `.credentials_file()`; using `connect()` defaults (no TLS, no auth) in production | A02, A05, A07 | Critical |
