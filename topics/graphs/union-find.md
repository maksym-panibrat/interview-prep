# Union-Find

## 1. TL;DR

Union-Find (Disjoint Set Union, DSU) answers "are A and B in the same connected component?" and "merge two components" in nearly O(1) amortized time per operation. The signal is **incremental connectivity**: edges arrive one by one and you need to query or track connected components after each addition. Classic applications include Kruskal's MST, "number of connected components after online edge insertions," equivalence classes, and redundant connections. Time: O(α(n)) amortized per operation (inverse Ackermann — effectively constant for any practical n). Space: O(n).

## 2. Intuition

Represent each set as a **tree**: every element points to a parent, and the root of the tree is the canonical representative of the set. `find(x)` walks up the parent chain to the root. `union(x, y)` links the root of x's tree under the root of y's tree (or vice versa).

Two optimizations make this nearly constant time:

**Path compression** (applied during `find`): after walking up to the root, set every node on the path to point directly to the root. The next `find` on any of those nodes costs O(1). The tree flattens as you use it.

**Union by rank**: when merging two trees, attach the shorter tree under the root of the taller tree. This keeps trees shallow — at most O(log n) height without path compression. Together with path compression, the amortized cost per operation is O(α(n)), where α is the inverse Ackermann function — a value ≤ 4 for any n that fits in the observable universe.

The key insight: you never need to enumerate the elements of a component; you only need a single canonical identifier (the root). This is why Union-Find is faster than DFS/BFS for pure connectivity queries on incrementally growing graphs.

## 3. Walkthrough

Elements 0..5. Operations: `union(0,1), union(2,3), union(0,2), find(3), union(4,5), find(1)`.

Initial state: each element is its own root.
```
parent = [0, 1, 2, 3, 4, 5]
rank   = [0, 0, 0, 0, 0, 0]
```

**union(0, 1)**
- find(0) = 0, find(1) = 1. Different roots → merge.
- rank[0] == rank[1] == 0 → attach 1 under 0, increment rank[0].
```
parent = [0, 0, 2, 3, 4, 5]
rank   = [1, 0, 0, 0, 0, 0]
```

**union(2, 3)**
- find(2) = 2, find(3) = 3. Different roots → merge.
- rank[2] == rank[3] == 0 → attach 3 under 2, increment rank[2].
```
parent = [0, 0, 2, 2, 4, 5]
rank   = [1, 0, 1, 0, 0, 0]
```

**union(0, 2)**
- find(0) = 0, find(2) = 2. Different roots → merge.
- rank[0] == rank[2] == 1 → attach 2 under 0 (tie: attach second under first), increment rank[0].
```
parent = [0, 0, 0, 2, 4, 5]
rank   = [2, 0, 1, 0, 0, 0]
```

**find(3)** with path compression
- 3 → parent[3]=2 → parent[2]=0 → root is 0.
- Path compression: set parent[3] = 0 directly (skip intermediate 2).
```
parent = [0, 0, 0, 0, 4, 5]   ← 3 now points directly to root 0
rank   = [2, 0, 1, 0, 0, 0]
```
Returns 0. Node 3 now directly points to the root, so future `find(3)` costs O(1).

**union(4, 5)**
- find(4) = 4, find(5) = 5. Different roots → merge.
- rank[4] == rank[5] == 0 → attach 5 under 4, increment rank[4].
```
parent = [0, 0, 0, 0, 4, 4]
rank   = [2, 0, 1, 0, 1, 0]
```

**find(1)**
- 1 → parent[1]=0 → root is 0. Path already flat.
Returns 0. Same component as node 3 — confirmed.

Final component structure: `{0,1,2,3}` rooted at 0, `{4,5}` rooted at 4.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


class UnionFind:
    """Disjoint Set Union with path compression and union by rank.

    Supports find, union, connected, and component size queries.
    Both optimizations together give O(α(n)) amortized per operation.
    """

    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))   # parent[i] = i initially (each is its own root)
        self.rank: List[int] = [0] * n             # rank[i] = upper bound on tree height
        self.size: List[int] = [1] * n             # size[i] = component size (only accurate at roots)
        self.num_components: int = n               # number of disjoint sets

    def find(self, x: int) -> int:
        """Return the root (canonical representative) of x's component.

        Path compression: every node on the path to the root is re-parented
        directly to the root, flattening the tree for future queries.
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # recursive path compression
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """Merge the components containing x and y.

        Returns True if they were in different components (a merge happened),
        False if they were already in the same component.
        Union by rank: attach the smaller-rank tree under the larger-rank root.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # already connected

        # Attach smaller rank tree under larger rank root.
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx   # ensure rx has >= rank

        self.parent[ry] = rx                          # ry's tree goes under rx
        self.size[rx] += self.size[ry]
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1                        # only grows on tied merge
        self.num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        """Return True if x and y are in the same component."""
        return self.find(x) == self.find(y)

    def component_size(self, x: int) -> int:
        """Return the size of the component containing x."""
        return self.size[self.find(x)]


if __name__ == "__main__":
    uf = UnionFind(6)

    uf.union(0, 1)
    assert uf.connected(0, 1)
    assert not uf.connected(0, 2)
    assert uf.num_components == 5

    uf.union(2, 3)
    assert uf.connected(2, 3)
    assert uf.num_components == 4

    uf.union(0, 2)
    assert uf.connected(0, 3)   # 0 and 3 are now in the same component
    assert uf.num_components == 3

    # find(3) with path compression
    root3 = uf.find(3)
    assert root3 == uf.find(0)  # same root

    uf.union(4, 5)
    assert uf.connected(4, 5)
    assert not uf.connected(0, 4)
    assert uf.num_components == 2

    # Component sizes
    assert uf.component_size(0) == 4   # {0,1,2,3}
    assert uf.component_size(4) == 2   # {4,5}

    # Union already-connected nodes → no change
    merged = uf.union(0, 1)
    assert merged is False
    assert uf.num_components == 2

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n
        self.size: List[int] = [1] * n
        self.num_components: int = n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)

    def component_size(self, x: int) -> int:
        return self.size[self.find(x)]
```

## 5. Variants & pitfalls

### Path compression alone vs union by rank alone vs both

Path compression alone gives O(log n) amortized. Union by rank alone gives O(log n) worst-case height, hence O(log n) per operation. Both together give O(α(n)) amortized — the theoretical optimal. In interviews, always implement both.

### Tracking component size

Store a `size[]` array (only accurate at roots). Update in `union`: `size[new_root] += size[old_root]`. Querying the largest component is then O(1) from the root. This is used for "largest island" and "most connections" problems.

### Weighted Union-Find for offset relationships

For problems like Evaluate Division (LC 399) where edges carry a numeric weight (ratio), store a `weight[]` alongside `parent[]`. `find` must propagate accumulated weights along the path. The path compression step updates `weight[x] *= weight[parent[x]]` (or appropriate operation). This extends Union-Find beyond binary connectivity to arbitrary group-theoretic relationships.

### Rollback Union-Find

For offline "undo last k unions" scenarios, skip path compression (use union by rank only, to preserve the tree structure). Each union records `(ry, old_rank_rx)` for rollback. This turns Union-Find into a persistent structure usable with divide-and-conquer on time (offline dynamic connectivity). Name-drop this in system-design contexts; rarely needed in standard interviews.

### Pitfalls

- **Comparing parents directly without `find`**: `parent[x] == parent[y]` is wrong — they could share a root several hops up without having the same immediate parent. Always call `find(x) == find(y)`.
- **Forgetting to update rank on tied mergers**: rank only increments when two trees of equal rank are merged. Missing this makes trees tall over time, degrading performance.
- **Using Union-Find for dynamic edge removal**: Union-Find is append-only. Once two elements are merged they cannot be separated without rebuilding. For problems involving edge deletions, use the offline reverse-time trick: process deletions in reverse (convert them to additions) or use link-cut trees.
- **Off-by-one on node IDs**: if nodes are labeled 1..n (not 0..n-1), either initialize `UnionFind(n+1)` (wasteful but simple) or subtract 1 from all IDs before calling.

## 6. Complexity

- **Time:** O(α(n)) amortized per `find`, `union`, or `connected` operation — where α is the inverse Ackermann function, ≤ 4 for n ≤ 10^80. In practice, treat as O(1) per operation.
- **Space:** O(n) — `parent`, `rank`, and `size` arrays each of length n.

## 7. Problem set

- [Medium] [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) — count components in an adjacency matrix; direct `union` on each edge, then count roots with `find(i)==i`.
- [Medium] [Redundant Connection](https://leetcode.com/problems/redundant-connection/) — find the last edge that forms a cycle; the redundant edge is the one where `union` returns False.
- [Medium] [Accounts Merge](https://leetcode.com/problems/accounts-merge/) — merge accounts sharing an email; union all emails of the same account, then group by root.
- [Medium] [Number of Operations to Make Network Connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/) — count extra edges (redundant connections) and check if they are enough to bridge all disconnected components.
- [Medium] [Most Stones Removed with Same Row or Column](https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/) — union stones sharing a row or column; maximum removals = n − number of components.
- [Medium] [Satisfiability of Equality Equations](https://leetcode.com/problems/satisfiability-of-equality-equations/) — union equal pairs, then check that no inequality pair has the same root.
- [Medium] [Find Latest Group of Size M](https://leetcode.com/problems/find-latest-group-of-size-m/) — online bit-flipping with component-size queries; union by rank + size tracking.
- [Hard] [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) — union cells as water level rises; answer is the minimum level when src and dst are connected.
- [Hard] [Number of Islands II](https://leetcode.com/problems/number-of-islands-ii/) — incremental island addition with online connectivity queries; the canonical online Union-Find problem.
- [Hard] [Bricks Falling When Hit](https://leetcode.com/problems/bricks-falling-when-hit/) — reverse-time UF: process hits in reverse order (additions instead of deletions); count bricks connected to the ceiling before and after each (reversed) hit.
- [Hard] [Evaluate Division](https://leetcode.com/problems/evaluate-division/) — weighted Union-Find: store ratios along edges; `find` propagates accumulated product.

## 8. Related patterns

- **[DFS](dfs.md)** — DFS and BFS can also find connected components in O(V + E), but they require the full graph in advance. Union-Find shines for online (incremental) edge additions where you need connectivity answers after each addition.
- **[MST](../nice-to-have/mst.md)** — Kruskal's MST algorithm repeatedly adds the cheapest non-cycle edge; "non-cycle" is tested in O(α(n)) per edge using Union-Find.
- **[Topological Sort](topological-sort.md)** — answers a different DAG question (ordering with dependency constraints); Union-Find answers undirected connectivity questions.

## 9. Interviewer follow-ups

**Q: Why is the amortized complexity O(α(n)) — what is the inverse Ackermann function?**
The Ackermann function A(m, n) is a recursive function that grows extremely fast — faster than any exponential. Its inverse α(n) is the number of times you need to "un-apply" Ackermann to bring n down to 1. For n = 2^65536 (far exceeding the number of atoms in the observable universe), α(n) = 4. In practice, every query costs ≤ 5 operations. The formal proof (Tarjan 1975) shows that path compression + union by rank together achieve this bound.

**Q: How do you track component sizes?**
Store an integer `size[]` array alongside `parent[]`. Initialize `size[i] = 1`. In `union`, after identifying the roots `rx` and `ry`, add `size[ry]` to `size[rx]` (the new combined root). Only the root's size entry is meaningful; non-root entries are stale after path compression. Query: `size[find(x)]`.

**Q: Can Union-Find support edge removal?**
No — Union-Find is a merge-only structure. Once two elements are merged they cannot be split without rebuilding from scratch. For offline problems with deletions, use the **reverse-time trick**: process the sequence backward, treating deletions as additions. For online problems requiring both additions and deletions, use a link-cut tree (O(log n) per operation) — significantly more complex to implement.
