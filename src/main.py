"""Entry point for the food delivery route optimization prototype."""

import sys

from src.engine import OrderDispatcher, build_sample_city_graph
from src.models import Order


def print_plan(title: str, dispatcher: OrderDispatcher, urgency_penalty: float) -> None:
    """Execute route optimization and display step-by-step itinerary."""
    plan = dispatcher.optimize_route(
        courier_start="H0", urgency_penalty=urgency_penalty
    )
    print(f"\n=== {title} (urgency_penalty={urgency_penalty}) ===")
    for idx, step in enumerate(plan.steps, start=1):
        route_str = " -> ".join(step.path)
        action_label = "PICKUP " if step.action == "pickup" else "DELIVER"
        print(
            f"  {idx}. [{action_label}] {step.order_id} | "
            f"{route_str} ({step.travel_time:.1f} dk)"
        )
    print(f"  Teslim Sirasi : {' -> '.join(plan.delivery_sequence)}")
    print(f"  Toplam Sure   : {plan.total_time:.1f} dakika")


def main() -> None:
    """Run the multi-order food delivery routing simulation."""
    print("Food Delivery Route Optimization Engine")
    print(f"Python Runtime: {sys.version.split()[0]}")

    city_graph = build_sample_city_graph()
    print(
        f"Harita Yuklendi: {city_graph.node_count()} dugum, "
        f"{city_graph.edge_count()} yonlu kenar"
    )

    dispatcher = OrderDispatcher(city_graph)
    dispatcher.add_order(
        Order(order_id="ORD-101", restaurant_id="R1", customer_id="C1", priority=2)
    )
    dispatcher.add_order(
        Order(order_id="ORD-102", restaurant_id="R2", customer_id="C4", priority=1)
    )
    dispatcher.add_order(
        Order(order_id="ORD-103", restaurant_id="R3", customer_id="C3", priority=3)
    )

    print_plan("Aciliyet Oncelikli Rota (SLA Odakli)", dispatcher, urgency_penalty=4.0)
    print_plan("Saf En Kisa Yol Odakli Rota", dispatcher, urgency_penalty=0.0)


if __name__ == "__main__":
    main()
