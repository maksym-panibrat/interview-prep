# Consistent hashing

## 1. TL;DR

Consistent hashing is a [hash-sharding scheme](sharding.md) that **minimizes data movement when nodes are added or removed**. Concretely: a 4-node cluster grown to 5 with `hash(key) % N` reshuffles `~(N-1)/N = 80%` of the keyspace, because `% 4` and `% 5` partition the keys into unrelated buckets. The same change on a hash ring moves `~1/(N+1) = 20%` of keys — only the arc the new node now owns. **That ratio is the entire reason the technique exists**: it turns a several-day cluster reshuffle into a several-hour one, and makes routine capacity changes routine. You reach for it whenever membership shifts under load — distributed caches, Dynamo-style key-value stores, request routing with affinity. The mechanism is a hash ring with virtual nodes; the failure modes are skew (asymptotic ~2x tail without help; 100–256 vnodes per node pulls it to ~1.1–1.3x) and the operational cost of teaching every client about ring membership.

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

Add node D between B and C. Only the keys whose ring position falls in the arc `(B, D]` move — they used to belong to C, now they belong to D. **Every other key's owner is unchanged.** With reasonably uniform hashing the new arc is `~1/(N+1)` of the ring, so growing from N to N+1 moves `~K/(N+1)` of the K keys. Removing a node hands its arc to the next clockwise neighbor — again `~1/N` of keys move.

Walk the contrast against `hash(key) % N`. Going from 4 nodes to 5: the key `hash=37` was on shard `37 % 4 = 1`, now it's on `37 % 5 = 2`. The key `hash=38` was on `2`, now on `3`. **Adjacent moduli partition the keyspace into completely unrelated buckets**, so `~(N-1)/N = 80%` of keys land somewhere new. With consistent hashing, `~1/(N+1) = 20%` of keys move and the other 80% don't even know a node was added. Same workload, four times less data crossing the network.

### Virtual nodes

Hashing one token per physical node gives you a coarse, lumpy ring — three nodes might land at positions that hand 60% of the keyspace to one of them. The failure mode is worse than the imbalance: **when node B fails, B's entire arc transfers to exactly one node — its clockwise successor**. If B and its successor were each carrying their fair `1/N` share, the survivor now carries `2/N`. **One node failure doubles its neighbor's load**, which often means the neighbor falls over and the failure cascades around the ring.

The fix is virtual nodes (vnodes): each physical node owns many ring positions, typically 100–256. The keyspace is sliced finely and the law of large numbers smooths ownership toward `1/N` per physical node. The failure-spread story changes too. With 256 vnodes per physical node, B's 256 arcs are scattered all over the ring, and **the clockwise successor of each B-vnode is some random other physical node**. When B dies, B's load is partitioned across roughly all surviving physical nodes — each takes a `1/(N-1)` share of B's keys, not the whole thing. The blast radius of a failure is bounded by the spread, not the topology of a single arc. Cassandra calls these "tokens"; Dynamo calls them "virtual nodes"; the idea is the same.

### Replication

For a replication factor of R, walk clockwise from the key's position and pick the next R *distinct* physical nodes — the first is the *coordinator*, the rest hold replicas. The "distinct" qualifier is load-bearing: with vnodes, the next vnode clockwise often belongs to a physical node already in the replica set, so you skip past it.

Rack- and AZ-aware variants extend the skip rule to failure domains. Walk Cassandra's `NetworkTopologyStrategy` for `RF=3` across three racks `r1, r2, r3`. Hash the partition key, find the natural owner — say the next vnode clockwise belongs to physical node `n7` in `r1`. That's replica 1. Continue clockwise until you hit a vnode whose physical node lives in a rack other than `r1` — say `n12` in `r2`. That's replica 2. Continue until you find a vnode in the remaining rack `r3` — say `n3`. That's replica 3. **The placement function guarantees the three replicas span three racks**, so a single rack outage costs you at most one replica per partition. The same logic generalizes to AZs and DCs; the per-DC RF in `NetworkTopologyStrategy` runs an independent walk in each datacenter.

Dynamo-style stores combine this layout with [quorum reads and writes](quorum-consistency.md) (`R + W > N`) for tunable consistency; the consistent-hashing ring is the placement substrate underneath.

### Bounded loads

Even with vnodes, consistent hashing has an **asymptotic ~2x worst-case skew at the tail** — in the limit there is a node that owns roughly twice the average load, because vnode positions are random and the heaviest node is whichever one drew unlucky arcs. In practice with 100–256 vnodes per node it sits closer to 1.1–1.3x, but the asymptotic ceiling matters when you're capacity-planning to peak.

Mirrokni, Thorup, and Zadimoghaddam (2016), "Consistent Hashing with Bounded Loads", **caps every node at `(1 + ε)` times the average load** and walks past full nodes. On insert: hash the key, look up the natural owner (the next vnode clockwise). If that owner's current load is below `(1 + ε) × avg_load`, the key lands there as usual. If the owner is at the cap, walk clockwise to the next vnode and re-check; keep walking until you find a node under the cap. The cap is a hard ceiling — by construction, **no node ever exceeds `(1 + ε) × avg_load`**, regardless of how unlucky the vnode placement was. The cost is a per-key probe and a load counter per node; the benefit is provable load balance with the consistent-hashing rebalance property still intact (a key only moves if its natural owner or one of the cap-walk overflow targets joins or leaves). Vimeo's haproxy implementation is the canonical real-world adoption when tail skew matters.

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

- **Hot keys are still hot.** **Consistent hashing solves rebalance pain, not skew.** A single hot key still pins to a single node and that node still melts. Salt the key, replicate the hot key across nodes, or put an L1 cache in front — same toolkit as for hash sharding.
- **vnode count is a tuning knob.** Too few (say, 1–10 per node) gives uneven ownership and a big load jump on failure. Too many (say, 10k+) costs lookup memory and gossip bandwidth. A few hundred is the sweet spot; Cassandra picked 256, Dynamo's paper used 100.
- **Tail imbalance.** A few hundred vnodes per node typically gives ~1.1–1.3x peak-to-average; the asymptotic worst case is ~2x. **If your capacity plan sizes to the peak node, that gap is what you pay over the mean.** Bounded-load consistent hashing is the formal fix; manual tuning of token assignment is the operational one.
- **Replica placement under failure.** Naive "next R clockwise" can put two replicas on one physical node (multiple vnodes back-to-back) or two replicas in the same rack. **The placement function must skip nodes already holding a replica and prefer unused failure domains.** Subtle and worth getting right once.
- **Hash function quality.** A weak hash with clusters or biases breaks the law-of-large-numbers argument that justified vnodes in the first place. Use a well-mixed, fast hash — MurmurHash3, xxHash, MD5 (Ketama uses MD5), SipHash if adversarial inputs are a concern.
- **Coordination on membership change.** When a node joins or leaves, every client and peer must learn the new ring. Gossip protocols (Cassandra, Dynamo) propagate ring state in seconds to tens of seconds. **Stale clients route to wrong nodes during the convergence window**, so the design must tolerate temporary mis-routes — re-route, forward, or fail-and-retry.
- **Data movement is real I/O.** "Only `1/N` of keys move" still means `1/N` of your data crossing the wire when you add a node. Throttle the rebalance, do it in a low-traffic window, and monitor the source node's load while it bleeds keys to the newcomer.

## 5. Real-world and interviewer probes

In the wild:

- **Amazon Dynamo** (the 2007 SOSP paper) introduced consistent hashing with virtual nodes to internet-scale storage; its descendants (DynamoDB, Riak, Voldemort) all use the same placement substrate. **DynamoDB partitions are assigned via consistent hashing internally** — when a hot partition splits or a base table grows past a partition's throughput cap, only that partition's keys re-home, not the whole table.
- **Apache Cassandra** has used vnodes by default since **1.2 (January 2013)** with **256 tokens per node** as the historical default; the partitioner (`Murmur3Partitioner`) hashes the partition key onto a signed 64-bit ring. (Modern releases tune this lower with the `allocate_tokens_for_keyspace` algorithm, but 256 is the number you'll see in interview discussions.)
- **Memcached client libraries** ship the *Ketama* algorithm (Last.fm, 2007): **MD5 of the server name, 160 hashes per server**, ring lookup on the client. The server is unaware that any of this is happening; consistency is entirely the client's problem, which is why a fleet of stale clients can split-brain a memcached pool during a membership change.
- **Redis Cluster** is a near-relative, **not a true ring**: it uses a fixed **16384-slot space** (`CRC16(key) mod 16384`) and an explicit slot-to-node map that ships in cluster gossip. The placement is direct lookup, not clockwise walk. The operational story is the same shape — add a node, migrate some slots, only those keys move — but the mechanism is different and the rebalance is manually orchestrated rather than automatic.
- **Akamai's CDN** uses consistent hashing for content placement across edge caches; the original Karger et al. paper (1997) was motivated by exactly this problem and explicitly named edge caching as the use case.

Probes:

- *"Why virtual nodes?"* — Two reasons. **They smooth ownership toward `1/N` per physical node** by the law of large numbers. And they **bound the blast radius of a failure**: when a node dies, its hundreds of vnode arcs are scattered across the ring, so its load spreads across roughly all surviving neighbors instead of doubling on one.
- *"What fraction of keys move when one node is added?"* — **`~1/(N+1)` for the (N+1)th node.** With `hash(key) % N`, almost every key moves because `% N` and `% (N+1)` partition the keyspace into unrelated buckets. That ratio is the entire reason consistent hashing exists.
- *"What's the worst-case load skew?"* — **Asymptotically ~2x average; in practice with 100–256 vnodes per node, more like 1.1–1.3x.** "Consistent hashing with bounded loads" (Mirrokni et al., 2016) caps load per node at `(1 + ε)` times the average — on insert, if the natural owner is at the cap, walk clockwise to the next under-cap node.
- *"How do replicas work?"* — Walk clockwise and **pick the next R *distinct* physical nodes**; with vnodes the same physical node can appear multiple times in a row, so you skip those. Rack- and AZ-aware placement adds a second skip: prefer candidates in failure domains not yet represented. The first chosen node is the coordinator. Combined with R/W quorums where `R + W > N`, this is the placement substrate for tunable-consistency stores.
- *"4 nodes with `hash % 4`, you add a 5th — what happens?"* — **About 80% of keys get reassigned** because `hash % 4` and `hash % 5` partition the keyspace into unrelated buckets and only the keys whose `% 4` and `% 5` answers happen to coincide stay put. With consistent hashing, only the keys in the new node's arc — about 20% — move. **That's the difference between a several-day rebalance and a several-hour one.**
