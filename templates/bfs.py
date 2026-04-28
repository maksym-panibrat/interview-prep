"""BFS templates — see topics/graphs/bfs.md for full explanation."""
from collections import deque
from typing import Dict, List, Set, Tuple


def bfs_shortest_path(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    visited: Set[int] = {src}
    queue: deque = deque([(src, 0)])
    while queue:
        node, dist = queue.popleft()
        for nb in graph.get(node, []):
            if nb == dst:
                return dist + 1
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, dist + 1))
    return -1


def bfs_grid(grid: List[List[int]], sources: List[Tuple[int, int]]) -> List[List[int]]:
    rows, cols = len(grid), len(grid[0])
    dist = [[float("inf")] * cols for _ in range(rows)]
    queue: deque = deque()
    for r, c in sources:
        dist[r][c] = 0
        queue.append((r, c))
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == float("inf"):
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return [[int(d) if d != float("inf") else -1 for d in row] for row in dist]


def bidirectional_bfs(graph: Dict[int, List[int]], src: int, dst: int) -> int:
    if src == dst:
        return 0
    front, back = {src}, {dst}
    vf, vb = {src: 0}, {dst: 0}
    d = 0
    while front and back:
        d += 1
        if len(front) > len(back):
            front, back, vf, vb = back, front, vb, vf
        nxt: Set[int] = set()
        for node in front:
            for nb in graph.get(node, []):
                if nb in vb:
                    return d + vb[nb]
                if nb not in vf:
                    vf[nb] = d
                    nxt.add(nb)
        front = nxt
    return -1
