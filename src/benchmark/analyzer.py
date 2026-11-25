"""Empirical benchmarks comparing O(log N) heap structures against linear baselines."""

import math
import random
import time

from src.engine.router import dijkstra_all_distances
from src.structures import Graph, HashMap, MinHeap


class LinearPriorityQueue:
    """Naive unsorted-list priority queue with O(1) push and O(N) pop."""

    def __init__(self) -> None:
        self._items: list[tuple[float, int]] = []

    def push(self, priority: float, item: int) -> None:
        self._items.append((priority, item))

    def pop(self) -> tuple[float, int]:
        if not self._items:
            raise IndexError("Cannot pop from an empty queue.")
        min_idx = 0
        min_prio = self._items[0][0]
        for i in range(1, len(self._items)):
            if self._items[i][0] < min_idx_prio(self._items, min_idx):
                min_idx = i
                min_prio = self._items[i][0]
        return self._items.pop(min_idx)

    def is_empty(self) -> bool:
        return len(self._items) == 0


def min_idx_prio(items: list[tuple[float, int]], idx: int) -> float:
    return items[idx][0]


def generate_city_grid_graph(side: int, seed: int = 42) -> Graph:
    """Generate a connected sparse grid graph with V = side * side vertices."""
    rng = random.Random(seed)
    graph = Graph()

    for r in range(side):
        for c in range(side):
            node_id = f"N_{r}_{c}"
            graph.add_node(node_id, row=r, col=c)

    for r in range(side):
        for c in range(side):
            u = f"N_{r}_{c}"
            if c + 1 < side:
                v_right = f"N_{r}_{c + 1}"
                graph.add_edge(
                    u, v_right, weight=float(rng.randint(1, 15)), bidirectional=True
                )
            if r + 1 < side:
                v_down = f"N_{r + 1}_{c}"
                graph.add_edge(
                    u, v_down, weight=float(rng.randint(1, 15)), bidirectional=True
                )

    return graph


def naive_dijkstra_all_distances(graph: Graph, start: str) -> dict[str, float]:
    """O(V^2) Dijkstra implementation using linear scan instead of a MinHeap."""
    nodes = graph.nodes()
    distances: dict[str, float] = {node: math.inf for node in nodes}
    visited: set[str] = set()
    distances[start] = 0.0

    for _ in range(len(nodes)):
        current_node: str | None = None
        current_dist = math.inf
        for node in nodes:
            if node not in visited and distances[node] < current_dist:
                current_dist = distances[node]
                current_node = node

        if current_node is None or math.isinf(current_dist):
            break

        visited.add(current_node)
        for neighbor, weight in graph.neighbors(current_node):
            if neighbor not in visited:
                candidate = current_dist + weight
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate

    return distances


def benchmark_priority_queue() -> None:
    """Measure MinHeap O(log N) vs Linear O(N) priority queue scaling."""
    print("\n[1] PRIORITY QUEUE BENCHMARK: MinHeap O(log N) vs Linear O(N)")
    print("-" * 78)
    print(
        f"{'N':>8} | {'log2(N)':>7} | {'MinHeap (ms)':>12} | "
        f"{'Avg/Op (us)':>11} | {'Linear (ms)':>11} | {'Speedup':>8}"
    )
    print("-" * 78)

    rng = random.Random(42)
    for size in (100, 500, 1_000, 2_500, 5_000):
        values = [rng.uniform(1.0, 10_000.0) for _ in range(size)]

        heap: MinHeap[int] = MinHeap()
        t0 = time.perf_counter()
        for idx, prio in enumerate(values):
            heap.push(prio, idx)
        while not heap.is_empty():
            heap.pop()
        heap_ms = (time.perf_counter() - t0) * 1000.0

        linear = LinearPriorityQueue()
        t1 = time.perf_counter()
        for idx, prio in enumerate(values):
            linear.push(prio, idx)
        while not linear.is_empty():
            linear.pop()
        linear_ms = (time.perf_counter() - t1) * 1000.0

        avg_op_us = (heap_ms * 1000.0) / (2 * size)
        speedup = linear_ms / heap_ms if heap_ms > 0 else 0.0
        print(
            f"{size:>8} | {math.log2(size):>7.2f} | {heap_ms:>12.3f} | "
            f"{avg_op_us:>11.3f} | {linear_ms:>11.3f} | {speedup:>7.2f}x"
        )


def benchmark_dijkstra() -> None:
    """Measure O((V + E) log V) Dijkstra vs O(V^2) naive scan across grid graphs."""
    print("\n[2] GRAPH ROUTING BENCHMARK: Dijkstra O((V+E) log V) vs Naive O(V^2)")
    print("-" * 84)
    print(
        f"{'Grid':>7} | {'V':>6} | {'E':>6} | {'MinHeap (ms)':>12} | "
        f"{'Naive (ms)':>10} | {'Speedup':>8} | {'us / (V+E)logV':>14}"
    )
    print("-" * 84)

    for side in (10, 20, 30, 40, 50, 70, 100):
        graph = generate_city_grid_graph(side)
        v_count = graph.node_count()
        e_count = graph.edge_count()

        t0 = time.perf_counter()
        dijkstra_all_distances(graph, "N_0_0")
        heap_ms = (time.perf_counter() - t0) * 1000.0

        if v_count <= 2_500:
            t1 = time.perf_counter()
            naive_dijkstra_all_distances(graph, "N_0_0")
            naive_ms = (time.perf_counter() - t1) * 1000.0
            naive_str = f"{naive_ms:>10.3f}"
            speedup_str = f"{(naive_ms / heap_ms):>7.2f}x"
        else:
            naive_str = "   skipped"
            speedup_str = "       -"

        theoretical_ops = (v_count + e_count) * math.log2(v_count)
        norm_us = (heap_ms * 1000.0) / theoretical_ops
        print(
            f"{f'{side}x{side}':>7} | {v_count:>6} | {e_count:>6} | {heap_ms:>12.3f} | "
            f"{naive_str} | {speedup_str} | {norm_us:>14.4f}"
        )


def benchmark_hashmap() -> None:
    """Verify O(1) average lookup latency on HashMap across growing sizes."""
    print("\n[3] HASH MAP BENCHMARK: O(1) Average Lookup Latency (10,000 queries)")
    print("-" * 68)
    print(
        f"{'Entries':>10} | {'Buckets':>10} | {'Load Factor':>11} | "
        f"{'10k Lookups (ms)':>16} | {'Avg (us)':>8}"
    )
    print("-" * 68)

    for size in (1_000, 10_000, 50_000):
        hmap: HashMap[str, int] = HashMap()
        for i in range(size):
            hmap[f"ORD-{i}"] = i

        queries = [f"ORD-{(i * 7) % size}" for i in range(10_000)]
        t0 = time.perf_counter()
        for q in queries:
            _ = hmap[q]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        avg_us = (elapsed_ms * 1000.0) / 10_000.0

        print(
            f"{size:>10} | {hmap.capacity:>10} | {hmap.load_factor:>11.3f} | "
            f"{elapsed_ms:>16.3f} | {avg_us:>8.3f}"
        )


def main() -> None:
    """Run all empirical complexity benchmarks."""
    print("=== Food Delivery Router: Algorithmic Efficiency Analysis ===")
    benchmark_priority_queue()
    benchmark_dijkstra()
    benchmark_hashmap()


if __name__ == "__main__":
    main()
