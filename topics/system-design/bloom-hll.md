# Bloom filters and HyperLogLog

## 1. TL;DR

Bloom filters and HyperLogLog (HLL) trade exactness for tiny, fixed memory. A **Bloom filter** answers "have I seen this key?" with possible false positives but never false negatives — its job is to short-circuit an expensive lookup when the answer is reliably "no." **HyperLogLog** estimates "how many distinct items?" with sub-2% relative error using a few kilobytes whether the true count is a thousand or a billion. Both merge across shards, which is what makes them indispensable in distributed systems where you can't afford to materialize the full set on any one node.

## 2. How it works

### Bloom filter

A bit array of length `m` plus `k` independent hash functions mapping a key to indices in `[0, m)`. **Insert(x)** sets the `k` bits at `h_1(x)..h_k(x)`. **Query(x)** returns "maybe" if all `k` are 1, "definitely absent" if any is 0. False negatives are impossible — bits never get cleared. False positives happen when other insertions collectively set the same `k` bits.

A worked example with `m = 16`, `k = 3`:

```
Insert "alice"  -> bits {2, 7, 13} set
Insert "bob"    -> bits {0, 7, 11} set

index:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
bits:   1  0  1  0  0  0  0  1  0  0  0  1  0  1  0  0

Query "alice"  -> {2, 7, 13} all 1 -> "maybe"  (true positive)
Query "carol"  -> {0, 7, 11} all 1 -> "maybe"  (false positive!)
Query "dave"   -> {3, 9, 14} any 0 -> "no"     (true negative)
```

`carol` was never inserted, but her three bits were set by `alice` and `bob` together. That is the false-positive event.

For `n` inserted keys, the false-positive rate is approximately `p ≈ (1 - e^{-kn/m})^k`. Optimal sizing for target `p` at expected cardinality `n`: `m = -n · ln(p) / (ln 2)^2` bits and `k = (m/n) · ln 2` hash functions. A 1% rate at `n = 10M` takes about 12 MB and `k = 7`; cutting `p` to 0.1% roughly doubles the memory.

### Counting Bloom and Cuckoo filters

Vanilla Bloom does not support deletion: clearing a bit could falsify keys that share it. **Counting Bloom** uses small counters (4 bits typical) per slot — insert increments, delete decrements, ~4× the memory. **Cuckoo filter** stores compact fingerprints in a hash table with cuckoo-eviction insertion: supports deletion, beats Bloom on space at low false-positive rates, better cache locality. Trade is operational complexity and a non-trivial high-load failure (see §4).

### HyperLogLog

Hash each item to a uniformly distributed value and split it into a bucket selector and a tail. Per bucket, track the maximum number of leading zeros seen in its tail. Because hash bits are uniform, a `ρ`-leading-zero prefix is a 1-in-`2^ρ` event, so the maximum `ρ` per bucket is a noisy estimator of `log2(n)`. Averaging across `m` buckets via a harmonic mean gives the cardinality estimate, with relative standard error `~1.04 / √m`.

Concrete sizing: `m = 2^12 = 4096` buckets at 6 bits each is about **3 KB** and yields **~1.6% relative error**, whether you're counting 10 thousand or 10 billion distinct items. Bumping to `2^14` buckets (~12 KB) cuts the error to ~0.8%.

Pure HLL underestimates at small cardinality; **HLL++** (Redis, BigQuery, DataSketches) detects the low-end regime and switches to a linear-counting estimator from the empty-bucket count, hiding the regime change behind one knob. HLL tells you *how many distinct*, not *which ones* — pair with a separate structure if you also need identity.

### Mergeability — the distributed-systems point

This is why both dominate at scale. **Bloom merge** is bitwise OR of two filters built with the same `m` and `k`, yielding the Bloom of the union. **HLL merge** is elementwise max of two register arrays of the same precision, yielding the HLL of the union. Each shard keeps its own structure locally; ship the fixed-size summary to a coordinator and merge. No re-shuffling, no exact deduplication, no shared state. That is how Redis Cluster computes `PFCOUNT` across keys, how Cassandra ships per-SSTable Bloom filters with replicas, and how a fleet of edge nodes reports unique-visitor counts hourly without a central database.

## 3. When to use

Reach for a **Bloom filter** in front of an expensive lookup ("is this key on disk / in this SSTable / in the remote cache?" — let the filter answer "no" cheaply, only pay the I/O when it says "maybe"), to filter repeated queries for keys you've already proven absent, for set-membership over a feed you don't store ("have I emitted this URL today?"), or for a giant denylist compressed to a few hundred KB you can ship to every client.

Reach for **HLL** for unique-X-per-Y at scale (daily unique visitors, distinct queries per tenant, distinct keys touched in a window), A/B cohort sizing, audience reach, cardinality monitoring on event streams, or anywhere `COUNT(DISTINCT ...)` is the slow query and 1–2% error is fine.

Anti-signals for both: you need exact answers and a wrong one has unacceptable downstream cost (billing, security); cardinality fits in a regular `set`; you need identities not counts (HLL) or the source of truth not a filter (Bloom). Use them as gates in front of an authoritative system, not as the system itself.

## 4. Trade-offs and failure modes

- **Bloom false positives must be handled by the consumer.** Every "maybe" path needs a real lookup behind it. If that branch is itself expensive or has user-visible side effects, the filter's value collapses.
- **Bloom degrades silently when overfilled.** Insert `2n` keys into a filter sized for `n` and the false-positive rate explodes — but no error fires, queries just return "maybe" more often. Track `inserted_count / sized_capacity` and alert before you cross the design point.
- **No deletion in vanilla Bloom.** A long-lived Bloom over a churning set has to be rebuilt periodically off-line from the source of truth. For real-time deletion, use counting Bloom (memory cost) or Cuckoo (insert-failure risk).
- **Cuckoo's high-load failure.** Insertion can fail above ~95% load when the eviction chain exceeds its retry budget. Needs resize headroom; don't run to capacity.
- **HLL gives counts, not items.** If you also need the list, carry a second structure for the slice that needs identity.
- **HLL underestimates at small `n`.** Use HLL++ (linear-counting fallback) unless you're certain you'll never read at low cardinality. Most production libraries already do; verify yours.
- **Hash quality matters.** Both structures assume uniform hash output. Use xxHash, MurmurHash3, or CityHash. A bad hash silently inflates false positives (Bloom) or skews bucket distribution (HLL).
- **Sized for the wrong cardinality.** "We sized for a million, then a feature shipped that pushed it to a hundred million" — accuracy collapses with no alarm. Make capacity an input to monitoring, not just to initial config.

## 5. Real-world and interviewer probes

In the wild:

- **Cassandra, HBase, RocksDB, LevelDB** keep a Bloom filter per SSTable so a key-not-here lookup avoids disk I/O. Canonical "skip expensive lookup."
- **Bitcoin SPV clients** ask peers for blocks filtered through a client-supplied Bloom of addresses of interest, receiving relevant transactions without revealing the exact set.
- **CDN edge caches** use Bloom-style structures to remember "have we ever seen this object?" before populating from origin.
- **Chrome's safe-browsing list** historically shipped as a compressed Bloom-filter-like structure; "maybe malicious" triggered a remote check, "definitely safe" stayed local.
- **Redis** ships HLL natively as `PFADD` / `PFCOUNT` / `PFMERGE` — a few KB per key, cluster-wide merge for free.
- **Druid, Apache DataSketches, Snowflake's and BigQuery's `APPROX_COUNT_DISTINCT`** all use HLL or HLL++ for cardinality at warehouse scale.

Probes:

- *"When would you use a Bloom filter in a database?"* — Per-SSTable membership filter on the read path: only pay disk I/O when the filter says the key *might* be present. Same idea for "is this key in the remote cache" before crossing the network.
- *"Cuckoo vs. Bloom?"* — Cuckoo if you need deletion, better space at low FPR, or cache locality. Bloom for simplicity, well-studied behavior, and easy bitwise-OR merge. Cuckoo's high-load insertion failure is real; size for headroom.
- *"How accurate is HLL?"* — Roughly `1.04 / √m`. `m = 2^12` (~3 KB) gives ~1.6% relative error; `m = 2^14` (~12 KB) gives ~0.8%. Independent of cardinality — same percentage at a million as at a billion.
- *"Distinct counts across a hundred shards?"* — Each shard maintains a local HLL at the same precision. Ship the fixed-size register array to a coordinator, take the elementwise max, read cardinality off the merged HLL. No movement of the actual items.
- *"Why not a HashSet?"* — Linear memory: a billion 16-byte keys is ~16 GB before pointer overhead. HLL stays at a few KB and merges across machines for free. The cost is 1–2% error — fine for analytics, unacceptable for billing.
- *"My Bloom filter has too many false positives — what now?"* — You've inserted past the sizing assumption. Check `inserted_count / sized_capacity`. Rebuild at a higher `m` for the new expected `n`; you cannot shrink false positives in place, only by replacement.
