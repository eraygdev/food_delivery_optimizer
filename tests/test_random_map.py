"""Tests for random 10x10 city map generation and sequential PNG saving."""

from pathlib import Path

from src.engine.random_map import build_random_grid_map, is_strongly_connected
from src.visualization.map_generator import (
    generate_and_plot_random_map,
    get_next_map_path,
)


def test_random_10x10_map_structure_and_connectivity() -> None:
    graph, coords = build_random_grid_map(
        rows=10,
        cols=10,
        num_restaurants=5,
        num_houses=8,
        one_way_ratio=0.22,
        seed=99,
    )

    assert graph.node_count() == 100
    assert len(coords) == 100
    assert graph.has_node("D0")
    for i in range(1, 6):
        assert graph.has_node(f"R{i}")
    for i in range(1, 9):
        assert graph.has_node(f"H{i}")

    assert is_strongly_connected(graph)

    # Verify at least some one-way streets exist (< 2 * 180 = 360 directed edges)
    assert graph.edge_count() < 360


def test_sequential_map_filenames_and_non_overwrite(tmp_path: Path) -> None:
    p1 = generate_and_plot_random_map(output_dir=tmp_path, seed=1)
    p2 = generate_and_plot_random_map(output_dir=tmp_path, seed=2)

    assert p1.name == "0001_map.png"
    assert p2.name == "0002_map.png"
    assert p1.exists() and p1.stat().st_size > 1_000
    assert p2.exists() and p2.stat().st_size > 1_000

    p1.unlink()
    assert get_next_map_path(tmp_path).name == "0003_map.png"
