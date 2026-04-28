# Tree Traversals

## 1. TL;DR

Tree traversal applies whenever you need to visit every node in a binary tree: serialize/deserialize, convert a tree to a list, or check a structural property. The signal is "binary-tree shaped," "visit all nodes," or "process in some order." Four canonical orders exist — pre-, in-, post-, and level-order — each with a recursive one-liner and a tractable iterative counterpart. Time: O(n). Space: O(h) where h is tree height (O(log n) balanced, O(n) worst-case).

## 2. Intuition

Think of each traversal as answering "when do I process the current node relative to its children?"

- **Preorder (root → left → right):** process now, recurse later. Good for serialization (root first = easy reconstruction) and copying a tree.
- **Inorder (left → root → right):** process in the middle. For a BST this produces a sorted list — the defining property.
- **Postorder (left → right → root):** process after both children. Good for computing subtree values (e.g., tree height, subtree sum) where you need children's answers first.
- **Level-order (BFS):** process row by row. Good for "k-th level," right-side view, minimum depth, and anything that needs proximity-to-root.

For iterative implementations: use an explicit **stack** (LIFO) to mimic the call stack for pre/in/post; use a **queue** (FIFO) for level-order.

## 3. Walkthrough

### Example tree: `[1, 2, 3, 4, 5, 6, 7]` (complete binary tree, level-order insertion)

```
        1
      /   \
     2     3
    / \   / \
   4   5 6   7
```

| Traversal  | Output              |
|------------|---------------------|
| Preorder   | [1, 2, 4, 5, 3, 6, 7] |
| Inorder    | [4, 2, 5, 1, 6, 3, 7] |
| Postorder  | [4, 5, 2, 6, 7, 3, 1] |
| Level-order| [1, 2, 3, 4, 5, 6, 7] |

### Iterative inorder — step by step

Maintain a stack and a current pointer `curr`. Push nodes as you walk left; when you can't go further, pop and record, then move right.

```
Stack: []        curr: 1
  → push 1, walk left → curr=2
  → push 2, walk left → curr=4
  → push 4, walk left → curr=None
  → pop 4, record 4, move right → curr=None
  → pop 2, record 2, move right → curr=5
  → push 5, walk left → curr=None
  → pop 5, record 5, move right → curr=None
  → pop 1, record 1, move right → curr=3
  → push 3, walk left → curr=6
  → push 6, walk left → curr=None
  → pop 6, record 6, move right → curr=None
  → pop 3, record 3, move right → curr=7
  → push 7, walk left → curr=None
  → pop 7, record 7, move right → curr=None
  → stack empty, done
Result: [4, 2, 5, 1, 6, 3, 7]
```

## 4. Implementation

```python
from __future__ import annotations
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val: int = 0,
                 left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def preorder(root: Optional[TreeNode]) -> List[int]:
    """Iterative preorder: root → left → right."""
    if root is None:
        return []
    result: List[int] = []
    stack = [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        # push right first so left is processed first (LIFO)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result


def inorder(root: Optional[TreeNode]) -> List[int]:
    """Iterative inorder: left → root → right."""
    result: List[int] = []
    stack: List[TreeNode] = []
    curr = root
    while curr is not None or stack:
        while curr is not None:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result


def postorder(root: Optional[TreeNode]) -> List[int]:
    """Iterative postorder: left → right → root.

    Two-stack approach: push root to stack1, mirror to stack2 (root → right → left),
    then reverse stack2 to get left → right → root order.
    """
    if root is None:
        return []
    stack1 = [root]
    stack2: List[TreeNode] = []
    while stack1:
        node = stack1.pop()
        stack2.append(node)
        if node.left:
            stack1.append(node.left)
        if node.right:
            stack1.append(node.right)
    return [n.val for n in reversed(stack2)]


def level_order(root: Optional[TreeNode]) -> List[int]:
    """BFS level-order traversal. Returns flat list."""
    if root is None:
        return []
    result: List[int] = []
    queue: deque = deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result


if __name__ == "__main__":
    # Build [1, 2, 3, 4, 5, 6, 7]
    #        1
    #      /   \
    #     2     3
    #    / \   / \
    #   4   5 6   7
    n4, n5, n6, n7 = TreeNode(4), TreeNode(5), TreeNode(6), TreeNode(7)
    n2 = TreeNode(2, n4, n5)
    n3 = TreeNode(3, n6, n7)
    root = TreeNode(1, n2, n3)

    assert preorder(root)    == [1, 2, 4, 5, 3, 6, 7], preorder(root)
    assert inorder(root)     == [4, 2, 5, 1, 6, 3, 7], inorder(root)
    assert postorder(root)   == [4, 5, 2, 6, 7, 3, 1], postorder(root)
    assert level_order(root) == [1, 2, 3, 4, 5, 6, 7], level_order(root)

    # Edge: single node
    single = TreeNode(42)
    assert preorder(single)    == [42]
    assert inorder(single)     == [42]
    assert postorder(single)   == [42]
    assert level_order(single) == [42]

    # Edge: None
    assert preorder(None)    == []
    assert inorder(None)     == []
    assert postorder(None)   == []
    assert level_order(None) == []

    print("All smoke tests passed.")
```

**Template:**

```python
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def preorder(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    result, stack = [], [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result


def inorder(root: Optional[TreeNode]) -> List[int]:
    result, stack, curr = [], [], root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result


def postorder(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    stack1, stack2 = [root], []
    while stack1:
        node = stack1.pop()
        stack2.append(node)
        if node.left:
            stack1.append(node.left)
        if node.right:
            stack1.append(node.right)
    return [n.val for n in reversed(stack2)]


def level_order(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result
```

## 5. Variants & pitfalls

### Morris traversal (O(1) space)
An advanced technique that temporarily threads right-child pointers to inorder successors, allowing traversal without a stack or recursion. Name-drop in interviews when asked about O(1) space; rarely expected to be coded from memory.

### Reconstruction from two traversals
Given preorder + inorder (or postorder + inorder), you can reconstruct a unique binary tree — provided all node values are distinct. Preorder tells you the root; inorder splits the remaining nodes into left and right subtrees. Recurse. (LeetCode 105, 106.)

### Right-side view / vertical order (BFS variants)
Level-order BFS with a minor twist: right-side view keeps only the *last* node per level; vertical-order groups by column index tracked during traversal. Both are standard interview BFS problems (LeetCode 199).

### Serialization formats
- Level-order with `null` markers (LeetCode's own format): compact, easy to implement with a queue.
- Preorder with sentinel (e.g., `#`): one pass, elegant recursive codec. Used in LeetCode 297.

### Pitfalls
- **Recursive depth vs. stack space:** recursion depth = tree height. Unbalanced trees can cause `RecursionError` in Python at ~1000 nodes; prefer iterative for large inputs.
- **Iterative postorder is the trickiest:** the two-stack method above is easiest to remember. The single-stack "last-visited" variant works but requires careful bookkeeping — track the previously visited node and check if you're returning from the right subtree.
- **Reconstruction requires unique values:** if duplicates exist, two traversals don't define a unique tree.

## 6. Complexity

- **Time:** O(n) — every node is visited exactly once.
- **Space:** O(h) — the stack (or call stack) grows proportional to tree height h; O(log n) for a balanced tree, O(n) worst-case (skewed tree).

## 7. Problem set

- [Easy] [Binary Tree Inorder Traversal](https://leetcode.com/problems/binary-tree-inorder-traversal/) — drills the iterative stack pattern end-to-end.
- [Easy] [Binary Tree Preorder Traversal](https://leetcode.com/problems/binary-tree-preorder-traversal/) — simplest iterative form; good entry point.
- [Easy] [Binary Tree Postorder Traversal](https://leetcode.com/problems/binary-tree-postorder-traversal/) — forces you to handle the hardest order iteratively.
- [Easy] [Same Tree](https://leetcode.com/problems/same-tree/) — simultaneous traversal of two trees; tests structural comparison.
- [Easy] [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) — DFS/BFS both work; compare approaches.
- [Medium] [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) — BFS with level grouping; template for all level-based problems.
- [Medium] [Binary Tree Zigzag Level Order Traversal](https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/) — BFS with alternating direction per level.
- [Medium] [Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/) — reconstruction; root-finding + recursive split.
- [Medium] [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) — BFS variant: keep last node per level.
- [Medium] [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) — combines preorder traversal with sentinel encoding; end-to-end design problem.
- [Hard] [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) — postorder DFS returning subtree max gain; classic Tree DP.
- [Hard] [Recover Binary Search Tree](https://leetcode.com/problems/recover-binary-search-tree/) — two swapped nodes found via inorder; optimal solution uses Morris traversal.

## 8. Related patterns

- [Tree DP](../dp/tree-dp.md) — post-order traversal is the backbone of tree DP; each node combines results from its children.
- [BFS](../graphs/bfs.md) — level-order traversal is BFS applied to a tree; the same queue-based skeleton applies.
- [DFS](../graphs/dfs.md) — preorder/inorder/postorder are all DFS variants; the graph DFS template generalizes here.
- **[BST](bst.md)** — inorder traversal of a BST yields a sorted sequence; BST operations depend heavily on traversal order.
- **[LCA](lca.md)** — lowest-common-ancestor algorithms rely on post-order recursive traversal.

## 9. Interviewer follow-ups

**Q: How would you implement iterative postorder without two stacks?**
Use a single stack with a `last_visited` pointer. Pop a node only when its right child is null or was the last visited node. Otherwise, push the node back (or leave it) and descend into the right subtree. This avoids the second stack at the cost of extra bookkeeping — acceptable but error-prone under pressure.

**Q: How do you reconstruct a binary tree from preorder + inorder traversals?**
The first element of preorder is the root. Find it in inorder; everything to the left is the left subtree, everything to the right is the right subtree. Recurse with the corresponding preorder slices. Use a hashmap to index inorder positions for O(n) total.

**Q: What is Morris traversal and why does it matter?**
Morris traversal achieves O(n) time and O(1) space by temporarily modifying the tree: for each node, if it has a left subtree, find the inorder predecessor and set its right pointer to the current node. After visiting, the threading is removed. It appears on LeetCode 99 (Recover BST) but is rarely expected to be coded from scratch in 45 minutes.
