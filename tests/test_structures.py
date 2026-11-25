"""Unit tests for HashMap, MinHeap, and Graph implementations."""

import pytest

from src.structures import Graph, HashMap, MinHeap


def test_hash_map_crud_and_resize() -> None:
    hmap: HashMap[str, int] = HashMap(initial_capacity=4, max_load_factor=0.75)

    for i in range(50):
        hmap[f"order_{i}"] = i * 10

    assert len(hmap) == 50
    assert hmap.capacity > 4
    assert hmap["order_0"] == 0
    assert hmap["order_49"] == 490

    hmap["order_10"] = 999
    assert hmap["order_10"] == 999
    assert len(hmap) == 50

    removed = hmap.remove("order_10")
    assert removed == 999
    assert "order_10" not in hmap
    assert hmap.get("order_10", -1) == -1

    with pytest.raises(KeyError):
        _ = hmap["missing"]


def test_min_heap_ordering_and_fifo_ties() -> None:
    heap: MinHeap[dict[str, str]] = MinHeap()

    heap.push(10, {"id": "O1"})
    heap.push(3, {"id": "O2"})
    heap.push(5, {"id": "O3"})
    heap.push(3, {"id": "O4"})

    assert len(heap) == 4
    assert heap.peek() == (3, {"id": "O2"})

    assert heap.pop() == (3, {"id": "O2"})
    assert heap.pop() == (3, {"id": "O4"})
    assert heap.pop() == (5, {"id": "O3"})
    assert heap.pop() == (10, {"id": "O1"})
    assert heap.is_empty()

    with pytest.raises(IndexError):
        heap.pop()


def test_graph_directed_and_bidirectional_edges() -> None:
    graph = Graph()
    graph.add_node("D0", node_type="depot")
    graph.add_node("I2", node_type="intersection")
    graph.add_node("R2", node_type="restaurant")

    graph.add_edge("D0", "I2", weight=2, bidirectional=True)
    graph.add_edge("I2", "R2", weight=3, bidirectional=False)

    assert graph.node_count() == 3
    assert graph.edge_count() == 3
    assert ("I2", 2) in graph.neighbors("D0")
    assert ("D0", 2) in graph.neighbors("I2")
    assert ("R2", 3) in graph.neighbors("I2")
    assert ("I2", 3) not in graph.neighbors("R2")
    assert graph.get_node_data("D0") == {"node_type": "depot"}

    with pytest.raises(ValueError):
        graph.add_edge("D0", "R2", weight=-1)

    with pytest.raises(KeyError):
        graph.neighbors("UNKNOWN")
