# KMP

## 1. TL;DR

KMP (Knuth-Morris-Pratt) finds all occurrences of a pattern of length m inside a text of length n in O(n + m) time. The signal is "find pattern in text," substring search where naïve O(nm) is too slow, or any problem that involves the **longest proper prefix that is also a suffix** (LPS) of a string. Key idea: precompute an LPS array for the pattern so that on a mismatch you know how far back in the pattern to jump — without ever rewinding the text pointer. Time: O(n + m). Space: O(m).

## 2. Intuition

Imagine you are matching the pattern `ABABC` against a text, and after matching four characters `ABAB` the next text character doesn't match `C`. Naïve search discards everything and restarts one position later. KMP notices that the matched prefix `ABAB` ends with `AB`, which is also a prefix of the pattern. So the next comparison can start from position 2 of the pattern (`C` after the prefix `AB`) rather than from position 0 — the text pointer never moves backward.

The **LPS array** (Longest Proper Prefix that is also a Suffix) encodes this shortcut for every position in the pattern. `lps[i]` is the length of the longest proper prefix of `pattern[:i+1]` that is also a suffix. On a mismatch at pattern position `j`, reset `j = lps[j-1]` and retry; only when `j == 0` do you advance the text pointer without a match.

## 3. Walkthrough

### Building the LPS array for `pattern = "ABABCABAB"`

Start with `lps = [0] * 9`, `length = 0` (length of current longest prefix-suffix), `i = 1`.

```
pattern: A  B  A  B  C  A  B  A  B
index:   0  1  2  3  4  5  6  7  8
lps:     0  0  1  2  0  1  2  3  4
```

Step-by-step transitions:

| i | pattern[i] | length | pattern[length] | action                          | lps[i] |
|---|-----------|--------|-----------------|----------------------------------|--------|
| 1 | B         | 0      | A               | mismatch, length==0 → lps[1]=0, i=2 | 0  |
| 2 | A         | 0      | A               | match → length=1, lps[2]=1, i=3  | 1      |
| 3 | B         | 1      | B               | match → length=2, lps[3]=2, i=4  | 2      |
| 4 | C         | 2      | A               | mismatch, length→lps[1]=0; mismatch again, length==0 → lps[4]=0, i=5 | 0 |
| 5 | A         | 0      | A               | match → length=1, lps[5]=1, i=6  | 1      |
| 6 | B         | 1      | B               | match → length=2, lps[6]=2, i=7  | 2      |
| 7 | A         | 2      | A               | match → length=3, lps[7]=3, i=8  | 3      |
| 8 | B         | 3      | B               | match → length=4, lps[8]=4, done | 4      |

Final: `lps = [0, 0, 1, 2, 0, 1, 2, 3, 4]`.

### Searching `pattern = "ABABCABAB"` in `text = "ABABCABABABABCABAB"`

```
text:    A  B  A  B  C  A  B  A  B  A  B  A  B  C  A  B  A  B
index:   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17
```

- `i=0..8`: pattern fully matches starting at text[0]. Match found at index **0**. Resume: `j = lps[8] = 4`.
- `i=9..`: with `j=4` (pattern at `C`), text[9]=`A` vs pattern[4]=`C` → mismatch. `j = lps[3] = 2`. text[9]=`A` vs pattern[2]=`A` → match, continue.
- Eventually pattern fully matches again starting at text[9]. Match found at index **9**.
- Continue from `j = lps[8] = 4` into the remaining text; the third match is found at index **14** (`ABABCABABAB` ... `ABABCABAB`).

The text pointer `i` never decreased — the LPS let us skip redundant comparisons.

## 4. Implementation

```python
from __future__ import annotations
from typing import List


def compute_lps(pattern: str) -> List[int]:
    """Build the LPS (Longest Proper Prefix that is also a Suffix) array.

    lps[i] = length of the longest proper prefix of pattern[:i+1] that is
             also a suffix.  'Proper' means the prefix/suffix is not the
             whole string itself.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0  # length of the current longest prefix-suffix
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                # Fall back: try the next shorter prefix-suffix.
                # Do NOT increment i here — retry the same i with shorter length.
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> List[int]:
    """Return all starting indices where pattern occurs in text.

    Uses the KMP algorithm: O(n + m) time, O(m) space.
    """
    if not pattern:
        return list(range(len(text) + 1))
    n, m = len(text), len(pattern)
    lps = compute_lps(pattern)
    results: List[int] = []
    j = 0  # index into pattern
    i = 0  # index into text
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            results.append(i - j)
            # Resume search: jump back by lps[j-1] positions in pattern.
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]  # don't move i; retry at shorter prefix
            else:
                i += 1
    return results


if __name__ == "__main__":
    # LPS smoke test
    assert compute_lps("ABABCABAB") == [0, 0, 1, 2, 0, 1, 2, 3, 4]
    assert compute_lps("AABAABAAA") == [0, 1, 0, 1, 2, 3, 4, 5, 2]
    assert compute_lps("ABCABC")   == [0, 0, 0, 1, 2, 3]
    assert compute_lps("A")        == [0]

    # Search smoke tests
    matches = kmp_search("ABABCABABABABCABAB", "ABABCABAB")
    assert matches == [0, 9], f"got {matches}"

    assert kmp_search("AAAAAA", "AA") == [0, 1, 2, 3, 4]
    assert kmp_search("HELLO", "LL")  == [2]
    assert kmp_search("HELLO", "XY")  == []

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import List


def compute_lps(pattern: str) -> List[int]:
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> List[int]:
    if not pattern:
        return list(range(len(text) + 1))
    n, m = len(text), len(pattern)
    lps = compute_lps(pattern)
    results: List[int] = []
    i = j = 0
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            results.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return results
```

## 5. Variants & pitfalls

### Classic substring search

`kmp_search` returns all starting indices. For "find the first occurrence only" (LeetCode 28), return on the first append. The text pointer `i` never rewinds, so the total number of character comparisons is at most 2(n + m).

### LPS for "Longest Happy Prefix" (LeetCode 1392)

The answer is the prefix (not the whole string) of length `lps[-1]` — just call `compute_lps` and return `s[:lps[-1]]`. The LPS array itself is the answer.

### Checking if a string is a rotation / repetition

A string `s` is a repetition `a + a + ...` if and only if `len(s) % (len(s) - lps[-1]) == 0` **and** `len(s) - lps[-1] < len(s)`. The period of the shortest repetition unit is `len(s) - lps[-1]`.

### Pitfalls

- **Off-by-one in LPS construction**: when `pattern[i] != pattern[length]` and `length != 0`, set `length = lps[length - 1]` without incrementing `i`. Beginners often add `i += 1` here, which skips characters and produces a wrong LPS.
- **Conflating LPS index with length**: `lps[i]` is a *length*, not an index. To jump back in the pattern on a mismatch, use `j = lps[j - 1]`, not `j = lps[j]`.
- **When not to use KMP**: if the pattern is very short, naïve search or Python's built-in `str.find` is simpler and fast enough. If you need to match a *set* of patterns, use Aho-Corasick (KMP on a trie) or Rabin-Karp with a hash set. If you only need prefix-suffix lengths (not search), the Z-function is often cleaner to code.

## 6. Complexity

- **Time:** O(n + m) — the LPS array is built in O(m); the search loop advances `i` at most n times and `j` can only fall back as many times as it has advanced, so total character comparisons are O(n + m).
- **Space:** O(m) — only the LPS array of length m is kept; the text is scanned in a single pass with O(1) extra state.

## 7. Problem set

- [Medium] [Find the Index of the First Occurrence in a String](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) — canonical KMP application; forces you to implement the full algorithm rather than calling `str.find`.
- [Medium] [Repeated Substring Pattern](https://leetcode.com/problems/repeated-substring-pattern/) — uses the period-detection property: `len(s) % (len(s) - lps[-1]) == 0` when the string is a repetition.
- [Medium] [Longest Happy Prefix](https://leetcode.com/problems/longest-happy-prefix/) — the answer is exactly `s[:lps[-1]]`; tests whether you understand what the LPS array means.
- [Hard] [Shortest Palindrome](https://leetcode.com/problems/shortest-palindrome/) — find the longest palindromic prefix via KMP on `s + "#" + reversed(s)`; illustrates how KMP solves non-obvious string problems.
- [Hard] [Sum of Scores of Built Strings](https://leetcode.com/problems/sum-of-scores-of-built-strings/) — alternatively solved with the Z-function, but the LPS / KMP family applies; demands careful prefix-scoring logic.

## 8. Related patterns

- **[Rabin-Karp](rabin-karp.md)** — hash-based alternative; wins when matching a set of patterns via hash-set lookup rather than one fixed pattern.
- **[Z-Algorithm](../nice-to-have/z-algorithm.md)** — often simpler to code for prefix-matching tasks; computes similar information to KMP from a different angle.
- **[Trie](trie.md)** — Aho-Corasick is multi-pattern KMP built on top of a trie; reach for it when you need to match many patterns simultaneously.

## 9. Interviewer follow-ups

**Q: How would you find all occurrences, not just the first?**
Continue past each match using `j = lps[j - 1]` instead of resetting `j = 0`. The current implementation already does this — `results.append(i - j)` then resumes with `j = lps[j - 1]`, so overlapping matches (e.g., "AA" in "AAAA") are found correctly.

**Q: Multiple patterns at once?**
Use **Aho-Corasick**: build a trie of all patterns, then compute failure links on the trie nodes (exactly the LPS/failure function generalized to a trie). You get O(n + total_pattern_length + number_of_matches) — a single pass over the text matches all patterns simultaneously.
