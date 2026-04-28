# Tarjan's & Kosaraju's (Strongly Connected Components)

## 1. TL;DR

Tarjan's and Kosaraju's algorithms both find **Strongly Connected Components (SCCs)** in a directed graph — maximal subsets of nodes where every node can reach every other. Signal: "critical connections," "find groups where every node is mutually reachable," "condensation DAG," or 2-SAT problems. Both run in **O(V + E)**. Tarjan's uses a single DFS with low-link values; Kosaraju's uses two DFS passes (original + transposed graph).

## 2. Intuition

A **strongly connected component** is a maximal set of nodes with a cycle connecting them all. The condensation of any directed graph — collapse each SCC to a single super-node — is always a DAG.

**Kosaraju** exploits finish-time ordering. The first DFS on the original graph computes post-order finish times; the last-finishing node lives in a "source" SCC of the DAG. Run DFS on the **transposed** graph (edges reversed) in reverse-finish order: each DFS tree explores exactly one SCC, because the transpose flips DAG edges so you can't leak into another SCC.

**Tarjan** uses a single DFS and maintains two arrays per node:
- `disc[v]` — discovery time (a global counter that increments on every visit).
- `low[v]` — the minimum `disc` reachable from the subtree of `v` via tree edges plus **at most one back-edge**.

A node `v` is the **root of an SCC** when `low[v] == disc[v]` (nothing in its subtree can reach an ancestor above `v`). At that moment, pop the stack back to `v` — those nodes form one SCC.

**Bridge-finding** reuses the same low-link: an edge `(u, v)` is a bridge if `low[v] > disc[u]`.

## 3. Walkthrough

Graph: 6 nodes, edges `0->1, 1->2, 2->0, 1->3, 3->4, 4->5, 5->3`.

Expected SCCs: `{0, 1, 2}` (a 3-cycle) and `{3, 4, 5}` (another 3-cycle).

### Kosaraju trace

**Pass 1 — DFS on original graph, record finish order (push on finish):**

```
Start at 0: visit 0 -> 1 -> 2 -> (back-edge to 0, stop). Finish: push 2, push 1.
  From 1: visit 3 -> 4 -> 5 -> (back-edge to 3, stop). Finish: push 5, push 4, push 3.
Finish 1. Push 0 last from initial call.
```

Stack top-to-bottom (last finished = top): `0, 1, 3, 4, 5, 2`
(Exact order depends on adjacency iteration; the invariant is: node 0 finishes after nodes in its SCC dominate the stack top.)

**Pass 2 — DFS on transposed graph, pop stack:**

Transposed edges: `1->0, 2->1, 0->2, 3->1, 4->3, 5->4, 3->5`.

Pop `0` (unvisited): DFS on transposed graph from 0 reaches 2, then 1. SCC = `{0, 1, 2}`.
Pop next unvisited `3`: DFS reaches 5, then 4. SCC = `{3, 4, 5}`.

### Tarjan trace (abbreviated)

DFS from 0, global timer starts at 0.

```
Enter 0: disc[0]=low[0]=0. Stack=[0].
  Enter 1: disc[1]=low[1]=1. Stack=[0,1].
    Enter 2: disc[2]=low[2]=2. Stack=[0,1,2].
      Back-edge 2->0: low[2] = min(2, disc[0]) = 0.
    Exit 2: low[2]=0 != disc[2]=2 -> not SCC root. Propagate: low[1]=min(1,0)=0.
    Enter 3: disc[3]=low[3]=3. Stack=[0,1,2,3].
      Enter 4: disc[4]=low[4]=4. Stack=[0,1,2,3,4].
        Enter 5: disc[5]=low[5]=5. Stack=[0,1,2,3,4,5].
          Back-edge 5->3: low[5] = min(5, disc[3]) = 3.
        Exit 5: low[5]=3 != disc[5]=5 -> not root. Propagate: low[4]=min(4,3)=3.
      Exit 4: low[4]=3 != disc[4]=4 -> not root. Propagate: low[3]=min(3,3)=3.
    Exit 3: low[3]=3 == disc[3]=3 -> SCC root! Pop until 3: SCC={5,4,3}.
  Exit 1: low[1]=0 != disc[1]=1 -> not root.
Exit 0: low[0]=0 == disc[0]=0 -> SCC root! Pop until 0: SCC={2,1,0}.
```

Result: `{0,1,2}` and `{3,4,5}`.

## 4. Implementation

```python
from __future__ import annotations

from typing import List, Tuple


# ---------------------------------------------------------------------------
# Kosaraju's algorithm — two-pass DFS
# ---------------------------------------------------------------------------

def kosaraju(n: int, edges: List[Tuple[int, int]]) -> List[List[int]]:
    """Return list of SCCs (each SCC is a sorted list of node indices).

    edges: directed edges as (u, v) pairs.
    """
    # Build adjacency list and transposed adjacency list.
    graph: List[List[int]] = [[] for _ in range(n)]
    trans: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        trans[v].append(u)  # reversed edge

    # Pass 1: iterative DFS on original graph; push each node on finish.
    visited = [False] * n
    finish_order: List[int] = []

    def dfs1(start: int) -> None:
        stack = [(start, 0)]  # (node, neighbour_index)
        visited[start] = True
        while stack:
            node, idx = stack[-1]
            if idx < len(graph[node]):
                stack[-1] = (node, idx + 1)
                nb = graph[node][idx]
                if not visited[nb]:
                    visited[nb] = True
                    stack.append((nb, 0))
            else:
                stack.pop()
                finish_order.append(node)  # post-order

    for v in range(n):
        if not visited[v]:
            dfs1(v)

    # Pass 2: iterative DFS on transposed graph in reverse-finish order.
    visited2 = [False] * n
    sccs: List[List[int]] = []

    def dfs2(start: int) -> List[int]:
        component: List[int] = []
        stack = [start]
        visited2[start] = True
        while stack:
            node = stack.pop()
            component.append(node)
            for nb in trans[node]:
                if not visited2[nb]:
                    visited2[nb] = True
                    stack.append(nb)
        return component

    for v in reversed(finish_order):
        if not visited2[v]:
            sccs.append(sorted(dfs2(v)))

    return sccs


# ---------------------------------------------------------------------------
# Tarjan's algorithm — single-pass DFS with low-link values
# ---------------------------------------------------------------------------

def tarjan(n: int, edges: List[Tuple[int, int]]) -> List[List[int]]:
    """Return list of SCCs (each SCC is a sorted list of node indices).

    edges: directed edges as (u, v) pairs.
    Uses iterative DFS to avoid Python recursion-limit issues.
    """
    graph: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)

    disc = [-1] * n   # -1 = unvisited
    low = [0] * n
    on_stack = [False] * n
    scc_stack: List[int] = []
    timer = [0]
    sccs: List[List[int]] = []

    def dfs(start: int) -> None:
        # Iterative post-order DFS using an explicit call stack.
        call_stack = [(start, 0)]
        disc[start] = low[start] = timer[0]
        timer[0] += 1
        scc_stack.append(start)
        on_stack[start] = True

        while call_stack:
            v, idx = call_stack[-1]
            if idx < len(graph[v]):
                call_stack[-1] = (v, idx + 1)
                w = graph[v][idx]
                if disc[w] == -1:
                    # Tree edge: push w onto DFS stack.
                    disc[w] = low[w] = timer[0]
                    timer[0] += 1
                    scc_stack.append(w)
                    on_stack[w] = True
                    call_stack.append((w, 0))
                elif on_stack[w]:
                    # Back/cross edge to a node still on the SCC stack.
                    low[v] = min(low[v], disc[w])
            else:
                # Post-order: propagate low upward and check for SCC root.
                call_stack.pop()
                if call_stack:
                    parent = call_stack[-1][0]
                    low[parent] = min(low[parent], low[v])
                if low[v] == disc[v]:
                    # v is the root of an SCC — pop until v.
                    scc: List[int] = []
                    while True:
                        w = scc_stack.pop()
                        on_stack[w] = False
                        scc.append(w)
                        if w == v:
                            break
                    sccs.append(sorted(scc))

    for v in range(n):
        if disc[v] == -1:
            dfs(v)

    return sccs


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Graph: 0->1, 1->2, 2->0, 1->3, 3->4, 4->5, 5->3
    # SCCs: {0,1,2} and {3,4,5}
    n = 6
    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 5), (5, 3)]

    expected = {(0, 1, 2), (3, 4, 5)}

    k_sccs = kosaraju(n, edges)
    k_set = {tuple(scc) for scc in k_sccs}
    assert k_set == expected, f"Kosaraju: expected {expected}, got {k_set}"

    t_sccs = tarjan(n, edges)
    t_set = {tuple(scc) for scc in t_sccs}
    assert t_set == expected, f"Tarjan: expected {expected}, got {t_set}"

    print("Smoke tests passed.")
    print("Kosaraju SCCs:", k_sccs)
    print("Tarjan SCCs:", t_sccs)
```

**Template:**

```python
from typing import List, Tuple


def kosaraju(n: int, edges: List[Tuple[int, int]]) -> List[List[int]]:
    graph: List[List[int]] = [[] for _ in range(n)]
    trans: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        trans[v].append(u)

    visited = [False] * n
    finish_order: List[int] = []

    def dfs1(start: int) -> None:
        stack = [(start, 0)]
        visited[start] = True
        while stack:
            node, idx = stack[-1]
            if idx < len(graph[node]):
                stack[-1] = (node, idx + 1)
                nb = graph[node][idx]
                if not visited[nb]:
                    visited[nb] = True
                    stack.append((nb, 0))
            else:
                stack.pop()
                finish_order.append(node)

    for v in range(n):
        if not visited[v]:
            dfs1(v)

    visited2 = [False] * n
    sccs: List[List[int]] = []

    def dfs2(start: int) -> List[int]:
        component: List[int] = []
        stack = [start]
        visited2[start] = True
        while stack:
            node = stack.pop()
            component.append(node)
            for nb in trans[node]:
                if not visited2[nb]:
                    visited2[nb] = True
                    stack.append(nb)
        return component

    for v in reversed(finish_order):
        if not visited2[v]:
            sccs.append(sorted(dfs2(v)))
    return sccs


def tarjan(n: int, edges: List[Tuple[int, int]]) -> List[List[int]]:
    graph: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)

    disc = [-1] * n
    low = [0] * n
    on_stack = [False] * n
    scc_stack: List[int] = []
    timer = [0]
    sccs: List[List[int]] = []

    def dfs(start: int) -> None:
        call_stack = [(start, 0)]
        disc[start] = low[start] = timer[0]
        timer[0] += 1
        scc_stack.append(start)
        on_stack[start] = True
        while call_stack:
            v, idx = call_stack[-1]
            if idx < len(graph[v]):
                call_stack[-1] = (v, idx + 1)
                w = graph[v][idx]
                if disc[w] == -1:
                    disc[w] = low[w] = timer[0]
                    timer[0] += 1
                    scc_stack.append(w)
                    on_stack[w] = True
                    call_stack.append((w, 0))
                elif on_stack[w]:
                    low[v] = min(low[v], disc[w])
            else:
                call_stack.pop()
                if call_stack:
                    low[call_stack[-1][0]] = min(low[call_stack[-1][0]], low[v])
                if low[v] == disc[v]:
                    scc: List[int] = []
                    while True:
                        w = scc_stack.pop()
                        on_stack[w] = False
                        scc.append(w)
                        if w == v:
                            break
                    sccs.append(sorted(scc))

    for v in range(n):
        if disc[v] == -1:
            dfs(v)
    return sccs
```

## 5. Variants & pitfalls

### Variants

- **Kosaraju (two-pass):** Simpler to remember and implement; requires building the transposed graph explicitly.
- **Tarjan (single-pass):** Lower constant factor — one pass, no transpose. The canonical choice in competitive programming.
- **Bridge-finding (Tarjan variant):** Edge `(u, v)` is a bridge if `low[v] > disc[u]`. Note: for bridges, ignore the parent edge to avoid counting undirected edges twice.
- **Articulation points:** Node `u` is an articulation point if it is not the DFS root and some child `v` has `low[v] >= disc[u]`; or if it is the DFS root with more than one DFS child.
- **2-SAT:** Build the implication graph for a 2-CNF formula, find SCCs with Tarjan/Kosaraju, check that no variable and its negation are in the same SCC.

### Pitfalls

- **Tarjan stack invariant:** Only update `low[v]` from a neighbor `w` if `w` is currently on the SCC stack (`on_stack[w]`). Using `disc[w] != -1` instead would incorrectly count cross-edges to already-completed SCCs.
- **Iterative Tarjan post-order timing:** The low-link propagation from child to parent must happen in the post-order step (when the child's frame pops), not when the tree edge is first taken.
- **Python recursion limit:** Recursive Tarjan/Kosaraju will crash on graphs with more than ~1000 nodes. Always use the iterative version shown above.
- **Weakly vs. strongly connected:** A directed graph can be weakly connected (connected if edges are treated as undirected) but have many SCCs. Don't conflate the two.
- **Kosaraju finish-order correctness:** The first-pass finish order is a reverse topological order on the SCC-DAG. Reversing it gives a topological order, so the root SCC is always processed first in pass 2 — exactly the SCC that cannot be reached from any other SCC.

## 6. Complexity

- **Time:** O(V + E) — each node and edge is visited at most twice (once per pass for Kosaraju; once for Tarjan).
- **Space:** O(V + E) — adjacency lists, the explicit DFS stacks, and the SCC stack are all at most O(V + E).

## 7. Problem set

- [Hard] [Critical Connections in a Network](https://leetcode.com/problems/critical-connections-in-a-network/) — Tarjan's bridge-finding variant; find all edges whose removal disconnects the graph.
- [Medium] [Course Schedule IV](https://leetcode.com/problems/course-schedule-iv/) — transitive closure on a DAG; condense SCCs first, then topological DP for reachability queries.

## 8. Related patterns

- [DFS](../graphs/dfs.md) — both algorithms are DFS with extra bookkeeping; solid DFS fluency is a prerequisite.
- [Topological Sort](../graphs/topological-sort.md) — the condensation DAG of SCCs is always a DAG; topological sort on the condensation gives processing order for SCC-based DP.

## 9. Interviewer follow-ups

**Q: Why does Kosaraju's reverse-finish-order trick work?**
The first DFS finish order is a reverse topological order on the SCC-DAG. The last node to finish lives in a source SCC — a component with no incoming edges from other SCCs. On the transposed graph, that source SCC becomes a sink (all edges point inward), so a DFS from it cannot escape to other SCCs. Peeling SCCs one by one in that order decomposes the whole graph correctly.

**Q: Articulation points vs. bridges — what changes in the predicate?**
Both use the same `disc`/`low` low-link DFS. For a **bridge** `(u, v)`: `low[v] > disc[u]` — no back-edge from `v`'s subtree reaches above `u`. For an **articulation point** `u`: a child `v` satisfies `low[v] >= disc[u]` AND `u` is not the DFS root (or `u` is the root with two or more DFS-tree children). The bridge condition is strict (`>`); the articulation-point condition is non-strict (`>=`).
