"""Fenwick (Binary Indexed) tree — point update, prefix sum. See ../topics/trees/segment-tree-fenwick.md."""
from typing import List


class BIT:
    """Binary Indexed Tree. 1-indexed: pass indices in [1, n] to update/prefix_sum."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.tree: List[int] = [0] * (n + 1)  # tree[0] unused

    def update(self, i: int, delta: int) -> None:
        """Add delta to position i (1-indexed). Walk upward: i += i & -i."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, i: int) -> int:
        """Return sum of [1..i] (1-indexed). Walk downward: i -= i & -i."""
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def range_sum(self, l: int, r: int) -> int:
        """Return sum of [l..r] (1-indexed, inclusive)."""
        return self.prefix_sum(r) - self.prefix_sum(l - 1)
