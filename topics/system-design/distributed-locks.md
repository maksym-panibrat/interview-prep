# Distributed locks

## 1. TL;DR

A **distributed lock** gives one client exclusive access to a resource across machines. It is deceptively dangerous: the holder can crash, GC-pause, or partition out and become a "ghost" — waking up convinced it still has the floor while someone else has already taken it. The fix is a lease (TTL with renewal) plus a **fencing token**: a monotonically increasing ID returned with the lock that the resource itself validates. Without fencing tokens you do not have a safe distributed lock; you have an advisory hint that fails rarely enough to fool you. Redlock on Redis is the canonical near-miss and the source of one of the most-cited debates in distributed systems.

## 2. How it works

### Lease, not lock

A distributed "lock" is really a **lease**: an exclusive grant with a TTL, renewed by the holder before expiry or auto-released by the service when expiry hits. Walk it: process A acquires a lease with TTL 30s. A pings the lock service every 10s to renew, well inside the TTL. A's host crashes. After 30s of no renewal, the service expires the lease on its own. Process B acquires. **No human is in the cleanup path** — failure of the holder is recovered by the passage of time, not by an operator. Drop the TTL and a single crashed holder pins the resource forever.

### The TTL trap

The lease buys autonomy at the cost of a timing assumption: the holder must notice "I still own this" inside the TTL window. The runtime stops cooperating the moment a stop-the-world GC, a scheduling stall on an over-committed VM, or a swap-thrashing host steals more time than the TTL allows. Walk it: A holds the lease with token `33` and TTL 30s. A enters a 35s GC pause. At t=30 the service expires A's lease and at t=31 grants B a fresh lease with token `34`. B writes. At t=35 A resumes — still convinced it owns the lock, with no in-band signal that anything changed — and writes too. **Both writes succeed at the resource unless something at the resource rejects A.** A network partition between the holder and the service, or a clock jump on the service host, produces the same picture.

```mermaid
sequenceDiagram
    participant A as Client A
    participant L as Lock service
    participant R as Resource
    participant B as Client B
    A->>L: acquire (TTL = 30s)
    L-->>A: granted, token = 33
    Note over A: GC pause 45s
    Note over L: lease expires at t=30
    B->>L: acquire
    L-->>B: granted, token = 34
    B->>R: write (token = 34)
    R-->>B: accepted; last_fence = 34
    Note over A: wakes, still believes it holds the lock
    A->>R: write (token = 33)
    R-->>A: REJECTED (33 < 34)
```

**You cannot use wall-clock time to reason about safety across processes** — time on the holder and time on the service are not the same clock, and TTLs are guesses about pause durations you cannot bound.

### Fencing tokens

The fix is to stop trusting the holder and let the resource arbitrate. Every successful acquisition returns a monotonically increasing **fencing token** — `33`, `34`, `35`, never reused, never decreasing. Every write to the protected resource carries the token, and the resource enforces the rule:

```
on write(value, incoming_token):
    if incoming_token >= latest_lock_token:
        apply(value)
        latest_lock_token = incoming_token   # atomic with the apply
    else:
        reject
```

Walk the zombie scenario: B writes with `34`, the resource accepts and bumps `latest_lock_token` to `34`. A wakes from its GC pause and writes with `33`. `33 < 34`, **rejected**. **The resource is the source of truth, not the lock service.** The lock service can lose its mind — reissue early, double-grant, partition — and safety still holds, because the only way to corrupt the resource is to present a token at least as large as the one it last accepted, and the lock service's monotonicity guarantees there is at most one such holder at any moment.

The check must live at the resource, atomic with the write. In SQL, that is `UPDATE row SET col = ?, latest_lock_token = ? WHERE id = ? AND ? >= latest_lock_token`; if zero rows are affected, your token is stale. With S3, the token rides in `If-Match` against the object's ETag (or in object-lock conditional headers); GCS uses `x-goog-if-generation-match`. A plain POSIX filesystem has no atomic check-then-write against a stored fence, and that is the honest answer to "is my POSIX-file lock safe?" — **no, because the resource cannot enforce.**

### Coordination service-backed (etcd, ZooKeeper)

A strongly consistent, [leader-elected store](leader-election-consensus.md). A lock is a key with an attached lease; clients acquire by creating the key under the lease, watch for release, and use **the per-acquisition monotonic version the store already produces** as the fencing token — `mod_revision` in etcd, `czxid` in ZooKeeper. The store's consensus protocol handles failover, lease expiry, and ordering, and the version is monotonic by construction across the cluster. **You get a fence for free; you just have to send it.** A few milliseconds per acquisition within a region. The right answer when correctness matters more than latency.

### Single-Redis with TTL

`SET key value NX PX 30000`. One round trip, microseconds, trivial to reason about — and unsafe on failover because Redis replication is asynchronous. Walk it: client A sends `SET NX`, master accepts, master acks A. Master crashes before the write replicates. Sentinel promotes the replica, which has no record of the lock. Client B sends `SET NX` to the new master, succeeds. **Two holders, same key, neither aware of the other** — split-brain at the lock service. Single-Redis also has **no native fencing token**: you can stuff a UUID into the value to prevent unlock-of-a-stolen-lock (Lua compare-and-delete), but a UUID is not monotonic, so the resource has nothing to compare against. Safe single-Redis locking requires you to mint a fence yourself somewhere monotonic (e.g., a DB sequence), which usually defeats the point of using Redis.

### Redlock (multi-Redis)

Redlock acquires on a [majority of `N` independent Redis nodes](quorum-consistency.md) within a bounded time window `T`, treating that majority as ownership. The dispute is concrete. **Martin Kleppmann's argument:** Redlock's safety proof assumes the holder cannot pause longer than `T`'s implicit bound; a GC pause or scheduling stall longer than that bound lets the lease expire and be reissued while the holder still thinks it owns the lock. The multi-node majority does not eliminate this — it just adds a second timing assumption (bounded clock drift across the `N` independent nodes, since each node ages its TTL on its own clock). Without fencing tokens, no TTL-based lock is safe under unbounded pauses, and Redlock proposes none. **antirez's pushback:** clock jumps of the relevant magnitude don't happen on healthy production hosts, GC pauses long enough to matter are rare, and Redlock holds under the threat model it was designed for; you can layer fencing on top if you want.

Don't take a side; take the lesson. **The interesting question is not which lock service you picked. It is whether the resource validates fencing tokens.** A correct fence in front of a "wrong" lock service is safe. No fence in front of any lock service — Redis, etcd, Chubby — eventually isn't.

## 3. When to use

- **Exclusive access to a resource that can validate a fencing token.** DB row, S3 object, lease-aware service — the resource is the source of truth and rejects stale tokens.
- **Leader election.** Use a coordination service (etcd, ZooKeeper, Consul) and ride its monotonic version (`mod_revision`, `czxid`) as the fence. Reuse correct primitives instead of building one.
- **Throttling exclusive jobs.** "Only one cron worker runs the nightly batch." Cheap correctness, bounded blast radius.
- **Workflow gating.** "Only one orchestrator processes this saga at a time" with the saga row as the fence.

Anti-signals:

- **High-throughput per-row contention.** Reach for **optimistic concurrency control**, not a lock. Add a `version` column; on update, `UPDATE row SET col = ?, version = version + 1 WHERE id = ? AND version = ?`. If the `WHERE` matches, you got the row and won the race. If it didn't, someone wrote between your read and your update — re-read and retry. **No lock service, no lease, no GC-pause failure mode; throughput scales with row-level contention, not lock-service capacity.** Most "we need a distributed lock" asks are an OCC problem in disguise.
- **Resource cannot validate fencing tokens.** The "lock" is advisory. Be honest: redesign the resource, or accept the rare double-write.
- **Cross-service ordering, not exclusion.** That is what a saga or an idempotency key is for.

## 4. Trade-offs and failure modes

- **GC pauses, clock drift, network partitions** all break the assumption that lease expiry on the service and on the holder happen at the same wall-clock moment. Any one produces a zombie holder.
- **Without fencing tokens, no distributed lock is safe.** The resource must be the source of truth; the lock service is a hint. Redlock's specific issue is the same lesson: multi-node majority does not eliminate the timing assumption, it adds clock drift between the `N` nodes to the bet.
- **Lease length is a tuning trap.** Too short: renewal storms and false losses on a hiccup. Too long: recovery from a crashed client is slow — the resource is stranded for the full TTL. Pick a TTL longer than your worst expected pause; accept the recovery delay.
- **Lease renewal traffic.** Live clients ping the service constantly; a hot lock is a hot service, and a degraded service means lease loss and acquisition storms.
- **False sense of security.** "I added a Redis lock, problem solved." Without fencing tokens the bug got rarer, not gone — and rare bugs survive testing and surface at 3 AM.
- **Operational subtleties.** Reentrancy; unlock-of-a-stolen-lock (release must verify ownership — Redlock's Lua-script compare-and-delete); session-expiry semantics (ZooKeeper ties locks to sessions; etcd uses explicit lease IDs).

## 5. Real-world and interviewer probes

In the wild, Google's **Chubby** is the original coordination-service-with-locking — five-node Paxos, sessions with leases, foundation under GFS and BigTable. **ZooKeeper** and **etcd** are the open-source descendants and provide correct locks via lease-bound keys; Consul does the same. **Redlock** is the Redis-native alternative and the focus of the canonical "are distributed locks hard?" debate. AWS **DynamoDB**'s `ConditionExpression` is the optimistic-concurrency primitive most teams reach for instead of a lock — CAS at the data store, no separate lock service.

Probes you should expect:

- *"What's a fencing token and why do you need one?"* — A monotonically increasing ID returned with the lock; the resource tracks the highest seen and rejects stale-token writes. Without it, a zombie holder (GC pause, partition, clock jump) can write after the lock has been reassigned.
- *"Why is Redlock controversial?"* — It relies on bounded clock drift and bounded pauses across the `N` nodes; without fencing tokens you cannot prove safety under pauses or drift longer than the bound. The lesson is fencing tokens, not which lock service.
- *"What's the alternative to a distributed lock for hot rows?"* — Optimistic concurrency control: version column, `UPDATE ... WHERE version = ?`, retry on conflict. No lock service, throughput proportional to the row's write rate, no zombie-holder failure mode.
- *"When would you reach for ZooKeeper or etcd over Redis?"* — When correctness matters more than latency. They're built on consensus and give correct lock semantics; Redis is faster but still requires fencing tokens for safety.
- *"How do you guarantee the holder doesn't release someone else's lock?"* — Tag the lock with a holder-specific value at acquisition. Release is conditional: delete only if the value still matches (Redis: Lua-scripted compare-and-delete). ZooKeeper ties the lock to the session, so the question is moot.
