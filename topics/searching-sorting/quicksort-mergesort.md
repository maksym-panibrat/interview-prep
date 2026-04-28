# Quicksort & Mergesort

## 1. TL;DR

Both algorithms sort in O(n log n) average time using divide-and-conquer: split the problem in half, recurse, combine. The signal is "implement sort," "sort with constraints (in-place, stable, k-th element)," or "describe how your sort works." Use **mergesort** when you need stability, predictable worst-case O(n log n), or are sorting a linked list; use **quicksort** when you need in-place sort with good cache behavior and can tolerate O(n²) worst-case (mitigate with randomized pivot). Time: O(n log n) average. Space: O(n) mergesort, O(log n) quicksort (recursion stack).

## 2. Intuition

**Mergesort** splits the array down the middle, sorts each half independently, then merges two already-sorted halves into one sorted result. Splitting is trivial (structural halving); all the work happens in the merge step. Because the merge of two sorted sequences of total length n takes exactly O(n) time, and the recursion tree has O(log n) levels, the total work is O(n log n) regardless of the input.

**Quicksort** picks a pivot and partitions the array so everything smaller than the pivot is to the left and everything larger is to the right — the pivot is now in its final sorted position. Recursing on each side sorts the rest. No merge step is needed; the work is done during the partition. The split point depends on the pivot choice (not structural halving), so worst-case behaviour (already-sorted input with a naive last-element pivot) is O(n²). Randomizing the pivot makes this astronomically unlikely in practice.

Both recurrences are `T(n) = 2T(n/2) + O(n)`, solved by the master theorem to O(n log n). Understanding this recurrence is also why binary search is O(log n): you get `T(n) = T(n/2) + O(1)`, one level cheaper.

## 3. Walkthrough

### Mergesort on [5, 2, 4, 6, 1, 3]

Recursion tree (split phase — every node becomes two children):

```
                 [5, 2, 4, 6, 1, 3]
                /                   \
        [5, 2, 4]                 [6, 1, 3]
        /       \                 /       \
    [5, 2]      [4]           [6, 1]      [3]
    /    \                    /    \
  [5]   [2]               [6]    [1]
```

Merge phase (bottom up — merge pairs into sorted sequences):

```
[5] + [2]  → merge → [2, 5]
[2, 5] + [4]  → merge → [2, 4, 5]

[6] + [1]  → merge → [1, 6]
[1, 6] + [3]  → merge → [1, 3, 6]

[2, 4, 5] + [1, 3, 6]  → merge (final step below)
```

Detailed merge of `a = [2, 4, 5]` and `b = [1, 3, 6]`:

| i (ptr into a) | j (ptr into b) | min picked | result so far     |
|----------------|----------------|------------|-------------------|
| 0              | 0              | b[0]=1     | [1]               |
| 0              | 1              | a[0]=2     | [1, 2]            |
| 1              | 1              | b[1]=3     | [1, 2, 3]         |
| 1              | 2              | a[1]=4     | [1, 2, 3, 4]      |
| 2              | 2              | a[2]=5     | [1, 2, 3, 4, 5]   |
| exhausted a    | 2              | b[2]=6     | [1, 2, 3, 4, 5, 6]|

Result: `[1, 2, 3, 4, 5, 6]`.

### Quicksort Lomuto partition on [3, 6, 8, 10, 1, 2, 1], pivot = last element (1)

`pivot = 1`, `i = -1` (tracks the boundary of elements <= pivot).

```
Initial:  [3, 6, 8, 10, 1, 2, 1]
           0  1  2   3  4  5  6   (indices)
pivot = nums[6] = 1
i = -1

j=0: nums[0]=3 > 1 → no swap.   i=-1
j=1: nums[1]=6 > 1 → no swap.   i=-1
j=2: nums[2]=8 > 1 → no swap.   i=-1
j=3: nums[3]=10 > 1 → no swap.  i=-1
j=4: nums[4]=1 <= 1 → i=0, swap(nums[0], nums[4])
     [1, 6, 8, 10, 3, 2, 1]     i=0
j=5: nums[5]=2 > 1 → no swap.   i=0
End of scan: swap(nums[i+1], nums[6]) → swap(nums[1], nums[6])
     [1, 1, 8, 10, 3, 2, 6]
pivot 1 now sits at index 1.

Left subarray  [1]        (index 0)   → already sorted (length 1)
Right subarray [8,10,3,2,6] (indices 2–6) → recurse
```

After recursive sorts of both sides the array becomes `[1, 1, 2, 3, 6, 8, 10]`.

## 4. Implementation

```python
from __future__ import annotations
import random
from typing import List


# ── Mergesort ────────────────────────────────────────────────────────────────

def merge(a: List[int], b: List[int]) -> List[int]:
    """Merge two sorted lists into a new sorted list. O(len(a) + len(b)) time and space."""
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
    """Pure mergesort. Returns a new sorted list; does not mutate input."""
    if len(nums) <= 1:
        return list(nums)
    mid = len(nums) // 2
    left = mergesort(nums[:mid])
    right = mergesort(nums[mid:])
    return merge(left, right)


# ── Quicksort (Lomuto partition, randomized pivot) ────────────────────────────

def _lomuto_partition(nums: List[int], lo: int, hi: int) -> int:
    """Partition nums[lo..hi] around a random pivot using Lomuto scheme.

    Swaps the chosen pivot to nums[hi], then scans left-to-right.
    Returns the final index of the pivot.
    """
    # Randomize pivot to avoid O(n²) on sorted input.
    pivot_idx = random.randrange(lo, hi + 1)
    nums[pivot_idx], nums[hi] = nums[hi], nums[pivot_idx]
    pivot = nums[hi]

    i = lo - 1  # boundary: everything in nums[lo..i] is <= pivot
    for j in range(lo, hi):
        if nums[j] <= pivot:
            i += 1
            nums[i], nums[j] = nums[j], nums[i]
    # Place pivot in its final position.
    nums[i + 1], nums[hi] = nums[hi], nums[i + 1]
    return i + 1


def _quicksort_helper(nums: List[int], lo: int, hi: int) -> None:
    if lo < hi:
        p = _lomuto_partition(nums, lo, hi)
        _quicksort_helper(nums, lo, p - 1)
        _quicksort_helper(nums, p + 1, hi)


def quicksort(nums: List[int]) -> None:
    """In-place quicksort with Lomuto partition and randomized pivot."""
    if len(nums) > 1:
        _quicksort_helper(nums, 0, len(nums) - 1)


# ── Quickselect (k-th smallest, 1-indexed) ───────────────────────────────────

def quickselect(nums: List[int], k: int) -> int:
    """Return the k-th smallest element (1-indexed) in O(n) average time.

    Mutates nums in place during partitioning.
    """
    lo, hi = 0, len(nums) - 1
    target = k - 1  # convert to 0-indexed rank
    while lo < hi:
        p = _lomuto_partition(nums, lo, hi)
        if p == target:
            return nums[p]
        elif p < target:
            lo = p + 1
        else:
            hi = p - 1
    return nums[lo]


if __name__ == "__main__":
    # mergesort smoke tests
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert mergesort([1]) == [1]
    assert mergesort([]) == []
    assert mergesort([3, 3, 3]) == [3, 3, 3]

    # quicksort smoke tests
    arr = [3, 6, 8, 10, 1, 2, 1]
    quicksort(arr)
    assert arr == [1, 1, 2, 3, 6, 8, 10]

    arr2 = [5, 2, 4, 6, 1, 3]
    quicksort(arr2)
    assert arr2 == [1, 2, 3, 4, 5, 6]

    # quickselect smoke tests
    assert quickselect([3, 6, 8, 10, 1, 2, 1], 1) == 1   # smallest
    assert quickselect([3, 6, 8, 10, 1, 2, 1], 4) == 6   # 4th smallest from [1,1,2,3,6,8,10]
    assert quickselect([3, 6, 8, 10, 1, 2, 1], 7) == 10  # largest

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Lomuto vs Hoare partition

**Lomuto** (used above) scans left-to-right with a single write pointer `i`, then places the pivot at `i+1`. Easier to reason about and implement correctly; slightly more swaps on average. **Hoare** uses two inward-moving pointers and swaps when they find an inversion; fewer swaps in practice but the pivot ends up somewhere in the middle (not necessarily at `p`), so you recurse on `[lo, p]` and `[p+1, hi]` (note: include `p` in the left call). Hoare is subtly more error-prone under interview pressure.

### Randomized pivot

Without randomization, a naive last-element pivot hits O(n²) on already-sorted or reverse-sorted input — the partition produces subarrays of size 0 and n-1 at every level. `random.randrange(lo, hi + 1)` makes this probability negligible. In a real codebase, "median-of-three" (median of first, middle, last elements) is a common deterministic alternative.

### 3-way partition (Dutch National Flag)

When the input has many duplicate keys, standard 2-way Lomuto still runs O(n log n) but the constant is poor (pivots equal to many elements scatter across both sides). The 3-way (Dutch flag) partition maintains three regions: `< pivot`, `== pivot`, `> pivot`. Only the outer two regions need further recursion, so all duplicates are handled in one pass. See LeetCode 75 (Sort Colors) for the canonical implementation.

### Mergesort on a linked list

Mergesort is the natural choice for linked lists: finding the midpoint is O(n) via slow/fast pointers, and merging two sorted linked lists is O(n) with no extra space for values (only pointer rewiring). Array quicksort's random access and cache-line behavior don't translate to linked lists. Python's `list.sort()` uses Timsort (a mergesort variant); for linked list problems use the same recursive halving approach.

### Quickselect for k-th element

To find the k-th smallest element without sorting the whole array, reuse the partition step: after partitioning, if the pivot lands at index `p == k-1` you're done. If `p < k-1` recurse only on the right half; if `p > k-1` recurse only on the left. Expected O(n) time (geometric series 1 + 1/2 + 1/4 + ... = 2). Worst-case O(n²) without randomization. Never confuse quickselect with quicksort — you recurse on only ONE side, not both.

### When each algorithm wins

| Criterion               | Mergesort                            | Quicksort                         |
|-------------------------|--------------------------------------|-----------------------------------|
| Stability               | Stable (equal elements keep order)   | Not stable (Lomuto/Hoare)         |
| Worst-case              | O(n log n) guaranteed                | O(n²) without randomized pivot    |
| Extra space             | O(n) for merge buffers               | O(log n) recursion stack          |
| Cache behavior          | Poor (accesses two separate arrays)  | Good (in-place, sequential access)|
| Linked list             | Natural fit                          | Poor (no random access)           |
| External sort           | Ideal (streaming merge)              | Poor (requires random access)     |
| Average constant factor | Slightly higher                      | Slightly lower                    |

### Pitfalls

- **Sorted-input O(n²)**: Quicksort without a randomized pivot on a sorted array produces n-1 levels of recursion, each with O(n) work. Always randomize or use median-of-three.
- **Off-by-one in Lomuto**: After the scan, the pivot goes to `i + 1`, and recursion is on `[lo, p-1]` and `[p+1, hi]` — not `[lo, p]`. Placing the pivot at `i` instead of `i+1` or including `p` in a recursive call breaks the sort.
- **Quickselect vs quicksort**: Quickselect recurses on ONE side only. Writing both recursive calls (as in quicksort) makes it O(n log n) and defeats the purpose.
- **Mergesort O(n) auxiliary space**: Each merge allocates a new list. For memory-constrained environments, an in-place merge exists but is complex (O(n log² n) or O(n log n) with careful implementation).
- **Stack overflow on large inputs**: The default Python recursion limit is 1 000. For n > ~500 without tail-call optimization, use iterative bottom-up mergesort or increase the limit explicitly (`sys.setrecursionlimit`).

## 6. Complexity

- **Mergesort time:** O(n log n) always — the recursion tree always has ceil(log₂ n) levels, and each level performs O(n) total work in the merge step.
- **Mergesort space:** O(n) — the merge step needs a temporary buffer proportional to the combined size of the two halves; O(log n) additional space for the call stack.
- **Quicksort time:** O(n log n) average, O(n²) worst — with a random pivot, the expected split is close to even; a catastrophically bad pivot at every level gives O(n) levels of O(n) work each.
- **Quicksort space:** O(log n) — only the recursion call stack; no auxiliary array. Worst-case O(n) stack depth without tail-call optimization or iterative fallback.
- **Quickselect time:** O(n) average, O(n²) worst — expected cost is n + n/2 + n/4 + ... = 2n = O(n); pathological pivot choices degrade to O(n²).

## 7. Problem set

- [Easy] [Merge Sorted Array](https://leetcode.com/problems/merge-sorted-array/) — forces you to merge in-place from the back to avoid overwriting values; a clean isolated drill of just the merge step.
- [Medium] [Sort an Array](https://leetcode.com/problems/sort-an-array/) — implement both mergesort and quicksort from scratch; built-in sort is rejected, so there's no shortcut.
- [Medium] [Sort List](https://leetcode.com/problems/sort-list/) — mergesort on a linked list; practice slow/fast pointer midpoint-finding and pointer-rewiring merge instead of array slicing.
- [Medium] [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/) — the canonical quickselect problem; getting O(n) average instead of O(n log n) is the whole point.
- [Medium] [Sort Colors](https://leetcode.com/problems/sort-colors/) — Dutch National Flag 3-way partition; classic warm-up for the 3-pointer technique used in duplicate-heavy quicksort.
- [Hard] [Count of Smaller Numbers After Self](https://leetcode.com/problems/count-of-smaller-numbers-after-self/) — augment mergesort to count cross-half inversions while merging; teaches how to attach bookkeeping to the merge step.
- [Hard] [Reverse Pairs](https://leetcode.com/problems/reverse-pairs/) — same mergesort-with-counting pattern but the counting condition (`nums[i] > 2 * nums[j]`) is asymmetric, which makes the pointer management trickier.

## 8. Related patterns

- **Binary Search** (same folder, `binary-search.md`) — shares the same divide-and-conquer recurrence `T(n) = 2T(n/2) + O(...)`. Mergesort pays O(n) per level (merge cost); binary search pays O(1) per level (single comparison), which is why binary search is O(log n) rather than O(n log n).
- **Heapsort & Heaps** (will live at `heapsort.md` in this same folder) — another O(n log n) in-place sort; O(1) extra space, not stable, but avoids quicksort's O(n²) worst-case without needing randomization. Also the foundation for priority queues.
- **Segment Tree & Fenwick Tree** (will live at `../trees/segment-tree-fenwick.md`) — alternative data structures for inversion-count and range-sum problems; where the hard mergesort problems (315, 493) can also be solved by querying a Fenwick tree during a left-to-right scan instead of augmenting the merge step.

## 9. Interviewer follow-ups

**Q: Pick mergesort or quicksort for this scenario — which and why?**
The answer turns on four axes: (1) **Stability** — if equal elements must preserve their original relative order (e.g., sorting rows by a secondary key that's already sorted by a primary key), mergesort is required; quicksort with Lomuto/Hoare is not stable. (2) **Memory budget** — quicksort is in-place (O(log n) stack); mergesort needs O(n) auxiliary. For large arrays on constrained hardware, quicksort wins. (3) **Worst-case guarantees** — mergesort is O(n log n) always; quicksort's O(n²) worst-case is astronomically unlikely with randomized pivot but is not zero. For safety-critical or adversarial inputs, mergesort is safer. (4) **Data structure** — linked list? Always mergesort (random access for quicksort is O(n) per access). External sort (data larger than RAM)? Always mergesort (streaming merge of sorted chunks). In practice, most standard library sorts (Python's Timsort, Java's Arrays.sort for objects) choose mergesort variants precisely for stability and worst-case guarantees.

**Q: How do you make quicksort stable?**
You don't trivially. The partition step moves elements past each other based solely on their comparison with the pivot, erasing positional information. You can simulate stability by sorting on a `(value, original_index)` tuple, but that adds O(n) space and defeats the in-place appeal of quicksort. If stability is a hard requirement, switch to mergesort (or Timsort). The interview insight is recognizing that stability and in-place-ness are in tension: every known in-place sort that is also comparison-based and O(n log n) either isn't stable in its standard form (heapsort, quicksort) or is very complex to implement correctly (in-place mergesort).

**Q: Sort 1 TB of integers on a 16 GB machine.**
This is external mergesort in three phases. (1) **Chunking:** read 16 GB at a time (leaving room for I/O buffers), sort in memory with any fast sort, write the sorted chunk to disk. 1 TB / 16 GB ≈ 64 sorted runs. (2) **k-way merge:** open all 64 sorted run files simultaneously and do a streaming merge using a min-heap of size 64. Each heap operation is O(log 64) = O(6). Pull the smallest element from the heap, write it to the output stream, push the next element from the same run. Total work: O(n log k) where k=64. (3) **I/O considerations:** use double-buffering (fill one buffer while the other drains) to keep disk and CPU busy concurrently; tune chunk size to match disk block size and available RAM. Memory footprint at merge time: 64 read buffers + 1 write buffer + the 64-element heap — well within 16 GB.
