"""Sample 11-node city road network builder."""

from src.structures import Graph


def build_sample_city_graph() -> Graph:
    """Construct the 11-node directed weighted city graph with travel times in minutes."""
    graph = Graph()

    # Register hub, restaurants, intersections, and customer nodes
    graph.add_node("H0", node_type="hub", label="Merkez Hub")
    graph.add_node("R1", node_type="restaurant", label="Restoran 1 (Pizza)")
    graph.add_node("R2", node_type="restaurant", label="Restoran 2 (Burger)")
    graph.add_node("R3", node_type="restaurant", label="Restoran 3 (Kebap)")
    graph.add_node("I1", node_type="intersection", label="Kavsak 1")
    graph.add_node("I2", node_type="intersection", label="Kavsak 2")
    graph.add_node("I3", node_type="intersection", label="Kavsak 3")
    graph.add_node("C1", node_type="customer", label="Musteri 1")
    graph.add_node("C2", node_type="customer", label="Musteri 2")
    graph.add_node("C3", node_type="customer", label="Musteri 3")
    graph.add_node("C4", node_type="customer", label="Musteri 4")

    # Top horizontal corridor (two-way)
    graph.add_edge("R1", "I1", weight=6, bidirectional=True)
    graph.add_edge("I1", "C1", weight=4, bidirectional=True)
    graph.add_edge("C1", "I3", weight=9, bidirectional=True)

    # Middle horizontal corridor (main boulevard + two one-way streets)
    graph.add_edge("H0", "I2", weight=2, bidirectional=True)
    graph.add_edge("I2", "R2", weight=3, bidirectional=False)
    graph.add_edge("R2", "I3", weight=5, bidirectional=False)

    # Bottom horizontal corridor (two-way)
    graph.add_edge("C2", "R3", weight=5, bidirectional=True)
    graph.add_edge("R3", "C3", weight=4, bidirectional=True)
    graph.add_edge("C3", "C4", weight=3, bidirectional=True)

    # Vertical connectors (two-way)
    graph.add_edge("R1", "H0", weight=3, bidirectional=True)
    graph.add_edge("H0", "C2", weight=8, bidirectional=True)
    graph.add_edge("I1", "I2", weight=5, bidirectional=True)
    graph.add_edge("I2", "R3", weight=4, bidirectional=True)
    graph.add_edge("C1", "R2", weight=7, bidirectional=True)
    graph.add_edge("R2", "C3", weight=6, bidirectional=True)
    graph.add_edge("I3", "C4", weight=2, bidirectional=True)

    return graph
