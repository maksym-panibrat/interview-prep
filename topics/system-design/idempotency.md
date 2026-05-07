# Idempotency

## 1. TL;DR

**An operation is idempotent when N executions land the same effect as one — and on a real network you have no other way to be safe.** [Retries](resilience-four-pack.md) are inevitable: load balancers retry on connection errors, queues redeliver on visibility-timeout expiry, mobile clients fire a second `POST` after a 30-second stall on flaky 3G, humans double-click. Without server-side dedup, every one of those becomes a second charge, a second email, a second inventory hold. The "exactly-once delivery" myth dies on the same boundary: an unreliable network cannot tell "message lost" from "ack lost," so no protocol delivers exactly once. **What you can build is exactly-once *effects* — at-least-once delivery plus a server that recognizes a replay and refuses to do the work twice.** That recognition is the entire job of this pattern.

## 2. How it works

**Two ingredients carry the design: a key that names the logical operation, and a store that remembers what happened the first time.** Everything else — atomicity, races, reconciliation — is plumbing around those two pieces.

### Idempotency key

A unique ID per logical operation, supplied by the caller (`Idempotency-Key: 7f3c...`) or derived from request content (hash of the body, primary key + timestamp). **The contract is "same key → same effect": the server records `key → result` on first execution and returns the stored result on every replay**, regardless of how the duplicate arrived.

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

**The store's durability bounds your dedup guarantee — pick it deliberately.**

- **Redis with TTL.** Sub-millisecond reads and writes, but unreplicated keys can vanish on a failover between the first request and its retry. Acceptable when the side effect itself is cheap to redo (idempotent webhook fan-out); dangerous when it's a card charge.
- **Database row with a unique constraint on the key.** Durable and gives you transactional atomicity with a same-DB side effect, at the cost of an extra write per request. The default for money-moving paths.
- **Both, with the DB authoritative.** Redis as a hot-path cache to short-circuit replays in microseconds; the DB as the source of truth that ratifies every first-time write. Cache miss on Redis is not a license to execute — fall through to the DB.

### The atomicity problem

**The key write and the side effect must commit as one unit, or every crash window between them produces a wrong answer.** Concretely: if you `INSERT key (DONE)` *before* the side effect and the process dies, the next retry sees `DONE` and returns a fake success for work that never happened — silent data loss. If you do the side effect *first* and crash before writing the key, the next retry has no dedup record and re-executes — duplicate charge.

When the side effect lives in the same database, wrap both in one transaction:

```
BEGIN;
  INSERT INTO idempotency_keys (key, status) VALUES ('K1', 'PENDING');
  -- unique constraint on key fails here on retry -> caller goes to dedup branch
  INSERT INTO charges (...) VALUES (...);
  UPDATE idempotency_keys SET status='DONE', response=$1 WHERE key='K1';
COMMIT;
```

Cross-process side effects (a Stripe call, a Kafka publish, a write to a second DB) cannot enlist in that transaction. **Use a two-phase reservation**:

1. `INSERT idempotency_keys (key='K1', status='PENDING', started_at=now())` — commits before the external call.
2. Call the external API.
3. `UPDATE idempotency_keys SET status='DONE', response=...`.

The failure window is between step 2 and step 3: the external API succeeded but the process crashed before recording it. **The next retry lands on a `PENDING` row and must not re-call the API blindly** — it has no idea whether step 2 ran. A reconciler sweeps rows where `status='PENDING' AND started_at < now() - 5min`, queries the external system by an embedded correlation ID (`charge_id`, `message_id`) to learn whether the side effect actually happened, and either flips the row to `DONE` with the recovered response or to `FAILED` for a clean retry. Without that reconciler, `PENDING` rows are landmines: every duplicate request that hits one has to either block forever or guess.

### Natural idempotency

**The cheapest dedup is the one you don't have to write — when the operation's own semantics make replay safe, skip the key entirely.**

- **UPSERT** (`INSERT ... ON CONFLICT UPDATE`) over blind `INSERT`: replay sets the same row to the same values, no duplicate.
- **Set-state-X** (`SET balance = 100`) over **increment-by-X** (`balance += 10`): the absolute write is idempotent; the delta isn't.
- **DELETE by id**: running it twice still leaves the row gone.
- **PUT** over **POST** when the URL names the resource: `PUT /users/42` is replay-safe; `POST /users` mints a new ID each call.

Reach for keys when the business operation is genuinely not idempotent — creating a payment, sending a notification, allocating inventory off a finite pool.

### Dedup window

How far back you remember keys. **Pick the window to comfortably exceed your worst plausible retry delay, then bound storage with TTL.** A queue with a 15-minute visibility timeout and three redeliveries needs at least an hour. A mobile client that may sleep for a day before reconnecting needs a day. Stripe lands at 24 hours; SQS FIFO at 5 minutes; pick yours from the same kind of reasoning, not a round number.

## 3. When to use

- **Any HTTP endpoint behind a load balancer.** Most LBs retry on connection errors before the request ever reaches your server logs; you cannot tell the replay from a fresh hit.
- **Any queue consumer.** SQS, Kafka, RabbitMQ — [at-least-once is the default](pubsub-semantics.md), so the consumer owns dedup. The queue cannot do it for you across consumer crashes.
- **Webhook receivers.** The sender retries on every non-2xx, including the 504 your overloaded server returned after already processing the event. Design for duplicates from request one.
- **Cross-service writes** in microservices, where a saga supervisor retries a step after the caller crashes mid-flight.

Anti-signals:

- **Pure read endpoints.** A `GET` is already idempotent by definition; adding a key buys nothing and costs a write.
- **Operations whose business meaning is "do it again."** "Send a fresh OTP," "trigger another build," "post another tweet" — the user *wants* repeated execution. Dedup here is a bug, not a feature.

## 4. Trade-offs and failure modes

- **Storage cost grows with traffic × window × row size, faster than people guess.** A 1 KB row at 10k RPS over 24 h is ~864 GB; a realistic 4 KB row (hashed body + status + headers + response payload) puts you at **~3.5 TB of hot table just for dedup**. Past a few KB, stop storing the response inline: keep a SHA-256 of the request, a status code, and a pointer (S3 key, response cache ID) to the body. The dedup table stays small and indexable; the bulk lives where bulk belongs.
- **TTL too short → false dedup misses; too long → unbounded storage.** A queue redelivery that arrives 11 minutes later against a 10-minute window is processed as new work — a duplicate charge with no obvious cause until you correlate timestamps. Size the window from the worst retry source you accept (queue redelivery timer, mobile reconnect window), then add headroom.
- **The concurrency race needs an atomic compare-and-set, not check-then-write.** Two requests with the same key arrive on two app servers in the same millisecond. Naive code does `SELECT WHERE key='K1'` (both see no row) then `INSERT` (both succeed if the key column is non-unique; both proceed to charge the card if you didn't add a unique constraint). The fix is to skip the check entirely and let the database arbitrate:

  ```
  -- Postgres
  INSERT INTO idempotency_keys (key, status) VALUES ('K1', 'PENDING')
    ON CONFLICT (key) DO NOTHING
    RETURNING key;
  -- Empty result = someone else won; go fetch their row.
  ```

  Equivalents: `SET key value NX` (Redis), `PutItem` with `ConditionExpression: attribute_not_exists(key)` (DynamoDB). **Never check-then-write — the database's unique index is the only race-free arbiter you have.**
- **The loser of the race lands on a `PENDING` row, and your contract has to say what happens next.** Pick one and document it:
  - **Reject fast (Stripe-style).** Loser returns `409 Conflict` immediately with `{"error": {"type": "idempotency_error", "message": "Concurrent requests with same Idempotency-Key"}}`. Cheap, no shared waiting state; the client retries once the original commits and then gets the cached response. Best for public APIs where you don't trust callers to hold connections.
  - **Block on the winner.** Loser polls or subscribes (`LISTEN/NOTIFY`, Redis pub/sub) until the row flips to `DONE`, then returns the stored response. One round trip for the client, but you now hold a connection per duplicate — a thundering herd of retries can exhaust the connection pool.
  - **Stream once ready.** Long-poll variant; same trade-offs as block-on-winner with a tighter latency tail and the same connection-pool exposure.
- **Key reuse with a different body is the realistic failure, not key collision.** A random UUID colliding with another is ~zero; a buggy mobile client reusing one key for a fresh checkout because the cart got cleared incorrectly is a Tuesday. **Hash the request body alongside the key and compare on every replay**: same key + same hash → return stored response; same key + different hash → reject with a clear error. Stripe returns `400` with `{"error": {"code": "idempotency_key_in_use"}}` for this case; pick something equally unambiguous.
- **Replay returns a snapshot — and the snapshot can drift from current truth.** The first call to `POST /quotes` returned `{"price": 100, "expires_at": "..."}`. Six hours later the same key replays; pricing has changed and the live quote would be `120`, but the dedup store still returns `100`. Usually correct — the original request *did* succeed at price 100 — but if the client treats the replayed response as "current," you ship stale data downstream. Either keep the window short enough that staleness is bounded, or version responses so the client can tell a replay from a fresh quote.

## 5. Real-world and interviewer probes

**In the wild.**

- **Stripe** standardized the `Idempotency-Key` HTTP header. Keys are retained **24 hours**; replay returns the original response *including the original status code* — a replay of a request that originally 400'd will 400 again with the same body. Same key + different request body returns `400`:

  ```
  HTTP/1.1 400 Bad Request
  {
    "error": {
      "type": "idempotency_error",
      "message": "Keys for idempotent requests can only be used with the same parameters they were first used with."
    }
  }
  ```

  A same-key request hitting while the first is still in flight returns `409 Conflict` with `idempotency_error` — Stripe rejects rather than blocks, pushing the retry choice back to the client.
- **AWS SQS FIFO** queues accept a `MessageDeduplicationId` and dedup within a **5-minute window** — concrete evidence for the "minutes, not days" rule when the retry source is a queue, not a human.
- **Kafka** producers with `enable.idempotence=true` get a producer ID (PID) from the broker and tag each record with a per-partition sequence number; the broker rejects records whose `(PID, partition, sequence)` it has already seen, eliminating duplicates from broker-side retries. Note the scope: this protects against producer retries, not against a producer that crashes and restarts with a new PID.
- **DynamoDB** exposes `ClientRequestToken` on transactional writes for the same purpose, with a 10-minute dedup window scoped per token.

**Probes.**

- *"What if the same key arrives twice in flight?"* — Atomic insert (`INSERT ... ON CONFLICT DO NOTHING`, `SET NX`, conditional `PutItem`) decides the winner. The loser sees the row already exists and either returns `409` immediately (Stripe-style; client retries to fetch the cached response once the row is `DONE`) or blocks on the row flipping to `DONE` and returns the stored response. Pick one and document it. Never check-then-write — the read and the write are not atomic.
- *"How long should the dedup window be?"* — Sized to the realistic retry horizon for the worst retry source you accept: client retry policy, queue redelivery timer, mobile reconnect window. Minutes to hours, with days only when a specific business reason justifies the storage cost.
- *"Why is 'exactly-once delivery' a myth?"* — The sender cannot distinguish "message lost" from "ack lost" without an extra round trip, which can also be lost — induction, not engineering bravado, kills the property. What's achievable is exactly-once **effects** = at-least-once delivery + idempotent processing.
- *"Walk me through implementing it for a payment endpoint."* — Caller sends `Idempotency-Key`. Server opens a transaction, `INSERT ... ON CONFLICT DO NOTHING` into a unique-constrained `idempotency_keys` table; on conflict, `SELECT` the existing row and return its stored response (or `409` if still `PENDING`). On fresh insert, perform the charge in the same transaction (or via two-phase reserve/confirm if the gateway is external), store the response on the key row, commit. Same key + different body hash → `400`.
- *"Where does this break?"* — When the side effect crosses a boundary the dedup row cannot cover transactionally — an external API, a second database, a message bus. Mitigation is the two-phase reserve/confirm with a reconciler, or the [transactional outbox](outbox-cdc.md) when the second write is a published event. There is no free atomic commit across heterogeneous systems; you pay the cost in a reconciler or you pay it in duplicate effects.
