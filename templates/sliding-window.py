"""Sliding window templates. See ../topics/two-pointers-sliding-window/sliding-window.md."""
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
