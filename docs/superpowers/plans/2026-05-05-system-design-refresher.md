# System Design Refresher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a senior-level system-design refresher (new `topics/system-design/` category) to the existing interview-prep repo, with verifier support, README integration, and cross-linked topic content.

**Architecture:** Mirror the existing `topics/<category>/<topic>.md` convention with a new `topics/system-design/` directory. Add a second schema (5-section refresher template) to `scripts/verify.py`, dispatched by directory. Each topic is a self-contained ~800–1500-word reference; cross-links between topics are added in a final integration pass after all files exist (otherwise the verifier rejects forward refs).

**Tech Stack:** Plain markdown, Python 3 (verifier + tests). Python interpreter is `.venv/bin/python` — `python` is NOT on PATH on this machine.

**Spec:** `docs/superpowers/specs/2026-05-05-system-design-refresher-design.md` (commit `3a54202`).

---

## File Structure

**Create:**
- `topics/system-design/_TEMPLATE.md` — 5-section template (skipped by verifier per existing `_`-prefix rule)
- `topics/system-design/resilience-four-pack.md`
- `topics/system-design/idempotency.md`
- `topics/system-design/backpressure-load-shedding.md`
- `topics/system-design/outbox-cdc.md`
- `topics/system-design/saga.md`
- `topics/system-design/caching.md`
- `topics/system-design/cqrs-read-models.md`
- `topics/system-design/sharding.md`
- `topics/system-design/consistent-hashing.md`
- `topics/system-design/replication.md`
- `topics/system-design/quorum-consistency.md`
- `topics/system-design/leader-election-consensus.md`
- `topics/system-design/distributed-locks.md`
- `topics/system-design/rate-limiting.md`
- `topics/system-design/pubsub-semantics.md`
- `topics/system-design/bloom-hll.md`
- `topics/system-design/schema-evolution.md`
- `topics/system-design/strangler-fig.md`
- `topics/system-design/observability-trio.md`

**Modify:**
- `scripts/verify.py` — add per-directory schema dispatch
- `scripts/test_verify.py` — add tests for new dispatch behavior
- `README.md` — add **System Design** section listing topics grouped by problem-solved

---

## Conventions for All Topic-Writing Tasks

- **Voice:** Same as existing topic files — second-person where natural, no marketing tone, no emoji.
- **Length:** ~800–1500 words. Refresher density, not textbook density.
- **Code blocks:** Use plain ` ``` ` (untagged) for pseudocode/config snippets so the verifier doesn't try to parse them as Python. Avoid language-tagged blocks unless you intend valid Python.
- **Diagrams:** ASCII preferred. Mermaid acceptable when ASCII becomes unreadable. No image files.
- **Cross-links to other system-design topics:** **DO NOT add** during initial topic writing. They will be added in a single integration pass after all topics exist. Mention related topics in plain prose ("see also: replication") without making them markdown links. Cross-links to existing algorithm topics (`topics/<other-cat>/...`) are fine if natural.
- **No trailing summary.** End on the last useful section.
- **Section headings:** Use the exact form `## 1. TL;DR`, `## 2. How it works`, `## 3. When to use`, `## 4. Trade-offs and failure modes`, `## 5. Real-world and interviewer probes` so the verifier matches them.

---

## Task 1: Add tests for verifier per-directory schema dispatch

**Files:**
- Modify: `scripts/test_verify.py`

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_verify.py`:

```python
SYSTEM_DESIGN_VALID_MD = textwrap.dedent("""\
    # Title
    ## 1. TL;DR
    x
    ## 2. How it works
    x
    ## 3. When to use
    x
    ## 4. Trade-offs and failure modes
    x
    ## 5. Real-world and interviewer probes
    x
    """)


def _run_path(path):
    result = subprocess.run(
        [sys.executable, "scripts/verify.py", str(path)],
        capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1],
    )
    return result


def test_system_design_passes_with_5_sections(tmp_path):
    sd_dir = tmp_path / "topics" / "system-design"
    sd_dir.mkdir(parents=True)
    f = sd_dir / "sample.md"
    f.write_text(SYSTEM_DESIGN_VALID_MD)
    result = _run_path(f)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_system_design_fails_when_section_missing(tmp_path):
    sd_dir = tmp_path / "topics" / "system-design"
    sd_dir.mkdir(parents=True)
    f = sd_dir / "sample.md"
    f.write_text("# Title\n## 1. TL;DR\nx\n")
    result = _run_path(f)
    assert result.returncode != 0
    assert "How it works" in result.stdout


def test_algorithm_schema_fails_for_system_design_sections(tmp_path):
    """A file outside topics/system-design/ must still need 9-section schema."""
    other_dir = tmp_path / "topics" / "graphs"
    other_dir.mkdir(parents=True)
    f = other_dir / "sample.md"
    f.write_text(SYSTEM_DESIGN_VALID_MD)
    result = _run_path(f)
    assert result.returncode != 0
    assert "Intuition" in result.stdout
```

- [ ] **Step 2: Run tests, confirm new ones fail**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python -m pytest scripts/test_verify.py -v`

Expected: existing 4 tests pass; the 3 new tests fail (the verifier doesn't yet dispatch by directory).

- [ ] **Step 3: Commit**

```bash
git add scripts/test_verify.py
git commit -m "test(verify): add failing tests for per-directory schema dispatch"
```

---

## Task 2: Implement per-directory schema dispatch in verify.py

**Files:**
- Modify: `scripts/verify.py`

- [ ] **Step 1: Refactor verify.py to dispatch schemas by directory**

Replace the contents of `scripts/verify.py` with:

```python
#!/usr/bin/env python3
"""Structural linter for topic markdown files.

Two schemas, dispatched by directory:
- topics/system-design/<file>.md → 5-section refresher schema
  (TL;DR / How it works / When to use / Trade-offs and failure modes /
   Real-world and interviewer probes)
- everything else under topics/  → 9-section algorithm schema
  (TL;DR / Intuition / Walkthrough / Implementation / Variants & pitfalls /
   Complexity / Problem set / Related patterns / Interviewer follow-ups)

Both schemas additionally enforce:
- Every ```python code block parses as valid Python 3.
- Every internal markdown link resolves to an existing file.

Usage:
    python scripts/verify.py                       # verify all topic files
    python scripts/verify.py path/to/topic.md ...  # verify specific files
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = ROOT / "topics"

ALGORITHM_SECTIONS = [
    "TL;DR",
    "Intuition",
    "Walkthrough",
    "Implementation",
    "Variants & pitfalls",
    "Complexity",
    "Problem set",
    "Related patterns",
    "Interviewer follow-ups",
]

SYSTEM_DESIGN_SECTIONS = [
    "TL;DR",
    "How it works",
    "When to use",
    "Trade-offs and failure modes",
    "Real-world and interviewer probes",
]

PYTHON_BLOCK_RE = re.compile(r"```python[^\n]*\n(.*?)```", re.DOTALL)
LINK_RE = re.compile(r"(?<!!)\]\(([^)]+)\)")


def schema_for(path: Path) -> list[str]:
    # Dispatch by path component so the function works for both real repo
    # paths (topics/system-design/...) and temporary test paths
    # (tmp_path/topics/system-design/...).
    if "system-design" in path.resolve().parts:
        return SYSTEM_DESIGN_SECTIONS
    return ALGORITHM_SECTIONS


def check_sections(text: str, sections: list[str]) -> list[str]:
    errors = []
    for section in sections:
        pattern = rf"^#{{1,4}}\s+(?:\d+\.\s+)?{re.escape(section)}\s*$"
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"missing section '{section}'")
    return errors


def check_python_blocks(text: str) -> list[str]:
    errors = []
    for i, match in enumerate(PYTHON_BLOCK_RE.finditer(text), start=1):
        code = match.group(1)
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"invalid python in block #{i}: {e.msg} (line {e.lineno})")
    return errors


def check_links(path: Path, text: str) -> list[str]:
    errors = []
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.split("#", 1)[0]
        if not file_part:
            continue
        candidate = (path.parent / file_part).resolve()
        if not candidate.exists():
            errors.append(f"broken internal link '{target}'")
    return errors


def verify_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = []
    errors.extend(check_sections(text, schema_for(path)))
    errors.extend(check_python_blocks(text))
    errors.extend(check_links(path, text))
    return [f"{path}: {e}" for e in errors]


def collect_default_files() -> list[Path]:
    files = []
    for p in TOPICS.rglob("*.md"):
        if p.name.startswith("_"):
            continue
        files.append(p)
    return sorted(files)


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a) for a in argv]
    else:
        files = collect_default_files()
    all_errors = []
    for f in files:
        if not f.exists():
            all_errors.append(f"{f}: file not found")
            continue
        all_errors.extend(verify_file(f))
    if all_errors:
        for e in all_errors:
            print(e)
        return 1
    print(f"OK ({len(files)} file(s) verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

The change vs. the original: replace the single `REQUIRED_SECTIONS` constant with two named lists, add `schema_for(path)` that dispatches on whether `"system-design"` appears in the resolved path components (works equally for real repo paths and test tmp paths), and pass the chosen list into `check_sections`.

- [ ] **Step 2: Run all verifier tests, expect green**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python -m pytest scripts/test_verify.py -v`

Expected: all tests pass (the original 4 plus the 3 added in Task 1).

- [ ] **Step 3: Run the full verifier on the existing repo to confirm no regression**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python scripts/verify.py`

Expected: `OK (N file(s) verified)` where N is whatever the existing topic count is. Zero errors.

- [ ] **Step 4: Commit**

```bash
git add scripts/verify.py
git commit -m "feat(verify): dispatch schema by directory (system-design vs algorithm)"
```

---

## Task 3: Create the system-design `_TEMPLATE.md`

**Files:**
- Create: `topics/system-design/_TEMPLATE.md`

- [ ] **Step 1: Create the directory and template file**

Create `topics/system-design/_TEMPLATE.md` with:

```markdown
# <Topic name>

## 1. TL;DR

<2–4 sentences. State what the pattern/approach is, the operational pain it
solves, and the headline trade-off.>

## 2. How it works

<Mechanics. ASCII or mermaid diagrams where they help. State the invariants
the pattern maintains. For multi-variant patterns (e.g., "rate limiting"),
describe each variant briefly.>

## 3. When to use

<Signals in a design conversation that should make you reach for this. The
shape of problems where it pays off. Anti-signals — situations where it is
the *wrong* answer.>

## 4. Trade-offs and failure modes

<The honest list: what you give up, what breaks under load, what bites in
production. Concrete failure modes (e.g., "cache stampede on TTL expiry",
"split brain after network partition"). What you must operationally handle.>

## 5. Real-world and interviewer probes

- **In the wild:** systems that use this and how (e.g., "DynamoDB uses
  consistent hashing with virtual nodes for partition assignment").
- **Interviewer follow-ups:** the pointed questions you should expect and
  one-or-two-sentence answers that demonstrate depth.
```

- [ ] **Step 2: Confirm the template is skipped by the verifier**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python scripts/verify.py`

Expected: `OK (...)` with the same file count as before — `_TEMPLATE.md` is skipped because of the existing `_`-prefix rule.

- [ ] **Step 3: Commit**

```bash
git add topics/system-design/_TEMPLATE.md
git commit -m "docs(system-design): add 5-section refresher template"
```

---

## Topic-Writing Tasks (Tasks 4–22)

Each topic task follows this **same shape**:

1. Create the file at `topics/system-design/<slug>.md` using the template at `topics/system-design/_TEMPLATE.md`.
2. Write all five sections per the **content brief** in the task. Length target: ~800–1500 words.
3. **No cross-links to other system-design topics** — they are added in Task 23.
4. Run: `.venv/bin/python scripts/verify.py topics/system-design/<slug>.md` — expect `OK`.
5. Commit with message: `docs(system-design): add <topic> refresher`.

The content brief in each task lists what each section must cover. Treat it as the minimum bar — go deeper where it makes the refresher sharper. Do not pad to hit length; cut if you reach the bar in fewer words.

---

## Task 4: Write `resilience-four-pack.md`

**Files:**
- Create: `topics/system-design/resilience-four-pack.md`

**Content brief:**

- **§1 TL;DR.** Four patterns that protect every service-to-service call: timeout, retry-with-jittered-backoff, circuit breaker, bulkhead. They are never deployed alone — each one assumes the others are present. Headline trade-off: latency budget vs. blast-radius containment.
- **§2 How it works.**
  - **Timeout:** every outbound call has a deadline; budget propagation across hops (deadline ≤ caller's remaining budget).
  - **Retry with backoff + jitter:** exponential backoff (base × 2^attempt), full jitter (`sleep = random(0, base × 2^attempt)`) to break thundering-herd waves; bounded attempts; only retry on retryable errors (5xx, network, never 4xx).
  - **Circuit breaker:** states closed → open → half-open. Trip on error-rate or latency threshold within a rolling window; fail fast while open; probe with single request in half-open.
  - **Bulkhead:** isolated resource pools per dependency (thread pools, connection pools, semaphores). One slow dependency cannot exhaust the caller's whole pool.
- **§3 When to use.** Any service-to-service or service-to-datastore call. Anti-signal: pure in-process function calls. Specifically required: any caller that retries (without these you produce a retry storm and DDoS yourself).
- **§4 Trade-offs and failure modes.**
  - Retry without idempotency = duplicate side effects.
  - Retry without circuit breaker = retry storm during partial outage.
  - Circuit breaker without good metrics = wrong threshold, opens during normal load spikes.
  - Bulkhead misconfigured small = head-of-line blocking; misconfigured large = no isolation.
  - Timeouts without deadline propagation = downstream keeps working on a request the caller has already abandoned ("zombie work").
  - The classic failure: `client_timeout < server_timeout` causes server to keep computing after client gives up.
- **§5 Real-world and interviewer probes.**
  - In the wild: Netflix Hystrix popularized the four-pack; modern equivalents are resilience4j, Polly (.NET), gRPC deadlines, Envoy's outlier detection. AWS SDKs default to jittered backoff.
  - Probes:
    - "Why jitter?" → Synchronized retries from many clients DDoS the dependency the moment it recovers; jitter spreads them.
    - "Walk me through circuit breaker states." → closed/open/half-open with thresholds.
    - "What's the danger of retries without idempotency?" → duplicate side effects; lead into idempotency.
    - "How do you pick timeout values?" → percentile latency × small multiple, with deadline propagation respecting caller's remaining budget.

**Steps:**

- [ ] Write the file per the brief, all five sections present, ~1000–1300 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/resilience-four-pack.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/resilience-four-pack.md
  git commit -m "docs(system-design): add resilience four-pack refresher"
  ```

---

## Task 5: Write `idempotency.md`

**Files:**
- Create: `topics/system-design/idempotency.md`

**Content brief:**

- **§1 TL;DR.** An operation is idempotent if executing it N times produces the same effect as executing it once. In a world of retries (network blips, queue redelivery, client refreshes), every state-mutating endpoint needs an idempotency story. The "exactly-once delivery" myth dies here; what you can build is **exactly-once effects**.
- **§2 How it works.**
  - **Idempotency key:** caller-supplied (or derived) unique ID per logical operation; server records `key → result` and returns the stored result on replay.
  - **Storage:** Redis with TTL (cheap, lossy under failover); DB unique constraint (durable, costlier writes); both — write key to DB inside same txn as side effect.
  - **The atomicity problem:** key write and side effect must be atomic. Two-phase ("reserve key → do work → mark complete") with reconciliation if step 2 fails.
  - **Natural idempotency:** UPSERT, set-state-X (vs. increment-by-X), DELETE-by-id. Prefer over key-based when possible.
  - **Dedup window:** how far back you remember keys. Trade storage vs. correctness.
- **§3 When to use.**
  - Any HTTP endpoint behind a load balancer that retries (most LBs do).
  - Any queue consumer (at-least-once delivery is the default).
  - Webhook receivers (sender will retry on non-2xx).
  - Anti-signal: pure read endpoints (already idempotent by definition); operations whose business meaning is "do it again" (e.g., "send a fresh OTP").
- **§4 Trade-offs and failure modes.**
  - Storage cost grows with traffic × dedup window.
  - TTL too short → false dedup misses (legitimate duplicate accepted as new); too long → unbounded storage.
  - Race: two requests with same key arrive concurrently. Need atomic compare-and-set, not check-then-write.
  - Idempotency key collision (UUID overlap, or same caller reusing key for *different* operation): server must define behavior — return original result, or 409.
  - Result storage size: large response bodies blow up the dedup table. Store hash + reference, not full payload.
  - Replay vs. correctness: if downstream fan-out changed since first execution, replaying returns stale result.
- **§5 Real-world and interviewer probes.**
  - In the wild: Stripe's `Idempotency-Key` header (24h dedup window, returns original response). SQS message dedup ID (5-minute window). Kafka producer's `enable.idempotence=true` (sequence numbers per partition).
  - Probes:
    - "What if the same key arrives twice in flight?" → atomic insert (`INSERT ... ON CONFLICT`), second waits or returns conflict.
    - "How long should the dedup window be?" → bounded by realistic retry horizon (caller behavior, network MTUs); typically minutes-to-hours, not days.
    - "Why is 'exactly-once delivery' a myth?" → impossible across an unreliable network; achievable is exactly-once *effects* via dedup + idempotent operations.
    - "Walk me through implementing it for a payment endpoint." → key in unique-constraint table, payment row in same txn, return stored response on retry.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1000–1300 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/idempotency.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/idempotency.md
  git commit -m "docs(system-design): add idempotency refresher"
  ```

---

## Task 6: Write `backpressure-load-shedding.md`

**Files:**
- Create: `topics/system-design/backpressure-load-shedding.md`

**Content brief:**

- **§1 TL;DR.** Backpressure: a slow consumer signals upstream to slow down. Load shedding: when you can't slow down, drop work deliberately rather than collapse. Together they keep a degraded system serving its priority traffic instead of dying.
- **§2 How it works.**
  - **Backpressure mechanisms:** bounded queues (block producer at full), reactive-streams `request(n)` flow control, TCP window, gRPC flow control, HTTP/2 stream windows.
  - **Load shedding:** admission control at ingress (drop on arrival), priority-aware (drop low-priority first), adaptive (probe load, lower admission rate).
  - **Concurrency limits:** AIMD-style controllers (Netflix concurrency-limits) auto-tune in-flight cap to maximum throughput before latency degrades.
  - **Queue depth as signal:** monitor queue length / age-of-oldest-message; latency goes nonlinear before throughput does.
- **§3 When to use.**
  - Any system with a queue between producer and consumer (most real systems).
  - Any service with non-uniform downstream latency (where one slow dep can starve a thread pool).
  - Public APIs where you must protect SLOs for paying customers under burst load.
  - Anti-signal: synchronous request/response with hard SLA — there, prefer fast failure (timeouts + circuit breaker).
- **§4 Trade-offs and failure modes.**
  - **No backpressure → unbounded queue.** Memory blow-up; latency tail grows past usefulness; recovery requires drain.
  - **Drop-vs-block trade-off:** blocking pushes the problem upstream (good if upstream can shed); dropping requires the dropped work to be recoverable.
  - **Priority shedding requires a fairness model.** Without one, low-priority traffic gets fully starved during sustained overload.
  - **Cascading shed:** if every layer sheds independently, you can drop more than necessary. Coordinate or shed at the edge.
  - **Hidden queues:** OS socket buffers, NIC ring buffers, library-internal queues — these all add latency invisibly.
  - **Re-queue loops:** rejected work that retries immediately = livelock. Pair shedding with caller-side backoff.
- **§5 Real-world and interviewer probes.**
  - In the wild: Envoy/Linkerd circuit breakers with concurrency limits; Kafka consumer-side `max.poll.records`; AWS Lambda's reserved concurrency + provisioned concurrency; Netflix's concurrency-limits library; Akka/Reactor backpressure-aware streams.
  - Probes:
    - "Latency is rising — should you scale up or shed load?" → both, but shed first to protect what's already in flight; scaling is rarely fast enough.
    - "How do you implement priority shedding?" → tag each request with priority; drop highest-priority-bucket-with-spare-capacity-first inversion.
    - "How do you size a bounded queue?" → small enough that worst-case wait is below your SLO; bigger queues just defer the problem.
    - "Why is dropping better than blocking sometimes?" → blocking propagates the failure upstream; dropping localizes it and gives capacity back to other traffic.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1000–1300 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/backpressure-load-shedding.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/backpressure-load-shedding.md
  git commit -m "docs(system-design): add backpressure & load shedding refresher"
  ```

---

## Task 7: Write `outbox-cdc.md`

**Files:**
- Create: `topics/system-design/outbox-cdc.md`

**Content brief:**

- **§1 TL;DR.** The dual-write problem: you need to update your DB and publish an event, atomically. You can't (no distributed transaction). The transactional outbox + CDC pattern moves the publish from "happens at write time" to "derived from the DB log," giving you atomicity for free.
- **§2 How it works.**
  - **Outbox table:** in the same DB as your business data, an `outbox_events` table. Inside the same txn that mutates business state, INSERT the event row. Either both commit or neither.
  - **Relay/poller:** a separate process reads outbox rows and publishes them to the broker. Marks rows as published. At-least-once semantics.
  - **CDC (Change Data Capture):** instead of a custom relay, tail the DB write-ahead log (Debezium reading Postgres WAL / MySQL binlog). Outbox rows become Kafka messages automatically. Decouples publish path entirely from app code.
  - **Topology:** business txn → DB (data + outbox row, atomic) → CDC connector → Kafka → consumers.
  - **Ordering:** WAL is single-writer-ordered per shard; CDC preserves it. Kafka partition key = aggregate ID maintains per-aggregate order downstream.
- **§3 When to use.**
  - Any time you mutate state and need to notify other services reliably.
  - Replacing fragile "DB write then publish (and pray)" code paths.
  - Building event-driven architectures on top of an existing transactional DB.
  - Anti-signal: pure read paths; systems where eventual delivery is unacceptable (use synchronous request/response or sagas with explicit compensation).
- **§4 Trade-offs and failure modes.**
  - **At-least-once, not exactly-once.** Consumers must be idempotent.
  - **Outbox table size:** unbounded if relay falls behind. Background pruning required.
  - **Hot outbox:** every write touches the outbox table. Index carefully; the relay's read query must be cheap.
  - **CDC operational cost:** Debezium adds infra (Kafka Connect, schema registry, replication-slot management). WAL retention must outlive CDC downtime.
  - **Schema coupling:** if you publish raw row changes, all consumers couple to your schema. Prefer publishing semantic events (e.g., `OrderPlaced`) over raw `INSERT INTO orders`.
  - **Replication-slot leak (Postgres):** dead CDC slots block WAL cleanup and fill the disk. Monitor.
  - **Multi-DB transactions:** outbox only works within one DB. Cross-DB still needs sagas.
- **§5 Real-world and interviewer probes.**
  - In the wild: Debezium (CDC for PostgreSQL/MySQL/Mongo) → Kafka Connect; the de facto pattern at companies like Netflix, Uber, Airbnb. Confluent's "outbox event router" SMT.
  - Probes:
    - "Why not just publish to Kafka inside the txn?" → you can't; Kafka isn't part of the DB transaction. Either you publish before the commit (might roll back) or after (might fail post-commit). Outbox makes both atomic.
    - "Why CDC over a polling relay?" → no app code change; lower latency; preserves DB-level ordering; survives app crash.
    - "What about ordering?" → partition key = aggregate ID; per-aggregate ordering is preserved through partition assignment.
    - "How does this differ from a saga?" → outbox is *delivery* atomicity; saga is *business-process* atomicity. Sagas often use outbox for their step messages.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/outbox-cdc.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/outbox-cdc.md
  git commit -m "docs(system-design): add outbox + CDC refresher"
  ```

---

## Task 8: Write `saga.md`

**Files:**
- Create: `topics/system-design/saga.md`

**Content brief:**

- **§1 TL;DR.** A saga is a long-running business transaction split into local steps across multiple services, with compensating actions to undo earlier steps if a later one fails. The answer to "I need an atomic transaction across services" when 2PC is too expensive — which is almost always.
- **§2 How it works.**
  - **Steps + compensations:** every forward step has a compensating action that semantically undoes it (`ReserveInventory` ↔ `ReleaseInventory`, `ChargeCard` ↔ `RefundCard`).
  - **Choreography:** services react to each other's events, no central coordinator. Decoupled but the saga is invisible — emerges from event flow.
  - **Orchestration:** a saga orchestrator service tracks state and explicitly issues commands to participants. Centralized; easier to debug, monitor, change.
  - **Semantic locks:** because there are no real locks, you mark resources as "pending" (e.g., reserved inventory) until the saga commits or compensates.
  - **Idempotent steps:** every step retried; every compensation must be safe to retry too.
  - **Persistence:** orchestrator state must be durable (DB, event log) so the saga can resume after crash.
- **§3 When to use.**
  - Multi-service business transactions where eventual consistency is acceptable.
  - Replacing 2PC across heterogeneous services.
  - Workflows with human-in-the-loop steps (waits hours/days — locks impossible).
  - Anti-signal: single-DB transactions (just use ACID); workflows where partial states are unsafe to ever observe (use real ACID, not a saga).
- **§4 Trade-offs and failure modes.**
  - **No isolation.** Other reads see in-flight saga state; need read-after-saga semantics or compensating reads.
  - **Compensations may not be possible.** "Send email" can't be unsent — design steps so the irreversible one is last.
  - **Compensation chains can fail.** Need compensation retries + escalation to operator.
  - **Choreography has no central state** — debugging "where did this saga get stuck" requires tracing across services.
  - **Orchestrator is a SPOF** if not HA; needs durable state.
  - **2PC alternative is a smell:** XA transactions across services lock resources for the duration of the saga, kill throughput, and break under partial failure. Sagas trade isolation for liveness.
- **§5 Real-world and interviewer probes.**
  - In the wild: AWS Step Functions (orchestration); Temporal / Cadence (durable orchestration); Camunda BPMN; Uber's Cadence powering most of their workflows; Netflix Conductor.
  - Probes:
    - "Choreography or orchestration?" → orchestration unless the system is small and decoupling is paramount; orchestration scales better with workflow complexity.
    - "How do you handle a compensation that itself fails?" → idempotent compensations + retry + alerting; some compensations require human intervention.
    - "Why is 2PC usually wrong here?" → XA blocks resources and doesn't survive participant failure cleanly; throughput collapses.
    - "How do you guarantee step delivery?" → outbox + CDC for the orchestrator's command messages; idempotent step handlers.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/saga.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/saga.md
  git commit -m "docs(system-design): add saga pattern refresher"
  ```

---

## Task 9: Write `caching.md`

**Files:**
- Create: `topics/system-design/caching.md`

**Content brief:**

- **§1 TL;DR.** Caching is moving data closer to the reader to skip expensive work. The strategy decisions (where it lives, who writes it, when it expires) determine whether you get a speedup or a correctness nightmare. Stampede mitigation determines whether the cache helps you survive load spikes or amplifies them.
- **§2 How it works.**
  - **Cache-aside (lazy):** app reads cache; on miss, reads source, writes cache. Simple; cache and source can drift on writes.
  - **Read-through:** cache library fetches from source on miss. App only sees the cache. Cleaner abstraction.
  - **Write-through:** writes go to cache and source synchronously. Consistent at write time; slower writes.
  - **Write-back / write-behind:** writes go to cache, flushed to source asynchronously. Fastest writes; durability and consistency risk on cache failure.
  - **TTL + stampede mitigation:**
    - **Single-flight (request coalescing):** for a popular cold key, allow only one cache fill request, others wait.
    - **Jittered TTL:** randomize expiry per key (`base ± jitter`) to avoid synchronized expirations.
    - **Stale-while-revalidate:** serve stale value while a background refresh runs.
    - **Negative caching:** cache "not found" for short TTL to prevent miss-storms on missing keys.
    - **Probabilistic early refresh:** approaching TTL, randomly refresh ahead of time.
- **§3 When to use.**
  - Read-heavy workloads with low write rate or tolerable staleness.
  - Expensive computations or downstream calls (DB, search, LLM, external API).
  - Front of geo-distant calls (CDN, regional caches).
  - Anti-signal: write-heavy workloads with strong consistency needs (cache becomes a coherence problem); per-user data with no reuse.
- **§4 Trade-offs and failure modes.**
  - **Staleness vs. consistency:** every cached value is potentially stale. Pick TTL by the cost of staleness for your domain.
  - **Cache stampede / dogpile:** popular hot key expires; thousands of concurrent miss requests flatten the source. Mitigate with single-flight, jittered TTL, SWR.
  - **Thundering herd on cache restart:** cold cache after restart = entire load hits source. Pre-warm or roll restart.
  - **Coherence between cache and source:** writes to source bypass the cache; need invalidation, write-through, or TTL.
  - **Negative-cache amplification:** a bug that returns "not found" gets cached, hiding the fix until TTL expires.
  - **Hot keys:** one key getting 80% of traffic — sharded cache rebalances poorly. Pin or replicate hot keys.
  - **Memory pressure → eviction:** LRU/LFU choices matter for hit rate. Track eviction rate as a signal.
- **§5 Real-world and interviewer probes.**
  - In the wild: Memcached / Redis (process-local layer); Varnish (HTTP); Cloudflare/Fastly/CloudFront (CDN); ElastiCache. Facebook's TAO and the "leases" mechanism for stampede control. Netflix EVCache.
  - Probes:
    - "Walk me through cache stampede mitigation." → single-flight + jittered TTL + SWR + (optionally) probabilistic early refresh.
    - "Cache-aside vs. read-through?" → cache-aside is simpler and explicit; read-through hides the cache from app code, easier to swap.
    - "How do you keep cache and source consistent on writes?" → write-through (sync), invalidate-on-write (eventual), or TTL (eventual). Pick based on tolerable staleness.
    - "How do you handle a hot key?" → key splitting (`key#0..key#N`), cache replication, in-process L1 in front of remote L2.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1200–1500 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/caching.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/caching.md
  git commit -m "docs(system-design): add caching strategies + stampede mitigation refresher"
  ```

---

## Task 10: Write `cqrs-read-models.md`

**Files:**
- Create: `topics/system-design/cqrs-read-models.md`

**Content brief:**

- **§1 TL;DR.** CQRS separates the model used for writes (commands) from the model(s) used for reads (queries). Pair it with materialized read models — denormalized projections optimized for specific query shapes. Worth it when read shape diverges sharply from write shape; expensive when it doesn't.
- **§2 How it works.**
  - **Command side:** owns business invariants; writes through a normalized transactional store; emits events.
  - **Query side:** one or more denormalized read stores, each shaped to a query (search index, JSON document, aggregated counters). Built by projecting events.
  - **Projection:** consumer that reads events and updates the read store. Idempotent; replayable.
  - **Replay:** rebuild a read store from scratch by replaying the event log. The killer feature; required for adding new read models or fixing projection bugs.
  - **Event sourcing variant:** store the events themselves as the source of truth; the write model is derived too. Higher cost; only worth it when the audit log is the business.
- **§3 When to use.**
  - Read shape and write shape genuinely diverge — e.g., write as `{order, lineItems, customer}` but read as `{search results}` or `{daily revenue dashboard}`.
  - Multiple read models needed from the same source.
  - High read:write ratio where read scaling needs different storage.
  - Audit / temporal queries (event sourcing).
  - Anti-signal: CRUD with simple read/write parity (CQRS adds cost for nothing). Strong consistency required between write and read (CQRS is async).
- **§4 Trade-offs and failure modes.**
  - **Eventual consistency between write and read.** Reads can lag the write; users see stale state. UX must account for it (optimistic UI, "your change will appear shortly").
  - **Replay cost grows with event count.** Snapshotting helps; cold replay can take hours.
  - **Schema evolution of events is permanent contract.** Old events live forever; consumers must handle every historical version.
  - **Projection bugs require replay.** Cheap if the data is small, painful at scale.
  - **Operational complexity:** more stores, more pipelines, more monitoring surface.
  - **Event sourcing's specific pain:** every business operation must be modeled as an event (no quick `UPDATE`); migrations are events themselves.
- **§5 Real-world and interviewer probes.**
  - In the wild: search indexes (Elasticsearch as a read model over a relational write store) — the most common form of CQRS in the wild even when not called that. Banking ledgers (events as truth). EventStoreDB. Axon Framework.
  - Probes:
    - "When is CQRS a mistake?" → simple CRUD; small teams; when the write/read shapes are essentially the same.
    - "How do you handle eventual consistency in the UI?" → optimistic update, then reconcile; or read-your-writes via session-affinity to the write store.
    - "Why event sourcing on top of CQRS?" → audit, time travel, deriving new projections without re-querying. Costs: every model becomes an event-handling problem.
    - "How do you add a new read model after launch?" → replay the event log into the new projection; switch reads when caught up.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/cqrs-read-models.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/cqrs-read-models.md
  git commit -m "docs(system-design): add CQRS + materialized read models refresher"
  ```

---

## Task 11: Write `sharding.md`

**Files:**
- Create: `topics/system-design/sharding.md`

**Content brief:**

- **§1 TL;DR.** Sharding splits a dataset across N nodes so each holds a fraction. The strategy you pick (range, hash, directory) determines what's cheap, what's painful, and what wakes you up at 3am. Hot partitions and resharding-without-downtime are where most real engineering goes.
- **§2 How it works.**
  - **Range sharding:** key space partitioned into contiguous ranges. Cheap range scans; high risk of hot ranges (alphabetical user IDs, monotonic timestamps).
  - **Hash sharding:** shard = `hash(key) % N` or via consistent-hashing ring. Even distribution; range scans require fan-out.
  - **Directory-based:** explicit `key → shard` lookup table. Maximum flexibility; the lookup table itself becomes a critical dependency.
  - **Resharding:** changing N triggers data movement. With `% N`, almost everything moves; consistent hashing minimizes it.
  - **Hot-partition rescue:** salt the key (`user_id_<random_suffix>`), introduce a secondary shard key, or split the hot shard.
  - **Cross-shard queries:** scatter-gather adds latency proportional to slowest shard; aggregations require coordinator merge; joins across shards are usually denormalized away.
- **§3 When to use.**
  - Data set too large for one node (storage or write throughput).
  - Per-tenant isolation requirements (one tenant per shard or "noisy neighbor" elimination).
  - Geographic data locality (region-affinity sharding).
  - Anti-signal: small data, low write rate (you don't need to shard until you do; premature sharding is technical debt).
- **§4 Trade-offs and failure modes.**
  - **Hot partition:** one shard at 90% util while others at 10%. Re-shard or split.
  - **Cross-shard txn loss:** distributed transactions hard; usually denormalize, use sagas, or design key choice to keep txn within one shard.
  - **Resharding without downtime:** double-write to old + new during migration; cutover; backfill. Complex and slow.
  - **Skew:** the chosen shard key has uneven distribution (huge customer dominates). Choose keys with uniform cardinality.
  - **Secondary indexes:** local-to-shard (cheap, fan-out reads) vs. global (consistency cost).
  - **Multi-tenant noisy neighbor:** one tenant DDoS its shard; isolation requires per-tenant shard or quota.
  - **Operational complexity:** N shards = N replicas, N backups, N upgrades.
- **§5 Real-world and interviewer probes.**
  - In the wild: Vitess (MySQL), Citus (Postgres), MongoDB sharded clusters, Cassandra/DynamoDB (hash-on-partition-key), Spanner (range-sharded with auto-split). Snowflake-style ID generation explicitly designed to spread writes across shards.
  - Probes:
    - "Range vs. hash?" → range for ordered scans, hash for even load.
    - "How do you re-shard without downtime?" → dual-writes + backfill + read-cutover; takes weeks at scale.
    - "Walk me through hot-partition mitigation." → identify (per-shard metrics), short-term fix (split, salt), long-term (key redesign).
    - "How do you handle a query that needs data from multiple shards?" → scatter-gather (cost: tail latency), or denormalize so the query lives within one shard.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/sharding.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/sharding.md
  git commit -m "docs(system-design): add sharding strategies refresher"
  ```

---

## Task 12: Write `consistent-hashing.md`

**Files:**
- Create: `topics/system-design/consistent-hashing.md`

**Content brief:**

- **§1 TL;DR.** A hash-sharding scheme that minimizes data movement when nodes are added or removed: only `K/N` keys move when one node joins or leaves an N-node ring (vs. nearly all keys with `hash % N`). Used everywhere you can't afford a global re-shuffle on capacity changes.
- **§2 How it works.**
  - **The ring:** hash both keys and node identifiers onto a fixed-size ring (e.g., 0..2³²−1). Each key is owned by the next node clockwise.
  - **Add/remove a node:** only keys between the new node and its predecessor move. Mathematically: `≈ 1/N` of keys move when adding to an N-node ring.
  - **Virtual nodes (vnodes):** each physical node owns many ring positions (typically 100–256). Smooths key distribution and limits single-node load when one fails (load spreads across many neighbors instead of doubling on one).
  - **Lookup:** binary-search the sorted ring positions to find owner for a key. O(log N).
  - **Replication:** the next R nodes clockwise own replicas. Combined with quorum semantics, this is the basis of Dynamo-style stores.
- **§3 When to use.**
  - Distributed cache with frequent capacity changes (memcached client routing).
  - Distributed KV store / database where rebalancing must be cheap (Cassandra, DynamoDB partition assignment).
  - Sharded service routing where you want session/affinity stickiness without a directory.
  - Anti-signal: small fixed cluster (just use modulo); when you need range scans (consistent hashing scrambles order).
- **§4 Trade-offs and failure modes.**
  - **Hot keys still hot.** Consistent hashing solves rebalance pain, not skew. Hot key → hot node → cascading.
  - **vnode count tuning:** too few = uneven load and big load jump on failure; too many = lookup memory cost; a few hundred per node is the usual sweet spot.
  - **Bounded loads:** vanilla consistent hashing can have ~2× imbalance at the tail; "consistent hashing with bounded loads" caps load per node.
  - **Replica placement under failure:** must skip nodes already holding a replica when next-clockwise; rack/AZ awareness adds further constraints.
  - **Hash function quality matters.** Poor hash → clusters → uneven ownership.
  - **Coordination cost on membership change:** clients must learn new ring; gossip or coordination service required.
- **§5 Real-world and interviewer probes.**
  - In the wild: Amazon Dynamo (paper) and DynamoDB; Apache Cassandra (with vnodes since 1.2); Memcached client libraries (Ketama); Redis Cluster (slightly different — fixed 16384 slot space, but same goal); Akamai's CDN routing.
  - Probes:
    - "Why virtual nodes?" → smooth load distribution; bounded blast radius on node failure (load spreads across many neighbors, not one).
    - "What fraction of keys move when one node is added?" → `≈ 1/N` (vs. `≈ (N-1)/N` with `hash % N`).
    - "What's the worst-case skew?" → ~2× at the tail without bounded loads; configurable with bounded-load variant.
    - "How do replicas work?" → next R nodes clockwise; combined with R/W quorums for tunable consistency.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1000–1300 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/consistent-hashing.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/consistent-hashing.md
  git commit -m "docs(system-design): add consistent hashing refresher"
  ```

---

## Task 13: Write `replication.md`

**Files:**
- Create: `topics/system-design/replication.md`

**Content brief:**

- **§1 TL;DR.** Replication makes copies of data on multiple nodes for durability, availability, and read scaling. The choice of model (single-leader, multi-leader, leaderless) and timing (sync, async, semi-sync) is the central trade-off between consistency, latency, and availability.
- **§2 How it works.**
  - **Single-leader (primary-replica):** one node accepts writes; others stream the change log. Simple consistency model; leader is the bottleneck and SPOF.
  - **Multi-leader:** multiple nodes accept writes (often per-region). Conflict resolution required (LWW, CRDTs, app-level merge). Improves write availability and locality.
  - **Leaderless (Dynamo-style):** clients write to any node; replication via gossip / hinted handoff; quorum reads/writes. Highly available; weak consistency unless quorums tuned.
  - **Sync replication:** write returns only after replicas ack. Strong durability, higher latency, blocks if a replica is slow.
  - **Async:** fire-and-forget to replicas. Fast writes; window of data loss on leader failure.
  - **Semi-sync:** wait for at least one replica ack. Compromise.
  - **Failover:** detect leader failure → elect new leader → re-route writes. Split-brain risk if old leader returns.
  - **Replication lag:** async replicas behind by milliseconds-to-seconds. Causes read-after-write anomalies if reads go to a replica.
- **§3 When to use.**
  - Durability (lose a node, keep the data).
  - Read scaling (more replicas = more read throughput).
  - Geo-distribution (a replica per region for local low-latency reads).
  - High availability (failover during leader outage).
  - Anti-signal: data that doesn't need durability or scale (don't replicate just because).
- **§4 Trade-offs and failure modes.**
  - **Replication lag:** async replicas serve stale reads. "Read your own writes" requires routing back to the leader or to a session-sticky replica.
  - **Split brain after failover:** two nodes both believe they're leader; both accept conflicting writes. Fence the old leader (STONITH) or use consensus for leader election.
  - **Sync replication and a slow replica:** write latency = slowest replica. One bad node can stall the cluster. Fall back to async if a replica falls too far behind.
  - **Multi-leader conflicts:** two regions update the same row. LWW loses data; CRDTs avoid that but constrain operations; app-level merge is custom code per type.
  - **Replication topology choices:** chain (low fan-in, high latency tail), star (single fan-out point), all-to-all (complex, used in multi-leader).
  - **Backfill cost:** new replica from scratch must transfer entire dataset; throttle to avoid swamping the leader.
- **§5 Real-world and interviewer probes.**
  - In the wild: Postgres (streaming replication, single-leader, sync/async modes); MySQL (binlog replication); Cassandra/DynamoDB (leaderless); CockroachDB / Spanner (Raft-replicated ranges); Kafka (per-partition leader, ISR replication); MongoDB (replica sets, single-leader with elections).
  - Probes:
    - "Sync vs. async vs. semi-sync — when?" → financial / no-data-loss → sync; latency-sensitive → async with replica lag SLO; one-replica-ack semi-sync as compromise.
    - "How do you avoid split brain?" → quorum-based leader election (majority required); fencing tokens; STONITH.
    - "Read-your-writes consistency on a read replica?" → session-sticky to leader for some interval; or check log position before serving.
    - "Multi-leader conflict resolution?" → LWW (data loss), CRDTs (limited operations), app merge (custom). Most teams use LWW and accept the risk; high-stakes systems use CRDTs or single-leader.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1200–1500 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/replication.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/replication.md
  git commit -m "docs(system-design): add replication models refresher"
  ```

---

## Task 14: Write `quorum-consistency.md`

**Files:**
- Create: `topics/system-design/quorum-consistency.md`

**Content brief:**

- **§1 TL;DR.** Quorum-based replication writes to W of N replicas and reads from R of N. As long as `R + W > N`, every read sees at least one replica that observed the latest write. Tuning R, W, and N gives you a knob between consistency, latency, and availability — Dynamo-style "tunable consistency."
- **§2 How it works.**
  - **The math:** N replicas, write to W, read from R. `R + W > N` guarantees overlap → strong consistency. Common knobs:
    - `W=N, R=1` — strong reads, slow writes, write-unavailable on any failure.
    - `W=1, R=N` — fast writes, slow reads.
    - `W=R=quorum=⌈(N+1)/2⌉` — balanced strong.
    - `W=R=1` — weak (eventual) consistency; high availability.
  - **Read repair:** when a read returns divergent values from replicas, reconcile (write the latest value back to lagging replicas).
  - **Hinted handoff:** if a replica is down at write time, a peer holds the write as a "hint" and replays it when the dead node returns. Preserves W during transient failures.
  - **Sloppy quorum:** when the "right" replicas are unreachable, write to any N healthy nodes. Maintains write availability at the cost of consistency guarantees.
  - **Conflict resolution:** if two writes happen concurrently to different replicas, you need a way to merge. LWW (timestamp-based, can lose data), version vectors (track per-actor causality), CRDTs (conflict-free merges by construction).
- **§3 When to use.**
  - Highly available distributed datastores (Dynamo, Cassandra, Riak).
  - Workloads where you can tolerate eventual consistency for some reads but need strong for others (per-request quorum tuning).
  - Multi-region replication with no single leader.
  - Anti-signal: workloads requiring serializable transactions across keys (use a consensus-based store like Spanner / CockroachDB instead).
- **§4 Trade-offs and failure modes.**
  - **`R + W > N` is necessary but not sufficient.** Concurrent writes during the read window can still produce surprises; need version vectors or CRDTs for safety.
  - **LWW silently drops writes.** Two writers updating the same key, the loser's write disappears. Mitigate with vector clocks or CRDTs; don't rely on wall-clock time across nodes.
  - **Sloppy quorum confusion:** apparent quorum success may have been written to "the wrong" nodes; consistency guarantee weakens.
  - **Read repair latency:** every read may trigger writes; can multiply traffic.
  - **Tail latency:** read with R=quorum waits for slowest of R nodes; speculative reads (issue R+1, take fastest R) help.
  - **CAP and PACELC implicit here:** under partition you choose A or C; even without partition, choose latency or consistency.
- **§5 Real-world and interviewer probes.**
  - In the wild: Amazon Dynamo (the paper) and DynamoDB; Cassandra (per-query consistency level: ONE / QUORUM / ALL / LOCAL_QUORUM); Riak; Voldemort.
  - Probes:
    - "Why R + W > N?" → guarantees the read set and write set overlap on at least one replica, so the latest committed write is visible.
    - "Why might you still see stale data with R + W > N?" → concurrent writes; need version vectors. Quorum overlap is necessary not sufficient.
    - "When would you use W=1, R=N?" → write-heavy workload that tolerates stale writes; rare.
    - "What's hinted handoff?" → a healthy node accepts a write destined for a down peer and forwards it later. Preserves write availability without breaking quorum semantics.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/quorum-consistency.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/quorum-consistency.md
  git commit -m "docs(system-design): add quorum & tunable consistency refresher"
  ```

---

## Task 15: Write `leader-election-consensus.md`

**Files:**
- Create: `topics/system-design/leader-election-consensus.md`

**Content brief:**

- **§1 TL;DR.** Consensus protocols (Raft, Paxos, Multi-Paxos, EPaxos) let a cluster agree on a single value despite failures. Leader election is the most common building block: agreeing "who's in charge" so other operations can be serialized through one node. Use them only when you actually need them — they cost latency and operational complexity.
- **§2 How it works.**
  - **Raft (the readable one):** terms, leader election by majority vote, log replication to majority before commit. If you remember one consensus protocol, remember Raft.
  - **Election:** each node has a random election timeout; on timeout, candidate requests votes; majority wins. Term number prevents stale leaders.
  - **Log replication:** leader appends to its log, replicates to followers, commits when majority ack. Followers apply committed entries in order.
  - **Safety: state-machine replication.** Same operations applied in same order = same state on every replica. Linearizable reads (when reads also go through the leader's log).
  - **Quorum size:** majority (`⌊N/2⌋ + 1`). N=3 tolerates 1 failure; N=5 tolerates 2. Even N gains nothing extra over odd N-1.
  - **Paxos / Multi-Paxos:** older, harder to understand, similar guarantees. EPaxos: leaderless, lower latency for low-conflict workloads.
- **§3 When to use.**
  - Leader election when you need a single coordinator (sequencer, lock service, master in primary-replica DB).
  - Strongly consistent metadata (cluster membership, configuration, schema).
  - Replicated state machines (distributed log: Kafka via KRaft, etcd, ZooKeeper).
  - Anti-signal: high-throughput data plane (consensus is `O(majority)` round trips; not for per-request critical path); workloads where eventual consistency is sufficient (use quorum + CRDTs and skip the consensus tax).
- **§4 Trade-offs and failure modes.**
  - **Latency:** every committed op needs a majority round trip. Within-AZ ~ms, cross-region ~tens of ms — adds up.
  - **Availability under partition:** without majority, no progress (CP system). The minority partition is read-only at best.
  - **Throughput cap:** single leader bottlenecks writes. Sharding the keyspace + per-shard Raft groups is the standard scaling move.
  - **Operational complexity:** members must agree on cluster membership; reconfiguration (joint consensus) is its own protocol.
  - **Stale leader reads:** a partitioned-out leader may still believe it's leader. Lease-based reads or read-from-majority required for true linearizability.
  - **Disk fsync on leader:** every committed entry must be durable; fsync latency is the floor.
- **§5 Real-world and interviewer probes.**
  - In the wild: etcd, Consul (Raft); ZooKeeper (Zab, similar to Paxos); Spanner (Paxos per range); CockroachDB (Raft per range); Kafka KRaft (Raft replacing ZooKeeper); HashiCorp Vault.
  - Probes:
    - "Why is the cluster size usually odd?" → tolerates `⌊N/2⌋` failures; an even N gains zero extra fault tolerance over N-1 odd.
    - "How does Raft elect a leader?" → election timeout, vote request, majority. Term numbers prevent split-brain.
    - "Why not put everything behind Raft?" → latency tax; throughput bottleneck on the leader; use it only for things that need agreement.
    - "Linearizable reads with Raft?" → read through the log (slow), or use leader leases (faster, still safe).
    - "Difference between consensus and quorum-based replication?" → consensus picks one ordering of commits; quorum-based replication accepts concurrent writes and reconciles later.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/leader-election-consensus.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/leader-election-consensus.md
  git commit -m "docs(system-design): add leader election & consensus refresher"
  ```

---

## Task 16: Write `distributed-locks.md`

**Files:**
- Create: `topics/system-design/distributed-locks.md`

**Content brief:**

- **§1 TL;DR.** Distributed locks are deceptively dangerous: clients can hold a lock then crash, GC-pause, or partition out, leaving the protected resource exposed to a "ghost" lock holder. The fix is leases (locks expire) plus fencing tokens (monotonically increasing IDs that the resource itself validates). The Redlock algorithm is the famous example of getting this almost-but-not-quite right.
- **§2 How it works.**
  - **Lease, not lock:** lock has a TTL; client must renew before expiry. If client dies, lease expires, lock auto-released.
  - **The TTL trap:** if client holds a lease, GC-pauses for longer than the TTL, and resumes — it now believes it holds the lock, but the system has reissued it to someone else. Both will write.
  - **Fencing tokens:** every successful lock acquisition returns a monotonically increasing token. The protected resource must check the token: any write with a smaller token than the latest seen is rejected. Old/zombie holder cannot do harm.
  - **Coordination service-backed (etcd, ZooKeeper):** strongly consistent, leader-elected store. Lock = a key with a lease + watch for release. Correct by construction; relatively heavy.
  - **Single-Redis-with-TTL:** simplest; loses correctness on Redis failover (master fails before replicating SETNX).
  - **Redlock (multi-Redis):** acquire lock on majority of N independent Redis nodes within bounded time. Argued by Martin Kleppmann to be unsafe under clock drift / GC pauses without fencing tokens; defended by Redis's antirez — the debate is the canonical "distributed locks are hard" lesson.
- **§3 When to use.**
  - Coordinating exclusive access where a strongly-consistent store can validate the fencing token.
  - Leader election (reuse a coordination service like etcd / ZooKeeper).
  - Throttling exclusive jobs (only one cron worker runs the nightly batch).
  - Anti-signal: high-throughput per-row contention (use optimistic concurrency control instead — version checks on update). Anything where the protected resource can't validate fencing tokens (then a "lock" is advisory, not safe).
- **§4 Trade-offs and failure modes.**
  - **GC pauses, clock drift, network partitions:** any of these can make a client think it still holds an expired lease.
  - **Redlock's specific problem:** depends on bounded clock drift across the N Redis nodes; without fencing tokens, a sufficiently long pause invalidates safety.
  - **Without fencing tokens, no distributed lock is safe.** The protected resource MUST be the source of truth.
  - **Lease renewal traffic:** clients ping the lock service constantly. Hot lock = hot service.
  - **Lease length tuning:** too short = renewal storm; too long = slow recovery from crashed client.
  - **False sense of security:** "I added a Redis lock, problem solved" — without fencing tokens, the bug just got rarer, not gone.
- **§5 Real-world and interviewer probes.**
  - In the wild: Chubby (Google), ZooKeeper, etcd, Consul — all coordination services that support correct distributed locking. Redlock as a controversial alternative. AWS DynamoDB's `ConditionExpression` as an optimistic-concurrency primitive used to *avoid* needing distributed locks.
  - Probes:
    - "What's a fencing token and why do you need one?" → monotonic ID returned with the lock; the resource rejects writes with stale tokens. Without it, zombie holders can write.
    - "Why is Redlock controversial?" → relies on bounded clock drift / pause time; without fencing tokens, you cannot prove safety.
    - "Alternative to a distributed lock?" → optimistic concurrency control: version on the row, update with `WHERE version = N`, retry on conflict. No lock needed, much higher throughput.
    - "When would you reach for ZooKeeper / etcd over Redis for locking?" → when correctness matters more than latency. ZooKeeper / etcd are slower but correct; Redis is fast but requires fencing tokens to be safe.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/distributed-locks.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/distributed-locks.md
  git commit -m "docs(system-design): add distributed locks done right refresher"
  ```

---

## Task 17: Write `rate-limiting.md`

**Files:**
- Create: `topics/system-design/rate-limiting.md`

**Content brief:**

- **§1 TL;DR.** Rate limiting caps how much traffic a caller can send in a window. Choice of algorithm (token bucket, leaky bucket, sliding window) determines burst tolerance and storage cost. The hard part is making it work *distributed* across many gateway instances without a central counter becoming the bottleneck.
- **§2 How it works.**
  - **Token bucket:** bucket holds up to `B` tokens, refills at rate `R` per second. Request takes one token; rejected if empty. Bursts up to `B` allowed; sustained rate capped at `R`.
  - **Leaky bucket:** queue with fixed drain rate. Smoother output; no bursts. Same shape as token bucket from the caller's perspective for sustained traffic, different for bursts.
  - **Fixed window counter:** count requests per `(key, time-window)` (e.g., per minute). Cheap; double-burst at window boundary (last second of one + first second of next).
  - **Sliding window log:** store timestamps of each request; count those in the last N seconds. Accurate; storage `O(rate × window)`.
  - **Sliding window counter:** weighted average between current and previous window counters. Cheap and reasonably accurate.
  - **Distributed quota:**
    - **Centralized counter (Redis INCR with TTL):** simple; the counter becomes a hot key.
    - **Per-instance with sync:** each gateway maintains a local share, syncs periodically. Lower latency, slight over-shoot.
    - **Probabilistic / sampled:** each instance allows requests with probability based on perceived global rate. Lossy.
- **§3 When to use.**
  - Public API protection from abuse / abuse of free tier.
  - Per-tenant fairness in multi-tenant systems.
  - Backpressure source for downstream protection.
  - Cost control (third-party API quotas, LLM token budgets).
  - Anti-signal: pure internal RPC between trusted services (use circuit breaker + concurrency limits instead).
- **§4 Trade-offs and failure modes.**
  - **Algorithm choice trade-off:** token bucket allows burst (good for human-shaped traffic); leaky bucket smooths (good for downstream protection); fixed window is cheap but has boundary-burst.
  - **Distributed counter is a hot key:** centralized Redis INCR can saturate; shard the counter or use per-instance sync.
  - **Clock skew across gateway instances:** windows misalign; sliding-log mitigates.
  - **Per-key explosion:** millions of keys (per-user limits) blow up memory; use approximate structures (probabilistic counters, count-min sketch) at huge scale.
  - **Failure mode for the limiter itself:** if Redis is down — fail open (let traffic through, risk overload) or fail closed (block all, become the outage)? Pick deliberately.
  - **Burst-after-throttle:** caller backs off, then all clients release at once. Need jittered retries from callers.
  - **Doesn't help if the source of overload is a single consumer with infinite concurrency.** Combine with concurrency limits.
- **§5 Real-world and interviewer probes.**
  - In the wild: Stripe (token bucket with per-account limits); Cloudflare (sliding window); AWS API Gateway (token bucket); GitHub's secondary rate limits. Envoy's local + global rate-limit filters. Linkerd's outbound rate limits.
  - Probes:
    - "Token bucket vs. leaky bucket?" → token bucket allows bursts (good for users); leaky bucket smooths to constant rate (good for protecting a downstream).
    - "How would you implement this distributed across 100 gateway instances?" → centralized Redis with sharded counters, or per-instance with periodic sync. Trade accuracy for latency.
    - "Fixed vs. sliding window?" → fixed is cheap but has the 2× boundary-burst problem; sliding window counter is the practical compromise.
    - "Limiter is down — fail open or closed?" → depends on what protects what; for billing protection fail closed, for SLA protection fail open. Document the choice.
    - "Per-key memory at huge scale?" → probabilistic structures (count-min sketch, approximate top-K) trade exactness for fixed memory.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/rate-limiting.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/rate-limiting.md
  git commit -m "docs(system-design): add rate limiting refresher"
  ```

---

## Task 18: Write `pubsub-semantics.md`

**Files:**
- Create: `topics/system-design/pubsub-semantics.md`

**Content brief:**

- **§1 TL;DR.** Pub/sub gives you decoupled producers and consumers, but the operational semantics — delivery guarantees, ordering, replay — are where every team gets bitten. "Exactly-once delivery" is a marketing term; what's achievable is at-least-once delivery + idempotent consumers = exactly-once *effects*.
- **§2 How it works.**
  - **Delivery guarantees:**
    - **At-most-once:** ack-on-receive, fire-and-forget. Lossy.
    - **At-least-once:** ack-on-process, redelivery on no-ack. Standard; requires idempotent consumers.
    - **Exactly-once:** unachievable across an unreliable network as a delivery property; achievable as an effect via dedup keys + idempotent operations.
  - **Ordering:** typically per-partition / per-key. Global ordering kills throughput. Partition key determines ordering boundary.
  - **Consumer groups:** N consumers split partitions. Adding consumers = rebalance. One partition = one consumer per group at a time (otherwise ordering breaks).
  - **Offset management:** consumer commits offset after processing. Commit-after-process = at-least-once; commit-before-process = at-most-once.
  - **Dead-letter queues (DLQ):** messages that fail processing N times go to a side queue for manual inspection / replay.
  - **Replay:** re-process from older offset for backfills, projection rebuilds, bug fixes. Requires consumers handle replays without producing duplicates downstream.
- **§3 When to use.**
  - Decoupled service-to-service communication (publisher doesn't know subscribers).
  - Fan-out: one event, many consumers (notifications, projections, audit, analytics).
  - Buffering bursts (broker absorbs traffic the consumer can't keep up with).
  - Event-driven architectures (combine with outbox/CDC for reliable publish).
  - Anti-signal: synchronous request/response with an immediate answer needed; very small system where direct calls are simpler.
- **§4 Trade-offs and failure modes.**
  - **Duplicates are inevitable.** Consumers must be idempotent.
  - **Ordering only within partition.** Cross-partition ordering requires app-level reconciliation.
  - **Rebalance pauses:** consumer group rebalance stops the world for the group. Frequent rebalances (consumer churn, slow processing) are a scaling killer.
  - **Slow consumer = backlog growth.** Lag metric is the canary. Solution: parallelize within partition (only safe if processing is per-message) or repartition.
  - **Poison messages:** one bad message blocks the partition. DLQ with bounded retries; without it, consumer loops forever.
  - **Schema evolution:** producers and consumers deploy independently; backward-compat is non-negotiable. Schema registry + Protobuf/Avro.
  - **The "exactly-once" myth:** if a vendor sells you "exactly-once delivery," ask exactly which step they mean. Usually they mean idempotent processing or transactional commit, not actual exactly-once delivery.
- **§5 Real-world and interviewer probes.**
  - In the wild: Apache Kafka (partitioned log, consumer groups, offset-based replay); Amazon SQS (queues with at-least-once + dedup IDs); Google Pub/Sub (push/pull); RabbitMQ (queues with manual ack); NATS JetStream; Apache Pulsar.
  - Probes:
    - "Why is exactly-once delivery a myth?" → impossible across an unreliable network without infinite memory; what's achievable is idempotent effects.
    - "How do you guarantee ordering?" → partition key = aggregate ID; one consumer per partition per group.
    - "How do you handle a poison message?" → bounded retries → DLQ; alert on DLQ depth.
    - "What happens during a consumer rebalance?" → group pauses, partitions reassigned, processing resumes. Frequent = bad.
    - "Walk me through achieving exactly-once *effects*." → at-least-once delivery + idempotent consumer (dedup key on the message, reject duplicates).

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1200–1500 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/pubsub-semantics.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/pubsub-semantics.md
  git commit -m "docs(system-design): add pub/sub semantics refresher"
  ```

---

## Task 19: Write `bloom-hll.md`

**Files:**
- Create: `topics/system-design/bloom-hll.md`

**Content brief:**

- **§1 TL;DR.** Two probabilistic data structures that trade exactness for tiny fixed memory. **Bloom filters** answer "have I seen this key?" with possible false positives but never false negatives — used to skip expensive lookups. **HyperLogLog** estimates "how many distinct items?" with sub-1% error using a few KB regardless of cardinality. Show up wherever exact answers cost too much.
- **§2 How it works.**
  - **Bloom filter:** bit array of size `m` plus `k` hash functions. Insert: set `k` bits chosen by the hashes. Query: all `k` bits set → "maybe present"; any not set → "definitely absent." False-positive rate `p ≈ (1 - e^{-kn/m})^k`; tunable by `m, k`.
  - **Counting Bloom / Cuckoo filter:** support deletion (vanilla Bloom does not). Cuckoo filter has better space efficiency and supports deletion.
  - **HyperLogLog:** observe leading zero count of `hash(item)`; track per-bucket maximum. Cardinality estimate from harmonic mean across buckets. ~1.04/√m relative error; m=2¹² (4KB) gives ~1.6% error for billions of distinct items.
  - **Mergeable:** both structures merge across shards (Bloom: bitwise OR; HLL: per-bucket max). Critical for distributed systems.
  - **Sizing:** Bloom — pick `m, k` for desired false-positive rate at expected cardinality. HLL — pick precision (number of buckets) for desired error.
- **§3 When to use.**
  - **Bloom:** front of an expensive lookup ("is this key in the DB / on disk / in this SSTable?"); URL / cache-miss filtering; CDN edge "have we seen this before?"; safe-browsing list distribution.
  - **HLL:** unique-visitor counting; distinct-query estimation; A/B test cohort sizing; cardinality monitoring at huge scale.
  - Anti-signal: when you need exact answers, when cardinality is small enough to fit in a regular set, when false positives have unacceptable downstream cost.
- **§4 Trade-offs and failure modes.**
  - **Bloom false positives:** consumer must handle the "go check the source anyway" path. False-positive rate degrades as the filter fills past sizing assumptions.
  - **No deletion:** vanilla Bloom can only add. Long-lived Bloom must be rebuilt; use counting/Cuckoo if deletion needed.
  - **Cuckoo's failure mode:** insert can fail at high load (>~95% capacity). Plan resize.
  - **HLL doesn't give individual identities:** can answer "how many distinct" but not "which ones." If you need both, combine with a second structure.
  - **HLL underestimates at very small cardinality:** linear-counting fallback for the low end (HLL++ does this).
  - **Hash collisions:** both structures depend on hash quality. Use a known-good hash (xxHash, MurmurHash3).
  - **Operational misuse:** sizing for the wrong cardinality assumption silently degrades accuracy without an alert. Track `inserted_count / sized_count`.
- **§5 Real-world and interviewer probes.**
  - In the wild: Bloom filters in Cassandra (per-SSTable, to skip disk reads), HBase, RocksDB, LevelDB; Bitcoin SPV clients (filter blocks by relevance); CDN edge caches; Chrome's safe-browsing local list (compressed Bloom). HyperLogLog in Redis (`PFADD`/`PFCOUNT`), Druid, Apache DataSketches, Snowflake's `APPROX_COUNT_DISTINCT`.
  - Probes:
    - "When would you use a Bloom filter in a database?" → SSTable lookup short-circuit: only read disk if the key *might* be present.
    - "Cuckoo vs. Bloom?" → Cuckoo supports deletion and has better space at low FPR; Bloom is simpler and well-studied. Pick Cuckoo if you need delete.
    - "How accurate is HLL?" → ~1.6% relative error with 4KB; tunable via precision.
    - "How do you merge HLL across shards?" → per-bucket max. This makes it the go-to for distributed cardinality.
    - "Why not just use a HashSet?" → memory grows linearly with cardinality; HLL stays constant.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/bloom-hll.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/bloom-hll.md
  git commit -m "docs(system-design): add bloom filters & HyperLogLog refresher"
  ```

---

## Task 20: Write `schema-evolution.md`

**Files:**
- Create: `topics/system-design/schema-evolution.md`

**Content brief:**

- **§1 TL;DR.** Long-lived data outlives the code that wrote it. Schema evolution is the discipline that lets new code read old data, old code read new data, and producers/consumers deploy independently. Core moves: backward-compatible field changes, expand-contract migrations, schema registry, and never-break-the-wire-format.
- **§2 How it works.**
  - **Compatibility flavors:**
    - **Backward-compatible:** new code reads old data. (Most common requirement.)
    - **Forward-compatible:** old code reads new data. (Required when consumers deploy out-of-order from producers.)
    - **Full:** both directions.
  - **Protobuf / Avro / Thrift rules:**
    - Add field: optional, with default. Safe.
    - Remove field: deprecate first, drop after all readers updated. Reserve the field number.
    - Rename: only the human-readable name; field number/ID is the wire identity. Don't reuse numbers.
    - Type changes: usually breaking; use a new field instead.
  - **Expand-contract migration (DBs):**
    1. **Expand:** add new column / table; dual-write to old + new.
    2. **Backfill:** populate new from old.
    3. **Migrate readers:** flip readers to new column.
    4. **Contract:** stop writing old; drop after a safety window.
  - **Schema registry:** central authority for event schemas. Producers register; consumers fetch; compatibility checks at registration time prevent breaking changes from being deployed.
  - **Versioned events:** event payloads carry schema version; consumers handle every version they may encounter (in practice: every version since the oldest unreplayed event).
- **§3 When to use.**
  - Any persisted data with a non-trivial lifetime (months+).
  - Any pub/sub stream with independent producers and consumers.
  - Any cross-team API with multi-version coexistence.
  - Anti-signal: ephemeral data with single-binary lifetime (caches, in-memory state). Even there, careful: Redis dumps and dev/prod skews bite.
- **§4 Trade-offs and failure modes.**
  - **Field number reuse:** reusing a Protobuf field number is permanent silent corruption. Reserve removed numbers.
  - **Required fields are forever.** A "required" field cannot be removed without breaking old readers. Almost always prefer optional + default.
  - **Default value mismatch:** if old and new code disagree on default for a missing field, you get inconsistent state.
  - **Long-tail consumers:** an old consumer still running months after the schema change reads new events with stale assumptions. Versioned events let consumers branch behavior.
  - **Replay across schema generations:** projection rebuilds replay every historical event format. Consumers must handle all of them.
  - **Big-bang migrations:** dropping a column without expand-contract = downtime + data loss risk.
  - **Schema registry as SPOF:** every producer / consumer needs it on hot path. Cache aggressively.
- **§5 Real-world and interviewer probes.**
  - In the wild: Confluent Schema Registry (Avro / Protobuf); LinkedIn's schema infrastructure on Kafka; Google's Protobuf style guide. Postgres `ALTER TABLE` semantics that gave rise to expand-contract patterns. Stripe's "API versioning by date" as a different solution to the same problem (caller pins a version).
  - Probes:
    - "Walk me through changing a column type without downtime." → expand-contract: add new column, dual-write, backfill, migrate readers, drop old.
    - "How do you safely remove a Protobuf field?" → mark deprecated, ensure no reader requires it, then remove and reserve the number.
    - "Why is a schema registry useful?" → pre-deploy compatibility check; central source of truth for replay/processing tools.
    - "How do you handle replay across many schema versions?" → consumer branches by schema version; old transformations preserved as long as old events exist.
    - "Why never reuse a field number?" → silent wire corruption: an old reader reads bytes intended for the new field as if it were the old field.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/schema-evolution.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/schema-evolution.md
  git commit -m "docs(system-design): add schema evolution refresher"
  ```

---

## Task 21: Write `strangler-fig.md`

**Files:**
- Create: `topics/system-design/strangler-fig.md`

**Content brief:**

- **§1 TL;DR.** The strangler fig pattern incrementally replaces a legacy system by routing pieces of its traffic to a new system, slice by slice, until the legacy is starved of work and can be removed. Named after the strangler-fig vine that grows around a host tree until the tree dies inside. The default playbook for any non-trivial migration.
- **§2 How it works.**
  - **Routing layer / facade:** in front of the legacy system, a proxy decides per-request whether to send to legacy or new. Gateway, BFF, ambassador, or sidecar — anything that can pattern-match.
  - **Slice the system:** identify a bounded surface (one endpoint, one feature, one tenant cohort). The smaller the slice, the less risk per cutover.
  - **Read slice first:** start with read-only paths. Easier to validate; failures are non-destructive.
  - **Dual-run / shadow mode:** new system processes alongside legacy; compare outputs; don't act on new. Builds confidence.
  - **Cutover:** flip routing — new system serves the slice. Legacy still warm for rollback.
  - **Backfill data ownership:** if data lived in legacy DB, migrate it to new system's store (often using CDC / outbox). Or, both write to old DB while new system is the read source of truth.
  - **Decommission:** when no traffic flows through legacy code path for a safety window, delete.
- **§3 When to use.**
  - Replacing any production system that can't be turned off (which is most of them).
  - Untangling a monolith into services (each service is a strangled slice).
  - Database migration (Postgres → Spanner, MySQL → Vitess, etc.) — strangler at the query level.
  - Cloud migration (on-prem → cloud) one slice at a time.
  - Anti-signal: greenfield (no legacy to strangle); systems small enough for a maintenance-window swap; truly stateless components (just deploy the replacement).
- **§4 Trade-offs and failure modes.**
  - **Two systems running in parallel = double cost.** Operational, monetary, cognitive. Plan to actually remove the legacy.
  - **Data ownership ambiguity:** which system is source of truth for a given record during migration? Document and enforce.
  - **Routing logic complexity grows.** As cutover progresses, the facade's "legacy or new?" rules accumulate. Discipline required to delete rules as slices stabilize.
  - **Forgotten dead code in legacy:** "we cut over years ago but the old code is still here, we're not sure what calls it." Decommission step is often skipped; budget for it explicitly.
  - **Behavioral drift between legacy and new during dual-run:** old assumptions baked into legacy not replicated in new. Shadow comparisons help catch.
  - **Schema coupling:** if both systems share a DB, schema changes affect both. Often the strangler must include a DB split.
  - **Rollback cost:** if you cut over and roll back, in-flight new-system writes may be lost. Need rollback plan per slice.
- **§5 Real-world and interviewer probes.**
  - In the wild: Stripe's payments-platform migration; Shopify's monolith decomposition (each "section" extracted as a service). Amazon's S3 (originally fronted with a strangler over older systems). Practically every cloud migration writeup. The original Martin Fowler article ("Strangler Fig Application").
  - Probes:
    - "How do you pick the first slice?" → smallest, lowest-risk, ideally read-only; high enough volume to give confidence.
    - "How do you handle data during migration?" → dual-write or single source of truth + CDC. Document which system owns the write path.
    - "What if rollback is needed mid-cutover?" → routing facade flips back; in-flight writes to new system reconciled to old (or accepted as loss if low-stakes).
    - "When is strangler the wrong choice?" → small system where a maintenance window swap is cheaper than the strangler scaffolding.
    - "What's the most common failure of strangler projects?" → never finishing the decommission step; living with both systems forever.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1100–1400 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/strangler-fig.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/strangler-fig.md
  git commit -m "docs(system-design): add strangler fig refresher"
  ```

---

## Task 22: Write `observability-trio.md`

**Files:**
- Create: `topics/system-design/observability-trio.md`

**Content brief:**

- **§1 TL;DR.** Production observability is the trio of metrics, logs, and traces practiced as one discipline. The patterns that earn their keep at senior+ level: golden-signal frameworks (RED / USE / Four Golden Signals), correlation-ID propagation across services, structured logging, and sampled distributed tracing. Together they are how you debug a distributed system without ssh'ing into it.
- **§2 How it works.**
  - **Metrics — what shape to track:**
    - **RED:** Rate, Errors, Duration (per service/endpoint).
    - **USE:** Utilization, Saturation, Errors (per resource).
    - **Four Golden Signals (Google SRE):** latency, traffic, errors, saturation.
    - Aggregation: histograms over averages (averages hide the tail). p50/p95/p99/p99.9.
  - **Structured logging:** key/value JSON, not text strings. Indexed in a log store; queryable; correlation-friendly.
  - **Correlation IDs:** every request gets a UUID at the edge; propagated through every downstream call as a header (`X-Request-ID`, W3C `traceparent`); included in every log line. Ties logs from many services to one user request.
  - **Distributed tracing:** spans for each operation, parent-child links forming a tree. Sampled (head-based or tail-based) because 100% tracing is too expensive. Exemplars link a metric data point to a representative trace.
  - **Cardinality discipline:** every label dimension multiplies time-series count. Per-user labels = explosion. Bound cardinality at instrumentation time.
- **§3 When to use.**
  - Any production system with more than one service.
  - Anything you'll have to debug at 3am.
  - Specifically required: SLO measurement, on-call alerting, capacity planning, post-incident analysis.
  - Anti-signal: prototypes with single user; never an excuse to skip in production.
- **§4 Trade-offs and failure modes.**
  - **Cardinality explosion:** high-cardinality labels (user ID, request ID, full URL) overwhelm metrics backends. Use exemplars for high-card, metrics for low-card aggregates.
  - **Sampled traces miss rare paths:** 1% sampling won't catch a 0.01% error. Tail-based sampling (sample after seeing the trace, keep errors and slow ones) costs more but catches what matters.
  - **Log volume cost:** at scale, logging every request is expensive. Sample logs too; keep errors at 100%.
  - **Correlation ID gaps:** any service that drops the header breaks the chain. Enforce at the framework / mesh level.
  - **Alerting on symptoms vs. causes:** alert on user-facing symptoms (SLO burn, error rate); diagnose with traces + logs. Symptom alerts survive refactors; cause alerts go stale.
  - **Vendor lock:** every observability stack has its own protocol. OpenTelemetry standardizes the wire format; use it.
  - **Trace context loss across async boundaries:** queue → consumer typically drops trace context unless explicitly propagated in message headers.
- **§5 Real-world and interviewer probes.**
  - In the wild: Prometheus + Grafana (metrics); ELK / Loki / Splunk (logs); Jaeger / Zipkin / Tempo (traces); Datadog, New Relic, Honeycomb (unified vendors). OpenTelemetry as the cross-vendor protocol. W3C Trace Context standard for cross-service propagation. Google's Dapper paper as the original distributed-tracing spec.
  - Probes:
    - "What are the four golden signals?" → latency, traffic, errors, saturation.
    - "Logs vs. metrics vs. traces — when?" → metrics for aggregates and alerting; logs for arbitrary detail you didn't know to instrument; traces for "where is time spent in this request."
    - "Why do you sample traces?" → cost; 100% trace storage at high QPS is unaffordable.
    - "Tail-based vs. head-based sampling?" → head-based (decide at start) is cheaper, may miss errors; tail-based (decide at end) catches errors but requires buffering whole trace.
    - "How does cardinality blow up Prometheus?" → each label combination = a separate time-series; high-cardinality labels (user ID) explode count. Bound at instrumentation.
    - "Walk me through debugging a latency spike across services." → SLO alert fires → check golden-signal dashboards for the affected service → pivot to trace exemplars in the bad bucket → drill into representative traces → cross-reference logs by trace ID.

**Steps:**

- [ ] Write the file per the brief, all five sections, ~1200–1500 words.
- [ ] Run: `.venv/bin/python scripts/verify.py topics/system-design/observability-trio.md` — expect `OK`.
- [ ] Commit:
  ```bash
  git add topics/system-design/observability-trio.md
  git commit -m "docs(system-design): add golden signals + tracing trio refresher"
  ```

---

## Task 23: Add cross-links between system-design topics

**Files:**
- Modify: every file under `topics/system-design/` (except `_TEMPLATE.md`).

This task adds the cross-references between topics that were intentionally deferred during initial writing. Each modification adds a few links inside the existing prose (typically in §3 "When to use," §4 "Trade-offs," or §5 "Real-world"). The exact prose can be paraphrased; the **link targets** below are the contract.

**Link map (each topic gets links TO the listed topics; phrasing is the writer's choice):**

| Source file | Outbound links |
|---|---|
| `resilience-four-pack.md` | `idempotency.md`, `backpressure-load-shedding.md`, `observability-trio.md` |
| `idempotency.md` | `resilience-four-pack.md`, `pubsub-semantics.md`, `outbox-cdc.md` |
| `backpressure-load-shedding.md` | `resilience-four-pack.md`, `rate-limiting.md`, `pubsub-semantics.md` |
| `outbox-cdc.md` | `idempotency.md`, `pubsub-semantics.md`, `saga.md` |
| `saga.md` | `outbox-cdc.md`, `idempotency.md` |
| `caching.md` | `cqrs-read-models.md`, `bloom-hll.md` |
| `cqrs-read-models.md` | `caching.md`, `pubsub-semantics.md`, `replication.md`, `schema-evolution.md` |
| `sharding.md` | `consistent-hashing.md`, `replication.md` |
| `consistent-hashing.md` | `sharding.md`, `quorum-consistency.md` |
| `replication.md` | `quorum-consistency.md`, `leader-election-consensus.md` |
| `quorum-consistency.md` | `replication.md`, `leader-election-consensus.md` |
| `leader-election-consensus.md` | `quorum-consistency.md`, `distributed-locks.md` |
| `distributed-locks.md` | `leader-election-consensus.md`, `quorum-consistency.md` |
| `rate-limiting.md` | `backpressure-load-shedding.md` |
| `pubsub-semantics.md` | `idempotency.md`, `outbox-cdc.md`, `backpressure-load-shedding.md`, `schema-evolution.md` |
| `bloom-hll.md` | `caching.md` |
| `schema-evolution.md` | `pubsub-semantics.md`, `cqrs-read-models.md` |
| `strangler-fig.md` | `schema-evolution.md`, `outbox-cdc.md` |
| `observability-trio.md` | `resilience-four-pack.md` |

Use relative paths (e.g., `[idempotency](idempotency.md)`) since all targets live in the same directory.

**Steps:**

- [ ] **Step 1: Add links to each file per the table above.**

For every row, edit the source file. Find a sentence inside §3, §4, or §5 where the linked concept is naturally referenced (the content briefs already mention every cross-reference in prose) and convert that mention into a markdown link. If the brief mentioned the concept in multiple places, only link the first occurrence per file.

Example: in `outbox-cdc.md`, the brief mentions "consumers must be idempotent" in §4. Replace that phrase with: `consumers must be [idempotent](idempotency.md)`.

- [ ] **Step 2: Run the full verifier — every link must resolve.**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python scripts/verify.py`

Expected: `OK (N file(s) verified)` with no `broken internal link` errors.

- [ ] **Step 3: Commit**

```bash
git add topics/system-design/
git commit -m "docs(system-design): add cross-links between related topics"
```

---

## Task 24: Add System Design section to README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Append the new section to README.md**

Open `README.md`. After the existing **Study order** section (after the line for "Boyer-Moore Majority Vote") and before the existing **See also** section, insert:

```markdown
## System Design

A senior-level refresher of the patterns that show up in almost any non-trivial production system. Single-tier core; grouped by the problem they solve, not by perceived difficulty. See `docs/superpowers/specs/2026-05-05-system-design-refresher-design.md` for the inclusion criteria.

**Reliable service-to-service communication**

- [Resilience four-pack](topics/system-design/resilience-four-pack.md)
- [Idempotency](topics/system-design/idempotency.md)
- [Backpressure & load shedding](topics/system-design/backpressure-load-shedding.md)

**Reliable data flow across services**

- [Transactional outbox + CDC](topics/system-design/outbox-cdc.md)
- [Saga pattern](topics/system-design/saga.md)

**Scaling reads**

- [Caching strategies & stampede mitigation](topics/system-design/caching.md)
- [CQRS + materialized read models](topics/system-design/cqrs-read-models.md)

**Data distribution & write scaling**

- [Sharding strategies](topics/system-design/sharding.md)
- [Consistent hashing](topics/system-design/consistent-hashing.md)
- [Replication models](topics/system-design/replication.md)
- [Quorum & tunable consistency](topics/system-design/quorum-consistency.md)

**Coordination**

- [Leader election & consensus](topics/system-design/leader-election-consensus.md)
- [Distributed locks done right](topics/system-design/distributed-locks.md)

**Throttling & fairness**

- [Rate limiting](topics/system-design/rate-limiting.md)

**Event-driven plumbing**

- [Pub/sub semantics](topics/system-design/pubsub-semantics.md)

**Probabilistic structures at scale**

- [Bloom filters & HyperLogLog](topics/system-design/bloom-hll.md)

**Evolution in production**

- [Schema evolution & backward compatibility](topics/system-design/schema-evolution.md)
- [Strangler fig](topics/system-design/strangler-fig.md)

**Production observability**

- [Golden signals + tracing trio](topics/system-design/observability-trio.md)
```

- [ ] **Step 2: Run verifier on README links and on full repo**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python scripts/verify.py`

Note: `verify.py` only walks `topics/`; it doesn't validate README links. Verify README links manually:

```bash
cd /Users/panibrat/dev/interview-prep
grep -oE '\(topics/system-design/[^)]+\)' README.md | tr -d '()' | while read p; do
  test -f "$p" && echo "OK: $p" || echo "BROKEN: $p"
done
```

Expected: every printed line begins with `OK:`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): add System Design section linking the new refresher"
```

---

## Task 25: Final integration check

**Files:** none modified — verification only.

- [ ] **Step 1: Run the full verifier from clean working tree**

Run: `cd /Users/panibrat/dev/interview-prep && git status && .venv/bin/python scripts/verify.py`

Expected: `working tree clean` and `OK (N file(s) verified)` with the full set of algorithm topics + the system-design topics, no errors.

- [ ] **Step 2: Run the full pytest suite**

Run: `cd /Users/panibrat/dev/interview-prep && .venv/bin/python -m pytest -v`

Expected: all tests in `scripts/test_verify.py` pass (the original 4 + the 3 added in Task 1).

- [ ] **Step 3: Eyeball the README rendering**

Run: `cd /Users/panibrat/dev/interview-prep && grep -n "System Design" README.md`

Expected: a `## System Design` heading sits below the existing **Study order** list and above the **See also** section.

- [ ] **Step 4: Confirm no orphan files**

Run: `cd /Users/panibrat/dev/interview-prep && ls topics/system-design/`

Expected: `_TEMPLATE.md` plus every file listed in the **File Structure** section above. Nothing missing, nothing extra.

If any check fails, file an issue and stop — do not paper over with quick fixes.
