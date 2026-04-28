"""Backtracking templates. See ../topics/backtracking/backtracking-template.md."""
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
