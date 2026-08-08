# NATS and JetStream Rules

## NATS Connection (typical severity: High)

> NATS rules cover [async-nats](https://crates.io/crates/async-nats) specific patterns. The `async-nats` crate requires **tokio** as its async runtime. For general async patterns, see ASYNC rules. For concurrency primitives, see CONC rules.

- **NATS-1.** Use `ConnectOptions::new()` instead of bare `connect()`; bare connect lacks event visibility, reconnect control, and client naming
- **NATS-2.** Set `.name()` for server-side debugging and connection identification
- **NATS-3.** Configure `.event_callback()` for connection state visibility (connect, disconnect, reconnect, error)
- **NATS-4.** Set `.reconnect_delay_callback()` with exponential backoff
- **NATS-5.** Use `.retry_on_initial_connect()` for container orchestration environments
- **NATS-6.** Configure `.connection_timeout()` and `.ping_interval()` appropriately for the environment
- **NATS-7.** Call `client.drain()` on graceful shutdown
- **NATS-8.** Clone client (cheap) rather than recreating connections

## NATS Streams (typical severity: High)

- **NATS-9.** Set explicit `retention` policy (Limits / Interest / WorkQueue)
- **NATS-10.** Configure `max_bytes` and/or `max_msgs` resource limits
- **NATS-11.** Set `num_replicas` >= 3 for clustered production deployments with 5+ nodes; for 3-node clusters, replicas=3 means every node stores every stream — acceptable for small clusters and provides 1-node fault tolerance (Raft quorum = 2-of-3), whereas replicas=2 tolerates 0 failures (quorum = 2-of-2); adjust based on actual cluster size and fault-tolerance requirements. **Maintenance**: quorum math is based on JetStream's Raft consensus as of NATS 2.x — verify against [NATS docs](https://docs.nats.io/running-a-nats-service/configuration/clustering/jetstream_clustering) if the server version differs
- **NATS-12.** Configure `duplicate_window` for idempotency
- **NATS-13.** Enable `allow_direct` only when needed for direct-get API access (key-value stores, direct message retrieval)
- **NATS-14.** Use explicit `storage` type (File vs Memory)

## NATS Consumers (typical severity: High)

- **NATS-15.** Use durable consumers for persistent subscriptions (projections, read models)
- **NATS-16.** Configure `ack_wait` based on processing time
- **NATS-17.** Set `max_ack_pending` for consumer-level backpressure
- **NATS-18.** Use pull consumers for controlled message fetching; set `max_waiting` on pull consumers to limit outstanding pull requests
- **NATS-19.** Use `message.ack_with(AckKind::InProgress).await` for long-running handlers
- **NATS-20.** Handle `AckKind::Nak(Option<Duration>)` for retriable failures

## NATS Observability (typical severity: Medium)

- **NATS-21.** Handle connection events configured via NATS-3 — do not silently ignore; log state changes without credentials (see SEC-21 for secret handling in logs)
- **NATS-22.** Track reconnects, publish/subscribe counts, consumer lag; instrument manually or use NATS server monitoring endpoints. **Maintenance**: verify async-nats metrics support against current crate docs — built-in metrics availability may change between releases
- **NATS-23.** Ensure failures are visible (no swallow-and-ignore); propagate or log with context

## NATS Subject Design (typical severity: Low)

- **NATS-24.** Use hierarchical subject patterns for filtering efficiency; avoid flat subjects, inconsistent naming, or hardcoded subjects

## NATS Backpressure & Flow Control (typical severity: High)

- **NATS-25.** Set bounded capacity on subscription buffers (`ConnectOptions::subscription_capacity()`) to prevent unbounded memory growth
- **NATS-26.** Enable server-side flow control on push consumers when message rates may exceed consumer processing speed
- **NATS-27.** Use publish acknowledgements in JetStream (`jetstream.publish(subject, payload).await?.await?` — first await sends, second await confirms server ack) to detect backpressure from the server; handle `Err` (server full / slow) with retry or backoff

> **NATS Security**: TLS, credentials, and secrets concerns are covered by SEC rules. See [nats-security](nats-security.md) for NATS-specific SEC rule mapping.
