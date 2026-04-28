# Sliding Window

## 1. TL;DR

The sliding window pattern applies whenever you need the longest or shortest subarray/substring satisfying a property, or the maximum/minimum aggregate of a fixed-size window. Maintain indices `[l, r]`: advance `r` to expand; while a constraint is violated, advance `l` to contract. Because each pointer moves at most n times, the total work is O(n). The signal is "longest/shortest substring/subarray with property X," "max sum of size-k window," or "minimum window containing X." Time: O(n). Space: O(k) or O(charset).

## 2. Intuition

Imagine scanning a string with a magnifying glass. You slide the right edge rightward to include new characters. The moment the view violates your constraint (too many distinct characters, sum exceeds the target, a repeat appears), you shrink from the left until the constraint is satisfied again. The key insight: you never need to reconsider any window smaller than the best you've already seen, and you never need to restart — each pointer moves only forward, so together they traverse the input once.

This works because the constraint is **monotone with respect to window size**: making the window larger can only make a "valid" constraint harder to satisfy (for minimum-window problems) or a "too large" sum more excessive. Without this monotonicity (e.g., negative numbers in a "max sum" problem) the shrink step isn't safe — you might miss a smaller window that becomes valid later. That's why sliding window breaks on arrays with negative values for sum problems; you fall back to prefix sums plus a hash map instead.

The window's internal state (a character counter, a frequency map, a running sum) is maintained incrementally: add `s[r]` on expand, subtract `s[l]` on contract. Never recompute from scratch.

## 3. Walkthrough

### Variable window: longest substring without repeating characters, s = "abcabcbb"

Maintain a set of characters currently in the window. `l` and `r` are indices; `max_len` tracks the best.

```
l=0 r=0: add 'a' → window={'a'}                        max_len=1
l=0 r=1: add 'b' → window={'a','b'}                    max_len=2
l=0 r=2: add 'c' → window={'a','b','c'}                max_len=3
l=0 r=3: try 'a' → 'a' already in window! → shrink:
  remove s[l=0]='a', l=1 → window={'b','c'}
  now 'a' not in window → add 'a' → window={'b','c','a'} max_len=3
l=1 r=4: try 'b' → 'b' already in window! → shrink:
  remove s[l=1]='b', l=2 → window={'c','a'}
  add 'b' → window={'c','a','b'}                        max_len=3
l=2 r=5: try 'c' → 'c' already in window! → shrink:
  remove s[l=2]='c', l=3 → window={'a','b'}
  add 'c' → window={'a','b','c'}                        max_len=3
l=3 r=6: try 'b' → 'b' already in window! → shrink:
  remove s[l=3]='a', l=4 → window={'b','c'}
  'b' still in window → remove s[l=4]='b', l=5 → window={'c'}
  add 'b' → window={'c','b'}                            max_len=3
l=5 r=7: try 'b' → 'b' already in window! → shrink:
  remove s[l=5]='c', l=6 → window={'b'}
  'b' still in window → remove s[l=6]='b', l=7 → window={}
  add 'b' → window={'b'}                                max_len=3
r reaches end. Answer: 3.
```

### Fixed window: max sum of size 3, nums = [1, 4, 2, 9, 3]

Compute the first window [0..2], then slide: add `nums[r]`, subtract `nums[l]`, advance both.

```
Initial window [1, 4, 2]: sum = 7                       max_sum=7
Slide: r=3, l=1 → add 9, subtract 1 → sum = 7+9-1=15   max_sum=15
Slide: r=4, l=2 → add 3, subtract 4 → sum = 15+3-4=14  max_sum=15
Answer: 15.
```

## 4. Implementation

```python
from __future__ import annotations
from collections import defaultdict, deque
from typing import List


def longest_substring_no_repeat(s: str) -> int:
    """LeetCode 3. Longest substring without repeating characters.

    last_seen maps each character to its most recent index. When a duplicate
    is found, jump l directly past the previous occurrence — faster than the
    set-shrink approach because it avoids the inner while loop.
    """
    last_seen: dict = {}
    l = 0
    max_len = 0
    for r, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= l:
            l = last_seen[ch] + 1  # jump l past the last occurrence of ch
        last_seen[ch] = r
        max_len = max(max_len, r - l + 1)
    return max_len


def min_window(s: str, t: str) -> str:
    """LeetCode 76. Minimum window substring.

    need tracks how many of each character in t we still require.
    have counts characters in t whose window count meets the requirement.
    When have == len(unique chars in t), the window is valid; contract from left.
    """
    if not s or not t:
        return ""
    need: dict = defaultdict(int)
    for ch in t:
        need[ch] += 1
    required = len(need)   # number of distinct characters in t
    have = 0
    window_counts: dict = defaultdict(int)
    l = 0
    best = (float("inf"), 0, 0)  # (length, l, r)
    for r, ch in enumerate(s):
        window_counts[ch] += 1
        if ch in need and window_counts[ch] == need[ch]:
            have += 1  # this character's requirement is now met
        while have == required:
            # Contract: try to shrink from the left.
            window_len = r - l + 1
            if window_len < best[0]:
                best = (window_len, l, r)
            left_ch = s[l]
            window_counts[left_ch] -= 1
            if left_ch in need and window_counts[left_ch] < need[left_ch]:
                have -= 1  # losing this character breaks the requirement
            l += 1
    return s[best[1]: best[2] + 1] if best[0] != float("inf") else ""


def max_sum_fixed_window(nums: List[int], k: int) -> int:
    """Maximum sum of any contiguous subarray of size exactly k.

    O(n) time: build first window, then slide one element at a time.
    """
    if len(nums) < k:
        return 0
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for r in range(k, len(nums)):
        window_sum += nums[r] - nums[r - k]  # add new right, drop old left
        max_sum = max(max_sum, window_sum)
    return max_sum


def monotonic_deque_max(nums: List[int], k: int) -> List[int]:
    """LeetCode 239. Sliding Window Maximum.

    A monotone decreasing deque stores indices; the front is always the max
    of the current window. Before adding nums[r]: pop all indices from the
    back whose values are <= nums[r] (they can never be the max while r is
    in the window). Before reading the max: pop the front if it's out of window.
    O(n) — each index is pushed and popped at most once.
    """
    dq: deque = deque()  # stores indices; decreasing in terms of nums[dq[i]]
    result: List[int] = []
    for r in range(len(nums)):
        # Remove indices out of the window [r-k+1, r].
        while dq and dq[0] < r - k + 1:
            dq.popleft()
        # Maintain decreasing order: pop smaller elements from the back.
        while dq and nums[dq[-1]] <= nums[r]:
            dq.pop()
        dq.append(r)
        # Start recording results once the first full window is formed.
        if r >= k - 1:
            result.append(nums[dq[0]])
    return result


def longest_substring_at_most_k_distinct(s: str, k: int) -> int:
    """Longest substring with at most k distinct characters.

    Classic variable-window with a frequency map as the window state.
    """
    freq: dict = defaultdict(int)
    l = 0
    max_len = 0
    for r, ch in enumerate(s):
        freq[ch] += 1
        while len(freq) > k:
            left_ch = s[l]
            freq[left_ch] -= 1
            if freq[left_ch] == 0:
                del freq[left_ch]
            l += 1
        max_len = max(max_len, r - l + 1)
    return max_len


if __name__ == "__main__":
    # longest_substring_no_repeat
    assert longest_substring_no_repeat("abcabcbb") == 3
    assert longest_substring_no_repeat("bbbbb") == 1
    assert longest_substring_no_repeat("pwwkew") == 3
    assert longest_substring_no_repeat("") == 0

    # min_window
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""

    # max_sum_fixed_window
    assert max_sum_fixed_window([1, 4, 2, 9, 3], 3) == 15
    assert max_sum_fixed_window([2, 1, 5, 1, 3, 2], 3) == 9
    assert max_sum_fixed_window([1, 2], 3) == 0

    # monotonic_deque_max
    assert monotonic_deque_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert monotonic_deque_max([1], 1) == [1]

    # longest_substring_at_most_k_distinct
    assert longest_substring_at_most_k_distinct("eceba", 2) == 3  # "ece"
    assert longest_substring_at_most_k_distinct("aa", 1) == 2

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Fixed-size window

The window size k is given. Build the first window with `sum(nums[:k])`, then slide: `window_sum += nums[r] - nums[r - k]`. Time O(n). Common use cases: max/min sum of size k, anagram detection (fixed-size character-count window), checking all windows for a property.

### Variable-size window on a constraint (expand-then-contract)

The window expands by advancing `r`; contracts by advancing `l` until the constraint holds. Use a frequency map, counter, or integer as the window's state. After each `r` step, update state; then contract `l` as long as the constraint is violated. Record the window length before or after contracting depending on whether you're tracking the longest valid window (record before contracting, after adding) or the shortest valid window (record inside the while loop, while valid). The `min_window` implementation uses the inner-while-valid approach for the shortest window.

### Count problems: subarrays with sum = k

When the constraint is equality (not "at most") on a sum, sliding window doesn't apply directly — you can't tell whether to expand or contract. Use **prefix sums with a hash map**: for each index `r`, ask "how many prefixes have sum = `prefix[r] - k`?" That's O(n) time, O(n) space.

### Monotonic deque for window max/min

A plain sliding window can report the sum of any window in O(1) but cannot report the max in O(1) without extra structure. A **monotonic decreasing deque** (stores indices; front is the max) supports:
- Push right: pop all back elements smaller than the new one, then append.
- Pop left (expired): if the front index is outside the window, pop it.
Each index is pushed and popped at most once → O(n) total. This is strictly better than a heap with lazy deletion (O(n log n)) for a streaming max.

### Anagram detection (LeetCode 567)

Fixed-size window of length `len(p)`. Maintain a character-count delta: decrement for characters entering the window on the right, increment for characters leaving on the left. When the delta for all characters is zero, an anagram is found. Using a single "number of characters with nonzero delta" counter avoids iterating over the entire count array for every window position.

### Pitfalls

- **Negative values break sum-based sliding window**: if elements can be negative, shrinking the window might make the sum smaller, so you can't decide to contract based on "sum too large." Use prefix sums + hash map instead.
- **Forgetting to decrement on contract**: when `l` advances past `s[l]`, decrement `window_counts[s[l]]` before incrementing `l`. Forgetting this makes the window appear to contain characters it no longer does.
- **Off-by-one in window length**: the number of elements in `[l, r]` is `r - l + 1`, not `r - l`. Use `r - l + 1` for length and `s[l:r+1]` for slicing.
- **Recording after vs before the contract loop**: for the longest-valid-window pattern, record `r - l + 1` after expanding `r` and before (or outside) the contract loop. For the shortest-valid-window pattern, record inside the while loop when the window is valid.

## 6. Complexity

- **Time:** O(n) — `l` advances at most n times and `r` advances at most n times; total 2n pointer moves. Each element is added to and removed from the window state exactly once. The monotonic deque gives O(1) amortized max/min per step.
- **Space:** O(k) for a fixed-size window state; O(charset) or O(k) for a variable-size window with a character map; O(k) for the monotonic deque.

## 7. Problem set

- [Easy] [Maximum Average Subarray I](https://leetcode.com/problems/maximum-average-subarray-i/) — fixed-size window sum divided by k; the simplest possible sliding window to build muscle memory.
- [Easy] [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) — sliding minimum so far and running max profit; can be framed as a one-pass window scan.
- [Medium] [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) — variable window with a last-seen map; the last-seen jump optimization avoids an inner while loop.
- [Medium] [Permutation in String](https://leetcode.com/problems/permutation-in-string/) — fixed-size window anagram detection; character-count delta approach keeps state in O(26).
- [Medium] [Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) — variable window; the key insight is that you only need to track the maximum frequency character in the window to decide validity.
- [Medium] [Max Consecutive Ones III](https://leetcode.com/problems/max-consecutive-ones-iii/) — variable window allowing at most k zeros; `l` advances only when the zero count exceeds k.
- [Medium] [Fruit Into Baskets](https://leetcode.com/problems/fruit-into-baskets/) — at-most-2-distinct-types window; reduces directly to the longest-substring-with-at-most-k-distinct template.
- [Medium] [Minimum Size Subarray Sum](https://leetcode.com/problems/minimum-size-subarray-sum/) — shortest window with sum ≥ target (non-negative numbers only); the inner while loop shrinks while valid and records the minimum each time.
- [Hard] [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) — shortest window containing all characters of t; the `have`/`required` counter avoids checking the entire frequency map on every contraction.
- [Hard] [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) — fixed-size window max; the monotonic deque is the canonical O(n) solution; a heap gives O(n log n).
- [Hard] [Substring with Concatenation of All Words](https://leetcode.com/problems/substring-with-concatenation-of-all-words/) — fixed-size multi-word window; run k separate sliding-window passes (one per offset mod word_length) to keep each pass O(n).

## 8. Related patterns

- **[Two Pointers](two-pointers.md)** — sliding window is a two-pointer pattern where both move in the same direction and the window state is tracked between them; two pointers in opposing-pointer mode targets sorted arrays and pair sums rather than substring/subarray properties.
- **[Fast/Slow Pointers](fast-slow-pointers.md)** — another same-direction two-pointer variant, specialized for linked-list cycle detection; does not maintain window state.
- **Rabin-Karp / rolling hash** — an alternative for fixed-size window substring matching that replaces the character-count comparison with a hash equality check; O(n) average, O(1) space per window. (File at `../strings/rabin-karp.md` does not exist yet.)
- **Segment Tree & Fenwick Tree** — for window queries that need more than sum/max (e.g., count of elements in a range), a Fenwick tree supports O(log n) point-update and prefix-sum queries; pairs with a sliding window when the state is a range query. (File at `../trees/segment-tree-fenwick.md` does not exist yet.)

## 9. Interviewer follow-ups

**Q: What if values can be negative?**
The shrink step assumes that removing an element from the left reduces the window sum (or moves toward satisfying the constraint). With negatives this assumption breaks: removing a negative element increases the sum, so you might shrink past a valid window. The correct approach is **prefix sums plus a hash map**: compute `prefix[r]` for each position; for each `r`, look up how many previous indices had `prefix[j] == prefix[r] - k`. This gives the count of subarrays with sum exactly k in O(n) / O(n).

**Q: Sliding window maximum?**
A monotonic deque, not a heap. A min-heap with lazy deletion gives O(n log k) — you pay O(log k) per pop and there are O(n) pops in the worst case. The monotonic deque is O(n) total because each index is pushed once and popped once regardless of k. The deque is decreasing: before adding index `r`, pop all back elements whose values are ≤ `nums[r]` (they can never be the window max while `r` is present). Pop the front whenever its index falls outside the current window. See `monotonic_deque_max` in Section 4.
