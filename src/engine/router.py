"""Shortest-path algorithms powered by MinHeap and HashMap."""

import math

from src.structures import Graph, HashMap, MinHeap


def dijkstra_all_distances(
    graph: Graph,
    start: str,
) -> tuple[HashMap[str, float], HashMap[str, str | None]]:
    """Compute shortest distances from start to all reachable nodes in O((V + E) log V)."""
    if not graph.has_node(start):
        raise KeyError(f"Start node '{start}' does not exist in the graph.")

    distances: HashMap[str, float] = HashMap()
    parents: HashMap[str, str | None] = HashMap()
    visited: HashMap[str, bool] = HashMap()
    pq: MinHeap[str] = MinHeap()

    for node in graph.nodes():
        distances[node] = math.inf
        parents[node] = None

    distances[start] = 0.0
    pq.push(0.0, start)

    while not pq.is_empty():
        current_dist, current_node = pq.pop()

        if visited.get(current_node, False):
            continue
        visited[current_node] = True

        for neighbor, weight in graph.neighbors(current_node):
            if visited.get(neighbor, False):
                continue

            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parents[neighbor] = current_node
                pq.push(new_dist, neighbor)

    return distances, parents


def reconstruct_path(
    parents: HashMap[str, str | None],
    start: str,
    target: str,
) -> list[str]:
    """Reconstruct the shortest node sequence from start to target."""
    path: list[str] = []
    current: str | None = target

    while current is not None:
        path.append(current)
        if current == start:
            break
        current = parents.get(current)

    path.reverse()
    if not path or path[0] != start:
        raise ValueError(f"No valid path from '{start}' to '{target}'.")

    return path


def dijkstra_shortest_path(
    graph: Graph,
    start: str,
    target: str,
) -> tuple[float, list[str]]:
    """Return (minimum_cost, path) between start and target."""
    if not graph.has_node(target):
        raise KeyError(f"Target node '{target}' does not exist in the graph.")

    distances, parents = dijkstra_all_distances(graph, start)
    total_cost = distances[target]
    if math.isinf(total_cost):
        raise ValueError(f"Node '{target}' is unreachable from '{start}'.")

    return total_cost, reconstruct_path(parents, start, target)
