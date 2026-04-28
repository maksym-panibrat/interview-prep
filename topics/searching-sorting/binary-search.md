# Binary Search

## 1. TL;DR

Binary search applies whenever you have a **sorted array** (or any monotonic predicate over an integer or real range): either to locate a target in O(log n), or to find the smallest/largest value satisfying some condition. The signal is "sorted input", "O(log n) required", or a feasibility check that flips from False to True exactly once as you move across a range. Time: O(log n). Space: O(1).

## 2. Intuition

Imagine searching a phone book for "Smith." You open to the middle: if the page shows "Rogers," Smith must be in the right half — you tear the left half away and repeat. Each step cuts the remaining candidates in half, so after k steps you have n / 2^k candidates left. When that hits 1 you have found (or ruled out) your target.

The general principle: if a predicate P(x) is **monotonic** — False for all values below some threshold and True for all values above — you can binary-search for the threshold. Half the range is discarded at every step because the monotonicity invariant tells you which half can't contain the answer.

Two questions determine your loop structure:

1. Are you looking for an exact match, or a boundary (first True / last False)?
2. What invariant do you maintain about `lo` and `hi`?

Getting those two answers right prevents the classic off-by-one bugs.

## 3. Walkthrough

### Classic search: find target = 7 in [1, 3, 5, 7, 9, 11]

```
nums  = [1, 3, 5, 7, 9, 11]
index =  0  1  2  3  4   5
```

| step | lo | hi | mid | nums[mid] | action          |
|------|----|----|-----|-----------|-----------------|
| 1    | 0  | 5  | 2   | 5         | 5 < 7 → lo = 3  |
| 2    | 3  | 5  | 4   | 9         | 9 > 7 → hi = 3  |
| 3    | 3  | 3  | 3   | 7         | found → return 3|

Loop condition `lo <= hi` keeps running while there is at least one candidate. At step 3 `lo == hi == mid == 3`; `nums[3] == 7` — done.

### Leftmost insert (bisect_left): find leftmost position for target = 2 in [1, 2, 2, 2, 3]

We want the index of the first element `>= 2`. Invariant: everything to the left of `lo` is `< target`; everything from `hi` onward is `>= target`. `lo` converges on the answer.

```
nums  = [1, 2, 2, 2, 3]
index =  0  1  2  3  4
```

| step | lo | hi | mid | nums[mid] | action          |
|------|----|----|-----|-----------|-----------------|
| 1    | 0  | 5  | 2   | 2         | 2 >= 2 → hi = 2 |
| 2    | 0  | 2  | 1   | 2         | 2 >= 2 → hi = 1 |
| 3    | 0  | 1  | 0   | 1         | 1 < 2 → lo = 1  |
| 4    | lo == hi == 1 | | | | return 1        |

Notice `hi` starts at `len(nums)` (not `len(nums) - 1`) so the insert position "after all elements" is reachable.

### Search on answer space: Koko eating bananas

Koko has piles of bananas. She must finish all piles in H hours. What is the minimum eating speed k? As k increases, finishing in H hours gets easier — the feasibility function is monotonic. Binary-search for the smallest k where `can_finish(k)` is True.

```
piles = [3, 6, 7, 11], H = 8
lo = 1, hi = max(piles) = 11

feasible(6): ceil(3/6)+ceil(6/6)+ceil(7/6)+ceil(11/6) = 1+1+2+2 = 6 <= 8  → True
feasible(4): ceil(3/4)+ceil(6/4)+ceil(7/4)+ceil(11/4) = 1+2+2+3 = 8 <= 8  → True
feasible(3): ceil(3/3)+ceil(6/3)+ceil(7/3)+ceil(11/3) = 1+2+3+4 = 10 > 8  → False
feasible(4): true (already shown above) → lo stays high, hi=4 (range narrows further). With lo=hi=4 the loop exits.
Result: 4 hours per banana — the smallest feasible rate.
```

Answer: 4. This pattern — binary search on the *answer value*, not array indices — is one of the highest-leverage patterns to internalize.

## 4. Implementation

```python
from __future__ import annotations
from typing import Callable, List


def binary_search(nums: List[int], target: int) -> int:
    """Classic binary search. Returns index of target, or -1 if not found."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2  # avoids overflow in C++/Java; same as (lo+hi)//2 in Python
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bisect_left(nums: List[int], target: int) -> int:
    """Leftmost insertion point: index of first element >= target.

    Equivalent to Python's bisect.bisect_left.
    Returns len(nums) if all elements are < target.
    """
    lo, hi = 0, len(nums)  # hi = len, not len-1, to allow insert-at-end
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid  # nums[mid] >= target: mid could be the answer, keep it
    return lo


def bisect_right(nums: List[int], target: int) -> int:
    """Rightmost insertion point: index of first element > target.

    Equivalent to Python's bisect.bisect_right.
    Returns len(nums) if all elements are <= target.
    """
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] <= target:
            lo = mid + 1  # nums[mid] <= target: mid is definitely not after the last match
        else:
            hi = mid
    return lo


def search_on_answer(lo: int, hi: int, feasible: Callable[[int], bool]) -> int:
    """Generic template: smallest integer x in [lo, hi] where feasible(x) is True.

    Assumes feasible is monotonic: False ... False True ... True over [lo, hi].
    Returns `hi` if no feasible value exists in `[lo, hi]`; the caller should check `feasible(result)` if the no-solution case is possible.
    """
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid   # mid might be the answer; don't discard it
        else:
            lo = mid + 1  # mid is definitely not the answer
    return lo


if __name__ == "__main__":
    # Classic search smoke tests
    assert binary_search([1, 3, 5, 7, 9], 5) == 2
    assert binary_search([1, 3, 5, 7, 9], 1) == 0
    assert binary_search([1, 3, 5, 7, 9], 9) == 4
    assert binary_search([1, 3, 5, 7, 9], 4) == -1
    assert binary_search([], 1) == -1

    # bisect_left / bisect_right
    assert bisect_left([1, 2, 2, 2, 3], 2) == 1
    assert bisect_right([1, 2, 2, 2, 3], 2) == 4

    # Search on answer space: minimum eating speed (Koko)
    import math

    def koko_feasible(speed: int, piles: list, h: int) -> bool:
        return sum(math.ceil(p / speed) for p in piles) <= h

    piles, h = [3, 6, 7, 11], 8
    ans = search_on_answer(1, max(piles), lambda k: koko_feasible(k, piles, h))
    assert ans == 4, f"expected 4, got {ans}"

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import Callable, List


def binary_search(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bisect_left(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def bisect_right(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def search_on_answer(lo: int, hi: int, feasible: Callable[[int], bool]) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## 5. Variants & pitfalls

### Classic search (`lo <= hi`)

Use when you want an exact match and -1 on miss. The invariant is "if target is present, it lives in `[lo, hi]`." When `lo > hi` the range is empty — not found.

### Leftmost insert (`bisect_left` semantics)

Use when you want the first index where `nums[idx] >= target`. Loop condition is `lo < hi`; `hi` starts at `len(nums)`. Key update rule: `hi = mid` (not `mid - 1`) when `nums[mid] >= target`, because `mid` itself could be the answer.

### Rightmost insert (`bisect_right` semantics)

Use when you want the first index where `nums[idx] > target`. Same structure as `bisect_left` but `lo = mid + 1` when `nums[mid] <= target`. The range of indices of `target` in `nums` is then `[bisect_left(nums, target), bisect_right(nums, target))`.

### Search in rotated sorted array (LeetCode 33)

One of the two halves around `mid` is always sorted. Check which half is sorted (compare `nums[lo]` with `nums[mid]`), then determine whether target lies in that sorted half. If yes, narrow to that half; otherwise narrow to the other.

### Search on answer space

When the answer is itself a numeric value `x` and you can write a monotonic feasibility function `f(x)` (False for too-small values, True once x is large enough), binary-search on `[lo_answer, hi_answer]` for the first True. This handles:
- **Koko Eating Bananas** (minimum eating speed)
- **Capacity to Ship Packages** (minimum ship capacity)
- **Split Array Largest Sum** (minimum maximum subarray sum)

The template is `search_on_answer` above. This is one of the highest-leverage patterns in binary search — many problems that look unrelated to sorted arrays are really "binary search on the answer" in disguise.

### Pitfalls

- **`mid = (lo + hi) // 2` overflow**: Not an issue in Python (arbitrary-precision integers), but in C++/Java use `lo + (hi - lo) // 2` to avoid signed-integer overflow when `lo + hi` exceeds `INT_MAX`.
- **`lo < hi` vs `lo <= hi`**: Classic exact-match uses `<=`; boundary-search uses `<`. Mixing these up either skips the last candidate or loops forever.
- **Forgetting `lo = mid + 1`** (writing `lo = mid`): When `feasible(mid)` is False and you set `lo = mid`, `mid` is always `(lo + lo) // 2 == lo`, so `lo` never advances — infinite loop. Always write `lo = mid + 1` to discard `mid`.
- **Wrong invariant for `bisect_*`**: The *only* difference between `bisect_left` and `bisect_right` is the comparison in the lo-advance branch: `nums[mid] < target` (left) vs `nums[mid] <= target` (right). The `hi = mid` rule is identical for both. Confusing the two by a single character flips the result for runs of equal elements — left finds the first occurrence, right finds the position just after the last.

## 6. Complexity

- **Time:** O(log n) — each iteration cuts the candidate range in half, so after at most ceil(log2(n + 1)) iterations the range is empty or a single element.
- **Space:** O(1) — only a constant number of index variables (`lo`, `hi`, `mid`) are maintained regardless of input size.

## 7. Problem set

- [Easy] [Binary Search](https://leetcode.com/problems/binary-search/) — the purest form; good for drilling the `lo <= hi` loop without distractions.
- [Easy] [Search Insert Position](https://leetcode.com/problems/search-insert-position/) — forces you to return the correct insertion index on a miss, confirming your off-by-one handling.
- [Medium] [Find First and Last Position of Element in Sorted Array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/) — combines `bisect_left` and `bisect_right` in one problem; solidifies both boundary variants.
- [Medium] [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) — classic twist that forces you to reason about which half is sorted at every step.
- [Medium] [Find Peak Element](https://leetcode.com/problems/find-peak-element/) — binary search on a non-sorted array using a local monotonicity argument; expands intuition beyond "sorted input only."
- [Medium] [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) — binary search for a structural feature (the rotation pivot) rather than a value.
- [Medium] [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) — the entry-level search-on-answer problem; write the feasibility check, then plug into the template.
- [Medium] [Capacity to Ship Packages Within D Days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/) — structurally identical to Koko but with a slightly trickier feasibility check; builds fluency with the pattern.
- [Hard] [Median of Two Sorted Arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/) — binary search on partition indices across two arrays; requires careful invariant reasoning under pressure.
- [Hard] [Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/) — search-on-answer at hard difficulty; the feasibility check is a greedy scan, not a one-liner.

## 8. Related patterns

- **Two Pointers** (will live at `../two-pointers-sliding-window/two-pointers.md`) — a linear-time alternative when the array is not sorted or you need to find pairs; binary search and two pointers both exploit sorted structure but in different ways.
- **Quicksort & Mergesort** (will live at `quicksort-mergesort.md` in this same folder) — share the same divide-and-conquer recurrence (halving the problem each step); understanding the recurrence deepens intuition for why binary search is O(log n).
- **Binary Search Tree** (will live at `../trees/bst.md`) — binary search on an explicit tree shape; each comparison at a node mirrors the `mid` comparison in array binary search.

## 9. Interviewer follow-ups

**Q: What changes if the array has duplicates?**
Classic binary search still finds *a* match but not necessarily the first or last. Use `bisect_left` to get the leftmost index of `target` and `bisect_right` to get one past the rightmost. The range of all occurrences is `[bisect_left(nums, target), bisect_right(nums, target))`. If `bisect_left` returns `idx`, the element is present iff `idx < len(nums) and nums[idx] == target`. The bounds check matters: `bisect_left` returns `len(nums)` when the target is larger than every element, so indexing `nums[idx]` would raise `IndexError` without it.

**Q: What if the array is rotated?**
At every `mid`, one of the two halves `[lo, mid]` or `[mid, hi]` is guaranteed to be sorted (compare `nums[lo]` with `nums[mid]`). Check whether the target falls within the sorted half. If yes, discard the other half; if no, discard the sorted half. This keeps O(log n) time with no pivot-finding pre-pass.

**Q: What if the data doesn't fit in memory?**
Model the input as a sorted sequence accessible via random reads (e.g., a sorted file on disk or a remote query API). Binary search still works: issue at most O(log n) page/seek reads to the storage layer, each cutting the candidate range in half. The key is that binary search touches only O(log n) positions, so you never need to load the full dataset. For a remote API (e.g., "is value x in the dataset?"), each call is one API query — O(log n) calls total.
