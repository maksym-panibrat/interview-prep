# Caching

## 1. TL;DR

Caching moves data closer to the reader so a request can skip expensive work — a database query, a downstream call, a model inference, a transcontinental round trip. The mechanics are easy; the strategy decisions (where the cache lives, who writes it, when entries expire) are what determine whether you get a speedup or a correctness nightmare. Most cache outages are not "the cache went down" but stampede events triggered by the cache working exactly as designed, so stampede mitigation is the part interviewers want to hear you talk about.

## 2. How it works

A cache sits between the reader and the source of truth, holding recently or frequently used values keyed by some derivation of the request. Four strategies cover almost every production cache; pick by who owns the read path, who owns the write path, and your tolerance for staleness.

### Cache-aside (lazy loading)

The application owns miss handling. On a read it checks the cache; on a miss the application reads the source and writes the result back. On a write it updates the source and either invalidates or updates the cache. Simple, explicit, the most common shape in the wild. Downside: cache and source drift on writes, and every miss pays a full source read before the cache warms. Each call site is responsible for its own stampede protection.

### Read-through

The cache library or proxy owns miss handling. The application calls `cache.get(key)` and the library, on miss, invokes a registered loader and populates the entry — the application never sees the miss. Cleaner abstraction and the natural place to centralize single-flight, jitter, and SWR for every caller. Costs: you depend on a library that does the right thing under contention, and the cache becomes a hard dependency on the read path.

### Write-through

Writes go to the cache and the source synchronously, in the same call. Consistent at write time, but writes pay both latencies and fail if either side is unavailable. Pairs naturally with read-through.

### Write-back (write-behind)

Writes go to the cache only and the client is acknowledged immediately; a background worker flushes to the source asynchronously. The fastest write path you can build. Durability and consistency risk: any acknowledged write that has not yet been flushed is lost if the cache node crashes, the process OOMs, or the eviction policy reclaims the dirty entry — and the client has no way to know. The exposure window is `flush_interval + flush_queue_depth / drain_rate`. Reasonable for high-volume telemetry or counters where a few seconds of loss is tolerable; dangerous as the default for anything you bill on.

### TTL and stampede mitigation

Every cached value has an expiry. The naive design — fixed TTL, populate on miss — works fine until a popular key expires under load, at which point you discover what a *cache stampede* (or *dogpile*) feels like: thousands of concurrent requests all miss simultaneously, all stampede the source, source falls over. The five techniques below, used in combination, are how you survive this.

- **Single-flight (request coalescing).** When N concurrent requests miss the same key, allow exactly one to fetch from the source; the other N-1 wait on the in-flight result. Implemented as a per-key mutex or `singleflight.Group` (Go's stdlib name has stuck). Eliminates duplicate work for the cold-key case.

- **Jittered TTL.** Instead of `ttl = 600s`, use `ttl = 600s ± rand(60s)`. A batch of keys populated together in a deploy will otherwise expire together; jitter spreads the expiry storm across a window.

- **Stale-while-revalidate (SWR).** On a request that finds an expired-but-still-present value, serve the stale value immediately and refresh the cache asynchronously. The user sees no latency hit; the source sees one refresh per stale-window, not one per request. HTTP `Cache-Control: stale-while-revalidate` standardizes this; CDNs implement it natively.

- **Negative caching.** Cache "not found" results too — with a *short* TTL. Without it, every request for a missing key is a guaranteed source hit; with a 30s negative TTL you cap the damage from a popular missing key (misconfigured client, deleted record someone is still polling) at a manageable miss-storm. A [Bloom filter](bloom-hll.md) is the fixed-memory variant for the same job — answer "definitely absent" cheaply before paying the source lookup.

- **Probabilistic early refresh.** As a key's age approaches its TTL, each read has a small randomized probability of triggering an early refresh. The XFetch algorithm (Vattani, Chierichetti, Lowenstein, 2015) formalizes this — on each read, recompute if `now - delta * beta * ln(rand()) >= expiry`, where `delta` is the measured recompute cost, `beta` is a tunable aggressiveness factor (typically 1), and `rand()` draws from `(0, 1)`. Since `ln(rand())` is negative, the LHS exceeds `now`, and the probability of triggering rises smoothly toward 1 as `now` approaches `expiry`. Hot keys get refreshed by exactly one reader before they expire, with no synchronized expiry event.

Jittered TTL plus single-flight plus SWR is the bread-and-butter combination.

## 3. When to use

- **Read-heavy workloads** with low write rate or tolerable staleness. Classic shape: 1000:1 read-to-write, a 60-second tolerance for stale data, an obvious 10x speedup.
- **Expensive computations or downstream calls** — slow database queries, search index fan-outs, LLM inferences, third-party APIs you pay per call for. Anything where computing the value costs much more than storing it. When the "expensive computation" is a denormalized join you keep recomputing, the right shape is often a [materialized read model](cqrs-read-models.md), not a cache.
- **Geographically distant calls.** A CDN in front of static assets, a regional cache in front of a single-region origin. The cache exists to absorb the speed of light.
- **Smoothing bursty load.** If the source can serve steady-state QPS but not peaks, a cache absorbs the spikes.

Anti-signals:

- **Write-heavy workloads with strong consistency requirements.** The cache becomes a coherence problem you have to solve forever, and the hit rate is poor anyway.
- **Per-user data with no reuse.** A cache for a key only one user ever requests at most once is just an extra hop and an extra component to fail.
- **Tiny, fast sources.** A cache in front of a primary-key lookup on a warm in-memory database is overhead, not speedup.

## 4. Trade-offs and failure modes

- **Staleness vs. consistency.** Every cached value is potentially stale. TTL encodes "how stale is acceptable for this domain" — pricing data wants seconds, a display name tolerates an hour, a product taxonomy survives a day. Pick TTL by the cost of staleness.
- **Cache stampede / dogpile.** A popular hot key expires; thousands of concurrent requests miss simultaneously and stampede the source. Source QPS spikes by orders of magnitude in milliseconds. Mitigate with single-flight, jittered TTL, and SWR. This is the failure mode interviewers expect you to volunteer.
- **Thundering herd on cache restart.** The cache restarts (deploy, OOM, instance failure) and comes back empty. Every read is now a miss; the source absorbs the entire production load uncached. Mitigate with pre-warming (replay a captured key list), rolling restarts, or a persistent local snapshot.
- **Coherence between cache and source.** A write that bypasses the cache leaves the cached value stale until TTL. If the writer is a different service, a batch job, or a human at a SQL prompt, the cache will silently lie. Choose your reconciliation contract: write-through, invalidate-on-write, or TTL alone.
- **Negative-cache amplification.** A bug returns "not found" for a key that exists; the negative cache happily stores it for 30 seconds. The fix ships, but every replica still serves the cached "not found" until TTL. The bigger the negative TTL, the longer the incident outlives the fix. Keep negative TTLs short and have a way to flush them.
- **Hot keys.** Traffic is rarely uniform; one key may take 80% of the load. A sharded cache that hashes keys to nodes rebalances poorly — the hot shard is permanently overloaded. Mitigations: replicate the hot key across nodes, key-split (`key#0..key#N` chosen randomly per request), or put a small in-process L1 in front of the remote L2.
- **Memory pressure and eviction.** A full cache evicts to make room. LRU is the default; LFU helps when frequency is more stable than recency. Track the *eviction rate* as a first-class signal — high eviction means your working set exceeds your cache size and your hit rate is dropping.

## 5. Real-world and interviewer probes

In the wild:

- **Memcached** and **Redis** dominate the process-local-but-network-attached layer. Redis adds data structures, persistence, and replication; Memcached stays simple and very fast.
- **Varnish** for HTTP-layer caching in front of origin servers.
- **CDNs** — Cloudflare, Fastly, CloudFront, Akamai — for geographically distributed edge caching, with native SWR and stale-if-error semantics.
- **AWS ElastiCache**, **GCP Memorystore**, **Azure Cache for Redis** as the managed offerings.
- **Facebook's memcache deployment** uses a *leases* mechanism — on a miss the cache hands one client a lease token to populate the key; concurrent missers wait or accept a stale value — to control stampedes at scale (Nishtala et al., NSDI 2013). **Facebook TAO** is a separate system: a graph cache over MySQL with a write-through, regional-leader model, not the leases mechanism.
- **Netflix EVCache** is a multi-region Memcached-derived cache designed for AWS, with cross-region replication and tunable consistency.

Probes:

- *"Walk me through cache stampede mitigation."* — Single-flight to coalesce concurrent misses on the same key; jittered TTL to desynchronize bulk-loaded keys; stale-while-revalidate to absorb the refresh cost without a user-facing miss; optionally probabilistic early refresh so hot keys never see expiry. Negative caching to cap miss-storms on missing keys.
- *"Cache-aside vs. read-through?"* — Cache-aside is simpler, more explicit, and lets the application decide what to cache. Read-through hides the source from the read path, makes the cache a swappable dependency, and centralizes stampede protection in the cache library. Pick read-through when you want the abstraction; cache-aside when you want the control.
- *"How do you keep cache and source consistent on writes?"* — Three options on a spectrum. Write-through writes both synchronously, consistent at write time, slower writes. Invalidate-on-write deletes the cache key after the source write, eventually consistent within one round trip. TTL alone, eventually consistent within the TTL. Pick by tolerable staleness and write-path latency budget.
- *"How do you handle a hot key?"* — Key splitting, where the application appends a random suffix `key#0..key#N` per request and writers fan out to all suffixes. Replication, where the cache layer keeps the hot key on multiple nodes. An in-process L1 (small LRU in the app process) in front of the remote L2 (Redis), absorbing hot-key reads inside the process before they hit the network.
