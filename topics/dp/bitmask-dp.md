# Bitmask DP

## 1. TL;DR

Bitmask DP applies when N is small (≤ ~20) and you need to track which subset of N elements has been processed. The signal is "visit all cities/jobs/nodes," TSP-like constraints, or "cover all requirements with a subset." Encode the processed subset as an integer bitmask; `dp[mask]` (or `dp[mask][i]`) gives the optimal answer when exactly the elements in `mask` have been used. Time: O(2^N · N). Space: O(2^N · N).

## 2. Intuition

Imagine you have 4 cities to visit and you must return home. At any point in the tour you can describe your state as "which cities have I visited, and where am I now." There are only 2^4 = 16 possible visited-sets and 4 possible current cities — 64 total states. That is tiny. Bitmask DP exploits exactly this: for small N, the full state space is manageable.

An integer with N bits is a perfect subset descriptor. Bit `k` is 1 if element `k` has been included, 0 otherwise. Common bit operations:

- Check if element `k` is in `mask`: `mask & (1 << k)`
- Add element `k` to `mask`: `mask | (1 << k)`
- Remove element `k` from `mask`: `mask & ~(1 << k)` or `mask ^ (1 << k)` if `k` is known to be set
- Previous mask without element `k`: `mask ^ (1 << k)` (when `k` is in `mask`)
- Iterate all submasks of `mask`: `sub = mask; while sub: ... sub = (sub - 1) & mask`

The constraint N ≤ 20 comes from 2^20 ≈ 10^6 — manageable in memory and time. At N = 25, 2^25 ≈ 33×10^6, and the full O(2^N · N) table hits ~800M operations — typically too slow for a 1-second time limit.

## 3. Walkthrough

### Held-Karp TSP on 4 cities

Distance matrix (symmetric):
```
     0   1   2   3
0  [ 0, 10, 15, 20]
1  [10,  0, 35, 25]
2  [15, 35,  0, 30]
3  [20, 25, 30,  0]
```

`dp[mask][i]` = minimum cost to start at city 0, visit exactly the cities in `mask`, and end at city `i`. City 0 is always included in `mask`.

**Base case:** `dp[0b0001][0] = 0` (started at 0, visited only 0, zero cost). All other base states are infinity.

**Filling by popcount (number of bits set):**

popcount = 2 (visit city 0 + one other):
- `dp[0b0011][1]` = dp[0b0001][0] + dist[0][1] = 0 + 10 = **10** (0→1)
- `dp[0b0101][2]` = dp[0b0001][0] + dist[0][2] = 0 + 15 = **15** (0→2)
- `dp[0b1001][3]` = dp[0b0001][0] + dist[0][3] = 0 + 20 = **20** (0→3)

popcount = 3, mask = `0b0111` (cities 0,1,2), city `i = 2`:
- Previous mask `0b0101` (cities 0,2) ending at city 0: dp[0b0101][0] + dist[0][2] — but dp[0b0101][0] = ∞ (we can't be at 0 after visiting {0,2} without looping).

  Actually: prev mask = `0b0111 ^ (1<<2)` = `0b0011`, ending at city `j≠2`:
  - j=0: dp[0b0011][0] + dist[0][2] = ∞ (can't be at 0 after visiting {0,1} without looping back, only valid start is 0)
  - j=1: dp[0b0011][1] + dist[1][2] = 10 + 35 = 45

  prev mask = `0b0111 ^ (1<<1)` = `0b0101`, ending at city `j≠2`:
  - j=0: dp[0b0101][0] + dist[0][2] = ∞
  - j=2 not valid (we're computing ending at 2)
  Actually for i=2, j iterates over cities in `prev_mask = mask ^ (1<<2)`:
  - prev_mask = 0b0011 = {0,1}, j can be 0 or 1:
    - j=0: dp[0b0011][0] + dist[0][2] — dp[0b0011][0] = ∞ (city 0 is only the start)
    - j=1: dp[0b0011][1] + dist[1][2] = 10 + 35 = 45
  - prev_mask = 0b0101 = {0,2}: but we're computing `dp[0b0111][2]` so prev_mask for ending at 2 is mask without bit 2 = 0b0011, done above.

  `dp[0b0111][2]` = **45**

mask = `0b0111`, city `i = 1`:
  - prev_mask = 0b0101 = {0,2}, j=2: dp[0b0101][2] + dist[2][1] = 15 + 35 = **50**

popcount = 4, full mask = `0b1111`:
After filling all 3-city states, compute the tour cost = min over last city `i ≠ 0` of `dp[0b1111][i] + dist[i][0]`.

The minimum tour is 0→1→3→2→0: 10+25+30+15 = **80**.

## 4. Implementation

```python
from __future__ import annotations
from typing import List
import math


def tsp(dist: List[List[int]]) -> int:
    """Held-Karp TSP — O(2^n * n^2) time, O(2^n * n) space.

    Returns the minimum-cost Hamiltonian cycle starting and ending at city 0.
    dist[i][j] is the cost to travel from city i to city j.
    """
    n = len(dist)
    if n == 0:
        return 0
    if n == 1:
        return 0

    INF = math.inf
    # dp[mask][i] = min cost to start at 0, visit all cities in mask, end at i
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # started at city 0, mask = 0b...0001

    for mask in range(1, 1 << n):
        if not (mask & 1):          # city 0 must always be in the mask
            continue
        for last in range(n):
            if not (mask & (1 << last)):   # last must be in mask
                continue
            if dp[mask][last] == INF:
                continue
            # Extend the path to a new city `nxt`
            for nxt in range(n):
                if mask & (1 << nxt):      # already visited
                    continue
                new_mask = mask | (1 << nxt)
                new_cost = dp[mask][last] + dist[last][nxt]
                if new_cost < dp[new_mask][nxt]:
                    dp[new_mask][nxt] = new_cost

    # Close the tour: return from last city back to city 0
    full_mask = (1 << n) - 1
    return int(min(
        dp[full_mask][i] + dist[i][0]
        for i in range(1, n)
        if dp[full_mask][i] < INF
    ))


if __name__ == "__main__":
    dist4 = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    assert tsp(dist4) == 80  # 0→1→3→2→0: 10+25+30+15 = 80

    # Single city
    assert tsp([[0]]) == 0

    # Two cities
    assert tsp([[0, 5], [5, 0]]) == 10  # 0→1→0

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List
import math


def bitmask_dp(n, cost_matrix) -> int:
    INF = float("inf")
    # dp[mask][i]: optimal value having used subset `mask`, currently at element i
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # base case: start at element 0, mask = {0}

    for mask in range(1, 1 << n):
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            if dp[mask][i] == INF:
                continue
            for j in range(n):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                cost = dp[mask][i] + cost_matrix[i][j]   # transition cost
                if cost < dp[new_mask][j]:
                    dp[new_mask][j] = cost

    full = (1 << n) - 1
    return int(min(dp[full][i] + cost_matrix[i][0] for i in range(n)))
```

## 5. Variants & pitfalls

### Held-Karp TSP (`dp[mask][i]`)

Two-dimensional state: the visited set and the current city. Final answer requires closing the tour. O(2^N · N²) time.

### Assignment problem (`dp[mask]`)

Assign the first `popcount(mask)` people to the items in `mask`. One-dimensional mask state. `dp[mask] = min cost to assign people 0..popcount(mask)-1 to items in mask`. Transition adds the next item to the mask. O(2^N · N) time.

### Subset-sum / boolean partitioning (`dp[mask]` as bool)

`dp[mask]` = True if the subset `mask` satisfies some property. Used for partition-into-k-equal-subsets: can we partition elements into groups each summing to `target`?

### Bitmask + BFS (Shortest Path Visiting All Nodes — LeetCode 847)

State = `(current_node, visited_mask)`. BFS guarantees minimum steps. Total states = N · 2^N; each processed once. O(2^N · N²) in the worst case.

### Submask enumeration

To iterate all non-empty submasks of `mask`:
```python
sub = mask
while sub:
    # process sub
    sub = (sub - 1) & mask
```
This runs in O(2^popcount(mask)) per mask, and summed over all masks gives O(3^N) total (each element is either in neither, in outer only, or in both).

### Pitfalls

- **N > 20**: 2^25 ≈ 33M masks times N inner operations often exceeds time and memory limits. If N is large, bitmask DP is the wrong approach.
- **City 0 always in mask**: in TSP, the starting city must always be in the mask. Skipping this check wastes computation on unreachable states.
- **Submask enumeration is O(3^N)**: not O(2^N · 2^N). The sum ∑_mask 2^popcount(mask) = 3^N by the binomial theorem.
- **Forgetting to close the tour**: the final TSP answer is not `min(dp[full][i])` — you must add `dist[i][0]` to return to the start.

## 6. Complexity

- **Time:** O(2^N · N²) for TSP-like problems with a transition inner loop; O(2^N · N) for assignment-style; O(3^N) for full submask DP.
- **Space:** O(2^N · N) for the DP table.

## 7. Problem set

- [Medium] [Beautiful Arrangement](https://leetcode.com/problems/beautiful-arrangement/) — assignment bitmask DP; count valid permutations where each element satisfies a divisibility condition.
- [Medium] [Partition to K Equal Sum Subsets](https://leetcode.com/problems/partition-to-k-equal-sum-subsets/) — boolean bitmask DP; check if array can be split into k equal-sum groups.
- [Hard] [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) — bitmask BFS; state = (node, visited_mask); minimum steps to visit all nodes.
- [Hard] [Smallest Sufficient Team](https://leetcode.com/problems/smallest-sufficient-team/) — bitmask DP over skill sets; find minimum number of people covering all required skills.
- [Hard] [Find Minimum Time to Finish All Jobs](https://leetcode.com/problems/find-minimum-time-to-finish-all-jobs/) — assign jobs (bitmask) to k workers; minimize max load.
- [Hard] [Number of Ways to Wear Different Hats to Each Other](https://leetcode.com/problems/number-of-ways-to-wear-different-hats-to-each-other/) — assign hats to people; dp[mask] = ways to assign hats to people in mask.
- [Hard] [Maximum Students Taking Exam](https://leetcode.com/problems/maximum-students-taking-exam/) — row-by-row bitmask DP; each row's seating mask must be compatible with the previous row.
- [Hard] [Minimum Number of Work Sessions to Finish the Tasks](https://leetcode.com/problems/minimum-number-of-work-sessions-to-finish-the-tasks/) — subset packing; dp[mask] = min sessions to complete tasks in mask.

## 8. Related patterns

- [BFS](../graphs/bfs.md) — combined with bitmask for state-space BFS where the state includes a visited subset; "Shortest Path Visiting All Nodes" is the canonical example.
- [2D DP](2d-dp.md) — bitmask DP can be viewed as a 2D DP where one axis is an exponentially large state; same fill-order discipline applies.
- [Topological Sort](../graphs/topological-sort.md) — some bitmask DP problems over DAGs fill states in topological order of the mask (increasing popcount).
- [Tree DP](tree-dp.md) — when the tree has small branching factor and small N, tree DP can combine with bitmask to track subsets at each node.

## 9. Interviewer follow-ups

**Q: Why does N ≤ 20 matter?**
2^20 ≈ 10^6 states, times N ≈ 20 transitions each, gives ~2×10^7 operations — fast. At N = 25, the table has 2^25 ≈ 33M rows; with N columns each, the table alone is ~660M integers — gigabytes of memory and billions of operations. N = 30 is completely infeasible for any bitmask DP. The moment N exceeds ~20, look for a different approach (greedy, approximation, branch-and-bound).

**Q: Explain the submask iteration trick `sub = (sub - 1) & mask`.**
Subtracting 1 from `sub` flips the lowest set bit to 0 and sets all lower bits to 1. ANDing with `mask` clears any bits that are not in `mask`. The result is the largest submask of `mask` that is strictly less than `sub`. This iterates all 2^popcount(mask) submasks of `mask` (excluding 0) in descending order, and terminates when `sub` reaches 0. It runs in O(2^popcount(mask)) per call — not O(mask) — making it efficient.
