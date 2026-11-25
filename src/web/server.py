"""Lightweight HTTP server exposing the interactive routing presentation UI."""

from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import random
import time
from typing import Any
from urllib.parse import urlparse

from src.benchmark.analyzer import (
    LinearPriorityQueue,
    generate_city_grid_graph,
    naive_dijkstra_all_distances,
)
from src.engine import OrderDispatcher, build_sample_city_graph
from src.engine.random_map import build_random_grid_map
from src.engine.router import dijkstra_all_distances
from src.models import Order
from src.structures import Graph, HashMap, MinHeap

STATIC_DIR = Path(__file__).resolve().parent / "static"

SAMPLE_COORDS: dict[str, tuple[float, float]] = {
    "R1": (0.0, 2.0),
    "I1": (1.0, 2.0),
    "H1": (2.0, 2.0),
    "D0": (0.0, 1.0),
    "I2": (1.0, 1.0),
    "R2": (2.0, 1.0),
    "I3": (3.0, 1.0),
    "H2": (0.0, 0.0),
    "R3": (1.0, 0.0),
    "H3": (2.0, 0.0),
    "H4": (3.0, 0.0),
}

MAP_STORE: HashMap[str, tuple[Graph, dict[str, tuple[float, float]]]] = HashMap()
MAP_COUNTER: int = 0


def _serialize_graph(
    map_id: str,
    graph: Graph,
    coords: dict[str, tuple[float, float]],
) -> dict[str, Any]:
    """Convert a Graph and coordinate table into a JSON-serializable payload."""
    nodes_payload: list[dict[str, Any]] = []
    for node_id in graph.nodes():
        meta = graph.get_node_data(node_id)
        x, y = coords[node_id]
        nodes_payload.append(
            {
                "id": node_id,
                "type": meta.get("node_type", "intersection"),
                "label": meta.get("label", node_id),
                "x": x,
                "y": y,
            }
        )

    edges_payload: list[dict[str, Any]] = []
    seen_undirected: set[tuple[str, str]] = set()
    for u in graph.nodes():
        for v, weight in graph.neighbors(u):
            reverse_neighbors = {nbr for nbr, _ in graph.neighbors(v)}
            is_bidirectional = u in reverse_neighbors
            if is_bidirectional:
                pair = tuple(sorted((u, v)))
                if pair in seen_undirected:
                    continue
                seen_undirected.add((pair[0], pair[1]))
            edges_payload.append(
                {
                    "source": u,
                    "target": v,
                    "weight": weight,
                    "bidirectional": is_bidirectional,
                }
            )

    return {"map_id": map_id, "nodes": nodes_payload, "edges": edges_payload}


def build_sample_map_payload() -> dict[str, Any]:
    """Return or initialize the 11-node sample city map payload."""
    if "sample_11" not in MAP_STORE:
        MAP_STORE["sample_11"] = (build_sample_city_graph(), SAMPLE_COORDS)
    graph, coords = MAP_STORE["sample_11"]
    return _serialize_graph("sample_11", graph, coords)


def create_random_map_payload(seed: int | None = None) -> dict[str, Any]:
    """Generate a new 10x10 random city map and store it in MAP_STORE."""
    global MAP_COUNTER
    MAP_COUNTER += 1
    map_id = f"random_{MAP_COUNTER}"
    graph, coords = build_random_grid_map(
        rows=10,
        cols=10,
        num_restaurants=5,
        num_houses=8,
        one_way_ratio=0.22,
        seed=seed,
    )
    MAP_STORE[map_id] = (graph, coords)
    return _serialize_graph(map_id, graph, coords)


def _bfs_unweighted_path_cost(graph: Graph, start: str, target: str) -> float:
    """Compute travel time along the fewest-hop BFS path (ignoring edge weights)."""
    if start == target:
        return 0.0

    queue: deque[str] = deque([start])
    parents: dict[str, tuple[str | None, float]] = {start: (None, 0.0)}

    while queue:
        current = queue.popleft()
        if current == target:
            break
        for neighbor, weight in graph.neighbors(current):
            if neighbor not in parents:
                parents[neighbor] = (current, weight)
                queue.append(neighbor)

    if target not in parents:
        raise ValueError(f"Node '{target}' is unreachable from '{start}'.")

    total = 0.0
    cursor: str | None = target
    while cursor is not None and cursor != start:
        prev_node, edge_w = parents[cursor]
        total += edge_w
        cursor = prev_node
    return total


def compute_unoptimized_baseline(
    graph: Graph,
    courier_start: str,
    orders: list[Order],
) -> float:
    """Estimate total time without multi-order batching or Dijkstra weighting."""
    total = 0.0
    for idx, order in enumerate(orders):
        total += _bfs_unweighted_path_cost(graph, courier_start, order.restaurant_id)
        total += _bfs_unweighted_path_cost(
            graph, order.restaurant_id, order.customer_id
        )
        if idx < len(orders) - 1:
            total += _bfs_unweighted_path_cost(graph, order.customer_id, courier_start)
    return total


def optimize_payload(body: dict[str, Any]) -> dict[str, Any]:
    """Validate request payload and compute the optimal multi-order delivery route."""
    map_id = str(body.get("map_id", "sample_11"))
    if map_id == "sample_11" and "sample_11" not in MAP_STORE:
        build_sample_map_payload()
    if map_id not in MAP_STORE:
        raise ValueError(f"Unknown map_id '{map_id}'. Please reload the map.")

    graph, _ = MAP_STORE[map_id]
    courier_start = str(body.get("courier_start", "D0")).strip().upper()
    urgency_penalty = float(body.get("urgency_penalty", 4.0))
    raw_orders = body.get("orders", [])
    if not isinstance(raw_orders, list) or not raw_orders:
        raise ValueError("Please add at least one order before optimizing.")

    dispatcher = OrderDispatcher(graph)
    parsed_orders: list[Order] = []
    for idx, item in enumerate(raw_orders, start=1):
        order_id = str(item.get("order_id") or f"ORD-{idx}").strip().upper()
        restaurant_id = str(item.get("restaurant_id", "")).strip().upper()
        customer_id = str(item.get("customer_id", "")).strip().upper()
        priority = int(item.get("priority", 2))
        order = Order(
            order_id=order_id,
            restaurant_id=restaurant_id,
            customer_id=customer_id,
            priority=priority,
        )
        dispatcher.add_order(order)
        parsed_orders.append(order)

    plan = dispatcher.optimize_route(
        courier_start=courier_start,
        urgency_penalty=urgency_penalty,
    )
    unoptimized_time = compute_unoptimized_baseline(graph, courier_start, parsed_orders)
    time_saved = round(unoptimized_time - plan.total_time, 1)
    savings_pct = (
        round((time_saved / unoptimized_time) * 100.0, 1)
        if unoptimized_time > 0
        else 0.0
    )

    return {
        "courier_start": plan.courier_start,
        "total_time": plan.total_time,
        "unoptimized_time": round(unoptimized_time, 1),
        "time_saved": time_saved,
        "savings_percent": savings_pct,
        "delivery_sequence": plan.delivery_sequence,
        "steps": [
            {
                "step": idx,
                "action": step.action,
                "order_id": step.order_id,
                "from_node": step.from_node,
                "to_node": step.to_node,
                "path": step.path,
                "travel_time": step.travel_time,
            }
            for idx, step in enumerate(plan.steps, start=1)
        ],
    }


def run_live_benchmark_payload() -> dict[str, Any]:
    """Run fast live complexity benchmarks for the browser presentation tab."""
    rng = random.Random(42)
    pq_results: list[dict[str, Any]] = []
    for size in (100, 500, 1_000, 2_500):
        values = [rng.uniform(1.0, 10_000.0) for _ in range(size)]
        heap: MinHeap[int] = MinHeap()
        t0 = time.perf_counter()
        for idx, prio in enumerate(values):
            heap.push(prio, idx)
        while not heap.is_empty():
            heap.pop()
        heap_ms = (time.perf_counter() - t0) * 1000.0

        linear = LinearPriorityQueue()
        t1 = time.perf_counter()
        for idx, prio in enumerate(values):
            linear.push(prio, idx)
        while not linear.is_empty():
            linear.pop()
        linear_ms = (time.perf_counter() - t1) * 1000.0
        pq_results.append(
            {
                "n": size,
                "minheap_ms": round(heap_ms, 3),
                "linear_ms": round(linear_ms, 3),
            }
        )

    graph_results: list[dict[str, Any]] = []
    for side in (10, 20, 30, 40, 50):
        grid = generate_city_grid_graph(side)
        v_count = grid.node_count()
        t0 = time.perf_counter()
        dijkstra_all_distances(grid, "N_0_0")
        heap_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        naive_dijkstra_all_distances(grid, "N_0_0")
        naive_ms = (time.perf_counter() - t1) * 1000.0

        graph_results.append(
            {
                "v": v_count,
                "e": grid.edge_count(),
                "minheap_ms": round(heap_ms, 3),
                "naive_ms": round(naive_ms, 3),
                "v_log_v": round(v_count * math.log2(v_count), 1),
            }
        )

    return {"priority_queue": pq_results, "dijkstra": graph_results}


class RoutingRequestHandler(BaseHTTPRequestHandler):
    """Serve static frontend assets and JSON routing API endpoints."""

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _serve_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found.")
            return
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/static/style.css":
            self._serve_file(STATIC_DIR / "style.css", "text/css; charset=utf-8")
        elif path == "/static/app.js":
            self._serve_file(
                STATIC_DIR / "app.js", "application/javascript; charset=utf-8"
            )
        elif path == "/api/map/sample":
            self._send_json(HTTPStatus.OK, build_sample_map_payload())
        elif path == "/api/benchmark":
            self._send_json(HTTPStatus.OK, run_live_benchmark_payload())
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
            return

        if path == "/api/map/random":
            seed = body.get("seed")
            self._send_json(HTTPStatus.OK, create_random_map_payload(seed=seed))
        elif path == "/api/optimize":
            try:
                result = optimize_payload(body)
                self._send_json(HTTPStatus.OK, result)
            except (ValueError, KeyError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    """Start the interactive web presentation server."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), RoutingRequestHandler)
    print(f"Interactive Route Optimizer running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    main()
