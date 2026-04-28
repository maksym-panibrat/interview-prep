# Trie

## 1. TL;DR

A trie (prefix tree) is a tree where each root-to-node path spells out a prefix and each node holds children plus an end-of-word marker. The signal is **prefix matching**, autocomplete, "word search II," dictionary lookups with wildcards, multi-pattern search, or longest-common-prefix queries. Every `insert`, `search`, and `startsWith` is O(L) where L is the word length — independent of how many words are stored. Space: O(N · L) worst case.

## 2. Intuition

A hashset can tell you whether an exact word exists, but it cannot tell you whether any stored word starts with a given prefix without scanning all words. A trie encodes that prefix information structurally: every character on a root-to-node path is shared by all words that begin with that prefix. Traversing to a node takes O(L) steps regardless of dictionary size; once there, every word reachable from that node shares the same prefix.

Each node holds:
1. A mapping from character to child node (dict, or fixed-size array for small alphabets).
2. An end-of-word flag (or sentinel key `"*"` in the dict).

`search(word)` differs from `startsWith(prefix)` in exactly one way: `search` requires the flag to be set at the final node; `startsWith` returns True as soon as the traversal succeeds.

## 3. Walkthrough

### Insert `["cat", "car", "card", "dog"]`

After all four inserts the trie looks like this:

```
(root)
├── c
│   └── a
│       ├── t [*]          ← "cat" ends here
│       └── r [*]          ← "car" ends here
│           └── d [*]      ← "card" ends here
└── d
    └── o
        └── g [*]          ← "dog" ends here
```

`[*]` marks a node where `is_end = True`.

### `startsWith("ca")` → True

Traverse: root → `c` → `a`. Both nodes exist. Return **True** — there are words with this prefix.

### `search("ca")` → False

Traverse: root → `c` → `a`. Node exists, but `is_end` on the `a` node is **False** — "ca" was never inserted. Return **False**.

### `search("cat")` → True

Traverse: root → `c` → `a` → `t`. Node exists and `is_end` is **True**. Return **True**.

## 4. Implementation

```python
from __future__ import annotations
from typing import Dict


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: Dict[str, TrieNode] = {}
        self.is_end: bool = False


class Trie:
    """Dict-of-dicts trie supporting insert, search, and startsWith."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        """Return True iff word was inserted exactly."""
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def startsWith(self, prefix: str) -> bool:
        """Return True iff any inserted word starts with prefix."""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True


if __name__ == "__main__":
    t = Trie()
    for word in ["cat", "car", "card", "dog"]:
        t.insert(word)

    # prefix queries
    assert t.startsWith("ca") is True
    assert t.startsWith("do") is True
    assert t.startsWith("xy") is False

    # exact lookups
    assert t.search("cat")  is True
    assert t.search("car")  is True
    assert t.search("card") is True
    assert t.search("dog")  is True
    assert t.search("ca")   is False   # prefix only, no end-of-word marker
    assert t.search("cats") is False
    assert t.search("do")   is False

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import Dict


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
```

## 5. Variants & pitfalls

### Dict-of-dicts vs class-based with array children

Dict-of-dicts (shown above) is flexible for arbitrary alphabets and uses only as much memory as words actually inserted. For a fixed lowercase-only alphabet, a 26-element `children` array avoids dict overhead at the cost of 26 pointers per node — fine when node count is small, wasteful when the trie is sparse.

### Sentinel key `"*"` instead of `is_end`

Some implementations use `children["*"] = None` to mark end-of-word. It avoids a separate attribute but conflates children with the terminator — be consistent.

### Trie + DFS (Word Search II)

Combine a board DFS with a trie of target words: prune the DFS branch early whenever the current path prefix is not in the trie. This turns an O(4^(R·C) · W) brute force into O(4^(R·C) · L) where L is the maximum word length and R·C is the board size.

### Bitwise trie for max-XOR problems

Each node has exactly two children (bit `0` and bit `1`). Insert integers bit by bit from the MSB. For max XOR, greedily traverse the opposite bit at each node.

### Compressed trie / radix tree

Merge chains of single-child nodes into edge labels. Reduces node count from O(total characters) to O(number of words) at the cost of more complex insert/search logic. Name-drop in interviews; implementing it under time pressure is rarely required.

### Pitfalls

- **Forgetting `is_end`**: if you only check whether the traversal succeeds, `search("ca")` returns True even though "ca" was never inserted — because the `a` node exists as a prefix of "cat" and "car". Always check `node.is_end` at the end of `search`.
- **Memory blowup with large alphabets**: a 26-element array per node wastes memory when most slots are empty. Use a dict unless you know the alphabet is dense.
- **Using a trie when a hashset suffices**: tries win on *prefix* queries and *enumeration* of words with a shared prefix. For plain exact-word lookup, a `set` or `dict` is simpler and has better constant factors. Always ask whether the problem actually needs prefix queries before reaching for a trie.

## 6. Complexity

- **Time:** O(L) per insert, search, and startsWith — each operation traverses at most L nodes, one per character.
- **Space:** O(N · L) worst case where N is the number of inserted words and L is the average length — in the worst case (no shared prefixes) each word creates L new nodes.

## 7. Problem set

- [Easy] [Longest Common Prefix](https://leetcode.com/problems/longest-common-prefix/) — insert all strings and walk the trie until a node has more than one child or is an end-of-word; the depth at that point is the LCP length.
- [Medium] [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/) — the canonical trie implementation problem; covers insert, search, and startsWith exactly as in this file.
- [Medium] [Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/) — extends basic trie with wildcard `.` matching via DFS over the trie.
- [Medium] [Map Sum Pairs](https://leetcode.com/problems/map-sum-pairs/) — each node stores an accumulated sum; `sum(prefix)` traverses to the prefix node and returns its stored value.
- [Medium] [Replace Words](https://leetcode.com/problems/replace-words/) — insert all roots into a trie, then for each word in the sentence search for the shortest matching root.
- [Medium] [Longest Word in Dictionary](https://leetcode.com/problems/longest-word-in-dictionary/) — BFS/DFS the trie, only visiting nodes where every prefix along the path is a complete word (is_end = True at each ancestor).
- [Hard] [Word Search II](https://leetcode.com/problems/word-search-ii/) — classic trie + board DFS; prune backtracking when the current path is not in the trie.
- [Hard] [Maximum XOR of Two Numbers in an Array](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/) — bitwise trie; insert all numbers and greedily traverse the opposite-bit branch to maximize XOR.
- [Hard] [Stream of Characters](https://leetcode.com/problems/stream-of-characters/) — suffix trie or Aho-Corasick over a reversed dictionary; each incoming character advances pointers through the trie.
- [Hard] [Word Squares](https://leetcode.com/problems/word-squares/) — use a prefix-to-words index (trie variant) to prune the backtracking search for valid squares.
- [Hard] [Concatenated Words](https://leetcode.com/problems/concatenated-words/) — trie + DFS/DP to check whether each word can be formed from shorter words in the dictionary.
- [Hard] [Palindrome Pairs](https://leetcode.com/problems/palindrome-pairs/) — trie over reversed words; for each word check for palindrome prefixes/suffixes that complete a palindrome pair.

## 8. Related patterns

- [KMP](kmp.md) — Aho-Corasick is multi-pattern KMP built on top of a trie; reach for it when you need to match many patterns simultaneously in a single pass over the text.
- [DFS](../graphs/dfs.md) — trie traversal (Word Search II, wildcard search) is a DFS over the trie nodes; understanding DFS makes trie-based backtracking natural.
- **[Grid Backtracking](../backtracking/grid-search.md)** — Word Search II combines board DFS with a trie; grid search provides the outer backtracking framework.

## 9. Interviewer follow-ups

**Q: How do you handle wildcard search where `.` matches any character?**
At each node, if the current pattern character is `.`, branch into every child (DFS over all children). If it is a specific character, follow only that child. Mark found words as you hit `is_end` nodes. This gives O(26^d) worst case where d is the number of wildcards, but in practice the trie prunes most branches early.

**Q: Memory-tight implementation?**
Use a class-based node with `__slots__` to eliminate per-instance `__dict__` overhead (already done above). For lowercase-only input, a 26-element array of child pointers reduces dict overhead — each node allocates exactly 26 slots regardless of actual children. Trade-off: saves per-lookup hash cost but wastes memory on sparse tries.

**Q: Auto-complete top-3 results by frequency?**
Three options: (1) each node stores a sorted list of the top-k (word, frequency) pairs, updated on insert — O(k) update, O(1) query; (2) each node stores only the count of insertions in its subtree, then do a DFS from the prefix node collecting words and sorting at query time — O(output) per query; (3) each node holds a min-heap of size k — O(log k) per insert, O(k) per query.
