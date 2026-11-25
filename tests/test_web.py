"""Tests for the interactive web API payload builders and same-restaurant batching."""

from src.web.server import (
    build_sample_map_payload,
    create_random_map_payload,
    optimize_payload,
    run_live_benchmark_payload,
)


def test_sample_and_random_map_payloads() -> None:
    sample = build_sample_map_payload()
    assert sample["map_id"] == "sample_11"
    assert len(sample["nodes"]) == 11

    random_map = create_random_map_payload(seed=7)
    assert random_map["map_id"].startswith("random_")
    assert len(random_map["nodes"]) == 100


def test_two_orders_from_r2_batched_before_departing() -> None:
    build_sample_map_payload()
    result = optimize_payload(
        {
            "map_id": "sample_11",
            "courier_start": "D0",
            "urgency_penalty": 4.0,
            "orders": [
                {
                    "order_id": "ORD-1",
                    "restaurant_id": "R2",
                    "customer_id": "H1",
                    "priority": 1,
                },
                {
                    "order_id": "ORD-2",
                    "restaurant_id": "R2",
                    "customer_id": "H4",
                    "priority": 3,
                },
            ],
        }
    )

    assert result["unoptimized_time"] > result["total_time"]
    assert result["time_saved"] > 0
    assert result["savings_percent"] > 0

    steps = result["steps"]
    assert len(steps) == 4
    # Both R2 pickups must occur consecutively before delivering
    assert steps[0]["action"] == "pickup" and steps[0]["to_node"] == "R2"
    assert steps[1]["action"] == "pickup" and steps[1]["to_node"] == "R2"
    assert steps[1]["travel_time"] == 0.0
    assert steps[2]["action"] == "deliver"
    assert steps[3]["action"] == "deliver"


def test_live_benchmark_payload() -> None:
    data = run_live_benchmark_payload()
    assert len(data["priority_queue"]) == 4
    assert len(data["dijkstra"]) == 5
