"""CLI tool to generate numbered 10x10 random city maps with optimized routes."""

from pathlib import Path
import random
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from src.engine.dispatcher import OrderDispatcher
from src.engine.random_map import build_random_grid_map
from src.models import Order

MAP_FILENAME_RE = re.compile(r"^(\d{4})_map\.png$")


def get_next_map_path(output_dir: Path) -> Path:
    """Return the next sequential NNNN_map.png path without overwriting existing files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    max_num = 0
    for entry in output_dir.iterdir():
        if entry.is_file():
            match = MAP_FILENAME_RE.match(entry.name)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return output_dir / f"{max_num + 1:04d}_map.png"


def generate_and_plot_random_map(
    output_dir: Path = Path("outputs"),
    seed: int | None = None,
    num_orders: int = 4,
) -> Path:
    """Create a random 10x10 city map, optimize random orders, and save NNNN_map.png."""
    rng = random.Random(seed)
    graph, coords = build_random_grid_map(
        rows=10,
        cols=10,
        num_restaurants=5,
        num_houses=8,
        one_way_ratio=0.22,
        seed=seed,
    )

    restaurants = [n for n in graph.nodes() if n.startswith("R")]
    houses = [n for n in graph.nodes() if n.startswith("H")]

    dispatcher = OrderDispatcher(graph)
    chosen_restaurants = rng.choices(restaurants, k=num_orders)
    chosen_houses = rng.sample(houses, k=min(num_orders, len(houses)))
    orders: list[Order] = []

    for i in range(len(chosen_houses)):
        order = Order(
            order_id=f"ORD-{i + 1}",
            restaurant_id=chosen_restaurants[i],
            customer_id=chosen_houses[i],
            priority=rng.randint(1, 3),
        )
        dispatcher.add_order(order)
        orders.append(order)

    plan = dispatcher.optimize_route(courier_start="D0", urgency_penalty=4.0)

    fig, ax = plt.subplots(figsize=(15, 13.5), dpi=150)
    ax.set_facecolor("#F8FAFC")

    drawn_undirected: set[tuple[str, str]] = set()
    one_way_count = 0

    for u in graph.nodes():
        x1, y1 = coords[u]
        for v, weight in graph.neighbors(u):
            x2, y2 = coords[v]
            reverse_neighbors = {nbr for nbr, _ in graph.neighbors(v)}
            if u in reverse_neighbors:
                pair = tuple(sorted((u, v)))
                if pair in drawn_undirected:
                    continue
                drawn_undirected.add((pair[0], pair[1]))
                ax.plot([x1, x2], [y1, y2], color="#CBD5E1", linewidth=1.6, zorder=1)
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                ax.text(
                    mx,
                    my,
                    f"{int(weight)}",
                    fontsize=6.5,
                    color="#475569",
                    ha="center",
                    va="center",
                    bbox={
                        "boxstyle": "round,pad=0.12",
                        "fc": "white",
                        "ec": "none",
                        "alpha": 0.85,
                    },
                    zorder=2,
                )
            else:
                one_way_count += 1
                ax.annotate(
                    "",
                    xy=(x2, y2),
                    xytext=(x1, y1),
                    arrowprops={
                        "arrowstyle": "-|>,head_length=0.5,head_width=0.28",
                        "color": "#F59E0B",
                        "lw": 1.5,
                        "ls": "--",
                        "shrinkA": 9,
                        "shrinkB": 9,
                    },
                    zorder=2,
                )
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                ax.text(
                    mx,
                    my,
                    f"{int(weight)}>",
                    fontsize=6.5,
                    color="#B45309",
                    ha="center",
                    va="center",
                    bbox={
                        "boxstyle": "round,pad=0.12",
                        "fc": "#FEF3C7",
                        "ec": "none",
                        "alpha": 0.9,
                    },
                    zorder=2,
                )

    # Overlay optimized route
    leg_palette = [
        "#DC2626",
        "#9333EA",
        "#0284C7",
        "#0D9488",
        "#D97706",
        "#DB2777",
        "#4F46E5",
        "#059669",
    ]
    legend_lines: list[str] = []

    for step_idx, step in enumerate(plan.steps, start=1):
        color = leg_palette[(step_idx - 1) % len(leg_palette)]
        rad = 0.16 if step_idx % 2 == 1 else -0.16
        for i in range(len(step.path) - 1):
            p_start = coords[step.path[i]]
            p_end = coords[step.path[i + 1]]
            ax.annotate(
                "",
                xy=p_end,
                xytext=p_start,
                arrowprops={
                    "arrowstyle": "-|>,head_length=0.55,head_width=0.3",
                    "color": color,
                    "lw": 2.3,
                    "connectionstyle": f"arc3,rad={rad}",
                    "shrinkA": 10,
                    "shrinkB": 10,
                },
                zorder=3,
            )
        tag = "PICKUP " if step.action == "pickup" else "DELIVER"
        legend_lines.append(
            f"Step {step_idx} [{tag} {step.order_id}]: {step.from_node} -> {step.to_node} ({step.travel_time:.0f}m)"
        )

    # Draw vertices by role
    for node_id in graph.nodes():
        x, y = coords[node_id]
        ntype = graph.get_node_data(node_id).get("node_type", "intersection")
        if ntype == "depot":
            ax.scatter(
                x, y, s=680, c="#2563EB", edgecolors="white", linewidths=2.2, zorder=5
            )
            ax.text(
                x,
                y,
                node_id,
                color="white",
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=6,
            )
        elif ntype == "restaurant":
            ax.scatter(
                x, y, s=560, c="#EA580C", edgecolors="white", linewidths=2.0, zorder=5
            )
            ax.text(
                x,
                y,
                node_id,
                color="white",
                fontsize=8.5,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=6,
            )
        elif ntype == "house":
            ax.scatter(
                x, y, s=560, c="#16A34A", edgecolors="white", linewidths=2.0, zorder=5
            )
            ax.text(
                x,
                y,
                node_id,
                color="white",
                fontsize=8.5,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=6,
            )
        else:
            ax.scatter(
                x, y, s=85, c="#64748B", edgecolors="white", linewidths=1.0, zorder=4
            )

    handles = [
        mpatches.Patch(color="#2563EB", label="Depot / Courier Start (D0)"),
        mpatches.Patch(color="#EA580C", label="Restaurants (R1-R5)"),
        mpatches.Patch(color="#16A34A", label="Houses (H1-H8)"),
        mpatches.Patch(color="#64748B", label="Intersections"),
        mpatches.Patch(color="#F59E0B", label=f"One-Way Streets ({one_way_count})"),
    ]
    ax.legend(
        handles=handles, loc="upper right", frameon=True, facecolor="white", fontsize=9
    )

    orders_summary = " | ".join(
        f"{o.order_id}:{o.restaurant_id}->{o.customer_id}(P{o.priority})"
        for o in orders
    )
    footer_text = (
        f"Orders: {orders_summary}\n"
        + "\n".join(legend_lines)
        + f"\nTotal Optimized Time: {plan.total_time:.1f} min"
    )
    ax.text(
        0.01,
        -0.02,
        footer_text,
        transform=ax.transAxes,
        fontsize=8,
        family="monospace",
        va="top",
        bbox={"boxstyle": "round,pad=0.45", "fc": "#F1F5F9", "ec": "#CBD5E1"},
    )

    out_path = get_next_map_path(output_dir)
    ax.set_title(
        f"Random 10x10 City Graph ({out_path.name}) | {graph.node_count()} Nodes, "
        f"{graph.edge_count()} Directed Edges ({one_way_count} One-Way)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlim(-0.6, 9.6)
    ax.set_ylim(-0.6, 9.6)
    ax.axis("off")

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    print(f"Created random 10x10 map: {out_path}")
    print(
        f"Nodes: {graph.node_count()} | Directed Edges: {graph.edge_count()} | One-Way Streets: {one_way_count}"
    )
    print(f"Orders: {orders_summary}")
    print(f"Optimized Total Time: {plan.total_time:.1f} min")
    return out_path


def main() -> None:
    """CLI entry point for generating a sequential 10x10 random map."""
    generate_and_plot_random_map()


if __name__ == "__main__":
    main()
