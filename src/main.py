"""Entry point for the food delivery route optimization prototype."""

import argparse
import sys

from src.engine import OrderDispatcher, build_sample_city_graph, dijkstra_shortest_path
from src.models import Order
from src.structures import Graph


def print_plan(
    title: str,
    dispatcher: OrderDispatcher,
    courier_start: str,
    urgency_penalty: float,
) -> None:
    """Execute route optimization and display step-by-step itinerary."""
    plan = dispatcher.optimize_route(
        courier_start=courier_start,
        urgency_penalty=urgency_penalty,
    )
    print(
        f"\n=== {title} (start={courier_start}, urgency_penalty={urgency_penalty}) ==="
    )
    for idx, step in enumerate(plan.steps, start=1):
        route_str = " -> ".join(step.path)
        action_label = "PICKUP " if step.action == "pickup" else "DELIVER"
        print(
            f"  {idx}. [{action_label}] {step.order_id} | "
            f"{route_str} ({step.travel_time:.1f} min)"
        )
    print(f"  Delivery Order: {' -> '.join(plan.delivery_sequence)}")
    print(f"  Total Time    : {plan.total_time:.1f} min")


def parse_orders_arg(raw_orders: str) -> list[Order]:
    """Parse CLI order string formatted as 'ID:RESTAURANT:HOUSE:PRIORITY,...'."""
    orders: list[Order] = []
    for chunk in raw_orders.split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [p.strip().upper() for p in item.split(":")]
        if len(parts) != 4:
            raise ValueError(
                f"Invalid order format '{item}'. Expected 'ID:RESTAURANT:HOUSE:PRIORITY'."
            )
        order_id, restaurant_id, house_id, prio_str = parts
        orders.append(
            Order(
                order_id=order_id,
                restaurant_id=restaurant_id,
                customer_id=house_id,
                priority=int(prio_str),
            )
        )
    if not orders:
        raise ValueError("At least one valid order must be provided.")
    return orders


def prompt_interactive_orders(city_graph: Graph) -> tuple[str, list[Order], float]:
    """Prompt the user interactively for courier start node and custom orders."""
    print(
        "\nNodes: Depot=[D0], Restaurants=[R1,R2,R3], Houses=[H1,H2,H3,H4], Intersections=[I1,I2,I3]"
    )

    while True:
        start_input = input("Courier start node [D0]: ").strip().upper() or "D0"
        if city_graph.has_node(start_input):
            break
        print(f"Error: '{start_input}' is not on the map. Try again.")

    penalty_raw = input("Urgency penalty weight [4.0]: ").strip()
    urgency_penalty = float(penalty_raw) if penalty_raw else 4.0

    orders: list[Order] = []
    print("\nAdd orders (press Enter on Order ID or type 'q' to finish):")
    while True:
        default_id = f"ORD-{len(orders) + 1}"
        oid_prompt = f"  Order ID (e.g. {default_id}, 'q' to finish): "
        oid = input(oid_prompt).strip().upper()
        if oid in ("", "Q") and orders:
            break
        if oid == "Q" and not orders:
            print("  Please enter at least 1 order.")
            continue
        if not oid:
            oid = default_id

        rest = input("  Restaurant (R1/R2/R3): ").strip().upper()
        house = input("  House (H1/H2/H3/H4): ").strip().upper()
        prio_str = input("  Priority (1=Urgent, 2=Normal, 3=Standard) [2]: ").strip()
        prio = int(prio_str) if prio_str else 2

        try:
            order = Order(
                order_id=oid,
                restaurant_id=rest,
                customer_id=house,
                priority=prio,
            )
            if not city_graph.has_node(rest) or not city_graph.has_node(house):
                raise KeyError("Invalid restaurant or house node.")
            orders.append(order)
            print(f"  -> Added: {oid} ({rest} -> {house}, priority={prio})")
        except (ValueError, KeyError) as exc:
            print(f"  Error: {exc}. Order skipped, try again.")

    return start_input, orders, urgency_penalty


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for default, custom, and interactive runs."""
    parser = argparse.ArgumentParser(description="Food Delivery Route Optimizer")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Enter custom courier start and orders interactively.",
    )
    parser.add_argument(
        "--start",
        default="D0",
        help="Courier starting node ID (default: D0).",
    )
    parser.add_argument(
        "--orders",
        default=None,
        help="Comma-separated orders as ID:RESTAURANT:HOUSE:PRIORITY.",
    )
    parser.add_argument(
        "--penalty",
        type=float,
        default=4.0,
        help="Urgency penalty per priority tier (default: 4.0).",
    )
    parser.add_argument(
        "--path",
        nargs=2,
        metavar=("FROM", "TO"),
        help="Compute shortest Dijkstra path between two nodes and exit.",
    )
    return parser


def main() -> None:
    """Run the multi-order food delivery routing simulation."""
    args = build_arg_parser().parse_args()
    print("Food Delivery Route Optimization Engine")
    print(f"Python Runtime: {sys.version.split()[0]}")

    city_graph = build_sample_city_graph()
    print(
        f"Map Loaded: {city_graph.node_count()} nodes, "
        f"{city_graph.edge_count()} directed edges"
    )

    if args.path:
        src_node, dst_node = args.path[0].upper(), args.path[1].upper()
        cost, path = dijkstra_shortest_path(city_graph, src_node, dst_node)
        print(
            f"\nShortest Path ({src_node} -> {dst_node}): {' -> '.join(path)} ({cost:.1f} min)"
        )
        return

    if args.interactive:
        courier_start, orders, penalty = prompt_interactive_orders(city_graph)
        dispatcher = OrderDispatcher(city_graph)
        for order in orders:
            dispatcher.add_order(order)
        print_plan("Custom Interactive Route", dispatcher, courier_start, penalty)
        return

    if args.orders:
        courier_start = args.start.upper()
        orders = parse_orders_arg(args.orders)
        dispatcher = OrderDispatcher(city_graph)
        for order in orders:
            dispatcher.add_order(order)
        print_plan("Custom CLI Route", dispatcher, courier_start, args.penalty)
        return

    dispatcher = OrderDispatcher(city_graph)
    dispatcher.add_order(
        Order(order_id="ORD-101", restaurant_id="R1", customer_id="H1", priority=2)
    )
    dispatcher.add_order(
        Order(order_id="ORD-102", restaurant_id="R2", customer_id="H4", priority=1)
    )
    dispatcher.add_order(
        Order(order_id="ORD-103", restaurant_id="R3", customer_id="H3", priority=3)
    )

    print_plan("Urgency-Priority Route (SLA)", dispatcher, "D0", 4.0)
    print_plan("Shortest-Path Route", dispatcher, "D0", 0.0)


if __name__ == "__main__":
    main()
