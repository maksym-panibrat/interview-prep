# BFS

## 1. TL;DR

BFS (Breadth-First Search) is the go-to algorithm for **shortest path in an unweighted graph**, level-order traversal, and "minimum steps to reach a state" problems. The signal is "shortest path," "minimum steps/moves," "level-order," grid problems where each cell-to-cell move costs 1, or state-space problems like word ladder and open-the-lock. Key property: FIFO queue ensures the first time you reach a node, you've taken the fewest edges. Time: O(V + E). Space: O(V).

## 2. Intuition

Imagine dropping a stone in a pond. The ripple expands outward in a perfect ring — every point exactly distance 1 from the center is hit before any point at distance 2. BFS works the same way: it processes every node at depth d before touching any node at depth d + 1.

The correctness argument is simple: when you dequeue a node u at distance d, every path to u via the queue was already processed — no shorter path can arrive later, because shorter paths would have been enqueued earlier and already dequeued. This is only true for **unweighted** edges (or unit-weight edges). Once edges have different weights, BFS can miss a cheaper path that arrives via a longer chain of edges; that is Dijkstra's territory.

The key mechanical insight: **mark a node visited at enqueue time, not dequeue time**. If you delay until dequeue, the same node can be enqueued multiple times before it is processed, causing redundant work that can blow up to O(V·E) in dense graphs.

## 3. Walkthrough

### Graph BFS: shortest distances from node 0

Graph edges: `0—1, 0—2, 1—3, 2—3, 3—4`.

```
Adjacency list:
  0: [1, 2]
  1: [0, 3]
  2: [0, 3]
  3: [1, 2, 4]
  4: [3]
```

Start: node 0. Track `queue`, `visited`, and `dist[]`.

```
Initial:  visited = {0},  dist = [0, ∞, ∞, ∞, ∞],  queue = deque([0])

Step 1 — dequeue 0:
  neighbors: 1, 2  (both unvisited)
  enqueue 1, enqueue 2  → visited = {0,1,2},  dist = [0,1,1,∞,∞]
  queue = deque([1, 2])

Step 2 — dequeue 1:
  neighbors: 0 (visited), 3 (unvisited)
  enqueue 3  → visited = {0,1,2,3},  dist = [0,1,1,2,∞]
  queue = deque([2, 3])

Step 3 — dequeue 2:
  neighbors: 0 (visited), 3 (visited)
  nothing new
  queue = deque([3])

Step 4 — dequeue 3:
  neighbors: 1 (visited), 2 (visited), 4 (unvisited)
  enqueue 4  → visited = {0,1,2,3,4},  dist = [0,1,1,2,3]
  queue = deque([4])

Step 5 — dequeue 4:
  neighbors: 3 (visited)
  queue empty → done
```

Final distances: `[0, 1, 1, 2, 3]`. Nodes 1 and 2 are one hop away; node 3 is two hops; node 4 is three hops.

### Multi-source grid BFS (01 Matrix style)

Grid (0 = zero-cell, 1 = one-cell). Goal: for every cell, find the distance to the nearest 0.

```
Input:                  Output:
  0 0 0                   0 0 0
  0 1 0          →        0 1 0
  1 1 1                   1 2 1
```

Algorithm: seed the queue with all zero-cells at distance 0. Then BFS outward, assigning `dist[r][c] = dist[parent] + 1` to each unvisited cell.

```
Seed all zeros → queue = [(0,0), (0,1), (0,2), (1,0), (1,2)]
dist:
  0 0 0
  0 ∞ 0
  ∞ ∞ ∞

Process (0,0): neighbors (0,1) visited, (1,0) visited → nothing
Process (0,1): neighbors all visited → nothing
Process (0,2): neighbors all visited → nothing
Process (1,0): neighbors (0,0) visited, (1,1) unvisited, (2,0) unvisited
  → dist[1][1] = 1,  dist[2][0] = 1
dist:
  0 0 0
  0 1 0
  1 ∞ ∞
Process (1,2): neighbors (0,2) visited, (1,1) visited, (2,2) unvisited
  → dist[2][2] = 1
dist:
  0 0 0
  0 1 0
  1 ∞ 1
Process (1,1): neighbors (0,1) visited, (1,0) visited, (1,2) visited, (2,1) unvisited
  → dist[2][1] = 2
dist:
  0 0 0
  0 1 0
  1 2 1    ← final answer
```

## 4. Implementation

```python
from __future__ import annotations
from collections import deque
from typing import Dict, List, Optional, Set, Tuple


def bfs_shortest_path(
    graph: Dict[int, List[int]], src: int, dst: int
) -> int:
    """Return the shortest distance (in edges) from src to dst.

    Returns -1 if dst is unreachable.
    graph is an adjacency list: {node: [neighbor, ...]}.
    """
    if src == dst:
        return 0
    visited: Set[int] = {src}
    queue: deque[Tuple[int, int]] = deque([(src, 0)])
    while queue:
        node, dist = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == dst:
                return dist + 1
            if neighbor not in visited:
                visited.add(neighbor)   # mark at enqueue time — critical
                queue.append((neighbor, dist + 1))
    return -1


def bfs_grid(grid: List[List[int]], sources: List[Tuple[int, int]]) -> List[List[int]]:
    """Multi-source BFS on a grid.

    Returns a dist grid where dist[r][c] is the minimum steps from the nearest source.
    Cells with value 0 in `grid` are treated as sources; others are targets.
    (01 Matrix / Walls and Gates style.)
    """
    rows, cols = len(grid), len(grid[0])
    INF = float("inf")
    dist: List[List[float]] = [[INF] * cols for _ in range(rows)]
    queue: deque[Tuple[int, int]] = deque()
    for r, c in sources:
        dist[r][c] = 0
        queue.append((r, c))
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == INF:
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return [[int(d) if d != INF else -1 for d in row] for row in dist]


def bidirectional_bfs(
    graph: Dict[int, List[int]], src: int, dst: int
) -> int:
    """Bidirectional BFS: expand from both ends and meet in the middle.

    Returns the shortest distance, or -1 if unreachable.
    Works only on undirected graphs (or directed graphs with a reverse adjacency list).
    Halves the frontier size compared to single-direction BFS: O(b^(d/2)) vs O(b^d).
    """
    if src == dst:
        return 0
    front: Set[int] = {src}
    back: Set[int] = {dst}
    visited_front: Dict[int, int] = {src: 0}
    visited_back: Dict[int, int] = {dst: 0}
    dist = 0
    while front and back:
        dist += 1
        # Always expand the smaller frontier to keep them balanced.
        if len(front) > len(back):
            front, back = back, front
            visited_front, visited_back = visited_back, visited_front
        next_front: Set[int] = set()
        for node in front:
            for neighbor in graph.get(node, []):
                if neighbor in visited_back:
                    return dist + visited_back[neighbor]
                if neighbor not in visited_front:
                    visited_front[neighbor] = dist
                    next_front.add(neighbor)
        front = next_front
    return -1


if __name__ == "__main__":
    # Graph: 0-1, 0-2, 1-3, 2-3, 3-4
    g: Dict[int, List[int]] = {
        0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3]
    }
    assert bfs_shortest_path(g, 0, 4) == 3
    assert bfs_shortest_path(g, 0, 1) == 1
    assert bfs_shortest_path(g, 0, 3) == 2
    assert bfs_shortest_path(g, 0, 0) == 0
    assert bfs_shortest_path(g, 4, 0) == 3

    # Multi-source grid BFS (01 Matrix example)
    grid = [[0, 0, 0], [0, 1, 0], [1, 1, 1]]
    sources = [(r, c) for r in range(3) for c in range(3) if grid[r][c] == 0]
    result = bfs_grid(grid, sources)
    assert result == [[0, 0, 0], [0, 1, 0], [1, 2, 1]]

    # Bidirectional BFS
    assert bidirectional_bfs(g, 0, 4) == 3
    assert bidirectional_bfs(g, 0, 0) == 0

    print("All smoke tests passed.")
```

**Template:**

```python
from collections import deque
from typing import Dict, List, Set, Tuple


def bfs_shortest_path(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    visited: Set[int] = {src}
    queue: deque = deque([(src, 0)])
    while queue:
        node, dist = queue.popleft()
        for nb in graph.get(node, []):
            if nb == dst:
                return dist + 1
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, dist + 1))
    return -1


def bfs_grid(grid: List[List[int]], sources: List[Tuple[int, int]]) -> List[List[int]]:
    rows, cols = len(grid), len(grid[0])
    dist = [[float("inf")] * cols for _ in range(rows)]
    queue: deque = deque()
    for r, c in sources:
        dist[r][c] = 0
        queue.append((r, c))
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        pass  # inline below
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == float("inf"):
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return [[int(d) if d != float("inf") else -1 for d in row] for row in dist]


def bidirectional_bfs(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    front, back = {src}, {dst}
    vf, vb = {src: 0}, {dst: 0}
    d = 0
    while front and back:
        d += 1
        if len(front) > len(back):
            front, back, vf, vb = back, front, vb, vf
        nxt: Set[int] = set()
        for node in front:
            for nb in graph.get(node, []):
                if nb in vb:
                    return d + vb[nb]
                if nb not in vf:
                    vf[nb] = d
                    nxt.add(nb)
        front = nxt
    return -1
```

## 5. Variants & pitfalls

### Graph BFS (adjacency list)

The standard form. Build an adjacency list, seed the queue with source(s), mark visited at enqueue time, and propagate distances or parents.

### Grid BFS (4-direction or 8-direction)

Treat each cell `(r, c)` as a node; neighbors are the 4 (or 8) adjacent in-bounds cells. The queue holds `(row, col)` tuples. Guard: `0 <= nr < rows and 0 <= nc < cols`. Mark a cell visited the moment it is added to the queue, not when it is popped.

### Multi-source BFS

Pre-load the queue with all source cells (distance 0) before starting the main loop. This lets BFS compute the nearest-source distance for every cell in one pass — the same O(V + E) as single-source BFS. Classic problems: Rotting Oranges, Walls and Gates, 01 Matrix.

### 0-1 BFS

For graphs where edge weights are 0 or 1, use a `deque` instead of a plain queue. For a weight-0 edge, push to the **front** of the deque (`appendleft`); for a weight-1 edge, push to the **back** (`append`). This preserves the distance ordering without a heap, running in O(V + E) instead of Dijkstra's O((V + E) log V).

### Bidirectional BFS

Launch BFS simultaneously from both `src` and `dst`. Expand the smaller frontier each round. The search terminates as soon as the two frontiers meet. This cuts the maximum frontier radius from d to d/2, reducing work from O(b^d) to O(b^(d/2)) — a dramatic speedup when d is large and the branching factor b > 1. Useful for word ladder with a large dictionary, or any search where the answer is far away.

### Pitfalls

- **Marking visited at dequeue time**: the classic off-by-one error. A node can be added to the queue multiple times before it is processed, causing O(V·E) blow-up on dense graphs. Always `visited.add(node)` **before** `queue.append(node)`.
- **Forgetting to mark the start node visited**: if you do not add `src` to `visited` at initialization, it can be re-enqueued by one of its own neighbors.
- **Using BFS on weighted graphs**: BFS only finds shortest paths when all edges have equal cost. For weighted graphs, use Dijkstra (min-heap) or Bellman-Ford.
- **Forgetting bounds checks in grid BFS**: `nr, nc` must be checked before accessing `dist[nr][nc]`.

## 6. Complexity

- **Time:** O(V + E) — each vertex is enqueued at most once (marked at enqueue time); each edge is inspected at most twice (once from each endpoint in an undirected graph).
- **Space:** O(V) — the `visited` set and the queue together hold at most V entries.

## 7. Problem set

- [Easy] [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) — purest BFS form on a tree; no cycle risk, just practice the level-grouping pattern.
- [Medium] [Number of Islands](https://leetcode.com/problems/number-of-islands/) — count connected components via BFS flood-fill; good for grid-BFS muscle memory.
- [Medium] [01 Matrix](https://leetcode.com/problems/01-matrix/) — multi-source BFS from all zeros simultaneously; the canonical example of seeding multiple sources at once.
- [Medium] [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) — multi-source BFS with an answer derived from the final distance; also tests the "all cells reachable?" check.
- [Medium] [Walls and Gates](https://leetcode.com/problems/walls-and-gates/) — multi-source BFS from all gates; identical structure to 01 Matrix with different labels.
- [Medium] [Open the Lock](https://leetcode.com/problems/open-the-lock/) — BFS over a state space (4-digit combination); enumerating neighbors is the challenge, not the BFS itself.
- [Medium] [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) — 8-direction grid BFS; also handles impossible cases.
- [Hard] [Word Ladder](https://leetcode.com/problems/word-ladder/) — BFS over a word state space with implicit graph construction; use bidirectional BFS for large dictionaries.
- [Hard] [Word Ladder II](https://leetcode.com/problems/word-ladder-ii/) — all shortest transformation sequences; BFS to find level distances, DFS/backtrack to reconstruct all paths.
- [Hard] [Bus Routes](https://leetcode.com/problems/bus-routes/) — BFS where nodes are bus routes, not stops; the graph construction trick is the hard part.
- [Hard] [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) — BFS over bitmask states `(node, visited_mask)`; combines BFS with bitmask DP state encoding.

## 8. Related patterns

- **[DFS](dfs.md)** — DFS explores as deep as possible before backtracking; use it for connectivity, cycle detection, and problems with a natural recursive structure. BFS is the right choice when you need the shortest path.
- **[Topological Sort](topological-sort.md)** — Kahn's algorithm is BFS on a DAG, peeling nodes with in-degree 0 level by level.
- **[Shortest Paths / Dijkstra](shortest-paths.md)** — Dijkstra = BFS with a min-heap to handle non-uniform edge weights; when all weights are 1, Dijkstra degenerates to BFS.
- **[Bitmask DP](../dp/bitmask-dp.md)** — BFS over bitmask states models TSP-style "visit all nodes" problems (see Shortest Path Visiting All Nodes).

## 9. Interviewer follow-ups

**Q: BFS or DFS for this problem — and why?**
BFS guarantees the shortest path in unweighted graphs because it explores nodes in non-decreasing distance order; once a node is reached, that distance is minimal. DFS gives no such guarantee — it may find a long path before a short one. Use DFS when you need to explore all possibilities (connected components, cycle detection, path enumeration) and distance minimality is not required, or when the problem has a natural recursive / tree-shaped structure.

**Q: What if the graph is infinite (e.g., word ladder with an unbounded vocabulary)?**
Bidirectional BFS: launch from both the start word and the end word simultaneously, expanding the smaller frontier each step. The two frontiers meet at depth d/2 each instead of one frontier reaching depth d. Because BFS frontier size grows as b^d (branching factor b), this reduces work from O(b^d) to O(b^(d/2)) — effectively squaring the tractable depth. For a branching factor of 26 (English alphabet) and answer distance 10, single-direction BFS explores ~26^10 ≈ 1.4 × 10^14 nodes; bidirectional explores only ~2 × 26^5 ≈ 24 million.
