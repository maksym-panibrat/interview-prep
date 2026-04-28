"""Trie (prefix tree) — see topics/strings/trie.md for full reference."""
from typing import Dict, List, Optional


# Style 1: dict-of-dicts — flexible alphabet, memory-proportional to insertions
class Trie:
    def __init__(self) -> None:
        self.root: Dict = {}

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["*"] = True  # end-of-word sentinel

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node:
                return False
            node = node[ch]
        return "*" in node

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            if ch not in node:
                return False
            node = node[ch]
        return True


# Style 2: 26-element children array — lowercase alphabet only, avoids dict overhead
class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: List[Optional["TrieNode"]] = [None] * 26  # fixed allocation cost
        self.is_end: bool = False


class TrieArray:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            idx = ord(ch) - ord("a")
            if node.children[idx] is None:
                node.children[idx] = TrieNode()
            node = node.children[idx]  # type: ignore[assignment]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            idx = ord(ch) - ord("a")
            if node.children[idx] is None:
                return False
            node = node.children[idx]  # type: ignore[assignment]
        return node.is_end

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            idx = ord(ch) - ord("a")
            if node.children[idx] is None:
                return False
            node = node.children[idx]  # type: ignore[assignment]
        return True
