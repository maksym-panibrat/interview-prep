---
title: System Design Refresher — Design Spec
date: 2026-05-05
status: approved
---

# System Design Refresher — Design Spec

## 1. Goal

Add a focused, high-ROI **system design refresher** to the interview-prep repo. It sits alongside the existing algorithm reference and serves the same purpose for distributed-systems / system-design interviews: a place to re-load the patterns that come up everywhere, in a form that can be skimmed before an interview and read end-to-end when learning.

This is a **refresher, not a textbook.** Every topic must justify itself by ROI in real production systems. No exhaustive surveys, no trendy-but-unproven patterns, no entry-level explainers.

## 2. Audience and scope

**Audience:** senior / staff / principal engineers. Assume comfort with the basics — what a load balancer is, SQL vs NoSQL, what an HTTP request is, what a cache is. The refresher exists to sharpen the *next* layer: the patterns and trade-offs that distinguish someone who has actually run these systems.

**Filter for inclusion** — every topic must pass all four:

1. Shows up in almost any non-trivial production system (not "only at FAANG scale").
2. Proven for 10+ years (not the current hype cycle).
3. Failing to know it bites in concrete, recurring ways (real outages, real bills, real data loss).
4. Senior-level depth, not introductory.

**Out of scope (explicitly):**

- Entry-level concepts (what a CDN is, monolith vs microservices, SQL vs NoSQL).
- Trendy/unproven patterns (service mesh as a standalone topic, current AI-stack patterns).
- Niche/specialized patterns unless paid for elsewhere (CRDTs, geo-distribution as standalone, pure event sourcing).
- Code organization patterns (hexagonal/clean architecture) — relevant but not system-level.
- Domain-specific patterns (multi-tenancy, payments, ML serving) — expansion candidates.
- Code implementations / Python templates. Patterns are described, not coded.
- LeetCode-style problem sets. System design questions don't fit that shape; "real-world examples" replaces it.

## 3. Repo integration

### 3.1 Location

New category under existing `topics/` tree:

```
topics/
  system-design/
    _TEMPLATE.md
    <topic>.md
```

This matches the existing convention (`topics/<category>/<topic>.md`).

### 3.2 README

Extend `README.md` with a new top-level section **System Design** below the existing **Study order** section. List the topics grouped by problem-solved (no tier markers — single-tier core).

### 3.3 RECALL

Skip extending `RECALL.md`. The 30-second-card format ("TL;DR + Python template") doesn't map to system-design content (no template, TL;DR alone is too thin). If a refresher-of-refreshers becomes useful later, create a separate `RECALL-SYSTEM-DESIGN.md` — out of scope for now.

### 3.4 Templates folder

Not applicable. System-design topics have no Python implementations to template.

### 3.5 Verifier

`scripts/verify.py` currently enforces a single 9-section schema for all topic files. It needs to be extended to support a **second schema** (see §4) selected by directory: files under `topics/system-design/` use the system-design schema; everything else continues to use the algorithm schema. Internal-link checking and Python-block parsing apply to both.

Files starting with `_` (e.g., `_TEMPLATE.md`) continue to be skipped — already-existing behavior.

## 4. Topic template

Each system-design topic file uses this template (the verifier enforces section presence). Sections are ordered the way someone reading the topic for understanding (not just recall) wants them.

```
# <Topic>

## 1. TL;DR
2–4 sentences. What it is, the problem it solves, the headline trade-off.

## 2. How it works
Mechanics. Diagrams (ASCII or mermaid) where they help. State the invariants.
For multi-variant patterns (e.g., "rate limiting"), describe each variant.

## 3. When to use
The signals in a design conversation that should make you reach for this. The
shape of the problems where it pays off. Anti-signals — when *not* to use it.

## 4. Trade-offs and failure modes
The honest list: what you give up, what breaks under load, what bites in
production. Concrete failure modes (e.g., "cache stampede on TTL expiry",
"split brain after network partition"). What you must operationally handle.

## 5. Real-world and interviewer probes
- **In the wild:** systems that use this and how (e.g., "DynamoDB uses
  consistent hashing with virtual nodes for partition assignment").
- **Interviewer follow-ups:** the pointed questions you should expect and the
  one-or-two-sentence answers that demonstrate depth.
```

**Length target:** refresher density, not textbook density. A senior engineer should be able to read a topic in a few minutes and walk away ready to discuss it cold.

## 5. Topic list

Grouped by **problem solved**, not by tier — patterns within a group are usually composed in real designs, so co-location aids both reading and recall. Order within README will follow this grouping. The list below is the agreed core; treat it as the starting set, not a fixed-size cap (topics may merge or split during writing).

### Reliable service-to-service communication

- **Resilience four-pack** — `topics/system-design/resilience-four-pack.md`
  Timeout + retry-with-jittered-backoff + circuit breaker + bulkhead. One topic because they are never deployed alone — every retry needs a timeout, every retry storm needs a breaker, every breaker needs a bulkhead to isolate the blast radius.

- **Idempotency** — `topics/system-design/idempotency.md`
  Idempotency keys, dedup windows, idempotent consumers. The "exactly-once delivery is a myth, exactly-once *effects* is achievable" framing lives here.

- **Backpressure and load shedding** — `topics/system-design/backpressure-load-shedding.md`
  Queue-depth signals, drop-vs-block, priority shedding, admission control. The pattern that keeps a degraded system from becoming a dead system.

### Reliable data flow across services

- **Transactional outbox + CDC** — `topics/system-design/outbox-cdc.md`
  The canonical answer to the dual-write problem. Combined because outbox is the producer side and CDC is the consumer/transport side of the same picture.

- **Saga pattern** — `topics/system-design/saga.md`
  Choreography vs orchestration, compensating actions, semantic locks. Includes a short "why 2PC is usually a smell" foil.

### Scaling reads

- **Caching strategies + stampede mitigation** — `topics/system-design/caching.md`
  Cache-aside / read-through / write-through / write-back. Single-flight, jittered TTL, stale-while-revalidate, negative caching, cache warming. Combined because stampede mitigation only makes sense alongside the strategy that creates the stampede risk.

- **CQRS + materialized read models** — `topics/system-design/cqrs-read-models.md`
  When read shape diverges from write shape; replay; the cost (consistency lag, dual schemas, ops complexity). Event sourcing referenced here, not as standalone.

### Data distribution and write scaling

- **Sharding strategies** — `topics/system-design/sharding.md`
  Range / hash / directory. Rebalancing. Hot-partition rescue (key salting, secondary keys). Cross-shard queries. Resharding without downtime.

- **Consistent hashing** — `topics/system-design/consistent-hashing.md`
  Virtual nodes, ring math, why DynamoDB / Cassandra / memcached client routing all use it. The math of "what fraction of keys move when a node joins/leaves."

- **Replication models** — `topics/system-design/replication.md`
  Single-leader / multi-leader / leaderless. Sync vs async vs semi-sync. Failover. Replication lag and read-your-writes. Brief mention of geo-distribution as a flavor.

- **Quorum and tunable consistency** — `topics/system-design/quorum-consistency.md`
  R + W > N. Read repair. Hinted handoff. Last-write-wins vs version vectors. CAP and PACELC enter implicitly here, not as standalone topics.

### Coordination

- **Leader election and consensus** — `topics/system-design/leader-election-consensus.md`
  Raft architecturally. The "do I actually need consensus or does eventual consistency suffice?" framing. Quorum-based commit. Brief mention of Paxos by name.

- **Distributed locks done right** — `topics/system-design/distributed-locks.md`
  Leases instead of locks. Fencing tokens. The Redlock debate. Why optimistic concurrency control is usually the better answer.

### Throttling and fairness

- **Rate limiting** — `topics/system-design/rate-limiting.md`
  Token bucket / leaky bucket / sliding-window-counter / sliding-window-log. Distributed quota (centralized counter vs probabilistic local). Gateway-side vs client-side. Per-key vs per-tenant.

### Event-driven plumbing

- **Pub/sub semantics** — `topics/system-design/pubsub-semantics.md`
  At-least-once vs at-most-once vs exactly-once-effects. Ordering and partition keys. Consumer groups. Dead-letter queues. Replay. Why "exactly-once delivery" is a marketing term.

### Probabilistic structures at scale

- **Bloom filters and HyperLogLog** — `topics/system-design/bloom-hll.md`
  Combined because both are "probabilistic shortcuts to skip expensive work" — Bloom for membership ("is this key worth a disk seek?"), HLL for cardinality ("how many uniques without a hashset"). When the false-positive / approximate-count budget is worth the savings.

### Evolution in production

- **Schema evolution and backward compatibility** — `topics/system-design/schema-evolution.md`
  Protobuf / Avro forward + backward compatibility rules. Expand-contract migrations. Double-writing. Versioned events. The "old code, new data; new code, old data" matrix.

- **Strangler fig** — `topics/system-design/strangler-fig.md`
  Incremental replacement of a legacy system. Routing strategies (proxy, ambassador). Read/write split during migration. Knowing when to delete.

### Production observability

- **Golden signals + tracing trio** — `topics/system-design/observability-trio.md`
  RED (rate, errors, duration) and USE (utilization, saturation, errors). Correlation-ID propagation across services. Structured logging. Distributed tracing (sampling, span hierarchy). Combined because logs / metrics / traces are practiced as one discipline.

## 6. Conventions

- **Voice.** Same as existing topic files — second-person where natural, no breathless marketing tone, no emoji.
- **Diagrams.** ASCII preferred (renders in any reader); mermaid acceptable when ASCII becomes unreadable. No external image files.
- **Code blocks.** Pseudocode / config snippets only where they earn their keep. No language-tagged code that the verifier might try to parse — use plain ` ``` ` blocks for pseudocode.
- **Internal links.** Cross-link liberally between related topics (Sagas ↔ Outbox/CDC, Idempotency ↔ Pub/sub, Caching ↔ CQRS). Verifier checks resolution.
- **No trailing summary.** End topics on the last useful section, not a recap.

## 7. Tooling changes

1. **`scripts/verify.py`** — extend to dispatch on directory:
   - `topics/system-design/*.md` → system-design schema (TL;DR / How it works / When to use / Trade-offs and failure modes / Real-world and interviewer probes).
   - everything else → existing algorithm schema (unchanged).
   - Internal-link checking and Python-block parsing run for both.
2. **`topics/system-design/_TEMPLATE.md`** — author the system-design template file matching §4.
3. **`README.md`** — add the System Design section listing the topics in problem-solved order.

## 8. Success criteria

- Every topic in §5 has a file under `topics/system-design/` that passes `verify.py`.
- `_TEMPLATE.md` exists and is excluded from verification (existing `_`-prefix rule).
- `README.md` has a new **System Design** heading that lists the topics grouped by the §5 categories.
- `verify.py` enforces the system-design schema for the new directory and the existing algorithm schema for everything else; existing algorithm files continue to pass.
- Each topic reads in a few minutes and gives the senior reader the mechanics, the trade-offs, and the questions to expect.

## 9. Future expansion (out of scope for this spec)

- Multi-tenancy (silo / pool / bridge).
- Geo-distribution and multi-region writes as a standalone topic.
- CRDTs.
- Distributed ID generation (Snowflake, ULID) — currently a callout inside Sharding/Replication.
- Event sourcing as standalone (currently inside CQRS).
- Service mesh patterns when/if proven outside the K8s-shop demographic.
- A `RECALL-SYSTEM-DESIGN.md` aggregator if the topics prove useful as TL;DR-only flash refreshers.
