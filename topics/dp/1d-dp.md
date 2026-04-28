# 1D DP

## 1. TL;DR

1D DP applies when a problem can be broken into subproblems that each depend on a small number of earlier states along a single axis: positions, values, or steps. The signal is "ways to reach state n," "max/min value ending at index i," "decode/parse with overlapping subproblems," or "fewest steps." Define `dp[i]` as the answer for the first `i` elements (or state at position `i`); each cell is a function of O(1) earlier cells. Time: O(n). Space: O(n), often reducible to O(1).

## 2. Intuition

Imagine walking a hallway with numbered rooms. You want to know the maximum loot you can collect arriving at room `i`. You cannot collect from two adjacent rooms, so the best at room `i` is either the best up to room `i-1` (skip this room) or the best up to room `i-2` plus this room's loot. Once you know those two predecessors you have your answer — you never need to look further back.

That is the essence of 1D DP: prove that your state captures *everything* relevant about the past, so transitions require only a constant-size window of history. When the window is exactly 2, you can discard the array entirely and keep only two scalars, achieving O(1) space.

The key discipline is writing the recurrence before writing code. Ask: "what does `dp[i]` mean in plain English?" and "what cases apply at position `i`?" If the recurrence is clean, the implementation is mechanical.

## 3. Walkthrough

### House Robber on `[2, 7, 9, 3, 1]`

Recurrence: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` — either skip house `i` (take whatever you had through `i-1`) or rob it (add its value to the best through `i-2`).

Base cases: `dp[0] = nums[0] = 2`, `dp[1] = max(nums[0], nums[1]) = 7`.

| i | nums[i] | dp[i-2] | dp[i-1] | dp[i]               |
|---|---------|---------|---------|---------------------|
| 0 | 2       | —       | —       | 2                   |
| 1 | 7       | —       | 2       | max(2, 7) = 7       |
| 2 | 9       | 2       | 7       | max(7, 2+9) = 11    |
| 3 | 3       | 7       | 11      | max(11, 7+3) = 11   |
| 4 | 1       | 11      | 11      | max(11, 11+1) = 12  |

Answer: `dp[4] = 12`. Optimal: rob houses 0, 2, 4 → 2 + 9 + 1 = 12.

### Rolling-window optimization

Because `dp[i]` only needs `dp[i-2]` and `dp[i-1]`, keep two scalars:

```
nums = [2, 7, 9, 3, 1]

start:  prev2 = 0,  prev1 = 0
i=0:    curr = max(0, 0+2) = 2      → prev2=0, prev1=2
i=1:    curr = max(2, 0+7) = 7      → prev2=2, prev1=7
i=2:    curr = max(7, 2+9) = 11     → prev2=7, prev1=11
i=3:    curr = max(11, 7+3) = 11    → prev2=11, prev1=11
i=4:    curr = max(11, 11+1) = 12   → prev2=11, prev1=12

return prev1 = 12
```

O(1) space, same O(n) time.

## 4. Implementation

```python
from __future__ import annotations
import bisect
from typing import List


def house_robber(nums: List[int]) -> int:
    """House Robber — O(n) time, O(1) space via rolling window.

    dp[i] = max(dp[i-1], dp[i-2] + nums[i])
    Rolled: keep two scalars prev2, prev1.
    """
    prev2, prev1 = 0, 0
    for n in nums:
        curr = max(prev1, prev2 + n)
        prev2, prev1 = prev1, curr
    return prev1


def lis(nums: List[int]) -> int:
    """Longest Increasing Subsequence — O(n log n) patience-sorting variant.

    tails[i] is the smallest tail element of any IS of length i+1 seen so far.
    For each num, binary-search for the leftmost tail >= num and replace it,
    or append if num is larger than all tails.
    The length of tails at the end is the LIS length.
    """
    tails: List[int] = []
    for num in nums:
        pos = bisect.bisect_left(tails, num)  # first tail >= num
        if pos == len(tails):
            tails.append(num)                 # extends the longest IS so far
        else:
            tails[pos] = num                  # improves a tail to allow longer future IS
    return len(tails)


if __name__ == "__main__":
    # House Robber
    assert house_robber([2, 7, 9, 3, 1]) == 12
    assert house_robber([1, 2, 3, 1]) == 4
    assert house_robber([]) == 0
    assert house_robber([5]) == 5

    # LIS
    assert lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4  # [2,3,7,18] or [2,5,7,18]
    assert lis([0, 1, 0, 3, 2, 3]) == 4
    assert lis([7, 7, 7, 7]) == 1
    assert lis([1]) == 1

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List
import bisect


def house_robber(nums: List[int]) -> int:
    prev2, prev1 = 0, 0
    for n in nums:
        curr = max(prev1, prev2 + n)
        prev2, prev1 = prev1, curr
    return prev1


def lis(nums: List[int]) -> int:
    tails: List[int] = []
    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    return len(tails)
```

## 5. Variants & pitfalls

### Constant-state recurrence (Climbing Stairs, House Robber)

When the window of prior states is fixed and small (2 for House Robber, also 2 for Climbing Stairs), roll to O(1) space. The guard: if you ever need `dp[i-3]` or further, you must either widen the rolling window or keep the full array.

### String DP (Decode Ways)

Index over characters; `dp[i]` = number of ways to decode `s[:i]`. Transitions inspect 1–2 characters back to check valid single-digit and two-digit decodings. Take care with leading zeros: `"06"` is not a valid two-digit code.

### Subsequence DP (LIS)

Naive O(n²): `dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i])`. The O(n log n) patience variant (shown above) replaces the inner scan with a binary search; it finds the *length* but not the actual subsequence without extra bookkeeping.

### Coin Change (value-space DP)

`dp[amount]` is indexed by *amount* (value space), not position. `dp[0] = 0`; for each coin `c`, update `dp[a] = min(dp[a], dp[a-c] + 1)`. The table has `amount+1` cells regardless of the number of coins.

### Pitfalls

- **`dp[i-2]` underflow**: when computing `dp[2]` in a 0-indexed array, `dp[-2]` in Python wraps around to the last element — always define `dp[0]` and `dp[1]` as explicit base cases before the loop, or start the loop at index 2.
- **Premature rolling**: if the recurrence of a variant looks back more than two steps (e.g., some word-break formulations), rolling to two scalars silently gives wrong answers. Check the look-back distance before optimizing.
- **Boolean vs count**: Word Break asks whether the string is breakable (`dp[i]` is a bool). Decode Ways asks how many ways (`dp[i]` is an int). Using the wrong type causes subtle bugs where `True + True == 2` is accidentally correct in Python but obscures the logic.

## 6. Complexity

- **Time:** O(n) — one pass through the array; each cell computed in O(1) (or O(log n) for the LIS patience variant giving O(n log n) total).
- **Space:** O(n) for the full dp array; O(1) after rolling when look-back is constant.

## 7. Problem set

- [Easy] [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) — the smallest possible 1D DP; forces you to write the Fibonacci recurrence from scratch.
- [Easy] [House Robber](https://leetcode.com/problems/house-robber/) — canonical two-state rolling window; master this recurrence cold.
- [Easy] [Min Cost Climbing Stairs](https://leetcode.com/problems/min-cost-climbing-stairs/) — small twist: starting position is a choice, reinforcing base-case discipline.
- [Easy] [Fibonacci Number](https://leetcode.com/problems/fibonacci-number/) — sanity check for rolling O(1) space.
- [Medium] [House Robber II](https://leetcode.com/problems/house-robber-ii/) — circular array; run linear House Robber twice (skip first or skip last element) and take the max.
- [Medium] [Decode Ways](https://leetcode.com/problems/decode-ways/) — string DP; look back 1–2 chars with validity checks for zeros.
- [Medium] [Coin Change](https://leetcode.com/problems/coin-change/) — value-space DP; table indexed by amount, not position.
- [Medium] [Word Break](https://leetcode.com/problems/word-break/) — boolean DP; `dp[i]` = "is prefix of length i breakable."
- [Medium] [Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/) — practice both O(n²) and O(n log n) variants.
- [Medium] [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) — Kadane's algorithm is a 1D DP reduced to O(1) space; `dp[i] = max(nums[i], dp[i-1] + nums[i])`.
- [Medium] [Best Time to Buy and Sell Stock with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/) — state machine DP; three states (held, sold, rest) each tracked as a rolling scalar.
- [Hard] [Longest Valid Parentheses](https://leetcode.com/problems/longest-valid-parentheses/) — `dp[i]` = length of longest valid suffix ending at `i`; transitions require careful case analysis on `(` vs `)`.
- [Hard] [Coin Change II](https://leetcode.com/problems/coin-change-ii/) — counting combinations; run coins in outer loop to avoid counting permutations as separate.

## 8. Related patterns

- **[2D DP](2d-dp.md)** — extends the state to two dimensions when two inputs (two strings, a grid) interact; builds directly on 1D DP intuition.
- **[Tree DP](tree-dp.md)** — applies the same "summarize subtree in a small state tuple" idea on tree structure instead of a linear array.
- **[Interval Scheduling](../greedy/interval-scheduling.md)** — some scheduling problems that look like DP admit greedy solutions; knowing the boundary sharpens both skills.

## 9. Interviewer follow-ups

**Q: Can you reduce space to O(1)?**
Yes, whenever the recurrence looks back at most a constant number of steps. Replace the `dp` array with that many scalars and advance them each iteration. House Robber, Climbing Stairs, and Fibonacci all reduce to O(1). Coin Change and Word Break cannot (they look back up to `amount` or `len(word)` steps).

**Q: What if the DP table is sparse — most states are unreachable?**
Use a dictionary (hash map) instead of an array for memoization. Initialize only the base cases, and skip any state that is never reachable. This is standard in top-down memoized recursion and reduces memory to O(reachable states).

**Q: How do you reconstruct the actual choice sequence, not just the optimal value?**
Maintain a parallel `parent` array: `parent[i] = j` means "to achieve `dp[i]`, we came from state `j`." After filling the table, back-trace from the final state by following `parent` pointers to the start. For House Robber, record whether each cell was reached by "rob" or "skip." For LIS, record the predecessor index in the subsequence.
