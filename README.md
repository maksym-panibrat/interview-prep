# LeetCode Interview Prep — Python Reference

A long-term, high-quality reference for LeetCode-style algorithm interviews. Each topic file contains a TL;DR, intuition, walkthrough, implementation, variants, complexity, curated problem set, related patterns, and interviewer follow-ups. Solutions are practiced on LeetCode itself; this repo is the study guide.

## How to use

1. Pick a topic from the **Study order** below.
2. Read its file end to end. Solve the problem set on leetcode.com.
3. When refreshing before an interview, re-read [`RECALL.md`](RECALL.md) (TL;DRs and templates only) and copy from [`templates/`](templates/README.md).

## Tier legend

- **★★★ Must-know cold** — show up constantly. Fluent recall required.
- **★★ Strongly recommended** — show up regularly. Recognize and execute.
- **★ Nice to have** — appear occasionally, mostly at top-tier or specialized roles.

## Study order

**★★★ Must-know cold**

1. [Binary Search](topics/searching-sorting/binary-search.md)
2. [Quicksort & Mergesort](topics/searching-sorting/quicksort-mergesort.md)
3. [Heapsort & Heaps](topics/searching-sorting/heapsort.md)
4. [Two Pointers](topics/two-pointers-sliding-window/two-pointers.md)
5. [Fast/Slow Pointers](topics/two-pointers-sliding-window/fast-slow-pointers.md)
6. [Sliding Window](topics/two-pointers-sliding-window/sliding-window.md)
7. [BFS](topics/graphs/bfs.md)
8. [DFS](topics/graphs/dfs.md)
9. [Topological Sort](topics/graphs/topological-sort.md)
10. [Union-Find](topics/graphs/union-find.md)
11. [Shortest Paths (Dijkstra)](topics/graphs/shortest-paths.md)
12. [1D DP](topics/dp/1d-dp.md)
13. [2D DP](topics/dp/2d-dp.md)
14. [Interval DP](topics/dp/interval-dp.md)
15. [Tree DP](topics/dp/tree-dp.md)
16. [Bitmask DP](topics/dp/bitmask-dp.md)

**★★ Strongly recommended**

17. [KMP](topics/strings/kmp.md)
18. [Rabin-Karp](topics/strings/rabin-karp.md)
19. [Trie](topics/strings/trie.md)
20. [Tree Traversals](topics/trees/traversals.md)
21. [Binary Search Tree](topics/trees/bst.md)
22. [Lowest Common Ancestor](topics/trees/lca.md)
23. [Segment Tree & Fenwick](topics/trees/segment-tree-fenwick.md)
24. [Interval Scheduling](topics/greedy/interval-scheduling.md)
25. [Activity Selection (and Huffman name-drop)](topics/greedy/activity-selection.md)
26. [Backtracking Template](topics/backtracking/backtracking-template.md)
27. [N-Queens & Sudoku](topics/backtracking/n-queens-sudoku.md)
28. [Grid Backtracking](topics/backtracking/grid-search.md)
29. [GCD](topics/math/gcd.md)
30. [Sieve of Eratosthenes](topics/math/sieve.md)
31. [Fast Exponentiation](topics/math/fast-exponentiation.md)

**★ Nice to have**

32. [A* Search](topics/nice-to-have/a-star.md)
33. [Minimum Spanning Tree](topics/nice-to-have/mst.md)
34. [Max Flow / Min Cut](topics/nice-to-have/max-flow.md)
35. [Reservoir Sampling](topics/nice-to-have/reservoir-sampling.md)
36. [Manacher's Algorithm](topics/nice-to-have/manacher.md)
37. [Z-Algorithm](topics/nice-to-have/z-algorithm.md)
38. [Tarjan's & Kosaraju's (SCC)](topics/nice-to-have/tarjan-kosaraju.md)
39. [Boyer-Moore Majority Vote](topics/nice-to-have/boyer-moore.md)

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

## See also

- [`RECALL.md`](RECALL.md) — consolidated 30-second cards (TL;DR + Template per topic)
- [`templates/README.md`](templates/README.md) — bare-bones Python snippet library
