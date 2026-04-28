# Backtracking Template

## 1. TL;DR

Backtracking applies when a problem asks you to **enumerate all valid configurations** — subsets, permutations, combinations, or constrained arrangements — by building solutions element by element and pruning branches the moment a partial solution cannot extend to a valid one. Signals: "all permutations / combinations / subsets," "find all valid configurations," small input (n ≤ ~20) where exponential exploration is acceptable. Time: O(2^n · n) for subsets, O(n!) for permutations, O(C(n,k) · k) for combinations.

## 2. Intuition

Think of backtracking as a guided tour of a decision tree. At each node you pick one candidate from your remaining options, add it to the partial solution, recurse into the subtree, and then **undo the pick** before trying the next candidate. That last step — restoring the state exactly as you found it — is what distinguishes backtracking from naive recursion. Without the undo, later branches inherit state from earlier ones and produce wrong results.

Three questions structure every backtracking problem:

1. **What is a "choice" at each step?** (take/skip an element, choose which position to fill, choose the next character)
2. **When is the partial solution complete?** (base case — append a copy to results)
3. **When can you prune?** (remaining candidates cannot satisfy a constraint — skip the entire subtree)

The recursion depth equals the depth of the partial solution being built, not the total input size. For subsets of n elements, depth is at most n; for permutations, exactly n.

## 3. Walkthrough

### Subsets of [1, 2, 3] — take/skip recursion

At each index we branch on two choices: include the element or skip it.

```
index 0 (1): take ───────────────────── skip ─────────────────────
                 |                                                  |
          index 1 (2): take ── skip               index 1 (2): take ── skip
                          |       |                                |       |
                   idx 2: t  s  t  s                       idx 2: t  s  t  s
                   [1,2,3][1,2][1,3][1]                   [2,3] [2] [3]  []
```

Output (left-to-right leaf order): `[1,2,3]`, `[1,2]`, `[1,3]`, `[1]`, `[2,3]`, `[2]`, `[3]`, `[]`

Each leaf is visited exactly once. The recursion reaches depth n = 3; there are 2^3 = 8 leaves.

### Permutations of [1, 2, 3] — in-place swap variant

Fix position 0 by swapping it with each of positions 0, 1, 2 in turn. Then recurse to fix position 1 among the remaining positions. Swap back before trying the next candidate at the current level.

```
start=0: swap(0,0)→[1,2,3]  swap(0,1)→[2,1,3]  swap(0,2)→[3,2,1]
  start=1: swap(1,1)→[1,2,3]  swap(1,2)→[1,3,2]
    start=2: leaf [1,2,3]       leaf [1,3,2]
  swap back to [1,2,3]        swap back to [1,2,3]
  ... (similar for [2,1,3] and [3,2,1] subtrees)
```

Six leaves total (3! = 6). At each internal node, the element swapped into position `start` is the "choice"; swap-back restores the array for sibling branches.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def subsets(nums: List[int]) -> List[List[int]]:
    """Return all subsets (power set) of nums. Each element: take or skip."""
    result: List[List[int]] = []
    path: List[int] = []

    def backtrack(index: int) -> None:
        result.append(path[:])          # every node (not just leaves) is a valid subset
        for i in range(index, len(nums)):
            path.append(nums[i])        # take
            backtrack(i + 1)
            path.pop()                  # undo — restore for the skip branch

    backtrack(0)
    return result


def permutations(nums: List[int]) -> List[List[int]]:
    """Return all permutations using the in-place swap variant."""
    result: List[List[int]] = []
    nums = list(nums)                   # work on a copy to avoid mutating the caller's list

    def backtrack(start: int) -> None:
        if start == len(nums):
            result.append(nums[:])      # leaf: full permutation
            return
        for i in range(start, len(nums)):
            nums[start], nums[i] = nums[i], nums[start]   # choose: fix nums[i] at position start
            backtrack(start + 1)
            nums[start], nums[i] = nums[i], nums[start]   # undo swap

    backtrack(0)
    return result


def combinations(n: int, k: int) -> List[List[int]]:
    """Return all k-length combinations chosen from [1, 2, ..., n] without repetition."""
    result: List[List[int]] = []
    path: List[int] = []

    def backtrack(start: int) -> None:
        if len(path) == k:
            result.append(path[:])
            return
        # pruning: need k - len(path) more elements; only proceed if enough candidates remain
        for i in range(start, n + 1):
            if n - i + 1 < k - len(path):   # not enough elements left — prune
                break
            path.append(i)
            backtrack(i + 1)
            path.pop()

    backtrack(1)
    return result


def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    """Return all combinations that sum to target; each candidate may be used unlimited times."""
    result: List[List[int]] = []
    path: List[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            c = candidates[i]
            if c > remaining:            # candidates sorted ascending — prune tail
                break
            path.append(c)
            backtrack(i, remaining - c)  # i (not i+1): same element can be reused
            path.pop()

    candidates.sort()                    # sort enables the c > remaining prune
    backtrack(0, target)
    return result


if __name__ == "__main__":
    # subsets
    ss = subsets([1, 2, 3])
    assert len(ss) == 8
    assert [] in ss and [1, 2, 3] in ss and [2] in ss

    # permutations
    perms = permutations([1, 2, 3])
    assert len(perms) == 6
    assert [1, 2, 3] in perms and [3, 2, 1] in perms

    # combinations
    combs = combinations(4, 2)
    assert len(combs) == 6
    assert [1, 2] in combs and [3, 4] in combs

    # combination_sum
    cs = combination_sum([2, 3, 6, 7], 7)
    assert sorted(sorted(c) for c in cs) == [[2, 2, 3], [7]]

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def subsets(nums: List[int]) -> List[List[int]]:
    result: List[List[int]] = []
    path: List[int] = []

    def backtrack(index: int) -> None:
        result.append(path[:])
        for i in range(index, len(nums)):
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return result


def permutations(nums: List[int]) -> List[List[int]]:
    result: List[List[int]] = []
    nums = list(nums)

    def backtrack(start: int) -> None:
        if start == len(nums):
            result.append(nums[:])
            return
        for i in range(start, len(nums)):
            nums[start], nums[i] = nums[i], nums[start]
            backtrack(start + 1)
            nums[start], nums[i] = nums[i], nums[start]

    backtrack(0)
    return result


def combinations(n: int, k: int) -> List[List[int]]:
    result: List[List[int]] = []
    path: List[int] = []

    def backtrack(start: int) -> None:
        if len(path) == k:
            result.append(path[:])
            return
        for i in range(start, n + 1):
            if n - i + 1 < k - len(path):
                break
            path.append(i)
            backtrack(i + 1)
            path.pop()

    backtrack(1)
    return result


def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    result: List[List[int]] = []
    path: List[int] = []
    candidates.sort()

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            path.append(candidates[i])
            backtrack(i, remaining - candidates[i])
            path.pop()

    backtrack(0, target)
    return result
```

## 5. Variants & pitfalls

### Subsets II — input has duplicates
Sort first. At a given recursion depth, skip an element if it equals the previous element **at the same depth** (i.e., `i > start and nums[i] == nums[i-1]: continue`). This prunes duplicate subtrees before entering them.

### Permutations II — input has duplicates
Sort first. Within a single `backtrack(start)` call, track which values have already been swapped into position `start` with a local `seen` set. Skip if `nums[i]` is already in `seen`.

### Combination Sum II — each element used at most once
Pass `i + 1` (not `i`) into the recursive call. Add the duplicate-skip check from Subsets II.

### Combination Sum III — exactly k numbers summing to n from digits 1–9
Run the combinations template over `[1..9]` with the target-sum base case.

### Pitfalls

- **Forgetting to copy the path** — appending `path` directly means all stored lists point to the same mutable object. Always append `path[:]` (or `list(path)`).
- **Forgetting the undo step** — any mutation to shared state (`path.append`, an in-place swap, a visited flag) must be reversed before the loop continues. Missing the undo corrupts all subsequent branches.
- **Skipping by index instead of by value for permutations-with-duplicates** — you must track which *values* have been placed at the current position, not which *indices*.
- **Failing to prune** — without `break` on `c > remaining` or `if n - i + 1 < k - len(path)`, the recursion explores branches that can never succeed, causing exponential blowup even on moderate inputs.

## 6. Complexity

- **Time:** O(2^n · n) for subsets — 2^n subsets, each requiring O(n) to copy; O(n!) for permutations — n! leaves, each O(n) to copy; O(C(n,k) · k) for combinations — C(n,k) leaves, each O(k) to copy.
- **Space:** O(n) auxiliary stack depth (equal to the depth of the partial solution), plus O(2^n · n) / O(n! · n) / O(C(n,k) · k) for the output itself. Inputs are small for a reason — n ≤ ~20 is the practical ceiling.

## 7. Problem set

- [Medium] [Subsets](https://leetcode.com/problems/subsets/) — baseline take/skip recursion; builds the core template.
- [Medium] [Subsets II](https://leetcode.com/problems/subsets-ii/) — adds the sort + skip-equal-sibling prune for duplicate inputs.
- [Medium] [Permutations](https://leetcode.com/problems/permutations/) — in-place swap variant; solidifies the undo pattern.
- [Medium] [Permutations II](https://leetcode.com/problems/permutations-ii/) — permutations with duplicates; requires tracking placed values at each depth.
- [Medium] [Combinations](https://leetcode.com/problems/combinations/) — C(n,k) without repetition; practice the remaining-elements prune.
- [Medium] [Combination Sum](https://leetcode.com/problems/combination-sum/) — unlimited reuse variant; note the `i` (not `i+1`) in the recursive call.
- [Medium] [Combination Sum II](https://leetcode.com/problems/combination-sum-ii/) — each element used at most once; combines the duplicate-skip with no-reuse.
- [Medium] [Combination Sum III](https://leetcode.com/problems/combination-sum-iii/) — exactly k digits summing to n; constrained combinations over [1..9].
- [Medium] [Letter Combinations of a Phone Number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/) — maps digits to character sets; good practice for branching on a different "candidate set" at each level.
- [Medium] [Generate Parentheses](https://leetcode.com/problems/generate-parentheses/) — builds strings under a structural constraint (open count >= close count); illustrates pruning with counters instead of sorted candidates.
- [Medium] [Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/) — partitions a string into palindromes; prune branches where the current substring is not a palindrome.
- [Medium] [Restore IP Addresses](https://leetcode.com/problems/restore-ip-addresses/) — builds exactly 4 segments under range and leading-zero constraints; a clean example of structural pruning.
- [Hard] [Word Break II](https://leetcode.com/problems/word-break-ii/) — enumerate all sentences; backtracking with memoisation to avoid recomputing suffixes.

## 8. Related patterns

- [Bitmask DP](../dp/bitmask-dp.md) — state-compressed alternative when subsets are the universe and you need the *optimal* result across all subsets rather than enumerating them all.
- **[N-Queens & Sudoku](n-queens-sudoku.md)** — backtracking on a 2-D board where constraint-checking (row/column/box conflicts) drives most of the pruning.
- **[Grid Backtracking](grid-search.md)** — explores paths on a grid cell by cell; same try/undo skeleton but the "candidates" at each step are the four adjacent cells.

## 9. Interviewer follow-ups

**Q: How do you avoid duplicates in the result when the input has duplicate elements?**
Sort the input first. Inside the loop, add `if i > start and nums[i] == nums[i-1]: continue`. This skips starting a new subtree with the same value as the one you just finished — identical subtrees are pruned before entering them, giving a clean deduplicated output with no post-processing.

**Q: Can you solve subsets iteratively?**
Yes — enumerate all integers from 0 to 2^n - 1. Each integer's binary representation encodes which elements to include (bit k = 1 -> include `nums[k]`). This is the bitmask enumeration approach: one pass, no recursion, O(2^n · n) work. It is rarely cleaner than the recursive version for arbitrary backtracking, but it is exact and branchless for pure subsets.

**Q: The recursion stack is deep for large n. How would you reduce peak memory?**
Iterative deepening DFS (IDDFS) — artificially cap the recursion depth, run to completion at that depth, then increase the cap by one and repeat. This trades time (re-exploring shallow nodes) for stack space: peak stack depth stays bounded while still finding all solutions. In practice, n <= 20 means the native recursive depth of 20 frames is negligible, so IDDFS is a name-drop rather than a practical necessity here.
