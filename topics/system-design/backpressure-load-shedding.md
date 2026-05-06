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

- **Admission control at the ingress.** Decide on arrival, before allocating expensive resources. A `503` returned after auth, body parse, and worker queue has burned the capacity you were trying to save.
- **Priority-aware shedding.** Tag requests by priority (paying vs. free, interactive vs. batch, retry vs. fresh) and drop low priority first. Without priority, shedding is a tax on every customer equally — including the ones whose SLOs you're paid to keep.
- **Adaptive shedding.** Don't shed at a static threshold; probe. Lower the admission rate when latency rises, raise it when latency recovers — same control loop as TCP congestion control.

### Concurrency limits beat fixed thread pools

A fixed thread pool sized for "normal" load either oversizes (waste) or undersizes (queueing under burst). Netflix's `concurrency-limits` uses an **AIMD** (additive-increase, multiplicative-decrease) controller — like TCP — to auto-tune the in-flight cap: increase while latency is healthy, slash on degradation. The cap converges on actual capacity rather than your guess from six months ago.

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
arrival rate
   ^
   |              ___________
   |             /           \      throughput
   |  __________/             \____ stays flat...
   |
   +----------------------------------> time
                  ^
                  | latency p99 already off the chart here
```

## 3. When to use

- **Any system with a queue between producer and consumer** — which is most real systems. Kafka topics, SQS, in-process channels, thread-pool work queues, even a TCP socket buffer.
- **Any service with non-uniform downstream latency.** When one slow dependency can starve a shared thread pool, you need either a bulkhead or backpressure-plus-shedding (deliberate drop instead of accidental queue-up).
- **Public APIs with paying-customer SLOs under burst load.** Free-tier traffic should shed first; the platform should degrade along the priority axis you defined, not randomly along the axis the OS chose.

**Anti-signal:** synchronous request/response with a hard SLA. There the right answer is fast failure — tight timeout plus circuit breaker — not a queue you can shed from. If the call has 200 ms to complete or it's worthless, queueing for 50 ms and then maybe shedding is theatre.

## 4. Trade-offs and failure modes

- **No backpressure → unbounded queue.** Memory grows until OOM; latency grows until work is stale before the consumer reaches it; recovery requires draining a backlog that may take hours. By the time you notice, the buffered work is already useless.
- **Drop vs. block trade-off.** Blocking pushes the problem upstream — fine if the upstream can also shed, catastrophic if it just queues harder. Dropping localizes the problem but only works if the dropped work is **recoverable** (idempotent retry, durable source like Kafka with consumer offsets) or genuinely losable (telemetry samples, impression pings).
- **Priority shedding requires a fairness model.** Naive "drop low priority first" starves low-priority traffic completely under sustained overload. Use weighted fair queueing or a reservation floor so low-priority customers see degraded service, not zero service.
- **Cascading shed.** If every layer sheds 20% independently, you drop roughly 49% end-to-end when the signal warranted 20%. **Shed at the edge** and let downstream layers backpressure rather than re-shed.
- **Hidden queues at every layer.** OS socket buffers, NIC ring buffers, NGINX worker queues, library-internal channels, the kernel's runqueue. Each adds latency invisibly and breaks the assumption that "my service queue is empty, so we're healthy." The classic symptom: queue-depth metric is zero but p99 is 4 seconds — the work is queued somewhere else.
- **Re-queue loops and livelock.** Reject a request, the client retries immediately, you reject again. CPU goes to 100% serving rejections; useful work goes to zero. Pair shedding with caller-side backoff and a `Retry-After` header. On the consumer side, a poison message that fails and returns to the queue is the same livelock.
- **Shedding the wrong thing.** Dropping cheap work (a health check, a 5-byte ack) while the expensive work (a full report query) sails through. Cost-aware shedding weighs requests by resource consumption, not count.

## 5. Real-world and interviewer probes

**In the wild.** Envoy and Linkerd implement circuit-breaker-style concurrency limits per upstream cluster — in-flight over the cap, new requests fast-fail. Kafka's consumer-side `max.poll.records` is direct backpressure: the consumer pulls only what it can handle, so the broker stays a durable log rather than a queue. AWS Lambda's reserved concurrency is admission control — beyond the reservation, the platform sheds with throttle errors so other functions aren't starved; provisioned concurrency warms the pool so admitted requests don't pay cold-start. Netflix's `concurrency-limits` is the canonical AIMD reference. Akka Streams and Project Reactor make backpressure the default — you opt out (`onBackpressureDrop`) to get a shed.

**Probes.**

- *"Latency is rising — should you scale up or shed load?"* — Both, but shed first. Scaling takes minutes (instance boot, JVM warm-up, cache fill); shedding takes milliseconds. Shedding protects the in-flight work that's already paid the cost of getting this far; scaling is the medium-term fix shedding buys you time for.
- *"How do you implement priority shedding?"* — Tag every request with a priority class at the edge (customer tier, request kind, retry-vs-original). Maintain a per-class admission limit or weighted fair queue. Under overload, drop the lowest class first but reserve a floor so it's degraded, not extinct. The hard part is getting product to agree on the priority order before the incident.
- *"How do you size a bounded queue?"* — Small enough that worst-case wait (queue length × per-item service time) is below your SLO. A bigger queue just defers the problem — you serve stale work and the producer doesn't get the backpressure signal until things are already broken. Heuristic: queue depth ≤ a few seconds of work.
- *"Why is dropping sometimes better than blocking?"* — Blocking propagates the failure: the producer's thread is stuck, and *its* upstream is now blocked too. The slowdown spreads in O(layers). Dropping localizes it: this request is gone, the producer is free to handle healthy traffic for unrelated callers. Drop when the producer has other useful work; block when the producer can correctly throttle its own source.
