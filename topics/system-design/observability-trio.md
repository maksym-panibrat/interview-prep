# Observability trio

## 1. TL;DR

Production observability is the discipline of running **metrics, logs, and traces** as one practice, not three tools your platform team happened to buy. Metrics tell you *that* something is wrong; traces tell you *where* in the call graph the time or error went; logs tell you *why* a specific request did the wrong thing. The patterns that matter at senior+ level: golden-signal frameworks (RED, USE, the Four Golden Signals), correlation-ID propagation through every hop, structured logging keyed on those IDs, and sampled distributed tracing with exemplars linking metric points back to representative traces. Together they are how you debug a distributed system without ssh'ing into anything.

## 2. How it works

The trio shares one operational invariant: **every event in every signal is correlatable to the originating user request via a propagated ID.** Lose that and you have three disconnected dashboards.

### Metrics — what shape to track

Metrics are aggregates over time. Three frameworks cover almost every case, complementary not competing:

- **RED** (per service/endpoint): **R**ate, **E**rrors, **D**uration. The service from the outside — what callers see.
- **USE** (per resource — CPU, disk, queue, pool): **U**tilization, **S**aturation, **E**rrors. The internal-capacity view.
- **Four Golden Signals** (Google SRE): **latency, traffic, errors, saturation.** A superset of RED with saturation; the canonical answer if an interviewer asks for one framework.

Aggregation rule: **histograms over averages.** An average hides the tail; a histogram lets you compute p50/p95/p99/p99.9 directly. The interesting failure modes (GC pauses, slow downstreams, queue backups) live at p99 and above, invisible in the mean.

### Structured logging

Logs are key/value JSON, not text strings. Indexed in a log store (Elasticsearch, Loki, Splunk), queryable with a real query language, and *correlation-friendly* because every line carries trace ID, span ID, and request-scoped IDs as discrete fields. A JSON line `{"level":"ERROR","svc":"checkout","trace_id":"...","user_id":"u_8231","msg":"payment declined"}` is a row in a table filterable by any field; "ERROR: payment declined for user 8231" is not.

### Correlation IDs

Every request gets a UUID at the edge (load balancer, API gateway, ingress) and is propagated through every downstream call as an HTTP header — historically `X-Request-ID`, today the W3C `traceparent` standard, which encodes trace ID + span ID + sampling flag. Every log line, every metric exemplar, every span carries it, so logs from N services can be joined into the timeline of one user request. The chain is only as strong as its weakest link: any service that drops the header breaks correlation for every downstream hop. Enforce propagation at the framework or service-mesh level (Envoy, Istio, OpenTelemetry SDKs auto-propagate), not in application code where it will be forgotten.

### Distributed tracing

A trace is a tree of **spans**, one per logical operation, linked parent-to-child. The shape shows where time was spent and where errors originated.

```
trace_id=t1
└── POST /orders               2400ms
    ├── inventory.reserve       120ms
    └── payments.charge        2200ms  ← latency lives here
        └── stripe.api.charge 2150ms  ← and here
```

100% tracing is too expensive at any reasonable QPS, so traces are **sampled**:

- **Head-based sampling** decides at the start (at the edge, via `traceparent`'s sampled flag): "trace 1% of requests." Cheap, decentralized, may miss the 0.01% errors that matter.
- **Tail-based sampling** buffers the entire trace and decides at the end: "keep all errors, all traces over p99 latency, plus 1% baseline." Catches what head-based drops, at the cost of buffering and a centralized collector.

**Exemplars** are the bridge from metrics to traces: each histogram bucket stores a few trace IDs that landed in it. Click the p99 bucket, follow the exemplar, land in a representative slow trace. Aggregates surface the *problem*, exemplars route you to the *example*.

### Cardinality discipline

Every label dimension on a metric multiplies stored time-series. A metric labelled `service × endpoint × status × user_id` over a million users has a million series per (service, endpoint, status) combination, and Prometheus collapses under that. **Bound cardinality at instrumentation time:** keep low-card labels (service, endpoint, status, region) on metrics; push high-card identifiers (user ID, request ID, full URL) to logs and trace attributes. Exemplars cover the gap — a histogram bucket can carry a trace ID without exploding the metric.

## 3. When to use

- **Any production system with more than one service.** A monolith can survive on logs and a process dashboard; a distributed system cannot.
- **Anything you will have to debug at 3am.** If you cannot answer "is the system healthy, where is the latency, why did this request fail" from a dashboard, you have not built it yet.
- **Specifically required for** SLO measurement (error budgets from metrics), on-call alerting (pages on SLO burn), capacity planning (USE metrics drive scaling), and post-incident analysis (traces + logs reconstruct the timeline).

Anti-signals: a single-user prototype on your laptop (stdout is fine); a cron job that runs once a day does not need a tracing stack. There is no "production system, but skip observability" — that is the situation where you discover the failure at 3am with no dashboard.

## 4. Trade-offs and failure modes

- **Cardinality explosion.** The classic Prometheus outage: an engineer adds `user_id` as a label, series count goes from 10k to 10M overnight, the TSDB OOMs, alerting goes blind. The cure is structural — exemplars for high-card IDs, keep metrics low-card, lint metric definitions in CI.
- **Sampled traces miss rare paths.** 1% head-based sampling will not catch a 0.01% error rate; you see metric error spikes with no example trace to drill into. Tail-based sampling fixes this at the cost of buffering and a centralized collector. For high-stakes flows (payments, auth) consider 100% trace retention.
- **Log volume cost.** At scale, logging every request body costs more than the application itself. Sample logs too: errors at 100%, sample successes, redact PII before write — and make redaction a framework concern, not a per-call discipline.
- **Correlation ID gaps.** Any service that drops the header breaks the chain. The bug is silent — logs still write, just without the ID — and you discover it during an incident when the trace stops mid-graph. Enforce propagation at the framework / mesh level so application code cannot opt out.
- **Alerting on symptoms vs. causes.** Alert on user-facing symptoms (SLO burn rate, error rate, p99 latency) — stable across refactors, fires when users are actually hurt. Diagnose with traces and logs, *don't alert on them*. Cause alerts ("CPU > 80%", "queue depth > 1000") go stale the moment infrastructure changes and train the on-call to ignore the pager.
- **Vendor lock.** Every stack historically had its own protocol. **OpenTelemetry** is the cure: a vendor-neutral wire format and SDK across all three signals. Instrument once in OTel; swap Datadog for Honeycomb without touching application code.
- **Trace context loss across async boundaries.** A queue → consumer hop drops trace context unless the producer puts `traceparent` into message headers (Kafka headers, SQS attributes) and the consumer reads it back. The single most common place trace trees break in microservices.

## 5. Real-world and interviewer probes

In the wild, the canonical open-source stack is **Prometheus + Grafana** (metrics), **ELK / Loki / Splunk** (logs), and **Jaeger / Zipkin / Tempo** (traces). **Datadog**, **New Relic**, and **Honeycomb** sell the unified version — Honeycomb is built around high-cardinality event-style telemetry rather than pre-aggregated metrics. **OpenTelemetry** is the cross-vendor protocol and SDK suite: instrument once, ship anywhere. The **W3C Trace Context** spec defines `traceparent` / `tracestate` as the propagation standard. Google's **Dapper** paper (2010) is the original distributed-tracing design.

Probes you should expect:

- *"What are the four golden signals?"* — Latency, traffic, errors, saturation. RED is the same idea per-endpoint without saturation; USE is the resource-side view.
- *"Logs vs. metrics vs. traces — when?"* — Metrics for aggregates and alerting (cheap, low cardinality). Logs for arbitrary detail you didn't know you'd need (high cardinality, cheap to write, expensive to query). Traces for "where in the call graph did time go or this fail." Complementary, not substitutable.
- *"Why sample traces?"* — Cost. Storing 100% of traces at high QPS is unaffordable in any backend.
- *"Tail-based vs. head-based sampling?"* — Head-based decides at the edge (cheap, decentralized, may drop the rare error). Tail-based buffers the whole trace and decides at the end (keeps errors and slow traces, costs a centralized collector and buffer memory). Head-based by default; add tail-based for high-stakes services.
- *"How does cardinality blow up Prometheus?"* — Each unique label-value combination is a separate time-series consuming TSDB memory and an index slot. High-card labels (user ID, request ID, full URL) multiply series count without bound. Bound at instrumentation; push high-card to logs and trace attributes; use exemplars for the metric→trace bridge.
- *"Walk me through debugging a latency spike across services."* — SLO burn-rate alert fires. Open the affected service's golden-signal dashboard: which signal moved — latency, errors, saturation? If latency, look at the p99 histogram, click the bad bucket, follow the exemplar to a representative trace. Read the trace tree: which span owns the time? Cross-reference logs by trace ID at that span's service. The flow is "metrics → trace exemplar → trace → logs by trace ID," and it only works if correlation IDs propagated cleanly.
- *"How do you keep trace context across a Kafka hop?"* — Producer copies `traceparent` (and `tracestate`) from the current span context into Kafka message headers; consumer reads them back and continues the trace under the same trace ID with a new parent span. OpenTelemetry's Kafka instrumentation does this automatically. Skip it and every async boundary becomes a wall in the trace tree.
