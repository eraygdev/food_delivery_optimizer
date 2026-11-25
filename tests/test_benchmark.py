"""Differential correctness test comparing MinHeap Dijkstra against naive Dijkstra."""

from src.benchmark.analyzer import (
    generate_city_grid_graph,
    naive_dijkstra_all_distances,
)
from src.engine.router import dijkstra_all_distances


def test_minheap_dijkstra_matches_naive_baseline() -> None:
    graph = generate_city_grid_graph(side=10, seed=123)
    heap_distances, _ = dijkstra_all_distances(graph, "N_0_0")
    naive_distances = naive_dijkstra_all_distances(graph, "N_0_0")

    for node in graph.nodes():
        assert heap_distances[node] == naive_distances[node]
