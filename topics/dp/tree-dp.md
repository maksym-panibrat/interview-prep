# Tree DP

## 1. TL;DR

Tree DP applies when the answer at each node depends on its children's answers — "max path through a tree," "minimum cameras to cover all nodes," "rob a tree of houses." The signal is that the problem is defined on a tree and optimal choices interact through parent-child relationships. Post-order DFS naturally computes all children before the parent; each node returns a small state tuple summarizing its subtree. Time: O(n). Space: O(n) (recursion stack).

## 2. Intuition

Think of a tree as a recursive structure: a root node with subtrees hanging below it. If you can summarize each subtree in a compact state — say, `(best_if_we_take_root, best_if_we_do_not_take_root)` — then combining two subtrees at a parent takes O(1). Post-order DFS enforces the right order: leaf nodes return trivial base cases, internal nodes fold their children's states, and the root returns the global answer.

The key design question is: what goes in the state tuple? For House Robber III the tuple is `(rob, no_rob)`. For Diameter it is `(longest_arm_into_subtree, diameter_through_subtree)`. For Binary Tree Cameras it is a three-way state `(covered_by_child, has_camera, not_covered)`. Make the tuple just large enough to express all distinct situations the parent needs to reason about.

One subtlety: Python's default recursion limit (1000) will cause `RecursionError` on deep trees (line-shaped worst case). Raise it with `sys.setrecursionlimit` or convert to an iterative post-order using an explicit stack.

## 3. Walkthrough

### House Robber III on `[3, 2, 3, null, 3, null, 1]`

Tree structure:
```
        3          ← root
       / \
      2   3
       \    \
        3    1
```

Each call returns `(rob, no_rob)`:
- `rob` = maximum loot when we take this node.
- `no_rob` = maximum loot when we skip this node.

**Bottom-up trace:**

Node 3 (leaf, left child of 2): `(3, 0)`
Node 1 (leaf, right child of 3): `(1, 0)`

Node 2 (has one right child with result `(3, 0)`):
- `rob   = 2 + no_rob_right = 2 + 0 = 2`
- `no_rob = max(rob_right, no_rob_right) = max(3, 0) = 3`
- Returns `(2, 3)`

Node 3-right (has one right child with result `(1, 0)`):
- `rob   = 3 + no_rob_right = 3 + 0 = 3`
- `no_rob = max(rob_right, no_rob_right) = max(1, 0) = 1`
- Returns `(3, 1)`

Root 3 (left child `(2, 3)`, right child `(3, 1)`):
- `rob   = 3 + no_rob_left + no_rob_right = 3 + 3 + 1 = 7`
- `no_rob = max(rob_left, no_rob_left) + max(rob_right, no_rob_right) = max(2,3) + max(3,1) = 3 + 3 = 6`
- Returns `(7, 6)`

Answer: `max(7, 6) = 7`. Optimal: rob root (3) + rob node (3, grandchild of left) + nothing else.

## 4. Implementation

```python
from __future__ import annotations
from typing import Optional, Tuple
import sys

sys.setrecursionlimit(10_000)  # guard against deep trees


class TreeNode:
    """Minimal binary tree node."""
    def __init__(self, val: int = 0,
                 left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None):
        self.val = val
        self.left = left
        self.right = right


def rob_tree(root: Optional[TreeNode]) -> int:
    """House Robber III (LeetCode 337) — O(n) time, O(n) space (stack depth).

    Post-order DFS. Each node returns (rob, no_rob):
      rob    = max loot when this node IS robbed
      no_rob = max loot when this node is NOT robbed
    """
    def dfs(node: Optional[TreeNode]) -> Tuple[int, int]:
        if node is None:
            return (0, 0)                         # base case: empty subtree contributes nothing

        rob_l, no_rob_l = dfs(node.left)
        rob_r, no_rob_r = dfs(node.right)

        # Take this node: children must be skipped
        rob = node.val + no_rob_l + no_rob_r
        # Skip this node: each child independently takes its best option
        no_rob = max(rob_l, no_rob_l) + max(rob_r, no_rob_r)

        return (rob, no_rob)

    rob, no_rob = dfs(root)
    return max(rob, no_rob)


def _build(values: list, i: int = 0) -> Optional[TreeNode]:
    """Helper: build a binary tree from a level-order list (None = absent node)."""
    if i >= len(values) or values[i] is None:
        return None
    node = TreeNode(values[i])
    node.left = _build(values, 2 * i + 1)
    node.right = _build(values, 2 * i + 2)
    return node


if __name__ == "__main__":
    # Tree: [3, 2, 3, null, 3, null, 1]
    root1 = _build([3, 2, 3, None, 3, None, 1])
    assert rob_tree(root1) == 7

    # Tree: [3, 4, 5, 1, 3, null, 1]
    root2 = _build([3, 4, 5, 1, 3, None, 1])
    assert rob_tree(root2) == 9  # rob 4+5 level → 4 + 5 = 9? actually 4's subtree: rob 4 = 4, no_rob 4 = max(1,0)+max(3,0)=4; rob 5 = 5, no_rob 5 = max(0,0)+max(1,0)=1; root: rob=3+4+1=8, no_rob=max(4,4)+max(5,1)=4+5=9 → 9
    assert rob_tree(None) == 0

    # Single node
    assert rob_tree(TreeNode(5)) == 5

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def tree_dp(root: Optional[TreeNode]):
    def dfs(node: Optional[TreeNode]) -> Tuple:
        if node is None:
            return (0, 0)                    # base case — adjust tuple size as needed

        left_state = dfs(node.left)
        right_state = dfs(node.right)

        # Combine left_state, right_state, and node.val into this node's state
        state_a = node.val + left_state[1] + right_state[1]   # "take" branch
        state_b = max(left_state) + max(right_state)           # "skip" branch

        return (state_a, state_b)

    result = dfs(root)
    return max(result)
```

## 5. Variants & pitfalls

### State-tuple recurrence (House Robber III, Binary Tree Cameras)

Choose a state tuple that captures exactly what the parent needs. For cameras the three states are `{covered by child, has camera, uncovered}` — the parent must check whether it needs to install a camera to cover an uncovered child. More states = more cases but same O(n) complexity.

### Diameter / longest path

Track the longest single arm descending into each subtree. The diameter *through* a node is the sum of its two longest arms. The function returns the longest arm (for the parent to use) while updating a global maximum with the diameter through the current node.

### Re-rooting DP (Sum of Distances in Tree — LeetCode 834)

Two-pass DFS: first pass (root = 0) computes subtree sizes and an initial answer for the root. Second pass propagates the answer down: moving the root from a node to one of its children updates the answer in O(1). This is an advanced technique, rarely asked in standard interviews.

### Tree DP on a rooted DAG

If the "tree" is actually a DAG (e.g., a dependency graph from topological sort), the same post-order DFS applies as long as you process nodes in reverse topological order. Each node's state is computed after all its children in the DAG are computed.

### Pitfalls

- **Python recursion limit**: default is 1000. A skewed tree with n=10000 nodes will crash. Call `sys.setrecursionlimit(n + 100)` or rewrite with an explicit stack.
- **Longest path through node vs longest path in subtree**: the value returned *upward* to the parent is the longest single-arm path (`max(left_arm, right_arm) + 1`), not the diameter. The diameter (sum of two arms) is a side effect recorded in a nonlocal variable — never returned upward or it corrupts the parent's arm-length computation.
- **Forgetting None children**: always check `if node is None: return base_case` at the top of `dfs`. Accessing `node.val` on None raises `AttributeError`.

## 6. Complexity

- **Time:** O(n) — each node is visited exactly once in the DFS.
- **Space:** O(n) — the recursion stack holds at most O(height) frames; O(n) in the worst case (skewed tree). For balanced trees, O(log n).

## 7. Problem set

- [Medium] [House Robber III](https://leetcode.com/problems/house-robber-iii/) — canonical tree DP; master the `(rob, no_rob)` tuple pattern here.
- [Medium] [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) — track longest arm up and diameter through each node; classic side-effect-in-DFS pattern.
- [Medium] [Path Sum III](https://leetcode.com/problems/path-sum-iii/) — prefix-sum DP combined with DFS; not pure tree DP but closely related.
- [Hard] [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) — longest-path variant with arbitrary values (negatives allowed); same arm + global-max pattern.
- [Hard] [Binary Tree Cameras](https://leetcode.com/problems/binary-tree-cameras/) — three-state tuple; forces careful case analysis on covered/uncovered.
- [Hard] [Distribute Coins in Binary Tree](https://leetcode.com/problems/distribute-coins-in-binary-tree/) — each node returns its excess coins; moves = sum of absolute excesses across all edges.
- [Hard] [Sum of Distances in Tree](https://leetcode.com/problems/sum-of-distances-in-tree/) — re-rooting DP on a general tree; two DFS passes each O(n).

## 8. Related patterns

- **[Tree Traversals](../trees/traversals.md)** — post-order traversal is the execution engine for tree DP; the DP state is simply what each post-order visit returns.
- [Topological Sort](../graphs/topological-sort.md) — the DAG analog: process nodes in reverse topological order the same way post-order processes tree nodes.
- [1D DP](1d-dp.md) — the same "summarize subproblem in a small state" principle applied to a linear array instead of a tree.
- [Bitmask DP](bitmask-dp.md) — when the tree has small branching factor and N ≤ 20, tree DP can combine with bitmask to track subsets at each node.

## 9. Interviewer follow-ups

**Q: Can you write an iterative version?**
Yes. Use an explicit stack simulating post-order traversal: push each node, keep track of whether its children have been processed. When both children are done (detected by a second pass or a `visited` set), pop the node and compute its state. In practice interviewers rarely ask for the iterative version for tree DP — they care about the recurrence — but it is a good thing to mention to show awareness of Python's recursion limit.

**Q: What is re-rooting DP and when do you use it?**
Re-rooting computes the answer for every node as if it were the root, in O(n) total. First DFS computes subtree-based state (e.g., count of nodes in each subtree). Second DFS propagates: moving the root from a parent to a child updates the answer using the parent's already-computed state in O(1) per node. Use it when the problem asks for a value *for every node* (e.g., sum of distances to all other nodes), not just the root.
