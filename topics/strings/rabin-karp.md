# Rabin-Karp

## 1. TL;DR

Rabin-Karp finds a pattern of length m in a text of length n by treating each window as a polynomial hash and sliding it in O(1) per step. The signal is "find substring or k-length window with hash equality," plagiarism / repeated-substring detection, or any rolling-hash sliding window over a string. Average time is O(n + m); naïve verification on every hash hit gives O(nm) worst case with adversarial collisions. Space: O(1) beyond the input.

## 2. Intuition

Treat a string window `s[l..r]` as a base-B number: each character contributes its value times B raised to its positional power, all taken mod a large prime p. When the window slides one step right, you subtract the contribution of the leftmost character, multiply the remainder by B (shifting all positional values up by one), then add the new rightmost character. This keeps the hash current in O(1) per step.

The catch: two different strings can hash to the same value (a collision). KMP guarantees no false positives; Rabin-Karp does not — always verify a hit by comparing the actual strings. With a good prime and base, collisions are rare (roughly 1/p probability per window), so in practice the algorithm runs in O(n + m) time.

## 3. Walkthrough

### Rolling a hash over `text = "ababcd"`, `pattern = "bab"`, k = 3

Parameters: `BASE = 26`, `MOD = 10**9 + 7`. Map characters `a=1, b=2, c=3, d=4`.

**Initial hash of `"bab"` (pattern):**

```
hash("bab") = (2 * 26^2 + 1 * 26^1 + 2 * 26^0) % MOD
            = (1352 + 26 + 2) % MOD
            = 1380
```

**Initial window hash `"aba"` in text (positions 0-2):**

```
hash("aba") = (1 * 26^2 + 2 * 26^1 + 1 * 26^0) % MOD
            = (676 + 52 + 1) % MOD
            = 729
```

729 ≠ 1380 → no match.

**Slide window to `"bab"` (positions 1-3):**

```
drop 'a' (leftmost):   729 - 1 * 26^2 = 729 - 676 = 53
shift remaining left:  53 * 26 = 1378
add 'b' (new right):   1378 + 2 = 1380
```

1380 == 1380 → hash match! Verify: `text[1:4] == "bab" == pattern`. **Match confirmed at index 1.**

**Slide to `"abc"` (positions 2-4):**

```
drop 'b':  1380 - 2 * 26^2 = 1380 - 1352 = 28
shift:     28 * 26 = 728
add 'c':   728 + 3 = 731
```

731 ≠ 1380 → no match.

**Slide to `"bcd"` (positions 3-5):** continues similarly, no match.

This is the rolling-hash update formula: subtract the high-order digit multiplied by `BASE^(k-1)`, multiply by `BASE`, add the new character.

## 4. Implementation

```python
from __future__ import annotations
from typing import List

BASE = 257
MOD = 10**9 + 7


def rabin_karp(text: str, pattern: str) -> List[int]:
    """Return all starting indices where pattern occurs in text.

    Uses a single rolling hash with BASE=257 and MOD=10**9+7.
    Always verifies on a hash hit to avoid false positives.
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []

    # Precompute BASE^(m-1) mod MOD — the weight of the leftmost character.
    high_base = pow(BASE, m - 1, MOD)

    # Compute hash of pattern and first window.
    pat_hash = 0
    win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * BASE + ord(pattern[i])) % MOD
        win_hash = (win_hash * BASE + ord(text[i])) % MOD

    results: List[int] = []

    for l in range(n - m + 1):
        if win_hash == pat_hash:
            # Verify to rule out hash collisions.
            if text[l:l + m] == pattern:
                results.append(l)

        # Slide the window: drop text[l], add text[l + m].
        if l + m < n:
            win_hash = (win_hash - ord(text[l]) * high_base) % MOD
            win_hash = (win_hash * BASE + ord(text[l + m])) % MOD
            win_hash %= MOD  # keep positive under Python's signed arithmetic

    return results


if __name__ == "__main__":
    assert rabin_karp("ababcd", "bab") == [1]
    assert rabin_karp("AAAAAA", "AA")  == [0, 1, 2, 3, 4]
    assert rabin_karp("HELLO",  "LL")  == [2]
    assert rabin_karp("HELLO",  "XY")  == []
    assert rabin_karp("abcabc", "abc") == [0, 3]
    assert rabin_karp("", "a")         == []
    assert rabin_karp("a", "")         == [0, 1]

    print("All smoke tests passed.")
```

**Template:**

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

## 5. Variants & pitfalls

### Single-pattern search

Rabin-Karp rarely beats KMP for a single pattern — KMP has no false-positive overhead and a simpler worst case. Rabin-Karp's edge comes when a hash comparison is cheaper than a character-by-character string comparison (e.g., when checking membership in a set of patterns).

### Set of length-k patterns

Hash every pattern into a `set`, then slide one window over the text. Each window costs O(1) to hash and O(1) average for set lookup — the total cost is O(n + sum_of_pattern_lengths), far better than running k separate KMP searches.

### 2D rolling hash for matrix substrings

Hash each row of a k×k submatrix with one rolling hash; hash the column of row-hashes with a second. This finds k×k pattern occurrences in a 2D grid in O(rows × cols) time.

### Double hashing

Use two independent (base, mod) pairs and only report a match when both hashes agree. The probability of a false positive drops from ~1/p to ~1/(p1 × p2). Useful when the input might be adversarially crafted to cause collisions.

### Pitfalls

- **Verify on every hit**: hash equality does not mean string equality. Skipping verification silently produces wrong output on collisions. Always compare `text[l:l+m] == pattern` when hashes match.
- **Negative hashes in Python**: Python's `%` operator keeps results non-negative, but after subtracting `ord(text[l]) * high_base` the intermediate value can be negative. Adding `% MOD` after each step fixes this.
- **Mismatched base and alphabet**: if `BASE` is smaller than the number of distinct character codes, distinct characters can map to the same value mod BASE before the prime is applied, increasing collisions. Using `BASE = 257` covers the full ASCII range.
- **Pre-computing `BASE^(k-1) mod MOD`**: use `pow(BASE, m-1, MOD)` (Python's built-in modular exponentiation) rather than a loop — it is O(log m) and avoids intermediate overflow.

## 6. Complexity

- **Time:** O(n + m) average — O(m) to hash the pattern and first window; O(1) per slide step; O(m) per verification, but collisions are rare (probability ~1/MOD per window). Worst case O(nm) when every window collides.
- **Space:** O(1) beyond the input — only a constant number of hash values and the `high_base` constant are maintained; results list is O(k) where k is the number of matches.

## 7. Problem set

- [Medium] [Repeated DNA Sequences](https://leetcode.com/problems/repeated-dna-sequences/) — slide a length-10 window and collect windows seen more than once; a hash set of rolling hashes avoids hashing strings explicitly.
- [Medium] [Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) — fixed-size window; compare character-count hashes (or a frequency multiset) rather than polynomial hashes, but the sliding-window intuition is identical.
- [Hard] [Longest Duplicate Substring](https://leetcode.com/problems/longest-duplicate-substring/) — binary search on length combined with Rabin-Karp to check if any substring of that length repeats; the rolling hash makes each length-check O(n).
- [Hard] [Distinct Echo Substrings](https://leetcode.com/problems/distinct-echo-substrings/) — count substrings that are the concatenation of two equal halves; rolling hashes over both halves let you check equality in O(1) per position.
- [Hard] [Longest Common Subpath](https://leetcode.com/problems/longest-common-subpath/) — binary search on length; for each candidate length, hash all subpaths of each friend's path and intersect the sets.

## 8. Related patterns

- [KMP](kmp.md) — deterministic O(n + m) substring search with no false positives; prefer KMP for a single fixed pattern where worst-case guarantees matter.
- [Sliding Window](../two-pointers-sliding-window/sliding-window.md) — the rolling-hash technique is a special case of the sliding window pattern; the window shrinks and grows by one character at a time.
- **Z-Algorithm** (`../nice-to-have/z-algorithm.md` — computes prefix-match lengths in O(n) without hashing; often simpler when you need prefix-suffix structure rather than a hash)

## 9. Interviewer follow-ups

**Q: Why use double hashing?**
Adversarial inputs can be constructed to cause O(nm) collisions against a single known (base, mod) pair — the attacker chooses a text where every window hashes to the same value as the pattern. With two independent hashes, the attacker needs to find a string that collides in both simultaneously, which is computationally infeasible with large primes.

**Q: How would you find the longest repeated substring efficiently?**
Binary search on the length L: for each candidate L, run Rabin-Karp to collect all length-L substrings into a hash set. If any hash value appears more than once (verify the actual strings), a repeated substring of length L exists. The binary search runs O(log n) iterations, each O(n), for O(n log n) total. A suffix array gives O(n) after an O(n log n) build — name-drop if asked for asymptotically optimal.
