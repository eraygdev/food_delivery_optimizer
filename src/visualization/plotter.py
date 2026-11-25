"""Generates PNG visualizations for the city route graph and complexity analysis."""

import math
from pathlib import Path
import random
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from src.benchmark.analyzer import (
    LinearPriorityQueue,
    generate_city_grid_graph,
    naive_dijkstra_all_distances,
)
from src.engine import OrderDispatcher, build_sample_city_graph
from src.engine.router import dijkstra_all_distances
from src.models import Order
from src.structures import Graph, MinHeap

NODE_COORDS: dict[str, tuple[float, float]] = {
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

NODE_COLORS: dict[str, str] = {
    "depot": "#2563EB",
    "restaurant": "#EA580C",
    "house": "#16A34A",
    "intersection": "#64748B",
}


def plot_route_map(
    output_path: Path,
    urgency_penalty: float = 4.0,
) -> Path:
    """Render the 11-node city graph and overlay the optimized multi-order route."""
    graph: Graph = build_sample_city_graph()
    dispatcher = OrderDispatcher(graph)
    dispatcher.add_order(
        Order(order_id="ORD-101", restaurant_id="R1", customer_id="H1", priority=2)
    )
    dispatcher.add_order(
        Order(order_id="ORD-102", restaurant_id="R2", customer_id="H4", priority=1)
    )
    dispatcher.add_order(
        Order(order_id="ORD-103", restaurant_id="R3", customer_id="H3", priority=3)
    )
    plan = dispatcher.optimize_route(
        courier_start="D0", urgency_penalty=urgency_penalty
    )

    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=150)
    ax.set_facecolor("#F8FAFC")

    # Draw base road network
    drawn_undirected: set[tuple[str, str]] = set()
    for u in graph.nodes():
        x1, y1 = NODE_COORDS[u]
        reverse_lookup: dict[str, set[str]] = {}
        for v, weight in graph.neighbors(u):
            x2, y2 = NODE_COORDS[v]
            if v not in reverse_lookup:
                reverse_lookup[v] = {nbr for nbr, _ in graph.neighbors(v)}
            is_bidirectional = u in reverse_lookup[v]

            if is_bidirectional:
                pair = tuple(sorted((u, v)))
                if pair in drawn_undirected:
                    continue
                drawn_undirected.add((pair[0], pair[1]))
                ax.plot([x1, x2], [y1, y2], color="#CBD5E1", linewidth=2.4, zorder=1)
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                ax.text(
                    mx,
                    my,
                    f"{int(weight)}m",
                    fontsize=8.5,
                    color="#334155",
                    ha="center",
                    va="center",
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#CBD5E1"},
                    zorder=2,
                )
            else:
                ax.annotate(
                    "",
                    xy=(x2, y2),
                    xytext=(x1, y1),
                    arrowprops={
                        "arrowstyle": "-|>,head_length=0.7,head_width=0.4",
                        "color": "#94A3B8",
                        "lw": 2.0,
                        "ls": "--",
                        "shrinkA": 18,
                        "shrinkB": 18,
                    },
                    zorder=1,
                )
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                ax.text(
                    mx,
                    my + 0.08,
                    f"{int(weight)}m (1-way)",
                    fontsize=8,
                    color="#B45309",
                    ha="center",
                    va="center",
                    bbox={
                        "boxstyle": "round,pad=0.2",
                        "fc": "#FEF3C7",
                        "ec": "#F59E0B",
                    },
                    zorder=2,
                )

    # Overlay optimized multi-order route legs
    leg_palette = ["#DC2626", "#9333EA", "#0284C7", "#0D9488", "#D97706", "#DB2777"]
    legend_lines: list[str] = []

    for step_idx, step in enumerate(plan.steps, start=1):
        color = leg_palette[(step_idx - 1) % len(leg_palette)]
        rad = 0.14 if step_idx % 2 == 1 else -0.14
        for i in range(len(step.path) - 1):
            p_start = NODE_COORDS[step.path[i]]
            p_end = NODE_COORDS[step.path[i + 1]]
            ax.annotate(
                "",
                xy=p_end,
                xytext=p_start,
                arrowprops={
                    "arrowstyle": "-|>,head_length=0.65,head_width=0.35",
                    "color": color,
                    "lw": 2.6,
                    "connectionstyle": f"arc3,rad={rad}",
                    "shrinkA": 18,
                    "shrinkB": 18,
                },
                zorder=3,
            )
        action_tag = "PICKUP" if step.action == "pickup" else "DELIVER"
        legend_lines.append(
            f"Step {step_idx} [{action_tag} {step.order_id}]: "
            f"{' -> '.join(step.path)} ({step.travel_time:.0f}m)"
        )

    # Draw graph vertices
    for node_id in graph.nodes():
        x, y = NODE_COORDS[node_id]
        node_type = graph.get_node_data(node_id).get("node_type", "intersection")
        fill = NODE_COLORS.get(node_type, "#64748B")
        ax.scatter(
            x,
            y,
            s=950,
            c=fill,
            edgecolors="white",
            linewidths=2.5,
            zorder=4,
        )
        ax.text(
            x,
            y,
            node_id,
            color="white",
            fontsize=10,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=5,
        )

    # Legend and route itinerary summary
    node_handles = [
        mpatches.Patch(color=NODE_COLORS["depot"], label="Depot / Start (D0)"),
        mpatches.Patch(color=NODE_COLORS["restaurant"], label="Restaurants (R1-R3)"),
        mpatches.Patch(color=NODE_COLORS["house"], label="Houses (H1-H4)"),
        mpatches.Patch(
            color=NODE_COLORS["intersection"], label="Intersections (I1-I3)"
        ),
    ]
    ax.legend(handles=node_handles, loc="upper right", frameon=True, facecolor="white")

    itinerary_text = (
        "\n".join(legend_lines) + f"\nTotal Optimized Time: {plan.total_time:.1f} min"
    )
    ax.text(
        0.02,
        -0.16,
        itinerary_text,
        transform=ax.transAxes,
        fontsize=8.5,
        family="monospace",
        va="top",
        bbox={"boxstyle": "round,pad=0.5", "fc": "#F1F5F9", "ec": "#CBD5E1"},
    )

    ax.set_title(
        f"Food Delivery Route Optimization (11-Node Directed Graph | urgency_penalty={urgency_penalty})",
        fontsize=13,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlim(-0.45, 3.55)
    ax.set_ylim(-0.45, 2.45)
    ax.axis("off")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_efficiency_charts(
    output_path: Path,
    pq_sizes: tuple[int, ...] = (100, 500, 1_000, 2_500, 5_000),
    grid_sides: tuple[int, ...] = (10, 20, 30, 40, 50, 70, 100),
) -> Path:
    """Benchmark MinHeap and Dijkstra scaling and render comparative complexity plots."""
    rng = random.Random(42)
    pq_heap_ms: list[float] = []
    pq_linear_ms: list[float] = []

    for size in pq_sizes:
        values = [rng.uniform(1.0, 10_000.0) for _ in range(size)]
        heap: MinHeap[int] = MinHeap()
        t0 = time.perf_counter()
        for idx, prio in enumerate(values):
            heap.push(prio, idx)
        while not heap.is_empty():
            heap.pop()
        pq_heap_ms.append((time.perf_counter() - t0) * 1000.0)

        linear = LinearPriorityQueue()
        t1 = time.perf_counter()
        for idx, prio in enumerate(values):
            linear.push(prio, idx)
        while not linear.is_empty():
            linear.pop()
        pq_linear_ms.append((time.perf_counter() - t1) * 1000.0)

    v_counts: list[int] = []
    dijk_heap_ms: list[float] = []
    naive_v_counts: list[int] = []
    dijk_naive_ms: list[float] = []

    for side in grid_sides:
        graph = generate_city_grid_graph(side)
        v_count = graph.node_count()
        v_counts.append(v_count)

        t0 = time.perf_counter()
        dijkstra_all_distances(graph, "N_0_0")
        dijk_heap_ms.append((time.perf_counter() - t0) * 1000.0)

        if v_count <= 2_500:
            t1 = time.perf_counter()
            naive_dijkstra_all_distances(graph, "N_0_0")
            dijk_naive_ms.append((time.perf_counter() - t1) * 1000.0)
            naive_v_counts.append(v_count)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=150)

    ax1.plot(
        pq_sizes,
        pq_heap_ms,
        marker="o",
        lw=2.2,
        color="#16A34A",
        label="MinHeap: O(N log N)",
    )
    ax1.plot(
        pq_sizes,
        pq_linear_ms,
        marker="s",
        lw=2.2,
        color="#DC2626",
        label="Linear Scan: O(N^2)",
    )
    ax1.set_title("Priority Queue: MinHeap vs Linear Scan")
    ax1.set_xlabel("Number of Operations (N)")
    ax1.set_ylabel("Total Execution Time (ms)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    ax2.plot(
        v_counts,
        dijk_heap_ms,
        marker="o",
        lw=2.2,
        color="#2563EB",
        label="MinHeap Dijkstra: O((V+E) log V)",
    )
    ax2.plot(
        naive_v_counts,
        dijk_naive_ms,
        marker="s",
        lw=2.2,
        color="#EA580C",
        label="Naive Dijkstra: O(V^2)",
    )
    ax2.set_title("Shortest Path Scaling Across City Grids")
    ax2.set_xlabel("Number of Vertices (V)")
    ax2.set_ylabel("Execution Time (ms)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    # Add theoretical logarithmic ratio callout
    if len(pq_sizes) >= 2 and pq_heap_ms[0] > 0:
        theo_ratio = math.log2(pq_sizes[-1]) / math.log2(pq_sizes[0])
        fig.suptitle(
            f"Logarithmic Efficiency Analysis (log2({pq_sizes[-1]}) / log2({pq_sizes[0]}) = {theo_ratio:.2f}x per-op growth)",
            fontsize=12.5,
            fontweight="bold",
        )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    """Generate all project visualizations into outputs/."""
    out_dir = Path("outputs")
    route_img = plot_route_map(out_dir / "route_map.png")
    eff_img = plot_efficiency_charts(out_dir / "efficiency_analysis.png")
    print(f"Generated: {route_img}")
    print(f"Generated: {eff_img}")


if __name__ == "__main__":
    main()
