"""Unit tests for the city map, Dijkstra router, and multi-order dispatcher."""

from src.engine import OrderDispatcher, build_sample_city_graph, dijkstra_shortest_path
from src.models import Order


def test_city_map_counts_and_one_way_asymmetry() -> None:
    graph = build_sample_city_graph()
    assert graph.node_count() == 11
    assert graph.edge_count() == 30

    # H0 -> I2 -> R2 uses the one-way street (2 + 3 = 5)
    go_cost, go_path = dijkstra_shortest_path(graph, "H0", "R2")
    assert go_cost == 5.0
    assert go_path == ["H0", "I2", "R2"]

    # Returning from R2 cannot reverse I2 -> R2; shortest is R2 -> C3 -> R3 -> I2 -> H0 (16)
    back_cost, back_path = dijkstra_shortest_path(graph, "R2", "H0")
    assert back_cost == 16.0
    assert back_path == ["R2", "C3", "R3", "I2", "H0"]


def test_dijkstra_bypass_routes() -> None:
    graph = build_sample_city_graph()

    cost_c3, path_c3 = dijkstra_shortest_path(graph, "H0", "C3")
    assert cost_c3 == 10.0
    assert path_c3 == ["H0", "I2", "R3", "C3"]

    cost_c4, path_c4 = dijkstra_shortest_path(graph, "C1", "C4")
    assert cost_c4 == 11.0
    assert path_c4 == ["C1", "I3", "C4"]


def test_multi_order_dispatch_precedence_and_completion() -> None:
    graph = build_sample_city_graph()
    dispatcher = OrderDispatcher(graph)

    dispatcher.add_order(
        Order(order_id="ORD-101", restaurant_id="R1", customer_id="C1", priority=2)
    )
    dispatcher.add_order(
        Order(order_id="ORD-102", restaurant_id="R2", customer_id="C4", priority=1)
    )
    dispatcher.add_order(
        Order(order_id="ORD-103", restaurant_id="R3", customer_id="C3", priority=3)
    )

    plan = dispatcher.optimize_route(courier_start="H0", urgency_penalty=4.0)

    assert len(plan.steps) == 6
    assert set(plan.delivery_sequence) == {"ORD-101", "ORD-102", "ORD-103"}
    assert plan.total_time > 0

    seen_pickups: set[str] = set()
    for step in plan.steps:
        if step.action == "pickup":
            seen_pickups.add(step.order_id)
        elif step.action == "deliver":
            assert step.order_id in seen_pickups

    for oid in ("ORD-101", "ORD-102", "ORD-103"):
        assert dispatcher.get_order(oid).status == "delivered"
