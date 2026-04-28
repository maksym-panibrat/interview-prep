# Interval DP

## 1. TL;DR

Interval DP applies when the problem asks you to optimally combine or partition a contiguous sequence — "merge piles," "burst balloons in best order," "matrix chain multiplication," "minimum cost to triangulate." The signal is that the cost of operating on a range `[i..j]` depends on how you split or order actions within it. Define `dp[i][j]` as the optimal answer for the subarray `[i..j]`; iterate over increasing interval lengths so all shorter subproblems are ready when you need them. Time: O(n³). Space: O(n²).

## 2. Intuition

Imagine you have a row of piles of stones. You can merge any two adjacent piles, paying their combined weight. What order minimizes total cost? Brute-force tries every possible ordering. The insight is that whatever the *last merge* is, it combines two contiguous groups. If you know the cost of optimally merging each group, you can compute the cost of combining them in O(1). This induces a recurrence over intervals.

The critical discipline: iterate by *interval length* (length 2, then 3, …, then n). Length-`k` intervals reference length `< k` intervals, which are already filled if you sweep by length. Iterating by `i` or `j` directly breaks this dependency and yields wrong answers.

A useful reframing for many problems is "last action" rather than "first split." Burst Balloons is the canonical example: instead of asking "which balloon do I burst first in `[i..j]`?" ask "which balloon do I burst *last*?" The last balloon to burst in `[i..j]` is surrounded only by virtual boundaries at that point, making the cost formula clean.

## 3. Walkthrough

### Burst Balloons on `[3, 1, 5, 8]`

Pad with virtual 1s: `nums = [1, 3, 1, 5, 8, 1]` (indices 0–5). We solve on the interior `[1..4]` (real balloons). `dp[i][j]` = maximum coins collectible from balloons strictly between virtual boundaries `nums[i]` and `nums[j]` (i.e., balloons `i+1` through `j-1` with boundaries `i` and `j`).

Recurrence: `dp[i][j] = max over k in (i, j) of dp[i][k] + nums[i]*nums[k]*nums[j] + dp[k][j]` where `k` is the **last** balloon burst in `(i, j)`.

**Length-2 intervals (span = 1 real balloon between boundaries):**

| (i, j) | k | cost                        | dp[i][j] |
|--------|---|-----------------------------|----------|
| (0,2)  | 1 | dp[0][1]+1*3*1+dp[1][2] = 0+3+0 = 3  | 3  |
| (1,3)  | 2 | dp[1][2]+3*1*5+dp[2][3] = 0+15+0 = 15 | 15 |
| (2,4)  | 3 | dp[2][3]+1*5*8+dp[3][4] = 0+40+0 = 40 | 40 |
| (3,5)  | 4 | dp[3][4]+5*8*1+dp[4][5] = 0+40+0 = 40 | 40 |

**Length-3 intervals (2 real balloons):**

| (i, j) | k=i+1 cost | k=i+2 cost | dp[i][j] |
|--------|-----------|-----------|----------|
| (0,3)  | dp[0][1]+1*3*5+dp[1][3]=0+15+15=30 | dp[0][2]+1*1*5+dp[2][3]=3+5+0=8 | 30 |
| (1,4)  | dp[1][2]+3*1*8+dp[2][4]=0+24+40=64 | dp[1][3]+3*5*8+dp[3][4]=15+120+0=135 | 135 |
| (2,5)  | dp[2][3]+1*5*1+dp[3][5]=0+5+40=45 | dp[2][4]+1*8*1+dp[4][5]=40+8+0=48 | 48 |

**Length-4 interval (the full range):**

`dp[1][5]`: try k = 2, 3, 4:
- k=2: dp[1][2] + nums[1]*nums[2]*nums[5] + dp[2][5] = 0 + 3*1*1 + 48 = 51
- k=3: dp[1][3] + nums[1]*nums[3]*nums[5] + dp[3][5] = 15 + 3*5*1 + 40 = 70
- k=4: dp[1][4] + nums[1]*nums[4]*nums[5] + dp[4][5] = 135 + 3*8*1 + 0 = 159

`dp[0][5]`: try k = 1, 2, 3, 4:
- k=1: dp[0][1]+1*3*1+dp[1][5] = 0+3+159 = 162  ← not right for full problem
- Actually solve dp[0][5] directly: boundaries 0 and 5 (both virtual 1s)
  - k=1: 0 + 1*3*1 + dp[1][5] = 3 + 159 = 162
  - k=2: dp[0][2] + 1*1*1 + dp[2][5] = 3 + 1 + 48 = 52
  - k=3: dp[0][3] + 1*5*1 + dp[3][5] = 30 + 5 + 40 = 75
  - k=4: dp[0][4] + 1*8*1 + dp[4][5] = 135+8+0 — wait, need dp[0][4]

Let me note dp[0][4]: try k=1,2,3:
- k=1: 0+1*3*8+dp[1][4]=24+135=159
- k=2: dp[0][2]+1*1*8+dp[2][4]=3+8+40=51
- k=3: dp[0][3]+1*5*8+dp[3][4]=30+40+0=70
  dp[0][4] = 159

Back to dp[0][5]:
- k=4: dp[0][4]+1*8*1+dp[4][5]=159+8+0=167
  dp[0][5] = max(162, 52, 75, 167) = **167**

Final answer: **167**.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def burst_balloons(nums: List[int]) -> int:
    """Burst Balloons (LeetCode 312) — O(n^3) time, O(n^2) space.

    Pad with virtual 1s. dp[i][j] = max coins from balloons strictly
    inside (i, j), where k is the LAST balloon burst in that interval.
    Iterate by interval length to ensure subproblems are ready.
    """
    # Pad with virtual boundary balloons
    balloons = [1] + nums + [1]
    n = len(balloons)
    dp: List[List[int]] = [[0] * n for _ in range(n)]

    # length is the gap between boundary indices i and j (j - i >= 2 for real interval)
    for length in range(2, n):               # length = j - i
        for i in range(0, n - length):
            j = i + length
            for k in range(i + 1, j):        # k is the last balloon burst in (i, j)
                coins = (
                    dp[i][k]
                    + balloons[i] * balloons[k] * balloons[j]
                    + dp[k][j]
                )
                dp[i][j] = max(dp[i][j], coins)

    return dp[0][n - 1]


if __name__ == "__main__":
    assert burst_balloons([3, 1, 5, 8]) == 167
    assert burst_balloons([1, 5]) == 10
    assert burst_balloons([1]) == 1
    assert burst_balloons([]) == 0

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def interval_dp(arr: List[int]) -> int:
    n = len(arr)
    dp = [[0] * n for _ in range(n)]

    for length in range(2, n + 1):          # iterate by interval length
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float("inf")         # or -inf for maximization
            for k in range(i, j):           # split point (or last-action point)
                cost = dp[i][k] + dp[k + 1][j]  # + merge_cost(i, k, j)
                dp[i][j] = min(dp[i][j], cost)

    return dp[0][n - 1]
```

## 5. Variants & pitfalls

### Matrix chain multiplication

Classic textbook interval DP. `dp[i][j]` = minimum scalar multiplications to compute the product of matrices `i` through `j`. Split point `k` means "compute `i..k` first, then `k+1..j`." Same O(n³) recurrence.

### Burst Balloons — last-action framing

Asking "which balloon do I burst *last*?" is cleaner than "first" because when balloon `k` is last, both sides `(i, k)` and `(k, j)` are already empty, so `k` interacts only with the virtual boundary values `balloons[i]` and `balloons[j]`. First-action framing forces you to track which boundaries remain — much harder.

### Minimum cost to cut a stick (LeetCode 1547)

`dp[i][j]` = minimum cost to cut all required cuts within the segment `[i, j]`. Cost of a cut is the current segment length. Iterate over cuts sorted by position; the interval endpoints are cut positions.

### Remove Boxes (LeetCode 546) — three-dimensional extension

Adds a third dimension for the count of equal boxes attached to the left boundary. `dp[i][j][k]` = max points from boxes `[i..j]` with `k` extra boxes of the same color as `boxes[i]` attached on the left. Complexity jumps to O(n⁴).

### Palindromic subsequence DP

`dp[i][j]` = length of longest palindromic subsequence in `s[i..j]`. Transition: if `s[i] == s[j]`, `dp[i][j] = dp[i+1][j-1] + 2`; else `max(dp[i+1][j], dp[i][j-1])`. The interval is over a single string.

### Pitfalls

- **Wrong iteration order**: looping over `i` from 0 to n while `j` from `i+1` to n computes `dp[i][j]` before shorter subintervals it depends on. Always loop over `length` (or equivalently `j - i`) from small to large.
- **Off-by-one in split loop**: for Burst Balloons, `k` ranges over `(i, j)` exclusive (k is inside the open interval). For most standard interval DP (merge, matrix chain), `k` ranges from `i` to `j-1` inclusive as a split between two halves.
- **Last-action vs first-action**: last-action framing is usually cleaner (Burst Balloons) because the remaining boundaries are known at burst time. Prefer last-action unless the problem structure forces first-action.

## 6. Complexity

- **Time:** O(n³) — O(n²) intervals each requiring an O(n) scan over split points.
- **Space:** O(n²) — the dp table; no standard rolling optimization exists since every prior subinterval may be referenced.

## 7. Problem set

- [Medium] [Longest Palindromic Subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/) — interval DP on a single string; clean entry point without cost functions.
- [Medium] [Stone Game](https://leetcode.com/problems/stone-game/) — two-player interval game; `dp[i][j]` is the score advantage of the current player.
- [Medium] [Minimum Cost to Cut a Stick](https://leetcode.com/problems/minimum-cost-to-cut-a-stick/) — cost = segment length at time of cut; requires sorting cut positions first.
- [Hard] [Burst Balloons](https://leetcode.com/problems/burst-balloons/) — the canonical interval DP with last-action reframing; must-know.
- [Hard] [Strange Printer](https://leetcode.com/problems/strange-printer/) — interval DP on a string; `dp[i][j]` = minimum turns to print `s[i..j]`.
- [Hard] [Remove Boxes](https://leetcode.com/problems/remove-boxes/) — three-dimensional extension; harder but instructive for extending the pattern.
- [Hard] [Predict the Winner](https://leetcode.com/problems/predict-the-winner/) — two-player interval game similar to Stone Game; `dp[i][j]` = max score advantage for the current player over `[i..j]`.

## 8. Related patterns

- [1D DP](1d-dp.md) — foundation; 1D DP recurrences are the building blocks for interval DP cells.
- [2D DP](2d-dp.md) — interval DP tables are 2D but with the special constraint that only cells where `i ≤ j` matter and subproblems are nested intervals.
- **[Segment Tree & Fenwick Tree](../trees/segment-tree-fenwick.md)** — for range *queries* on static or mutable arrays (sum, min, max over `[l, r]`); often confused with interval DP but solves a different class of problems.

## 9. Interviewer follow-ups

**Q: Why is the complexity O(n³)? Can it be reduced?**
There are O(n²) distinct intervals and each requires scanning O(n) split points — giving O(n³). For most interval DP problems this is tight. Knuth's optimization applies when the split-point function satisfies a specific monotonicity property (opt(i, j-1) ≤ opt(i, j) ≤ opt(i+1, j)), reducing to O(n²). It applies to matrix chain multiplication and some cost-monotone merge problems, but not to Burst Balloons.

**Q: When does "last-action" framing beat "first-action"?**
Whenever the cost of an action depends on the *current state of the boundaries* rather than the initial configuration. In Burst Balloons, bursting balloon `k` last means its neighbors are exactly `balloons[i]` and `balloons[j]` — a clean formula. Bursting `k` first would require tracking which neighbors remain, adding complexity. If cost depends only on the *indices* (e.g., merging two ranges whose cost is their sum of elements), either framing works and first-action is equally clean.
