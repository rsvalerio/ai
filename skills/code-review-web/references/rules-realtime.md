# Real-Time Rules — RT (socket.io-client / WebSocket)

> RT rules cover client-side real-time collaboration over `socket.io-client` (and raw WebSocket). They are the web analog of a message-bus ruleset. For general async patterns see ASYNC rules; for crypto of broadcast payloads see SEC-5--9. Security-relevant RT findings map to the OWASP WebSocket Security Cheat Sheet and OWASP Top 10:2025 (see [owasp-2025.md](owasp-2025.md)).

## Real-Time: Inbound Message Safety (typical severity: High--Critical)

**Detection heuristics** — search for: `socket.on("...", (data) => ...)` handlers that destructure/use `data` without validation, `JSON.parse` on socket payloads without try/catch, decrypted payloads applied to scene/state without shape checks.

- **RT-1.** Validate every inbound message before use: check the event shape, wrap parsing/decryption in try/catch, and reject malformed payloads instead of applying them. A bad message must not crash the handler or inject untrusted data into application state. — owasp.org WebSocket Security Cheat Sheet
- **RT-2.** Do not treat a live connection as authorization for every operation. Each privileged action (joining a room, persisting a scene, mutating shared state) must be authorized server-side; the client must not assume "connected" means "allowed". Client-side gating is UX only (mirrors SEC-15). — owasp.org WebSocket Security Cheat Sheet
- **RT-3.** Bound resource consumption: cap/validate inbound payload size and guard against floods (the server should enforce `maxPayload` and rate limits; the client should not blindly process unbounded streams of events). — owasp.org WebSocket Security Cheat Sheet

## Real-Time: Traffic Control & Correctness (typical severity: Medium--High)

- **RT-4.** Throttle high-frequency *volatile* signals (cursor/pointer position) and debounce *persisted* broadcasts (full scene snapshots) so the socket isn't flooded — e.g. cursor updates throttled to ~30 fps (~33 ms) and snapshot saves debounced to ~1 s. Use the platform's volatile/ephemeral channel for transient data and the durable channel for state that must persist. Magic intervals belong in named constants (READ-4).
- **RT-5.** Watermark/deduplicate echoed updates: track the last broadcast version/sequence so the client doesn't re-apply or re-broadcast its own change (feedback loop). Reconcile remote and local element sets with a deterministic merge rather than last-writer-wins clobbering. — collaboration-protocol pattern (e.g. Excalidraw `reconcileElements`)
- **RT-6.** Manage socket lifecycle deterministically: create the connection on join, remove **all** listeners and disconnect on `stop()`/unmount (no leaked handlers across rooms), and have an explicit reconnection/backoff and presence-cleanup story. A handler registered in an Effect must be removed in its cleanup (REACT-7).

## Real-Time: Encryption & Secrets (typical severity: High)

- **RT-7.** Encrypt broadcast payloads end-to-end when the relay is untrusted, with a fresh IV per message (SEC-5) and a CSPRNG-generated room key (SEC-6); carry the room key in the URL fragment, never the query string or the server (SEC-12). Never log decrypted payloads, keys, or IVs (SEC-8). — maps to SEC-5--9, SEC-12
