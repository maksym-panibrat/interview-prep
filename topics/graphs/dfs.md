# DFS

## 1. TL;DR

DFS (Depth-First Search) is the workhorse for **connected components**, **cycle detection**, **path enumeration**, and any problem with a natural recursive decomposition on a graph. The signal is "connected components," "find all paths," "detect cycle," "explore everything reachable," or problems where the problem tree mirrors the call stack. Key insight: stack-based exploration goes as deep as possible before backtracking; post-order discovery (finish time) is the reverse of topological order. Time: O(V + E). Space: O(V) for the recursion stack.

## 2. Intuition

Imagine exploring a maze by always taking the first unexplored corridor you see. You walk deep into the maze, marking every junction you visit. When you hit a dead end or a visited junction, you backtrack to the last junction with an unexplored corridor and try that. DFS is that exploration strategy: the call stack (or explicit stack) remembers exactly where to backtrack to.

The critical distinction from BFS: DFS is LIFO (last in, first out), so it dives deep before going wide. This means it finds *a* path quickly, but not necessarily the *shortest* path. On the other hand, DFS naturally enumerates all paths, detects cycles, and computes finish times that encode topological order — things BFS cannot do in one pass.

Two DFS discovery orderings matter:
- **Pre-order**: process a node when first entered (before any neighbor). Used for reachability and path tracing.
- **Post-order**: process a node when fully finished (after all neighbors). Post-order reversed = topological order for DAGs.

## 3. Walkthrough

### Recursive DFS pre-order: graph 0—1, 0—2, 1—3, 2—3, 3—4

```
Adjacency list:
  0: [1, 2]
  1: [0, 3]
  2: [0, 3]
  3: [1, 2, 4]
  4: [3]
```

Call tree (call frame shows which node is active; children are recursive calls):

```
dfs(0)  visited={0}
  dfs(1)  visited={0,1}
    skip 0 (visited)
    dfs(3)  visited={0,1,3}
      skip 1 (visited)
      dfs(2)  visited={0,1,2,3}
        skip 0 (visited)
        skip 3 (visited)
      ← return from dfs(2)
      dfs(4)  visited={0,1,2,3,4}
        skip 3 (visited)
      ← return from dfs(4)
    ← return from dfs(3)
  ← return from dfs(1)
  skip 2 (visited)
← return from dfs(0)

Pre-order visit sequence: 0, 1, 3, 2, 4
```

### Iterative DFS using an explicit stack (same graph)

```
stack = [0],  visited = {}

Pop 0:  visited={0},  push neighbors [1, 2] → stack=[1, 2]
Pop 2:  visited={0,2},  push unvisited neighbors [3] → stack=[1, 3]
Pop 3:  visited={0,2,3},  push unvisited neighbors [1, 4] → stack=[1, 1, 4]
Pop 4:  visited={0,2,3,4},  push unvisited neighbors [] → stack=[1, 1]
Pop 1:  visited={0,1,2,3,4},  push unvisited neighbors [] → stack=[1]
Pop 1:  already visited, skip → stack=[]
Done.

Visit sequence (iterative): 0, 2, 3, 4, 1
```

Note: iterative DFS order differs from recursive order because the stack reverses the adjacency list. Both are valid DFS traversals.

### Cycle detection in a directed graph: 3-color DFS on A→B, B→C, C→A

Three colors: WHITE (unvisited) = 0, GRAY (in current path) = 1, BLACK (done) = 2.

```
Adjacency list:  A:[B], B:[C], C:[A]
color = {A:0, B:0, C:0}

dfs(A):  color[A]=GRAY(1)
  dfs(B):  color[B]=GRAY(1)
    dfs(C):  color[C]=GRAY(1)
      neighbor A → color[A] == GRAY → BACK EDGE FOUND → cycle detected!
```

A back edge (edge to a GRAY ancestor in the current DFS path) is the signature of a cycle in a directed graph. If we never hit a GRAY neighbor, mark each node BLACK when we finish it. A WHITE→GRAY→BLACK sequence with no back edges = no cycle.

## 4. Implementation

```python
from __future__ import annotations
import sys
from typing import Dict, List, Optional, Set


def dfs_recursive(
    graph: Dict[int, List[int]], start: int, visited: Optional[Set[int]] = None
) -> List[int]:
    """Pre-order DFS from `start`. Returns nodes in visit order."""
    if visited is None:
        visited = set()
    visited.add(start)
    order = [start]
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            order.extend(dfs_recursive(graph, neighbor, visited))
    return order


def dfs_iterative(graph: Dict[int, List[int]], start: int) -> List[int]:
    """Iterative DFS using an explicit stack. Avoids Python recursion limit.

    Note: visit order may differ from recursive DFS because the stack reverses
    the neighbor list — both are valid depth-first orderings.
    """
    visited: Set[int] = set()
    stack = [start]
    order: List[int] = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        # Push neighbors in reverse so the first neighbor is processed first.
        for neighbor in reversed(graph.get(node, [])):
            if neighbor not in visited:
                stack.append(neighbor)
    return order


def has_cycle_directed(graph: Dict[int, List[int]]) -> bool:
    """Detect a cycle in a directed graph using 3-color DFS.

    WHITE=0: not yet visited.
    GRAY=1:  currently on the DFS stack (in-progress path).
    BLACK=2: fully processed.

    A back edge (neighbor is GRAY) means we found a cycle.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[int, int] = {node: WHITE for node in graph}
    # Add implicit nodes that appear as neighbors but not as keys.
    for neighbors in graph.values():
        for nb in neighbors:
            if nb not in color:
                color[nb] = WHITE

    def _dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:       # back edge → cycle
                return True
            if color[v] == WHITE and _dfs(v):
                return True
        color[u] = BLACK
        return False

    return any(_dfs(node) for node in list(color) if color[node] == WHITE)


def connected_components(graph: Dict[int, List[int]]) -> List[List[int]]:
    """Find all connected components of an undirected graph via DFS.

    Returns a list of components, each component a list of node ids.
    """
    visited: Set[int] = set()
    components: List[List[int]] = []
    all_nodes: Set[int] = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)

    for node in sorted(all_nodes):  # sorted for deterministic output
        if node not in visited:
            component: List[int] = []
            stack = [node]
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                component.append(u)
                for v in graph.get(u, []):
                    if v not in visited:
                        stack.append(v)
            components.append(sorted(component))
    return components


if __name__ == "__main__":
    # Undirected graph: 0-1, 0-2, 1-3, 2-3, 3-4
    g: Dict[int, List[int]] = {
        0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3]
    }

    rec_order = dfs_recursive(g, 0)
    assert set(rec_order) == {0, 1, 2, 3, 4}
    assert rec_order[0] == 0  # starts at source

    iter_order = dfs_iterative(g, 0)
    assert set(iter_order) == {0, 1, 2, 3, 4}

    # Connected components (one component for this graph)
    comps = connected_components(g)
    assert comps == [[0, 1, 2, 3, 4]]

    # Two-component graph: 0-1 and 2-3
    g2 = {0: [1], 1: [0], 2: [3], 3: [2]}
    comps2 = connected_components(g2)
    assert comps2 == [[0, 1], [2, 3]]

    # Directed graph with cycle: A→B, B→C, C→A
    directed_cycle = {0: [1], 1: [2], 2: [0]}
    assert has_cycle_directed(directed_cycle) is True

    # Directed DAG: 0→1, 0→2, 1→3
    dag = {0: [1, 2], 1: [3], 2: [], 3: []}
    assert has_cycle_directed(dag) is False

    print("All smoke tests passed.")
```

**Template:**

```python
import sys
from typing import Dict, List, Optional, Set


def dfs_recursive(graph: Dict[int, List[int]], start: int, visited: Optional[Set[int]] = None) -> List[int]:
    if visited is None:
        visited = set()
    visited.add(start)
    order = [start]
    for nb in graph.get(start, []):
        if nb not in visited:
            order.extend(dfs_recursive(graph, nb, visited))
    return order


def dfs_iterative(graph: Dict[int, List[int]], start: int) -> List[int]:
    visited: Set[int] = set()
    stack = [start]
    order: List[int] = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nb in reversed(graph.get(node, [])):
            if nb not in visited:
                stack.append(nb)
    return order


def has_cycle_directed(graph: Dict[int, List[int]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[int, int] = {}
    for u in graph:
        color[u] = WHITE
        for v in graph[u]:
            if v not in color:
                color[v] = WHITE

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    return any(dfs(n) for n in list(color) if color[n] == WHITE)


def connected_components(graph: Dict[int, List[int]]) -> List[List[int]]:
    visited: Set[int] = set()
    components: List[List[int]] = []
    all_nodes: Set[int] = set(graph.keys())
    for nbs in graph.values():
        all_nodes.update(nbs)
    for node in sorted(all_nodes):
        if node not in visited:
            comp: List[int] = []
            stack = [node]
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                comp.append(u)
                for v in graph.get(u, []):
                    if v not in visited:
                        stack.append(v)
            components.append(sorted(comp))
    return components
```

## 5. Variants & pitfalls

### Recursive vs iterative

Recursive DFS is cleaner and directly matches the call-stack mental model. Use it for graphs with at most ~10^3–10^4 nodes (Python's default recursion limit is 1 000; increase with `sys.setrecursionlimit(200_000)` for larger graphs). For ~10^5–10^6 nodes, convert to iterative using an explicit stack to avoid stack overflow.

### Pre-order vs post-order

Pre-order (process node on entry): used for reachability, path tracing, and marking connected components. Post-order (process node on exit, after all recursion returns): the reverse of post-order is a valid topological order for DAGs. Iterative DFS can compute post-order by pushing `(node, False)` initially and `(node, True)` before exploring neighbors — when you pop `True`, you are in post-order.

### Cycle detection: undirected vs directed

For **undirected** graphs: track parent. If a neighbor is visited and is not the immediate parent, you have a cycle. For **directed** graphs: use 3-color (WHITE/GRAY/BLACK). A back edge to a GRAY node is the cycle signal; a visited but BLACK node is fine (it is a cross or forward edge, not a back edge).

### SCC (strongly connected components)

Tarjan's algorithm and Kosaraju's algorithm both find SCCs in O(V + E). Both are based on DFS; Tarjan uses a single DFS with a low-link value; Kosaraju runs DFS twice (once on the original graph, once on the transpose, in reversed finish-time order). Name-drop these in interviews when asked about directed-graph decomposition.

### Mutate-restore pattern for grid backtracking

When counting distinct paths or enumerating solutions, DFS on a grid often modifies the cell (e.g., marking it as visited by setting `grid[r][c] = '#'`) and restores it after the recursive call. Forgetting to restore is a common bug that corrupts the grid for sibling recursive calls.

### Pitfalls

- **Python recursion limit**: `sys.setrecursionlimit` is needed for graphs with more than ~1 000 nodes. Alternatively, convert to iterative.
- **Shared-state bug in backtracking**: if you mutate the grid or a path list inside the recursive call, you must undo the mutation on the way back — otherwise sibling branches see corrupted state.
- **"Visited" semantics**: for reachability/component problems, once-visited is enough. For path-enumeration problems (e.g., all paths from A to B), you need to un-visit on return so the same node can appear in a different path.
- **Iterative DFS order**: because of stack reversal, iterative DFS visits neighbors in a different order than recursive DFS. Both are valid depth-first orderings, but they produce different traversal sequences.

## 6. Complexity

- **Time:** O(V + E) — each vertex is discovered at most once; each edge is inspected at most twice (once from each endpoint in an undirected graph).
- **Space:** O(V) — the recursion stack (or explicit stack) holds at most V frames in the worst case (a path graph). The `visited` set is also O(V).

## 7. Problem set

- [Easy] [Flood Fill](https://leetcode.com/problems/flood-fill/) — simplest DFS on a grid; change connected cells to a new color.
- [Medium] [Number of Islands](https://leetcode.com/problems/number-of-islands/) — count connected components via DFS flood-fill; canonical component-counting problem.
- [Medium] [Max Area of Island](https://leetcode.com/problems/max-area-of-island/) — DFS while accumulating component size; teaches the "count during traversal" pattern.
- [Medium] [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) — DFS from the border to mark safe cells; flips the intuition (start from outside, not inside).
- [Medium] [Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/) — reverse DFS from each ocean; intersection of reachable sets is the answer.
- [Medium] [Course Schedule](https://leetcode.com/problems/course-schedule/) — directed cycle detection via 3-color DFS; direct application of `has_cycle_directed`.
- [Medium] [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) — count connected components in an adjacency matrix; swap adjacency-list DFS with row indexing.
- [Medium] [Clone Graph](https://leetcode.com/problems/clone-graph/) — DFS with a node-to-clone mapping; tests the "build while you traverse" pattern.
- [Medium] [Keys and Rooms](https://leetcode.com/problems/keys-and-rooms/) — DFS where keys unlock new neighbors; pure reachability check.
- [Hard] [Longest Increasing Path in a Matrix](https://leetcode.com/problems/longest-increasing-path-in-a-matrix/) — DFS with memoization; the DAG structure (strictly increasing) guarantees no cycles so caching is safe.
- [Hard] [Reconstruct Itinerary](https://leetcode.com/problems/reconstruct-itinerary/) — Hierholzer's algorithm / DFS post-order to find an Eulerian path; visit edges, not vertices.
- [Hard] [Critical Connections in a Network](https://leetcode.com/problems/critical-connections-in-a-network/) — Tarjan's bridge-finding algorithm; uses DFS discovery time and low-link values.

## 8. Related patterns

- **[BFS](bfs.md)** — BFS uses a queue (FIFO) instead of a stack (LIFO) and guarantees shortest-path distance; DFS is better for exhaustive exploration and cycle detection.
- **Topological Sort** (file at `topological-sort.md` — will exist after Task 12): DFS post-order reversed is a valid topological order for DAGs.
- **Union-Find** (file at `union-find.md` — will exist after Task 13): an alternative for static connected-component queries; faster per-query amortized, but cannot enumerate the component.
- **Grid Backtracking** (file at `../backtracking/grid-search.md` — does not exist yet): DFS with mutate-restore on a grid; the explicit backtracking variant of grid DFS.

## 9. Interviewer follow-ups

**Q: How do you convert recursive DFS to iterative?**
Replace the call stack with an explicit stack. Push the start node; loop while the stack is non-empty: pop a node, skip if visited, mark visited, process it, push its unvisited neighbors. For post-order, push `(node, False)` initially; when processing, if `False`, push `(node, True)` back and push unvisited neighbors; if `True`, record the finish. This produces the same post-order as the recursive version.

**Q: How do you detect a cycle in a directed graph?**
3-color DFS: color each node WHITE (unvisited), GRAY (in current recursion path), or BLACK (fully processed). When exploring a neighbor, if it is GRAY, you have found a back edge — a cycle. If it is WHITE, recurse. If it is BLACK, it was finished in a previous DFS call (cross or forward edge) — no cycle on this path.

**Q: What do you do with a 10^7-node graph?**
Python's default recursion limit (~1 000) would immediately overflow on a path graph of 10^7 nodes. Convert to iterative DFS with an explicit stack to use heap memory instead of the call stack. Also ensure the visited set and adjacency list are memory-efficient (e.g., use arrays instead of dicts when node IDs are dense integers). The time complexity remains O(V + E).
