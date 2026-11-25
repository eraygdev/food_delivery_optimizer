"""Sample 11-node city road network builder."""

from src.structures import Graph


def build_sample_city_graph() -> Graph:
    """Construct the 11-node directed weighted city graph with travel times in minutes."""
    graph = Graph()

    # Register depot, restaurants, intersections, and house nodes
    graph.add_node("D0", node_type="depot", label="Main Depot")
    graph.add_node("R1", node_type="restaurant", label="Restaurant 1 (Pizza)")
    graph.add_node("R2", node_type="restaurant", label="Restaurant 2 (Burger)")
    graph.add_node("R3", node_type="restaurant", label="Restaurant 3 (Kebab)")
    graph.add_node("I1", node_type="intersection", label="Intersection 1")
    graph.add_node("I2", node_type="intersection", label="Intersection 2")
    graph.add_node("I3", node_type="intersection", label="Intersection 3")
    graph.add_node("H1", node_type="house", label="House 1")
    graph.add_node("H2", node_type="house", label="House 2")
    graph.add_node("H3", node_type="house", label="House 3")
    graph.add_node("H4", node_type="house", label="House 4")

    # Top horizontal corridor (two-way)
    graph.add_edge("R1", "I1", weight=6, bidirectional=True)
    graph.add_edge("I1", "H1", weight=4, bidirectional=True)
    graph.add_edge("H1", "I3", weight=9, bidirectional=True)

    # Middle horizontal corridor (main boulevard + two one-way streets)
    graph.add_edge("D0", "I2", weight=2, bidirectional=True)
    graph.add_edge("I2", "R2", weight=3, bidirectional=False)
    graph.add_edge("R2", "I3", weight=5, bidirectional=False)

    # Bottom horizontal corridor (two-way)
    graph.add_edge("H2", "R3", weight=5, bidirectional=True)
    graph.add_edge("R3", "H3", weight=4, bidirectional=True)
    graph.add_edge("H3", "H4", weight=3, bidirectional=True)

    # Vertical connectors (two-way)
    graph.add_edge("R1", "D0", weight=3, bidirectional=True)
    graph.add_edge("D0", "H2", weight=8, bidirectional=True)
    graph.add_edge("I1", "I2", weight=5, bidirectional=True)
    graph.add_edge("I2", "R3", weight=4, bidirectional=True)
    graph.add_edge("H1", "R2", weight=7, bidirectional=True)
    graph.add_edge("R2", "H3", weight=6, bidirectional=True)
    graph.add_edge("I3", "H4", weight=2, bidirectional=True)

    return graph
