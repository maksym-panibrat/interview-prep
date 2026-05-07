# Consistent hashing

## 1. TL;DR

Consistent hashing is a [hash-sharding scheme](sharding.md) that minimizes data movement when nodes are added or removed: when an N-node cluster grows to N+1, only `~K/(N+1)` of the `K` keys move (the new node's arc); removing a node moves `~K/N`. Compare against the obvious `hash(key) % N`, where changing N reshuffles `~(N-1)/N` of the keyspace. You reach for it any time you can't afford a global re-shuffle on capacity changes — distributed caches, Dynamo-style key-value stores, request routing with affinity. The mechanics are a hash ring plus virtual nodes; the failure modes are skew (without enough vnodes, ~2x tail skew is the asymptotic bound; 100–256 vnodes per node typically pull it to ~1.1–1.3x) and the operational cost of teaching every client about ring membership.

## 2. How it works

### The ring

Hash both keys and node identifiers onto a fixed-size token space — typically `[0, 2^32)` or `[0, 2^64)` — and arrange that space as a ring. Each key is owned by the next node clockwise from the key's position. With `2^32` slots, three nodes A, B, C, and a few keys k1..k5:

```
                     0 / 2^32
                       |
              k5 ---> [A]
            ...               ...
          k1                     k2
        .                           .
       .                             .
      [C]                           [B]
       .                             .
        .            k4             .
          ...                  ...
                     k3
```

`k1` falls between A and B going clockwise — owned by B. `k4` between B and C — owned by C. `k5` past C, wraps to A. Lookup is `bisect` on the sorted ring positions: `O(log N)` for N tokens.

### Adding and removing nodes

Add node D between B and C. Only the keys whose ring position falls in the arc `(B, D]` move — they used to belong to C, now they belong to D. Every other key's owner is unchanged. With reasonably uniform hashing, that arc is `~1/N` of the ring on a balanced cluster, so adding the (N+1)th node moves `~K/(N+1)` of the keys. Removing a node hands its arc to the next clockwise neighbor — again `~1/N` of keys move. Compare against `hash(key) % N`: changing N from 4 to 5 reshuffles almost every key, because the modulus partition is unrelated for adjacent N.

### Virtual nodes

Hashing one token per physical node gives you a coarse, lumpy ring — three nodes might land at positions that hand 60% of the keyspace to one of them. Worse, when a node fails, its entire arc dumps onto exactly one neighbor, potentially doubling that neighbor's load.

The fix is virtual nodes (vnodes): each physical node owns many ring positions, typically 100–256. The keyspace is now sliced finely; the law of large numbers smooths ownership toward `1/N` per physical node. When a physical node fails, its 200 vnode arcs are scattered across the ring, so the surrendered load spreads across many neighbors instead of doubling on one. Cassandra calls these "tokens"; Dynamo calls them "virtual nodes"; the idea is the same.

### Replication

For a replication factor of R, walk clockwise from the key's position and pick the next R *distinct* physical nodes — the first is the *coordinator*, the rest hold replicas. The "distinct" qualifier is load-bearing: with vnodes, the next vnode clockwise often belongs to a physical node already in the replica set, so you skip past it. Rack- and AZ-aware variants extend the skip rule, picking the next clockwise candidate that lives in an unused failure domain (Cassandra's `NetworkTopologyStrategy` is the canonical implementation). Dynamo-style stores combine this layout with [quorum reads and writes](quorum-consistency.md) (`R + W > N`) for tunable consistency; the consistent-hashing ring is the placement substrate underneath.

### Bounded loads

Even with vnodes, consistent hashing has an asymptotic ~2x worst-case skew at the tail — in the limit there is a node that owns roughly twice the average load. In practice with 100–256 vnodes per node it sits closer to 1.1–1.3x, but the asymptotic ceiling matters when you're capacity-planning to peak. Mirrokni, Thorup, and Zadimoghaddam (2016), "Consistent Hashing with Bounded Loads", caps load per node at `(1 + epsilon)` times the average: when a key would land on a node already at the cap, the key skips clockwise to the next under-cap node. The cost is a per-key probe and bookkeeping; the benefit is provable load balance. Vimeo's haproxy implementation is the canonical real-world adoption when tail skew matters.

## 3. When to use

- **Distributed cache with frequent capacity changes.** Memcached client libraries (Ketama is the canonical algorithm) hash keys onto a ring of memcached servers so that adding or removing an instance evicts only `1/N` of the cached entries — the rest still hit cache.
- **Distributed key-value store.** Dynamo, DynamoDB, Cassandra, Riak: rebalancing has to be cheap because clusters grow, shrink, and replace failed nodes routinely. The ring is the placement function for both primary ownership and replication.
- **Stateful service routing with affinity.** When you want session stickiness or per-user locality without a directory — route user X always to the pod that owns user X's hash arc. Adding a pod only re-homes `1/N` of users.
- **CDN edge selection.** Akamai-style routing of a content key to a cache node: same property, the same trick.

Anti-signals:

- **Small, fixed cluster.** With four nodes that never change, `hash(key) % 4` is fine. Consistent hashing's value is amortized over membership changes you don't have.
- **Range scans.** Consistent hashing scrambles key order by design. If you need "give me keys between X and Y", you want range sharding, not a hash ring.
- **Strict, even load is required.** Vanilla ring is ~2x imbalanced at the tail. Use bounded loads or a different scheme if peak load matters more than minimizing rebalance.

## 4. Trade-offs and failure modes

- **Hot keys are still hot.** Consistent hashing solves rebalance pain, not skew. A single hot key still pins to a single node and that node still melts. Salt the key, replicate the hot key across nodes, or put an L1 cache in front — same toolkit as for hash sharding.
- **vnode count is a tuning knob.** Too few vnodes (say, 1–10 per node) gives uneven ownership and a big load jump on failure. Too many (say, 10k+) costs lookup memory and gossip bandwidth. A few hundred per physical node is the usual sweet spot; Cassandra defaults to 256, Dynamo's paper used 100.
- **Tail imbalance.** A few hundred vnodes per node typically gives ~1.1–1.3x peak-to-average; the asymptotic worst case is ~2x. If your capacity plan sizes to the peak node, that gap is what you pay over the mean. Bounded-load consistent hashing is the formal fix; manual tuning of token assignment is the operational fix.
- **Replica placement under failure.** Naive "next R clockwise" can put two replicas on one physical node (multiple vnodes) or two replicas in the same rack. The placement function must skip nodes already holding a replica and prefer different failure domains. This logic is subtle and worth getting right once.
- **Hash function quality.** A weak hash with clusters or biases breaks the law-of-large-numbers argument that justified vnodes in the first place. Use a well-mixed, fast hash — MurmurHash3, xxHash, MD5 (Ketama uses MD5), SipHash if adversarial inputs are a concern.
- **Coordination on membership change.** When a node joins or leaves, every client and peer must learn the new ring. Gossip protocols (Cassandra, Dynamo) propagate ring state in seconds-to-tens-of-seconds. Stale clients route to wrong nodes during the window: the design must tolerate temporary mis-routes — re-route, forward, or fail-and-retry — until convergence.
- **Data movement is real I/O.** "Only `1/N` of keys move" still means `1/N` of your data crossing the wire when you add a node. Throttle the rebalance, do it during low-traffic windows, and monitor source-node load while it bleeds keys to the new node.

## 5. Real-world and interviewer probes

In the wild:

- **Amazon Dynamo** (the 2007 paper) introduced consistent hashing with virtual nodes to internet-scale storage; its descendants (DynamoDB, Riak, Voldemort) all use the same placement substrate.
- **Apache Cassandra** has used vnodes by default since 1.2 (256 tokens per node by default); the partitioner (Murmur3Partitioner) hashes the partition key onto a 64-bit ring.
- **Memcached client libraries** ship the *Ketama* algorithm (Last.fm, 2007): MD5 of the server name, 160 vnodes per server, ring lookup on the client. The server is unaware; consistency is the client's problem.
- **Redis Cluster** is a near-relative: it uses a fixed 16384-slot space (`CRC16(key) mod 16384`) rather than a hash ring, but the operational story is identical — add a node, migrate some slots, only those keys move.
- **Akamai's CDN** uses consistent hashing for content placement across edge caches; the original Karger et al. paper (1997) was motivated by exactly this problem.

Probes:

- *"Why virtual nodes?"* — Two reasons. They smooth ownership toward `1/N` per physical node by the law of large numbers. And they bound the blast radius of a failure: when a node dies, its 200 vnode arcs are scattered across the ring, so its load spreads across many neighbors instead of doubling on one.
- *"What fraction of keys move when one node is added?"* — `~1/N` for the (N+1)th node. With `hash(key) % N`, almost every key moves because `% N` and `% (N+1)` are unrelated partitions. That ratio is the entire reason consistent hashing exists.
- *"What's the worst-case load skew?"* — Asymptotically ~2x average; in practice with 100–256 vnodes per node, more like 1.1–1.3x. "Consistent hashing with bounded loads" (Mirrokni et al., 2016) caps load per node at `(1 + epsilon)` times the average by walking clockwise past any node already at the cap.
- *"How do replicas work?"* — Walk clockwise and pick the next R *distinct* physical nodes; with vnodes the same physical node can appear multiple times in a row, so you skip those. Rack- and AZ-aware placement adds a second skip: prefer candidates in failure domains not yet represented. The first chosen node is the coordinator. Combined with R/W quorums where `R + W > N`, this is the placement substrate for tunable-consistency stores.
- *"4 nodes with `hash % 4`, you add a 5th — what happens?"* — Almost every key gets reassigned, because `hash % 4` and `hash % 5` partition the key space differently and only a small fraction happen to keep the same owner. With consistent hashing, only the keys in the new node's arc — about `1/5` — move. That's the difference between a several-hour rebalance and a several-day one.
