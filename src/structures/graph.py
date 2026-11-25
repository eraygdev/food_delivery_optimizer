"""Weighted directed graph represented via an adjacency list backed by HashMap."""

from typing import Any

from src.structures.hash_map import HashMap


class Graph:
    """Weighted directed graph with O(V + E) space complexity."""

    def __init__(self) -> None:
        self._adjacency: HashMap[str, list[tuple[str, float]]] = HashMap()
        self._node_data: HashMap[str, dict[str, Any]] = HashMap()
        self._edge_count: int = 0

    def add_node(self, node_id: str, **metadata: Any) -> None:
        """Register a vertex and optionally attach metadata."""
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
            self._node_data[node_id] = dict(metadata)
        elif metadata:
            existing = self._node_data[node_id]
            existing.update(metadata)

    def add_edge(
        self,
        source: str,
        target: str,
        weight: float,
        bidirectional: bool = False,
    ) -> None:
        """Add a weighted edge from source to target, and optionally the reverse."""
        if weight < 0:
            raise ValueError("Edge weight must be non-negative for Dijkstra routing.")

        if source not in self._adjacency:
            self.add_node(source)
        if target not in self._adjacency:
            self.add_node(target)

        self._upsert_directed_edge(source, target, weight)
        if bidirectional:
            self._upsert_directed_edge(target, source, weight)

    def _upsert_directed_edge(self, source: str, target: str, weight: float) -> None:
        neighbors = self._adjacency[source]
        for i, (existing_target, _) in enumerate(neighbors):
            if existing_target == target:
                neighbors[i] = (target, weight)
                return

        neighbors.append((target, weight))
        self._edge_count += 1

    def neighbors(self, node_id: str) -> list[tuple[str, float]]:
        """Return outgoing (neighbor_id, weight) pairs for the given node."""
        if node_id not in self._adjacency:
            raise KeyError(f"Node '{node_id}' does not exist in the graph.")
        return list(self._adjacency[node_id])

    def get_node_data(self, node_id: str) -> dict[str, Any]:
        """Return metadata associated with the given node."""
        if node_id not in self._node_data:
            raise KeyError(f"Node '{node_id}' does not exist in the graph.")
        return dict(self._node_data[node_id])

    def has_node(self, node_id: str) -> bool:
        """Return True if the node exists in the graph."""
        return node_id in self._adjacency

    def nodes(self) -> list[str]:
        """Return all node identifiers in the graph."""
        return self._adjacency.keys()

    def node_count(self) -> int:
        """Return total number of vertices (V)."""
        return len(self._adjacency)

    def edge_count(self) -> int:
        """Return total number of directed edges (E)."""
        return self._edge_count
