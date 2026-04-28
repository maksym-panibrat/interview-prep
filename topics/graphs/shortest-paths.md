# Shortest Paths (Dijkstra)

## 1. TL;DR

Dijkstra's algorithm finds the shortest path from a source to all other nodes in a **weighted graph with non-negative edge weights**. The signal is "shortest path with weights," "minimum cost to traverse," or any weighted-graph distance question where edges are non-negative. A min-heap processes the closest unsettled node first; each node is settled at most once, giving O((V + E) log V) with a binary heap. For negative edges use **Bellman-Ford** (O(VE)); for all-pairs distances on small dense graphs use **Floyd-Warshall** (O(V³)). Space: O(V + E).

## 2. Intuition

Imagine a city road network where each road has a travel time. You want the fastest route from downtown to the airport. A greedy strategy works: always extend the route with the cheapest unsettled city. Why? Once you commit to the cheapest city, you know no path through any other unsettled city can improve on it — every unsettled city is at least as far away, and edge weights are non-negative, so adding more edges cannot decrease the total distance. The closest city's distance is therefore final.

This is Dijkstra in one sentence: *greedily settle nodes in order of increasing tentative distance, using a min-heap to find the next cheapest node efficiently.*

The heap key is the current best known distance `dist[u]`. When you pop `(d, u)`, if `d > dist[u]` the entry is stale (a shorter path was found later) — skip it. This lazy deletion avoids the need for a decrease-key operation.

Contrast with BFS: BFS works when all edge weights are 1 (or 0). Dijkstra generalizes BFS to arbitrary non-negative weights by replacing the FIFO queue with a min-heap. When all weights are 0 or 1, use 0-1 BFS (deque) for O(V + E) instead of Dijkstra's O((V + E) log V).

## 3. Walkthrough

Weighted graph: `0—1 (4), 0—2 (1), 2—1 (2), 1—3 (1), 2—3 (5)`.

```
Adjacency list (node: [(neighbor, weight)]):
  0: [(1, 4), (2, 1)]
  1: [(0, 4), (2, 2), (3, 1)]
  2: [(0, 1), (1, 2), (3, 5)]
  3: [(1, 1), (2, 5)]
```

Start: source = 0. Initialize `dist = [0, ∞, ∞, ∞]`, heap = `[(0, 0)]`.

```
Pop (0, 0):  d=0, node=0  → dist[0]=0 (settled)
  Relax neighbor 1: dist[1] = min(∞, 0+4) = 4  → push (4, 1)
  Relax neighbor 2: dist[2] = min(∞, 0+1) = 1  → push (1, 2)
  heap = [(1,2), (4,1)]
  dist = [0, 4, 1, ∞]

Pop (1, 2):  d=1, node=2  → dist[2]=1 (settled)
  Relax neighbor 0: dist[0] = min(0, 1+1) = 0  → no improvement
  Relax neighbor 1: dist[1] = min(4, 1+2) = 3  → push (3, 1)
  Relax neighbor 3: dist[3] = min(∞, 1+5) = 6  → push (6, 3)
  heap = [(3,1), (4,1), (6,3)]
  dist = [0, 3, 1, 6]

Pop (3, 1):  d=3, node=1  → dist[1]=3 (settled)
  Relax neighbor 0: dist[0] = min(0, 3+4) = 0  → no improvement
  Relax neighbor 2: dist[2] = min(1, 3+2) = 1  → no improvement
  Relax neighbor 3: dist[3] = min(6, 3+1) = 4  → push (4, 3)
  heap = [(4,1), (4,3), (6,3)]
  dist = [0, 3, 1, 4]

Pop (4, 1):  d=4 > dist[1]=3  → STALE, skip

Pop (4, 3):  d=4, node=3  → dist[3]=4 (settled)
  All neighbors already settled or not improved.
  heap = [(6,3)]

Pop (6, 3):  d=6 > dist[3]=4  → STALE, skip
  heap empty → done
```

Final distances from source 0: `dist = [0, 3, 1, 4]`.

Path reconstruction: 0→2→1→3 (cost 1+2+1=4).

## 4. Implementation

```python
from __future__ import annotations
import heapq
from typing import Dict, List, Optional, Tuple


def dijkstra(graph: Dict[int, List[Tuple[int, int]]], src: int) -> Dict[int, float]:
    """Return shortest distances from src to all reachable nodes.

    graph: adjacency list {node: [(neighbor, weight), ...]}
    Uses lazy deletion to avoid decrease-key: stale heap entries are skipped.
    Time: O((V + E) log V).  Space: O(V + E).
    """
    dist: Dict[int, float] = {src: 0.0}
    # Min-heap entries: (distance, node)
    heap: List[Tuple[float, int]] = [(0.0, src)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue  # stale entry — a shorter path was already found

        for v, w in graph.get(u, []):
            new_dist = d + w
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    return dist


def dijkstra_with_path(
    graph: Dict[int, List[Tuple[int, int]]], src: int, dst: int
) -> Tuple[float, Optional[List[int]]]:
    """Return (shortest distance, path) from src to dst.

    Path is a list of nodes from src to dst (inclusive).
    Returns (inf, None) if dst is unreachable.
    """
    dist: Dict[int, float] = {src: 0.0}
    prev: Dict[int, Optional[int]] = {src: None}   # predecessor map for path reconstruction
    heap: List[Tuple[float, int]] = [(0.0, src)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue

        if u == dst:
            break  # early exit once destination is settled

        for v, w in graph.get(u, []):
            new_dist = d + w
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(heap, (new_dist, v))

    if dst not in dist:
        return (float("inf"), None)

    # Reconstruct path by following predecessor map backwards.
    path: List[int] = []
    node: Optional[int] = dst
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return (dist[dst], path)


if __name__ == "__main__":
    # Graph: 0-1 (4), 0-2 (1), 2-1 (2), 1-3 (1), 2-3 (5)
    g: Dict[int, List[Tuple[int, int]]] = {
        0: [(1, 4), (2, 1)],
        1: [(0, 4), (2, 2), (3, 1)],
        2: [(0, 1), (1, 2), (3, 5)],
        3: [(1, 1), (2, 5)],
    }

    dist = dijkstra(g, 0)
    assert dist[0] == 0
    assert dist[1] == 3   # 0→2→1, cost 1+2=3
    assert dist[2] == 1   # 0→2, cost 1
    assert dist[3] == 4   # 0→2→1→3, cost 1+2+1=4

    # Path reconstruction
    d, path = dijkstra_with_path(g, 0, 3)
    assert d == 4
    assert path == [0, 2, 1, 3]

    # Unreachable node
    d2, path2 = dijkstra_with_path(g, 0, 99)
    assert d2 == float("inf")
    assert path2 is None

    print("All smoke tests passed.")
```

**Template:**

```python
import heapq
from typing import Dict, List, Optional, Tuple


def dijkstra(graph: Dict[int, List[Tuple[int, int]]], src: int) -> Dict[int, float]:
    dist: Dict[int, float] = {src: 0.0}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def dijkstra_with_path(
    graph: Dict[int, List[Tuple[int, int]]], src: int, dst: int
) -> Tuple[float, Optional[List[int]]]:
    dist: Dict[int, float] = {src: 0.0}
    prev: Dict[int, Optional[int]] = {src: None}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u == dst:
            break
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if dst not in dist:
        return (float("inf"), None)
    path: List[int] = []
    node: Optional[int] = dst
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return (dist[dst], path)
```

## 5. Variants & pitfalls

### Dijkstra (the workhorse)

Use when edges have non-negative weights and you need single-source shortest paths. Lazy deletion with a binary heap is the standard interview implementation. A Fibonacci heap gives O(E + V log V) — the theoretical improvement is rarely needed in practice.

### Bellman-Ford (name-drop)

O(VE) time; handles negative edge weights. Relax all edges V−1 times; if a V-th relaxation still reduces a distance, a negative cycle exists. Use when the graph has negative weights or when you need to detect negative cycles.

### Floyd-Warshall (name-drop)

O(V³) time, O(V²) space. Computes shortest paths between **all pairs** of nodes via DP: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])` for each intermediate node k. Practical only for small dense graphs (V ≤ 500 or so in interviews).

### A\* (forward-link)

Dijkstra + an admissible heuristic h(u) (lower bound on remaining distance to goal). The heap priority becomes `g(u) + h(u)` instead of just `g(u)`. When the heuristic is zero, A\* degenerates to Dijkstra. See `../nice-to-have/a-star.md` (does not exist yet) for details.

### K-shortest paths / Cheapest Flights with K Stops

Modify Dijkstra to allow settling a node up to k+1 times instead of once. Each settlement corresponds to a path using a different number of intermediate hops. This handles problems where you can take at most k stops (LC 787).

### 0-1 BFS

When edge weights are only 0 or 1, replace the heap with a deque: push weight-0 neighbors to the front, weight-1 neighbors to the back. This runs in O(V + E) — faster than Dijkstra's O((V + E) log V).

### Pitfalls

- **Negative edge weights**: Dijkstra is incorrect with negative edges. The greedy argument breaks down because a longer path through a negative edge could be cheaper than the currently settled minimum. Use Bellman-Ford.
- **Missing the staleness check**: without `if d > dist[u]: continue`, the same node is processed multiple times, giving wrong answers and O(E log E) or worse performance. This one-liner is non-negotiable.
- **Using `dist[u]` as a visited set**: unlike BFS, Dijkstra can push the same node multiple times with different distances. Using a `visited` set instead of the staleness check is equivalent but forces you to be careful about when to add to it (at settlement, not enqueue time).

## 6. Complexity

- **Dijkstra (binary heap):** O((V + E) log V) time — each node is popped at most once (O(V log V) heap pops), and each edge triggers at most one heap push (O(E log V) total). O(V + E) space for the graph, O(V) for `dist` and heap.
- **Dijkstra (Fibonacci heap):** O(E + V log V) time — decrease-key is O(1) amortized; rarely needed in practice.
- **Bellman-Ford:** O(VE) time, O(V) space.
- **Floyd-Warshall:** O(V³) time, O(V²) space.

## 7. Problem set

- [Medium] [Network Delay Time](https://leetcode.com/problems/network-delay-time/) — single-source Dijkstra; answer is `max(dist.values())` or -1 if any node is unreachable.
- [Medium] [Path with Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/) — Dijkstra on a grid; edge weight is the height difference; classic "minimize the maximum along the path."
- [Medium] [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) — Bellman-Ford with exactly K relaxation rounds, or modified Dijkstra tracking (cost, stops).
- [Medium] [Path with Maximum Probability](https://leetcode.com/problems/path-with-maximum-probability/) — Dijkstra with a max-heap; probability product instead of cost sum (negate or use max-heap).
- [Medium] [Number of Ways to Arrive at Destination](https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/) — Dijkstra augmented with a `count[]` array; increment count when a new shortest path is found.
- [Hard] [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) — Dijkstra on a grid; edge weight is the max elevation encountered; minimize the maximum along the path.
- [Hard] [The Maze II](https://leetcode.com/problems/the-maze-ii/) — Dijkstra where edge weights are the number of steps a ball rolls before hitting a wall.
- [Hard] [Minimum Cost to Make at Least One Valid Path in a Grid](https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/) — 0-1 BFS: following the existing direction costs 0, redirecting costs 1.

## 8. Related patterns

- **[BFS](bfs.md)** — BFS is Dijkstra with all edge weights equal to 1; the FIFO queue is equivalent to a min-heap when all priorities are identical. For 0/1 weights use 0-1 BFS (deque) instead of a full heap.
- **[Union-Find](union-find.md)** — answers a different question: "are A and B connected?" without computing distances; Kruskal's MST uses Union-Find alongside edge sorting.
- **A\*** (file at `../nice-to-have/a-star.md` — does not exist yet): Dijkstra guided by an admissible heuristic; dramatically faster for point-to-point shortest paths in spatial graphs.

## 9. Interviewer follow-ups

**Q: What if the graph has negative edge weights?**
Dijkstra fails — the greedy settlement argument breaks down because a negative-weight edge could make a longer (in edge count) path cheaper than the already-settled minimum. Use **Bellman-Ford**: relax every edge V−1 times. If a V-th iteration still relaxes any distance, a negative cycle exists and no shortest path is well-defined. Time O(VE).

**Q: What if you need all-pairs shortest paths?**
Use **Floyd-Warshall**: a 3-nested-loop DP over all pairs `(i, j)` and intermediate node `k`. `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`. Time O(V³), space O(V²). Practical for V ≤ 500. For sparse large graphs, run Dijkstra once from each node: O(V(V + E) log V) total — better than Floyd-Warshall when E << V².

**Q: What is the Fibonacci heap bound, and why don't people use it?**
With a Fibonacci heap, decrease-key is O(1) amortized, giving Dijkstra a total time of O(E + V log V) — better than O((V + E) log V) for dense graphs where E > V log V. In practice, Fibonacci heaps have large constants and poor cache behavior, so binary-heap Dijkstra is almost always faster on real inputs. The improvement is asymptotically relevant only for extremely dense graphs (E ≈ V²) which rarely appear in competitive programming or system design.
