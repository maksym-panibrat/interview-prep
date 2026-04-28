"""Topological sort templates — see topics/graphs/topological-sort.md for full explanation."""
from collections import deque
from typing import Dict, List, Optional


def kahn(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    in_degree = [0] * n
    for u in range(n):
        for v in graph.get(u, []):
            in_degree[v] += 1
    queue: deque = deque(i for i in range(n) if in_degree[i] == 0)
    result: List[int] = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    return result if len(result) == n else None


def dfs_topo(graph: Dict[int, List[int]], n: int) -> Optional[List[int]]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n
    result: List[int] = []

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        result.append(u)
        return False

    for i in range(n):
        if color[i] == WHITE:
            if dfs(i):
                return None
    result.reverse()
    return result
