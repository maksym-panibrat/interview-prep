"""Dijkstra templates — see topics/graphs/shortest-paths.md for full explanation."""
import heapq
from typing import Dict, List, Optional, Tuple


def dijkstra(graph: Dict[int, List[Tuple[int, int]]], src: int) -> Dict[int, float]:
    dist: Dict[int, float] = {src: 0.0}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def dijkstra_with_path(
    graph: Dict[int, List[Tuple[int, int]]], src: int, dst: int
) -> Tuple[float, Optional[List[int]]]:
    dist: Dict[int, float] = {src: 0.0}
    prev: Dict[int, Optional[int]] = {src: None}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u == dst:
            break
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if dst not in dist:
        return (float("inf"), None)
    path: List[int] = []
    node: Optional[int] = dst
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return (dist[dst], path)
