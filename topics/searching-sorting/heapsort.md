# Heapsort & Heaps

## 1. TL;DR

Reach for a heap whenever you see "k-th largest/smallest," "top k frequent," "merge k sorted things," or "next best item repeatedly." A binary min-heap stores an array and gives O(log n) insertion/extraction with O(1) peek at the minimum; Python's `heapq` module exposes exactly this. In interviews you almost never implement heapsort from scratch — you use `heapq` on a carefully chosen key. Time: O(log n) per push/pop; O(n) heapify; O(n log k) for top-k on n elements. Space: O(k) or O(n).

## 2. Intuition

Picture a complete binary tree where every parent is smaller than its children — that is a min-heap. Because the tree is complete it can be stored perfectly in an array: the node at index `i` has children at `2i+1` and `2i+2`, and parent at `(i-1)//2`. The minimum is always at index 0 (the root); you can read it in O(1).

Two operations maintain the heap property:

- **Sift-up** (used after inserting at the end): compare the new node with its parent; if smaller, swap and continue up. At most O(log n) swaps because tree height is floor(log₂ n).
- **Sift-down** (used after extracting the root): place the last element at the root, then compare with the smaller child; if larger, swap and continue down. Again O(log n).

The key interview insight is the **size-k min-heap trick for top-k largest**: push each element; once the heap exceeds k elements, pop the smallest. After processing all n elements the heap holds the k largest. You never need a full sort — you only pay O(log k) per element instead of O(log n), giving O(n log k) total.

For a **max-heap** in Python, negate values before pushing and negate again on pop. Python's `heapq` has no max-heap mode; negation is the idiomatic workaround.

## 3. Walkthrough

### heappush / heappop on [3, 1, 4, 1, 5, 9]

We push elements one by one onto a min-heap and watch the array representation evolve.

```
Push 3: heap = [3]
Push 1: heap = [3, 1]  → sift-up: 1 < 3, swap → heap = [1, 3]
Push 4: heap = [1, 3, 4]  → 4 > parent 1, no swap. heap = [1, 3, 4]
Push 1: heap = [1, 3, 4, 1]
  → 1 at index 3, parent at index 1 (value 3) → 1 < 3, swap → [1, 1, 4, 3]
  → 1 at index 1, parent at index 0 (value 1) → not <, stop. heap = [1, 1, 4, 3]
Push 5: heap = [1, 1, 4, 3, 5]  → 5 > parent 1, no swap.
Push 9: heap = [1, 1, 4, 3, 5, 9]  → 9 > parent 4, no swap.
```

Final heap array: `[1, 1, 4, 3, 5, 9]`. The invariant: each `heap[i] <= heap[2i+1]` and `heap[i] <= heap[2i+2]`.

Now pop (extract minimum) three times:

```
Pop #1: min=1, place last element 9 at root → [9, 1, 4, 3, 5]
  → sift-down from index 0: children are 1 (idx 1) and 4 (idx 2). min child = 1.
  → 9 > 1, swap → [1, 9, 4, 3, 5]
  → now at index 1: children are 3 (idx 3) and 5 (idx 4). min child = 3.
  → 9 > 3, swap → [1, 3, 4, 9, 5]
  → now at index 3: children would be indices 7, 8 — out of bounds. Stop.
heap = [1, 3, 4, 9, 5], popped value = 1

Pop #2: min=1, last=5 → [5, 3, 4, 9]
  → sift-down from 0: children 3 (idx1), 4 (idx2). min child=3.
  → 5>3, swap → [3, 5, 4, 9]
  → at idx1: children 9 (idx3), out of bounds. min child=9.
  → 5<9, stop.
heap = [3, 5, 4, 9], popped value = 1

Pop #3: min=3, last=9 → [9, 5, 4]
  → sift-down from 0: children 5(idx1), 4(idx2). min child=4.
  → 9>4, swap → [4, 5, 9]
  → at idx2: no children. Stop.
heap = [4, 5, 9], popped value = 3
```

Pops returned: 1, 1, 3 — the three smallest, in sorted order.

### Top-k largest via size-k min-heap: nums = [4, 5, 8, 2], k = 2

We maintain a min-heap of size at most k. Elements that fall below the heap's minimum get evicted immediately; only the k largest survive.

```
Process 4: heap = [4]              (size 1 ≤ 2, no eviction)
Process 5: heap = [4, 5]           (size 2 ≤ 2, no eviction)
Process 8: push 8 → heap = [4, 5, 8]  size 3 > 2
  → pop min (4) → heap = [5, 8]
  → 8 > current minimum 5, so 8 stays. ✓
Process 2: push 2 → heap = [2, 8, 5]  size 3 > 2
  → pop min (2) → heap = [5, 8]
  → 2 was evicted because it's smaller than both 5 and 8. ✓

Final heap = [5, 8] → the 2 largest elements in nums.
```

Reading the heap tells you the k largest, and the heap root (5) is the k-th largest itself.

## 4. Implementation

```python
from __future__ import annotations
import heapq
from typing import List, Optional


def top_k_largest(nums: List[int], k: int) -> List[int]:
    """Return the k largest elements (unsorted) using a min-heap of size k.

    O(n log k) time, O(k) space.
    """
    min_heap: List[int] = []
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)  # evict smallest; keep only k largest
    return min_heap  # elements are not sorted, just the k largest


def kth_largest(nums: List[int], k: int) -> int:
    """Return the k-th largest element. Root of size-k min-heap is the answer."""
    heap = top_k_largest(nums, k)
    return heap[0]  # min of the k largest = k-th largest


# ── Max-heap via negation ─────────────────────────────────────────────────────

def top_k_largest_max_heap(nums: List[int], k: int) -> List[int]:
    """Same result via max-heap (negate, then negate back). Demonstrates pattern."""
    max_heap = [-x for x in nums]
    heapq.heapify(max_heap)  # O(n) — converts arbitrary list into a heap in-place
    result = []
    for _ in range(k):
        result.append(-heapq.heappop(max_heap))
    return result


# ── Merge k sorted lists ──────────────────────────────────────────────────────

class ListNode:
    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def merge_k_sorted(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """Merge k sorted linked lists using a min-heap on (value, list_index, node).

    The list_index breaks ties when values are equal — avoids comparing ListNodes.
    O(n log k) time where n is total nodes across all lists. O(k) heap space.
    """
    dummy = ListNode(0)
    curr = dummy
    heap: List[tuple] = []

    # Seed the heap with the first node of each non-empty list.
    for i, node in enumerate(lists):
        if node is not None:
            heapq.heappush(heap, (node.val, i, node))

    while heap:
        val, i, node = heapq.heappop(heap)
        curr.next = node
        curr = curr.next
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, i, node.next))

    return dummy.next


# ── Two-heap pattern: median of a stream ─────────────────────────────────────

class MedianFinder:
    """Maintain a running median using two heaps.

    lower  — max-heap (negated) of the smaller half.
    upper  — min-heap of the larger half.
    Invariant: len(lower) == len(upper) or len(lower) == len(upper) + 1.
    Median: lower[0] if sizes differ, else average of both tops.
    """

    def __init__(self) -> None:
        self.lower: List[int] = []  # max-heap via negation
        self.upper: List[int] = []  # min-heap

    def add_num(self, num: int) -> None:
        # Step 1: push to lower (max-heap), then move its max to upper.
        heapq.heappush(self.lower, -num)
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        # Step 2: if upper has more elements, rebalance.
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def find_median(self) -> float:
        if len(self.lower) > len(self.upper):
            return float(-self.lower[0])
        return (-self.lower[0] + self.upper[0]) / 2.0


# ── Heapsort from scratch (interview variant) ─────────────────────────────────

def _sift_down(arr: List[int], i: int, n: int) -> None:
    """Sift element at index i down within arr[0..n-1]."""
    while True:
        left = 2 * i + 1
        right = 2 * i + 2
        largest = i
        if left < n and arr[left] > arr[largest]:
            largest = left
        if right < n and arr[right] > arr[largest]:
            largest = right
        if largest == i:
            break
        arr[i], arr[largest] = arr[largest], arr[i]
        i = largest


def heapsort(arr: List[int]) -> None:
    """In-place heapsort. O(n log n) time, O(1) space. Not stable.

    Phase 1: heapify — build a max-heap in O(n) by sifting down from n//2-1 to 0.
    Phase 2: extract — repeatedly swap root (max) with last unsorted, sift down.
    """
    n = len(arr)
    # Build max-heap: start from last non-leaf, sift each down.
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(arr, i, n)
    # Extract elements: shrink the heap boundary by 1 each step.
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]  # max goes to its final position
        _sift_down(arr, 0, end)


if __name__ == "__main__":
    # top_k_largest
    assert sorted(top_k_largest([4, 5, 8, 2], 2)) == [5, 8]
    assert kth_largest([4, 5, 8, 2], 2) == 5
    assert sorted(top_k_largest([3, 1, 4, 1, 5, 9], 3)) == [4, 5, 9]

    # max-heap variant produces same answers
    assert sorted(top_k_largest_max_heap([4, 5, 8, 2], 2)) == [5, 8]

    # heapsort
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    heapsort(arr)
    assert arr == [1, 1, 2, 3, 4, 5, 6, 9]

    # MedianFinder
    mf = MedianFinder()
    mf.add_num(1)
    assert mf.find_median() == 1.0
    mf.add_num(2)
    assert mf.find_median() == 1.5
    mf.add_num(3)
    assert mf.find_median() == 2.0

    # merge_k_sorted: [[1,4,5],[1,3,4],[2,6]] -> 1->1->2->3->4->4->5->6
    def make_list(vals):
        dummy = ListNode(0)
        cur = dummy
        for v in vals:
            cur.next = ListNode(v)
            cur = cur.next
        return dummy.next

    def list_to_arr(node):
        result = []
        while node:
            result.append(node.val)
            node = node.next
        return result

    merged = merge_k_sorted([make_list([1, 4, 5]), make_list([1, 3, 4]), make_list([2, 6])])
    assert list_to_arr(merged) == [1, 1, 2, 3, 4, 4, 5, 6]

    print("All smoke tests passed.")
```

**Template:**

```python
import heapq
from typing import List, Optional


def top_k_largest(nums: List[int], k: int) -> List[int]:
    min_heap: List[int] = []
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    return min_heap


def merge_k_sorted(lists: List[Optional[object]]) -> Optional[object]:
    heap: List[tuple] = []
    for i, node in enumerate(lists):
        if node is not None:
            heapq.heappush(heap, (node.val, i, node))
    dummy = type('N', (), {'val': 0, 'next': None})()
    curr = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        curr.next = node
        curr = curr.next
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next


class MedianFinder:
    def __init__(self) -> None:
        self.lower: List[int] = []
        self.upper: List[int] = []

    def add_num(self, num: int) -> None:
        heapq.heappush(self.lower, -num)
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def find_median(self) -> float:
        if len(self.lower) > len(self.upper):
            return float(-self.lower[0])
        return (-self.lower[0] + self.upper[0]) / 2.0
```

## 5. Variants & pitfalls

### Min-heap vs max-heap

Python's `heapq` is a min-heap only. To simulate a max-heap, negate every value on the way in and negate again on the way out: `heapq.heappush(h, -x)` and `-heapq.heappop(h)`. The `heapq.nlargest(k, iterable)` convenience function does this internally for you when you just need k largest items without maintaining a heap across calls — it is O(n log k) like the manual approach.

### heapify in O(n)

`heapq.heapify(arr)` converts an arbitrary list into a heap in-place in O(n), not O(n log n). The trick: leaves (bottom half) need no work; sift-down each internal node from the bottom up. Because lower levels have more nodes but require fewer sift-down steps, the total work sums to O(n). Use `heapify` when you already have all the data up front rather than pushing one element at a time — it's twice as fast in practice.

### Fixed-size top-k vs full sort

If k is small relative to n, maintain a min-heap of size k: O(n log k) and O(k) space. If k is close to n, just sort: O(n log n). The crossover is roughly when k > n / log n, but in interviews the distinction usually matters only when k is explicitly described as "small."

### Two-heap pattern for running median

Split the stream into a lower half (max-heap, negated) and an upper half (min-heap). Keep them balanced within one element. The median is then the lower half's root (when sizes differ) or the average of both roots. This is the canonical hard-level heap pattern; practice `add_num` until the two-step push (push-to-lower, then push-to-upper) feels automatic.

### Custom comparator via tuple key

`heapq` compares tuples lexicographically. To push elements with a custom priority, push `(priority, tiebreaker, element)`. The `tiebreaker` (e.g., an auto-incrementing counter or list index) prevents Python from falling back to comparing `element` itself, which would raise `TypeError` if `element` is not comparable (e.g., a custom class, a `ListNode`). Always include a tiebreaker when elements may be equal in priority — forgetting this is a common source of `TypeError` in Merge k Sorted Lists.

### Pitfalls

- **Forgetting to negate for max-heap**: pushing raw values into `heapq` and expecting max-heap behavior is wrong; the root is the minimum. The bug is silent — results look plausible until they are wrong.
- **Using a list as a heap without heapify**: `arr = [3, 1, 2]; heapq.heappop(arr)` returns 3, not 1, because the list is not a valid heap. Always call `heapq.heapify(arr)` first if the list was not built via `heappush`.
- **Comparable tiebreaker required**: pushing `(priority, ListNode(...))` crashes when two priorities are equal, because Python then tries `ListNode < ListNode` which raises `TypeError`. Add an integer counter as the middle element of the tuple.

## 6. Complexity

- **Time:** Insertion/extraction O(log n) — sift-up or sift-down traverses at most the tree height, which is floor(log₂ n). `heapify` O(n) — the sift-down work per level sums to O(n) via the geometric series argument. Top-k on n elements O(n log k) — n pushes each costing O(log k) because the heap never grows past k.
- **Space:** O(k) for top-k; O(n) for heapify in-place (no extra space beyond the input); O(k) for the merge-k heap (one node per list at any moment).

## 7. Problem set

- [Easy] [Last Stone Weight](https://leetcode.com/problems/last-stone-weight/) — max-heap to repeatedly extract the two heaviest stones; the simplest demonstration of the "next best item" loop.
- [Easy] [Kth Largest Element in a Stream](https://leetcode.com/problems/kth-largest-element-in-a-stream/) — maintain a min-heap of size k; reading the root is an O(1) k-th largest query at any time.
- [Medium] [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) — count frequencies with a hash map, then top-k on (frequency, element) tuples; forces the tuple-key pattern.
- [Medium] [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) — top-k by Euclidean distance using a max-heap of size k; no need to take the square root — compare squared distances to avoid floating point.
- [Medium] [Task Scheduler](https://leetcode.com/problems/task-scheduler/) — max-heap to always pick the most-frequent remaining task; idle slots emerge naturally from the greedy extraction order.
- [Medium] [Reorganize String](https://leetcode.com/problems/reorganize-string/) — similar greedy max-heap extraction; must alternate characters and detect impossibility when one character dominates.
- [Hard] [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) — canonical merge-k pattern using (val, idx, node) tuples to avoid comparing ListNodes at tie-break.
- [Hard] [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) — two-heap pattern; building it under interview pressure tests muscle memory of the two-step add.
- [Hard] [Sliding Window Median](https://leetcode.com/problems/sliding-window-median/) — two-heap with lazy deletion (track invalid elements and skip them on pop); harder than static median because elements leave the window.

## 8. Related patterns

- **[Quicksort & Mergesort](quicksort-mergesort.md)** — both achieve O(n log n) sorting; heapsort shares the time complexity but is in-place and avoids quicksort's O(n²) worst case. Unlike mergesort it's not stable.
- **Shortest Paths / Dijkstra** — Dijkstra's algorithm uses a min-heap to greedily extract the nearest unvisited node; the heap loop structure is identical to merge-k and top-k patterns. (File at `../graphs/shortest-paths.md` does not exist yet.)
- **Sliding Window** — fixed-size windows sometimes need an efficient running max/min; a heap with lazy deletion or a monotonic deque are the two options. (File at `../two-pointers-sliding-window/sliding-window.md` does not exist yet.)

## 9. Interviewer follow-ups

**Q: Implement a max-heap from scratch.**
Store values in an array. `_sift_up(arr, i)`: while `i > 0` and `arr[i] > arr[(i-1)//2]`, swap with parent and move up. `_sift_down(arr, i, n)`: find the larger child; if larger than `arr[i]`, swap and continue. `heappush` appends then sifts up; `heappop` swaps root with last, shrinks, and sifts down. The `heapsort` implementation in Section 4 shows the full `_sift_down` loop.

**Q: Stream with billions of items, find top 10.**
Maintain a min-heap of size 10. For each incoming item: if the heap has fewer than 10 elements, push it; otherwise if the item is larger than the heap's root (the 10th largest so far), pop the root and push the new item. After the stream ends the heap holds the 10 largest. Memory footprint: 10 elements regardless of stream length.

**Q: Median of a stream.**
Use two heaps: `lower` (max-heap, negated in Python) holds the smaller half; `upper` (min-heap) holds the larger half. For each new number, push to `lower`, then move `lower`'s max to `upper`; if `upper` becomes larger than `lower`, move `upper`'s min back to `lower`. This keeps sizes within one of each other. The median is the top of `lower` (odd total) or average of both tops (even total). See `MedianFinder` in Section 4.
