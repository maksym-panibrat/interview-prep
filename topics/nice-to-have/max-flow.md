# Max Flow / Min Cut

## 1. TL;DR

Max Flow finds the maximum amount of flow that can be sent from a **source** to a **sink** in a capacity-constrained network. The signal is "maximum bipartite matching," "maximum throughput in a network," or any min-cut equivalence problem. Key theorem: **max flow = min cut** (Ford-Fulkerson duality). Edmonds-Karp (BFS-based): O(VE²). Dinic's: O(V²E); O(E√V) for unit-capacity bipartite.

## 2. Intuition

Imagine water flowing through pipes of fixed capacity from a source to a sink. You want to push as much water as possible. **Ford-Fulkerson** says: keep finding any path from source to sink with remaining capacity (an *augmenting path*), push as much flow along it as possible, and repeat until no path remains.

The key non-obvious piece is the **residual graph**: when you push flow along edge (u→v), you also add (or increase) a reverse edge (v→u) with the same amount. This lets the algorithm "undo" earlier choices — sending flow back along a reverse edge re-routes it. Without residual edges, a greedy first path can block the optimal solution.

**Max-flow min-cut theorem:** the maximum flow equals the capacity of the minimum cut (the minimum total capacity of edges that, if removed, disconnect source from sink). After the algorithm terminates, BFS in the residual graph from source identifies the reachable set S; the min-cut is the set of original edges from S to V\S.

**Edmonds-Karp** uses BFS (not DFS) to find augmenting paths, guaranteeing O(VE²) time because BFS picks the *shortest* augmenting path, which limits how many times an edge can be saturated.

## 3. Walkthrough

### Bipartite matching via max flow

Left nodes {A, B, C}, right nodes {X, Y, Z}. Edges: A-X, A-Y, B-X, C-Y, C-Z.

**Reduction:** add super-source `s` → {A, B, C} with capacity 1; add {X, Y, Z} → super-sink `t` with capacity 1; bipartite edges directed left→right with capacity 1.

```
s --1--> A --1--> X --1--> t
         A --1--> Y --1--> t
s --1--> B --1--> X (saturated → use residual)
s --1--> C --1--> Y (saturated → use residual)
         C --1--> Z --1--> t
```

**Trace:**

| Step | BFS path             | Action                                        | Flow |
|------|----------------------|-----------------------------------------------|------|
| 1    | s→A→X→t              | Push 1. X→t saturated.                        | 1    |
| 2    | s→B→X→A(rev)→Y→t     | Residual X→A "un-routes" A from X; A now→Y.   | 2    |
| 3    | s→C→Z→t              | Push 1. Direct path available.                | 3    |

No more augmenting paths. **Max flow = 3 = max matching** {A→Y, B→X, C→Z}.

The residual trick in step 2 is the heart of the algorithm: sending flow backward along A→X (i.e., along reverse edge X→A) frees X for B while re-routing A's flow to Y.

## 4. Implementation

```python
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional


class FlowNetwork:
    """Edmonds-Karp max-flow (BFS augmenting paths). O(VE^2)."""

    def __init__(self, n: int) -> None:
        self.n = n
        # graph[u] = list of [v, capacity, rev_index]
        # rev_index is the index of the reverse edge in graph[v]
        self.graph: List[List[List[int]]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: int) -> None:
        """Add a directed edge u→v with given capacity (and a reverse edge with 0 cap)."""
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])  # reverse edge

    def bfs_augmenting_path(self, s: int, t: int) -> Optional[List[int]]:
        """BFS in residual graph; return parent list if t is reachable, else None."""
        parent = [-1] * self.n
        parent[s] = s
        queue: deque[int] = deque([s])
        while queue:
            u = queue.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and parent[v] == -1:  # residual capacity and unvisited
                    parent[v] = u
                    if v == t:
                        return parent
                    queue.append(v)
        return None  # sink unreachable → no augmenting path

    def max_flow(self, s: int, t: int) -> int:
        """Return maximum flow from s to t using Edmonds-Karp."""
        flow = 0
        while True:
            parent = self.bfs_augmenting_path(s, t)
            if parent is None:
                break
            # Find bottleneck capacity along the path
            path_flow = float("inf")
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        path_flow = min(path_flow, edge[1])
                        break
                v = u
            # Update residual capacities
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        edge[1] -= path_flow                          # forward edge: reduce cap
                        self.graph[v][edge[2]][1] += path_flow        # reverse edge: add cap
                        break
                v = u
            flow += path_flow
        return flow


if __name__ == "__main__":
    # Smoke test: s=0, t=3, edges (0,1,3),(0,2,2),(1,2,2),(1,3,2),(2,3,3)
    fn = FlowNetwork(4)
    fn.add_edge(0, 1, 3)
    fn.add_edge(0, 2, 2)
    fn.add_edge(1, 2, 2)
    fn.add_edge(1, 3, 2)
    fn.add_edge(2, 3, 3)
    result = fn.max_flow(0, 3)
    # Compute expected: let the algorithm determine it, then assert self-consistency
    fn2 = FlowNetwork(4)
    fn2.add_edge(0, 1, 3)
    fn2.add_edge(0, 2, 2)
    fn2.add_edge(1, 2, 2)
    fn2.add_edge(1, 3, 2)
    fn2.add_edge(2, 3, 3)
    expected = fn2.max_flow(0, 3)
    assert result == expected, f"got {result}, expected {expected}"
    assert result == 5, f"max flow should be 5, got {result}"
    print(f"Smoke test passed. Max flow = {result}")
```

**Template:**

```python
from collections import deque
from typing import List, Optional


class FlowNetwork:
    def __init__(self, n: int) -> None:
        self.n = n
        self.graph: List[List[List[int]]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: int) -> None:
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

    def bfs_augmenting_path(self, s: int, t: int) -> Optional[List[int]]:
        parent = [-1] * self.n
        parent[s] = s
        queue: deque[int] = deque([s])
        while queue:
            u = queue.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and parent[v] == -1:
                    parent[v] = u
                    if v == t:
                        return parent
                    queue.append(v)
        return None

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        while True:
            parent = self.bfs_augmenting_path(s, t)
            if parent is None:
                break
            path_flow = float("inf")
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        path_flow = min(path_flow, edge[1])
                        break
                v = u
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        edge[1] -= path_flow
                        self.graph[v][edge[2]][1] += path_flow
                        break
                v = u
            flow += path_flow
        return flow
```

## 5. Variants & pitfalls

### Variants

- **Edmonds-Karp:** Ford-Fulkerson with BFS to select the *shortest* augmenting path. Guarantees O(VE²) time; the BFS constraint prevents the exponential behavior possible with DFS on irrational capacities.
- **Dinic's algorithm:** Builds a level graph (BFS layers), then finds a *blocking flow* in it. Repeat. O(V²E) general; O(E√V) for unit-capacity bipartite — much faster in practice and the preferred choice for competitive programming.
- **Push-relabel:** Maintains a "preflow" and uses node heights to push excess flow toward the sink. O(V²√E) for the highest-label variant; faster in practice on dense graphs but complex to implement.
- **Min-cut from max-flow:** After `max_flow` terminates, BFS in the residual graph from source. Nodes reachable from source form set S; unreachable nodes form set T. The min-cut edges are the original edges from S to T that are saturated (residual capacity = 0).

### Pitfalls

- **Forgetting reverse edges:** Without reverse (residual) edges, the algorithm can make a locally greedy choice that blocks the global optimum and has no way to undo it.
- **Non-integer capacities:** Ford-Fulkerson with DFS may not terminate for irrational capacities. Edmonds-Karp (BFS) terminates for any rational capacities because the number of augmentations is bounded by O(VE).
- **Wrong source/sink edges in reductions:** For bipartite matching, forgetting to cap source→left or right→sink edges at 1 allows a single node to match multiple partners.
- **Modifying graph between queries:** `FlowNetwork` holds residual state; re-use requires rebuilding or resetting all edge capacities.
- **Multiple edges between same pair:** The adjacency-list representation handles this correctly since each `add_edge` call appends distinct edge objects; avoid deduplicating or merging entries.

## 6. Complexity

- **Time (Edmonds-Karp):** O(VE²) — BFS finds shortest augmenting paths; each edge can be a bottleneck at most O(V) times, and each augmentation takes O(E) for BFS.
- **Time (Dinic's):** O(V²E) general; O(E√V) for unit-capacity bipartite graphs.
- **Time (push-relabel, highest-label):** O(V²√E).
- **Space:** O(V + E) — adjacency list stores at most 2E edge entries (each directed edge plus its reverse).

## 7. Problem set

- [Hard] [Maximum Students Taking Exam](https://leetcode.com/problems/maximum-students-taking-exam/) — bipartite matching in disguise (or bitmask DP); recognizing the matching reduction is the key insight.
- [Hard] [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) — primarily a Dijkstra/binary-search problem, but illustrates min-cut thinking on grids.

## 8. Related patterns

- [BFS](../graphs/bfs.md) — Edmonds-Karp uses BFS to find shortest augmenting paths; BFS also identifies the reachable set for min-cut extraction.
- [Shortest Paths](../graphs/shortest-paths.md) — Dijkstra's SSSP structure inspires flow on weighted graphs; both process edges greedily using a priority structure.
- [Union-Find](../graphs/union-find.md) — solves a different connectivity question (same component?), but union-find thinking helps reason about cuts and connected components in the residual graph.

## 9. Interviewer follow-ups

**Q: Reduce bipartite matching to max flow.**
Add super-source `s`, super-sink `t`. For each left node L add edge s→L with capacity 1. For each right node R add edge R→t with capacity 1. For each bipartite edge (L, R) add edge L→R with capacity 1. Max flow equals max matching; the saturated L→R edges form the matching.

**Q: Find min-cut from max flow.**
After `max_flow` terminates, BFS in the residual graph from source (following only edges with remaining capacity > 0). Let S = reachable nodes. The min-cut is the set of original edges from S to V\S. Their total original capacity equals the max flow (by max-flow min-cut duality).
