# Topological Sort

## 1. TL;DR

Topological sort orders the nodes of a **DAG** (directed acyclic graph) so that every directed edge `u → v` has `u` appearing before `v`. The signal is "build order," "course prerequisites," "task scheduling with constraints," "compile order," or any problem that requires respecting dependency chains. Two equivalent algorithms: **Kahn's** (BFS-based, peels in-degree-0 nodes level by level) and **DFS-based** (post-order reversed). Kahn's naturally detects cycles; DFS-based is cleaner if you already have DFS set up. Time: O(V + E). Space: O(V).

## 2. Intuition

In any DAG, at least one node has no incoming edges — no dependencies. That node can go first. Remove it and all its outgoing edges; now another node has become dependency-free. Repeat until all nodes are placed or you detect a cycle (nothing left with in-degree 0 but nodes remain).

This is Kahn's algorithm in one sentence: *repeatedly peel nodes with in-degree 0 into the output*. The BFS queue holds all currently in-degree-0 nodes; each time you pop a node, you reduce its successors' in-degrees and enqueue any that reach 0.

The DFS-based view comes from a different angle: in a DFS, a node is not "done" until all nodes reachable from it are done. So the **finish time** captures dependency ordering: a node that finishes last has no dependents, i.e., it belongs at the end. Reverse the finish-time order and you get topological order — dependents come after their dependencies.

Both views produce a valid topological order. Kahn's is preferred when you need cycle detection or a deterministic (lex-smallest) order; DFS-based is convenient when you already have recursive DFS in your solution.

## 3. Walkthrough

### Kahn's algorithm

Edges: `[1,0], [2,0], [3,1], [3,2]`. Course 3 depends on 1 and 2; both depend on 0.

```
Graph:  0 → 1,  0 → 2 (reversed: 1 depends on 0, 2 depends on 0)
Actually: edge [1,0] means "course 1 requires course 0" → directed edge 0→1.
So adjacency list:
  0: [1, 2]
  1: [3]
  2: [3]
  3: []

In-degree array (count of incoming edges):
  node:     0  1  2  3
  in-deg:   0  1  1  2
```

```
Step 1: queue = [0]  (in-degree 0)
  Pop 0: add to result → result = [0]
  Reduce in-degree of 0's neighbors:
    1: 1→0  → enqueue 1
    2: 1→0  → enqueue 2
  queue = [1, 2]

Step 2: Pop 1: result = [0, 1]
  Reduce in-degree of 1's neighbor:
    3: 2→1
  queue = [2]

Step 3: Pop 2: result = [0, 1, 2]
  Reduce in-degree of 2's neighbor:
    3: 1→0  → enqueue 3
  queue = [3]

Step 4: Pop 3: result = [0, 1, 2, 3]
  No neighbors.  queue = []
```

Final order: `[0, 1, 2, 3]`. Valid: 0 before 1, 0 before 2, 1 before 3, 2 before 3. Another valid order is `[0, 2, 1, 3]` — Kahn's output depends on queue order.

**Cycle detection**: if `len(result) < n` at the end, some nodes were never peeled — they are in a cycle (their in-degree never reached 0).

### DFS-based variant (same graph)

Run DFS from each unvisited node; on finish (post-order), push to a result list; reverse at end.

```
Visit 0 (unvisited):
  recurse → 1 (unvisited):
    recurse → 3 (unvisited):
      no unvisited neighbors → finish 3 → result = [3]
    back to 1 → finish 1 → result = [3, 1]
  recurse → 2 (unvisited):
    3 already visited → finish 2 → result = [3, 1, 2]
  finish 0 → result = [3, 1, 2, 0]

Reverse: [0, 2, 1, 3]  ← valid topological order
```

## 4. Implementation

```python
from __future__ import annotations
from collections import deque
from typing import Dict, List, Optional, Set


def kahn(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    """Kahn's algorithm (BFS-based topological sort).

    `graph` is an adjacency list of a directed graph on nodes 0..n-1.
    Returns a valid topological order, or None if the graph has a cycle.
    """
    in_degree = [0] * n
    for u in range(n):
        for v in graph.get(u, []):
            in_degree[v] += 1

    queue: deque[int] = deque(i for i in range(n) if in_degree[i] == 0)
    result: List[int] = []

    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # If not all nodes were processed, there is a cycle.
    return result if len(result) == n else None


def dfs_topo(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    """DFS-based topological sort.

    Returns a valid topological order, or None if the graph has a cycle.
    Uses 3-color DFS to detect cycles.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n
    result: List[int] = []

    def dfs(u: int) -> bool:
        """Returns True if a cycle is detected."""
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:   # back edge → cycle
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        result.append(u)           # post-order: push on finish
        return False

    for i in range(n):
        if color[i] == WHITE:
            if dfs(i):
                return None         # cycle found

    result.reverse()               # post-order reversed = topo order
    return result


if __name__ == "__main__":
    # Edges: [1,0], [2,0], [3,1], [3,2]  → adjacency list 0→[1,2], 1→[3], 2→[3]
    g: Dict[int, List[int]] = {0: [1, 2], 1: [3], 2: [3], 3: []}
    n = 4

    kahn_result = kahn(g, n)
    assert kahn_result is not None
    # Verify: every edge u→v has u before v in the order
    pos = {node: i for i, node in enumerate(kahn_result)}
    for u in g:
        for v in g[u]:
            assert pos[u] < pos[v], f"Violation: {u} before {v} not satisfied"

    dfs_result = dfs_topo(g, n)
    assert dfs_result is not None
    pos2 = {node: i for i, node in enumerate(dfs_result)}
    for u in g:
        for v in g[u]:
            assert pos2[u] < pos2[v], f"DFS topo violation: {u} before {v}"

    # Graph with a cycle: 0→1, 1→2, 2→0
    cyclic: Dict[int, List[int]] = {0: [1], 1: [2], 2: [0]}
    assert kahn(cyclic, 3) is None
    assert dfs_topo(cyclic, 3) is None

    print("All smoke tests passed.")
```

**Template:**

```python
from collections import deque
from typing import Dict, List, Optional


def kahn(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    in_degree = [0] * n
    for u in range(n):
        for v in graph.get(u, []):
            in_degree[v] += 1
    queue: deque = deque(i for i in range(n) if in_degree[i] == 0)
    result: List[int] = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    return result if len(result) == n else None


def dfs_topo(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n
    result: List[int] = []

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        result.append(u)
        return False

    for i in range(n):
        if color[i] == WHITE:
            if dfs(i):
                return None
    result.reverse()
    return result
```

## 5. Variants & pitfalls

### Kahn's vs DFS-based

Both produce a valid topological order in O(V + E). Choose Kahn's when you also need cycle detection expressed as a simple count check (`len(result) < n`), or when you want a deterministic lex-smallest order by replacing the queue with a min-heap. Choose DFS-based when you already have recursive DFS and want to add topo order with minimal extra code.

### Lex-smallest topological order

In Kahn's, replace `deque` with `heapq` (min-heap). Each time in-degree reaches 0, push to the heap instead of the queue. This processes nodes in ascending node-id order at each level, producing the lexicographically smallest valid topological order in O((V + E) log V).

### Cycle detection

Kahn's: if `len(result) < n` after the loop, there is a cycle (those nodes' in-degrees never reached 0). DFS-based: a back edge to a GRAY node signals a cycle.

### DAG longest path (critical path)

Process nodes in topological order; for each node u, relax outgoing edges: `dist[v] = max(dist[v], dist[u] + weight(u, v))`. This is DP over the topo order and runs in O(V + E) — much faster than Dijkstra-based approaches on DAGs.

### Pitfalls

- **DFS pre-order mistake**: topological order comes from DFS **post-order** reversed, not pre-order. Pre-order gives the order nodes were first encountered, not the order they finished — these are different for non-linear graphs.
- **Forgetting to reverse**: after collecting post-order finish times, `result.reverse()` turns them into topological order. Missing this step silently produces the wrong (reversed) answer.
- **Treating undirected graph as a DAG**: undirected graphs have no direction on edges and no well-defined topological order. Cycle detection on undirected graphs uses a different algorithm (visited + parent check).
- **Disconnected DAGs**: always loop over all nodes (not just a single DFS from node 0) to handle disconnected components. Kahn's handles this naturally via the in-degree initialization; DFS-based needs an outer loop `for i in range(n)`.

## 6. Complexity

- **Time:** O(V + E) — in-degree computation visits every edge once; the main loop dequeues each node once and processes each edge once.
- **Space:** O(V) — the in-degree array, the queue, and the result list are all O(V); the adjacency list itself is O(V + E) but is pre-existing input.

## 7. Problem set

- [Medium] [Course Schedule](https://leetcode.com/problems/course-schedule/) — detect if a valid course ordering exists; pure cycle detection on a directed graph; Kahn's `len(result) == n` check is the one-liner answer.
- [Medium] [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) — return the actual ordering (not just existence); direct application of `kahn` or `dfs_topo`.
- [Medium] [Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/) — iterative leaf-peeling on an undirected tree; structurally identical to Kahn's (peel degree-1 nodes repeatedly).
- [Medium] [Find Eventual Safe States](https://leetcode.com/problems/find-eventual-safe-states/) — find nodes that cannot be part of a cycle; reverse the graph and run Kahn's, or 3-color DFS.
- [Medium] [Sort Items by Groups Respecting Dependencies](https://leetcode.com/problems/sort-items-by-groups-respecting-dependencies/) — two-level topological sort (topo within groups, topo of groups); hardest medium topo problem.
- [Hard] [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) — infer character ordering from sorted word list; build a directed graph from adjacent-word comparisons, then topo sort.
- [Hard] [Parallel Courses III](https://leetcode.com/problems/parallel-courses-iii/) — minimum time to finish all courses; DAG longest path via DP in topological order.

## 8. Related patterns

- **[BFS](bfs.md)** — Kahn's algorithm is BFS on a DAG, using in-degree as the BFS driver instead of distance.
- **[DFS](dfs.md)** — DFS post-order reversed is an equivalent topological sort; also needed for the 3-color cycle detection used in `dfs_topo`.
- **Tree DP** (file at `../dp/tree-dp.md` — does not exist yet): DAG DP often processes nodes in topological order, computing a DP value for each node after all its predecessors are settled.

## 9. Interviewer follow-ups

**Q: How do you detect a cycle using Kahn's algorithm?**
After running Kahn's, check `len(result) == n`. If the count is less than n, then n − len(result) nodes were never enqueued because their in-degree never reached 0 — these nodes form one or more cycles. This is often cleaner than DFS-based cycle detection for "does a valid order exist?" questions.

**Q: How do you get the lexicographically smallest topological order?**
Replace the `deque` in Kahn's with a min-heap (`heapq`). Push nodes with in-degree 0 onto the heap; `heappop` always extracts the smallest current candidate. The rest of the algorithm is unchanged. Complexity becomes O((V + E) log V) due to heap operations.

**Q: How do you find the longest path in a DAG?**
Process nodes in topological order; maintain a `dist[]` array initialized to 0. For each node u in topo order, for each edge u → v with weight w: `dist[v] = max(dist[v], dist[u] + w)`. The answer is `max(dist)`. This is O(V + E) and works because topo order guarantees all predecessors of v are processed before v.
