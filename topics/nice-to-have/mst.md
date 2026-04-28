# Minimum Spanning Tree

## 1. TL;DR

A Minimum Spanning Tree (MST) connects all nodes in a weighted undirected graph with the minimum total edge weight, using exactly V−1 edges. Signal: "minimum cost to connect all nodes," "connect all cities with minimum cable," or any problem that asks you to wire up a network cheaply. Two classic algorithms: **Kruskal** (sort edges, union-find) and **Prim** (grow from a root with a min-heap). Kruskal: O(E log E). Prim with heap: O((V + E) log V).

## 2. Intuition

Imagine you are laying cables to connect N cities as cheaply as possible — you need every city reachable but you want to use the cheapest subset of roads.

**Kruskal** thinks globally: sort all candidate edges from cheapest to most expensive, and greedily accept each edge unless it would create a cycle (i.e., both endpoints are already connected). Union-find detects cycles in near O(1). The result is guaranteed optimal by a cut-property exchange argument.

**Prim** thinks locally: start with one node in the tree, then repeatedly pull in the cheapest edge that crosses the boundary between the current tree and the remaining nodes. A min-heap gives efficient extraction of that cheapest crossing edge.

Both are correct because of the **cut property**: for any partition of the nodes into two groups, the minimum-weight edge crossing that cut belongs to some MST. Kruskal implicitly verifies this for each edge; Prim explicitly maintains the cut between tree and non-tree nodes.

## 3. Walkthrough

Graph: 4 nodes A(0), B(1), C(2), D(3) with edges (A,B,1), (A,C,4), (B,C,2), (B,D,5), (C,D,3).

### Kruskal

Sort edges by weight: `[(A,B,1), (B,C,2), (C,D,3), (A,C,4), (B,D,5)]`

```
Components start: {A} {B} {C} {D}

Take (A,B,1): A and B different components → accept. {A,B} {C} {D}   cost=1
Take (B,C,2): B and C different components → accept. {A,B,C} {D}     cost=3
Take (C,D,3): C and D different components → accept. {A,B,C,D}       cost=6
All nodes connected → done. MST cost = 6.
```

Skip (A,C,4): A and C already in same component → reject (would form cycle).
Skip (B,D,5): already connected.

### Prim (from A)

```
In-tree: {A}      Heap: [(1,A,B), (4,A,C)]

Pop (1,A,B) → add B. Push B's edges to non-tree: (2,B,C), (5,B,D)
In-tree: {A,B}    Heap: [(2,B,C), (4,A,C), (5,B,D)]

Pop (2,B,C) → add C. Push C's edges to non-tree: (3,C,D)  [A,C ignored: A in tree]
In-tree: {A,B,C}  Heap: [(3,C,D), (4,A,C), (5,B,D)]

Pop (3,C,D) → add D. All 4 nodes in tree → done. MST cost = 6.
```

## 4. Implementation

```python
from __future__ import annotations

import heapq
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Kruskal's algorithm
# ---------------------------------------------------------------------------

def kruskal(n: int, edges: List[Tuple[int, int, int]]) -> Tuple[int, List]:
    """Return (total_cost, mst_edges) for a graph of n nodes (0-indexed).

    edges: list of (u, v, weight)
    Uses inline union-find with path compression and union-by-rank.
    """
    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    def union(x: int, y: int) -> bool:
        rx, ry = find(x), find(y)
        if rx == ry:
            return False  # same component → would form a cycle
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    sorted_edges = sorted(edges, key=lambda e: e[2])
    total_cost = 0
    mst_edges: List[Tuple[int, int, int]] = []
    for u, v, w in sorted_edges:
        if union(u, v):
            total_cost += w
            mst_edges.append((u, v, w))
            if len(mst_edges) == n - 1:
                break  # MST complete
    return total_cost, mst_edges


# ---------------------------------------------------------------------------
# Prim's algorithm
# ---------------------------------------------------------------------------

def prim(n: int, adj: List[List[Tuple[int, int]]]) -> int:
    """Return total MST cost for a graph of n nodes (0-indexed).

    adj[u] = [(v, weight), ...]  adjacency list
    Heap-based: O((V + E) log V).
    """
    in_tree = [False] * n
    heap: List[Tuple[int, int]] = [(0, 0)]  # (cost, node); start from node 0
    total_cost = 0
    while heap:
        cost, u = heapq.heappop(heap)
        if in_tree[u]:
            continue  # stale entry
        in_tree[u] = True
        total_cost += cost
        for v, w in adj[u]:
            if not in_tree[v]:
                heapq.heappush(heap, (w, v))
    return total_cost


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Graph: 4 nodes (0=A, 1=B, 2=C, 3=D)
    # Edges: (A,B,1),(A,C,4),(B,C,2),(B,D,5),(C,D,3)
    edges = [(0, 1, 1), (0, 2, 4), (1, 2, 2), (1, 3, 5), (2, 3, 3)]

    cost_k, mst = kruskal(4, edges)
    assert cost_k == 6, f"Kruskal expected 6, got {cost_k}"
    assert len(mst) == 3, f"MST should have 3 edges, got {len(mst)}"

    adj: List[List[Tuple[int, int]]] = [[] for _ in range(4)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    cost_p = prim(4, adj)
    assert cost_p == 6, f"Prim expected 6, got {cost_p}"

    print("Smoke tests passed. Kruskal MST cost:", cost_k, "Prim MST cost:", cost_p)
```

**Template:**

```python
import heapq
from typing import List, Tuple


def kruskal(n: int, edges: List[Tuple[int, int, int]]) -> Tuple[int, List]:
    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> bool:
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    total_cost = 0
    mst_edges: List[Tuple[int, int, int]] = []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if union(u, v):
            total_cost += w
            mst_edges.append((u, v, w))
            if len(mst_edges) == n - 1:
                break
    return total_cost, mst_edges


def prim(n: int, adj: List[List[Tuple[int, int]]]) -> int:
    in_tree = [False] * n
    heap: List[Tuple[int, int]] = [(0, 0)]
    total_cost = 0
    while heap:
        cost, u = heapq.heappop(heap)
        if in_tree[u]:
            continue
        in_tree[u] = True
        total_cost += cost
        for v, w in adj[u]:
            if not in_tree[v]:
                heapq.heappush(heap, (w, v))
    return total_cost
```

## 5. Variants & pitfalls

### Variants

- **Borůvka's algorithm:** Each component simultaneously picks its cheapest outgoing edge; merge and repeat. O(E log V) like Kruskal but parallelism-friendly — used in parallel MST implementations.
- **MST with a mandatory edge:** Force-include the required edge (union its endpoints), then run Kruskal/Prim on the remaining graph. Correct because the mandatory edge is part of the cut it crosses.
- **Maximum spanning tree:** Reverse the sort order in Kruskal (descending weight) or flip the heap comparison in Prim. Everything else stays identical.
- **MST on a complete graph (Prim with adjacency matrix):** When E ≈ V², scanning the full matrix row-by-row for the minimum crossing edge costs O(V²) overall — asymptotically better than Kruskal's O(E log E ≈ V² log V).

### Pitfalls

- **Forgetting to sort in Kruskal:** If edges are not sorted by weight the greedy choice is wrong and the result is not an MST.
- **Tracking visited in Prim:** Without `in_tree`, each node can be added multiple times and the cost will be overcounted. Always skip stale heap entries.
- **Kruskal on dense graphs:** For E ≈ V², Kruskal is O(V² log V) while the O(V²) Prim scan wins by a log factor. Choose Prim for dense graphs.
- **Disconnected graphs:** Kruskal naturally produces a minimum spanning **forest** (one tree per connected component). Prim started from one node will not reach other components — restart Prim for each unvisited node to handle forest cases.
- **Directed graphs:** MST algorithms assume undirected graphs. For directed graphs the analogous problem is **Minimum Spanning Arborescence**, solved by Edmonds' algorithm (much harder).

## 6. Complexity

- **Time (Kruskal):** O(E log E) = O(E log V) — sorting edges dominates; union-find operations are near O(1) amortized.
- **Time (Prim, binary heap):** O((V + E) log V) — each edge is pushed to the heap at most twice; each pop is O(log V).
- **Time (Prim, adjacency matrix):** O(V²) — linear scan per node; optimal for dense graphs where E ≈ V².
- **Space:** O(V + E) for adjacency list and heap; O(V) for union-find.

## 7. Problem set

- [Medium] [Connecting Cities With Minimum Cost](https://leetcode.com/problems/connecting-cities-with-minimum-cost/) — direct MST application; straightforward Kruskal or Prim.
- [Medium] [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) — complete graph with Manhattan-distance edges; Prim's O(V²) scan is ideal since E = O(V²).
- [Hard] [Optimize Water Distribution in a Village](https://leetcode.com/problems/optimize-water-distribution-in-a-village/) — adds a virtual node for well-digging costs; reduces to MST after the modeling insight.
- [Hard] [Minimum Cost to Make at Least One Valid Path in a Grid](https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/) — 0-1 BFS or Dijkstra variant; tests weighted shortest-path intuition adjacent to MST thinking.

## 8. Related patterns

- [Union-Find](../graphs/union-find.md) — Kruskal's primary cycle-detection tool; MST is the canonical union-find application.
- [Shortest Paths (Dijkstra)](../graphs/shortest-paths.md) — different problem: SSSP finds cheapest path from one source, MST connects all nodes at minimum total cost; Prim's structure resembles Dijkstra but the heap key is edge weight, not cumulative distance.
- [BFS](../graphs/bfs.md) — BFS gives unweighted shortest paths; MST uses weighted edges and a different objective.

## 9. Interviewer follow-ups

**Q: Would you pick Kruskal or Prim for a dense graph (E ≈ V²)?**
Prim with an adjacency-matrix scan: iterate over all V non-tree nodes each step, picking the minimum crossing edge directly. Total work is O(V²) — no heap overhead. Kruskal's sort alone costs O(E log E ≈ V² log V), so the adjacency-matrix Prim beats it by a log factor on dense inputs.

**Q: What if the graph has multiple connected components?**
Kruskal handles it naturally: the algorithm runs to completion and the result is a minimum spanning **forest** — one tree per component. With Prim you must restart from an unvisited node after each tree is complete; the union of those trees is the same minimum spanning forest.
