"""Plotly Earth-surface (Scattergeo) plotting for named batches of points and lines."""
from typing import Dict, List, Optional

import plotly.graph_objects as go

import tts_dtat.commonchartfuncs as common
import tts_dtat.palette as palette
from tts_dtat.types import GeoBatch


def _hovertemplate(has_text: bool) -> str:
    if has_text:
        return "%{text}<br>(%{lat}°, %{lon}°)<extra></extra>"
    return "(%{lat}°, %{lon}°)<extra></extra>"


def earth_surface_plot(
    batches: Dict[str, GeoBatch],
    projection: str = "equirectangular",
    plot_scope: str = "world",
    land_color: str = "LightGreen",
    ocean_color: str = "LightBlue",
    lake_color: str = "royalblue",
    figure_title: Optional[str] = None,
    figure_width: int = 1100,
    figure_height: int = 600,
    unassigned_colors: Optional[List[str]] = None,
) -> go.Figure:
    """Plot named batches of points and/or lat/lon lines on an Earth map.

    Each entry in `batches` becomes one go.Scattergeo trace. Marker batches
    (mode="markers", the default) get hover text from `text`; the
    hovertemplate shows the label plus lat/lon, or just lat/lon when `text`
    is omitted. Line batches (mode="lines") draw a path through the given
    lat/lon vertices (e.g. an orbit ground track); by default they skip
    hover text (dense paths are impractical to label per-vertex) unless
    `text` is explicitly provided, in which case they use the same
    hovertemplate as marker batches.

    Batches without an explicit marker/line color are auto-assigned the
    next color from tts_dtat.palette, matching make_stacked_graph's
    behavior.

    Args:
        batches (Dict[str, GeoBatch]): Named batches to plot. Each key is
            used as the trace's legend name unless the batch sets `name`.
        projection (str, optional): Plotly geo projection type. Defaults to
            "equirectangular" (cylindrical).
        plot_scope (str, optional): Plotly geo scope. Defaults to "world".
        land_color (str, optional): Land fill color.
        ocean_color (str, optional): Ocean fill color.
        lake_color (str, optional): Lake fill color.
        figure_title (Optional[str], optional): Figure title.
        figure_width (int, optional): Figure width in pixels.
        figure_height (int, optional): Figure height in pixels.
        unassigned_colors (Optional[List[str]], optional): Palette colors
            available for auto-assignment. Defaults to the full default
            palette (tts_dtat.palette.get_default_colors()).

    Returns:
        go.Figure: The resulting Scattergeo figure.
    """
    if unassigned_colors is None:
        unassigned_colors = palette.get_default_colors()

    fig = go.Figure()

    for key, batch in batches.items():
        mode = batch.get("mode", "markers")
        text = batch.get("text")
        name = batch.get("name") or key

        if mode == "lines":
            line_config = dict(batch.get("line") or {})
            if "color" not in line_config or line_config["color"] is None:
                color, unassigned_colors = palette.pop_next_color(unassigned_colors)
                line_config["color"] = color
            fig.add_trace(go.Scattergeo(
                lat=batch["lat"],
                lon=batch["lon"],
                text=text,
                mode="lines",
                line=line_config,
                name=name,
                hoverinfo="skip" if text is None else "text",
                hovertemplate=_hovertemplate(text is not None) if text is not None else None,
            ))
            continue

        marker_config = dict(batch.get("marker") or {})
        if "color" not in marker_config or marker_config["color"] is None:
            color, unassigned_colors = palette.pop_next_color(unassigned_colors)
            marker_config["color"] = color
        marker = common.get_plotly_marker_values(marker_config)

        fig.add_trace(go.Scattergeo(
            lat=batch["lat"],
            lon=batch["lon"],
            text=text,
            mode="markers",
            marker=marker,
            name=name,
            hovertemplate=_hovertemplate(text is not None),
        ))

    fig.update_geos(
        projection=dict(type=projection),
        showland=True, landcolor=land_color,
        showocean=True, oceancolor=ocean_color,
        showlakes=True, lakecolor=lake_color,
        scope=plot_scope,
    )

    fig.update_layout(
        title=figure_title,
        width=figure_width,
        height=figure_height,
    )

    return fig
