# A* Search

## 1. TL;DR

A* finds shortest paths in large state spaces where Dijkstra is too slow but a good heuristic exists. Signal: grid pathfinding, sliding puzzles, or any weighted shortest-path problem where you can cheaply estimate remaining cost. Key idea: Dijkstra prioritizes nodes by `g(n)` (cost so far); A* prioritizes by `f(n) = g(n) + h(n)` where `h(n)` is an **admissible** heuristic (never overestimates). With a **consistent** heuristic A* is provably optimal and expands far fewer nodes than Dijkstra. Time: O((V + E) log V) worst case; O(d) with a perfect heuristic. Space: O(V).

## 2. Intuition

Dijkstra fans out equally in all directions because it has no idea where the goal is. If you can estimate how far each node is from the goal — without overestimating — you can bias the search toward the goal and skip expanding nodes that are obviously headed the wrong way.

An **admissible** heuristic `h(n)` never overestimates the true remaining cost. This guarantees that when A* settles a node, it has found the true shortest path to it. A **consistent** (monotonic) heuristic also satisfies `h(n) ≤ cost(n, n') + h(n')` for every edge — the triangle inequality. Consistency lets you short-circuit: once a node leaves the open set, its `f` value is final and it need not be re-opened. Admissible but inconsistent heuristics can produce suboptimal results when combined with a closed set.

Think of `g(n)` as "how much did I pay to reach here" and `h(n)` as "my optimistic estimate of the remaining bill." The priority queue orders nodes by their total estimated bill `f(n)`, so A* always extends the path that looks cheapest end-to-end.

## 3. Walkthrough

### 8-puzzle with Manhattan-distance heuristic

Goal state: `[[1,2,3],[4,5,6],[7,8,_]]`.

Starting board:

```
1  2  3
4  _  6
7  5  8
```

Manhattan distance = sum over each non-blank tile of `|row_current - row_goal| + |col_current - col_goal|`.

- Tile 5 is at (2,1); its goal is (1,1). Distance = 1.
- Tile 6 is at (1,2); its goal is (1,2). Distance = 0.
- All other tiles are already in place. Manhattan = 1.

So `h(start) = 1`. Since only one tile is misplaced by one step, A* explores essentially one path. BFS would explore all states reachable in 0, 1, 2, … moves, potentially thousands. With a large starting Manhattan distance (say, 20), BFS expands roughly 9^(d/2) states while A* expands a small fraction because states far from goal have large `h` and are deprioritized.

### Small grid example

```
. . . . .
. # # # .
. . . . .
. . # # .
. . . . G
```

Start = (0,0), Goal G = (4,4), `#` = wall. Manhattan heuristic steers A* diagonally toward the goal, only detouring when blocked. Dijkstra would instead expand in concentric rings from (0,0) regardless of direction.

## 4. Implementation

```python
from __future__ import annotations
import heapq
from typing import Callable, Hashable, Iterable, Optional, TypeVar

S = TypeVar("S")


def astar(
    start: S,
    goal: S,
    neighbors: Callable[[S], Iterable[tuple[S, float]]],
    heuristic: Callable[[S], float],
) -> Optional[list[S]]:
    """Generic A* on a graph.

    Parameters
    ----------
    start      : starting state (any hashable)
    goal       : target state
    neighbors  : function returning (neighbor_state, edge_cost) pairs
    heuristic  : admissible (never-overestimates) h(state) -> float

    Returns reconstructed path [start, ..., goal] or None if unreachable.
    """
    g: dict[S, float] = {start: 0.0}
    prev: dict[S, Optional[S]] = {start: None}
    # heap entries: (f, tie-breaker, state)
    counter = 0
    heap: list[tuple[float, int, S]] = [(heuristic(start), 0, start)]  # type: ignore[type-var]

    while heap:
        f, _, state = heapq.heappop(heap)
        if state == goal:
            path: list[S] = []
            node: Optional[S] = goal
            while node is not None:
                path.append(node)
                node = prev[node]
            path.reverse()
            return path
        g_state = g.get(state, float("inf"))
        if f - heuristic(state) > g_state + 1e-9:
            continue  # stale entry
        for nb, cost in neighbors(state):
            ng = g_state + cost
            if ng < g.get(nb, float("inf")):
                g[nb] = ng
                prev[nb] = state
                counter += 1
                heapq.heappush(heap, (ng + heuristic(nb), counter, nb))

    return None


# ---------------------------------------------------------------------------
# Smoke test: 5x5 grid with one wall
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ROWS, COLS = 5, 5
    WALLS = {(1, 1), (1, 2), (1, 3), (2, 3), (3, 3)}

    def grid_neighbors(pos: tuple[int, int]) -> list[tuple[tuple[int, int], float]]:
        r, c = pos
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in WALLS:
                result.append(((nr, nc), 1.0))
        return result

    def manhattan(pos: tuple[int, int]) -> float:
        return abs(pos[0] - 4) + abs(pos[1] - 4)

    path = astar((0, 0), (4, 4), grid_neighbors, manhattan)
    assert path is not None, "no path found"
    assert path[0] == (0, 0) and path[-1] == (4, 4)
    # Optimal path length should be 8 moves (Manhattan distance 8, no forced detour)
    assert len(path) == 9, f"expected 9 nodes (8 moves), got {len(path)}"
    print("Smoke test passed. Path:", path)
```

**Template:**

```python
import heapq
from typing import Callable, Hashable, Iterable, Optional, TypeVar

S = TypeVar("S")


def astar(
    start: S,
    goal: S,
    neighbors: Callable[[S], Iterable[tuple[S, float]]],
    heuristic: Callable[[S], float],
) -> Optional[list[S]]:
    g: dict[S, float] = {start: 0.0}
    prev: dict[S, Optional[S]] = {start: None}
    counter = 0
    heap: list[tuple[float, int, S]] = [(heuristic(start), 0, start)]  # type: ignore[type-var]
    while heap:
        f, _, state = heapq.heappop(heap)
        if state == goal:
            path: list[S] = []
            node: Optional[S] = goal
            while node is not None:
                path.append(node)
                node = prev[node]
            path.reverse()
            return path
        g_state = g.get(state, float("inf"))
        if f - heuristic(state) > g_state + 1e-9:
            continue
        for nb, cost in neighbors(state):
            ng = g_state + cost
            if ng < g.get(nb, float("inf")):
                g[nb] = ng
                prev[nb] = state
                counter += 1
                heapq.heappush(heap, (ng + heuristic(nb), counter, nb))
    return None
```

## 5. Variants & pitfalls

### Variants

- **Uniform-cost search (Dijkstra):** A* with `h ≡ 0`. Optimal but explores all directions equally.
- **IDA\* (Iterative Deepening A\*):** Memory-bounded version. Uses iterative deepening with an f-cost cutoff instead of an open list. Trades time for memory — useful when state space is too large to hold in a heap.
- **Bidirectional A\*:** Run two A* searches simultaneously from start and goal; terminate when the frontiers meet. Can halve the effective search depth on symmetric graphs.

### Pitfalls

- **Inadmissible heuristic:** If `h(n)` overestimates, A* may return a suboptimal path. Admissibility is not checked automatically — you must prove it.
- **Inconsistent heuristic + closed set:** An admissible but inconsistent heuristic can cause a node to be settled with a non-optimal `g` value. Either skip the closed set (re-open nodes) or use a consistent heuristic.
- **Floating-point tie-breaking:** When many nodes share the same `f` value, heap ordering is arbitrary. Use a counter as a tie-breaker (done above) to ensure FIFO ordering among equal-`f` nodes and avoid non-determinism.
- **Stale heap entries:** Lazy deletion — skip a popped entry if its stored `g` cost exceeds the current best known `g`.

## 6. Complexity

| Metric | Value |
|--------|-------|
| Time (worst case, consistent h) | O((V + E) log V) |
| Time (perfect heuristic, h = true remaining cost) | O(d) where d = solution depth |
| Space | O(V) for the open/closed sets |

The quality of the heuristic determines where actual performance lands between O(d) and O((V+E) log V). With a stronger heuristic you expand fewer nodes; with a weaker one you approach Dijkstra's behavior.

## 7. Problem set

- [Medium] [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) — 8-directional BFS works; A* with Chebyshev distance (`max(|dr|, |dc|)`) as heuristic gives a minor speedup on large grids.
- [Hard] [Sliding Puzzle](https://leetcode.com/problems/sliding-puzzle/) — 773. A* with Manhattan-distance heuristic shines; BFS is also feasible because the state space (6! = 720) is tiny.
- [Hard] [Race Car](https://leetcode.com/problems/race-car/) — 818. State = (position, speed); BFS/Dijkstra and A* both apply; A* with distance-to-target heuristic prunes effectively.

## 8. Related patterns

- [Shortest Paths (Dijkstra)](../graphs/shortest-paths.md) — A* generalizes Dijkstra by adding a heuristic. When `h ≡ 0` the algorithms are identical.
- [BFS](../graphs/bfs.md) — A* with `h ≡ 0` and uniform edge weights reduces to BFS. BFS is preferable on unweighted grids for simplicity.

## 9. Interviewer follow-ups

**Q: What's an admissible heuristic for grid Manhattan distance?**
Manhattan distance itself: `|dr| + |dc|` never overestimates the number of moves on a 4-directional grid because you must move at least that many steps, and you cannot cut corners.

**Q: Why does consistency matter?**
Consistency (monotonicity) guarantees that once a node is settled (popped from the heap), its `g` value is optimal and it will never need to be re-opened. This makes the closed-set short-circuit sound: a settled node's `f` value is the true shortest-path cost, so no future path through any open node can improve it. Without consistency, a node could be settled with a suboptimal `g` and the algorithm must allow re-opening — making analysis and implementation more complex.

**Q: When would you prefer IDA* over A*?**
When memory is the bottleneck. IDA* uses O(d) memory (recursion stack depth) compared to A*'s O(V) open-list size. The trade-off is that IDA* re-expands nodes across iterations, which can multiply runtime by a factor related to the branching factor.
