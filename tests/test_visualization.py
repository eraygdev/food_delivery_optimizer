"""Tests verifying headless PNG chart generation."""

from pathlib import Path

from src.visualization.plotter import plot_efficiency_charts, plot_route_map


def test_route_map_png_created(tmp_path: Path) -> None:
    out_file = tmp_path / "route_map.png"
    result = plot_route_map(out_file)
    assert result.exists()
    assert result.stat().st_size > 1_000


def test_efficiency_charts_png_created(tmp_path: Path) -> None:
    out_file = tmp_path / "efficiency.png"
    result = plot_efficiency_charts(
        out_file,
        pq_sizes=(50, 100),
        grid_sides=(5, 10),
    )
    assert result.exists()
    assert result.stat().st_size > 1_000
