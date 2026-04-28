# 2D DP

## 1. TL;DR

2D DP applies when the problem involves two strings, two arrays, or a grid, and the answer for a pair of prefixes (or a grid cell) can be built from three neighboring subproblems. The signal is "edit distance," "LCS," "knapsack," "unique paths," or "interleaving." Define `dp[i][j]` as the answer for the first `i` elements of one input and first `j` of the other (or position `(i,j)` in a grid); transitions look at `(i-1,j)`, `(i,j-1)`, and `(i-1,j-1)`. Time: O(n·m). Space: O(n·m), often reducible to O(min(n,m)).

## 2. Intuition

Imagine aligning two strings letter by letter. At each position you face three choices: delete a character from the first string, insert a character into the first string, or match/replace the current characters. The cost of the cheapest alignment through position `(i, j)` can be computed from three smaller alignments: `(i-1, j)`, `(i, j-1)`, `(i-1, j-1)`. Once those three cells are filled, cell `(i, j)` takes O(1) to compute.

This is the standard 2D DP structure. A table with one axis per input accumulates answers bottom-up. The base row (`i=0`) and base column (`j=0`) represent empty-prefix cases, which are always trivial to initialize.

The same geometry applies to grids: `dp[i][j]` = best path to cell `(i,j)`, computed from the cell above and the cell to the left. And to knapsack: `dp[i][w]` = best value using the first `i` items with capacity `w`, computed from the same row at lower capacity or the previous row.

## 3. Walkthrough

### Edit Distance: `"horse"` → `"ros"`

Operations: insert, delete, replace — each costs 1. `dp[i][j]` = minimum edits to convert `horse[:i]` into `ros[:j]`.

Base cases: `dp[i][0] = i` (delete all `i` chars), `dp[0][j] = j` (insert `j` chars).

```
     ""  r   o   s
""  [ 0,  1,  2,  3 ]
h   [ 1,  1,  2,  3 ]
o   [ 2,  2,  1,  2 ]
r   [ 3,  2,  2,  2 ]
s   [ 4,  3,  3,  2 ]
e   [ 5,  4,  4,  3 ]
```

Tracing cell `dp[2][2]` (`"ho"` vs `"ro"`):
- `dp[1][2] + 1 = 3` (delete `o` from `"ho"`)
- `dp[2][1] + 1 = 3` (insert `o` into `"ho"` → `"hoo"`)
- `dp[1][1] + (0 if 'o'=='o' else 1) = 1 + 0 = 1` (match `o`=`o`, keep best from `"h"`→`"r"`)
- `dp[2][2] = min(3, 3, 1) = 1`

Final answer: `dp[5][3] = 3`. One solution: replace `h`→`r`, delete `r`, delete `e`.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def edit_distance(a: str, b: str) -> int:
    """Edit Distance (LeetCode 72) — O(n*m) time, O(min(n,m)) space (rolling row).

    dp[i][j] = min edits to convert a[:i] to b[:j].
    Rolled to two 1-D arrays: prev row and current row.
    Keep the shorter string on the column axis to minimize memory.
    """
    if len(a) < len(b):
        a, b = b, a                 # ensure len(b) <= len(a) so b is the column axis
    n, m = len(a), len(b)

    # prev[j] represents dp[i-1][j]
    prev = list(range(m + 1))       # base case: dp[0][j] = j
    for i in range(1, n + 1):
        curr = [i] + [0] * m       # curr[0] = i  (base case: dp[i][0] = i)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1]                       # characters match — free
            else:
                curr[j] = 1 + min(
                    prev[j],        # delete from a
                    curr[j - 1],    # insert into a (from current row)
                    prev[j - 1],    # replace
                )
        prev = curr
    return prev[m]


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    """0/1 Knapsack — O(n * capacity) time, O(capacity) space (1-D rolling).

    dp[w] = max value achievable with weight budget w.
    Iterate weights in *descending* order so each item is used at most once.
    """
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        # Traverse right-to-left: ensures item i is not reused in this pass.
        for cap in range(capacity, w - 1, -1):
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[capacity]


if __name__ == "__main__":
    # Edit Distance
    assert edit_distance("horse", "ros") == 3
    assert edit_distance("intention", "execution") == 5
    assert edit_distance("", "abc") == 3
    assert edit_distance("abc", "") == 3
    assert edit_distance("abc", "abc") == 0

    # 0/1 Knapsack
    assert knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7) == 9
    assert knapsack_01([2, 3, 4], [3, 4, 5], 5) == 7
    assert knapsack_01([], [], 10) == 0
    assert knapsack_01([5], [10], 4) == 0
    assert knapsack_01([5], [10], 5) == 10

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[m]


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for cap in range(capacity, w - 1, -1):  # descending → 0/1 (each item once)
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[capacity]
```

## 5. Variants & pitfalls

### Grid DP (Unique Paths, Minimum Path Sum)

The table mirrors the grid: `dp[i][j]` depends only on `dp[i-1][j]` (above) and `dp[i][j-1]` (left). Space rolls to O(cols) trivially.

### String DP (Edit Distance, LCS)

Table indexed by prefix lengths, not character indices. `dp[0][*]` and `dp[*][0]` represent empty-string base cases. For LCS, `dp[i][j] = dp[i-1][j-1] + 1` when characters match, else `max(dp[i-1][j], dp[i][j-1])`.

### 0/1 Knapsack

Two nested loops: outer over items, inner over capacity in *descending* order. Descending ensures each item is considered at most once per row (since `dp[cap - w]` in the current pass still holds the *previous* item's value for that capacity).

### Unbounded Knapsack (Coin Change variants)

Identical structure but inner loop runs in *ascending* order. Ascending allows reusing the current item because `dp[cap - coin]` in the current pass already reflects the current item being included.

### Subset Sum / Partition Equal Subset Sum (416)

Boolean knapsack: `dp[w]` = True if some subset sums to `w`. Same descending pass as 0/1 knapsack but with `or` instead of `max`.

### Pitfalls

- **Loop direction for rolling knapsack**: forward (ascending) = unbounded; backward (descending) = 0/1. Mixing them up silently gives wrong answers.
- **Off-by-one — "first i" vs "ending at i"**: when `dp[i][j]` means "using first `i` items," rows are 1-indexed over items and `dp[0][*]` is always the empty-set base case. Shifting the index by 1 avoids needing `dp[-1]`.
- **Forgetting base row/column**: skipping `dp[i][0] = i` or `dp[0][j] = j` in Edit Distance causes wrong answers for short strings.
- **Maximal Square (221)**: `dp[i][j]` = side length of largest square with bottom-right corner at `(i,j)`. Transition is `min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1`. The `min` (not `max`) trips people up.

## 6. Complexity

- **Time:** O(n·m) — fill every cell of the table with O(1) work; n and m are the two input sizes.
- **Space:** O(n·m) for the full table; rolls to O(min(n, m)) by keeping only the previous row (or column).

## 7. Problem set

- [Medium] [Unique Paths](https://leetcode.com/problems/unique-paths/) — simplest grid DP; good entry point, answer also has a combinatorial closed form.
- [Medium] [Minimum Path Sum](https://leetcode.com/problems/minimum-path-sum/) — grid DP with costs; reinforces top-left to bottom-right sweep.
- [Medium] [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) — canonical string DP; master `dp[i][j] = dp[i-1][j-1]+1` vs `max(dp[i-1][j], dp[i][j-1])`.
- [Medium] [Edit Distance](https://leetcode.com/problems/edit-distance/) — three-way transition; the benchmark for two-string DP.
- [Medium] [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) — boolean 0/1 knapsack; reduces to "can some subset sum to total/2."
- [Medium] [Target Sum](https://leetcode.com/problems/target-sum/) — counting subset-sum variant; maps to knapsack with target offset.
- [Medium] [Last Stone Weight II](https://leetcode.com/problems/last-stone-weight-ii/) — partition into two groups minimizing difference; subset-sum knapsack.
- [Medium] [Coin Change II](https://leetcode.com/problems/coin-change-ii/) — unbounded knapsack counting combinations; ascending inner loop.
- [Medium] [Maximal Square](https://leetcode.com/problems/maximal-square/) — grid DP with a `min`-based transition; classic pitfall.
- [Medium] [Unique Paths II](https://leetcode.com/problems/unique-paths-ii/) — grid DP with obstacles; forces explicit zero-initialization.
- [Hard] [Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/) — counting how many times t appears as a subsequence of s.
- [Hard] [Interleaving String](https://leetcode.com/problems/interleaving-string/) — boolean 2D DP; `dp[i][j]` = can `s1[:i]` and `s2[:j]` interleave to form `s3[:i+j]`.
- [Hard] [Regular Expression Matching](https://leetcode.com/problems/regular-expression-matching/) — `.` and `*` wildcards; `*` case must peek at `dp[i][j-2]`.
- [Hard] [Wildcard Matching](https://leetcode.com/problems/wildcard-matching/) — similar to regex but `*` matches any sequence; slightly simpler transition.

## 8. Related patterns

- [1D DP](1d-dp.md) — 1D DP is the foundation; 2D DP adds a second dimension when two inputs interact.
- **Interval DP** (`interval-dp.md`) — a specialized 2D table where both axes index positions within the *same* sequence and subproblems are intervals; builds on 2D DP ideas.
- **Bitmask DP** (`bitmask-dp.md`) — encodes subset state as a bitmask integer; can be viewed as a DP over exponentially many "rows."

## 9. Interviewer follow-ups

**Q: Can you reduce space to O(min(n, m))?**
Yes. Process the shorter string along the column axis and keep only the previous row. At each outer-loop step, overwrite `prev` with `curr`. The rolling works because each cell only looks left (same row, already computed) and up/diagonally (previous row, still in `prev`).

**Q: How do you reconstruct the alignment, not just the distance?**
Maintain a `parent` table alongside `dp`. At each cell record which of the three transitions was taken (delete, insert, replace/match). After filling the table, trace back from `(n, m)` to `(0, 0)` following parent pointers to produce the edit script or alignment string.

**Q: Can you handle custom operation costs (e.g., replace costs 2, insert costs 3)?**
Yes — replace each `1 +` in the recurrence with the actual cost of that operation. The rest of the algorithm is unchanged. Weighted edit distance is standard in spelling-correction and bioinformatics alignment.
