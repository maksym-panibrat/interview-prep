# N-Queens & Sudoku

## 1. TL;DR

N-Queens and Sudoku Solver are constraint-satisfaction problems solved with the same backtracking template as subsets and permutations: build the solution row-by-row (or empty-cell-by-empty-cell), enumerate only candidates that don't conflict with the current partial state, place, recurse, and undo. The signal is "place queens such that no two attack each other," "fill the Sudoku board," or any combinatorial search with explicit row/column/diagonal/region conflict constraints. Time: O(N!) for N-Queens (heavily pruned in practice); Sudoku is NP-hard in theory but runs instantly for 9×9. Space: O(N) recursion depth plus conflict sets.

## 2. Intuition

Both problems are the same pattern: at each decision point, pick the next "slot" to fill (the next row for N-Queens; the next empty cell for Sudoku), enumerate candidates that don't conflict with what's already placed, commit, recurse, and undo. Pruning happens before the recursive call — you never enter a branch you already know is invalid.

For N-Queens, three sets track which columns and diagonals are occupied. A queen at `(r, c)` occupies column `c`, anti-diagonal `r + c` (all cells on that diagonal share the same sum), and main diagonal `r - c` (all cells on that diagonal share the same difference). A candidate column `c` at row `r` is valid iff none of these three values appears in the corresponding conflict set.

For Sudoku, three sets of sets track which digits appear in each row, each column, and each 3×3 box. A digit `d` is valid at `(r, c)` iff it does not appear in `rows[r]`, `cols[c]`, or `boxes[r//3 * 3 + c//3]`. Because the board is small (81 cells, 9 possible digits) the search completes in microseconds even without advanced heuristics.

The key realization: conflict-checking in O(1) via sets (or bitmasks) is what makes pruning cheap. Without it, every candidate would require an O(N) scan.

## 3. Walkthrough

### N-Queens for n = 4

Goal: place 4 queens on a 4×4 board so no two share a row, column, or diagonal. Process one row at a time.

```
State: cols={}, pos_diag={}, neg_diag={}

Row 0, try col 0: pos=0, neg=0 — no conflict. Place. cols={0}, pos={0}, neg={0}
  Row 1, try col 0: col 0 in cols — skip.
  Row 1, try col 1: pos=2 not in pos, neg=0 in neg — skip.
  Row 1, try col 2: pos=3 not in pos, neg=1 not in neg — Place.
    cols={0,2}, pos={0,3}, neg={0,1}
    Row 2, try col 0: col 0 in cols — skip.
    Row 2, try col 1: pos=3 in pos — skip.
    Row 2, try col 2: col 2 in cols — skip.
    Row 2, try col 3: pos=5, neg=1 in neg — skip.
    Row 2: no valid column. Backtrack.
  Row 1, try col 3: pos=4 not in pos, neg=2 not in neg — Place.
    cols={0,3}, pos={0,4}, neg={0,2}
    Row 2, try col 0: col 0 in cols — skip.
    Row 2, try col 1: pos=3, neg=1 — no conflict. Place.
      cols={0,1,3}, pos={0,3,4}, neg={0,1,2}
      Row 3, try col 0: col 0 in cols — skip.
      Row 3, try col 1: col 1 in cols — skip.
      Row 3, try col 2: pos=5, neg=1 in neg — skip.
      Row 3, try col 3: col 3 in cols — skip.
      Backtrack.
    Row 2, try col 2: pos=4 in pos — skip.
    Row 2, try col 3: col 3 in cols — skip.
    Backtrack.

Row 0, try col 1: ...continue search...
  Eventually finds solution: row 0->col 1, row 1->col 3, row 2->col 0, row 3->col 2
  Board: .Q.. / ...Q / Q... / ..Q.
```

The two solutions for n=4 are `[.Q.., ...Q, Q..., ..Q.]` and `[..Q., Q..., ...Q, .Q..]`.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def solve_n_queens(n: int) -> List[List[str]]:
    """Return all N-Queens solutions as boards.

    Each solution is a list of n strings; '.' is empty, 'Q' is a queen.
    Uses three sets for O(1) conflict checking at each candidate column.
    """
    results: List[List[str]] = []
    placement: List[int] = []     # placement[r] = column of queen in row r
    cols: set[int] = set()        # occupied columns
    pos_diag: set[int] = set()    # occupied anti-diagonals (r + c = const)
    neg_diag: set[int] = set()    # occupied main diagonals (r - c = const)

    def backtrack(row: int) -> None:
        if row == n:
            # Build board strings from the placement list
            results.append(["." * c + "Q" + "." * (n - c - 1) for c in placement])
            return

        for col in range(n):
            if col in cols or (row + col) in pos_diag or (row - col) in neg_diag:
                continue  # conflict — prune this candidate
            # Place queen at (row, col)
            cols.add(col)
            pos_diag.add(row + col)
            neg_diag.add(row - col)
            placement.append(col)

            backtrack(row + 1)

            # Undo placement
            cols.remove(col)
            pos_diag.remove(row + col)
            neg_diag.remove(row - col)
            placement.pop()

    backtrack(0)
    return results


def solve_sudoku(board: List[List[str]]) -> None:
    """Solve a Sudoku puzzle in-place.

    Empty cells are represented by '.'. Fills the board with a valid solution.
    Uses three arrays of sets (rows, cols, boxes) for O(1) conflict checking.
    """
    rows: List[set[str]] = [set() for _ in range(9)]
    cols: List[set[str]] = [set() for _ in range(9)]
    boxes: List[set[str]] = [set() for _ in range(9)]

    empty: List[tuple[int, int]] = []

    # Initialize conflict sets from the pre-filled clues
    for r in range(9):
        for c in range(9):
            d = board[r][c]
            if d != ".":
                box_id = (r // 3) * 3 + (c // 3)
                rows[r].add(d)
                cols[c].add(d)
                boxes[box_id].add(d)
            else:
                empty.append((r, c))

    def backtrack(idx: int) -> bool:
        if idx == len(empty):
            return True  # all empty cells filled — solution found
        r, c = empty[idx]
        box_id = (r // 3) * 3 + (c // 3)
        for d in "123456789":
            if d in rows[r] or d in cols[c] or d in boxes[box_id]:
                continue  # conflict — skip this digit
            # Place digit
            board[r][c] = d
            rows[r].add(d)
            cols[c].add(d)
            boxes[box_id].add(d)

            if backtrack(idx + 1):
                return True  # propagate success up

            # Undo placement
            board[r][c] = "."
            rows[r].remove(d)
            cols[c].remove(d)
            boxes[box_id].remove(d)

        return False  # no digit worked — trigger backtrack

    backtrack(0)


if __name__ == "__main__":
    # N-Queens n=4: expect exactly 2 solutions
    solutions = solve_n_queens(4)
    assert len(solutions) == 2, f"expected 2 solutions, got {len(solutions)}"
    # Both known solutions for n=4
    expected = {
        tuple([".Q..", "...Q", "Q...", "..Q."]),
        tuple(["..Q.", "Q...", "...Q", ".Q.."]),
    }
    assert {tuple(s) for s in solutions} == expected, f"wrong solutions: {solutions}"

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def solve_n_queens(n: int) -> List[List[str]]:
    results: List[List[str]] = []
    placement: List[int] = []
    cols: set[int] = set()
    pos_diag: set[int] = set()
    neg_diag: set[int] = set()

    def backtrack(row: int) -> None:
        if row == n:
            results.append(["." * c + "Q" + "." * (n - c - 1) for c in placement])
            return
        for col in range(n):
            if col in cols or (row + col) in pos_diag or (row - col) in neg_diag:
                continue
            cols.add(col); pos_diag.add(row + col); neg_diag.add(row - col)
            placement.append(col)
            backtrack(row + 1)
            cols.remove(col); pos_diag.remove(row + col); neg_diag.remove(row - col)
            placement.pop()

    backtrack(0)
    return results


def solve_sudoku(board: List[List[str]]) -> None:
    rows: List[set[str]] = [set() for _ in range(9)]
    cols: List[set[str]] = [set() for _ in range(9)]
    boxes: List[set[str]] = [set() for _ in range(9)]
    empty: List[tuple[int, int]] = []

    for r in range(9):
        for c in range(9):
            d = board[r][c]
            if d != ".":
                box_id = (r // 3) * 3 + (c // 3)
                rows[r].add(d); cols[c].add(d); boxes[box_id].add(d)
            else:
                empty.append((r, c))

    def backtrack(idx: int) -> bool:
        if idx == len(empty):
            return True
        r, c = empty[idx]
        box_id = (r // 3) * 3 + (c // 3)
        for d in "123456789":
            if d in rows[r] or d in cols[c] or d in boxes[box_id]:
                continue
            board[r][c] = d
            rows[r].add(d); cols[c].add(d); boxes[box_id].add(d)
            if backtrack(idx + 1):
                return True
            board[r][c] = "."
            rows[r].remove(d); cols[c].remove(d); boxes[box_id].remove(d)
        return False

    backtrack(0)
```

## 5. Variants & pitfalls

### N-Queens: count solutions vs print solutions

The recursion is identical; the only difference is the aggregator. To count, replace `results.append(...)` with `count[0] += 1` (or use a `nonlocal` counter). LeetCode 52 asks for count only, so the board-building step can be skipped entirely — this cuts constant-factor overhead when n is larger.

### Sudoku Solver vs Sudoku Validator

The validator (LeetCode 36) does not search at all: iterate the board once, check that no row, column, or 3×3 box contains a repeated digit. The solver (LeetCode 37) applies backtracking. A common interview mistake is conflating the two; make sure you understand which one you are being asked to write before coding.

### General CSP framing

Both problems are instances of **Constraint Satisfaction Problems (CSPs)**: variables (rows / empty cells), domains (columns 0..N-1 / digits 1-9), and constraints (no two queens attack each other / Sudoku rules). Backtracking is the baseline solver. **Constraint propagation** (e.g., AC-3 — Arc Consistency 3) can shrink domains before each placement, reducing the branching factor significantly. For Sudoku, even a simple "naked singles" propagation (if a cell has only one candidate, fill it immediately) eliminates most of the search.

### MRV (Most Restricted Variable) heuristic

Instead of picking empty cells left-to-right top-to-bottom, pick the empty cell with the **fewest remaining candidates** first. A cell with only two legal digits forces a commit sooner, and if one branch leads to a contradiction, you find out earlier — the search tree shrinks dramatically on hard Sudoku puzzles. MRV is a name-drop interviewers love: mention it when asked how you would optimize the solver.

### Bitmask conflict tracking

Replace each `set` with an integer bitmask. For N-Queens, three integers `cols_mask`, `pos_mask`, `neg_mask` encode occupied columns and diagonals as bits. Candidate columns at the next row are `available = ((1 << n) - 1) & ~(cols_mask | pos_mask | neg_mask)`. Extract the lowest set bit with `bit = available & (-available)`, place there, shift the diagonal masks, recurse. This reduces each conflict check to a handful of bitwise operations and is the fastest known approach for large N.

### Pitfalls

- **Diagonal index sign confusion**: `r + c` identifies one diagonal family (anti-diagonals, top-right to bottom-left); `r - c` identifies the other (main diagonals, top-left to bottom-right). Swapping them or using the wrong sign produces silent incorrect results — the code runs but finds wrong solutions.
- **Missing one of the three constraint sets**: For N-Queens, omitting any one of `cols`, `pos_diag`, `neg_diag` silently allows invalid placements. For Sudoku, forgetting the box check is the most common omission.
- **Deep-copying the board**: Using `copy.deepcopy(board)` instead of in-place mutate-and-restore produces correct output but O(N^2) space per recursion level. Mutate and undo is always the right pattern here.
- **Arbitrary cell iteration order without MRV**: On hard Sudoku instances, fixed left-to-right cell order without any prioritization can make the solver noticeably slow. MRV is a one-line change (sort `empty` by remaining candidates at each step) with dramatic practical impact.

## 6. Complexity

- **Time:** O(N!) for N-Queens — each row eliminates at least one column from consideration; heavily pruned in practice. Sudoku is NP-hard in general (for an n^2 x n^2 board) but for the fixed 9x9 case the constant is tiny and the solver finishes in microseconds.
- **Space:** O(N) recursion depth and O(N) for the three conflict sets in N-Queens; O(81) = O(1) for the Sudoku empty-cell list and conflict sets (fixed board size).

## 7. Problem set

- [Medium] [Valid Sudoku](https://leetcode.com/problems/valid-sudoku/) — validate an existing board; no search required, just the constraint-checking logic.
- [Hard] [N-Queens](https://leetcode.com/problems/n-queens/) — return all solutions as boards; the primary N-Queens problem.
- [Hard] [N-Queens II](https://leetcode.com/problems/n-queens-ii/) — return only the count; drop board-building, same recursion.
- [Hard] [Sudoku Solver](https://leetcode.com/problems/sudoku-solver/) — fill the board in-place; the primary Sudoku problem.

## 8. Related patterns

- [Backtracking Template](backtracking-template.md) — the try/recurse/undo skeleton that both N-Queens and Sudoku instantiate directly.
- [Bitmask DP](../dp/bitmask-dp.md) — bitmask conflict tracking is the same trick: a single integer encodes a set of occupied positions; bitwise AND/OR/NOT replace set operations.
- [Grid Backtracking](grid-search.md) — the same mutate-restore discipline applied to pathfinding on a 2-D board; N-Queens constrains placements by row/col/diagonal while grid search constrains by visited cells.

## 9. Interviewer follow-ups

**Q: Can you bitmask the conflict sets?**
Yes. Represent `cols`, `pos_diag`, `neg_diag` as three integers. Available columns at row `r` are `available = ((1 << n) - 1) & ~(cols_mask | pos_mask | neg_mask)`. Extract each candidate with `bit = available & (-available); available &= available - 1`. Shift the diagonal masks on each recursive call. This replaces three set operations with a handful of bitwise operations per candidate, and is the standard approach when N is large.

**Q: Print all solutions vs count?**
Same recursion, different aggregator. To print (or collect) all solutions, append a copy of the board at the base case. To count only, replace that with `count[0] += 1` — the board-building step disappears entirely. For N-Queens II, counting is all that is asked; you save O(N) work per leaf.

**Q: MRV heuristic for Sudoku?**
At each step, instead of picking the first empty cell in list order, pick the one with the fewest remaining legal digits. Cells with only one or two candidates force a decision sooner, and contradictions surface earlier — the branching factor drops substantially on hard puzzles. Implementation: before each `backtrack(idx)` call, scan the remaining empty cells, compute candidate counts, and pick the minimum.
