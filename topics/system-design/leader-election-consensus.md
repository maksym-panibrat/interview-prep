# Leader election and consensus

## 1. TL;DR

**Consensus** protocols — Raft, Paxos, Multi-Paxos, EPaxos — let a cluster agree on a single value (or single ordered log of values) despite crashes, slow links, and partitions. **Leader election** is the most common building block on top: agreeing "who's in charge" so operations can be serialized through one node. The engineering question is whether you actually need consensus at all. Every commit costs a majority round trip and pins a single leader as the throughput ceiling, so reach for it only when one ordering of events is a hard requirement; workloads that tolerate eventual consistency should skip the tax and use quorum replication instead.

## 2. How it works

### Raft, the readable one

If you remember one consensus protocol, remember Raft. It exists because Paxos is correct but unreadable, and unreadable protocols become buggy implementations. Raft splits the problem into clean sub-problems: leader election, log replication, and safety.

A Raft cluster has `N` nodes (typically 3 or 5). Each node is **follower**, **candidate**, or **leader**. Time is divided into **terms** — monotonically increasing integers, at most one leader per term. A node persists `currentTerm`, `votedFor`, and its log to disk before responding to any RPC.

```
   term 7              term 8 (election)              term 8
 leader L1 ---X---> [no leader, candidates fight] ---> leader L2
                    (election timeout, RequestVote)
```

### Election

Each follower runs a **randomized election timeout** (typically 150–300ms). If it does not hear a heartbeat before the timeout, it becomes a candidate, increments `currentTerm`, votes for itself, and sends `RequestVote` to peers. A node grants its vote only if the candidate's log is at least as up-to-date as its own (last-term, last-index check). The first candidate to collect a **majority** wins; ties trigger another randomized timeout and a new term. The term number is the anti-stale-leader weapon — any RPC carrying a higher term forces the receiver to step down.

### Log replication

The leader appends client commands to its log and sends `AppendEntries` to followers. An entry is **committed** when it is durable on a majority of logs — at which point the leader applies it to its state machine and replies to the client. Followers apply committed entries in the same order. The invariant: **same operations applied in the same order to deterministic state machines produce the same state on every replica** — state-machine replication.

```
client --write--> leader
                    | log: [.. e1 e2 e3]
                    +--AppendEntries(e3)--> follower A   (ack)
                    +--AppendEntries(e3)--> follower B   (ack)   <- majority
                    +--AppendEntries(e3)--> follower C   (slow)
                  e3 committed, apply to state machine, reply to client
```

### Safety

The election rule (vote only for candidates whose logs are at least as up-to-date) plus the commit rule (a leader only commits entries from its own term once a majority has them) together guarantee that a committed entry is never overwritten. Lagging followers catch up; diverging followers get their conflicting suffix overwritten by the leader.

### Quorum size

A cluster of `N` tolerates `⌊N/2⌋` failures and needs `⌊N/2⌋ + 1` for any commit. `N = 3` tolerates 1; `N = 5` tolerates 2; `N = 7` tolerates 3. **Even `N` gains nothing extra over odd `N − 1`** — both tolerate the same number of failures, but `N = 4` requires 3 of 4 alive and loses on a 2-2 partition where 3 of 3 would still have majority. Odd `N` is the convention.

### Paxos, Multi-Paxos, EPaxos

**Paxos** (Lamport, 1989) is the original; single-decree Paxos agrees on one value through prepare/promise/accept/accepted phases. **Multi-Paxos** amortizes the prepare phase by electing a stable leader, so steady-state operation is one round trip per command — operationally similar to Raft, just less readable. **EPaxos** is leaderless: any replica can propose, conflicts ordered via dependency graphs. It pays off when writes rarely conflict and clients are geographically spread.

## 3. When to use

Reach for consensus when:

- **You need a single coordinator.** Sequencer for global IDs, lock service, primary in a primary-replica DB, current-leader-of-shard. Leader election is the cheapest correct way.
- **You need strongly consistent metadata.** Cluster membership, configuration, schema, feature flags that must never diverge. Small data, low write rate — a perfect fit.
- **You need a replicated log / state machine.** Every replica applies the same operations in the same order. etcd, ZooKeeper, KRaft, the per-range groups in CockroachDB and Spanner.
- **You need linearizable reads.** Route reads through the leader's log or use leader leases.

Anti-signals — do not use consensus for:

- **High-throughput data plane.** Every commit is a majority round trip. Raft fits a coordination plane; it does not fit "every customer event goes through Raft." Shard the keyspace and run a Raft group per shard if you need to scale.
- **Workloads where eventual consistency is fine.** Feeds, social graphs, analytics, audit-style append. Use quorum replication and CRDTs and skip the consensus tax.
- **Cross-region critical-path writes you cannot afford tens of ms for.** Consensus across regions costs WAN RTT per commit; the answer is sharded leadership per region, not a single global Raft group.

## 4. Trade-offs and failure modes

- **Latency floor is one majority round trip.** Within an AZ a few ms; across regions tens to hundreds. Every committed write pays it. You cannot optimize past it without weakening the guarantee.
- **CP under partition.** Without a majority, the cluster makes no progress. The minority side is read-only at best (and only safely under a leader lease that has not expired). This is the price of strong consistency — pretending otherwise is split-brain.
- **Single-leader throughput cap.** All writes funnel through the leader. Disk fsync on the leader is the floor on commit latency. Group commit batches help; raising IOPS helps; the only architectural escape is sharding into multiple Raft groups.
- **Stale-leader reads.** A partitioned-out leader may still believe it is leader and serve local reads, missing commits by the new leader. Mitigations: route reads through the log (no-op committed via majority confirms leadership, slow); or use **leader leases** — reads served within a time-bounded lease are linearizable (faster, requires bounded clock drift).
- **Cluster reconfiguration is its own protocol.** Naive add/remove opens a window where two majorities disagree on membership. Raft uses **joint consensus** (`C_old,new` requires majority in both old and new sets). Operationally awkward and rarely well-tested in homegrown implementations.
- **Disk fsync dominates p99.** Every commit is durable on the leader before ack — a noisy-neighbor disk becomes a cluster-wide latency spike. Provision dedicated disks for consensus volumes.
- **Operational complexity.** Snapshots, log compaction, term and index invariants on disk — Raft is simpler than Paxos but still a real distributed system. Recovering from quorum loss is a fraught manual procedure.

## 5. Real-world and interviewer probes

In the wild: **etcd** and **Consul** use Raft for their coordination logs; Kubernetes is etcd-on-Raft underneath. **ZooKeeper** uses **Zab**, a Paxos-family atomic broadcast protocol. **Spanner** runs Paxos per data range to replicate writes synchronously across zones, layering TrueTime on top for external consistency. **CockroachDB** runs Raft per range — one cluster contains tens of thousands of small Raft groups. **Kafka KRaft** is a Raft-based metadata quorum that replaced ZooKeeper for cluster controllers. **HashiCorp Vault** uses Raft for its integrated storage backend.

Probes you should expect:

- *"Why is the cluster size usually odd?"* — A cluster of `N` tolerates `⌊N/2⌋` failures. `N = 4` tolerates 1 (same as `N = 3`) but costs an extra node and loses on a 2-2 partition. Odd sizes give you the most fault tolerance per replica cost.
- *"How does Raft elect a leader?"* — Followers run randomized election timeouts. On timeout, a follower becomes a candidate, increments its term, votes for itself, and asks peers for votes. First candidate to a majority wins. The randomized timeout breaks ties; the term number prevents stale leaders from acting after a partition heals.
- *"Why not put everything behind Raft?"* — Latency tax (every write is a majority round trip plus an fsync), throughput cap (single leader), and operational complexity. Use it only for things that genuinely need agreement on an ordering — coordination metadata, lock services, replicated state machines — not the customer-facing data plane.
- *"How do you do linearizable reads in Raft?"* — Two options. Route the read through the log: append a no-op, wait for it to commit on a majority, then read. Slow, always correct. Or use **leader leases**: the leader holds a time-bounded lease confirmed by majority heartbeats, and reads served while the lease is valid are linearizable. Faster, assumes bounded clock drift.
- *"Difference between consensus and quorum-based replication?"* — Consensus picks **one** ordering of commits; every replica agrees that operation X happened before Y. Quorum-based replication accepts concurrent writes at different coordinators and reconciles later via LWW, vector clocks, or CRDTs; replicas temporarily disagree on ordering and converge through read repair. Consensus buys strong consistency at the cost of latency and a single-leader bottleneck; quorum replication buys availability and throughput at the cost of conflict resolution.
