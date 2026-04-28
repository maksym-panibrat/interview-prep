# Grid Backtracking

## 1. TL;DR

Grid backtracking applies when you need to **find a word (or words) in a 2-D grid**, **explore connected regions with reversal**, or **count paths that must visit every cell**. The signal is "find a word in a grid," "all paths in a grid with constraints," or "explore connected region with reversal" — whenever plain DFS isn't enough because you need to revisit cells across different paths. Key technique: **mutate-restore** — temporarily mark a cell visited (overwrite with `#`), recurse to neighbors, unmark on the way out. Pair with a trie when searching for many patterns at once (Word Search II). Time: O(M·N·4^L) where L is word length; pruning reduces this sharply on real inputs. Space: O(L) recursion depth.

## 2. Intuition

Imagine tracing the word "ABCCED" with your finger on a grid. You step onto 'A', keep your finger there (so you can't reuse that cell), move to each adjacent cell, and try to continue the match. When a path fails you lift your finger and try another direction from the parent cell. That "lift your finger" action is the restore step — without it, sibling paths would see a falsely-visited cell and miss valid routes.

The grid is the implicit decision tree: at each node (cell, word-index) you have up to four children (the four neighbors). The backtracking skeleton is identical to the general template — the only change is that your "state" is the grid itself, mutated in-place rather than a separate visited set. Mutate-restore is strictly cheaper than keeping a separate `visited` set because it uses O(1) extra memory and avoids a set lookup.

Three questions structure every grid-backtracking problem:

1. **What is a "choice"?** Move to any unvisited adjacent cell that matches the next character (or any constraint).
2. **When is the path complete?** All characters matched (or all cells visited for Unique Paths III).
3. **When can you prune?** Out-of-bounds, character mismatch, already-visited cell.

## 3. Walkthrough

### Word Search: board = `[['A','B','C'],['S','F','C'],['A','D','E']]`, word = `"ABCCED"`

```
Board (indices):
  (0,0)A  (0,1)B  (0,2)C
  (1,0)S  (1,1)F  (1,2)C
  (2,0)A  (2,1)D  (2,2)E
```

**Successful path:**

| step | cell   | char | action                                    |
|------|--------|------|-------------------------------------------|
| 0    | (0,0)  | 'A'  | matches word[0]. Mark (0,0)='#'. Recurse. |
| 1    | (0,1)  | 'B'  | matches word[1]. Mark (0,1)='#'. Recurse. |
| 2    | (0,2)  | 'C'  | matches word[2]. Mark (0,2)='#'. Recurse. |
| 3    | (1,2)  | 'C'  | matches word[3]. Mark (1,2)='#'. Recurse. |
| 4    | (2,2)  | 'E'  | matches word[4]. Mark (2,2)='#'. Recurse. |
| 5    | (2,1)  | 'D'  | matches word[5]. All 6 chars matched — return True. |

Board after matching (shown with marks): `['#','#','#'] / ['S','F','#'] / ['A','D','#']`. On return the marks are restored, but since we found the answer we propagate True immediately.

**False path (early backtrack):**

| step | cell   | char | action                                        |
|------|--------|------|-----------------------------------------------|
| 0    | (0,0)  | 'A'  | matches word[0]. Mark (0,0)='#'. Recurse.     |
| 1    | (0,1)  | 'B'  | matches word[1]. Mark (0,1)='#'. Recurse.     |
| 2    | (1,1)  | 'F'  | 'F' != word[2]='C'. Return False immediately. |
|      |        |      | Restore (0,1)='B'. Try next neighbor of (0,0).|
|      |        |      | (eventually) Restore (0,0)='A'. Try next start.|

The restore on the way out is essential: without restoring (0,1), a subsequent path starting at a different cell would incorrectly see (0,1) as visited.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def word_search(board: List[List[str]], word: str) -> bool:
    """Return True if word exists in board, using mutate-restore backtracking.

    Standard Word Search (LeetCode 79).  Time: O(M*N*4^L).  Space: O(L).
    """
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True  # all characters matched
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False  # out of bounds
        if board[r][c] != word[idx]:
            return False  # character mismatch or already visited ('#')

        # Mutate: mark cell as visited
        tmp, board[r][c] = board[r][c], "#"

        found = (
            dfs(r + 1, c, idx + 1)
            or dfs(r - 1, c, idx + 1)
            or dfs(r, c + 1, idx + 1)
            or dfs(r, c - 1, idx + 1)
        )

        # Restore: unmark cell before returning to caller
        board[r][c] = tmp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


# ---------------------------------------------------------------------------
# Trie node used by word_search_ii
# ---------------------------------------------------------------------------

class _TrieNode:
    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: dict = {}
        self.word = None  # non-None at end of a word


def word_search_ii(board: List[List[str]], words: List[str]) -> List[str]:
    """Return all words from `words` that appear in `board`.

    Word Search II (LeetCode 212).  Build a trie of all target words, then run
    a single DFS pass over the grid, walking the trie alongside the board.
    When a complete word is found, record it and remove its leaf from the trie
    to avoid duplicates and prune further matching along that branch.

    Time: O(M*N*4^L) per starting cell in the worst case, but trie pruning
    keeps practical runtime far below that.  Space: O(N*L) for the trie.
    """
    # Build trie
    root = _TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        node.word = w

    rows, cols = len(board), len(board[0])
    found: List[str] = []

    def dfs(r: int, c: int, node: _TrieNode) -> None:
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        ch = board[r][c]
        if ch == "#" or ch not in node.children:
            return  # visited or no trie branch for this character

        child = node.children[ch]

        if child.word is not None:
            found.append(child.word)
            child.word = None  # de-duplicate: don't report the same word twice

        # Mutate-restore
        board[r][c] = "#"
        dfs(r + 1, c, child)
        dfs(r - 1, c, child)
        dfs(r, c + 1, child)
        dfs(r, c - 1, child)
        board[r][c] = ch

        # Prune: if this trie node has no children left and no word, remove it
        # from parent to avoid exploring dead branches in future DFS calls.
        if not child.children and child.word is None:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)

    return found


if __name__ == "__main__":
    # --- word_search smoke tests ---
    board1 = [["A", "B", "C"], ["S", "F", "C"], ["A", "D", "E"]]
    assert word_search(board1, "ABCCED") is True
    assert word_search(board1, "SEE") is True
    assert word_search(board1, "ABCB") is False  # cannot reuse (0,1)

    board2 = [["A"]]
    assert word_search(board2, "A") is True
    assert word_search(board2, "B") is False

    # --- word_search_ii smoke tests ---
    board3 = [
        ["o", "a", "a", "n"],
        ["e", "t", "a", "e"],
        ["i", "h", "k", "r"],
        ["i", "f", "l", "v"],
    ]
    words3 = ["oath", "pea", "eat", "rain"]
    result3 = sorted(word_search_ii(board3, words3))
    assert result3 == ["eat", "oath"], f"got {result3}"

    board4 = [["a", "b"], ["c", "d"]]
    result4 = sorted(word_search_ii(board4, ["abcd", "abdc", "acdb", "dcba", "xyz"]))
    assert result4 == ["abcd", "abdc", "acdb", "dcba"], f"got {result4}"

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def word_search(board: List[List[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        tmp, board[r][c] = board[r][c], "#"
        found = (
            dfs(r + 1, c, idx + 1) or dfs(r - 1, c, idx + 1)
            or dfs(r, c + 1, idx + 1) or dfs(r, c - 1, idx + 1)
        )
        board[r][c] = tmp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


class _TrieNode:
    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: dict = {}
        self.word = None


def word_search_ii(board: List[List[str]], words: List[str]) -> List[str]:
    root = _TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        node.word = w

    rows, cols = len(board), len(board[0])
    found: List[str] = []

    def dfs(r: int, c: int, node: _TrieNode) -> None:
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        ch = board[r][c]
        if ch == "#" or ch not in node.children:
            return
        child = node.children[ch]
        if child.word is not None:
            found.append(child.word)
            child.word = None
        board[r][c] = "#"
        dfs(r + 1, c, child)
        dfs(r - 1, c, child)
        dfs(r, c + 1, child)
        dfs(r, c - 1, child)
        board[r][c] = ch
        if not child.children and child.word is None:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)
    return found
```

## 5. Variants & pitfalls

### Single word search (mutate-restore)

The canonical pattern: overwrite `board[r][c]` with a sentinel (`'#'`) before recursing, restore it after. The sentinel must be a character that cannot appear in the word so that any neighbor trying to revisit the cell will fail the `board[r][c] != word[idx]` guard. Restoring unconditionally (regardless of whether the recursion succeeded) is the key discipline — the board must look pristine to every sibling path.

### Word Search II (trie + DFS)

Build one trie from all target words, then run a single DFS across the grid, walking the trie node alongside the grid position. This amortizes the per-character matching cost across all words simultaneously. Two extra optimizations compound dramatically: (1) when a word is found, set `node.word = None` to prevent duplicates; (2) when a trie leaf becomes empty (no children and no word), delete it from its parent — subsequent DFS calls skip that branch entirely.

### Unique Paths III (visit-all variant)

Count paths from start to end that visit every non-obstacle cell exactly once. The base case fires only when all empty cells are visited and the current cell is the end. Track the count of remaining empty cells; decrement on visit, increment on restore. Mutate-restore on the board (mark/unmark) handles the "exactly once" constraint.

### BFS on a grid (contrast)

When the goal is **shortest path** (minimum steps, not "does a path exist with specific characters"), use BFS with a **separate visited set** — do not use mutate-restore. BFS must keep all frontier cells simultaneously reachable; undoing visits would allow cells to be re-entered across BFS levels, destroying the shortest-path guarantee. Snakes-and-ladders, Minimum Knight Moves, and similar problems fall here.

### Pitfalls

- **Forgetting to restore** — the single most common bug. If you return early on success without restoring, the board is permanently corrupted for any subsequent search from a different starting cell.
- **Off-by-one on grid bounds** — the guard `0 <= r < rows and 0 <= c < cols` must be checked before accessing `board[r][c]`. Order matters: Python's short-circuit evaluation means the bounds check must come first.
- **Recursing into the same cell within a single path** — prevented by the sentinel, but only if the sentinel character is genuinely absent from the word/board alphabet. Using `'#'` is safe for lowercase-letter problems; verify for other character sets.
- **Word Search II without trie leaf pruning** — omitting the `del node.children[ch]` step leaves exhausted branches in the trie. On a large board with many short words, the DFS explores those dead branches at every future cell, blowing up the constant factor substantially.
- **Appending the same word multiple times** — in Word Search II, multiple starting cells may reach the same complete word. Setting `child.word = None` after the first hit de-duplicates at zero extra cost.

## 6. Complexity

- **Time:** O(M·N·4^L) for single Word Search, where M·N is the number of starting cells and 4^L bounds the DFS tree from each cell (each step has at most 4 directions, depth L = word length). In practice, character mismatches prune the vast majority of branches and the real runtime is far lower.
- **Space:** O(L) recursion stack for single word search (depth = word length); O(N·L) for the trie in Word Search II (N words of average length L), plus O(max-L) recursion stack.

## 7. Problem set

- [Medium] [Word Search](https://leetcode.com/problems/word-search/) — the canonical mutate-restore grid problem; drill bounds-checking and the restore discipline.
- [Medium] [Robot Room Cleaner](https://leetcode.com/problems/robot-room-cleaner/) — DFS with rotation state; the robot has no map, so you simulate a virtual coordinate system; classic extension of the mutate-restore idea to an implicit grid.
- [Hard] [Word Search II](https://leetcode.com/problems/word-search-ii/) — trie + backtracking; the leaf-pruning optimization is the key insight that makes large inputs tractable.
- [Hard] [Unique Paths III](https://leetcode.com/problems/unique-paths-iii/) — visit-all variant; mutate-restore combined with counting empty cells; contrasts with the standard path-exists form.

## 8. Related patterns

- [Backtracking Template](backtracking-template.md) — the universal try/recurse/undo skeleton that grid backtracking instantiates directly; the grid is just the decision tree made physical.
- [N-Queens & Sudoku](n-queens-sudoku.md) — the same mutate-restore discipline on a 2-D board with explicit constraint sets; the grid-marking trick is analogous to conflict-set management.
- [DFS](../graphs/dfs.md) — grid backtracking is DFS on an implicit graph (cells as nodes, adjacency as edges); the distinction is that backtracking needs to undo state, which standard DFS with a visited set does not.
- [Trie](../strings/trie.md) — Word Search II uses both; the trie prunes the character-matching dimension while backtracking prunes the spatial dimension; neither alone is sufficient for the hard variant.

## 9. Interviewer follow-ups

**Q: What if you need to find many words at once?**
Use a trie (Word Search II). Build one trie from all target words and run a single DFS sweep over the grid, walking the trie alongside the board. This shares the traversal cost across all patterns: instead of running M·N·4^L DFS calls per word, you run a single pass. When a word is found, remove its leaf from the trie to prune future exploration. Without trie sharing, searching K words would cost K × O(M·N·4^L); the trie collapses the shared prefixes so the effective branching factor shrinks dramatically.

**Q: What if revisits across paths must be forbidden, not just within a single path (visit-all variant)?**
That is the Unique Paths III variant. Mutate-restore still works: mark the cell before recursing, unmark after — exactly the same as the standard pattern. Track the count of remaining empty cells; the base case fires only when that count hits zero and the current cell is the end. If the topology is complex (many branching choices, deep tree), you can add memoisation on `(current_cell, visited_bitmask)` — but for grid sizes where every cell must be visited, the bitmask is typically too large and the DFS-with-restore approach is the intended solution.

---

## RECALL card

**TL;DR:** Grid backtracking applies to "find word in grid," "paths with constraints," "visit all cells." Key move: **mutate-restore** — overwrite `board[r][c]='#'` before recursing, restore after. Same skeleton as Backtracking Template; the grid is the implicit decision tree. For many words: trie + DFS (Word Search II), remove trie leaves on match to prune. For shortest path: BFS + separate visited set, not mutate-restore.

**Template:**

```python
from typing import List


def word_search(board: List[List[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        tmp, board[r][c] = board[r][c], "#"
        found = (
            dfs(r + 1, c, idx + 1) or dfs(r - 1, c, idx + 1)
            or dfs(r, c + 1, idx + 1) or dfs(r, c - 1, idx + 1)
        )
        board[r][c] = tmp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


class _TrieNode:
    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: dict = {}
        self.word = None


def word_search_ii(board: List[List[str]], words: List[str]) -> List[str]:
    root = _TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        node.word = w

    rows, cols = len(board), len(board[0])
    found: List[str] = []

    def dfs(r: int, c: int, node: _TrieNode) -> None:
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        ch = board[r][c]
        if ch == "#" or ch not in node.children:
            return
        child = node.children[ch]
        if child.word is not None:
            found.append(child.word)
            child.word = None
        board[r][c] = "#"
        dfs(r + 1, c, child)
        dfs(r - 1, c, child)
        dfs(r, c + 1, child)
        dfs(r, c - 1, child)
        board[r][c] = ch
        if not child.children and child.word is None:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)
    return found
```
