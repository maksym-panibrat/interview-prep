# Backpressure and load shedding

## 1. TL;DR

**Backpressure** is the upstream signal that a slow consumer cannot keep up — producers are told (or forced) to slow down. **Load shedding** is what you do when you cannot slow the producer down: drop work deliberately, on your terms, before the system collapses on its own. They are complementary, not redundant — backpressure where the producer can be paced, shedding where it cannot. Headline trade-off: **end-to-end fairness vs. localized survival** — backpressure preserves work but propagates the slowdown; shedding preserves the surviving service but throws work away.

## 2. How it works

Every queue between a producer and a consumer hides a rate mismatch *temporarily*. If the rates stay mismatched, latency and memory both blow up. You need either a feedback signal (backpressure) or a deliberate drop policy (load shedding), and ideally both.

### Backpressure mechanisms

- **Bounded queues.** Fixed capacity blocks the producer when full (`BlockingQueue.put`, Go channel with capacity). The block *is* the backpressure signal.
- **Reactive streams `request(n)`.** Consumer asks for `n` items; producer never sends more. Buffer size is implicit in outstanding credit (RxJava, Reactor, Akka Streams).
- **TCP receive window.** Receiver advertises bytes it can accept; window hits zero, sender stops. An HTTP client that stalls reading eventually blocks the server's `write()`.
- **gRPC and HTTP/2 stream flow control.** Per-stream window updates layered on TCP, so one slow stream doesn't stall the connection.

Same pattern every time: **bounded buffer + a way to tell upstream "I'm full"**.

### Load shedding

When you cannot push back — public APIs, multi-tenant platforms, anything where the producer is "the internet" — you drop.

- **Admission control at the ingress.** Decide on arrival, before allocating expensive resources. A `503` returned after auth, body parse, and worker queue has burned the capacity you were trying to save. Pair with a [rate limiter](rate-limiting.md) that caps per-tenant flow before any of this runs.
- **Priority-aware shedding.** Tag requests by priority (paying vs. free, interactive vs. batch, retry vs. fresh) and drop low priority first. Without priority, shedding is a tax on every customer equally — including the ones whose SLOs you're paid to keep.
- **Adaptive shedding.** Don't shed at a static threshold; probe. Lower the admission rate when latency rises, raise it when latency recovers — same control loop as TCP congestion control.

### Concurrency limits beat fixed thread pools

A fixed thread pool sized for "normal" load either oversizes (waste) or undersizes (queueing under burst). **Netflix's `concurrency-limits` auto-tunes the in-flight cap from observed latency.** Each window it samples actual RTT and compares against the minimum RTT ever seen on this endpoint — the floor representing zero queueing. **Vegas treats `RTT - RTT_min` as queueing delay**: if `RTT > RTT_min × tolerance` (default ~2×), the cap shrinks multiplicatively; if RTT is at the floor with the cap saturated, it grows by one. **Gradient2** is the same idea with a smoothed gradient between long-window and short-window RTT. Plain **AIMD** (additive-increase, multiplicative-decrease — TCP Reno's congestion control, Van Jacobson 1988) is also available but reacts only after timeouts or rejections, missing the early queue-build signal Vegas catches at the latency knee. The cap converges on actual capacity rather than your guess from six months ago — and it tracks capacity changes (a slow downstream, a noisy neighbour) without redeploys.

```
in_flight_limit
   ^
   |              /\
   |       /\    /  \      /\
   |      /  \  /    \    /  \
   |  ___/    \/      \__/    \___    <- AIMD: ramp up, halve on degradation
   |
   +----------------------------------> time
```

### Queue depth as a signal

Watch **queue length** and **age-of-oldest-message**, not just throughput. Latency goes nonlinear *before* throughput drops — the queue fills, items wait longer, p99 explodes — but you're still meeting throughput SLO right up to the cliff. Queue depth is the leading indicator.

```
throughput
   ^
   |              ___________
   |             /           \       throughput sits at
   |  __________/             \____  service capacity...
   |
   +----------------------------------> offered load
                  ^
                  | p99 latency already off the chart here:
                  | every additional request waits behind the queue,
                  | but the server is still completing requests at the rate it can.
```

## 3. When to use

- **Any system with a queue between producer and consumer** — which is most real systems. Kafka topics, SQS, in-process channels, thread-pool work queues, even a TCP socket buffer.
- **Any service with non-uniform downstream latency.** When one slow dependency can starve a shared thread pool, you need either a bulkhead or backpressure-plus-shedding (deliberate drop instead of accidental queue-up).
- **Public APIs with paying-customer SLOs under burst load.** Free-tier traffic should shed first; the platform should degrade along the priority axis you defined, not randomly along the axis the OS chose.

**Anti-signal:** synchronous request/response with a hard SLA. There the right answer is fast failure — tight timeout plus circuit breaker, the [resilience four-pack](resilience-four-pack.md) — not a queue you can shed from. If the call has 200 ms to complete or it's worthless, queueing for 50 ms and then maybe shedding is theatre.

## 4. Trade-offs and failure modes

- **No backpressure → unbounded queue.** Memory grows until OOM; latency grows until work is stale before the consumer reaches it; recovery requires draining a backlog that may take hours. By the time you notice, the buffered work is already useless.
- **Drop vs. block trade-off.** **Blocking propagates the slowdown; dropping localizes it but loses work.** Block: your worker thread parks on `queue.put()`, its caller's HTTP handler now holds a connection open, *its* upstream's bounded queue starts filling, and the stall walks back toward the edge — fine if every layer can also shed, catastrophic if any layer just queues harder. Drop: the meaning of "lost" depends on the protocol. **Synchronous HTTP**: the client gets a `503` and either retries (pushing the problem to its retry budget) or surfaces the error to a human. **Synchronous RPC** inside a request graph: the caller's parent request fails unless that branch is optional or has a fallback. **Kafka consumer**: you don't drop — you pause the partition (`KafkaConsumer.pause()`) so the broker keeps the [offset](pubsub-semantics.md); the log is the buffer, durable and rewindable. **Async fire-and-forget** (telemetry, impression pings, audit events without legal retention): drop is free. **Rule:** drop only when work is recoverable from a durable source or genuinely losable; block only when every layer above you can backpressure or shed correctly.
- **Priority shedding requires a fairness model.** Naive "drop low priority first" starves low-priority traffic completely under sustained overload. Use weighted fair queueing or a reservation floor so low-priority customers see degraded service, not zero service.
- **Cascading shed: shed 20% at three layers and you've dropped half your legitimate traffic.** `0.8 × 0.8 × 0.8 = 0.512` — survival is 51%, loss is 49% when each layer thought it was being moderate. The math is multiplicative, the signal is local, and every layer thinks the next one is fine. **Shed once, at the edge** (the API gateway, or the first service that owns the priority taxonomy); let downstream layers backpressure rather than re-shed. Concretely: gateway does admission control with per-tenant priority and a global concurrency limit; internal services run bounded queues that block on full and trust the gateway. If an internal service finds itself shedding under normal traffic, the gateway's limit is wrong — fix that, don't add a second admission point.
- **Hidden queues at every layer — your application queue is one of many.** **Kernel:** the listen backlog (`net.core.somaxconn`, `tcp_max_syn_backlog`) holds connections before `accept()`; the per-socket receive buffer holds bytes before `read()`; NIC RX descriptor rings hold frames before the kernel. **Reverse proxy:** NGINX's `worker_connections` and the upstream `keepalive` pool; Envoy's per-cluster connection pool. **Runtime:** the Go scheduler's runqueue, the JVM's `ForkJoinPool` work-stealing deque, Node's event loop and microtask queue, GC safepoint pauses that look like queueing because every in-flight request stalls together. **Library:** an HTTP client's per-host connection pool (a request waiting for a free connection is queued whether you see it or not), a database driver's connection-pool wait queue. The classic symptom: your service-level queue-depth metric reads zero but p99 is 4 seconds because the work is parked in one of the above. **Instrument every queue you depend on, or you're flying blind by definition.**
- **Re-queue loops and livelock.** Server rejects a request in 1 ms; client retries immediately because no `Retry-After` told it otherwise; rejection takes the same TLS handshake, auth, and routing budget as a real request — the server is now spending 100% CPU on rejections and 0% on useful work. **The system is "up" by every health check and getting nothing done.** Defence: return `503` with `Retry-After`, give clients **exponential backoff with jitter** (jitter prevents the synchronised retry storm — every client retrying at exactly 2s is just a slower DDoS), and cap the global retry rate with a token-bucket retry budget. On the consumer side, a Kafka or SQS message that throws, returns to the queue, and is re-delivered immediately is the same livelock — route to a dead-letter queue after N attempts.
- **Shedding the wrong thing.** Dropping cheap work (a health check, a 5-byte ack) while the expensive work (a full report query) sails through. Cost-aware shedding weighs requests by resource consumption, not count.

## 5. Real-world and interviewer probes

**In the wild.** Envoy and Linkerd implement circuit-breaker-style concurrency limits per upstream cluster — in-flight over the cap, new requests fast-fail. Kafka's consumer-side `max.poll.records` is direct backpressure: the consumer pulls only what it can handle, so the broker stays a durable log rather than a queue. AWS Lambda's **reserved concurrency** both guarantees a function its slice of the account-wide concurrency pool and caps it there — isolation in both directions, so the function can't be starved by noisy neighbours and can't starve them either; **provisioned concurrency** pre-warms the pool so admitted requests don't pay cold-start latency. Netflix's `concurrency-limits` is the canonical AIMD reference. Akka Streams and Project Reactor make backpressure the default — you opt out (`onBackpressureDrop`) to get a shed.

**Probes.**

- *"Latency is rising — should you scale up or shed load?"* — Both, but shed first. Scaling takes minutes (instance boot, JVM warm-up, cache fill); shedding takes milliseconds. Shedding protects the in-flight work that's already paid the cost of getting this far; scaling is the medium-term fix shedding buys you time for.
- *"How do you implement priority shedding?"* — Tag every request with a priority class at the edge (customer tier, request kind, retry-vs-original). Maintain a per-class admission limit or weighted fair queue. Under overload, drop the lowest class first but reserve a floor so it's degraded, not extinct. The hard part is getting product to agree on the priority order before the incident.
- *"How do you size a bounded queue?"* — Use Little's Law backwards: `L = λ × W`, so `max queue depth = arrival rate × tolerable wait`. If you serve 1000 rps and your latency SLO leaves 200 ms of slack for queueing, the cap is 200 items, not 10000. A bigger queue defers the problem — you serve stale work and the producer doesn't get the backpressure signal until things are already broken. The queue exists to absorb burstiness on the timescale of the service time, not to hold a backlog.
- *"Why is dropping sometimes better than blocking?"* — Blocking propagates the failure: the producer's thread is stuck, and *its* upstream is now blocked too. The slowdown spreads in O(layers). Dropping localizes it: this request is gone, the producer is free to handle healthy traffic for unrelated callers. Drop when the producer has other useful work; block when the producer can correctly throttle its own source.
