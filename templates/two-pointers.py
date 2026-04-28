"""Two-pointer templates. See ../topics/two-pointers-sliding-window/two-pointers.md."""
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
