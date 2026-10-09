import plotly.graph_objects as go

from tts_dtat import earth_surface, palette


def test_earth_surface_plot_basic_markers():
    """Two marker batches produce two named Scattergeo marker traces."""
    batches = {
        "Stations": {
            "lat": [1.0, 2.0],
            "lon": [3.0, 4.0],
            "text": ["A", "B"],
        },
        "Targets": {
            "lat": [5.0],
            "lon": [6.0],
            "text": ["C"],
        },
    }
    fig = earth_surface.earth_surface_plot(batches)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.data[0].name == "Stations"
    assert fig.data[1].name == "Targets"
    assert fig.data[0].mode == "markers"
    assert fig.data[1].mode == "markers"


def test_earth_surface_plot_line_batch():
    """A mode='lines' batch produces a lines trace with no required text."""
    batches = {
        "Ground Track": {
            "lat": [0.0, 1.0, 2.0],
            "lon": [0.0, 1.0, 2.0],
            "mode": "lines",
        },
    }
    fig = earth_surface.earth_surface_plot(batches)

    assert len(fig.data) == 1
    assert fig.data[0].mode == "lines"
    assert fig.data[0].hoverinfo == "skip"


def test_earth_surface_plot_line_batch_with_text():
    """A mode='lines' batch with text uses the lat/lon hovertemplate instead of skip."""
    batches = {
        "Ground Track": {
            "lat": [0.0, 1.0],
            "lon": [0.0, 1.0],
            "mode": "lines",
            "text": ["t0", "t1"],
        },
    }
    fig = earth_surface.earth_surface_plot(batches)

    assert fig.data[0].hoverinfo == "text"
    assert "%{text}" in fig.data[0].hovertemplate
    assert "%{lat}" in fig.data[0].hovertemplate


def test_earth_surface_plot_explicit_vs_auto_color():
    """An explicit marker color is preserved; an unspecified one is auto-assigned from the palette."""
    batches = {
        "Explicit": {
            "lat": [1.0],
            "lon": [1.0],
            "marker": {"color": "purple"},
        },
        "Auto": {
            "lat": [2.0],
            "lon": [2.0],
        },
    }
    fig = earth_surface.earth_surface_plot(batches)

    assert fig.data[0].marker.color == "purple"
    assert fig.data[1].marker.color in palette.get_default_colors()


def test_earth_surface_plot_hovertemplate_without_text():
    """Batches without text get a lat/lon-only hovertemplate."""
    batches = {
        "NoText": {
            "lat": [1.0],
            "lon": [1.0],
        },
    }
    fig = earth_surface.earth_surface_plot(batches)

    assert "%{text}" not in fig.data[0].hovertemplate
    assert "%{lat}" in fig.data[0].hovertemplate


def test_earth_surface_plot_projection_and_scope():
    """Projection type and geo scope are applied to the figure layout."""
    fig = earth_surface.earth_surface_plot(
        {"Pts": {"lat": [0.0], "lon": [0.0]}},
        projection="orthographic",
        plot_scope="usa",
    )

    assert fig.layout.geo.projection.type == "orthographic"
    assert fig.layout.geo.scope == "usa"
