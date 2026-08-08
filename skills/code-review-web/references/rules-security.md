# Security Rules — SEC

Frontend/browser security rules. Each finding maps to an OWASP Top 10:2025 category (see [owasp-2025.md](owasp-2025.md)). Grounded in the OWASP cheat sheets, MDN Web Crypto, W3C WebCrypto, and Vite security docs.

## Security: XSS & DOM Injection (typical severity: Critical)

**Detection heuristics** — search for: `dangerouslySetInnerHTML`, `.innerHTML`/`.outerHTML`/`document.write`, `eval`/`new Function`, user-controlled values in `href`/`src`, template/HTML built by string concatenation from untrusted input.

- **SEC-1.** Do not pass unsanitized data to `dangerouslySetInnerHTML` (React) or `.innerHTML`/`.outerHTML` — it executes attacker script. If raw HTML is genuinely required, sanitize first with a maintained library (DOMPurify) kept patched; hand-rolled filtering is routinely bypassed. — owasp.org Cross-Site Scripting Prevention Cheat Sheet
- **SEC-2.** Prefer safe DOM sinks for untrusted data — render via React children / JSX text or `textContent`, never `innerHTML`/`document.write`/`eval`/`new Function`; safe sinks render data inert instead of executing it. — owasp.org DOM-based XSS Prevention Cheat Sheet
- **SEC-3.** Validate user-supplied URLs against an `http(s)` allowlist before using them in `href`/`src`/`window.open`; `javascript:` and untrusted `data:` URLs execute script on interaction. — owasp.org DOM-based XSS Prevention Cheat Sheet
- **SEC-4.** Never build framework templates or markup by string-concatenating untrusted input; bind data through React's escaping so data cannot become code. Where supported, enforce Trusted Types via CSP to make dangerous sinks reject raw strings at the browser level. — owasp.org XSS / DOM-based XSS Cheat Sheets

## Security: Web Crypto (SubtleCrypto) (typical severity: High--Critical)

**Detection heuristics** — search for: `crypto.subtle.encrypt`/`decrypt` with a reused or fixed IV, `Math.random()` near security values, `generateKey`/`importKey` with `extractable: true`, key/IV/plaintext passed to `console.*` or telemetry, ad-hoc base64 of binary key material.

- **SEC-5.** Generate a fresh, random 96-bit (12-byte) IV for **every** AES-GCM encryption with a given key. Reusing an IV with the same key is catastrophic — it breaks both confidentiality and authentication. Verify the IV comes from `crypto.getRandomValues()` per call and is not cached or counter-derived without a documented unique-nonce scheme. — developer.mozilla.org/en-US/docs/Web/API/AesGcmParams
- **SEC-6.** Generate IVs, salts, and keys with `crypto.getRandomValues()` or `crypto.subtle.generateKey()`, never `Math.random()` — only the Web Crypto RNG is cryptographically strong. `Math.random()` for any security value (key, nonce, token, ID used as a secret) is a Critical finding. — developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues
- **SEC-7.** Create `CryptoKey`s with `extractable: false` unless export is genuinely required; an extractable key can be read back out of the object and leaked. When export *is* required (e.g. capability URLs that carry the key), confine extraction to that path and document it. — developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/generateKey
- **SEC-8.** Never log, serialize to telemetry, or send to analytics any raw key, IV, or plaintext; logged secrets propagate into aggregation systems and crash reports. — owasp.org Logging Cheat Sheet
- **SEC-9.** Use authenticated encryption (AES-GCM) — do not pair unauthenticated modes without a MAC. Use a consistent, validated base64url encoding when transporting binary crypto material in URLs/JSON; mismatched encodings silently corrupt keys/IVs. — w3.org/TR/webcrypto-2/

## Security: Secrets in the Frontend (typical severity: Critical)

**Detection heuristics** — search for: string literals matching key/token/password patterns, non-`VITE_` secrets expected at runtime in client code, secret/capability tokens placed in query strings, `.env` files committed to VCS.

- **SEC-10.** Never hardcode API keys, tokens, or credentials in frontend source — everything shipped to the browser is fully readable in the bundle and devtools. Move secret-bearing calls behind a backend proxy. — owasp.org / sprocketsecurity.com (Vite secret leak)
- **SEC-11.** Treat every `VITE_`-prefixed env var as **public** — Vite inlines it into the client bundle at build time. A real secret must never use a `VITE_` var; keep secrets server-side and proxy. Keep non-public env values in git-ignored `.env.local`, never committed. — vite.dev/guide/env-and-mode, github.com/vitejs/vite (env exposure)
- **SEC-12.** Carry capability/secret tokens in the URL **fragment** (`#…`), which browsers do not send to the server, rather than the query string (which is logged by servers/proxies and sent in `Referer`). This is the correct pattern for share-link keys. — w3.org/TR/capability-urls/

## Security: Network & Data Handling (typical severity: High)

**Detection heuristics** — search for: `fetch`/`axios` responses used without shape validation, `credentials: "include"` to non-trusted origins, request/response bodies or tokens logged, missing `response.ok` handling (see ASYNC-4).

- **SEC-13.** Validate and schema-check untrusted responses (fetch, WebSocket, `postMessage`, `localStorage`) before use — never trust the shape of data crossing a boundary; a compromised or changed endpoint otherwise breaks runtime assumptions or injects bad data. Prefer a runtime validator (e.g. Zod) for security-relevant payloads. — owasp.org AJAX Security Cheat Sheet
- **SEC-14.** Do not log tokens, PII, or full request/response bodies to the console or telemetry; client logs are user-accessible and frequently shipped to third parties (mirrors SEC-8, READ-8). — owasp.org Logging Cheat Sheet
- **SEC-15.** Send credentials (`credentials: "include"`, cookies, auth headers) only to trusted origins; do not broaden CORS or attach auth to third-party requests. Authorize sensitive actions server-side — client-side checks are UX, not security (OWASP 2025 folds CORS under A01 Broken Access Control). — owasp.org/Top10/2025 A01

## Security: Build & Dependencies (typical severity: High)

- **SEC-16.** Do not ship readable source maps to production (or restrict their access); `build.sourcemap` true on a public deploy exposes full source and embedded constants. — vite.dev/config/build-options (build.sourcemap)
- **SEC-17.** Audit and pin dependencies: run `npm audit`/SCA in CI, commit the lockfile, and review new/transitive packages — a frontend bundle inherits its whole supply chain, a primary attack vector. — owasp.org/Top10/2025, github.com/vitejs/vite/security

> **Real-time security**: socket.io / WebSocket validation, per-action authorization, and message-size/rate limits are covered by RT rules but are security concerns — see [rules-realtime.md](rules-realtime.md) and the OWASP WebSocket Security Cheat Sheet. File those under the RT rule unless the issue is purely a secret/crypto/XSS concern, in which case use the SEC rule.
