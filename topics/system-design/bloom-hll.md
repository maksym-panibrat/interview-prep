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

For `n` inserted keys, the false-positive rate and the optimal sizing for target `p` at expected cardinality `n` are:

```
p   ≈ (1 - e^{-kn/m})^k
m   = -n · ln(p) / (ln 2)^2     bits
k   = (m/n) · ln 2 ≈ 0.69 (m/n) hash functions
```

Walk it for **10M URLs at 1% FPR**: `m/n ≈ 9.6 bits per element`, so `m ≈ 96 Mb = 12 MB` and `k = 7` hash functions per insert and per lookup. The HashSet alternative — 10M URL strings at ~150 bytes each with object headers and pointers — is **about 1.5 GB**. **Bloom buys you ~100× memory savings**; the price is roughly 1% extra source lookups when the filter says "maybe" but the key is absent. Since `m` scales with `−ln p`, tightening from 1% to 0.1% costs `ln(10⁻³)/ln(10⁻²) = 1.5×` more memory — ~5 extra bits per element. Each further 10× FPR cut adds another fixed ~5 bits, **linear in the log of the rate, not a doubling per nine of accuracy**.

### Counting Bloom and Cuckoo filters

**Vanilla Bloom cannot delete.** Clearing the `k` bits for a removed key would also clear bits other inserted keys depend on, turning their lookups into false negatives — and false negatives are the one failure mode Bloom's contract forbids. **Counting Bloom** replaces each bit with a small counter (4 bits is typical): insert increments the `k` slots, delete decrements them, query treats nonzero as set. You pay ~4× the memory, and counter overflow can still wedge a slot at the saturation value if a key is inserted more times than the counter can hold.

**Cuckoo filter** sidesteps deletion by storing **compact fingerprints** (e.g. 8–16 bits, a hash of the key truncated) in a cuckoo hash table with two candidate buckets per key. Insertion places the fingerprint in either bucket; if both are full, it evicts a resident fingerprint to *its* alternate bucket, repeating until a slot opens or a retry budget is hit. **Deletion is just removing the fingerprint** from whichever of the two buckets holds it. At ≤1% FPR Cuckoo beats Bloom on space (around 7 bits/element vs. ~10), gets better cache locality (two bucket probes vs. `k` scattered bits), and supports deletion natively. The catch: **insertion can fail above ~95% load** when an eviction chain exhausts its retry budget — you can't run a Cuckoo to the brim, and a failed insert means resize-and-rebuild.

### HyperLogLog

Hash each item to a uniformly distributed value and split it into a **bucket selector** (the leading `log2 m` bits) and a **tail**. Per bucket, track the maximum number of leading zeros seen in its tail across all items routed there. Because hash bits are uniform, a `ρ`-leading-zero prefix is a 1-in-`2^ρ` event, so each bucket's max `ρ` is a noisy estimator of `log2(n/m)` — the cardinality routed to it. The harmonic mean of `2^ρ_j` across buckets, scaled by `m` and a bias constant `α_m`, gives the cardinality estimate, with relative standard error `≈ 1.04 / √m`.

Walk it for **counting unique source IPs hitting your service in a day**. With `m = 2^12 = 4096` buckets at 6 bits each, the register array is `4096 × 6 bits ≈ 3 KB`, and the error is `1.04 / √4096 ≈ 1.6%`. Bumping to `m = 2^14 = 16384` buckets gives `≈ 12 KB` for `1.04 / √16384 ≈ 0.8%` error. The startling part: **at 100M distinct IPs, HLL still uses 3 KB**. A HashSet of 100M IPv4-as-strings is **on the order of a gigabyte**; HLL is six orders of magnitude smaller for ~1.6% error, **and the size does not grow with cardinality** — same 3 KB at a thousand IPs or a trillion.

Pure HLL underestimates at small cardinality; **HLL++** (Google, 2013) detects the low-end regime and switches to a linear-counting estimator from the empty-bucket count, hiding the regime change behind one knob. BigQuery and DataSketches implement HLL++ directly; Redis ships a related dense/sparse HLL with its own bias correction. HLL tells you *how many distinct*, not *which ones* — pair with a separate structure if you also need identity.

### Mergeability — the distributed-systems point

This is the property that makes both indispensable at scale. **Bloom merge is bitwise OR.** Picture 100 shards, each maintaining its own Bloom filter of the keys it stores, all sized to the same `m` and `k`. ORing the 100 bit arrays yields the Bloom filter of the *union* — "is this key in *any* shard?" answered in 12 MB of OR operations, no key movement, no cross-shard fan-out on the read path. **HLL merge is elementwise max** across registers. The same 100 shards each maintain an HLL of their unique visitors; taking the per-bucket max of the 100 register arrays yields the HLL of the global unique-visitor set. **You get distinct-count across shards without ever de-duplicating a single ID across machines** — ship the 3 KB register array, take the max, read cardinality off the merged HLL.

This is how Redis Cluster's `PFCOUNT` works across keys, how edge fleets report hourly unique visitors without a central database, and how ad-tech estimates cross-campaign reach by max-merging per-campaign HLLs instead of moving the underlying IDs.

## 3. When to use

Reach for a **Bloom filter** in front of an expensive lookup ("is this key on disk / in this SSTable / in the [remote cache](caching.md)?" — let the filter answer "no" cheaply, only pay the I/O when it says "maybe"), to filter repeated queries for keys you've already proven absent, for set-membership over a feed you don't store ("have I emitted this URL today?"), or for a giant denylist compressed to a few hundred KB you can ship to every client.

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
