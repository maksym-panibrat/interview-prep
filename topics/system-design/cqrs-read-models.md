# CQRS and materialized read models

## 1. TL;DR

**CQRS** — Command Query Responsibility Segregation — splits the model used for writes from the model(s) used for reads. Writes go through a normalized, invariant-enforcing store; reads come from one or more **materialized read models**, each denormalized to a specific query shape and kept fresh by projecting events from the write side. The win shows up when read and write shapes genuinely diverge: a write model of `{order, line_items, customer}` is hostile to "search orders by free-text product name" or "yesterday's revenue by region." Build a read model per query; rebuild from scratch when you need to. The cost is eventual consistency plus more pipelines to operate. CQRS is most often deployed *without* event sourcing — that is a separate, more expensive decision.

## 2. How it works

### Command and query sides

The write side ("command side") owns business invariants. A command (`PlaceOrder`, `ShipOrder`) hits an aggregate, runs validation, commits to a transactional store, and emits an event. The store is normalized for correctness — foreign keys, constraints, the shape that prevents bad states.

The read side ("query side") is one or more **denormalized stores**, each shaped to one query: a search index for free-text order search, a document store keyed by user with order history pre-joined, a pre-aggregated table of daily revenue by region. None are good for writing into; each is excellent for the one read it was built for.

```
commands --> Write model (normalized) --events--+
                                                |
                +-------------------------------+-------------------------------+
                v                               v                               v
          Search index (ES)            User-orders (Mongo)              Revenue rollup
                ^                               ^                               ^
queries --------+-------------------------------+-------------------------------+
```

### Projections

A **projection** is a consumer that reads the event stream and updates a read store. It is a pure function of `(current read state, event) -> new read state`, with two non-negotiable properties:

- **Idempotent.** Same event delivered twice produces the same read state. Track the last-applied event offset per projection; ignore replays of older offsets.
- **Replayable.** Re-running from offset zero against an empty read store reaches the same final state.

### Replay — the killer feature

Replay is what justifies most of the cost. Bug in a projection that mis-counted refunds for two months? Truncate, reset the offset to zero, replay. Want a new read model — "orders by customer ZIP" — that nobody asked for at launch? Spin up a fresh projection on the same stream, catch up, switch reads over. No re-querying the write store, no backfill. The event log already contains every fact; the new projection is just a new function over it. The read store is a cache.

### Event sourcing (the variant)

In the **without-event-sourcing** form — the common case — events are a side-effect of writes. The write model is a normal database; events are emitted via outbox + CDC, but the database is still the source of truth. Lose the event log, rebuild it from the database.

In **event sourcing**, events *are* the source of truth. The write model itself is a projection: to load aggregate state, fold over its events. No row in `orders` to read directly; there is `order_events` and a function. The write database, if any, is a cache.

That buys you a perfect audit log (events *are* the history) and the ability to derive any past state by replaying to a point in time. It costs the quick `UPDATE` — every change is an event, every read pays a fold (mitigated by snapshots), migrations are events, no admin panel just edits a row.

Event sourcing is a separate cost decision *on top of* CQRS. CQRS without event sourcing is the common production shape; event sourcing without CQRS is rare and usually a mistake.

## 3. When to use

- **Read and write shapes genuinely diverge.** Write a normalized order with line items and a customer FK; read "free-text search across order contents" or "this user's last 50 orders pre-joined." Forcing those reads through the normalized model means joins on every page load and ad-hoc indexes that fight each other.
- **Multiple read models from one source** — search index, customer-facing history view, analytics rollup. One write side feeding several independently-scaled read sides is exactly what CQRS is for.
- **Read:write ratio so skewed that read scaling needs different storage** — reads dominate by 100x; the right answer is a store engineered for reads (Elasticsearch, denormalized cache, column store).
- **Audit and temporal queries** ("what did this order look like on March 14?") — the event-sourcing case specifically.

Anti-signals:

- **Plain CRUD with read/write parity.** If reads are "show me the row I just wrote," CQRS is overhead with no payoff.
- **Strong consistency required between write and read.** CQRS is asynchronous — the read side trails by at least the projection lag. If "the next read after a write must reflect that write," handle read-your-writes explicitly (sticky-route to write, optimistic UI), don't paper it with a read-model lookup.
- **Small teams on small systems.** Two stores, an event pipeline, and projection monitoring is real operational weight; a single Postgres serves a startup for years.

## 4. Trade-offs and failure modes

- **Eventual consistency between write and read.** The headline cost. The write commits, the read store hasn't projected yet, the next page load shows stale state. UX has to handle it: optimistic updates that show new state immediately and reconcile on refresh, "your change will appear shortly" copy where reconcile is too complex, or session-affinity read-your-writes against the write store. Pretending the lag doesn't exist is the most common production failure mode.
- **Replay cost grows with event count.** A clean replay of a year-old log can take hours to days. Snapshotting (periodic dumps of read state plus offset) cuts cold-replay dramatically; without it, projection recovery is a real outage metric. Test replay regularly — a path nobody has run in two years no longer works.
- **Event schemas are permanent.** Old events live forever; every projection must handle every historical version. You add new event shapes, never delete. Versioning discipline (additive changes, version field, upcasters from v1 into v2 on read) is non-optional.
- **Projection bugs require replay.** Truncate, fix, replay — cheap when small, painful at scale. Any "fast fix that patches the read store directly" rots the replay invariant: the next replay reverts the patch and the bug is back.
- **Operational complexity.** Multiple stores, an event pipeline (Kafka, outbox + CDC), projection workers, snapshot jobs, offset tracking, lag monitoring, replay tooling. Make sure the read-shape divergence justifies that surface.
- **Event sourcing's specific tax.** Every change is an event; ad-hoc DB fixes are not available. Migrations are events (an `OrderCorrected` event, not an `UPDATE`). No admin tool changes a row because there is no row to change. Loading current state pays the fold cost, partially solved by snapshots but never fully.

## 5. Real-world and interviewer probes

The most common form of CQRS in production is **Elasticsearch as a read model over a relational write store**. Postgres or MySQL holds the authoritative records; outbox + Debezium or a service-side projection pushes documents into Elasticsearch shaped for the product's search queries. Nobody on the team calls it "CQRS." It is exactly CQRS. Denormalized DynamoDB tables fed from a transactional write side, and analytics warehouses pulling from CDC, are variants on the same idea.

Banking ledgers and trade-clearing systems are the canonical event-sourced production example — events as the source of truth because the audit log *is* the business. **EventStoreDB** and **Axon Framework** are dedicated event-sourcing tools; **Kafka with compacted topics** is sometimes pressed into the role.

Probes you should expect:

- *"When is CQRS a mistake?"* — Plain CRUD with read/write parity, small teams, no divergence between read and write shape. Two stores plus a pipeline buys nothing if one table answered the queries.
- *"How do you handle eventual consistency in the UI?"* — Optimistic update showing new state immediately, reconcile on the next refresh. For critical "did this happen?" reads, route the post-write read back to the write store via session affinity.
- *"Why event sourcing on top of CQRS?"* — Audit, time-travel debugging, and the freedom to derive future read models without re-querying the write store. The cost: every change is an event, ad-hoc updates gone, migrations become events, snapshots non-optional once counts grow.
- *"How do you add a new read model after launch?"* — New projection on the existing log from offset zero, catch up against an empty read store, monitor lag until it converges with live, switch reads over. No backfill, no touching the write side.
- *"What goes wrong in production?"* — Projection lag spikes nobody alerts on, schemas that drifted because a v3 field wasn't handled by the v1 projection, a replay path that bit-rotted because nobody ran it in two years, and patching the read store directly to fix a number — which works until the next replay reverts it.
