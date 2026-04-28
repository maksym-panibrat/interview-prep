# Manacher's Algorithm

## 1. TL;DR

Manacher's algorithm finds the **longest palindromic substring** (and counts all palindromic substrings) in O(n) time. The signal is "palindromic substring" when expand-around-center's O(n²) is too slow, or when an O(n) guarantee is explicitly required. Inserts separator characters to unify even/odd palindromes, then exploits a "current rightmost palindrome" to skip redundant comparisons. Time: O(n). Space: O(n).

## 2. Intuition

Expand-around-center computes the palindrome radius at every position independently — O(n) positions each taking up to O(n) time. Manacher cuts this to O(n) by reusing work already done.

Maintain a **center `c`** and its **right boundary `r`** — the palindrome centered at `c` that reaches furthest to the right. When computing the radius at a new position `i < r`, the mirror position `m = 2c - i` is already known. Because T[c-k] == T[c+k] for all k up to the radius, the radius at `i` is at least `min(P[m], r - i)`. Only characters past `r` need fresh comparisons. Each character can only push `r` to the right — never left — so the total number of fresh comparisons is O(n).

The **separator trick** (`#a#b#...#`) ensures every position has uniform parity: all palindromes in the transformed string T are odd-length, so a single loop handles both even- and odd-length palindromes in the original string.

## 3. Walkthrough

Transform `s = "abacaba"` by inserting `#` at boundaries and between characters:

```
T = # a # b # a # c # a # b # a #
i = 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
```

Compute `P[i]` = palindrome radius at `T[i]` (number of matching characters on each side):

| i  | T[i] | P[i] | Notes                                                          |
|----|------|------|----------------------------------------------------------------|
| 0  | #    | 0    | boundary                                                       |
| 1  | a    | 1    | expands to `#a#`                                               |
| 2  | #    | 0    |                                                                |
| 3  | b    | 1    | expands to `#b#`                                               |
| 4  | #    | 2    | expands to `#a#b#a#`; r advances to 6                         |
| 5  | a    | 1    | mirror of i=3 (m=3); P[3]=1, r-i=1 → start=1, no new chars   |
| 6  | #    | 6    | expands full left; r advances to 12                           |
| 7  | c    | 7    | center of whole string; r advances to 14 (end of T)           |
| 8  | #    | 6    | mirror of i=6 (m=6); P[6]=6, r-i=6 → no new comparisons      |
| 9  | a    | 1    | mirror of i=5; start=1                                        |
| 10 | #    | 2    | mirror of i=4; start=2                                        |
| 11 | b    | 1    | mirror of i=3                                                  |
| 12 | #    | 0    |                                                                |
| 13 | a    | 1    | mirror of i=1                                                  |
| 14 | #    | 0    |                                                                |

Maximum `P[i]` is 7 at i=7. Map back: `start = (7 - 7) // 2 = 0`, length = 7, so `s[0:7] = "abacaba"`. Positions 8–14 required zero fresh comparisons — all initialized from their mirrors.

## 4. Implementation

```python
from __future__ import annotations


def manacher(s: str) -> tuple[int, str]:
    """Return (length, longest_palindromic_substring) in O(n) time."""
    if not s:
        return 0, ""

    # Transform: insert '#' separators so all palindromes are odd-length.
    T = "#" + "#".join(s) + "#"
    n = len(T)
    P = [0] * n        # P[i] = palindrome radius at T[i]
    c = r = 0          # center and right boundary of rightmost palindrome so far

    for i in range(n):
        if i < r:
            mirror = 2 * c - i
            # Use mirror's radius, but don't go past the known boundary.
            P[i] = min(P[mirror], r - i)
        # Attempt to expand past the known boundary (or from scratch if i >= r).
        lo, hi = i - (P[i] + 1), i + (P[i] + 1)
        while lo >= 0 and hi < n and T[lo] == T[hi]:
            P[i] += 1
            lo -= 1
            hi += 1
        # Update rightmost palindrome if this one extends further right.
        if i + P[i] > r:
            c, r = i, i + P[i]

    # Find the position with largest radius.
    best_i = max(range(n), key=lambda x: P[x])
    length = P[best_i]
    # Map back to original string indices.
    start = (best_i - length) // 2
    return length, s[start: start + length]


def expand_around_center(s: str) -> tuple[int, str]:
    """Return (length, longest_palindromic_substring) in O(n^2) time.

    Simpler fallback; sufficient for most interview settings.
    """
    if not s:
        return 0, ""

    best_start = 0
    best_len = 1

    def expand(lo: int, hi: int) -> None:
        nonlocal best_start, best_len
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        # After the loop, the palindrome is s[lo+1 : hi].
        length = hi - lo - 1
        if length > best_len:
            best_len = length
            best_start = lo + 1

    for mid in range(len(s)):
        expand(mid, mid)      # odd-length palindromes
        expand(mid, mid + 1)  # even-length palindromes

    return best_len, s[best_start: best_start + best_len]


if __name__ == "__main__":
    # Smoke tests — both implementations must agree.
    cases = [
        ("babad",   3),   # "bab" or "aba"
        ("cbbd",    2),   # "bb"
        ("abacaba", 7),   # "abacaba"
        ("a",       1),
        ("",        0),
        ("racecar", 7),
    ]
    for s, expected_len in cases:
        ml, ms = manacher(s)
        el, es = expand_around_center(s)
        assert ml == expected_len, f"manacher({s!r}): expected len {expected_len}, got {ml}"
        assert el == expected_len, f"expand({s!r}): expected len {expected_len}, got {el}"
        # Both answers must actually be palindromes of the claimed length.
        assert ms == ms[::-1] and len(ms) == ml, f"manacher result not palindrome: {ms!r}"
        assert es == es[::-1] and len(es) == el, f"expand result not palindrome: {es!r}"
    print("All smoke tests passed.")
```

**Template:**

```python
def manacher(s: str) -> tuple[int, str]:
    if not s:
        return 0, ""
    T = "#" + "#".join(s) + "#"
    n = len(T)
    P = [0] * n
    c = r = 0
    for i in range(n):
        if i < r:
            P[i] = min(P[2 * c - i], r - i)
        lo, hi = i - (P[i] + 1), i + (P[i] + 1)
        while lo >= 0 and hi < n and T[lo] == T[hi]:
            P[i] += 1
            lo -= 1
            hi += 1
        if i + P[i] > r:
            c, r = i, i + P[i]
    best_i = max(range(n), key=lambda x: P[x])
    length = P[best_i]
    start = (best_i - length) // 2
    return length, s[start: start + length]
```

## 5. Variants & pitfalls

### Expand-around-center (O(n²) fallback)

For most interview problems (LeetCode 5, 647) this is fast enough and much simpler to code under pressure. Use Manacher only when O(n²) is explicitly too slow or the problem requires O(n).

### Counting palindromic substrings (LeetCode 647)

With the separator transform, `(P[i] + 1) // 2` gives the number of palindromic substrings centered at T[i] that correspond to original-string substrings. Summing over all i gives the total count in O(n).

### Shortest Palindrome (LeetCode 214)

Concatenate `s + "#" + reversed(s)` and run KMP (or Manacher) to find the longest palindromic prefix of s. Prepend the remaining suffix reversed to make the whole string a palindrome.

### Pitfalls

- **Forgetting the separator**: Without `#`, even-length palindromes have no center character and are missed entirely by a single loop.
- **Wrong separator character**: The separator must not appear in the input alphabet. `#` is safe for lowercase-letter problems; for arbitrary Unicode use a character outside the input range or a sentinel object.
- **Off-by-one when extracting the result**: In T the palindrome at `i` with radius `P[i]` maps back to `start = (i - P[i]) // 2`, `end = start + P[i]`. T has length `2n + 1`.
- **Not updating `c, r` correctly**: Only update when `i + P[i] > r`. Updating unconditionally is wrong and breaks the mirror guarantee.

## 6. Complexity

- **Time:** O(n) — each character in T is a "right-boundary" expansion at most once; the total comparisons across all expansions is bounded by the number of times `r` advances, which is at most `len(T) = 2n + 1`.
- **Space:** O(n) — the transformed string T and the radius array P are both length 2n + 1.

## 7. Problem set

- [Medium] [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) — canonical application; expand-around-center usually passes, but Manacher gives O(n).
- [Medium] [Palindromic Substrings](https://leetcode.com/problems/palindromic-substrings/) — count all palindromic substrings; Manacher yields the count in O(n) via `sum((P[i] + 1) // 2)`.
- [Hard] [Shortest Palindrome](https://leetcode.com/problems/shortest-palindrome/) — find the longest palindromic prefix then prepend the remainder reversed; solvable with KMP or Manacher.
- [Hard] [Palindrome Pairs](https://leetcode.com/problems/palindrome-pairs/) — all pairs (i, j) where `words[i] + words[j]` is a palindrome; trie + palindrome-check is standard, but Manacher helps analyze substrings efficiently.

## 8. Related patterns

- [KMP](../strings/kmp.md) — alternative O(n) string algorithm; can solve Shortest Palindrome via the `s + "#" + reversed(s)` concatenation trick.
- [Interval DP](../dp/interval-dp.md) — palindromic subsequence problems (e.g., Longest Palindromic Subsequence) use interval DP; a different family but shares the palindrome theme.

## 9. Interviewer follow-ups

**Q: Why does Manacher beat expand-around-center?**
Expand-around-center recomputes overlapping palindromes from scratch at every center. Manacher reuses already-computed radii via the mirror property: if `i < r`, `P[i]` is at least `min(P[mirror], r - i)` — no work needed for characters already proven to match. Only characters past `r` require new comparisons, and `r` only moves right, so total comparisons are O(n).

**Q: If asked, can you sketch it?**
Three key ideas: (1) separator trick — insert `#` between every character so even/odd palindromes unify into odd-length ones; (2) maintain `(c, r)` — center and right boundary of the rightmost palindrome seen; (3) mirror initialization — for `i < r`, set `P[i] = min(P[2c-i], r-i)`, then expand only past `r`. That is the whole algorithm.
