# Quorum and tunable consistency

## 1. TL;DR

Quorum-based [replication](replication.md) writes to **W of N** replicas and reads from **R of N**; **`R + W > N` forces every read set to intersect every committed write set on at least one replica**, so the latest write is visible to the reader. Tuning `R`, `W`, and `N` — Dynamo-style "tunable consistency" — is the knob between strong reads, write latency, and availability. The math is simple, the gotchas are not: **`R + W > N` is necessary, never sufficient**. Concurrent writers, sloppy quorums, and last-write-wins clocks all hand you stale or lost data while the protocol returns success.

## 2. How it works

### The math

Pick three numbers per keyspace (or per request, on Cassandra and DynamoDB):

- `N` — replication factor.
- `W` — replicas that must ack a write before it is "committed."
- `R` — replicas that must respond to a read before the coordinator returns.

**The invariant is `R + W > N`.** Walk it with `N = 5`, `W = 3`, `R = 3`:

```
replicas = {A, B, C, D, E}

write set = {A, B, C}     write x = "v2" succeeds when A, B, C ack
read  set = {C, D, E}     read fans out, waits for any 3 responses
intersection = {C}        C holds v2; reader picks the highest-version reply
```

`|W| + |R| = 6 > 5 = |N|`, so by pigeonhole the two sets must share at least one replica. **That shared replica saw the latest committed write**, the read sees it, and the coordinator returns the freshest version among the `R` responses. The intersection can be a single node — that's enough.

Now drop to `W = R = 2` (`R + W = 4 ≤ N = 5`). Write goes to `{A, B}`, read goes to `{D, E}`. Disjoint. **The reader returns stale data while the protocol still calls both operations successful.** `R + W ≤ N` is not "weaker quorum"; it is "no quorum guarantee at all."

Common knobs:

- `W = N, R = 1` — every replica converges before a write acks, so any single replica answers the read with the latest value. Cheap reads; write latency tracks the slowest replica and any replica down takes writes offline.
- `W = 1, R = N` — every read polls every replica; one ack commits a write. High read latency, low write durability (a single ack can be lost if that node fails before propagation). Rarely useful.
- `W = R = ⌈(N+1)/2⌉` — balanced strong; the typical "QUORUM" preset (`N = 3 → 2`, `N = 5 → 3`).
- `W = R = 1` — eventual consistency, max availability; reads can be stale.

The coordinator (any node — leaderless) fans the request to all `N` replicas and returns as soon as `W` (or `R`) responses arrive. Remaining replicas catch up out of band.

### Read repair

A quorum read returns `R` versioned responses (vector clock or timestamp). If they disagree, the coordinator returns the freshest version and writes it back to lagging replicas — **read repair**. Synchronous repair fixes divergence on the hot path; async repair logs the mismatch and fixes after responding, trading a freshness window for tail latency. **Every read can produce writes** — bake that into your traffic estimate.

### Hinted handoff

When a preferred replica is unreachable at write time, a healthy peer stores **the value plus a hint**: "this row was destined for node A; replay it when A returns." Concretely, key `K`'s preferred replicas are `{A, B, C}`; `A` is down; the coordinator writes to `B` and `C` for the data and parks a hint on, say, `B` saying *for A: K = v2*. When `A` rejoins, `B` drains its hint queue to `A` and the cluster converges. **This preserves `W` during transient outages without taking the keyspace write-unavailable.** Costs: hint queues consume disk and replay bandwidth; permanently dead nodes leave hints to expire (Cassandra defaults to 3 hours); the durable backstop is **anti-entropy via Merkle-tree sync**, which compares replica state out of band and ships missing rows.

### Sloppy quorum

Strict quorum says: a write needs `W` acks from the **preferred replicas** for the key — the `N` nodes the partitioner assigns. If too many of those are unreachable to reach `W`, the write fails. **Sloppy quorum** relaxes that: walk the ring past the preferred set to the next healthy nodes, accept the write there with a hint, hand off later. Walk a partition:

```
Key K's preferred replicas: {A, B, C}.   N = 3, W = 2.
A and B are partitioned away from the coordinator.

Strict:  fewer than W = 2 preferred replicas reachable -> write fails.
Sloppy:  coordinator writes to {C, D, E} where D, E are NOT in K's preferred set.
         D and E hold the value as hints "for A" and "for B."
         Coordinator returns success.
```

You kept accepting writes during the partition, but two of the three acks came from nodes that don't own this key. **A strict-quorum reader against the preferred set `{A, B, C}` only reads `C`** until the partition heals and `D`, `E` hand their hints off to `A` and `B`. During that window the read can miss the write entirely. The guarantee weakens to eventually consistent, even though you nominally configured `R + W > N`. **Sloppy quorum trades consistency for write availability under partition; that trade is what `R + W > N` does not, by itself, defend against.**

### Conflict resolution

Quorum overlap guarantees a read sees *some* committed write — **not which one wins when two writers raced**. Concretely: clients `C1` and `C2` write `x = 1` and `x = 2` to the same key at the same instant. Both reach `W` replicas. A subsequent read returns both versions via the overlap. Which is "latest"? The protocol does not answer; you need a merge rule:

- **Last-write-wins (LWW).** Each write carries a timestamp; the higher timestamp wins. Cheap, deterministic, **silently lossy**. Two coordinators with clocks 100 ms apart write `x = 1` at wall-clock 12:00:00.000 and `x = 2` at wall-clock 12:00:00.050. If NTP skew makes coordinator-1's clock read 12:00:00.200 when it stamps `x = 1`, **the write that actually arrived later (`x = 2`) loses** and is dropped on the next compaction. This is the bug Cassandra users hit when **backfilling historical data with old timestamps**: the backfill silently no-ops every cell that already exists with a newer timestamp, even when the backfill value is the correct one. Wall-clock time across nodes is not totally ordered; treating it as such drops data.
- **Version vectors.** Per-actor counters; a write carries the vector it observed when it read. Reads detect concurrent writes (vectors with no causal ordering between them) and return **siblings** for application merge — Riak's model — or merge them deterministically with a registered CRDT.
- **CRDTs.** Types whose operations commute and merge by definition: G-counters, OR-sets, LWW-element-sets, sequence CRDTs. Concurrent writes merge cleanly with no loss. The cost is restricted operations and metadata overhead (tombstones, dot-context vectors).

## 3. When to use

- **Highly available distributed datastores** where the failure mode is "any node, any time" and every node should take writes. Dynamo, Cassandra, Riak, Voldemort.
- **Per-request consistency tuning.** Some reads need strong (a just-updated profile), most can be eventual (a feed item). `LOCAL_QUORUM` for the hot path, `ONE` for analytics scans.
- **Multi-region without a global leader.** `LOCAL_QUORUM` per region keeps the hot path off cross-region RTT; replication and read repair converge in the background.
- **Workloads that fit a conflict model.** Counters that fit a CRDT, sets that fit OR-set, key-value where LWW is genuinely fine.

Anti-signals:

- **Serializable transactions across keys.** Quorum is per-key. Multi-key invariants — bank transfers, foreign keys, "no two users with the same email" — need a [consensus-based store](leader-election-consensus.md) (Spanner, CockroachDB) or an explicit transaction coordinator.
- **Strict read-your-writes everywhere.** If every read must see every write, you're paying quorum cost on every read. A leader-based system might be cheaper.
- **Workloads that can't tolerate hidden data loss.** LWW will eat writes you didn't realize were concurrent. If that's not okay, you're committing to vector clocks or CRDTs.

## 4. Trade-offs and failure modes

- **`R + W > N` is necessary but not sufficient.** It guarantees overlap, not ordering. Two concurrent writers both reach quorum; the protocol has no opinion on which wins. Without version vectors or CRDTs you fall back to LWW, which resolves the tie by deleting one write.
- **LWW silently drops writes.** Millisecond clock skew across coordinators is enough to lose one of two simultaneous updates; backfilling with old timestamps no-ops cells whose current value has a newer timestamp. **Don't use wall-clock LWW for anything you can't afford to lose.**
- **Sloppy quorum hides itself.** A write that "succeeded" landed on nodes outside the key's preferred replica set; a strict-quorum read of the preferred set won't see it until handoff completes. **The guarantee you advertised is not the guarantee you provided.**
- **Read repair amplifies traffic.** Every divergent read writes back. On a churning dataset, high-`R` read load multiplies cluster write traffic in ways capacity plans rarely model — async repair shifts the cost off the read path but doesn't remove it.
- **Tail latency tracks the slowest of `R` (or `W`).** A slow disk or GC pause becomes a coordinator-side latency spike. **Speculative reads** (issue to `R+1` replicas, take the first `R` responses) trade fan-out for shorter tail.
- **CAP and PACELC live in the knob.** Under partition, `W = R = 1` keeps accepting writes (AP); `W = N` stops on any unreachable replica (CP-leaning). Even without partition, raising `R` or `W` trades latency for consistency — that's the "ELC" half of PACELC, not a separate property.

## 5. Real-world and interviewer probes

In the wild, **Amazon Dynamo** (the 2007 paper) is the canonical design and the source of this vocabulary. **DynamoDB** exposes a simplified version: strongly-consistent reads (2x the cost) implement quorum reads; eventually-consistent reads are `R = 1`. **Cassandra** is the most explicit per-request knob in production — every query carries a `ConsistencyLevel` (`ONE`, `QUORUM`, `LOCAL_QUORUM`, `EACH_QUORUM`, `ALL`). **Riak** returns conflicting versions to the client for application-level merge using vector clocks. **Voldemort** at LinkedIn was an early Dynamo clone.

Probes you should expect:

- *"Why `R + W > N`?"* — **Pigeonhole.** Any `R`-set and any committed `W`-set drawn from the same `N` replicas must intersect on at least one node, which holds the latest committed value. The reader takes the highest-version response and is guaranteed to see the latest write.
- *"Why might you still see stale data with `R + W > N`?"* — **Concurrent writes.** Overlap guarantees a read sees *some* committed write, not a deterministic ordering of simultaneous ones. You need version vectors to detect concurrency and a merge policy (CRDT, application merge, or LWW) to resolve it. **Sloppy quorum** is the other answer: writes acked by nodes outside the preferred set don't appear to a strict-quorum reader until hinted handoff completes.
- *"When would you use `W = 1, R = N`?"* — **Almost never.** Write-heavy workloads that tolerate stale or lost writes and want maximum write throughput. Most teams use balanced `W = R = quorum` and tune from there.
- *"What's hinted handoff and what does it not solve?"* — A healthy peer stores writes destined for an unreachable replica and replays them on recovery, **preserving write availability and the apparent `W` during transient failures**. It does not solve permanent node loss (hints expire — **anti-entropy via Merkle trees is the durable backstop**) and does not extend the quorum guarantee to nodes outside the preferred set (sloppy quorum does that, and weakens consistency in exchange).
