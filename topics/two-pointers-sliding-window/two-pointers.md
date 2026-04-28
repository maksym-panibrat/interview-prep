# Two Pointers

## 1. TL;DR

Two pointers works on sorted (or sortable) arrays where you need pairs or triplets summing to a target, "largest area" problems, or in-place compaction without extra space. Maintain two indices that move toward each other (or one fast, one slow in the same direction); each step eliminates at least one candidate, giving O(n) after sorting. The signal is "sorted input," "pair/triplet sum," "in-place removal," or "without extra space." Time: O(n) on a sorted array; O(n log n) when sorting first dominates. Space: O(1) extra.

## 2. Intuition

Imagine `[2, 7, 11, 15]` sorted in ascending order and you want two numbers that sum to 18. Start with the widest possible window: left = smallest (index 0), right = largest (index 3). Their sum is 17 — too small. The only way to increase the sum is to move the left pointer right (since right is already at the maximum). There is no point checking any pair that includes `arr[0]` because the best partner for it is `arr[3]`, and that was already too small. This is the invariant: **at every step, we rule out at least one element permanently**, so the two pointers together advance at most n times — O(n) total.

For three-sum, fix one element with an outer loop and run the two-pointer inner loop on the remaining sorted subarray. The outer loop is O(n), the inner loop is O(n), giving O(n²) total for 3Sum.

The same-direction variant (slow/fast) compacts arrays in-place: `slow` tracks the write position, `fast` scans for the next valid element. Every element is visited once by `fast` — O(n).

## 3. Walkthrough

### 2Sum on a sorted array: [2, 7, 11, 15], target = 18

```
nums  = [2,  7,  11,  15]
index =  0   1    2    3
```

| step | l | r | nums[l] | nums[r] | sum | action               |
|------|---|---|---------|---------|-----|----------------------|
| 1    | 0 | 3 | 2       | 15      | 17  | 17 < 18 → l += 1    |
| 2    | 1 | 3 | 7       | 15      | 22  | 22 > 18 → r -= 1    |
| 3    | 1 | 2 | 7       | 11      | 18  | found! return [1, 2] |

At step 1, `sum = 17 < 18`: to get a larger sum we must replace the smaller element, so `l` moves right. At step 2, `sum = 22 > 18`: to reduce the sum we replace the larger element, so `r` moves left. At step 3 the sum matches — done in 3 steps on 4 elements.

### 3Sum on [-4, -1, -1, 0, 1, 2]

Sort first (already sorted here): `[-4, -1, -1, 0, 1, 2]`.

Fix `i = 0` (value -4), run two-pointer on `[-1, -1, 0, 1, 2]`:

```
l=1 r=5: -4 + (-1) + 2 = -3 < 0 → l += 1
l=2 r=5: -4 + (-1) + 2 = -3 < 0 → l += 1
l=3 r=5: -4 + 0 + 2 = -2 < 0 → l += 1
l=4 r=5: -4 + 1 + 2 = -1 < 0 → l += 1
l=5 == r=5 → inner loop ends. No triplet with i=0.
```

Fix `i = 1` (value -1). Skip if `nums[1] == nums[0]`? No: -1 ≠ -4, proceed.
Run two-pointer on `[-1, 0, 1, 2]` (indices 2–5):

```
l=2 r=5: -1 + (-1) + 2 = 0 ✓ → record [-1, -1, 2]
  skip duplicates: l advances past any -1s (l→3), r advances past any 2s (r→4)
l=3 r=4: -1 + 0 + 1 = 0 ✓ → record [-1, 0, 1]
  skip duplicates: l→4, r→3 → l > r, inner loop ends.
```

Fix `i = 2` (value -1). `nums[2] == nums[1]` (both -1) → skip to avoid duplicate triplets.

Fix `i = 3` (value 0). Run two-pointer on `[1, 2]` (indices 4–5):

```
l=4 r=5: 0 + 1 + 2 = 3 > 0 → r -= 1
l=4 == r=4 → inner loop ends.
```

Fix `i = 4` (value 1). Only one element to the right (`r=5`); `l >= r` immediately — stop outer loop.

Result: `[[-1, -1, 2], [-1, 0, 1]]`.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def two_sum_sorted(nums: List[int], target: int) -> List[int]:
    """Two Sum II: nums is 1-indexed in the problem but we use 0-indexed here.

    Returns [l, r] (0-indexed) such that nums[l] + nums[r] == target.
    Assumes exactly one solution exists.
    """
    l, r = 0, len(nums) - 1
    while l < r:
        s = nums[l] + nums[r]
        if s == target:
            return [l, r]
        elif s < target:
            l += 1
        else:
            r -= 1
    return []  # no solution (shouldn't reach here per problem guarantee)


def three_sum(nums: List[int]) -> List[List[int]]:
    """Return all unique triplets summing to 0. O(n^2) time, O(1) extra space."""
    nums.sort()
    result: List[List[int]] = []
    n = len(nums)
    for i in range(n - 2):
        # Skip duplicate values for the fixed element.
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                result.append([nums[i], nums[l], nums[r]])
                # Skip duplicates on both sides after recording.
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return result


def container_with_most_water(heights: List[int]) -> int:
    """LeetCode 11. Return the maximum water the container can hold.

    At each step, the area is (r - l) * min(heights[l], heights[r]).
    Move the pointer with the shorter bar inward — keeping the taller bar
    is the only chance to find a larger area with a narrower gap.
    """
    l, r = 0, len(heights) - 1
    max_water = 0
    while l < r:
        water = (r - l) * min(heights[l], heights[r])
        max_water = max(max_water, water)
        if heights[l] <= heights[r]:
            l += 1
        else:
            r -= 1
    return max_water


def remove_duplicates_sorted(nums: List[int]) -> int:
    """LeetCode 26. In-place dedup. Returns the count of unique elements.

    slow tracks the next write position; fast scans ahead for new values.
    Same-direction (slow/fast) two-pointer variant.
    """
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1  # number of unique elements


if __name__ == "__main__":
    # two_sum_sorted
    assert two_sum_sorted([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum_sorted([2, 7, 11, 15], 18) == [1, 2]
    assert two_sum_sorted([2, 7, 11, 15], 26) == [2, 3]

    # three_sum
    result = three_sum([-1, 0, 1, 2, -1, -4])
    result_sorted = [sorted(t) for t in result]
    result_sorted.sort()
    assert result_sorted == [[-1, -1, 2], [-1, 0, 1]]

    result2 = three_sum([-4, -1, -1, 0, 1, 2])
    result2_sorted = [sorted(t) for t in result2]
    result2_sorted.sort()
    assert result2_sorted == [[-1, -1, 2], [-1, 0, 1]]

    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    assert three_sum([1, 2, 3]) == []

    # container_with_most_water
    assert container_with_most_water([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert container_with_most_water([1, 1]) == 1

    # remove_duplicates_sorted
    arr = [1, 1, 2]
    k = remove_duplicates_sorted(arr)
    assert k == 2 and arr[:k] == [1, 2]

    arr2 = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    k2 = remove_duplicates_sorted(arr2)
    assert k2 == 5 and arr2[:k2] == [0, 1, 2, 3, 4]

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def two_sum_sorted(nums: List[int], target: int) -> List[int]:
    l, r = 0, len(nums) - 1
    while l < r:
        s = nums[l] + nums[r]
        if s == target:
            return [l, r]
        elif s < target:
            l += 1
        else:
            r -= 1
    return []


def three_sum(nums: List[int]) -> List[List[int]]:
    nums.sort()
    result: List[List[int]] = []
    n = len(nums)
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                result.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return result


def container_with_most_water(heights: List[int]) -> int:
    l, r = 0, len(heights) - 1
    max_water = 0
    while l < r:
        water = (r - l) * min(heights[l], heights[r])
        max_water = max(max_water, water)
        if heights[l] <= heights[r]:
            l += 1
        else:
            r -= 1
    return max_water
```

## 5. Variants & pitfalls

### Opposing pointers (toward each other)

The classic two-pointer setup: `l = 0, r = len(nums) - 1`, loop while `l < r`. Works on sorted arrays where the sum (or some monotone function of `nums[l]` and `nums[r]`) needs to hit a target. Container With Most Water uses the same structure but with a different greedy argument: always move the shorter-bar side because the width only decreases; keeping the taller bar maximizes any possible future gain.

### Same-direction (slow/fast)

`slow` marks the write position (or the last "valid" position); `fast` scans the full array. Use when compacting in-place: Remove Duplicates, Move Zeroes, partition around a value. The invariant is `nums[0..slow]` is the cleaned prefix; everything behind `fast` has been decided.

### Sorting first as enabler

Many two-pointer problems work only because the array is sorted. When the input is unsorted, sort it first — O(n log n) — then apply the linear two-pointer pass. The overall complexity is O(n log n) dominated by sort. If you're forbidden from sorting (e.g., original indices must be preserved), fall back to a hash set at O(n) time but O(n) space.

### Duplicate handling in 3Sum

After recording a triplet, advance both `l` and `r` past any identical values before the final `l += 1; r -= 1`. Skipping the dedup lets the same triplet appear multiple times. Similarly, in the outer loop, skip `nums[i] == nums[i-1]` (but only when `i > 0`). The guard `i > 0` prevents skipping the very first element.

### kSum generalization

For k-sum (k ≥ 4), recurse: reduce to (k-1)-sum by fixing the outermost element, recurse on the remaining sorted subarray, and use two-pointer as the base case (k=2). The time complexity is O(n^(k-1)). Duplicate skipping must be applied at every recursion level.

### Pitfalls

- **Using on unsorted arrays**: two-pointer relies on the monotone property of a sorted array. Applying it to an unsorted array produces wrong answers silently.
- **Off-by-one in duplicate skip**: writing `while nums[l] == nums[l + 1]: l += 1` instead of `while l < r and nums[l] == nums[l + 1]: l += 1` reads out of bounds when `l` reaches the last index.
- **Rebuilding inner state**: in 3Sum, re-sorting or re-initializing the inner two pointers for every outer iteration is O(n²) in initialization alone — always set `l = i + 1, r = n - 1` fresh for each outer `i`.

## 6. Complexity

- **Time:** O(n) on a sorted array — the two pointers together advance at most n steps. O(n log n) overall when sorting first. O(n²) for 3Sum — outer loop O(n) × inner two-pointer O(n).
- **Space:** O(1) extra — only the two index variables; the output list does not count toward auxiliary space.

## 7. Problem set

- [Easy] [Two Sum II — Input Array Is Sorted](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/) — the canonical opposing-pointers problem; forces you to justify the greedy pointer-movement rule.
- [Easy] [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) — opposing pointers on a string, skipping non-alphanumeric characters; good for practicing the inward-advance rule with a filter.
- [Easy] [Remove Duplicates from Sorted Array](https://leetcode.com/problems/remove-duplicates-from-sorted-array/) — same-direction slow/fast; confirms you can compact an array in-place without extra space.
- [Easy] [Move Zeroes](https://leetcode.com/problems/move-zeroes/) — same-direction two-pointer; variant where you write non-zero values forward and backfill zeroes.
- [Medium] [3Sum](https://leetcode.com/problems/3sum/) — the classic fixed-outer + two-pointer inner; duplicate handling is the main source of bugs.
- [Medium] [3Sum Closest](https://leetcode.com/problems/3sum-closest/) — same structure as 3Sum but track the minimum absolute difference instead of zero; no duplicate-skipping needed but the update condition changes.
- [Medium] [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) — the greedy argument (always move the shorter bar) is non-obvious; understanding why the other bar is safe to skip is the core insight.
- [Medium] [Sort Colors](https://leetcode.com/problems/sort-colors/) — Dutch National Flag with three pointers; extends the two-pointer partition idea to three regions.
- [Hard] [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) — two-pointer with running left-max and right-max; each bar can trap water equal to min(left_max, right_max) minus its own height.
- [Hard] [4Sum](https://leetcode.com/problems/4sum/) — kSum recursion bottoming out at two-pointer; applies duplicate skipping at two levels.

## 8. Related patterns

- **[Binary Search](../searching-sorting/binary-search.md)** — when the array is sorted and you need a single target location, binary search is O(log n); two pointers are O(n) but handle pair/triplet constraints that binary search cannot express in a single query.
- **[Heapsort & Heaps](../searching-sorting/heapsort.md)** — heaps handle "k-th element" in unsorted data without sorting; two pointers require sorted data but use O(1) space where a heap would need O(k).
- **[Fast/Slow Pointers](fast-slow-pointers.md)** — same-direction variant used specifically on linked lists for cycle detection and midpoint-finding.
- **[Sliding Window](sliding-window.md)** — same two-index structure but both pointers move in the same direction and the window expands right before contracting left; the constraint is on the window's contents rather than a pair sum.
- **[BST](../trees/bst.md)** — for an unsorted collection where the pair-sum problem must be answered online, a BST or hash set gives O(log n) or O(1) lookup per element; the trade-off is O(n) space.

## 9. Interviewer follow-ups

**Q: What if the array isn't sorted?**
Sort it first in O(n log n), then apply the two-pointer pass. The total complexity is O(n log n) dominated by sort. If the original indices must be preserved (e.g., Two Sum with a hash map), use a hash set instead: scan left to right, for each element check `target - element` in the set, then insert. That's O(n) time and O(n) space — better time but more space than the sort + two-pointer approach.

**Q: kSum generalization?**
Write a recursive `k_sum(nums, target, k, start)` function. When `k == 2`, apply the two-pointer base case from `start` to the end. For `k > 2`, fix `nums[i]` with an outer loop (with duplicate skipping), then recurse on `k_sum(nums, target - nums[i], k - 1, i + 1)`. Time complexity is O(n^(k-1)) — each recursion level adds one O(n) scan. Duplicate skipping must be applied at every recursion level, not just at the two-pointer base case.
