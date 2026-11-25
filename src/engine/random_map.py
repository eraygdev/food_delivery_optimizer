"""Random 10x10 city graph generator preserving strong connectivity and one-way streets."""

from collections import deque
import random

from src.structures import Graph


def _has_path(adjacency: dict[str, set[str]], start: str, goal: str) -> bool:
    """Return True if goal is reachable from start via BFS."""
    if start == goal:
        return True
    visited: set[str] = {start}
    queue: deque[str] = deque([start])

    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor == goal:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False


def is_strongly_connected(graph: Graph) -> bool:
    """Verify that every vertex in the directed graph can reach and be reached by D0."""
    nodes = graph.nodes()
    if not nodes:
        return True

    start = "D0" if graph.has_node("D0") else nodes[0]
    forward_adj: dict[str, set[str]] = {n: set() for n in nodes}
    reverse_adj: dict[str, set[str]] = {n: set() for n in nodes}

    for u in nodes:
        for v, _ in graph.neighbors(u):
            forward_adj[u].add(v)
            reverse_adj[v].add(u)

    def count_reachable(adj: dict[str, set[str]]) -> int:
        visited: set[str] = {start}
        queue: deque[str] = deque([start])
        while queue:
            cur = queue.popleft()
            for nxt in adj[cur]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return len(visited)

    expected = len(nodes)
    return (
        count_reachable(forward_adj) == expected
        and count_reachable(reverse_adj) == expected
    )


def build_random_grid_map(
    rows: int = 10,
    cols: int = 10,
    num_restaurants: int = 5,
    num_houses: int = 8,
    one_way_ratio: float = 0.22,
    seed: int | None = None,
) -> tuple[Graph, dict[str, tuple[float, float]]]:
    """Generate a random directed grid map with random depot, restaurants, and houses."""
    total_nodes = rows * cols
    total_special = 1 + num_restaurants + num_houses
    if total_special > total_nodes:
        raise ValueError("Special nodes exceed total grid capacity.")

    rng = random.Random(seed)
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    chosen_cells = rng.sample(all_cells, total_special)

    cell_to_id: dict[tuple[int, int], str] = {}
    coords: dict[str, tuple[float, float]] = {}
    graph = Graph()

    # Assign D0 (depot), R1..Rk (restaurants), H1..Hm (houses) to random cells
    depot_cell = chosen_cells[0]
    cell_to_id[depot_cell] = "D0"
    graph.add_node("D0", node_type="depot", label="Depo (D0)")

    for i in range(1, 1 + num_restaurants):
        cell = chosen_cells[i]
        rid = f"R{i}"
        cell_to_id[cell] = rid
        graph.add_node(rid, node_type="restaurant", label=f"Restoran {i}")

    for i in range(1, 1 + num_houses):
        cell = chosen_cells[num_restaurants + i]
        hid = f"H{i}"
        cell_to_id[cell] = hid
        graph.add_node(hid, node_type="house", label=f"Ev {i}")

    # Assign remaining cells as intersections
    inter_idx = 1
    for r, c in all_cells:
        if (r, c) not in cell_to_id:
            iid = f"I{inter_idx:02d}"
            inter_idx += 1
            cell_to_id[(r, c)] = iid
            graph.add_node(iid, node_type="intersection", label=f"Kavsak {iid}")

    for (r, c), node_id in cell_to_id.items():
        coords[node_id] = (float(c), float(rows - 1 - r))

    # Build initial bidirectional grid edges and track adjacency for safe one-way pruning
    road_segments: list[tuple[str, str, float]] = []
    forward_adj: dict[str, set[str]] = {nid: set() for nid in coords}

    for r in range(rows):
        for c in range(cols):
            u = cell_to_id[(r, c)]
            if c + 1 < cols:
                v = cell_to_id[(r, c + 1)]
                w = float(rng.randint(1, 12))
                road_segments.append((u, v, w))
                forward_adj[u].add(v)
                forward_adj[v].add(u)
            if r + 1 < rows:
                v = cell_to_id[(r + 1, c)]
                w = float(rng.randint(1, 12))
                road_segments.append((u, v, w))
                forward_adj[u].add(v)
                forward_adj[v].add(u)

    # Convert a subset of roads to one-way streets while preserving strong connectivity
    indices = list(range(len(road_segments)))
    rng.shuffle(indices)
    target_one_way = int(len(road_segments) * one_way_ratio)
    one_way_edges: set[int] = set()
    directed_orientations: dict[int, tuple[str, str]] = {}

    for idx in indices:
        if len(one_way_edges) >= target_one_way:
            break
        u, v, _ = road_segments[idx]
        src, dst = (u, v) if rng.random() < 0.5 else (v, u)

        # Removing dst -> src preserves strong connectivity iff dst can still reach src
        forward_adj[dst].remove(src)
        if _has_path(forward_adj, dst, src):
            one_way_edges.add(idx)
            directed_orientations[idx] = (src, dst)
        else:
            forward_adj[dst].add(src)

    for idx, (u, v, w) in enumerate(road_segments):
        if idx in one_way_edges:
            src, dst = directed_orientations[idx]
            graph.add_edge(src, dst, weight=w, bidirectional=False)
        else:
            graph.add_edge(u, v, weight=w, bidirectional=True)

    return graph, coords
