"""DFS templates — see topics/graphs/dfs.md for full explanation."""
import sys
from typing import Dict, List, Optional, Set


def dfs_recursive(graph: Dict[int, List[int]], start: int, visited: Optional[Set[int]] = None) -> List[int]:
    if visited is None:
        visited = set()
    visited.add(start)
    order = [start]
    for nb in graph.get(start, []):
        if nb not in visited:
            order.extend(dfs_recursive(graph, nb, visited))
    return order


def dfs_iterative(graph: Dict[int, List[int]], start: int) -> List[int]:
    visited: Set[int] = set()
    stack = [start]
    order: List[int] = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nb in reversed(graph.get(node, [])):
            if nb not in visited:
                stack.append(nb)
    return order


def has_cycle_directed(graph: Dict[int, List[int]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[int, int] = {}
    for u in graph:
        color[u] = WHITE
        for v in graph[u]:
            if v not in color:
                color[v] = WHITE

    def dfs(u: int) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    return any(dfs(n) for n in list(color) if color[n] == WHITE)


def connected_components(graph: Dict[int, List[int]]) -> List[List[int]]:
    visited: Set[int] = set()
    components: List[List[int]] = []
    all_nodes: Set[int] = set(graph.keys())
    for nbs in graph.values():
        all_nodes.update(nbs)
    for node in sorted(all_nodes):
        if node not in visited:
            comp: List[int] = []
            stack = [node]
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                comp.append(u)
                for v in graph.get(u, []):
                    if v not in visited:
                        stack.append(v)
            components.append(sorted(comp))
    return components
