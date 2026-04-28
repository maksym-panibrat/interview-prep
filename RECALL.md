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

## [DFS](topics/graphs/dfs.md) ★★★

DFS (Depth-First Search) is the workhorse for **connected components**, **cycle detection**, **path enumeration**, and any problem with a natural recursive decomposition on a graph. The signal is "connected components," "find all paths," "detect cycle," "explore everything reachable," or problems where the problem tree mirrors the call stack. Key insight: stack-based exploration goes as deep as possible before backtracking; post-order discovery (finish time) is the reverse of topological order. Time: O(V + E). Space: O(V) for the recursion stack.

```python
import sys
from typing import Dict, List, Optional, Set


def dfs_recursive(graph: Dict[int, List[int]], start: int, visited: Optional[Set[int]] = None) -> List[int]:
    if visited is None:
        visited = set()
    visited.add(start)
    order = [start]
    for nb in graph.get(start, []):
        if nb not in visited:
            order.extend(dfs_recursive(graph, nb, visited))
    return order


def dfs_iterative(graph: Dict[int, List[int]], start: int) -> List[int]:
    visited: Set[int] = set()
    stack = [start]
    order: List[int] = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nb in reversed(graph.get(node, [])):
            if nb not in visited:
                stack.append(nb)
    return order


def has_cycle_directed(graph: Dict[int, List[int]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[int, int] = {}
    for u in graph:
        color[u] = WHITE
        for v in graph[u]:
            if v not in color:
                color[v] = WHITE

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    return any(dfs(n) for n in list(color) if color[n] == WHITE)


def connected_components(graph: Dict[int, List[int]]) -> List[List[int]]:
    visited: Set[int] = set()
    components: List[List[int]] = []
    all_nodes: Set[int] = set(graph.keys())
    for nbs in graph.values():
        all_nodes.update(nbs)
    for node in sorted(all_nodes):
        if node not in visited:
            comp: List[int] = []
            stack = [node]
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                comp.append(u)
                for v in graph.get(u, []):
                    if v not in visited:
                        stack.append(v)
            components.append(sorted(comp))
    return components
```

## [Topological Sort](topics/graphs/topological-sort.md) ★★★

Topological sort orders the nodes of a **DAG** (directed acyclic graph) so that every directed edge `u → v` has `u` appearing before `v`. The signal is "build order," "course prerequisites," "task scheduling with constraints," "compile order," or any problem that requires respecting dependency chains. Two equivalent algorithms: **Kahn's** (BFS-based, peels in-degree-0 nodes level by level) and **DFS-based** (post-order reversed). Kahn's naturally detects cycles; DFS-based is cleaner if you already have DFS set up. Time: O(V + E). Space: O(V).

```python
from collections import deque
from typing import Dict, List, Optional


def kahn(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    in_degree = [0] * n
    for u in range(n):
        for v in graph.get(u, []):
            in_degree[v] += 1
    queue: deque = deque(i for i in range(n) if in_degree[i] == 0)
    result: List[int] = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    return result if len(result) == n else None


def dfs_topo(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n
    result: List[int] = []

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        result.append(u)
        return False

    for i in range(n):
        if color[i] == WHITE:
            if dfs(i):
                return None
    result.reverse()
    return result
```

## [Union-Find](topics/graphs/union-find.md) ★★★

Union-Find (Disjoint Set Union, DSU) answers "are A and B in the same connected component?" and "merge two components" in nearly O(1) amortized time per operation. The signal is **incremental connectivity**: edges arrive one by one and you need to query or track connected components after each addition. Classic applications include Kruskal's MST, "number of connected components after online edge insertions," equivalence classes, and redundant connections. Time: O(α(n)) amortized per operation (inverse Ackermann — effectively constant for any practical n). Space: O(n).

```python
from typing import List


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n
        self.size: List[int] = [1] * n
        self.num_components: int = n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)

    def component_size(self, x: int) -> int:
        return self.size[self.find(x)]
```

## [Shortest Paths (Dijkstra)](topics/graphs/shortest-paths.md) ★★★

Dijkstra's algorithm finds the shortest path from a source to all other nodes in a **weighted graph with non-negative edge weights**. The signal is "shortest path with weights," "minimum cost to traverse," or any weighted-graph distance question where edges are non-negative. A min-heap processes the closest unsettled node first; each node is settled at most once, giving O((V + E) log V) with a binary heap. For negative edges use **Bellman-Ford** (O(VE)); for all-pairs distances on small dense graphs use **Floyd-Warshall** (O(V³)). Space: O(V + E).

```python
import heapq
from typing import Dict, List, Optional, Tuple


def dijkstra(graph: Dict[int, List[Tuple[int, int]]], src: int) -> Dict[int, float]:
    dist: Dict[int, float] = {src: 0.0}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def dijkstra_with_path(
    graph: Dict[int, List[Tuple[int, int]]], src: int, dst: int
) -> Tuple[float, Optional[List[int]]]:
    dist: Dict[int, float] = {src: 0.0}
    prev: Dict[int, Optional[int]] = {src: None}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u == dst:
            break
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if dst not in dist:
        return (float("inf"), None)
    path: List[int] = []
    node: Optional[int] = dst
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return (dist[dst], path)
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

## [1D DP](topics/dp/1d-dp.md) ★★★

1D DP applies when a problem can be broken into subproblems that each depend on a small number of earlier states along a single axis: positions, values, or steps. The signal is "ways to reach state n," "max/min value ending at index i," "decode/parse with overlapping subproblems," or "fewest steps." Define `dp[i]` as the answer for the first `i` elements (or state at position `i`); each cell is a function of O(1) earlier cells. Time: O(n). Space: O(n), often reducible to O(1).

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

## [2D DP](topics/dp/2d-dp.md) ★★★

2D DP applies when the problem involves two strings, two arrays, or a grid, and the answer for a pair of prefixes (or a grid cell) can be built from three neighboring subproblems. The signal is "edit distance," "LCS," "knapsack," "unique paths," or "interleaving." Define `dp[i][j]` as the answer for the first `i` elements of one input and first `j` of the other (or position `(i,j)` in a grid); transitions look at `(i-1,j)`, `(i,j-1)`, and `(i-1,j-1)`. Time: O(n·m). Space: O(n·m), often reducible to O(min(n,m)).

```python
from typing import List


def edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[m]


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for cap in range(capacity, w - 1, -1):  # descending → 0/1 (each item once)
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[capacity]
```

## [Interval DP](topics/dp/interval-dp.md) ★★★

Interval DP applies when the problem asks you to optimally combine or partition a contiguous sequence — "merge piles," "burst balloons in best order," "matrix chain multiplication," "minimum cost to triangulate." The signal is that the cost of operating on a range `[i..j]` depends on how you split or order actions within it. Define `dp[i][j]` as the optimal answer for the subarray `[i..j]`; iterate over increasing interval lengths so all shorter subproblems are ready when you need them. Time: O(n³). Space: O(n²).

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

## [Tree DP](topics/dp/tree-dp.md) ★★★

Tree DP applies when the answer at each node depends on its children's answers — "max path through a tree," "minimum cameras to cover all nodes," "rob a tree of houses." The signal is that the problem is defined on a tree and optimal choices interact through parent-child relationships. Post-order DFS naturally computes all children before the parent; each node returns a small state tuple summarizing its subtree. Time: O(n). Space: O(n) (recursion stack).

```python
from typing import Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def tree_dp(root: Optional[TreeNode]):
    def dfs(node: Optional[TreeNode]) -> Tuple:
        if node is None:
            return (0, 0)                    # base case — adjust tuple size as needed

        left_state = dfs(node.left)
        right_state = dfs(node.right)

        # Combine left_state, right_state, and node.val into this node's state
        state_a = node.val + left_state[1] + right_state[1]   # "take" branch
        state_b = max(left_state) + max(right_state)           # "skip" branch

        return (state_a, state_b)

    result = dfs(root)
    return max(result)
```

## [Bitmask DP](topics/dp/bitmask-dp.md) ★★★

Bitmask DP applies when N is small (≤ ~20) and you need to track which subset of N elements has been processed. The signal is "visit all cities/jobs/nodes," TSP-like constraints, or "cover all requirements with a subset." Encode the processed subset as an integer bitmask; `dp[mask]` (or `dp[mask][i]`) gives the optimal answer when exactly the elements in `mask` have been used. Time: O(2^N · N). Space: O(2^N · N).

```python
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

## [KMP](topics/strings/kmp.md) ★★

KMP (Knuth-Morris-Pratt) finds all occurrences of a pattern of length m inside a text of length n in O(n + m) time. The signal is "find pattern in text," substring search where naïve O(nm) is too slow, or any problem that involves the **longest proper prefix that is also a suffix** (LPS) of a string. Key idea: precompute an LPS array for the pattern so that on a mismatch you know how far back in the pattern to jump — without ever rewinding the text pointer. Time: O(n + m). Space: O(m).

```python
from typing import List


def compute_lps(pattern: str) -> List[int]:
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> List[int]:
    if not pattern:
        return list(range(len(text) + 1))
    n, m = len(text), len(pattern)
    lps = compute_lps(pattern)
    results: List[int] = []
    i = j = 0
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            results.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return results
```

## [Rabin-Karp](topics/strings/rabin-karp.md) ★★

Rabin-Karp finds a pattern of length m in a text of length n by treating each window as a polynomial hash and sliding it in O(1) per step. The signal is "find substring or k-length window with hash equality," plagiarism / repeated-substring detection, or any rolling-hash sliding window over a string. Average time is O(n + m); naïve verification on every hash hit gives O(nm) worst case with adversarial collisions. Space: O(1) beyond the input.

```python
from typing import List

BASE = 257
MOD = 10**9 + 7


def rabin_karp(text: str, pattern: str) -> List[int]:
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    high_base = pow(BASE, m - 1, MOD)
    pat_hash = win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * BASE + ord(pattern[i])) % MOD
        win_hash = (win_hash * BASE + ord(text[i])) % MOD
    results: List[int] = []
    for l in range(n - m + 1):
        if win_hash == pat_hash and text[l:l + m] == pattern:
            results.append(l)
        if l + m < n:
            win_hash = (win_hash - ord(text[l]) * high_base) % MOD
            win_hash = (win_hash * BASE + ord(text[l + m])) % MOD
            win_hash %= MOD
    return results
```

## [Trie](topics/strings/trie.md) ★★

A trie (prefix tree) is a tree where each root-to-node path spells out a prefix and each node holds children plus an end-of-word marker. The signal is **prefix matching**, autocomplete, "word search II," dictionary lookups with wildcards, multi-pattern search, or longest-common-prefix queries. Every `insert`, `search`, and `startsWith` is O(L) where L is the word length — independent of how many words are stored. Space: O(N · L) worst case.

```python
from typing import Dict


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
```

## [Tree Traversals](topics/trees/traversals.md) ★★

Tree traversal applies whenever you need to visit every node in a binary tree: serialize/deserialize, convert a tree to a list, or check a structural property. The signal is "binary-tree shaped," "visit all nodes," or "process in some order." Four canonical orders exist — pre-, in-, post-, and level-order — each with a recursive one-liner and a tractable iterative counterpart. Time: O(n). Space: O(h) where h is tree height (O(log n) balanced, O(n) worst-case).

```python
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def preorder(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    result, stack = [], [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result


def inorder(root: Optional[TreeNode]) -> List[int]:
    result, stack, curr = [], [], root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result


def postorder(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    stack1, stack2 = [root], []
    while stack1:
        node = stack1.pop()
        stack2.append(node)
        if node.left:
            stack1.append(node.left)
        if node.right:
            stack1.append(node.right)
    return [n.val for n in reversed(stack2)]


def level_order(root: Optional[TreeNode]) -> List[int]:
    if root is None:
        return []
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result
```

## [Binary Search Tree](topics/trees/bst.md) ★★

A Binary Search Tree (BST) is a binary tree where every node satisfies the **BST invariant**: all values in the left subtree are strictly less than the node's value, and all values in the right subtree are strictly greater. The signal is "binary search tree," "k-th smallest in a tree," "insert/delete/validate a sorted-property tree," or any query that exploits sorted order on a tree. Inorder traversal of a BST yields a sorted sequence. Search, insert, and delete are all O(h) where h = O(log n) for a balanced tree and O(n) for a skewed one. Space: O(h) for recursion stack.

```python
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def validate_bst(root: Optional[TreeNode]) -> bool:
    def _check(node, lo, hi):
        if node is None:
            return True
        if not (lo < node.val < hi):
            return False
        return _check(node.left, lo, node.val) and _check(node.right, node.val, hi)
    return _check(root, float("-inf"), float("inf"))


def insert_bst(root: Optional[TreeNode], val: int) -> TreeNode:
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert_bst(root.left, val)
    elif val > root.val:
        root.right = insert_bst(root.right, val)
    return root


def delete_bst(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    if root is None:
        return None
    if val < root.val:
        root.left = delete_bst(root.left, val)
    elif val > root.val:
        root.right = delete_bst(root.right, val)
    else:
        if root.left is None:
            return root.right
        if root.right is None:
            return root.left
        successor = root.right
        while successor.left:
            successor = successor.left
        root.val = successor.val
        root.right = delete_bst(root.right, successor.val)
    return root


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    stack, curr, count = [], root, 0
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        count += 1
        if count == k:
            return curr.val
        curr = curr.right
    raise ValueError(f"k exceeds node count")
```

## [Lowest Common Ancestor](topics/trees/lca.md) ★★

LCA (Lowest Common Ancestor) finds the deepest node that is an ancestor of both target nodes in a tree. The signal is "lowest common ancestor of two nodes," "distance between two nodes in a tree," or "shortest path between two nodes in an undirected tree." Recursive post-order DFS is the workhorse: return the current node if it matches either target; otherwise combine results from left and right subtrees — if both sides return non-null, the current node is the LCA. Time: O(n) per query. Space: O(h) recursion stack.

```python
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def lca(root: Optional[TreeNode],
        p: TreeNode,
        q: TreeNode) -> Optional[TreeNode]:
    if root is None:
        return None
    if root is p or root is q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left is not None and right is not None:
        return root
    return left if left is not None else right


def lca_bst(root: Optional[TreeNode],
            p: TreeNode,
            q: TreeNode) -> Optional[TreeNode]:
    node = root
    while node is not None:
        if p.val < node.val and q.val < node.val:
            node = node.left
        elif p.val > node.val and q.val > node.val:
            node = node.right
        else:
            return node
    return None
```

## [Segment Tree & Fenwick](topics/trees/segment-tree-fenwick.md) ★★

Reach for these structures when a problem asks for **range queries with point updates** (or range updates with point queries): "sum/min/max over [l, r]" combined with mutations. The signal is "mutable prefix sum," "counting inversions," or "sum/min/max over a changing array." Fenwick (Binary Indexed Tree, BIT) is the compact O(log n) choice for prefix-sum, count, or XOR workloads; segment tree is the general-purpose choice supporting any associative merge operation plus lazy propagation for range updates. Both build in O(n) and answer queries in O(log n).

```python
class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def update(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, i):
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def range_sum(self, l, r):
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


class SegmentTree:
    def __init__(self, data):
        self.n = len(data)
        self.tree = [0] * (4 * self.n)
        if self.n:
            self._build(1, 0, self.n - 1, data)

    def _build(self, node, node_l, node_r, data):
        if node_l == node_r:
            self.tree[node] = data[node_l]
            return
        mid = (node_l + node_r) // 2
        self._build(2 * node, node_l, mid, data)
        self._build(2 * node + 1, mid + 1, node_r, data)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def update(self, i, val):
        self._update(1, 0, self.n - 1, i, val)

    def _update(self, node, node_l, node_r, i, val):
        if node_l == node_r:
            self.tree[node] = val
            return
        mid = (node_l + node_r) // 2
        if i <= mid:
            self._update(2 * node, node_l, mid, i, val)
        else:
            self._update(2 * node + 1, mid + 1, node_r, i, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query(self, l, r):
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, node, node_l, node_r, l, r):
        if r < node_l or node_r < l:
            return 0
        if l <= node_l and node_r <= r:
            return self.tree[node]
        mid = (node_l + node_r) // 2
        return (self._query(2 * node, node_l, mid, l, r) +
                self._query(2 * node + 1, mid + 1, node_r, l, r))
```

## [Interval Scheduling](topics/greedy/interval-scheduling.md) ★★

Interval scheduling problems place intervals on a number line and ask you to merge overlapping ones, find the minimum number of non-overlapping groups (rooms/machines), or select the maximum non-overlapping subset. The signal is "merge / insert / count overlaps," "minimum rooms," or "max non-overlapping." Sort by the right endpoint for maximum non-overlapping selection; sort by start for merge/insert; use an event sweep (+1 on start, -1 on end) for minimum rooms. Time: O(n log n) sort + O(n) sweep.

```python
from typing import List


def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    result = [intervals[0][:]]
    for start, end in intervals[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def min_rooms(intervals: List[List[int]]) -> int:
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], x[1]))
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def max_non_overlapping(intervals: List[List[int]]) -> int:
    sorted_ivs = sorted(intervals, key=lambda x: x[1])
    count = 0
    last_end = float("-inf")
    for start, end in sorted_ivs:
        if start >= last_end:
            count += 1
            last_end = end
    return count
```

## [Activity Selection (and Huffman name-drop)](topics/greedy/activity-selection.md) ★★

Activity selection asks you to pick the maximum number of non-overlapping activities (or jobs, intervals) from a set. The signal is "select max compatible activities," "maximum non-overlapping subset," or "maximize number of tasks that can be scheduled." Sort by finish time, then sweep: greedily pick each activity whose start time is at or after the last chosen finish time. Correctness is guaranteed by an exchange argument. Time: O(n log n) sort + O(n) sweep. Space: O(n).

```python
import heapq
from typing import List, Tuple


def activity_selection(activities: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    sorted_acts = sorted(activities, key=lambda x: x[1])
    selected: List[Tuple[int, int]] = []
    last_end = float("-inf")
    for start, end in sorted_acts:
        if start >= last_end:
            selected.append((start, end))
            last_end = end
    return selected


def huffman_cost(freqs: List[int]) -> int:
    if len(freqs) <= 1:
        return 0
    heap = list(freqs)
    heapq.heapify(heap)
    total_cost = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        merge = a + b
        total_cost += merge
        heapq.heappush(heap, merge)
    return total_cost
```

## [Backtracking Template](topics/backtracking/backtracking-template.md) ★★

Backtracking applies when a problem asks you to **enumerate all valid configurations** — subsets, permutations, combinations, or constrained arrangements — by building solutions element by element and pruning branches the moment a partial solution cannot extend to a valid one. Signals: "all permutations / combinations / subsets," "find all valid configurations," small input (n ≤ ~20) where exponential exploration is acceptable. Time: O(2^n · n) for subsets, O(n!) for permutations, O(C(n,k) · k) for combinations.

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

## [N-Queens & Sudoku](topics/backtracking/n-queens-sudoku.md) ★★

N-Queens and Sudoku Solver are constraint-satisfaction problems solved with the same backtracking template as subsets and permutations: build the solution row-by-row (or empty-cell-by-empty-cell), enumerate only candidates that don't conflict with the current partial state, place, recurse, and undo. The signal is "place queens such that no two attack each other," "fill the Sudoku board," or any combinatorial search with explicit row/column/diagonal/region conflict constraints. Time: O(N!) for N-Queens (heavily pruned in practice); Sudoku is NP-hard in theory but runs instantly for 9×9. Space: O(N) recursion depth plus conflict sets.

```python
from typing import List


def solve_n_queens(n: int) -> List[List[str]]:
    results: List[List[str]] = []
    placement: List[int] = []
    cols: set[int] = set()
    pos_diag: set[int] = set()
    neg_diag: set[int] = set()

    def backtrack(row: int) -> None:
        if row == n:
            results.append(["." * c + "Q" + "." * (n - c - 1) for c in placement])
            return
        for col in range(n):
            if col in cols or (row + col) in pos_diag or (row - col) in neg_diag:
                continue
            cols.add(col); pos_diag.add(row + col); neg_diag.add(row - col)
            placement.append(col)
            backtrack(row + 1)
            cols.remove(col); pos_diag.remove(row + col); neg_diag.remove(row - col)
            placement.pop()

    backtrack(0)
    return results


def solve_sudoku(board: List[List[str]]) -> None:
    rows: List[set[str]] = [set() for _ in range(9)]
    cols: List[set[str]] = [set() for _ in range(9)]
    boxes: List[set[str]] = [set() for _ in range(9)]
    empty: List[tuple[int, int]] = []

    for r in range(9):
        for c in range(9):
            d = board[r][c]
            if d != ".":
                box_id = (r // 3) * 3 + (c // 3)
                rows[r].add(d); cols[c].add(d); boxes[box_id].add(d)
            else:
                empty.append((r, c))

    def backtrack(idx: int) -> bool:
        if idx == len(empty):
            return True
        r, c = empty[idx]
        box_id = (r // 3) * 3 + (c // 3)
        for d in "123456789":
            if d in rows[r] or d in cols[c] or d in boxes[box_id]:
                continue
            board[r][c] = d
            rows[r].add(d); cols[c].add(d); boxes[box_id].add(d)
            if backtrack(idx + 1):
                return True
            board[r][c] = "."
            rows[r].remove(d); cols[c].remove(d); boxes[box_id].remove(d)
        return False

    backtrack(0)
```

## [Grid Backtracking](topics/backtracking/grid-search.md) ★★

Grid backtracking applies to "find word in grid," "paths with constraints," "visit all cells." Key move: **mutate-restore** — overwrite `board[r][c]='#'` before recursing, restore after. Same skeleton as Backtracking Template; the grid is the implicit decision tree. For many words: trie + DFS (Word Search II), remove trie leaves on match to prune. For shortest path: BFS + separate visited set, not mutate-restore.

```python
from typing import List


def word_search(board: List[List[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        tmp, board[r][c] = board[r][c], "#"
        found = (
            dfs(r + 1, c, idx + 1) or dfs(r - 1, c, idx + 1)
            or dfs(r, c + 1, idx + 1) or dfs(r, c - 1, idx + 1)
        )
        board[r][c] = tmp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


class _TrieNode:
    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: dict = {}
        self.word = None


def word_search_ii(board: List[List[str]], words: List[str]) -> List[str]:
    root = _TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        node.word = w

    rows, cols = len(board), len(board[0])
    found: List[str] = []

    def dfs(r: int, c: int, node: _TrieNode) -> None:
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        ch = board[r][c]
        if ch == "#" or ch not in node.children:
            return
        child = node.children[ch]
        if child.word is not None:
            found.append(child.word)
            child.word = None
        board[r][c] = "#"
        dfs(r + 1, c, child)
        dfs(r - 1, c, child)
        dfs(r, c + 1, child)
        dfs(r, c - 1, child)
        board[r][c] = ch
        if not child.children and child.word is None:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)
    return found
```

## [GCD](topics/math/gcd.md) ★★

GCD (Greatest Common Divisor) computes the largest integer that divides both `a` and `b` using the Euclidean recurrence `gcd(a, b) = gcd(b, a mod b)`. The signal is "common factor," "fraction in lowest terms," "LCM," "lattice problems on integers," or "modular inverse via extended Euclidean." Extended Euclidean additionally returns Bézout coefficients `x, y` satisfying `a*x + b*y = gcd(a, b)` — the basis for modular inverses. Time: O(log(min(a, b))). Space: O(1) iterative.

```python
from functools import reduce
from typing import Optional


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a) // gcd(a, b) * abs(b)


def extgcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extgcd(b, a % b)
    q = a // b
    return g, y1, x1 - q * y1


def modinv(a: int, m: int) -> Optional[int]:
    g, x, _ = extgcd(a % m, m)
    if g != 1:
        return None
    return x % m
```

## [Sieve of Eratosthenes](topics/math/sieve.md) ★★

Sieve of Eratosthenes: mark composites by walking multiples of each prime p starting at p². Total work ≈ O(N log log N). SPF table gives O(log n) factorization: `spf[i]` = smallest prime dividing `i`; divide by `spf[n]` repeatedly. Signal: "primes up to N," "count primes," batch factorizations. Pitfalls: array must be length N+1; start inner loop at p², not 2p; for single huge numbers use Miller-Rabin instead.

```python
import math


def sieve(n: int) -> list[int]:
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, math.isqrt(n) + 1):
        if is_prime[p]:
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
    return [i for i, flag in enumerate(is_prime) if flag]


def smallest_prime_factor(n: int) -> list[int]:
    if n < 2:
        return [0] * (n + 1)
    spf = list(range(n + 1))
    spf[0] = spf[1] = 0
    for p in range(2, math.isqrt(n) + 1):
        if spf[p] == p:
            for multiple in range(p * p, n + 1, p):
                if spf[multiple] == multiple:
                    spf[multiple] = p
    return spf


def factorize(n: int, spf: list[int]) -> dict[int, int]:
    factors: dict[int, int] = {}
    while n > 1:
        p = spf[n]
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    return factors
```

## [Fast Exponentiation](topics/math/fast-exponentiation.md) ★★

Fast exponentiation computes `x^n` in O(log n) multiplications by bit-decomposing n and accumulating: square `x` at each bit position; multiply into the result when the bit is set. Signal: `pow(x, n)` for huge n; "x^n mod m"; linear-recurrence speedup via matrix exponentiation (Fibonacci in O(log n)). Pitfalls: take modulus after every multiply (not just at the end); copy input matrix before mutating; `M^0 = I` (identity, not zero matrix).

```python
from typing import Optional


def pow_int(x: int, n: int) -> int:
    result, cur = 1, x
    while n:
        if n & 1:
            result *= cur
        cur *= cur
        n >>= 1
    return result


def pow_mod(x: int, n: int, mod: int) -> int:
    result, cur = 1 % mod, x % mod
    while n:
        if n & 1:
            result = result * cur % mod
        cur = cur * cur % mod
        n >>= 1
    return result


def mat_mult(A, B, mod=None):
    k = len(A)
    C = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            s = sum(A[i][t] * B[t][j] for t in range(k))
            C[i][j] = s % mod if mod is not None else s
    return C


def mat_pow(M, n, mod=None):
    k = len(M)
    result = [[int(i == j) for j in range(k)] for i in range(k)]
    cur = [row[:] for row in M]
    while n:
        if n & 1:
            result = mat_mult(result, cur, mod)
        cur = mat_mult(cur, cur, mod)
        n >>= 1
    return result
```

## [A* Search](topics/nice-to-have/a-star.md) ★

A* finds shortest paths in large state spaces where Dijkstra is too slow but a good heuristic exists. Signal: grid pathfinding, sliding puzzles, or any weighted shortest-path problem where you can cheaply estimate remaining cost. Key idea: Dijkstra prioritizes nodes by `g(n)` (cost so far); A* prioritizes by `f(n) = g(n) + h(n)` where `h(n)` is an **admissible** heuristic (never overestimates). With a **consistent** heuristic A* is provably optimal and expands far fewer nodes than Dijkstra. Time: O((V + E) log V) worst case; O(d) with a perfect heuristic. Space: O(V).

```python
import heapq
from typing import Callable, Hashable, Iterable, Optional, TypeVar

S = TypeVar("S")


def astar(
    start: S,
    goal: S,
    neighbors: Callable[[S], Iterable[tuple[S, float]]],
    heuristic: Callable[[S], float],
) -> Optional[list[S]]:
    g: dict[S, float] = {start: 0.0}
    prev: dict[S, Optional[S]] = {start: None}
    counter = 0
    heap: list[tuple[float, int, S]] = [(heuristic(start), 0, start)]  # type: ignore[type-var]
    while heap:
        f, _, state = heapq.heappop(heap)
        if state == goal:
            path: list[S] = []
            node: Optional[S] = goal
            while node is not None:
                path.append(node)
                node = prev[node]
            path.reverse()
            return path
        g_state = g.get(state, float("inf"))
        if f - heuristic(state) > g_state + 1e-9:
            continue
        for nb, cost in neighbors(state):
            ng = g_state + cost
            if ng < g.get(nb, float("inf")):
                g[nb] = ng
                prev[nb] = state
                counter += 1
                heapq.heappush(heap, (ng + heuristic(nb), counter, nb))
    return None
```

## [Minimum Spanning Tree](topics/nice-to-have/mst.md) ★

A Minimum Spanning Tree (MST) connects all nodes in a weighted undirected graph with the minimum total edge weight, using exactly V−1 edges. Signal: "minimum cost to connect all nodes," "connect all cities with minimum cable," or any problem that asks you to wire up a network cheaply. Two classic algorithms: **Kruskal** (sort edges, union-find) and **Prim** (grow from a root with a min-heap). Kruskal: O(E log E). Prim with heap: O((V + E) log V).

```python
import heapq
from typing import List, Tuple


def kruskal(n: int, edges: List[Tuple[int, int, int]]) -> Tuple[int, List]:
    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> bool:
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    total_cost = 0
    mst_edges: List[Tuple[int, int, int]] = []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if union(u, v):
            total_cost += w
            mst_edges.append((u, v, w))
            if len(mst_edges) == n - 1:
                break
    return total_cost, mst_edges


def prim(n: int, adj: List[List[Tuple[int, int]]]) -> int:
    in_tree = [False] * n
    heap: List[Tuple[int, int]] = [(0, 0)]
    total_cost = 0
    while heap:
        cost, u = heapq.heappop(heap)
        if in_tree[u]:
            continue
        in_tree[u] = True
        total_cost += cost
        for v, w in adj[u]:
            if not in_tree[v]:
                heapq.heappush(heap, (w, v))
    return total_cost
```

## [Max Flow / Min Cut](topics/nice-to-have/max-flow.md) ★

Max Flow finds the maximum amount of flow that can be sent from a **source** to a **sink** in a capacity-constrained network. The signal is "maximum bipartite matching," "maximum throughput in a network," or any min-cut equivalence problem. Key theorem: **max flow = min cut** (Ford-Fulkerson duality). Edmonds-Karp (BFS-based): O(VE²). Dinic's: O(V²E); O(E√V) for unit-capacity bipartite.

```python
from collections import deque
from typing import List, Optional


class FlowNetwork:
    def __init__(self, n: int) -> None:
        self.n = n
        self.graph: List[List[List[int]]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: int) -> None:
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

    def bfs_augmenting_path(self, s: int, t: int) -> Optional[List[int]]:
        parent = [-1] * self.n
        parent[s] = s
        queue: deque[int] = deque([s])
        while queue:
            u = queue.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and parent[v] == -1:
                    parent[v] = u
                    if v == t:
                        return parent
                    queue.append(v)
        return None

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        while True:
            parent = self.bfs_augmenting_path(s, t)
            if parent is None:
                break
            path_flow = float("inf")
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        path_flow = min(path_flow, edge[1])
                        break
                v = u
            v = t
            while v != s:
                u = parent[v]
                for edge in self.graph[u]:
                    if edge[0] == v and edge[1] > 0:
                        edge[1] -= path_flow
                        self.graph[v][edge[2]][1] += path_flow
                        break
                v = u
            flow += path_flow
        return flow
```
