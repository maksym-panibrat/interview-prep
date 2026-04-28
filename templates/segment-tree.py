"""Segment tree — point update, range sum. See ../topics/trees/segment-tree-fenwick.md."""
from typing import List


class SegmentTree:
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

    def update_point(self, i: int, val: int) -> None:
        """Set index i (0-indexed) to val."""
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

    def query_range(self, l: int, r: int) -> int:
        """Return sum of [l..r] (0-indexed, inclusive)."""
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, node: int, node_l: int, node_r: int, l: int, r: int) -> int:
        if r < node_l or node_r < l:
            return 0
        if l <= node_l and node_r <= r:
            return self.tree[node]
        mid = (node_l + node_r) // 2
        return (self._query(2 * node, node_l, mid, l, r) +
                self._query(2 * node + 1, mid + 1, node_r, l, r))

    # --- Lazy propagation extension point ---
    # To support range updates (add delta to [l, r]):
    #   1. Add self.lazy = [0] * (4 * self.n)
    #   2. Write push_down(node) to flush lazy[node] to both children.
    #   3. Call push_down(node) at the top of _update and _query before recursing.
    #   4. In the fully-covered case of _update, set self.tree[node] += delta * size
    #      and self.lazy[node] += delta instead of recursing.
