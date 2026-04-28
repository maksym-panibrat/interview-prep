# Segment Tree & Fenwick

## 1. TL;DR

Reach for these structures when a problem asks for **range queries with point updates** (or range updates with point queries): "sum/min/max over [l, r]" combined with mutations. The signal is "mutable prefix sum," "counting inversions," or "sum/min/max over a changing array." Fenwick (Binary Indexed Tree, BIT) is the compact O(log n) choice for prefix-sum, count, or XOR workloads; segment tree is the general-purpose choice supporting any associative merge operation plus lazy propagation for range updates. Both build in O(n) and answer queries in O(log n).

## 2. Intuition

**Fenwick tree.** Imagine each array index is responsible for a partial sum covering a range whose length is a power of two determined by the lowest set bit of its 1-based index. Index 4 (binary `100`) covers 4 elements [1..4]; index 6 (binary `110`) covers 2 elements [5..6]; index 7 (binary `111`) covers 1 element [7..7]. To query `prefix_sum(i)`, walk leftward stripping one lowest set bit each time: each stop adds one partial sum. To update index `i`, walk rightward adding one lowest set bit each time: each stop adjusts one partial sum. Both traversals visit at most log n nodes.

The bit trick `i & -i` isolates the lowest set bit of `i` in two's complement. Stripping it (`i -= i & -i`) moves left toward 0; adding it (`i += i & -i`) propagates the update rightward toward n.

**Segment tree.** A binary tree where each internal node stores the combined value (sum, min, max, …) of its range. The root covers [0, n-1]; its two children cover [0, mid] and [mid+1, n-1]; leaves hold single elements. Any range query decomposes into at most 4 log n tree nodes whose combined value is the answer. Any point update touches exactly one leaf and at most log n ancestors. Lazy propagation defers range updates by storing a "pending" tag at each node and pushing it down before descending further — this keeps range-update + range-query at O(log n) each.

Choose Fenwick for prefix sums, counting, and XOR where the inverse operation exists. Choose segment tree when the merge operation has no inverse (min, max, GCD), when you need range updates, or when you need custom merge logic.

## 3. Walkthrough

### Fenwick tree on [1, 2, 3, 4, 5] (1-indexed)

Build by calling `update(i, a[i])` for each i from 1 to 5:

```
Internal tree[] array after full build:
  index:  1   2   3   4   5
  tree[]: 1   3   3  10   5

  tree[1] = a[1]              = 1         (covers [1..1], 1 element)
  tree[2] = a[1] + a[2]       = 1+2 = 3  (covers [1..2], 2 elements)
  tree[3] = a[3]              = 3         (covers [3..3], 1 element)
  tree[4] = a[1]+a[2]+a[3]+a[4] = 10     (covers [1..4], 4 elements)
  tree[5] = a[5]              = 5         (covers [5..5], 1 element)
```

**Point update: `update(2, +3)`** (add delta=3 at index 2)

Walk indices upward: `i = 2 → 4` (i += i&-i: 2 += 2 = 4; 4 += 4 = 8 > 5, stop).

```
  tree[2] += 3  →  tree[2] = 6
  tree[4] += 3  →  tree[4] = 13
```

New tree[]: `[_, 1, 6, 3, 13, 5]` (index 0 unused).

**Prefix sum query: `prefix_sum(4)`**

Walk indices downward: `i = 4 → 0` (i -= i&-i: 4 -= 4 = 0, stop).

```
  result = tree[4] = 13
```

Answer: 13. (After the update a[2] became 5, so prefix sum [1..4] = 1+5+3+4 = 13.)

### Segment tree on [1, 2, 3, 4, 5]

The tree is stored in a 1-indexed array of size 4*n = 20. Each node `k` covers an interval; its left child is `2k`, right child is `2k+1`.

```
         [0..4] sum=15
        /              \
   [0..2] sum=6      [3..4] sum=9
   /        \         /        \
[0..1]=3  [2..2]=3  [3..3]=4  [4..4]=5
 /     \
[0..0]=1 [1..1]=2
```

**Point update: set index 2 to value 5** (delta = 5 - 3 = +2 at the leaf level)

Touches the path from leaf [2..2] to the root: update leaf, then propagate sums upward through [0..2] and [0..4]. Log n = 3 writes.

**Range sum query: [1..3]**

Decompose [1..3] against tree nodes:
- Node [0..4]: not fully inside — recurse
  - Node [0..2]: not fully inside — recurse
    - Node [0..1]: not fully inside — recurse
      - Node [0..0]: completely outside [1..3] — return 0
      - Node [1..1]: completely inside — return 2
    - Node [2..2]: completely inside — return 3
  - Node [3..4]: not fully inside — recurse
    - Node [3..3]: completely inside — return 4
    - Node [4..4]: completely outside — return 0

Result: 0 + 2 + 3 + 4 = 9. At most 4 log n nodes visited.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


class Fenwick:
    """Binary Indexed Tree (Fenwick Tree) for point-update, prefix-sum queries.

    1-indexed internally. Caller passes 1-based indices to update/prefix_sum.
    """

    def __init__(self, n: int) -> None:
        self.n = n
        self.tree: List[int] = [0] * (n + 1)  # tree[0] unused

    def update(self, i: int, delta: int) -> None:
        """Add delta to position i (1-indexed). Walk upward: i += i & -i."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i  # move to next responsible node

    def prefix_sum(self, i: int) -> int:
        """Return sum of [1..i] (1-indexed). Walk downward: i -= i & -i."""
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i  # strip lowest set bit → move left
        return s

    def range_sum(self, l: int, r: int) -> int:
        """Return sum of [l..r] (1-indexed, inclusive)."""
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


class SegmentTree:
    """Segment tree for point-update, range-sum queries.

    0-indexed interface. Array size is 4*n to safely hold all nodes.
    """

    def __init__(self, data: List[int]) -> None:
        self.n = len(data)
        self.tree: List[int] = [0] * (4 * self.n)
        if self.n:
            self._build(1, 0, self.n - 1, data)

    def _build(self, node: int, node_l: int, node_r: int, data: List[int]) -> None:
        if node_l == node_r:
            self.tree[node] = data[node_l]
            return
        mid = (node_l + node_r) // 2
        self._build(2 * node, node_l, mid, data)
        self._build(2 * node + 1, mid + 1, node_r, data)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def update(self, i: int, val: int) -> None:
        """Set position i (0-indexed) to val."""
        self._update(1, 0, self.n - 1, i, val)

    def _update(self, node: int, node_l: int, node_r: int, i: int, val: int) -> None:
        if node_l == node_r:
            self.tree[node] = val
            return
        mid = (node_l + node_r) // 2
        if i <= mid:
            self._update(2 * node, node_l, mid, i, val)
        else:
            self._update(2 * node + 1, mid + 1, node_r, i, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query(self, l: int, r: int) -> int:
        """Return sum of [l..r] (0-indexed, inclusive)."""
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, node: int, node_l: int, node_r: int, l: int, r: int) -> int:
        if r < node_l or node_r < l:
            return 0  # completely outside query range
        if l <= node_l and node_r <= r:
            return self.tree[node]  # completely inside query range
        mid = (node_l + node_r) // 2
        return (self._query(2 * node, node_l, mid, l, r) +
                self._query(2 * node + 1, mid + 1, node_r, l, r))


if __name__ == "__main__":
    data = [1, 2, 3, 4, 5]

    # ---- Fenwick smoke tests ----
    bit = Fenwick(5)
    for idx, val in enumerate(data, start=1):
        bit.update(idx, val)
    assert bit.prefix_sum(4) == 10, f"expected 10, got {bit.prefix_sum(4)}"
    assert bit.range_sum(2, 4) == 9, f"expected 9, got {bit.range_sum(2, 4)}"
    bit.update(2, 3)  # a[2] += 3 → a[2] = 5
    assert bit.prefix_sum(4) == 13, f"expected 13, got {bit.prefix_sum(4)}"
    assert bit.range_sum(1, 5) == 18, f"expected 18, got {bit.range_sum(1, 5)}"

    # ---- Segment tree smoke tests ----
    st = SegmentTree(data)
    assert st.query(0, 4) == 15, f"expected 15, got {st.query(0, 4)}"
    assert st.query(1, 3) == 9, f"expected 9, got {st.query(1, 3)}"
    st.update(2, 5)  # set index 2 to 5
    assert st.query(0, 4) == 17, f"expected 17, got {st.query(0, 4)}"
    assert st.query(1, 3) == 11, f"expected 11, got {st.query(1, 3)}"

    print("All smoke tests passed.")
```

**Template:**

```python
class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def update(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, i):
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def range_sum(self, l, r):
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


class SegmentTree:
    def __init__(self, data):
        self.n = len(data)
        self.tree = [0] * (4 * self.n)
        if self.n:
            self._build(1, 0, self.n - 1, data)

    def _build(self, node, node_l, node_r, data):
        if node_l == node_r:
            self.tree[node] = data[node_l]
            return
        mid = (node_l + node_r) // 2
        self._build(2 * node, node_l, mid, data)
        self._build(2 * node + 1, mid + 1, node_r, data)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def update(self, i, val):
        self._update(1, 0, self.n - 1, i, val)

    def _update(self, node, node_l, node_r, i, val):
        if node_l == node_r:
            self.tree[node] = val
            return
        mid = (node_l + node_r) // 2
        if i <= mid:
            self._update(2 * node, node_l, mid, i, val)
        else:
            self._update(2 * node + 1, mid + 1, node_r, i, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query(self, l, r):
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, node, node_l, node_r, l, r):
        if r < node_l or node_r < l:
            return 0
        if l <= node_l and node_r <= r:
            return self.tree[node]
        mid = (node_l + node_r) // 2
        return (self._query(2 * node, node_l, mid, l, r) +
                self._query(2 * node + 1, mid + 1, node_r, l, r))
```

## 5. Variants & pitfalls

### Fenwick variants

**Prefix sum (canonical).** Point update + prefix-sum/range-sum query. The standard Fenwick formulation described above.

**Range update + point query.** Store differences: `update(l, +delta)` and `update(r+1, -delta)`, then `prefix_sum(i)` gives the current value at index `i`. This is a difference-array trick applied on top of a Fenwick tree.

**Range update + range query.** Requires two BITs (B1, B2) maintaining auxiliary quantities derived from the difference array. More complex; segment tree with lazy propagation is usually clearer.

**Min/max via dual-BIT.** Possible for prefix-min/max on an append-only sequence, but the inverse operation doesn't exist for min/max in general — arbitrary updates aren't supported. Segment tree is the correct choice for general min/max with updates.

### Segment tree variants

**Classical (sum/min/max).** The implementation above supports any operation by swapping the merge in `_build`, `_update`, and `_query`.

**Lazy propagation.** For range updates (add delta to all elements in [l, r]): attach a `lazy[]` array alongside `tree[]`. When descending past a node, push its lazy tag to children before recursing. This keeps range-update + range-query at O(log n). The classic bug is forgetting to push lazy tags before querying a node's children — the child values are stale until the push.

**Persistent segment tree.** Each update creates a new root pointing to a new path of log n nodes; old roots remain valid for historical queries. Useful for "k-th smallest in a range" via merge sort tree.

**2D segment tree.** A segment tree where each node stores another segment tree over the second dimension. Builds in O(n^2) time and space; queries in O(log^2 n). Coordinate compression is often required.

### Pitfalls

- **Fenwick is 1-indexed.** The standard `i & -i` traversal breaks at `i = 0` (infinite loop). If your input is 0-indexed, translate: `update(i + 1, delta)` and `prefix_sum(i + 1)`. This 1-indexed/0-indexed boundary is the single most common Fenwick bug.
- **Segment tree array size.** Using `2*n` is not enough for a non-power-of-two `n`. Use `4*n` (or `2 * next_power_of_two(n)`) to guarantee no out-of-bounds writes.
- **Lazy push before descend.** In a lazy segment tree, always call `push_down(node)` at the start of `_update` and `_query` before recursing into children. Skipping the push returns stale child values.
- **Range boundary conventions.** Be consistent: the implementation above uses 0-indexed, inclusive [l, r] for segment tree and 1-indexed, inclusive [l, r] for Fenwick. Mixing conventions causes off-by-one errors.

## 6. Complexity

- **Time (Fenwick):** O(n) build (batched updates) or O(n log n) naïve; O(log n) per update and per prefix-sum query — each traversal visits at most log n nodes.
- **Time (Segment tree):** O(n) build (each of the 2n nodes set once); O(log n) per point update and per range query — traversal depth is at most log n.
- **Space:** O(n) for Fenwick (`tree` of size n+1); O(n) for segment tree (`tree` of size 4n, all within a constant factor of n).

## 7. Problem set

- [Medium] [Range Sum Query - Mutable](https://leetcode.com/problems/range-sum-query-mutable/) — direct application; implement either structure and you're done.
- [Hard] [Count of Smaller Numbers After Self](https://leetcode.com/problems/count-of-smaller-numbers-after-self/) — Fenwick tree on coordinate-compressed values; classic inversion-count pattern.
- [Hard] [Reverse Pairs](https://leetcode.com/problems/reverse-pairs/) — count pairs (i, j) with i < j and nums[i] > 2*nums[j]; BIT or merge sort.
- [Hard] [Count of Range Sum](https://leetcode.com/problems/count-of-range-sum/) — count subarrays whose sum falls in [lower, upper]; merge sort tree or segment tree.
- [Hard] [Range Sum Query 2D - Mutable](https://leetcode.com/problems/range-sum-query-2d-mutable/) — 2D Fenwick tree; natural extension of the 1D prefix-sum idea.
- [Hard] [The Skyline Problem](https://leetcode.com/problems/the-skyline-problem/) — segment tree (or sorted-set) on building heights; sweep-line + range max.
- [Hard] [Falling Squares](https://leetcode.com/problems/falling-squares/) — range max query + point update; segment tree with coordinate compression.
- [Hard] [Range Module](https://leetcode.com/problems/range-module/) — dynamic interval tracking; lazy segment tree or sorted set.
- [Hard] [Number of Longest Increasing Subsequence](https://leetcode.com/problems/number-of-longest-increasing-subsequence/) — augment Fenwick to track (length, count) pairs; non-trivial merge operation shows why segment tree generalizes BIT.

## 8. Related patterns

- [Lowest Common Ancestor](lca.md) — Euler tour + RMQ (range minimum query) converts LCA to a segment tree problem; the classic O(n log n) preprocessing + O(1) query uses a sparse table over the Euler tour.
- [Interval DP](../dp/interval-dp.md) — often confused with range trees: interval DP *combines ranges with a cost* to find an optimal substructure, while segment/Fenwick trees *query or update ranges* in a mutable array. Different problems, different tools.
- [Quicksort & Mergesort](../searching-sorting/quicksort-mergesort.md) — merge sort naturally counts inversions in O(n log n) without any auxiliary structure; when the inversion-count problem allows offline processing or a simple merge, merge sort is lighter than a BIT.

## 9. Interviewer follow-ups

**Q: Range update + point query with a Fenwick tree?**
Use a difference array on top of the BIT: `update(l, +delta)` and `update(r+1, -delta)`. Then `prefix_sum(i)` returns the current value at index `i` because the prefix sum of a difference array is the original value. This keeps both operations O(log n) without a segment tree.

**Q: Range update + range query?**
Use a lazy segment tree: each node carries a pending "add delta" tag. Before descending into children, push the tag down (add it to both children's values and tags, then clear the parent's tag). Both update and query remain O(log n). Alternatively, a two-BIT trick exists for linear updates, but lazy segment tree is clearer and more general.

**Q: When should I pick segment tree over Fenwick?**
Pick segment tree when: (1) the merge operation has no inverse (min, max, GCD, product under modular arithmetic); (2) you need range updates, not just point updates; (3) the query logic is complex (e.g., "find leftmost index in a range where value > k"). Fenwick is smaller, faster in practice (better cache behavior), and simpler to implement for the pure prefix-sum case — use it there and reach for segment tree when Fenwick doesn't fit.
