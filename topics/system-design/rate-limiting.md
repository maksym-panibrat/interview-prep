# Rate limiting

## 1. TL;DR

Rate limiting caps how much traffic a caller can send in a window, so **one client cannot starve everyone else and a downstream cannot be drowned**. The algorithm — token bucket, leaky bucket, fixed window, sliding window log, sliding window counter — sets your burst tolerance and storage cost. The hard part is making it work *distributed* across many gateway instances without the central counter becoming the bottleneck. **Headline trade-off: accuracy vs. throughput** — exact global counts demand a hot key; cheap distributed schemes leak some overshoot.

## 2. How it works

Every algorithm answers two questions: **how many requests in the last `N` seconds for this key**, and **what does "now" mean** when gateway instances see different clocks. The choice between them is a choice about burst behaviour, storage, and how much over-count you'll accept under contention.

### Token bucket

A bucket holds up to `B` tokens and refills at rate `R` per second. Each admitted request takes one token; empty means reject. **Bursts up to `B` allowed; sustained admit rate capped at `R`.** Store two numbers per key — `tokens` and `last_refill_ts` — and lazily refill on access:

```
tokens = min(B, tokens + (now - last_refill_ts) * R)
last_refill_ts = now
if tokens >= 1: tokens -= 1; admit
else:           reject
```

No background timer, no per-second writes — the read-modify-write at request time *is* the refill. The workhorse.

Walk it. **`B = 100`, `R = 10` tokens/sec.** Caller sits idle for 60 seconds; the bucket refills to its cap of 100 (not 600 — `min` clamps). A burst of 100 requests in one second arrives — **all 100 admitted**, bucket drains to 0. Next request 100 ms later: refill adds `0.1 × 10 = 1` token, admit, back to 0. The caller is now pinned to roughly 10 RPS — every additional request waits for the next refill tick. Sustain 11 RPS and the bucket stays empty; the eleventh request each second is rejected. **The bucket size sets how big a burst you tolerate; the refill rate sets the long-run admit rate.** Tune them independently.

### Leaky bucket

A queue with a fixed drain rate. Requests enter the bucket; the bucket drains at rate `R`; full bucket means reject. **Output is smoothed to a constant rate — no bursts on the way out, even when input was bursty.** Sustained admit rate matches token bucket; the difference is what *downstream* sees.

Same parameters — capacity 100, drain 10/sec — and the same 100-request burst. Token bucket admits all 100 instantly and forwards them as a spike. **Leaky bucket admits all 100 into the queue and releases them at exactly 10/sec for the next 10 seconds**; the 101st request during that window is rejected because the queue is full. Pick token bucket when the *caller's* burstiness is fine and you only care about long-run rate. Pick leaky bucket when the *downstream* — a payment processor, a single-writer DB — cannot absorb a 100-RPS spike even if the average is fine.

### Fixed window counter

Count requests per `(key, current_window)`, e.g. per minute. Cheap — one integer per key per window with a TTL — and trivially atomic via `INCR`. The classic flaw is the **boundary burst**.

Walk it. Limit is **100 requests per minute**. At `12:00:59` the client sends 100 requests — all admitted, the `12:00` counter hits exactly 100. One second later at `12:01:00` the window rolls; the `12:01` counter starts at zero. Client sends another 100 — also all admitted. **The caller just landed 200 requests in roughly two seconds — an effective rate of ~6,000/min — without any single window's counter ever exceeding the legal 100.** Any caller who can read a clock can exploit this; bots do, regularly. Use fixed window only when the doubling at the seam genuinely doesn't matter (e.g. a daily quota where two days' worth in a few seconds is still fine for the downstream).

### Sliding window log

Store a timestamp per request, count timestamps within the last `N` seconds. Exact, no boundary effect, but storage is `O(rate × window)` per key. Practical only when both rate and key cardinality are small.

### Sliding window counter

A weighted average of the previous window's count and the current window's count, prorated by how far into the current window you are. **Small error band, two integers per key — the practical compromise most production limiters land on.**

```
elapsed = (now - current_window_start) / window_size   # fraction in [0, 1)
estimate = prev_count * (1 - elapsed) + current_count
admit iff estimate < limit
```

Walk it. Limit **100/min**, `window_size = 60s`. We're **30 seconds into the current window** (`elapsed = 0.5`); `prev_count = 80`, `current_count = 20`. Estimate = `80 × 0.5 + 20 = 60`, well under 100, admit. The previous window's 80 only contributes its remaining half — which is the model's pretence that those requests were spread evenly across the prior minute. **Same storage as fixed window; no boundary-doubling exploit; a few-percent over- or under-count when traffic is genuinely bursty.** That's the whole bargain.

### Distributed quota

A single gateway instance sees only a fraction of the traffic. To enforce a *global* limit across N instances you pick one of three shapes, and the choice is **accuracy vs. latency vs. infrastructure cost**.

**1. Centralized counter (Redis `INCR` with TTL).** One round trip per request — same-AZ Redis is roughly **0.5–1 ms**, so the limiter adds that to every request's tail. Counts are exact. The cost: a single hot key for `global:api:writes` pins one Redis shard while the other 31 sit idle, and at **10k RPS that one key is the bottleneck** long before Redis itself runs out of CPU. Mitigations: shard the key (`key:0`..`key:15`, randomly pick one to `INCR`, sum all 16 to check) — turns one hot key into 16 warm ones at the cost of 16 reads on the check path; or use a Lua script to make the refill-and-decide atomic so you do one round trip instead of two.

**2. Per-instance quota with periodic sync.** Each gateway gets a local share — for a 10k-RPS global limit across 100 instances, each starts with 100 RPS — and syncs to Redis every `T` ms to reconcile. Local check is microseconds, no Redis on the hot path. The cost is **bounded over-shoot during a sync interval**. Worst case: every instance burns its local share to zero just before the sync, then refills locally and burns again — `sync_interval × per_instance_rate × instances`. **At `T = 100 ms`, 100 instances, local rate 10/sec each, you can leak ~1,000 requests above the global cap per sync window.** Shorter `T` shrinks the leak but raises sync traffic; the bargain is cap accuracy for tail latency. Resilient to a brief Redis outage — instances keep enforcing local shares.

**3. Probabilistic admission.** Each instance keeps a local estimate of the global incoming rate (gossip, or sampled from Redis), and admits each request with probability `target_global_rate / observed_global_rate`. **No coordination on the hot path, no central counter, no sync.** Drift is bounded by how stale the rate estimate is; you'll over- or under-shoot by tens of percent at the edges of rate changes. Use when "approximately fair under load" is the bar and you'd rather lose a little accuracy than spend a millisecond per request — DDoS shedding, free-tier shaping.

**Defaults.** Most production stacks combine **(1) sharded Redis for billing-critical or contractually exact quotas** with **(2) per-instance for per-user fairness**, and reserve (3) for shedding under attack. Envoy ships exactly this split: a `local_ratelimit` filter for fast in-process checks and a `ratelimit` filter that calls an external service.

## 3. When to use

- **Public API protection from abuse and free-tier overuse** — the canonical case. **One scraper must not consume capacity you owe paying customers.**
- **Per-tenant fairness in multi-tenant systems.** A noisy tenant cannot saturate a shared resource if every tenant has its own bucket.
- [**Backpressure**](backpressure-load-shedding.md) **source for downstream protection.** When a downstream has a hard capacity — third-party API, single-writer database, ML inference cluster — **the rate limiter is what keeps you under that ceiling**, not the downstream itself.
- **Cost control.** Third-party APIs billed per call, LLM token budgets, expensive external lookups — the rate limiter is your budget enforcement point.

**Anti-signal:** internal RPC between trusted services that scale together. Limiting your own services from each other usually means the wrong circuit in the wrong place — **what you want is a concurrency limit and a circuit breaker, not a quota**. Rate limiting is for *adversarial or unbounded* sources.

## 4. Trade-offs and failure modes

- **Algorithm choice is a behaviour choice.** Token bucket allows bursts — right for human-driven UIs and bursty batch jobs. Leaky bucket smooths to constant rate — right for a downstream that hates spikes. Fixed window is cheap but the boundary burst gets exploited; **sliding window counter is the safe default.**
- **The distributed counter is a hot key.** A single Redis key for "global API limit" saturates one shard while the rest sit idle. Shard the counter, sum at decision time, or move to per-instance quotas with sync. **Treat the counter as a workload, not a config value.**
- **Clock skew across gateway instances.** Two instances disagree on "now" by 200 ms; with a 1-second sliding window, the same request gets opposite verdicts depending on which instance handled it. Sliding-log mitigates because every event carries its own timestamp; counter-based schemes need NTP-tight clocks and a window slightly larger than the user-visible promise.
- **Per-key memory explosion.** Per-user limits across millions of users blow up Redis memory linearly. At huge scale, trade exactness for fixed memory: **count-min sketch** for approximate counts, **approximate top-K** (Misra-Gries, Space-Saving) for the heaviest hitters — the abusers, who are the keys you actually care about.
- **Fail open or fail closed when the limiter itself goes down?** Walk the decision. Redis becomes unreachable. **Fail open**: every request gets admitted; if you sit between users and a downstream that *needed* the limiter, the downstream sees full unrestricted traffic and blows up — you've just turned a Redis blip into an application outage. **Fail closed**: nothing gets admitted; you become the outage even though every backend is healthy. The right answer depends on **what the limiter protects**. Billing-critical or quota-bound paths (LLM tokens, paid third-party APIs, "we promised customer X exactly this rate"): fail closed — refusing is cheaper than overcharging or breaching contract. SLA-bound public endpoints with elastic downstreams: fail open — degraded fairness for ten minutes beats a self-inflicted outage. **Pick per limiter, document it on the runbook, and rehearse it** — the limiter's failure mode is the platform's failure mode, and you don't want to discover yours during the incident.
- **Synchronised retry storm.** All throttled clients back off by exactly the same `Retry-After` and retry on the same boundary, producing a sawtooth that hammers you every minute. **Always jitter** — server returns `Retry-After`, clients add uniform random jitter on top — or the limit becomes a metronome the whole population dances to.
- **A rate limiter does not stop a single greedy consumer.** One client opening 10,000 concurrent connections each at 1 RPS sits under every per-connection rate limit and still kills you. **Pair rate limits with concurrency limits per key** — rate governs flow over time, concurrency governs in-flight.

## 5. Real-world and interviewer probes

**In the wild.** Stripe uses a token bucket per account with separate buckets for reads vs. writes. Cloudflare's rate-limiting product is sliding window under the hood. AWS API Gateway uses token buckets at account and per-method scope. GitHub's "secondary rate limits" exist because the primary per-hour quota was too coarse for the abuse patterns they cared about. **Envoy ships both a local filter (per-instance, no central state, fast) and a global filter (external service, accurate, slower) — most deployments use both**: local as a cheap first line, global where accuracy matters.

**Probes.**

- *"Token bucket vs. leaky bucket?"* — Token bucket allows bursts up to bucket size, then settles to the refill rate. Leaky bucket smooths everything to a constant output rate. **Pick token bucket when the *caller's* bursts are fine; pick leaky bucket when the *downstream* cannot tolerate spikes** — a payment processor, a single-writer DB.
- *"Distributed across 100 gateway instances?"* — Three shapes, pick by what you need. Centralized Redis (hot-key bottleneck, fix with key sharding) when counts must be exact. Per-instance with periodic sync when latency matters more than the few-percent overshoot during a sync interval. Probabilistic when you're shedding under attack and approximate is fine. **"Exactly N per second globally" is rarely the actual requirement** — surface the real constraint.
- *"Fixed vs. sliding window?"* — Fixed is one counter per `(key, window)`, dirt cheap and atomic, but a client can deliver `2 × limit` across the boundary by timing the seam. **Sliding window counter weighs previous and current window's counts: same storage cost, no boundary burst, a few-percent approximate.** Sliding-log is exact but storage scales with rate.
- *"The limiter is down — fail open or closed?"* — Depends on what the limiter protects. **Public API guarded against abuse: fail open** — extra traffic for a few minutes is recoverable; becoming a self-inflicted outage isn't. **Billing-critical quotas or protection of a downstream that physically cannot survive overload: fail closed.** Make the choice per limiter, document it on the runbook, rehearse it — don't discover it during the incident.
- *"Per-key memory at huge scale?"* — Tracking millions of distinct keys, exact counters cost too much. Switch to probabilistic structures: **count-min sketch** for "how many requests has this key sent recently" with bounded over-counting in fixed memory; **Misra-Gries or Space-Saving** for approximate top-K in `O(K)` memory regardless of key cardinality. You lose exactness on the long tail but the keys that actually matter — the abusers — still surface.
