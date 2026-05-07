# Distributed locks

## 1. TL;DR

A **distributed lock** gives one client exclusive access to a resource across machines. It is deceptively dangerous: the holder can crash, GC-pause, or partition out and become a "ghost" — waking up convinced it still has the floor while someone else has already taken it. The fix is a lease (TTL with renewal) plus a **fencing token**: a monotonically increasing ID returned with the lock that the resource itself validates. Without fencing tokens you do not have a safe distributed lock; you have an advisory hint that fails rarely enough to fool you. Redlock on Redis is the canonical near-miss and the source of one of the most-cited debates in distributed systems.

## 2. How it works

### Lease, not lock

A distributed "lock" is really a **lease**: an exclusive grant with a TTL, renewed before expiry or auto-released. Without the TTL, a crashed holder pins the resource forever.

### The TTL trap

The lease introduces a timing assumption: the holder checks "do I still hold the lease?" often enough relative to the TTL. That breaks the moment the runtime stops cooperating — a stop-the-world GC pause, a scheduling stall on an over-committed VM, a swapping host. The client wakes up, still believing it holds the lock, and writes. Meanwhile the service has reissued the lease to someone else, who is also writing.

```
client A acquires lease (TTL = 30s)        client B
   |                                          .
   | -- GC pause 45s ------------------       .
   .                                          .
   .                  lease expires (t=30)    .
   .                                          .
   .                                  client B acquires lease
   .                                  client B writes (token = 34)
   |                                          .
   | wakes, still thinks it holds lock        .
   | writes (token = 33)  -- REJECTED by resource (33 < 34)
```

A network partition that cuts the holder off from the service, or a clock jump on the service host, produces the same picture. **You cannot use wall-clock time to reason about safety across processes** — time on the holder and time on the service are not the same clock.

### Fencing tokens

The fix is to stop trusting the holder. Every successful acquisition returns a monotonically increasing **fencing token** — `33`, `34`, `35`, never reused, never decreasing. The protected resource tracks the highest token it has accepted and **rejects any write with a smaller token**. The zombie above writes `33` after the resource has accepted `34`; the resource refuses it. The lock service no longer has to be perfect — the resource is the source of truth for "who is current."

The resource must support the check. A database stores `last_fence` on the row: `UPDATE ... WHERE row = ? AND last_fence < ?`. An object store with conditional writes (S3 If-Match, GCS generation numbers) carries the token as the precondition. A plain POSIX filesystem cannot — and that is the honest answer to "is a lock for this resource safe?"

### Coordination service-backed (etcd, ZooKeeper)

A strongly consistent, [leader-elected store](leader-election-consensus.md). A lock is a key with a lease; clients acquire by creating the key, watch for release, and use the key's `mod_revision` (etcd) or `czxid` (ZooKeeper) as the fencing token. The store's consensus protocol handles failover, lease expiry, and ordering. Correct by construction, a few ms per acquisition within a region. The right answer when correctness matters more than latency.

### Single-Redis with TTL

`SET key value NX PX 30000`. One round trip, microseconds, easy to reason about. Loses correctness on failover: master acks the `SET` and crashes before replicating; replica is promoted; a second client acquires the same lock. Two holders, no fencing.

### Redlock (multi-Redis)

Redlock acquires on a [majority of `N` independent Redis nodes](quorum-consistency.md) within a bounded time window, treating that majority as ownership. Martin Kleppmann's well-known critique: Redlock relies on bounded clock drift and bounded GC pauses across those nodes — a long enough holder pause violates safety **even when every node operated correctly** — and without fencing tokens no claimed safety property is provable. Redis's antirez defended the algorithm under different threat models. Take the lesson, not a side: **fencing tokens are the answer, not which lock service you used.**

## 3. When to use

- **Exclusive access to a resource that can validate a fencing token.** DB row, S3 object, lease-aware service — the resource is the source of truth and rejects stale tokens.
- **Leader election.** Use a coordination service (etcd, ZooKeeper, Consul) and treat the elected leader's session ID as the fence. Reuse correct primitives instead of building one.
- **Throttling exclusive jobs.** "Only one cron worker runs the nightly batch." Cheap correctness, bounded blast radius.
- **Workflow gating.** "Only one orchestrator processes this saga at a time" with the saga row as the fence.

Anti-signals:

- **High-throughput per-row contention.** Use **optimistic concurrency control** — a `version` column, `UPDATE ... SET ..., version = version + 1 WHERE id = ? AND version = ?`, retry on conflict. No lock service, no leases, no GC-pause failure mode; throughput limited only by the row's own write rate. Most "we need a distributed lock" requests are this in disguise.
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
