# Z-Algorithm

## 1. TL;DR

The Z-algorithm computes in O(n) the **Z-array** for a string `s`, where `Z[i]` is the length of the longest substring starting at index `i` that matches a prefix of `s`. The signal is "find pattern in text" (alternative to KMP), "longest happy prefix," or any problem requiring prefix-match lengths at every position. Build it with a sliding `(l, r)` window — the rightmost matching prefix seen — reusing mirror comparisons exactly as Manacher does for palindromes. Time: O(n). Space: O(n).

## 2. Intuition

A naïve scan computes `Z[i]` independently for each position — O(n) per position, O(n²) total. The Z-algorithm cuts this to O(n) by maintaining a window `[l, r)` that represents the rightmost prefix-match found so far.

When computing `Z[i]` with `i < r`, position `i` falls inside the known matching window. Its mirror position `i - l` inside the prefix has already been computed: `Z[i - l]`. If that mirror's match stays within `[l, r)`, we can copy it directly — no comparisons needed. If it reaches or passes `r`, we copy up to `r - i` and then extend character by character past `r`. Every character only pushes `r` forward, never back, so the total number of fresh comparisons across all positions is O(n).

The key payoff: to find all occurrences of pattern `P` in text `T`, build the Z-array of the concatenation `P + '$' + T` (using a sentinel `$` not in either string). Any position `i` in the `T` portion with `Z[i] >= len(P)` is a match start — no separate search loop needed.

## 3. Walkthrough

### Building the Z-array for `s = "aabaab"`

Start: `l = r = 0`. `Z[0] = 6` by convention (the whole string matches its own prefix).

| i | Z[i] | Reasoning |
|---|------|-----------|
| 1 | 1    | `s[1]='a'` matches `s[0]='a'`; `s[2]='b'` vs `s[1]='a'` — mismatch. Z[1]=1. Update window: l=1, r=2. |
| 2 | 0    | `s[2]='b'` vs `s[0]='a'` — mismatch. Z[2]=0. |
| 3 | 3    | `s[3..5]="aab"` matches `s[0..2]="aab"`, index runs out. Z[3]=3. Update window: l=3, r=6. |
| 4 | 1    | i=4 < r=6; mirror = 4−3=1, Z[1]=1; 4+1=5 ≤ r=6 → copy: Z[4]=1. (No extension needed.) |
| 5 | 0    | i=5 < r=6; mirror = 5−3=2, Z[2]=0 → copy: Z[5]=0. Check: `s[5]='b'` vs `s[0]='a'` — mismatch, confirms 0. |

Final Z-array: `[6, 1, 0, 3, 1, 0]`.

### Pattern matching via sentinel concatenation

To find pattern `P = "aab"` in `T = "aabaab"`, build:

```
combined = "aab$aabaab"
Z        = [10, 1, 0, 0, 3, 1, 0, 3, 1, 0]
```

Positions ≥ 4 (i.e., in the text portion) with `Z[i] >= 3`:
- i=4 → text position 4−3−1=0: match at index 0
- i=7 → text position 7−3−1=3: match at index 3

So `P` occurs at indices 0 and 3 in `T`. Verified: `T[0:3]="aab"`, `T[3:6]="aab"`. Correct.

## 4. Implementation

```python
from __future__ import annotations


def z_function(s: str) -> list[int]:
    """Return the Z-array of s.

    Z[0] = len(s) by convention.
    Z[i] = length of the longest substring starting at s[i] that matches a
           prefix of s.
    """
    n = len(s)
    if n == 0:
        return []
    Z = [0] * n
    Z[0] = n
    l = r = 0  # window [l, r) is the rightmost prefix-match seen so far
    for i in range(1, n):
        if i < r:
            # Mirror position inside the known window: reuse already-computed value.
            Z[i] = min(r - i, Z[i - l])
        # Extend past the known boundary (or from scratch when i >= r).
        while i + Z[i] < n and s[Z[i]] == s[i + Z[i]]:
            Z[i] += 1
        # Update window if this match extends further right.
        if i + Z[i] > r:
            l, r = i, i + Z[i]
    return Z


def z_search(text: str, pattern: str) -> list[int]:
    """Return all start indices where pattern occurs in text.

    Concatenates pattern + '$' + text and scans for Z[i] >= len(pattern).
    The sentinel '$' must not appear in pattern or text.
    Time: O(|pattern| + |text|). Space: O(|pattern| + |text|).
    """
    if not pattern:
        return list(range(len(text) + 1))
    m = len(pattern)
    combined = pattern + "$" + text
    Z = z_function(combined)
    results = []
    for i in range(m + 1, len(combined)):
        if Z[i] >= m:
            results.append(i - m - 1)  # map back to text index
    return results


if __name__ == "__main__":
    # Z-array smoke test: Z[0] = n by convention.
    assert z_function("aabaab") == [6, 1, 0, 3, 1, 0], f"got {z_function('aabaab')}"

    # Matching test.
    assert z_search("ababab", "ab") == [0, 2, 4], f"got {z_search('ababab', 'ab')}"

    # Pattern not present in text.
    result = z_search("aabxaabxcaabxaabxay", "aabxaaby")
    assert result == [], f"expected [], got {result}"

    print("All smoke tests passed.")
```

**Template:**

```python
def z_function(s: str) -> list[int]:
    n = len(s)
    if n == 0:
        return []
    Z = [0] * n
    Z[0] = n
    l = r = 0
    for i in range(1, n):
        if i < r:
            Z[i] = min(r - i, Z[i - l])
        while i + Z[i] < n and s[Z[i]] == s[i + Z[i]]:
            Z[i] += 1
        if i + Z[i] > r:
            l, r = i, i + Z[i]
    return Z


def z_search(text: str, pattern: str) -> list[int]:
    if not pattern:
        return list(range(len(text) + 1))
    m = len(pattern)
    Z = z_function(pattern + "$" + text)
    return [i - m - 1 for i in range(m + 1, len(Z)) if Z[i] >= m]
```

## 5. Variants & pitfalls

### Z-array for matching (sentinel concatenation)

The canonical pattern: `combined = P + '$' + T`. Any index `i` in the `T` portion where `Z[i] >= len(P)` is a match. The sentinel prevents the Z-value from incorrectly "bleeding" across the boundary.

### Suffix array (name-drop)

For multi-pattern or substring-heavy problems, a **suffix array** (with LCP array) is more powerful than Z or KMP — supports all-substring queries in O(n log n) build time — but is significantly heavier to implement in an interview setting.

### Pitfalls

- **Sentinel choice**: `$` must not appear in P or T; otherwise a Z-value can span the boundary and produce a false positive. For arbitrary inputs, use a character outside the input alphabet or a separator object (e.g., `None` in a list comparison).
- **Off-by-one in window update**: only update `(l, r)` when `i + Z[i] > r`; updating unconditionally overwrites a valid, further-right window.
- **Z[0] is a special case**: by convention `Z[0] = n` (the whole string trivially matches its own prefix). Skip index 0 when scanning for matches or the search loop will always report a spurious hit.
- **Confusing l/r semantics**: `r` is the exclusive right end of the window (`s[l:r]` matches `s[0:r-l]`), so the copy condition is `i < r` and the mirror is `i - l`.

## 6. Complexity

- **Time:** O(n) — each character can advance `r` at most once; total fresh comparisons are bounded by `r` moving from 0 to `n`.
- **Space:** O(n) — the Z-array is the only auxiliary structure; for matching, the concatenated string adds `O(|P| + |T|)`.

## 7. Problem set

- [Medium] [Find the Index of the First Occurrence in a String](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) — canonical substring search; KMP or Z both work; good to implement both and compare.
- [Hard] [Longest Happy Prefix](https://leetcode.com/problems/longest-happy-prefix/) — the answer is the prefix of length equal to the last non-zero Z-value (or equivalently KMP's `lps[-1]`); Z-array makes this direct.
- [Hard] [Sum of Scores of Built Strings](https://leetcode.com/problems/sum-of-scores-of-built-strings/) — asks for the sum of Z-values (including Z[0]=n); the Z-array is the direct answer.

## 8. Related patterns

- [KMP](../strings/kmp.md) — main alternative for string matching; builds an LPS array instead of a Z-array; no concatenation needed, slightly less auxiliary space, but conceptually heavier to derive.
- [Rabin-Karp](../strings/rabin-karp.md) — hash-based matching alternative; wins when matching a set of patterns simultaneously via a hash set.

## 9. Interviewer follow-ups

**Q: Z vs KMP — when to use which?**
Z-array is conceptually simpler and naturally provides prefix-match lengths at every position, which makes problems like "Longest Happy Prefix" and "Sum of Scores" trivial. KMP avoids the sentinel-concatenation step and uses O(m) auxiliary space instead of O(m + n), which can matter if the text is streamed. In practice, either works for standard substring search; pick whichever you can code from memory more reliably.

**Q: How does the window update prevent O(n²) behavior?**
`r` only ever moves right — never left. Each character in `s` can trigger at most one fresh comparison that advances `r`. Since `r` starts at 0 and ends at most at `n`, the total number of fresh comparisons across the entire loop is bounded by `n`.
