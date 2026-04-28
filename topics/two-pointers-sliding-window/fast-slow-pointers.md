# Fast/Slow Pointers

## 1. TL;DR

Fast/slow pointers (Floyd's tortoise and hare) detect cycles in linked lists and functional sequences in O(n) time and O(1) space. The signal is "linked-list cycle," "find middle of linked list," "k-th from end," "palindrome linked list," or "find duplicate in array treated as a graph." Move `slow` by one step and `fast` by two; if they ever meet, a cycle exists. A second phase — resetting `slow` to head and stepping both by one — locates the cycle's entry point exactly. Time: O(n). Space: O(1).

## 2. Intuition

Think of two runners on a circular track. If the track has a loop, the faster runner will eventually lap the slower one — they must meet somewhere inside the loop. If there is no loop, the faster runner reaches the end and the race stops cleanly.

The elegant part is the **phase-2 math** that pins down where the cycle begins. Let:

- μ = distance from the head to the cycle entry (the "tail length").
- L = cycle length.
- k = distance from the cycle entry to the meeting point (measured inside the loop).

When slow and fast first meet:
- Slow has traveled μ + k steps.
- Fast has traveled 2(μ + k) steps (twice as far, same meeting point).
- Fast has lapped slow, so the extra distance is a whole number of loops: 2(μ + k) − (μ + k) = μ + k = m × L for some integer m.

Therefore μ + k ≡ 0 (mod L), which means μ ≡ −k ≡ L − k (mod L). In plain English: if you walk μ more steps from the meeting point, you travel exactly to the cycle entry. But walking μ steps from the head also reaches the cycle entry. So: **reset slow to head, leave fast at the meeting point, both step by 1 — they converge at the cycle entry.**

This is O(1) space because you never build a visited set; you exploit the algebraic relationship between distances.

## 3. Walkthrough

### Cycle detection and entry: 1 → 2 → 3 → 4 → 5 → (back to 3)

The list has nodes with values 1, 2, 3, 4, 5 where node 5's `next` points back to node 3 (the node at index 2, 0-indexed). So μ = 2 (nodes 1 and 2 before the cycle), L = 3 (cycle: 3 → 4 → 5 → back to 3).

**Phase 1 — detect meeting point:**

```
Initial: slow = node(1), fast = node(1)

Step 1: slow → node(2),         fast → node(3)
Step 2: slow → node(3),         fast → node(5)
Step 3: slow → node(4),         fast → node(4)   ← meet!
```

Meeting point is node(4), which is at distance k = 1 inside the cycle from the entry node(3).

Verify the math: μ = 2, k = 1, L = 3. Check: μ + k = 3 = 1 × L. ✓

**Phase 2 — find cycle entry:**

Reset slow to head (node 1). Fast stays at node(4). Both step by 1.

```
Step 1: slow → node(2),  fast → node(5)
Step 2: slow → node(3),  fast → node(3)   ← meet at cycle entry!
```

Both arrive at node(3) after 2 steps — exactly μ = 2 steps from their respective starting points. The cycle entry is node(3). ✓

### Find middle of a linked list: 1 → 2 → 3 → 4 → 5

Start both at head. Advance slow by 1, fast by 2. When fast reaches the end (or null), slow is at the middle.

```
Initial: slow = node(1), fast = node(1)
Step 1: slow → node(2), fast → node(3)
Step 2: slow → node(3), fast → node(5)
Step 3: fast.next = null → stop. slow = node(3) = middle.
```

For an even-length list `1 → 2 → 3 → 4`: slow lands at node(2) (first of the two middle nodes), since `fast.next` becomes null at node(4) while slow is at node(2). For the palindrome check you want the second half to start at node(3), so advance slow one more step after the loop.

## 4. Implementation

```python
from __future__ import annotations
from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def has_cycle(head: Optional[ListNode]) -> bool:
    """LeetCode 141. Detect whether the linked list has a cycle.

    O(n) time, O(1) space. Returns True if fast catches slow.
    """
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
        if slow is fast:
            return True
    return False


def detect_cycle(head: Optional[ListNode]) -> Optional[ListNode]:
    """LeetCode 142. Return the node where the cycle begins, or None.

    Phase 1: find meeting point (standard fast/slow).
    Phase 2: reset slow to head, step both by 1 until they meet at cycle entry.
    """
    slow = fast = head
    # Phase 1: find meeting point inside the cycle.
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None  # no cycle
    # Phase 2: slow back to head, both step by 1.
    slow = head
    while slow is not fast:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next          # type: ignore[union-attr]
    return slow  # cycle entry node


def find_middle(head: Optional[ListNode]) -> Optional[ListNode]:
    """LeetCode 876. Return the middle node (second middle for even-length lists).

    When fast reaches the last node (or past it), slow is at the middle.
    For [1,2,3,4,5] → node(3). For [1,2,3,4] → node(3) (second middle).
    """
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
    return slow


def is_palindrome(head: Optional[ListNode]) -> bool:
    """LeetCode 234. Check if the linked list is a palindrome.

    1. Find middle with fast/slow.
    2. Reverse the second half in-place.
    3. Compare both halves.
    4. (Optional) restore the list.
    O(n) time, O(1) space.
    """
    if head is None or head.next is None:
        return True
    # Step 1: find end of first half.
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next          # type: ignore[assignment]
        fast = fast.next.next
    # slow is now at end of first half; slow.next starts the second half.
    # Step 2: reverse second half.
    second_half_start = _reverse(slow.next)  # type: ignore[arg-type]
    slow.next = None  # sever the link (optional for compare, needed for restore)
    # Step 3: compare.
    p1: Optional[ListNode] = head
    p2: Optional[ListNode] = second_half_start
    result = True
    while p2 is not None:
        if p1 is None or p1.val != p2.val:
            result = False
            break
        p1 = p1.next
        p2 = p2.next
    # Step 4: restore (good practice in interviews).
    slow.next = _reverse(second_half_start)
    return result


def _reverse(head: Optional[ListNode]) -> Optional[ListNode]:
    """Reverse a linked list in-place. Returns new head."""
    prev: Optional[ListNode] = None
    curr = head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev


def find_duplicate(nums: list) -> int:
    """LeetCode 287. Find the duplicate in nums = [1..n] with one extra duplicate.

    Treat each value as a pointer to the next index: index → nums[index].
    The duplicate creates a cycle (two indices point to the same next index).
    Apply Floyd's cycle-entry algorithm on indices, not ListNodes.
    O(n) time, O(1) space. Does not mutate the array.
    """
    slow = fast = nums[0]
    # Phase 1: find meeting point.
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    # Phase 2: find cycle entry = the duplicate.
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


if __name__ == "__main__":
    # Build a list with a cycle: 3 -> 1 -> 2 -> (back to node 1, 0-indexed)
    # i.e., values 3,1,2 and node(2).next = node(1)
    n3 = ListNode(3)
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3.next = n1
    n1.next = n2
    n2.next = n1  # cycle: points back to n1
    assert has_cycle(n3) is True
    entry = detect_cycle(n3)
    assert entry is n1

    # List without a cycle: 1 -> 2 -> 3 -> None
    a, b, c = ListNode(1), ListNode(2), ListNode(3)
    a.next = b
    b.next = c
    assert has_cycle(a) is False
    assert detect_cycle(a) is None

    # Find middle
    def make_list(vals):
        dummy = ListNode(0)
        cur = dummy
        for v in vals:
            cur.next = ListNode(v)
            cur = cur.next
        return dummy.next

    mid = find_middle(make_list([1, 2, 3, 4, 5]))
    assert mid is not None and mid.val == 3
    mid2 = find_middle(make_list([1, 2, 3, 4]))
    assert mid2 is not None and mid2.val == 3  # second of the two middles

    # Palindrome
    assert is_palindrome(make_list([1, 2, 2, 1])) is True
    assert is_palindrome(make_list([1, 2, 3, 2, 1])) is True
    assert is_palindrome(make_list([1, 2])) is False

    # Find duplicate
    assert find_duplicate([1, 3, 4, 2, 2]) == 2
    assert find_duplicate([3, 1, 3, 4, 2]) == 3

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Detect cycle existence (LeetCode 141)

The simplest application: just check whether `slow is fast` after any step. If `fast` or `fast.next` is `None` before a meeting, there is no cycle. The loop condition `while fast is not None and fast.next is not None` handles both.

### Find cycle entry (LeetCode 142)

After the phase-1 meeting, reset `slow` to `head` and step both by 1. They converge at the entry. This requires that `fast` stay at the meeting point — do not reset `fast`. The `while slow is not fast` condition uses identity (`is`), not value equality (`==`), because two different nodes can hold the same value.

### Find middle (LeetCode 876)

Two conventions exist: for an odd-length list there is a single middle; for even-length there are two middles. The standard `fast.next is not None and fast.next.next is not None` loop condition yields the **first** middle on even-length lists (slow ends at index n//2 - 1 for 0-indexed). The simpler `fast is not None and fast.next is not None` yields the **second** middle. Know which convention you need before the interview — for the palindrome check you typically want the second half to start at the node after the first-middle, so use the first convention and then take `slow.next`.

### Palindrome linked list (LeetCode 234)

Find the first-middle with fast/slow, reverse the second half in-place, compare both halves from head to the reversed tail, then restore the list (good practice to show you respect immutability). The in-place reversal is O(1) space and O(n) time; the entire palindrome check is O(n) / O(1).

### Find duplicate in [1..n] array (LeetCode 287)

Treat each element as a pointer: index `i` "points to" index `nums[i]`. Since every value is in `[1, n]` and the array has `n + 1` elements with one repeated value, there must be two indices that point to the same next index — a cycle with the cycle-entry being the duplicate. Apply Floyd's algorithm on the index graph: `slow = nums[slow]`, `fast = nums[nums[fast]]`. O(n) time, O(1) space — better than sorting (O(n log n)) or a hash set (O(n) space).

### Happy Number (LeetCode 202)

Define `f(x) = sum of squares of digits of x`. Apply fast/slow to the sequence x, f(x), f(f(x)), … If the sequence cycles back to 1, the number is happy; otherwise it cycles on some non-1 value. Floyd's algorithm detects whether the cycle contains 1 or not in O(n) time.

### Null safety before stepping

The most common runtime error: calling `fast.next.next` when `fast.next` is `None`. Always check `fast is not None and fast.next is not None` as the loop guard. When building the loop body, never assume `fast.next.next` exists without the guard.

### Pitfalls

- **`is` vs `==` for node comparison**: use `slow is fast` (identity) in the cycle-entry loop, not `slow == fast` (value equality). Two distinct nodes can hold the same integer value.
- **Stepping fast before slow**: the order doesn't matter for correctness, but the convention `slow = slow.next; fast = fast.next.next` is clearest — advance both before the equality check.
- **Even-length middle ambiguity**: decide before starting whether you want the first or second of the two middle nodes, and pick the matching loop condition. Mixing them breaks the palindrome check.
- **Not restoring the list after palindrome check**: in-place reversal mutates the original structure. Restore by reversing again if the caller might use the list afterward.

## 6. Complexity

- **Time:** O(n) — phase 1 takes at most μ + L ≤ n steps to reach the meeting point; phase 2 takes exactly μ ≤ n steps to reach the cycle entry. Total 2n = O(n).
- **Space:** O(1) — only the `slow` and `fast` pointer variables; no visited set or auxiliary array.

## 7. Problem set

- [Easy] [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/) — the purest form; just detect existence, no entry-finding needed.
- [Easy] [Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/) — confirms you know which loop condition to use for the desired middle convention.
- [Easy] [Palindrome Linked List](https://leetcode.com/problems/palindrome-linked-list/) — combines find-middle, reverse, and compare in one problem; tests all three sub-skills together.
- [Medium] [Linked List Cycle II](https://leetcode.com/problems/linked-list-cycle-ii/) — requires the full two-phase Floyd algorithm; the distance-math proof is the entire challenge.
- [Medium] [Find the Duplicate Number](https://leetcode.com/problems/find-the-duplicate-number/) — transfers fast/slow from a linked list to an index-as-pointer graph; the insight that the array encodes a functional graph is the problem's core.
- [Medium] [Happy Number](https://leetcode.com/problems/happy-number/) — applies Floyd's algorithm to a purely arithmetic sequence; demonstrates the pattern works on any `f: finite_domain → finite_domain`.

## 8. Related patterns

- **[Two Pointers](two-pointers.md)** — fast/slow is a same-direction two-pointer variant; the key difference is that fast moves 2× instead of scanning ahead by value, and the pattern targets linked lists (no random access) rather than sorted arrays.
- **[DFS](../graphs/dfs.md)** — for cycle detection in a **directed graph**, DFS with a "currently in stack" color is the standard approach; fast/slow doesn't generalize to directed graphs with branching.

## 9. Interviewer follow-ups

**Q: Why does resetting slow to head and stepping both by 1 reach the cycle entry?**
Let μ be the head-to-entry distance and L the cycle length. At the phase-1 meeting point, slow traveled μ + k steps and fast traveled 2(μ + k) steps. The difference μ + k must be a multiple of L, so μ ≡ L − k (mod L). Walking μ more steps from the meeting point wraps around the cycle exactly to the entry. Walking μ steps from the head also reaches the entry. Both pointers therefore converge at the cycle entry after exactly μ steps in phase 2.

**Q: Generalize to a function f(x) — does it eventually cycle?**
Yes, for any function f where the codomain is finite. Because the domain is finite, the sequence x, f(x), f(f(x)), … must eventually revisit a value — that revisit is the cycle. Floyd's algorithm applies to any such sequence, not just linked lists. Happy Number (LeetCode 202) and Find the Duplicate Number (LeetCode 287) both exploit this: the digit-square-sum function and the index-as-pointer function both have finite codomains, guaranteeing a cycle that Floyd's algorithm can find in O(n) / O(1).
