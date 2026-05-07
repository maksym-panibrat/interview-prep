# Idempotency

## 1. TL;DR

An operation is **idempotent** if executing it N times produces the same effect as executing it once. [Retries](resilience-four-pack.md) are inevitable — load balancers retry, queues redeliver, clients refresh, humans double-click — so every state-mutating endpoint needs an idempotency story or it will charge cards twice and send duplicate emails. The "exactly-once delivery" myth dies here: across an unreliable network you cannot guarantee a message arrives exactly once, but you *can* guarantee **exactly-once effects** by combining at-least-once delivery with server-side dedup.

## 2. How it works

Two ingredients: a **key** that names the logical operation, and a **store** that remembers what happened the first time.

### Idempotency key

A unique ID per logical operation, supplied by the caller (`Idempotency-Key: 7f3c...`) or derived from request content (hash of the body, primary key + timestamp). The contract: same key → same effect. The server records `key → result` on first execution and returns the stored result on every replay.

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant DB as Idempotency store
    C->>S: POST /charges, Idempotency-Key: K1
    S->>DB: INSERT (K1, PENDING)
    S->>S: charge card
    S->>DB: UPDATE K1 -> DONE, response R1
    S-->>C: 200 + receipt R1
    Note over C,S: ack lost; client retries with same key
    C->>S: POST /charges, Idempotency-Key: K1
    S->>DB: SELECT K1 -> DONE, R1
    S-->>C: 200 + receipt R1 (no re-charge)
```

### Storage choices

- **Redis with TTL.** Cheap and fast, but lossy under failover; an unreplicated key can disappear between the first and second request.
- **Database row with a unique constraint on the key.** Durable, costlier per write, and gives you transactional atomicity with the side effect.
- **Both.** Redis as the hot path, DB as the source of truth — but only the DB writes are authoritative.

### The atomicity problem

The key write and the side effect must commit atomically. If you write the key first and then the side effect crashes, the next retry returns "already done" for work that never happened. If you do the side effect first and then write the key, a crash leaves no dedup record and the next retry re-executes.

When the side effect lives in the same database, wrap both in one transaction:

```
BEGIN;
  INSERT INTO idempotency_keys (key, status) VALUES ('K1', 'PENDING');
  -- unique constraint on key fails here on retry -> caller goes to dedup branch
  INSERT INTO charges (...) VALUES (...);
  UPDATE idempotency_keys SET status='DONE', response=$1 WHERE key='K1';
COMMIT;
```

When the side effect crosses a boundary (external API, message bus), transactions don't span it. Use a **two-phase pattern**: reserve the key as `PENDING`, perform the side effect, then mark `DONE` with the stored response. A reconciler sweeps long-`PENDING` keys and either confirms or rolls them forward — the price of crossing an atomicity boundary.

### Natural idempotency

The cheapest dedup is one you don't have to write. Prefer inherently idempotent operations over key-based dedup:

- **UPSERT** (`INSERT ... ON CONFLICT UPDATE`) over blind INSERT.
- **Set-state-X** (`SET balance = 100`) over **increment-by-X** (`balance += 10`).
- **DELETE by id** — running it twice still leaves the row gone.
- **PUT** over **POST** when the URL names the resource.

Reach for keys when the business operation is not naturally idempotent (creating a payment, sending a notification, allocating inventory).

### Dedup window

How far back you remember keys. Shorter = cheaper storage, higher chance a legitimate retry slips past and is treated as new. Longer = more storage. Pick a window that comfortably exceeds the worst plausible retry delay (queue redelivery timer, mobile reconnect window) and bound storage with TTL or scheduled cleanup.

## 3. When to use

- **Any HTTP endpoint behind a load balancer.** Most LBs retry on connection errors; the server cannot tell a fresh request from a replay.
- **Any queue consumer.** SQS, Kafka, RabbitMQ — [at-least-once is the default](pubsub-semantics.md); the consumer owns dedup.
- **Webhook receivers.** The sender retries on any non-2xx, including timeouts. Design for duplicates from day one.
- **Cross-service writes** in microservices, where a supervisor retries a saga step after the caller crashes mid-flight.

Anti-signals:

- **Pure read endpoints.** A GET is already idempotent; adding a key buys nothing.
- **Operations whose business meaning is "do it again."** "Send a fresh OTP", "trigger another build", "post another tweet" — the user *wants* repeated execution. Dedup breaks the product.

## 4. Trade-offs and failure modes

- **Storage cost grows with traffic × dedup window × row size.** A modest 1 KB row at 10k RPS over 24 h is ~864 GB; a more realistic 4 KB row (request hash + response payload + headers) gets you to ~3.5 TB. Plan TTL eviction from day one and offload bulky response bodies out-of-band.
- **TTL too short → false dedup misses.** A legitimate retry arriving after expiry is processed as new work; you charge twice. Too long → unbounded storage.
- **The concurrency race.** Two requests with the same key arrive simultaneously. Naive `SELECT then INSERT` lets both threads see "no row" and both proceed. You need **atomic compare-and-set**: `INSERT ... ON CONFLICT DO NOTHING` (Postgres), `SET NX` (Redis), `PutItem` with `attribute_not_exists` (DynamoDB). Never check-then-write.
- **In-flight key still `PENDING`.** The race is resolved at insert time, but the loser still has to handle a row in `PENDING`. Three choices, and the answer should be explicit in your contract:
  - **Reject fast (409).** Loser returns `409 Conflict` immediately. Cheap, no shared waiting state, but the client must retry once the original commits to actually get the cached response. This is what Stripe does — concurrent retries on the same key get HTTP 409 with `idempotency_error`.
  - **Block on the winner.** Loser polls or subscribes until the row flips to `DONE`, then returns the stored response. One round trip for the client, but you now hold a connection per duplicate.
  - **Stream once ready.** Long-poll variant; same trade-offs as block-on-winner with a tighter latency tail.
- **Key collision and key reuse.** UUID collisions are vanishingly rare; a buggy client reusing one key for a *different* operation is not. Define behavior explicitly: return the stored response, or hash the request body, compare on retry, and reject mismatches. Stripe takes the second path — same key with a different body returns `400` with code `idempotency_error`.
- **Result storage size.** A real idempotency record (hashed body + status + headers + response payload) is rarely 1 KB; 4–16 KB is more typical. Stuff the full response body in and the dedup table becomes your largest table. Store a hash plus a reference (S3 object, response cache key) for big payloads.
- **Replay vs. correctness drift.** If downstream state has moved on since the original execution, the stored response is stale ("balance: 100" but it's now 90). Usually correct — the request *did* succeed — but understand that stored responses are snapshots.

## 5. Real-world and interviewer probes

**In the wild.**

- **Stripe** standardized the `Idempotency-Key` HTTP header. Keys are retained for **24 hours**, and the server returns the original response — including the original status code — on replay. Same key with a mismatched body returns `400` (`idempotency_error`); a same-key request hitting while the first is still in flight returns `409` (`idempotency_error`, "Conflict"), not a block.
- **AWS SQS FIFO** queues accept a `MessageDeduplicationId` and dedup within a **5-minute** window — the "minutes, not days" rule in production.
- **Kafka** producers with `enable.idempotence=true` are assigned a producer ID (PID) by the broker and tag each record with a per-partition sequence number; the broker rejects records whose `(PID, partition, sequence)` it has already seen, eliminating duplicates from broker-side retries.
- **DynamoDB** exposes `ClientRequestToken` on transactional writes for the same purpose.

**Probes.**

- *"What if the same key arrives twice in flight?"* — Atomic insert (`INSERT ... ON CONFLICT DO NOTHING`, `SET NX`, conditional `PutItem`) decides the winner. The loser then either returns `409` immediately (Stripe-style; client retries to fetch the cached response once the row is `DONE`) or blocks on the row flipping to `DONE` and returns the stored response. Pick one and document it. Never check-then-write.
- *"How long should the dedup window be?"* — Bounded by the realistic retry horizon: client retry policy, queue redelivery timer, mobile reconnect window. Minutes to hours. Days only with a specific business reason and the storage budget.
- *"Why is 'exactly-once delivery' a myth?"* — The sender cannot distinguish "message lost" from "ack lost" without an extra round trip, which can also be lost. Achievable: exactly-once **effects** = at-least-once delivery + idempotent processing.
- *"Walk me through implementing it for a payment endpoint."* — Caller sends `Idempotency-Key`. Server opens a transaction, `INSERT` into a unique-constrained `idempotency_keys` table; on conflict, return the existing row's stored response. On fresh insert, perform the charge in the same transaction (or via two-phase if the gateway is external), store the response on the key row, commit. Same key + different body → 409.
- *"Where does this break?"* — When the side effect crosses a boundary the dedup row cannot cover transactionally (external API, second database, bus). Mitigation is the two-phase reserve/confirm plus a reconciler, or the [transactional outbox](outbox-cdc.md) when the second write is a published event — there is no free atomic commit across heterogeneous systems.
