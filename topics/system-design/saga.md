# Saga

## 1. TL;DR

A **saga** is a long-running business transaction split into a sequence of local steps across multiple services, where every forward step has a **compensating action** that semantically undoes it if a later step fails. It is the answer to "I need an atomic transaction across services" once you accept that two-phase commit (XA) across heterogeneous services is too expensive — which is almost always. You trade isolation for liveness: in-flight saga state is visible to readers, but the system stays available and partial failures resolve through compensation rather than locking the world.

## 2. How it works

Worked example throughout: an e-commerce order — **reserve inventory → charge card → ship → notify**. Four services, four local transactions, no shared database, no XA.

### Steps and compensations

Each forward step is a local transaction in one service's database. Each step defines a **compensating action** that undoes its effect *semantically* — not by rolling back the original txn, which already committed:

```
forward              compensation
ReserveInventory <-> ReleaseInventory
ChargeCard       <-> RefundCard
ShipPackage      <-> CancelShipment
SendNotification <-> (none — irreversible)
```

Compensations are new business operations, not DB rollbacks: a refund is a separate ledger entry, not an UNDO of the charge. The saga maintains the invariant "every executed forward step is either still committed or has been compensated" — eventually.

### Choreography

Services react to each other's events; no central coordinator. Order emits `OrderPlaced`, inventory emits `InventoryReserved`, payments emits `CardCharged`, shipping ships. On failure a service emits a `*Failed` event and upstream services listen for it to trigger their compensations.

```
OrderSvc --OrderPlaced--> InventorySvc --InventoryReserved--> PaymentSvc --CardCharged--> ShippingSvc
                                                                  |
                                                                  +--ChargeFailed--> InventorySvc (compensate)
```

Decoupled and simple per service, but the saga as a whole is **invisible** — no single place describes the workflow, and adding a step means changing event topologies in multiple services.

### Orchestration

A dedicated **saga orchestrator** holds the workflow state and explicitly issues commands; services become step executors that handle commands and reply with success or failure.

```
            +-------------------+
            | OrderOrchestrator |
            +-------------------+
              |   ^   |   ^   |
              v   |   v   |   v
            Inventory  Payments  Shipping
```

The orchestrator owns the state machine ("reserved → charged → shipped → notified") and on failure walks the compensation list backwards. Centralized, easier to debug, easier to change. Pays for itself the moment a workflow has more than three or four steps or a non-trivial branch.

### Semantic locks

No real locks across services. Services mark resources as **pending** until the saga commits or compensates: inventory is `RESERVED` (not `SOLD`), the card hold is `AUTHORIZED` (not `CAPTURED`). Other reads see those states and decide what to treat as available. This is the read-side cost of giving up isolation — see §4.

### Idempotent steps and compensations

Every step and every compensation gets retried (network, restart, redelivery). Both must be **idempotent** — same `(saga_id, step)` produces the same effect on the second attempt as on the first. Dedup on the step key, store the result, return it on replay.

### Persistence

Orchestrator state must be durable. Crash mid-saga without persisted state and you cannot resume what you cannot remember — a half-charged, unshipped order with no refund sitting silently is the failure mode. Persist on every state transition, resume from the last persisted state on restart. Temporal makes this implicit (every workflow step is a durable checkpoint); hand-rolled orchestrators do it explicitly.

## 3. When to use

- **Multi-service business transactions** with eventual consistency: order placement, signup with provisioning, multi-account money movement, content publishing pipelines.
- **Replacing 2PC across heterogeneous services.** XA across a SQL database, a SaaS billing API, and a third-party shipping provider is not a real option; a saga is.
- **Workflows with human-in-the-loop steps.** Approvals, manual review, KYC checks. The workflow may pause for hours or days; real locks for that duration would kill the system. Sagas pause cheaply because they hold no locks.
- **Workflows with naturally compensating actions** in the domain — refunds, cancellations, releases.

Anti-signals:

- **Single-database transactions.** Use ACID. A saga inside one DB is theatre with worse semantics.
- **Workflows where partial states must never be observed.** A saga *will* expose intermediate state to readers. If that is unsafe — instantaneous all-or-nothing settlement — sagas are wrong; you need an ACID boundary.
- **Tight latency budgets** with synchronous request/response. Sagas are asynchronous by nature.

## 4. Trade-offs and failure modes

- **No isolation.** Other reads see in-flight saga state — inventory shows `RESERVED` items as unavailable even though the saga may compensate and release them. Designs need semantic locks or compensating reads. ACID's "I" is the property you give up, and it is real money on the table.
- **Compensations may not be possible.** "Send email" cannot be unsent; a webhook fired to a third party cannot be retracted. The cure is structural: **design steps so the irreversible one is last**, after every step that could fail. Notification is last in the order example for exactly this reason.
- **Compensation chains can fail.** A `RefundCard` the processor rejects leaves the saga half-compensated. Compensations must be idempotent, retried with backoff, and escalated to a human queue when retries exhaust — a refund the bank refuses is a person's problem.
- **Choreography has no central state.** "Where did this saga get stuck?" becomes a distributed-tracing problem across N services. Orchestration trades coupling for one place to look.
- **Orchestrator is a SPOF if not HA.** Replicate it and persist state, or a single instance crashing mid-saga loses the workflow.
- **Step delivery is a delivery-atomicity problem.** The orchestrator must publish "do step N" reliably even if it crashes mid-publish — the dual-write problem. The answer is the transactional outbox: persist the state transition and outbound command in one DB transaction, ship via CDC or a relay, dedup on `(saga_id, step)` at the handler.
- **2PC is a smell, not an alternative.** XA holds resource locks for the saga's duration (potentially hours), doesn't survive participant failure cleanly (in-doubt transactions strand DB locks for operators), throughput collapses, and third-party APIs don't speak XA anyway. Sagas trade isolation for liveness — the right trade in essentially every microservices context.
- **Timeouts.** Every step needs a timeout and defined timeout behavior (usually "treat as failure, compensate"); without it a stuck step hangs the saga forever.
- **Versioning long-running sagas.** A three-day saga may outlive a deploy that changes its step set. Either version sagas (V1 sagas finish on V1 code) or keep step changes backward compatible. Temporal makes this explicit; hand-rolled orchestrators discover it the hard way.

## 5. Real-world and interviewer probes

In the wild, **AWS Step Functions** is the dominant managed orchestration service on AWS, with compensation via `Catch` blocks. **Temporal** (and its predecessor **Cadence**, originally built at Uber and powering most of Uber's workflows) is the heavyweight durable orchestration engine: workflows are code, every step is a durable checkpoint, the runtime survives process failures transparently. **Netflix Conductor** and **Camunda** (BPMN) cover the same ground. Lighter-weight: a service-owned orchestrator on a database state table plus the outbox for command publication. Choreography-only sagas are common in smaller event-driven systems on Kafka.

Probes you should expect:

- *"Choreography or orchestration?"* — Orchestration unless the system is small and decoupling is paramount. Orchestration scales with workflow complexity; choreography turns "what does this saga do?" into archaeology across event logs.
- *"How do you handle a compensation that itself fails?"* — Idempotent, retried with backoff, escalated to an operator queue when retries exhaust. Some compensations (refund the processor refuses, shipment the carrier lost) genuinely require humans.
- *"Why is 2PC usually wrong here?"* — XA holds locks for the saga's duration, doesn't survive participant failure cleanly (in-doubt transactions strand resources), and third-party APIs don't speak XA anyway. Throughput collapses, availability craters.
- *"How do you guarantee the orchestrator's commands get delivered?"* — Outbox plus CDC for command messages, idempotent step handlers keyed on `(saga_id, step)`. State transition and outbound command commit together; the relay ships at-least-once; the handler dedups.
- *"What about isolation?"* — You don't get it. Mitigate with semantic locks, commutative operations, and compensating reads where it matters. If real isolation is non-negotiable, a saga is the wrong pattern.
- *"How do you order compensations under concurrent failures?"* — Reverse order of forward steps that *actually committed*. The orchestrator tracks executed steps (not planned ones) and walks that list backwards.
- *"How do you stop a saga from running forever?"* — Per-step timeouts plus a saga-level deadline, with defined timeout behavior per step. Without it, stuck steps fill the state table with zombies.
