# Lowest Common Ancestor

## 1. TL;DR

LCA (Lowest Common Ancestor) finds the deepest node that is an ancestor of both target nodes in a tree. The signal is "lowest common ancestor of two nodes," "distance between two nodes in a tree," or "shortest path between two nodes in an undirected tree." Recursive post-order DFS is the workhorse: return the current node if it matches either target; otherwise combine results from left and right subtrees — if both sides return non-null, the current node is the LCA. Time: O(n) per query. Space: O(h) recursion stack.

## 2. Intuition

Picture the tree as a family tree. The LCA of two people is their most recent common ancestor — the deepest node you reach before the family line splits to include one person on the left and the other on the right.

The recursive insight: do a post-order DFS. At each node, ask both children "does your subtree contain p or q?" When both children say yes (non-null), the current node is the crossroads — it is the LCA. When only one child says yes, bubble that answer upward because the crossroads must be higher in the tree (or the current node is itself one of the targets).

The short-circuit: if the current node is `p` or `q`, return it immediately. You do not need to descend further — even if the other target is a descendant, this node is still the shallowest point that covers both, so it is the LCA by definition.

For a **BST**, you can exploit the sorted order: if both targets are smaller than the current node, descend left; if both are larger, descend right; otherwise the current node straddles the two targets and is the LCA. This requires no ancestor tracking and runs in O(h).

## 3. Walkthrough

### Example tree — LeetCode 236

```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4
```

Array representation: `[3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]`.

#### Case 1: LCA(5, 1) = 3

Node 5 is in the left subtree; node 1 is in the right subtree. At node 3: left DFS returns 5, right DFS returns 1 — both non-null, so node 3 is the LCA.

#### Case 2: LCA(5, 4) = 5 — full trace

`p = node(5)`, `q = node(4)`.

```
lca(3, p=5, q=4)
  → lca(5, p=5, q=4)   [descend left of 3]
      node==p → return node(5)     # short-circuit: node IS p
  → lca(1, p=5, q=4)   [descend right of 3]
      → lca(0, ...) → null
      → lca(8, ...) → null
      ← left=null, right=null → return null
  ← left=node(5), right=null → return node(5)
← return node(5)
```

Step-by-step return values bubbling up:

| Call site | Left result | Right result | Returns |
|-----------|-------------|--------------|---------|
| `lca(5, …)` | — | — | `node(5)` (short-circuit: node IS p) |
| `lca(1, …)` | null (node 0) | null (node 8) | `null` |
| `lca(3, …)` | `node(5)` | `null` | `node(5)` |

Result: **5**.

## 4. Implementation

```python
from __future__ import annotations
from typing import Optional


class TreeNode:
    def __init__(self, val: int = 0,
                 left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def lca(root: Optional[TreeNode],
        p: TreeNode,
        q: TreeNode) -> Optional[TreeNode]:
    """Recursive LCA for a general binary tree.

    Assumes both p and q exist in the tree.
    Post-order: combine children's answers at each node.
    """
    if root is None:
        return None
    # Short-circuit: if this node is one of the targets, return it.
    # Even if the other target is a descendant, this node is still the LCA.
    if root is p or root is q:
        return root

    left = lca(root.left, p, q)
    right = lca(root.right, p, q)

    if left is not None and right is not None:
        # p and q live in different subtrees → current node is the LCA
        return root
    # Return whichever side found something (or None if neither did)
    return left if left is not None else right


def lca_bst(root: Optional[TreeNode],
            p: TreeNode,
            q: TreeNode) -> Optional[TreeNode]:
    """LCA specialized for a Binary Search Tree.

    Exploits BST ordering: no ancestor sets needed, O(h) time.
    """
    node = root
    while node is not None:
        if p.val < node.val and q.val < node.val:
            node = node.left   # both targets are in the left subtree
        elif p.val > node.val and q.val > node.val:
            node = node.right  # both targets are in the right subtree
        else:
            # node.val is between p.val and q.val (inclusive) → node is LCA
            return node
    return None  # p or q not in tree (shouldn't happen per problem constraints)


if __name__ == "__main__":
    # Build the LC 236 example tree:
    #         3
    #        / \
    #       5   1
    #      / \ / \
    #     6  2 0  8
    #       / \
    #      7   4
    n7, n4 = TreeNode(7), TreeNode(4)
    n6 = TreeNode(6)
    n2 = TreeNode(2, n7, n4)
    n0, n8 = TreeNode(0), TreeNode(8)
    n5 = TreeNode(5, n6, n2)
    n1 = TreeNode(1, n0, n8)
    root = TreeNode(3, n5, n1)

    # General binary tree LCA
    assert lca(root, n5, n1) is root,  "LCA(5,1) should be 3"
    assert lca(root, n5, n4) is n5,    "LCA(5,4) should be 5"
    assert lca(root, n6, n4) is n5,    "LCA(6,4) should be 5"
    assert lca(root, n7, n4) is n2,    "LCA(7,4) should be 2"
    assert lca(root, n6, n8) is root,  "LCA(6,8) should be 3"

    # BST LCA (reuse the same tree; it happens to be a valid BST for this check
    # only for adjacent nodes — use a proper BST instead)
    #   Build a small BST: 6 -> (2,8) -> (0,4,7,9)
    b0, b4, b7, b9 = TreeNode(0), TreeNode(4), TreeNode(7), TreeNode(9)
    b2 = TreeNode(2, b0, b4)
    b8 = TreeNode(8, b7, b9)
    bst_root = TreeNode(6, b2, b8)

    assert lca_bst(bst_root, b0, b4) is b2,       "BST LCA(0,4) should be 2"
    assert lca_bst(bst_root, b0, b9) is bst_root, "BST LCA(0,9) should be 6"
    assert lca_bst(bst_root, b7, b9) is b8,       "BST LCA(7,9) should be 8"
    assert lca_bst(bst_root, b2, b8) is bst_root, "BST LCA(2,8) should be 6"

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


def lca(root: Optional[TreeNode],
        p: TreeNode,
        q: TreeNode) -> Optional[TreeNode]:
    if root is None:
        return None
    if root is p or root is q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left is not None and right is not None:
        return root
    return left if left is not None else right


def lca_bst(root: Optional[TreeNode],
            p: TreeNode,
            q: TreeNode) -> Optional[TreeNode]:
    node = root
    while node is not None:
        if p.val < node.val and q.val < node.val:
            node = node.left
        elif p.val > node.val and q.val > node.val:
            node = node.right
        else:
            return node
    return None
```

## 5. Variants & pitfalls

### Recursive — general binary tree (workhorse)

The implementation above. Assumes both `p` and `q` exist in the tree. Time O(n), space O(h).

### BST-specific (LC 235)

Compare values: descend left if both targets are smaller, right if both are larger, return current node otherwise. No visited set, no ancestor tracking. O(h) time without extra space.

### With parent pointers (LC 1650)

Walk from `p` upward collecting ancestors into a set. Then walk from `q` upward until you hit a node already in the set — that is the LCA. O(h) time, O(h) space for the ancestor set.

### Iterative two-pointer balance walk (LC 1650 — cycle-detection trick)

Like the linked-list cycle trick: start two pointers at `p` and `q`. At each step, advance each pointer to its parent; when a pointer reaches the root, redirect it to the other starting node. Both pointers will meet at the LCA after at most `depth(p) + depth(q)` steps. O(h) time, O(1) space beyond the parent-pointer structure.

### Missing nodes — verify after recursion (LC 1644)

When the problem states that `p` or `q` may not exist in the tree, the naive recursion can return a false positive (returns `p` even when `q` is absent). Fix: track a `found_p` and `found_q` flag during recursion; only trust the returned node if both flags are set at the end.

### Euler tour + RMQ (offline, many queries)

Perform an Euler tour (in-order traversal that revisits nodes when backtracking), recording `(depth, node)` at each step. `LCA(u, v)` is the minimum-depth entry between `u`'s first occurrence and `v`'s first occurrence. Use a sparse table (built in O(n log n)) for O(1) range-minimum queries. Total: O(n log n) preprocessing, O(1) per query.

### Binary lifting (name-drop)

Pre-compute `up[v][k]` = 2^k-th ancestor of node `v` using `up[v][k] = up[up[v][k-1]][k-1]`. Jump both nodes to equal depth, then binary-search upward together. O(n log n) prep, O(log n) per query.

### Pitfalls

- **Assuming nodes always exist:** LC 1644 explicitly allows one or both nodes to be absent. The standard recursion returns a misleading result — add existence flags.
- **Confusing LCA with "any common ancestor":** the problem asks for the *deepest* one. The root is always a common ancestor but is rarely the answer.
- **BST shortcut applied to a non-BST:** `lca_bst` is only correct when the tree satisfies the BST invariant. Applying it to a general binary tree gives wrong answers.
- **Identity vs. value comparison:** `lca` compares nodes by identity (`is`), not by value. Two distinct nodes with the same value are treated as different targets — this matches LeetCode's constraint that node references are passed in.

## 6. Complexity

- **Time:** O(n) for recursive general-binary-tree LCA — every node is visited at most once; O(h) for BST LCA and parent-pointer LCA since we descend or ascend the height; O(1) per query after O(n log n) preprocessing for Euler+RMQ or binary lifting.
- **Space:** O(h) recursion stack for the recursive variant (O(log n) balanced, O(n) skewed); O(1) extra for BST iterative; O(n log n) for binary lifting ancestor table.

## 7. Problem set

- [Easy] [Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) — pure BST comparison shortcut; no recursion or visited set needed.
- [Medium] [Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) — the canonical post-order recursive template; must master this cold.
- [Medium] [Lowest Common Ancestor of a Binary Tree II](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree-ii/) — handle the case where p or q may not exist; teaches the existence-flag fix.
- [Medium] [Lowest Common Ancestor of a Binary Tree III](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree-iii/) — parent pointers available; two-pointer balance walk is the cleanest solution.
- [Medium] [Smallest Subtree with all the Deepest Nodes](https://leetcode.com/problems/smallest-subtree-with-all-the-deepest-nodes/) — equivalent to LCA of all deepest leaves; post-order returning (depth, node) pairs.
- [Hard] [Lowest Common Ancestor of Deepest Leaves](https://leetcode.com/problems/lowest-common-ancestor-of-deepest-leaves/) — same insight as 865 under a different name; teaches the depth-tracking post-order pattern.
- [Hard] [Lowest Common Ancestor of a Binary Tree IV](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree-iv/) — multiple target nodes stored in a set; generalize the two-target check to `node in targets`.

## 8. Related patterns

- [Tree Traversals](traversals.md) — post-order DFS is the direct backbone of the recursive LCA algorithm; review traversal patterns first.
- [Binary Search Tree](bst.md) — BST-specific LCA exploits the sorted-order invariant; understanding BST search is a prerequisite.
- [DFS](../graphs/dfs.md) — the recursive LCA is a specialized DFS; the graph DFS template generalizes to trees naturally.
- **[Segment Tree & Fenwick Tree](segment-tree-fenwick.md)** — the Euler tour + RMQ approach reduces LCA to a range-minimum query, which a sparse table or segment tree answers in O(1) or O(log n) respectively.

## 9. Interviewer follow-ups

**Q: What if you have ~10⁵ queries on a fixed tree?**
O(n) per query becomes O(n · 10⁵) — too slow. Use **binary lifting**: precompute `up[v][k]` = 2^k-th ancestor for all nodes v and levels k (0 ≤ k ≤ log n). Build table via `up[v][k] = up[up[v][k-1]][k-1]`. To find LCA(u, v): first bring both to equal depth using binary jumps, then binary-search upward together until they meet. O(n log n) preprocessing, O(log n) per query. Alternatively use Euler tour + sparse-table RMQ for O(1) per query at the cost of a larger constant.

**Q: How do you find the distance between two nodes?**
`distance(u, v) = depth(u) + depth(v) - 2 * depth(LCA(u, v))`. Compute node depths in one DFS pass, then answer each query in O(n) (or O(log n) with binary lifting).

**Q: How would you handle a forest (multiple disconnected trees)?**
Run LCA within each tree component independently. If `u` and `v` belong to different components, their LCA is undefined (or you can designate a virtual root connecting all trees and redefine LCA relative to that sentinel). Identify components first via union-find or DFS, then dispatch to the appropriate tree's LCA routine.
