# Recall Cards

The "30 minutes before the interview" file. Each section is a single topic's TL;DR plus its Template code block, copied verbatim from the full topic file. Sections appear in study order.

For full explanations, walkthroughs, and problem sets, follow the link on each topic heading.

<!-- card sections appended by per-topic tasks -->

## [BFS](topics/graphs/bfs.md) ★★★

BFS (Breadth-First Search) is the go-to algorithm for **shortest path in an unweighted graph**, level-order traversal, and "minimum steps to reach a state" problems. The signal is "shortest path," "minimum steps/moves," "level-order," grid problems where each cell-to-cell move costs 1, or state-space problems like word ladder and open-the-lock. Key property: FIFO queue ensures the first time you reach a node, you've taken the fewest edges. Time: O(V + E). Space: O(V).

```python
from collections import deque
from typing import Dict, List, Set, Tuple


def bfs_shortest_path(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    visited: Set[int] = {src}
    queue: deque = deque([(src, 0)])
    while queue:
        node, dist = queue.popleft()
        for nb in graph.get(node, []):
            if nb == dst:
                return dist + 1
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, dist + 1))
    return -1


def bfs_grid(grid: List[List[int]], sources: List[Tuple[int, int]]) -> List[List[int]]:
    rows, cols = len(grid), len(grid[0])
    dist = [[float("inf")] * cols for _ in range(rows)]
    queue: deque = deque()
    for r, c in sources:
        dist[r][c] = 0
        queue.append((r, c))
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == float("inf"):
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return [[int(d) if d != float("inf") else -1 for d in row] for row in dist]


def bidirectional_bfs(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    front, back = {src}, {dst}
    vf, vb = {src: 0}, {dst: 0}
    d = 0
    while front and back:
        d += 1
        if len(front) > len(back):
            front, back, vf, vb = back, front, vb, vf
        nxt: Set[int] = set()
        for node in front:
            for nb in graph.get(node, []):
                if nb in vb:
                    return d + vb[nb]
                if nb not in vf:
                    vf[nb] = d
                    nxt.add(nb)
        front = nxt
    return -1
```

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

## [Heapsort & Heaps](topics/searching-sorting/heapsort.md) ★★★

Reach for a heap whenever you see "k-th largest/smallest," "top k frequent," "merge k sorted things," or "next best item repeatedly." A binary min-heap stores an array and gives O(log n) insertion/extraction with O(1) peek at the minimum; Python's `heapq` module exposes exactly this. In interviews you almost never implement heapsort from scratch — you use `heapq` on a carefully chosen key. Time: O(log n) per push/pop; O(n) heapify; O(n log k) for top-k on n elements. Space: O(k) or O(n).

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

## [Two Pointers](topics/two-pointers-sliding-window/two-pointers.md) ★★★

Two pointers works on sorted (or sortable) arrays where you need pairs or triplets summing to a target, "largest area" problems, or in-place compaction without extra space. Maintain two indices that move toward each other (or one fast, one slow in the same direction); each step eliminates at least one candidate, giving O(n) after sorting. The signal is "sorted input," "pair/triplet sum," "in-place removal," or "without extra space." Time: O(n) on a sorted array; O(n log n) when sorting first dominates. Space: O(1) extra.

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

## [Fast/Slow Pointers](topics/two-pointers-sliding-window/fast-slow-pointers.md) ★★★

Fast/slow pointers (Floyd's tortoise and hare) detect cycles in linked lists and functional sequences in O(n) time and O(1) space. The signal is "linked-list cycle," "find middle of linked list," "k-th from end," "palindrome linked list," or "find duplicate in array treated as a graph." Move `slow` by one step and `fast` by two; if they ever meet, a cycle exists. A second phase — resetting `slow` to head and stepping both by one — locates the cycle's entry point exactly. Time: O(n). Space: O(1).

```python
from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def has_cycle(head: Optional[ListNode]) -> bool:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
        if slow is fast:
            return True
    return False


def detect_cycle(head: Optional[ListNode]) -> Optional[ListNode]:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None
    slow = head
    while slow is not fast:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next          # type: ignore[union-attr]
    return slow


def find_middle(head: Optional[ListNode]) -> Optional[ListNode]:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
    return slow


def find_duplicate(nums: list) -> int:
    slow = fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow
```

## [Sliding Window](topics/two-pointers-sliding-window/sliding-window.md) ★★★

The sliding window pattern applies whenever you need the longest or shortest subarray/substring satisfying a property, or the maximum/minimum aggregate of a fixed-size window. Maintain indices `[l, r]`: advance `r` to expand; while a constraint is violated, advance `l` to contract. Because each pointer moves at most n times, the total work is O(n). The signal is "longest/shortest substring/subarray with property X," "max sum of size-k window," or "minimum window containing X." Time: O(n). Space: O(k) or O(charset).

```python
from collections import defaultdict, deque
from typing import List


def longest_substring_no_repeat(s: str) -> int:
    last_seen: dict = {}
    l = 0
    max_len = 0
    for r, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= l:
            l = last_seen[ch] + 1
        last_seen[ch] = r
        max_len = max(max_len, r - l + 1)
    return max_len


def min_window(s: str, t: str) -> str:
    if not s or not t:
        return ""
    need: dict = defaultdict(int)
    for ch in t:
        need[ch] += 1
    required = len(need)
    have = 0
    window_counts: dict = defaultdict(int)
    l = 0
    best = (float("inf"), 0, 0)
    for r, ch in enumerate(s):
        window_counts[ch] += 1
        if ch in need and window_counts[ch] == need[ch]:
            have += 1
        while have == required:
            window_len = r - l + 1
            if window_len < best[0]:
                best = (window_len, l, r)
            left_ch = s[l]
            window_counts[left_ch] -= 1
            if left_ch in need and window_counts[left_ch] < need[left_ch]:
                have -= 1
            l += 1
    return s[best[1]: best[2] + 1] if best[0] != float("inf") else ""


def max_sum_fixed_window(nums: List[int], k: int) -> int:
    if len(nums) < k:
        return 0
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for r in range(k, len(nums)):
        window_sum += nums[r] - nums[r - k]
        max_sum = max(max_sum, window_sum)
    return max_sum


def monotonic_deque_max(nums: List[int], k: int) -> List[int]:
    dq: deque = deque()
    result: List[int] = []
    for r in range(len(nums)):
        while dq and dq[0] < r - k + 1:
            dq.popleft()
        while dq and nums[dq[-1]] <= nums[r]:
            dq.pop()
        dq.append(r)
        if r >= k - 1:
            result.append(nums[dq[0]])
    return result
```
