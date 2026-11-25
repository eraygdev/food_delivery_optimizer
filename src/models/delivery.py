"""Data models representing food delivery orders and optimized routes."""

from dataclasses import dataclass


@dataclass
class Order:
    """Represents a single food delivery request."""

    order_id: str
    restaurant_id: str
    customer_id: str
    priority: int = 2
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.priority < 1:
            raise ValueError("Order priority must be >= 1 (1 = highest urgency).")


@dataclass
class RouteStep:
    """Represents one leg of a courier's multi-stop itinerary."""

    from_node: str
    to_node: str
    path: list[str]
    travel_time: float
    action: str
    order_id: str


@dataclass
class DeliveryPlan:
    """Complete optimized route summary across multiple orders."""

    courier_start: str
    steps: list[RouteStep]
    total_time: float
    delivery_sequence: list[str]
