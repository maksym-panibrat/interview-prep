# Activity Selection (and Huffman name-drop)

## 1. TL;DR

Activity selection asks you to pick the maximum number of non-overlapping activities (or jobs, intervals) from a set. The signal is "select max compatible activities," "maximum non-overlapping subset," or "maximize number of tasks that can be scheduled." Sort by finish time, then sweep: greedily pick each activity whose start time is at or after the last chosen finish time. Correctness is guaranteed by an exchange argument. Time: O(n log n) sort + O(n) sweep. Space: O(n).

## 2. Intuition

Imagine booking as many conference rooms as possible for a single-track event. The key insight: always pick the talk that ends earliest among those you haven't ruled out. Why? Because finishing earlier leaves the most room for future talks — any other choice can only leave you with less time. This is provable via an **exchange argument**: if an optimal solution skips the earliest-finishing compatible activity A in favour of some later-finishing activity B, you can swap B for A. A ends no later than B, so everything scheduled after B still fits after A — the new solution has at least as many activities and is still valid.

Two extensions are worth naming in interviews:

- **Huffman coding** (optimal prefix-free codes): repeatedly merge the two lowest-frequency symbols using a min-heap. Each merge's weight equals the sum of the two children; the total encoding cost is the sum of all merge weights. This is a different greedy problem — frequency-driven, not interval-driven — but it uses the same "pick the two smallest repeatedly" min-heap structure. Time: O(n log n).
- **Fractional knapsack**: sort by value-per-weight density, fill greedily. Greedy is optimal here because you can take fractional units. The **0/1 knapsack** (whole items only) is *not* solvable by greedy — it requires DP.

## 3. Walkthrough

Activities (already sorted by finish time):

```
(1,4) (3,5) (0,6) (5,7) (3,8) (5,9) (6,10) (8,11) (8,12) (2,13) (12,14)
```

Sweep with `last_end = -inf`:

```
(1,4):   start 1  >= -inf → PICK   last_end = 4
(3,5):   start 3  <  4    → skip
(0,6):   start 0  <  4    → skip
(5,7):   start 5  >= 4    → PICK   last_end = 7
(3,8):   start 3  <  7    → skip
(5,9):   start 5  <  7    → skip
(6,10):  start 6  <  7    → skip
(8,11):  start 8  >= 7    → PICK   last_end = 11
(8,12):  start 8  <  11   → skip
(2,13):  start 2  <  11   → skip
(12,14): start 12 >= 11   → PICK   last_end = 14
```

Result: `[(1,4), (5,7), (8,11), (12,14)]` — 4 activities selected.

## 4. Implementation

```python
from __future__ import annotations
import heapq
from typing import List, Tuple


def activity_selection(activities: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Return maximum set of non-overlapping activities.

    Sort by finish time, then greedily pick each activity whose start is
    at or after the last chosen finish (exchange-argument optimal).
    O(n log n).
    """
    sorted_acts = sorted(activities, key=lambda x: x[1])  # sort by finish time
    selected: List[Tuple[int, int]] = []
    last_end = float("-inf")
    for start, end in sorted_acts:
        if start >= last_end:       # compatible: starts at or after last end
            selected.append((start, end))
            last_end = end
    return selected


def huffman_cost(freqs: List[int]) -> int:
    """Total encoding cost of a Huffman tree for the given symbol frequencies.

    Repeatedly pop the two smallest weights from a min-heap, push their sum,
    and accumulate the merge weight.  The sum of all merge weights equals the
    total number of bits used to encode the data.
    O(n log n).
    """
    if len(freqs) <= 1:
        return 0
    heap = list(freqs)
    heapq.heapify(heap)         # O(n) build
    total_cost = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)  # smallest
        b = heapq.heappop(heap)  # second smallest
        merge = a + b
        total_cost += merge      # each internal node contributes its weight
        heapq.heappush(heap, merge)
    return total_cost


if __name__ == "__main__":
    # activity_selection smoke test
    acts = [
        (1, 4), (3, 5), (0, 6), (5, 7), (3, 8),
        (5, 9), (6, 10), (8, 11), (8, 12), (2, 13), (12, 14),
    ]
    result = activity_selection(acts)
    assert result == [(1, 4), (5, 7), (8, 11), (12, 14)], result

    assert activity_selection([]) == []
    assert activity_selection([(0, 1)]) == [(0, 1)]

    # huffman_cost smoke test
    # freqs = [5, 9, 12, 13, 16, 45]
    # merges: 5+9=14, 12+13=25, 14+16=30, 25+30=55, 45+55=100
    # total = 14 + 25 + 30 + 55 + 100 = 224
    cost = huffman_cost([5, 9, 12, 13, 16, 45])
    assert cost == 224, f"expected 224, got {cost}"

    assert huffman_cost([10]) == 0
    assert huffman_cost([3, 3]) == 6

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Activity selection = max non-overlapping intervals

The two problems are identical. "Non-overlapping Intervals" (LC 435) asks for the minimum number of removals; that is `n - activity_selection_count`. Same sort-by-end greedy applies; the only difference is what you return.

### Huffman coding

Build a min-heap of symbol frequencies. Repeatedly extract the two smallest, combine them into a new node whose weight is their sum, and push it back. After `n-1` merges the heap contains one node — the tree root. The total encoding cost (bits × frequency, summed over all symbols) equals the sum of all merge weights. Use this sketch when asked: "how would you construct an optimal prefix-free code?"

### Fractional knapsack

Sort items by value/weight descending. Fill your knapsack greedily: take entire items until you'd exceed capacity, then take a fraction of the next item. Greedy is optimal here because partial units are allowed. **0/1 knapsack** (indivisible items) is *not* greedy-solvable — it requires DP (`dp[cap]` rolling array, O(n · W)).

### Job scheduling with deadlines and penalties

Variant: each job has a deadline and a penalty for missing it; schedule as many jobs as possible before their deadlines to minimize total penalty. Greedy by decreasing penalty: attempt to schedule each job as late as possible before its deadline using a union-find structure. O(n log n).

### Pitfalls

- **Sorting by start instead of end**: the canonical mistake. Max non-overlapping requires sort by *end*; sort by start is for the merge-intervals problem.
- **Off-by-one on endpoints**: `start >= last_end` (touching is allowed) vs `start > last_end` (touching overlaps). Read the problem statement.
- **Applying greedy to 0/1 knapsack**: fractional knapsack is greedy; 0/1 knapsack is DP. Mixing them up is a red flag in interviews.
- **Skipping the exchange-argument justification**: saying "take the earliest-finishing" without being able to explain *why* it's correct signals a gap. Practice the one-sentence proof.

## 6. Complexity

- **Time:** O(n log n) — sorting dominates; the sweep is O(n). Huffman is also O(n log n) for n heap operations of O(log n) each.
- **Space:** O(n) — output list or heap holds at most n entries.

## 7. Problem set

- [Medium] [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) — min removals = n minus max compatible count; validates the sort-by-end greedy.
- [Medium] [Minimum Number of Arrows to Burst Balloons](https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/) — count greedy transitions; arrow advances only when next interval's start exceeds current arrow position.
- [Medium] [Minimum Number of Taps to Open to Water a Garden](https://leetcode.com/problems/minimum-number-of-taps-to-open-to-water-a-garden/) — convert tap radii to intervals then greedy interval cover; combines sorting with the compatible-extension sweep.
- [Medium] [Boats to Save People](https://leetcode.com/problems/boats-to-save-people/) — two-pointer greedy on sorted weights; illustrates that greedy correctness still needs an argument even for simple problems.
- [Medium] [Minimum Cost to Connect Sticks](https://leetcode.com/problems/minimum-cost-to-connect-sticks/) — Huffman-style min-heap merge; practice `huffman_cost` directly.
- [Medium] [Reorganize String](https://leetcode.com/problems/reorganize-string/) — max-heap greedy interleaving of character frequencies; same "pick most frequent" structure as Huffman.
- [Medium] [Task Scheduler](https://leetcode.com/problems/task-scheduler/) — greedy formula or simulation; shows that frequency-based greedy reasoning extends beyond tree building.
- [Hard] [IPO](https://leetcode.com/problems/ipo/) — two-heap greedy; select max-profit unlocked project at each step, replenishing the candidate pool as capital grows.

## 8. Related patterns

- [Interval Scheduling](interval-scheduling.md) — superset topic covering merge, min-rooms, and the same max non-overlapping sort-by-end sweep; activity selection is the focused greedy proof version.
- [Heapsort & Heaps](../searching-sorting/heapsort.md) — Huffman coding uses a min-heap; review `heapq` push/pop and the O(n) heapify to implement `huffman_cost` fluently.
- [2D DP](../dp/2d-dp.md) — 0/1 knapsack is the canonical contrast showing when greedy fails and DP is required; the `knapsack_01` rolling-array template is the direct alternative.

## 9. Interviewer follow-ups

**Q: Prove that the greedy exchange argument works for activity selection.**
Suppose an optimal solution OPT does not include activity A, the earliest-finishing compatible activity. Let B be the first activity OPT does include. Since A finishes no later than B (`end_A <= end_B`), swap B for A in OPT. Every activity in OPT that was compatible after B is still compatible after A (A ends no later). The new solution has the same number of activities as OPT and is still valid, so it is also optimal. Hence including A never loses — the greedy choice is safe.

**Q: Sketch the Huffman algorithm.**
Maintain a min-heap of symbol frequencies. Pop the two smallest values `a` and `b`, push `a + b`, and add `a + b` to a running cost counter. Repeat until one element remains. The final running cost is the total weighted path length — the minimum number of bits needed to encode the data with any prefix-free code. With `n` symbols: O(n) to heapify, O(n log n) for the `n-1` merge steps.
