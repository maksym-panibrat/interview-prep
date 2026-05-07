# Caching

## 1. TL;DR

Caching moves data closer to the reader so a request can skip expensive work — a database query, a downstream call, a model inference, a transcontinental round trip. The mechanics are easy; the strategy decisions (where the cache lives, who writes it, when entries expire) are what determine whether you get a speedup or a correctness nightmare. Most cache outages are not "the cache went down" but stampede events triggered by the cache working exactly as designed, so stampede mitigation is the part interviewers want to hear you talk about.

## 2. How it works

A cache sits between the reader and the source of truth, holding recently or frequently used values keyed by some derivation of the request. Four strategies cover almost every production cache; pick by who owns the read path, who owns the write path, and your tolerance for staleness.

### Cache-aside (lazy loading)

The application owns miss handling. On a read it checks the cache; on a miss the application reads the source and writes the result back. On a write it updates the source and either invalidates or updates the cache. Simple, explicit, **the most common shape in the wild**. Downside: cache and source drift on writes, and every miss pays a full source read before the cache warms. **Every call site re-implements its own stampede protection** — and in a service of any size, some call sites won't.

### Read-through

The cache library or proxy owns miss handling. The application calls `cache.get(key)` and the library, on miss, invokes a registered loader and populates the entry — the application never sees the miss. The architectural difference from cache-aside is structural, not aesthetic: **the loader function is the single point that needs single-flight, jitter, and SWR**, so read-through *centralizes the discipline* one library deep instead of scattering it across every call site. Costs: you depend on a library that does the right thing under contention, and the cache becomes a hard dependency on the read path — if it's down, you can't degrade to a direct source read without a fallback path.

### Write-through

Writes go to the cache and the source synchronously, in the same call. Consistent at write time, but writes pay both latencies and fail if either side is unavailable. Pairs naturally with read-through.

### Write-back (write-behind)

Writes go to the cache only and the client is acknowledged immediately; a background worker flushes to the source asynchronously. The fastest write path you can build. Durability and consistency risk: any acknowledged write that has not yet been flushed is lost if the cache node crashes, the process OOMs, or the eviction policy reclaims the dirty entry — and the client has no way to know. The exposure window is `flush_interval + flush_queue_depth / drain_rate`. Reasonable for high-volume telemetry or counters where a few seconds of loss is tolerable; dangerous as the default for anything you bill on.

### TTL and stampede mitigation

Every cached value has an expiry. To see why this is the part of the design that hurts, picture a hot key serving **10k QPS at a 99% hit rate** — exactly the kind of cached lookup you put a cache in front of in the first place. The TTL ticks to zero. In the next millisecond, **all 10k concurrent requests miss simultaneously and pile onto the source**.

The source — say a 4-core Postgres — was sized for the **100 QPS** that leaks past the cache, not 10k. The connection pool saturates, queries queue, the page cache thrashes as the leaders all contend for the same row. While this is happening, *other* keys' TTLs expire and their reload requests join the queue behind the stampede — they can't reload because Postgres is too busy serving the first stampede. **One expired key has cascaded into a ten-minute outage.** This is *cache stampede* (or *dogpile*); the mitigations below, used in combination, are what keep it from happening.

- **Single-flight (request coalescing).** When N concurrent requests miss the same key, allow exactly one to fetch from the source; the other N-1 wait on the in-flight result. Concretely: the worker pool keeps a shared `Map<key, Future<value>>` guarded by a mutex. The first requester takes the lock, finds no entry, inserts a fresh `Future`, releases the lock, and starts the source read. The next 9,999 requesters take the lock, find the existing `Future`, release the lock, and `await` it. The source sees **exactly one read** instead of 10k. Go's stdlib ships this as `singleflight.Group`; the pattern is the same in any language.

- **Jittered TTL.** A deploy warms 10k keys at second 0 with `ttl = 60s`. At second 60, all 10k expire simultaneously — a synchronized stampede dressed up as a TTL. Use `ttl = 60s + rand(0, 20s)` and the same 10k keys now expire uniformly across seconds 60–80, so the miss rate stays near steady-state instead of spiking. **Jitter is the single cheapest stampede mitigation**; add it before anything else.

- **Stale-while-revalidate (SWR).** On a request that finds an expired-but-still-present value, **serve the stale value immediately and refresh the cache asynchronously**. The user sees no latency hit; the source sees one refresh per stale-window, not one per request. HTTP `Cache-Control: stale-while-revalidate` standardizes this; CDNs implement it natively.

- **Negative caching.** Cache "not found" results too — with a *short* TTL. Without it, every request for a missing key is a guaranteed source hit; with a 30s negative TTL you cap the damage from a popular missing key (misconfigured client, deleted record someone is still polling) at a manageable miss-storm. A [Bloom filter](bloom-hll.md) is the fixed-memory variant for the same job — answer "definitely absent" cheaply before paying the source lookup.

- **Probabilistic early refresh.** As a key's age approaches its TTL, each read has a small randomized probability of triggering an early refresh. The XFetch algorithm (Vattani, Chierichetti, Lowenstein, 2015) formalizes this — on each read, recompute if `now - delta * beta * ln(rand()) >= expiry`, where `delta` is the measured recompute cost, `beta` is a tunable aggressiveness factor (typically 1), and `rand()` draws from `(0, 1)`. Since `ln(rand())` is negative, the LHS exceeds `now`, and the probability of triggering rises smoothly toward 1 as `now` approaches `expiry`. **Hot keys get refreshed by exactly one reader before they expire**, with no synchronized expiry event.

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

- **Staleness vs. consistency.** Every cached value is potentially stale. **TTL encodes "how stale is acceptable for this domain"** — pricing data wants seconds, a display name tolerates an hour, a product taxonomy survives a day. Pick TTL by the cost of staleness, not by what feels round.
- **Cache stampede / dogpile.** Covered in §2 — single-flight + jittered TTL + SWR. **The failure mode interviewers expect you to volunteer**, so volunteer it.
- **Thundering herd on cache restart.** The cache restarts (deploy, OOM, instance failure) and comes back empty. Every read is now a miss; the source absorbs the **entire production read load uncached** — and unlike the single-key stampede, single-flight does not help, because the misses are spread across millions of distinct keys. Mitigate with pre-warming (replay a captured key list before serving traffic), rolling restarts that keep most of the fleet warm, or a persistent local snapshot (Redis RDB/AOF) so a restarted node comes up populated.
- **Coherence between cache and source.** A write that bypasses the cache leaves the cached value stale until TTL. If the writer is a different service, a batch job, or a human at a SQL prompt, the cache will silently lie. Choose your reconciliation contract: write-through, invalidate-on-write, or TTL alone — and **write it down**, because the bug otherwise lives in the gap between two teams' assumptions.
- **Negative-cache amplification.** Walk the bug. A config push at minute 0 makes the user-lookup service erroneously return 404 for valid IDs. The negative cache stores `{user_id: NOT_FOUND}` with a 5-minute TTL. At minute 1 you ship the fix and the source recovers — but **the cache layer keeps serving the stale 404 until minute 6**, four full minutes after the source is healthy. The mitigations are stacked: keep negative TTLs short (10–30s, not minutes); put negative entries in a **separate namespace** so they can be flushed without touching positive entries; and **wire a deploy hook** that flushes the negative namespace whenever the source service rolls — so a fix-the-bug deploy automatically clears the cache that's poisoning users.
- **Hot keys.** Traffic is rarely uniform; one key may take 80% of the load. A sharded cache that hashes keys to nodes rebalances poorly — the hot shard is permanently overloaded while its neighbors idle. Mitigations: replicate the hot key across nodes, **key-split** (`key#0..key#N` chosen randomly per request, writers fan out to all suffixes), or put a small in-process L1 in front of the remote L2 so most hot reads never leave the process.
- **Memory pressure and eviction.** A full cache evicts to make room. LRU is the default; LFU helps when frequency is more stable than recency. **Track the eviction rate as a first-class signal** — sustained eviction means your working set exceeds your cache size, your hit rate is dropping, and you should be sizing up or tightening what you cache.

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
