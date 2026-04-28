# Recall Cards

The "30 minutes before the interview" file. Each section is a single topic's TL;DR plus its Template code block, copied verbatim from the full topic file. Sections appear in study order.

For full explanations, walkthroughs, and problem sets, follow the link on each topic heading.

<!-- card sections appended by per-topic tasks -->

## [Binary Search](topics/searching-sorting/binary-search.md) ★★★

Binary search applies whenever you have a **sorted array** (or any monotonic predicate over an integer or real range): either to locate a target in O(log n), or to find the smallest/largest value satisfying some condition. The signal is "sorted input", "O(log n) required", or a feasibility check that flips from False to True exactly once as you move across a range. Time: O(log n). Space: O(1).

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

## [Quicksort & Mergesort](topics/searching-sorting/quicksort-mergesort.md) ★★★

Both algorithms sort in O(n log n) average time using divide-and-conquer: split the problem in half, recurse, combine. The signal is "implement sort," "sort with constraints (in-place, stable, k-th element)," or "describe how your sort works." Use **mergesort** when you need stability, predictable worst-case O(n log n), or are sorting a linked list; use **quicksort** when you need in-place sort with good cache behavior and can tolerate O(n²) worst-case (mitigate with randomized pivot). Time: O(n log n) average. Space: O(n) mergesort, O(log n) quicksort (recursion stack).

```python
import random
from typing import List


def merge(a: List[int], b: List[int]) -> List[int]:
    result: List[int] = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def mergesort(nums: List[int]) -> List[int]:
    if len(nums) <= 1:
        return list(nums)
    mid = len(nums) // 2
    return merge(mergesort(nums[:mid]), mergesort(nums[mid:]))


def _lomuto_partition(nums: List[int], lo: int, hi: int) -> int:
    pivot_idx = random.randrange(lo, hi + 1)
    nums[pivot_idx], nums[hi] = nums[hi], nums[pivot_idx]
    pivot = nums[hi]
    i = lo - 1
    for j in range(lo, hi):
        if nums[j] <= pivot:
            i += 1
            nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1], nums[hi] = nums[hi], nums[i + 1]
    return i + 1


def quicksort(nums: List[int]) -> None:
    def _qs(lo: int, hi: int) -> None:
        if lo < hi:
            p = _lomuto_partition(nums, lo, hi)
            _qs(lo, p - 1)
            _qs(p + 1, hi)
    if len(nums) > 1:
        _qs(0, len(nums) - 1)


def quickselect(nums: List[int], k: int) -> int:
    lo, hi, target = 0, len(nums) - 1, k - 1
    while lo < hi:
        p = _lomuto_partition(nums, lo, hi)
        if p == target:
            return nums[p]
        elif p < target:
            lo = p + 1
        else:
            hi = p - 1
    return nums[lo]
```
