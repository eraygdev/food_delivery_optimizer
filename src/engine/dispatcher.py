"""Multi-order delivery route planner combining HashMap, MinHeap, and Dijkstra."""

import math

from src.engine.router import dijkstra_all_distances, reconstruct_path
from src.models import DeliveryPlan, Order, RouteStep
from src.structures import Graph, HashMap, MinHeap


class OrderDispatcher:
    """Manages active orders and builds precedence-aware delivery routes."""

    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._orders: HashMap[str, Order] = HashMap()
        self._incoming_queue: MinHeap[str] = MinHeap()

    def add_order(self, order: Order) -> None:
        """Register an order in O(1) average HashMap time and O(log K) heap time."""
        if not self._graph.has_node(order.restaurant_id):
            raise KeyError(f"Unknown restaurant node '{order.restaurant_id}'.")
        if not self._graph.has_node(order.customer_id):
            raise KeyError(f"Unknown customer node '{order.customer_id}'.")
        if order.order_id in self._orders:
            raise ValueError(f"Duplicate order ID '{order.order_id}'.")

        self._orders[order.order_id] = order
        self._incoming_queue.push(float(order.priority), order.order_id)

    def get_order(self, order_id: str) -> Order:
        """Retrieve an order in O(1) average time."""
        return self._orders[order_id]

    def order_count(self) -> int:
        """Return total number of registered orders."""
        return len(self._orders)

    def optimize_route(
        self,
        courier_start: str,
        urgency_penalty: float = 4.0,
    ) -> DeliveryPlan:
        """Plan an efficient multi-order route honoring pickup-before-delivery rules."""
        if not self._graph.has_node(courier_start):
            raise KeyError(f"Courier start node '{courier_start}' does not exist.")

        # Drain incoming priority queue into active order list in urgency order
        active_ids: list[str] = []
        temp_queue: MinHeap[str] = MinHeap()
        while not self._incoming_queue.is_empty():
            prio, oid = self._incoming_queue.pop()
            active_ids.append(oid)
            temp_queue.push(prio, oid)
        self._incoming_queue = temp_queue

        # Reset statuses for fresh simulation runs
        for oid in active_ids:
            self._orders[oid].status = "pending"

        current_node = courier_start
        steps: list[RouteStep] = []
        delivery_sequence: list[str] = []
        total_time = 0.0

        while len(delivery_sequence) < len(active_ids):
            distances, parents = dijkstra_all_distances(self._graph, current_node)
            candidate_heap: MinHeap[tuple[str, str, str, float]] = MinHeap()

            for oid in active_ids:
                order = self._orders[oid]
                if order.status == "pending":
                    target = order.restaurant_id
                    action = "pickup"
                elif order.status == "picked_up":
                    target = order.customer_id
                    action = "deliver"
                else:
                    continue

                travel_time = distances[target]
                if math.isinf(travel_time):
                    continue

                score = travel_time + (order.priority - 1) * urgency_penalty
                candidate_heap.push(score, (oid, action, target, travel_time))

            if candidate_heap.is_empty():
                raise ValueError("Remaining orders contain unreachable nodes.")

            _, (chosen_oid, action, target_node, leg_time) = candidate_heap.pop()
            leg_path = reconstruct_path(parents, current_node, target_node)

            chosen_order = self._orders[chosen_oid]
            if action == "pickup":
                chosen_order.status = "picked_up"
            else:
                chosen_order.status = "delivered"
                delivery_sequence.append(chosen_oid)

            steps.append(
                RouteStep(
                    from_node=current_node,
                    to_node=target_node,
                    path=leg_path,
                    travel_time=leg_time,
                    action=action,
                    order_id=chosen_oid,
                )
            )
            total_time += leg_time
            current_node = target_node

        return DeliveryPlan(
            courier_start=courier_start,
            steps=steps,
            total_time=total_time,
            delivery_sequence=delivery_sequence,
        )
