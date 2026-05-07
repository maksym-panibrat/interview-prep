# Rate limiting

## 1. TL;DR

Rate limiting caps how much traffic a caller can send in a window, so one client cannot starve everyone else and a downstream cannot be drowned. Choice of algorithm — token bucket, leaky bucket, fixed window, sliding window log, sliding window counter — sets your burst tolerance and storage cost. The hard part is making it work *distributed* across many gateway instances without the central counter becoming the bottleneck. Headline trade-off: **accuracy vs. throughput** — exact global counts demand a hot key; cheap distributed schemes leak some over-shoot.

## 2. How it works

Every algorithm answers the same question two ways: how many requests in the last N seconds for this key, and what does "now" mean when gateway instances see different clocks?

### Token bucket

A bucket holds up to `B` tokens and refills at rate `R` per second. Each admitted request takes one token; empty means reject. Bursts up to `B` allowed; sustained admit rate capped at `R`. Store two numbers per key — `tokens` and `last_refill_ts` — and lazily refill on access: `tokens = min(B, tokens + (now - last_refill_ts) * R)`. The workhorse.

```
refill at R tokens/sec
        |
        v
   +----------+
   |  oo o o o|  capacity B
   +----------+
        |
   request takes 1 token; empty -> reject
```

### Leaky bucket

A queue with a fixed drain rate. Requests enter the bucket; the bucket drains at rate `R`; full bucket means reject. Output is *smoothed* to a constant rate — no bursts on the way out, even when input was bursty. Sustained rate matches token bucket; the difference shows up in burst behaviour.

### Fixed window counter

Count requests per `(key, current_window)`, e.g. per minute. Cheap — one integer per key per window, with TTL — and trivially atomic. The classic flaw is the **boundary burst**: a client sends the full quota in the last second of one window and again in the first second of the next, getting `2 × limit` in two seconds while never crossing any single window's count.

### Sliding window log

Store a timestamp per request, count timestamps within the last `N` seconds. Exact, no boundary effect, but storage is `O(rate × window)` per key. Practical only when both rate and key cardinality are small.

### Sliding window counter

A weighted average of the previous window's count and the current window's count, prorated by how far into the current window you are. Small error band, two integers per key — the practical compromise most production limiters land on. Example: prev=80, current=20, 30% into current → estimate = 80×0.7 + 20 = 76.

### Distributed quota

A single gateway instance sees only a fraction of the traffic. To enforce a global limit you have three shapes:

- **Centralized counter (Redis `INCR` with TTL).** One round trip per request; accurate, simple, and the counter for a hot key becomes the system's bottleneck. Mitigate by sharding the key (`key:0`..`key:N`, sum at check) or pre-allocating quota chunks per instance.
- **Per-instance with periodic sync.** Each gateway tracks a local share and reconciles every few hundred milliseconds. Lower latency, resilient to a Redis blip; you over-shoot during the sync gap.
- **Probabilistic / sampled.** Each instance admits with a probability calibrated against the perceived global rate. Cheap, lossy at the edges, fine when "approximately fair" is the bar.

## 3. When to use

- **Public API protection from abuse and free-tier overuse** — the canonical case. One scraper should not consume capacity you owe paying customers.
- **Per-tenant fairness in multi-tenant systems.** A noisy tenant cannot saturate a shared resource if every tenant has its own bucket.
- [**Backpressure**](backpressure-load-shedding.md) **source for downstream protection.** When a downstream has a hard capacity (third-party API, single-writer database, ML inference cluster), the rate limiter is what keeps you under that ceiling.
- **Cost control.** Third-party APIs you pay per call, LLM token budgets, expensive external lookups — rate limiting is the budget enforcement point.

**Anti-signal:** internal RPC between trusted services that scale together. Limiting your own services from each other usually means the wrong circuit in the wrong place — what you want is concurrency limits and a circuit breaker, not a quota. Rate limiting is for *adversarial or unbounded* sources.

## 4. Trade-offs and failure modes

- **Algorithm choice is a behaviour choice.** Token bucket allows bursts — right for human-driven UIs and bursty batch jobs. Leaky bucket smooths to constant rate — right for a downstream that hates spikes. Fixed window is cheap but the boundary burst gets exploited; sliding window counter is the safe default.
- **The distributed counter is a hot key.** A single Redis key for "global API limit" saturates one shard while the rest sit idle. Shard the counter, sum at decision time, or move to per-instance quotas with sync. Treat the counter as a workload, not configuration.
- **Clock skew across gateway instances.** If two instances disagree on "now" by 200 ms and you use a 1-second sliding window, decisions diverge. Sliding-log mitigates because every event has its own timestamp; counter-based schemes need NTP and a slightly larger window than the user thinks.
- **Per-key memory explosion.** Per-user limits across millions of users blow up Redis memory. At huge scale, trade exactness for fixed memory: count-min sketch for approximate counts, approximate top-K for the heaviest hitters.
- **Failure mode for the limiter itself: fail open or fail closed?** Redis is unreachable; do you let traffic through (risk overload) or block all of it (become the outage)? For abuse protection where the worst case is "extra traffic for ten minutes," fail open. For billing-critical quotas where the worst case is "we serve work the customer hasn't paid for," fail closed. **Pick deliberately and document it** — the limiter's failure mode is the platform's failure mode.
- **Burst-after-throttle.** All clients hit the limit, back off the same amount, retry at once at the next window boundary. Require jittered retries — `Retry-After` plus client-side jitter — or the limit becomes a metronome.
- **A rate limiter does not stop a single greedy consumer.** One client opening 10,000 concurrent connections each at 1 RPS is under any per-connection limit and still kills you. Pair rate limiting with **concurrency limits** per key — limiter governs flow over time, concurrency limit governs in-flight.

## 5. Real-world and interviewer probes

**In the wild.** Stripe uses a token bucket per account, separate buckets for reads vs. writes. Cloudflare's rate-limiting product is sliding window under the hood. AWS API Gateway uses token buckets at account and per-method scope. GitHub's "secondary rate limits" exist because the primary per-hour quota was too coarse for the abuse patterns they cared about. Envoy ships both a **local** rate limit filter (per-instance, no central state, fast) and a **global** filter (external service, accurate, slower) — most deployments use both: local as a cheap first line, global where accuracy matters.

**Probes.**

- *"Token bucket vs. leaky bucket?"* — Token bucket allows bursts up to bucket size, then settles to the refill rate. Leaky bucket smooths everything to a constant output rate. Pick token bucket when the caller is a human or a well-behaved client whose bursts you want to honour; pick leaky bucket when the *downstream* cannot tolerate spikes.
- *"Distributed across 100 gateway instances?"* — Two practical options. Centralized Redis with the counter sharded across N keys, summed at check time — accurate, hot-key headache to solve. Or per-instance quotas with periodic sync — lower latency, mild over-shoot during the sync interval. "Exactly N per second globally" usually isn't the real requirement.
- *"Fixed vs. sliding window?"* — Fixed is one counter per `(key, window)`, dirt cheap and atomic, but a client can deliver `2 × limit` across the boundary by timing the seam. Sliding window counter weights previous and current window's counts; same storage cost, no boundary burst, slightly approximate. Sliding-log is exact but storage scales with rate.
- *"The limiter is down — fail open or closed?"* — Depends on what the limiter protects. For a public API guarded against abuse, fail open: serving extra traffic for a few minutes is recoverable, becoming a self-inflicted outage isn't. For billing-critical quotas or protection of a downstream that physically cannot survive overload, fail closed. Make the choice deliberately, write it on the runbook, rehearse it — don't discover it during the incident.
- *"Per-key memory at huge scale?"* — Tracking millions of distinct keys, exact counters cost too much. Switch to probabilistic structures: count-min sketch for "how many requests has this key sent recently" with bounded over-counting, approximate top-K for the heaviest hitters. The keys that matter (the abusers) still surface.
