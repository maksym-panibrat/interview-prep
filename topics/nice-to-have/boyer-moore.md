# Boyer-Moore Majority Vote

## 1. TL;DR

Boyer-Moore Majority Vote finds the majority element (appearing > n/2 times) in a single O(n) pass using O(1) space — no hash map, no sorting. The signal is "majority element" with an O(1) extra-space constraint, "streaming counts where you can't store everything," or "voting-style aggregation." Generalized to > n/k: track k-1 candidates. Time: O(n). Space: O(1) (or O(k) for the k-variant).

## 2. Intuition

Imagine an election where each voter can cancel out one opposing voter. If a true majority exists — more than half the votes — then even after every minority vote has cancelled an equal number of majority votes, at least one majority vote survives uncancelled. That survivor is the candidate.

Concretely: maintain `candidate` and `count`. On each element, if `count` is 0 replace the candidate. If the element matches the candidate, increment `count`; otherwise decrement it. A decrement pairs off one "yes" vote with one "no" vote, cancelling both. Because the majority element has more votes than all others combined, it always survives the cancellation process.

Important: this only proves the surviving candidate is the *only possible* majority. If no element actually exceeds n/2, the candidate is arbitrary. A second pass verifying the count is required when existence is not guaranteed.

## 3. Walkthrough

Trace `majority_element([2, 2, 1, 1, 1, 2, 2])`:

```
i=0  x=2  count=0 → set candidate=2, count=1
i=1  x=2  matches  → count=2
i=2  x=1  differs  → count=1
i=3  x=1  differs  → count=0
i=4  x=1  count=0  → set candidate=1, count=1
i=5  x=2  differs  → count=0
i=6  x=2  count=0  → set candidate=2, count=1

Final candidate = 2
Verify: count(2) = 4 > 7/2 = 3.5 ✓
```

Each time two *different* values cancel each other, both are discarded from the "election." After all cancellations the only viable survivor is 2.

## 4. Implementation

```python
from __future__ import annotations


def majority_element(nums: list[int]) -> int:
    """Classic Boyer-Moore majority vote: returns the element appearing > n/2 times.

    Assumes a majority element exists. Caller should verify if uncertain.
    """
    candidate, count = nums[0], 0
    for x in nums:
        if count == 0:
            candidate = x
        count += 1 if x == candidate else -1
    return candidate


def majority_n_div_3(nums: list[int]) -> list[int]:
    """Return all elements appearing > n/3 times (at most 2 such elements).

    Uses two candidates and two counters — the generalised Boyer-Moore for k=3.
    Always includes a verification pass; returns a sorted list for determinism.
    """
    # Phase 1: find up to 2 candidate survivors
    cand1, cand2 = None, None
    cnt1, cnt2 = 0, 0
    for x in nums:
        if x == cand1:
            cnt1 += 1
        elif x == cand2:
            cnt2 += 1
        elif cnt1 == 0:
            cand1, cnt1 = x, 1
        elif cnt2 == 0:
            cand2, cnt2 = x, 1
        else:
            # cancel one vote against each candidate
            cnt1 -= 1
            cnt2 -= 1

    # Phase 2: verify — candidates are survivors, not guaranteed majorities
    threshold = len(nums) // 3
    result = [
        c for c in (cand1, cand2)
        if c is not None and nums.count(c) > threshold
    ]
    return sorted(result)


if __name__ == "__main__":
    assert majority_element([2, 2, 1, 1, 1, 2, 2]) == 2
    assert majority_element([3, 2, 3]) == 3
    assert majority_element([1]) == 1

    assert majority_n_div_3([3, 2, 3]) == [3]
    res = majority_n_div_3([1, 1, 1, 3, 3, 2, 2, 2])
    assert sorted(res) == [1, 2], f"got {res}"
    assert majority_n_div_3([1, 2, 3]) == []  # no element > n/3
    assert majority_n_div_3([1]) == [1]

    print("All smoke tests passed.")
```

**Template:**

```python
def majority_element(nums: list[int]) -> int:
    candidate, count = nums[0], 0
    for x in nums:
        if count == 0:
            candidate = x
        count += 1 if x == candidate else -1
    return candidate


def majority_n_div_3(nums: list[int]) -> list[int]:
    cand1, cand2 = None, None
    cnt1, cnt2 = 0, 0
    for x in nums:
        if x == cand1:
            cnt1 += 1
        elif x == cand2:
            cnt2 += 1
        elif cnt1 == 0:
            cand1, cnt1 = x, 1
        elif cnt2 == 0:
            cand2, cnt2 = x, 1
        else:
            cnt1 -= 1
            cnt2 -= 1
    threshold = len(nums) // 3
    return sorted(
        c for c in (cand1, cand2)
        if c is not None and nums.count(c) > threshold
    )
```

## 5. Variants & pitfalls

**Classic majority (> n/2):** single candidate, single counter. Guaranteed a majority exists on many LeetCode formulations — skip the verification pass only when the problem guarantees it.

**Generalized > n/k:** track k-1 candidates and k-1 counters. For each element, match against an existing candidate (increment its counter), claim an empty slot (counter = 1), or cancel all k-1 candidates by decrementing each counter by 1. Always follow with a verification pass.

**Boyer-Moore string search (different algorithm):** The *string-search* Boyer-Moore uses a bad-character heuristic (on mismatch, shift the pattern right so the last occurrence of the bad character aligns with it) plus a good-suffix shift — achieving sub-linear average-case search time. It is a completely separate algorithm that shares only the name. In interviews KMP and Z-Algorithm are preferred for string search; Boyer-Moore string search is rarely asked.

**Pitfalls:**

- Skipping the verification pass in the > n/k variant: when no element actually exceeds n/k, the surviving candidates are spurious. Always verify.
- Thinking the candidate is "the most frequent element": it is only the majority *if one exists*. Without verification the candidate is meaningless when no majority is present.
- For the two-candidate variant, checking `x == cand1` and `x == cand2` before checking for empty slots: order matters. Match existing candidates first, then fill empty slots, then cancel.

## 6. Complexity

- **Time:** O(n) — two linear passes (one to find candidates, one to verify); each element is processed O(1).
- **Space:** O(1) for the classic variant; O(k) for the > n/k variant (k-1 candidate/counter pairs).

## 7. Problem set

- [Easy] [Majority Element](https://leetcode.com/problems/majority-element/) — direct application of the single-candidate vote; existence is guaranteed, so no verification pass needed.
- [Medium] [Majority Element II](https://leetcode.com/problems/majority-element-ii/) — requires the two-candidate generalization; verification pass is mandatory since up to two results are possible.

## 8. Related patterns

- [Two Pointers](../two-pointers-sliding-window/two-pointers.md) — another O(n)/O(1) streaming pattern; two-pointer aggregates over a window while majority vote cancels across the whole stream.
- [KMP](../strings/kmp.md) — note the name clash: Boyer-Moore *string search* is a separate algorithm competing with KMP for string matching; in interviews KMP is preferred because the failure function is simpler to derive under pressure.

## 9. Interviewer follow-ups

**Q: Why does the majority-vote algorithm work?**
Pair-off intuition: every counter decrement cancels exactly one majority vote against one minority vote. Because the majority element appears more than n/2 times, there are not enough minority votes to cancel all majority votes — at least one majority vote survives. Any element with at most n/2 occurrences can always be fully cancelled. So the sole survivor (candidate with count > 0) must be the majority element.

**Q: Generalize to > n/k.**
Track k-1 candidates and k-1 counters. Process each element: if it matches an existing candidate increment that counter; else if any counter is 0 claim that slot; else decrement every counter by 1 (one cancellation per candidate). At most k-1 elements can exceed n/k. Always verify each surviving candidate with a second pass to confirm its true count exceeds n/k — survivors without a verification step may be false positives.
