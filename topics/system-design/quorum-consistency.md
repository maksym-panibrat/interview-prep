# Quorum and tunable consistency

## 1. TL;DR

Quorum-based [replication](replication.md) writes to **W of N** replicas and reads from **R of N**; as long as `R + W > N`, every read set intersects every committed write set on at least one replica, so the latest write is visible. Tuning `R`, `W`, and `N` per request — Dynamo-style "tunable consistency" — is the knob between strong reads, write latency, and availability. The math is simple, the gotchas are not: `R + W > N` is necessary, never sufficient. Concurrent writers, sloppy quorums, and last-write-wins clocks all hand you stale or lost data while the protocol claims success.

## 2. How it works

### The math

Pick three numbers per keyspace (or per request, on Cassandra and DynamoDB):

- `N` — replication factor.
- `W` — replicas that must ack a write before it is "committed."
- `R` — replicas that must respond to a read before the coordinator returns.

The invariant is `R + W > N`. Pigeonhole: any `W`-set and any `R`-set drawn from the same `N` must overlap on at least one node. That overlapping replica saw the latest committed write, so the read sees it (taking the highest-version response).

```
        N = 5 replicas       W = 3   R = 3   (R + W = 6 > 5)

        write set:   [ A  B  C  .  . ]
        read  set:   [ .  B  C  D  . ]   <- overlap on B and C
                            ^^^^^
                            latest write visible
```

Common knobs:

- `W = N, R = 1` — strong reads, slow writes; any replica down → write unavailable.
- `W = 1, R = N` — fast writes, slow reads; rarely useful.
- `W = R = ⌈(N+1)/2⌉` — balanced strong; the typical "QUORUM" preset.
- `W = R = 1` — eventual consistency, max availability; reads can be stale.

The coordinator (any node — leaderless) fans the request to all `N` replicas and returns as soon as `W` (or `R`) responses arrive. Remaining replicas catch up out of band.

### Read repair

A quorum read returns `R` versioned responses (vector clock or timestamp). If they disagree, the coordinator returns the freshest version and writes it back to lagging replicas — **read repair**. Synchronous repair fixes divergence on the hot path; async repair logs and fixes after responding, trading a freshness window for tail latency. Every read can produce writes — bake that into your traffic estimate.

### Hinted handoff

If a target replica is unreachable when a write arrives, the coordinator stores the value on a healthy peer along with a *hint* — *this belongs to node X, replay it when X returns*. On recovery, the peer streams hints to the owner and the cluster converges. Preserves `W` during transient outages without taking the keyspace write-unavailable. The cost is hint storage and the risk that a permanently dead node leaves hints stranded; anti-entropy via Merkle-tree sync is the durable backstop.

### Sloppy quorum

When too many *preferred* replicas are unreachable to reach `W`, **strict quorum** fails the write, while **sloppy quorum** writes to *any* `W` healthy nodes — even ones that don't normally own this key — and hands off later. You keep accepting writes during a partition, but those nodes aren't in the actual replica set, so a strict reader can miss them. The consistency guarantee weakens to eventually consistent, even though you nominally configured `R + W > N`.

### Conflict resolution

Quorum overlap tells you a read sees *some* write — not which one wins when two writers raced. You need a merge rule:

- **Last-write-wins (LWW).** Each write carries a timestamp; latest wins. Cheap, deterministic, **silently lossy** — two clients writing within a clock-skew window lose one write to whichever timestamp compares higher. Wall-clock time across nodes is not totally ordered; treating it as such drops data.
- **Version vectors.** Per-actor counters; a write carries the vector it observed. Reads detect concurrent writes (vectors with no causal ordering) and return siblings for application merge or merge them deterministically.
- **CRDTs.** Types whose operations commute and merge by definition: G-counters, OR-sets, LWW-element-sets, sequence CRDTs. Concurrent writes merge cleanly with no loss. The cost is restricted operations and metadata overhead.

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

- **`R + W > N` is necessary but not sufficient.** Two writers update the same key concurrently; both succeed at quorum; a reader sees both via overlap but has no rule for which is "latest." Without version vectors or CRDTs, the protocol is silent — and LWW resolves it by deleting one.
- **LWW silently drops writes.** Millisecond clock skew across coordinators is enough to lose one of two simultaneous updates. Mitigation is vector clocks or CRDTs; don't use wall-clock LWW for anything you can't afford to lose.
- **Sloppy quorum confusion.** A write that "succeeded" landed outside the preferred replica set; a subsequent strict-quorum read may not see it until handoff completes. The guarantee you advertised is not the guarantee you provided.
- **Read repair amplifies traffic.** Every divergent read writes back. On a churning dataset, a high-`R` read load multiplies cluster write traffic in ways capacity plans rarely model.
- **Tail latency tracks the slowest of `R` (or `W`).** A slow disk or GC pause becomes a coordinator-side latency spike. Speculative reads (issue `R+1`, take the first `R`) trade fan-out for shorter tail.
- **CAP and PACELC live in the knob.** Under partition, `W = R = 1` keeps accepting writes (AP); `W = N` stops on any unreachable replica (CP-leaning). Even without partition, raising `R` or `W` trades latency for consistency.

## 5. Real-world and interviewer probes

In the wild, **Amazon Dynamo** (the 2007 paper) is the canonical design and the source of this vocabulary. **DynamoDB** exposes a simplified version: strongly-consistent reads (2x the cost) implement quorum reads; eventually-consistent reads are `R = 1`. **Cassandra** is the most explicit per-request knob in production — every query carries a `ConsistencyLevel` (`ONE`, `QUORUM`, `LOCAL_QUORUM`, `EACH_QUORUM`, `ALL`). **Riak** returns conflicting versions to the client for application-level merge using vector clocks. **Voldemort** at LinkedIn was an early Dynamo clone.

Probes you should expect:

- *"Why `R + W > N`?"* — Pigeonhole. Any `R`-set and any committed `W`-set drawn from the same `N` must intersect on at least one node, which holds the latest committed value. The reader picks the highest-version response and is guaranteed to see the latest write.
- *"Why might you still see stale data with `R + W > N`?"* — Concurrent writes. Quorum overlap guarantees a read sees *some* committed write, not a deterministic ordering of simultaneous ones. You need version vectors to detect concurrency and a merge policy (CRDT, application merge, or the lossy LWW shortcut) to resolve it.
- *"When would you use `W = 1, R = N`?"* — Almost never. Write-heavy workloads that tolerate stale or lost writes and want maximum write throughput. Most teams use balanced `W = R = quorum` and tune from there.
- *"What's hinted handoff and what does it not solve?"* — A healthy node stores writes destined for an unreachable peer and replays them on recovery, preserving write availability and the apparent `W` during transient failures. It does not solve permanent node loss (hints expire — anti-entropy via Merkle trees is the durable backstop) and does not extend the quorum guarantee to nodes outside the preferred set (sloppy quorum does, weakening consistency).
