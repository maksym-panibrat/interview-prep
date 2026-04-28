# Interval Scheduling

## 1. TL;DR

Interval scheduling problems place intervals on a number line and ask you to merge overlapping ones, find the minimum number of non-overlapping groups (rooms/machines), or select the maximum non-overlapping subset. The signal is "merge / insert / count overlaps," "minimum rooms," or "max non-overlapping." Sort by the right endpoint for maximum non-overlapping selection; sort by start for merge/insert; use an event sweep (+1 on start, -1 on end) for minimum rooms. Time: O(n log n) sort + O(n) sweep.

## 2. Intuition

Think of intervals as jobs on a timeline. After sorting, the future is always "easier" or "same" relative to the current position, which lets you make one greedy pass.

- **Merge**: sort by start; the current interval can only overlap with the last merged interval (no earlier one, because they've already been absorbed).
- **Min rooms**: imagine a bus that picks up a passenger at `start` and drops them at `end`. The number of buses simultaneously on the road is the number of rooms needed. Convert each interval to two events — `(time, +1)` for boarding and `(time, -1)` for alighting — sort, and sweep, tracking the running total. The running maximum is the answer.
- **Max non-overlapping**: sort by *end*. Always pick the interval that finishes earliest among those compatible with the last chosen one. This leaves the most room for future intervals — the classic greedy exchange-argument insight (swapping in any later-ending interval can only reduce future options).

## 3. Walkthrough

### Merge Intervals: `[[1,3],[2,6],[8,10],[15,18]]`

Sort by start — already sorted here. Initialize `result = [[1,3]]`.

```
Interval [2,6]:   2 <= 3 (overlaps last end) → merge → result = [[1,6]]
Interval [8,10]:  8 >  6 (gap)               → append → result = [[1,6],[8,10]]
Interval [15,18]: 15 > 10 (gap)              → append → result = [[1,6],[8,10],[15,18]]
```

Result: `[[1,6],[8,10],[15,18]]`.

### Min Rooms: `[[0,30],[5,10],[15,20]]`

Events: `(0,+1),(5,+1),(10,-1),(15,+1),(20,-1),(30,-1)` — sort by time.

```
time  0 : count = 1  (max = 1)
time  5 : count = 2  (max = 2)
time 10 : count = 1
time 15 : count = 2  (max stays 2)
time 20 : count = 1
time 30 : count = 0
```

Min rooms = 2.

### Max Non-Overlapping: `[[1,2],[2,3],[3,4],[1,3]]`

Sort by end: `[[1,2],[2,3],[1,3],[3,4]]`. Sweep with `last_end = -inf`.

```
[1,2]: start 1 >= -inf → pick, last_end = 2
[2,3]: start 2 >= 2    → pick, last_end = 3
[1,3]: start 1 <  3    → skip
[3,4]: start 3 >= 3    → pick, last_end = 4
```

Result: 3 intervals selected.

## 4. Implementation

```python
from __future__ import annotations
from typing import List, Tuple


def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    """Merge all overlapping intervals. O(n log n)."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])  # sort by start
    result = [intervals[0][:]]  # copy first interval
    for start, end in intervals[1:]:
        if start <= result[-1][1]:          # overlaps with last merged
            result[-1][1] = max(result[-1][1], end)  # extend end
        else:
            result.append([start, end])
    return result


def min_rooms(intervals: List[List[int]]) -> int:
    """Minimum meeting rooms (max simultaneous overlaps). O(n log n)."""
    if not intervals:
        return 0
    events: List[Tuple[int, int]] = []
    for start, end in intervals:
        events.append((start, 1))    # +1 when a meeting starts
        events.append((end, -1))     # -1 when a meeting ends
    # Sort: on tie, end events (-1) come before start events (+1)
    # so a room freed at time t is available for a meeting starting at t
    events.sort(key=lambda e: (e[0], e[1]))
    current = max_rooms = 0
    for _time, delta in events:
        current += delta
        max_rooms = max(max_rooms, current)
    return max_rooms


def max_non_overlapping(intervals: List[List[int]]) -> int:
    """Maximum number of non-overlapping intervals. O(n log n).

    Sort by end time; greedily take the earliest-finishing compatible interval.
    """
    if not intervals:
        return 0
    sorted_ivs = sorted(intervals, key=lambda x: x[1])  # sort by END
    count = 0
    last_end = float("-inf")
    for start, end in sorted_ivs:
        if start >= last_end:   # compatible: starts at or after last chosen end
            count += 1
            last_end = end
    return count


if __name__ == "__main__":
    # --- merge_intervals ---
    result = merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]])
    assert result == [[1, 6], [8, 10], [15, 18]], result

    assert merge_intervals([]) == []
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([[1, 4], [2, 3]]) == [[1, 4]]  # contained interval

    # --- min_rooms ---
    assert min_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_rooms([[7, 10], [2, 4]]) == 1          # non-overlapping
    assert min_rooms([]) == 0

    # --- max_non_overlapping ---
    assert max_non_overlapping([[1, 2], [2, 3], [3, 4], [1, 3]]) == 3
    assert max_non_overlapping([[1, 2], [1, 2], [1, 2]]) == 1
    assert max_non_overlapping([]) == 0

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Merge / Insert

Sort by start, then do a single sweep maintaining the last merged interval. Insert Interval (LeetCode 57) skips sorting (input is already sorted) and handles three zones: intervals before the new one, the merged zone, and intervals after.

### Min rooms / Max simultaneous overlaps

Two equivalent implementations:

1. **Event sweep**: flatten to `(time, +1/-1)` events, sort, and track running total. On ties, process end events before start events so that a room freed at time `t` counts as available at time `t`.
2. **Two-pointer on sorted starts + sorted ends**: sort starts and ends separately; advance two pointers — if the next start is before the earliest end, a new room is needed; otherwise a room is freed. More cache-friendly but harder to remember.

Car Pooling (LC 1094) is the same pattern with a capacity limit; Sweep Line for rectangle area (LC 850) extends it to 2D.

### Max non-overlapping subset

Sort by **end** (not start — a common mistake). The exchange argument: if an optimal solution includes interval X with `end_X > end_greedy_choice`, you can swap X for the greedy choice without reducing the count (the greedy choice ends no later, giving at least as much room afterward).

Min arrows (LC 452) is the complement: each arrow bursts all overlapping balloons at its x-position; same sort-by-end greedy, but count transitions where the next interval's start exceeds the current arrow position.

### Pitfalls

- **Wrong sort key**: sort by *end* for max non-overlapping; sort by *start* for merge. Swapping the two is the single most common bug.
- **Inclusive vs exclusive endpoints**: does `[1,3]` and `[3,5]` overlap? Check the problem statement. In LeetCode 56 they do (`start <= result[-1][1]`); in Non-overlapping Intervals (435) they do not (`start >= last_end` allows touching).
- **Ties in event sort**: for min rooms, break ties by processing end (`-1`) before start (`+1`) so a room freed at time `t` is available at time `t`.
- **Assuming input is sorted**: LeetCode 56 does not guarantee sorted input; LeetCode 57 does. Always check.

## 6. Complexity

- **Time:** O(n log n) — sorting dominates; the sweep/scan is O(n).
- **Space:** O(n) — the output list or events array can be up to O(n); sorting uses O(log n) stack space.

## 7. Problem set

- [Easy] [Meeting Rooms](https://leetcode.com/problems/meeting-rooms/) — simplest interval overlap check; verify you can detect any overlap in one pass after sorting.
- [Medium] [Merge Intervals](https://leetcode.com/problems/merge-intervals/) — canonical merge problem; teaches the sort-by-start sweep.
- [Medium] [Insert Interval](https://leetcode.com/problems/insert-interval/) — insert into a pre-sorted list; three-zone handling sharpens edge-case reasoning.
- [Medium] [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) — minimum removals = n minus max non-overlapping; validates the sort-by-end greedy.
- [Medium] [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/) — minimum rooms; solidifies the event-sweep or two-pointer approach.
- [Medium] [Minimum Number of Arrows to Burst Balloons](https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/) — count greedy transitions; sort by end, advance arrow only when interval starts beyond current arrow.
- [Medium] [Car Pooling](https://leetcode.com/problems/car-pooling/) — event sweep with a capacity constraint; good extension of min-rooms.
- [Medium] [Minimum Number of Taps to Open to Water a Garden](https://leetcode.com/problems/minimum-number-of-taps-to-open-to-water-a-garden/) — convert tap radii to intervals, then greedy interval cover (sort by start, extend reach greedily).
- [Hard] [Maximum Profit in Job Scheduling](https://leetcode.com/problems/maximum-profit-in-job-scheduling/) — interval DP/binary search combo; shows where pure greedy breaks down and DP is needed.
- [Hard] [Employee Free Time](https://leetcode.com/problems/employee-free-time/) — merge across multiple sorted lists, then find gaps.
- [Hard] [Data Stream as Disjoint Intervals](https://leetcode.com/problems/data-stream-as-disjoint-intervals/) — online merge with a sorted structure; tests ability to maintain a set of disjoint intervals under insertion.

## 8. Related patterns

- [Segment Tree & Fenwick](../trees/segment-tree-fenwick.md) — alternative for range-add / range-query problems where a sorted sweep is insufficient; use when you need arbitrary range updates, not just point-by-point streaming.
- **[Activity Selection](activity-selection.md)** — classical greedy proof for maximum compatible activities; same sort-by-end logic as max non-overlapping, but with an exchange-argument correctness proof.

## 9. Interviewer follow-ups

**Q: Same problem but starts and ends are streamed one at a time?**
You can no longer sort up front. For merge/disjoint-set queries, maintain a sorted container (e.g., Python `sortedcontainers.SortedList` or a balanced BST) keyed on start; on each insertion find the neighbors and merge. For min rooms, maintain a running count with a sorted multiset of end times; when a new start arrives, check if the smallest end time is less than or equal to the new start (a room is freed). Both operations are O(log n) per event.

**Q: Find a busy schedule with the minimum number of machines?**
This is identical to the minimum meeting rooms problem: the minimum machines needed equals the maximum number of simultaneously active intervals. Use the event sweep or the sorted-starts / sorted-ends two-pointer approach — both give O(n log n).
