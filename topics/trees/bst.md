# Binary Search Tree

## 1. TL;DR

A Binary Search Tree (BST) is a binary tree where every node satisfies the **BST invariant**: all values in the left subtree are strictly less than the node's value, and all values in the right subtree are strictly greater. The signal is "binary search tree," "k-th smallest in a tree," "insert/delete/validate a sorted-property tree," or any query that exploits sorted order on a tree. Inorder traversal of a BST yields a sorted sequence. Search, insert, and delete are all O(h) where h = O(log n) for a balanced tree and O(n) for a skewed one. Space: O(h) for recursion stack.

## 2. Intuition

A BST is a sorted structure shaped like a binary tree. At every node you face the same binary decision as in binary search on an array: if the target is less than the current node, go left; if greater, go right; if equal, you are done. This is why BST search mirrors array binary search — both halve the search space at each step, achieving O(log n) on a balanced tree.

The **inorder traversal** (left → node → right) visits nodes in ascending order. This is the defining property: any algorithm that needs sorted order from a BST can collect it via inorder traversal in O(n).

For **validation**, a common mistake is to check only that each node is greater than its immediate left child and less than its immediate right child. That is not enough — a subtree's root could violate the invariant with respect to an ancestor. The correct approach threads an interval `(min_bound, max_bound)` down the tree: every node's value must fall strictly inside this interval. Descending left tightens the upper bound; descending right tightens the lower bound.

## 3. Walkthrough

### Validate `[2, 1, 3]` — should return True

```
    2
   / \
  1   3
```

Range method: start with `(-∞, +∞)`.
- Node 2: `2 ∈ (-∞, +∞)` — OK. Recurse left with `(-∞, 2)`, recurse right with `(2, +∞)`.
- Node 1: `1 ∈ (-∞, 2)` — OK. No children.
- Node 3: `3 ∈ (2, +∞)` — OK. No children.

Inorder: `[1, 2, 3]` — sorted. Result: **True**.

### Validate `[5, 1, 4, null, null, 3, 6]` — should return False

```
      5
     / \
    1   4
       / \
      3   6
```

Range method: start with `(-∞, +∞)`.
- Node 5: `5 ∈ (-∞, +∞)` — OK. Recurse left with `(-∞, 5)`, recurse right with `(5, +∞)`.
- Node 1: `1 ∈ (-∞, 5)` — OK. No children.
- Node 4: `4 ∈ (5, +∞)`? **No — 4 < 5. FAIL.**

The right child of 5 is 4, but the right subtree must have all values strictly greater than 5. Result: **False**.

Inorder: `[1, 5, 3, 4, 6]` — not sorted (confirms failure).

### Insert 4 into `[2, 1, 3]`

```
    2
   / \
  1   3
```

Trace: target = 4.
- At node 2: 4 > 2, descend right.
- At node 3: 4 > 3, descend right — child is null.
- Place 4 as right child of 3.

Result:

```
    2
   / \
  1   3
       \
        4
```

## 4. Implementation

```python
from __future__ import annotations
from typing import Optional


class TreeNode:
    def __init__(self, val: int = 0, left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def validate_bst(root: Optional[TreeNode]) -> bool:
    """Range method: each node's value must be strictly inside (lo, hi)."""
    def _check(node: Optional[TreeNode], lo: float, hi: float) -> bool:
        if node is None:
            return True
        if not (lo < node.val < hi):
            return False
        return (_check(node.left, lo, node.val) and
                _check(node.right, node.val, hi))

    return _check(root, float("-inf"), float("inf"))


def insert_bst(root: Optional[TreeNode], val: int) -> TreeNode:
    """Insert val into the BST; return the (possibly new) root."""
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert_bst(root.left, val)
    elif val > root.val:
        root.right = insert_bst(root.right, val)
    # val == root.val: duplicate — no-op (treat as distinct-values BST)
    return root


def delete_bst(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    """Delete val from the BST; return the (possibly new) root.

    Three cases:
      1. Leaf node — simply remove it.
      2. One child — promote that child.
      3. Two children — replace value with inorder successor's value,
         then delete the successor from the right subtree.
    """
    if root is None:
        return None
    if val < root.val:
        root.left = delete_bst(root.left, val)
    elif val > root.val:
        root.right = delete_bst(root.right, val)
    else:
        # Case 1 & 2: at most one child
        if root.left is None:
            return root.right
        if root.right is None:
            return root.left
        # Case 3: two children — find inorder successor (leftmost in right subtree)
        successor = root.right
        while successor.left is not None:
            successor = successor.left
        root.val = successor.val          # copy successor's VALUE (not its reference)
        root.right = delete_bst(root.right, successor.val)
    return root


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    """Return the k-th smallest value via iterative inorder (1-indexed).

    Early-terminates once the k-th node is visited — avoids traversing the
    entire tree when k is small.
    """
    stack: list = []
    curr: Optional[TreeNode] = root
    count = 0
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        count += 1
        if count == k:
            return curr.val
        curr = curr.right
    raise ValueError(f"k={k} exceeds the number of nodes in the BST")


if __name__ == "__main__":
    def build(val: int, left: Optional[TreeNode] = None,
              right: Optional[TreeNode] = None) -> TreeNode:
        return TreeNode(val, left, right)

    # Validate: [2, 1, 3] → True
    t1 = build(2, build(1), build(3))
    assert validate_bst(t1) is True, "expected True for [2,1,3]"

    # Validate: [5, 1, 4, null, null, 3, 6] → False
    t2 = build(5, build(1), build(4, build(3), build(6)))
    assert validate_bst(t2) is False, "expected False for [5,1,4,null,null,3,6]"

    # Insert 4 into [2, 1, 3]
    t3 = build(2, build(1), build(3))
    t3 = insert_bst(t3, 4)
    assert t3.right is not None and t3.right.right is not None
    assert t3.right.right.val == 4, "4 should be right child of 3"

    # Delete leaf
    t4 = build(5, build(3, build(2), build(4)), build(7))
    t4 = delete_bst(t4, 2)
    assert t4.left is not None and t4.left.left is None, "leaf 2 should be removed"

    # Delete node with two children (root = 5)
    t5 = build(5, build(3, build(2), build(4)), build(7))
    t5 = delete_bst(t5, 5)
    assert t5 is not None and t5.val == 7, "successor 7 should replace 5"

    # Kth smallest: [3, 1, 4, null, 2] → 1st=1, 2nd=2, 3rd=3
    t6 = build(3, build(1, None, build(2)), build(4))
    assert kth_smallest(t6, 1) == 1
    assert kth_smallest(t6, 2) == 2
    assert kth_smallest(t6, 3) == 3

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def validate_bst(root: Optional[TreeNode]) -> bool:
    def _check(node, lo, hi):
        if node is None:
            return True
        if not (lo < node.val < hi):
            return False
        return _check(node.left, lo, node.val) and _check(node.right, node.val, hi)
    return _check(root, float("-inf"), float("inf"))


def insert_bst(root: Optional[TreeNode], val: int) -> TreeNode:
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert_bst(root.left, val)
    elif val > root.val:
        root.right = insert_bst(root.right, val)
    return root


def delete_bst(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    if root is None:
        return None
    if val < root.val:
        root.left = delete_bst(root.left, val)
    elif val > root.val:
        root.right = delete_bst(root.right, val)
    else:
        if root.left is None:
            return root.right
        if root.right is None:
            return root.left
        successor = root.right
        while successor.left:
            successor = successor.left
        root.val = successor.val
        root.right = delete_bst(root.right, successor.val)
    return root


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    stack, curr, count = [], root, 0
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        count += 1
        if count == k:
            return curr.val
        curr = curr.right
    raise ValueError(f"k exceeds node count")
```

## 5. Variants & pitfalls

### Validation: range method vs. inorder comparison

The **range method** (`validate_bst` above) is the canonical approach. Threading `(lo, hi)` bounds handles:
- **Negative values**: inorder comparison using `prev` works fine, but initializing `prev = float("-inf")` must be done correctly; the range method avoids the need for a mutable `prev` variable.
- **Strict-less-than vs. allows-duplicates**: change `lo < node.val < hi` to `lo <= node.val < hi` (or similar) depending on the problem's definition. Mixing up `<` and `<=` is a frequent bug.
- **Common pitfall**: checking only the immediate parent's value — `node.val > node.left.val` — fails for a node inserted into the left subtree of an ancestor that violates the ancestor's right-child constraint.

### Insert: return the root

Always return `root` from `insert_bst`. Recursive calls reassign `root.left` and `root.right` in-place. Forgetting the return and discarding the new root is a common bug.

### Delete: three cases

1. **Leaf**: return `None`.
2. **One child**: return the surviving child.
3. **Two children**: find the **inorder successor** (leftmost node in the right subtree), copy its **value** into the current node, then delete the successor from the right subtree. The key point is copying the value — not splicing in the successor node by reference — which would corrupt the parent links.

### Kth smallest: early termination

An iterative inorder terminates as soon as the k-th node is visited. A recursive approach can do the same by threading a counter, but risks stack overflow on a skewed tree with 10⁶ nodes — the iterative form is safer.

### LCA in a BST

For Lowest Common Ancestor in a BST (problem 235), exploit the sorted property: start at root. If both targets are less than the current node, descend left; if both are greater, descend right; otherwise the current node is the LCA. No extra space needed beyond the traversal pointer.

### Pathological insertion order

Inserting an already-sorted sequence into a plain BST degenerates to a linked list (height n), making all operations O(n). Balanced BSTs (Red-Black, AVL, treap) maintain O(log n) by rebalancing; in Python these are available via `sortedcontainers.SortedList`. Almost never asked to implement in interviews — name-drop and move on.

## 6. Complexity

- **Time:** O(h) per operation (search, insert, delete, kth-smallest step) — each operation descends at most one root-to-leaf path of length h. h = O(log n) for a balanced BST, O(n) for a skewed BST.
- **Space:** O(h) — the recursion stack (or explicit stack for iterative inorder) holds at most h frames, one per level of the tree.

## 7. Problem set

- [Easy] [Search in a Binary Search Tree](https://leetcode.com/problems/search-in-a-binary-search-tree/) — entry-level drill for the basic compare-and-descend loop.
- [Easy] [Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) — exploit the BST property to avoid full-tree traversal; O(h) with no extra space.
- [Easy] [Convert Sorted Array to Binary Search Tree](https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/) — build a height-balanced BST from a sorted array using the midpoint as root; reinforces the BST–binary-search duality.
- [Easy] [Range Sum of BST](https://leetcode.com/problems/range-sum-of-bst/) — prune entire subtrees using BST bounds instead of visiting every node.
- [Medium] [Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/) — the canonical range-method problem; common wrong answer is checking only immediate children.
- [Medium] [Insert into a Binary Search Tree](https://leetcode.com/problems/insert-into-a-binary-search-tree/) — straightforward, but must return the root and handle the null-base-case correctly.
- [Medium] [Delete Node in a BST](https://leetcode.com/problems/delete-node-in-a-bst/) — requires correct handling of all three deletion cases; two-children case trips up many candidates.
- [Medium] [Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/) — iterative inorder with early termination; tests whether you can avoid a full traversal.
- [Medium] [Trim a Binary Search Tree](https://leetcode.com/problems/trim-a-binary-search-tree/) — prune out-of-range nodes recursively; requires understanding that an out-of-range node may have valid descendants.
- [Medium] [Binary Search Tree Iterator](https://leetcode.com/problems/binary-search-tree-iterator/) — implement `next()` and `hasNext()` with O(h) space using a lazy iterative inorder stack.
- [Hard] [Recover Binary Search Tree](https://leetcode.com/problems/recover-binary-search-tree/) — two nodes are swapped; find them via inorder scan tracking inversions; O(1) space with Morris traversal.
- [Hard] [Closest Binary Search Tree Value II](https://leetcode.com/problems/closest-binary-search-tree-value-ii/) — return k closest values to a target; combines inorder traversal with a sliding window or two-pointer approach.
- [Hard] [Merge BSTs to Create Single BST](https://leetcode.com/problems/merge-bsts-to-create-single-bst/) — combine multiple small BSTs by matching leaf values to roots; requires careful BST-property validation after merging.

## 8. Related patterns

- [Tree Traversals](traversals.md) — inorder traversal is the backbone of BST sorted-order queries; preorder serialization can reconstruct a BST.
- [DFS](../graphs/dfs.md) — BST validation, insertion, and deletion are all depth-first recursive traversals with pruning; the same stack-based iterative pattern applies.
- [Binary Search](../searching-sorting/binary-search.md) — BST search is binary search on an explicit tree shape; the compare-and-halve logic is identical, just navigated via pointers instead of array indices.
- **[Lowest Common Ancestor](lca.md)** — LCA algorithms generalize across arbitrary binary trees; in a BST the sorted property gives an O(h) shortcut without post-order annotation.

## 9. Interviewer follow-ups

**Q: What if the tree might be unbalanced and have 10⁶ nodes?**
Use the iterative implementation (e.g., `kth_smallest` above) to avoid Python's default recursion limit of ~1 000 frames. For search/insert/delete, iterative variants follow the same compare-and-descend logic with an explicit loop instead of recursion. If balance must be maintained, reach for a self-balancing structure — in Python, `sortedcontainers.SortedList` provides O(log n) ops without coding a Red-Black or AVL tree from scratch.

**Q: What about a persistent BST?**
A persistent (functional) BST supports point-in-time snapshots: instead of mutating nodes in-place, each update creates a new path of O(h) nodes from root to the modified leaf, sharing the rest of the tree with the old version. This gives O(log n) per update with O(log n) extra space per version. Name-drop only in an interview — implementation is out of scope unless the role is explicitly systems-heavy.
