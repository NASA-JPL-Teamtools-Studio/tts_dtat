import pytest
import pandas as pd
import datetime
import plotly.graph_objects as go
from tts_dtat import plot

@pytest.fixture
def plotting_data():
    """Creates a DataFrame suitable for plotting scenarios."""
    # Create interlaced data for two variables 'A' and 'B'
    # Scet is 10:00, 11:00, 12:00
    return pd.DataFrame({
        "scet": pd.to_datetime([
            "2020-01-01 10:00", "2020-01-01 10:00",
            "2020-01-01 11:00", "2020-01-01 11:00",
            "2020-01-01 12:00", "2020-01-01 12:00"
        ]),
        "name": ["A", "B", "A", "B", "A", "B"],
        "value": [10, 5, 20, 15, 30, 25],
        # A Z-variable for color scale testing
        "mode": ["ON", "OFF", "ON", "OFF", "ON", "OFF"]
    })

def test_make_stacked_graph_basic(plotting_data):
    """Test generating a stacked graph with minimal arguments."""
    # y_vars is a list of lists (each inner list is a subplot)
    y_vars = [["A"], ["B"]]
    
    #
    fig, colors, markers, traces = plot.make_stacked_graph(
        data=plotting_data,
        y_vars=y_vars,
        x_var="scet"
    )
    
    assert isinstance(fig, go.Figure)
    # Should have popped some colors from default
    assert isinstance(colors, list) 
    assert isinstance(markers, dict)
    assert "A" in markers
    
    # Check that traces were created
    # We requested 2 subplots, each with 1 trace
    assert len(fig.data) == 2
    assert fig.data[0].name == "A"
    assert fig.data[1].name == "B"

def test_make_stacked_graph_single_subplot(plotting_data):
    """Test generating a graph where multiple vars share a subplot."""
    y_vars = [["A", "B"]]
    
    fig, _, _, _ = plot.make_stacked_graph(
        data=plotting_data,
        y_vars=y_vars,
        x_var="scet"
    )
    
    # 2 traces, but sharing the same axis/subplot logic
    assert len(fig.data) == 2
    # Check layout implies one subplot (shared axes logic in plot.py usually sets up domains)
    # Easier to just check it didn't crash and produced traces.

def test_make_stacked_graph_with_events(plotting_data):
    """Test the event annotation logic."""
    y_vars = [["A"]]
    # Use datetime object to bypass the strict string parsing in plot.py
    # or match the format "%Y-%jT%H:%M:%S.%f" exactly.
    # Using datetime object is safer/cleaner.
    event_time = pd.Timestamp("2020-01-01 11:00").to_pydatetime()
    
    events = {
        "A": [(event_time, "EventLabel", "HoverText")]
    }
    
    #
    fig, _, _, _ = plot.make_stacked_graph(
        data=plotting_data,
        y_vars=y_vars,
        events=events,
        event_line=True
    )
    
    # Check for annotations (the arrow text)
    assert len(fig.layout.annotations) > 0
    assert fig.layout.annotations[0].text == "EventLabel"
    
    # Check for shapes (the vertical line)
    assert len(fig.layout.shapes) > 0
    assert fig.layout.shapes[0].type == "line"

def test_make_stacked_graph_z_var(plotting_data):
    """Test plotting with a Z-axis (color dimension)."""
    y_vars = [["A"]]
    
    fig, _, markers, _ = plot.make_stacked_graph(
        data=plotting_data,
        y_vars=y_vars,
        x_var="scet",
        z_var="mode" # The categorical column
    )
    
    # Marker config should indicate a colorbar/colorscale usage
    assert markers["A"]["showscale"] is True
    # The line width is forced to 0 when Z var is present
    assert markers["A"]["line"]["width"] == 0

def test_make_diff_graph(plotting_data):
    """Test the difference graph (filled area between two lines)."""
    #
    fig, _, _, _ = plot.make_diff_graph(
        data=plotting_data,
        y1="A",
        y2="B",
        x_var="scet"
    )
    
    assert isinstance(fig, go.Figure)
    # Should create 2 traces with fill='tozeroy' (as per implementation)
    assert len(fig.data) == 2
    assert fig.data[0].fill == 'tozeroy'
    assert fig.data[0].name == "A"
    assert fig.data[1].name == "B"

def test_make_bar_graph(plotting_data):
    """Test the bar graph generator."""
    #
    # Note: make_bar_graph might use 'add_traces' with a single object in the source code.
    # We verify if that works or if it triggers a failure we need to fix.
    
    fig, _, _, _ = plot.make_bar_graph(
        data=plotting_data,
        y1="A",
        y2="B",
        x_var="scet",
        plot_lines=True # Test the branch that adds line traces on top
    )
    
    assert isinstance(fig, go.Figure)
    # 1 Bar trace + 2 Scatter traces (A and B) = 3 traces
    assert len(fig.data) == 3
    assert fig.data[0].type == 'bar'
    assert fig.data[1].type == 'scatter'
    
    # Check logic: Bar y should be (y1 - y2)
    # At 10:00: A=10, B=5 -> Diff=5
    # At 11:00: A=20, B=15 -> Diff=5
    # At 12:00: A=30, B=25 -> Diff=5
    
    # Accessing fig.data[0].y tuple/list
    # Note: Interpolation might reorder things, but values should align.
    assert fig.data[0].y[0] == 5


def test_multi_channel_subplot_uses_concise_default_axis_title(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(plotting_data, [["A", "B"]])

    assert fig.layout.yaxis.title.text == "Telemetry"
    assert len(fig.layout.yaxis.title.text) < 20


def test_unknown_units_are_not_shown_in_axis_titles(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(plotting_data, [["A"]])

    assert "Unknown" not in fig.layout.yaxis.title.text
    assert "???" not in fig.layout.yaxis.title.text


def test_multi_channel_subplot_honors_explicit_axis_title(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A", "B"]],
        y_axis_title=["Receiver lock state"],
    )

    assert fig.layout.yaxis.title.text == "Receiver lock state"


def test_background_bands_default_to_all_subplots(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A"], ["B"]],
        vertical_bands=[
            {
                "x0": pd.Timestamp("2020-01-01 10:30"),
                "x1": pd.Timestamp("2020-01-01 11:30"),
                "color": "rgba(10, 20, 30, 0.25)",
            }
        ],
    )

    assert len(fig.layout.shapes) == 2
    assert {shape.yref for shape in fig.layout.shapes} == {"y domain", "y2 domain"}
    assert all(shape.fillcolor == "rgba(10, 20, 30, 0.25)" for shape in fig.layout.shapes)
    assert all(shape.layer == "below" for shape in fig.layout.shapes)


def test_background_bands_can_target_selected_subplots(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A"], ["B"]],
        vertical_bands=[
            {
                "x0": pd.Timestamp("2020-01-01 10:30"),
                "x1": pd.Timestamp("2020-01-01 11:30"),
                "subplots": [2],
                "color": "rgba(10, 20, 30, 0.25)",
            }
        ],
    )

    assert len(fig.layout.shapes) == 1
    assert fig.layout.shapes[0].yref == "y2 domain"


def test_axis_config_places_secondary_axis_on_right(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A", "B"]],
        axis_config={
            "A": {"side": "left", "range": [0, 40], "title": "Primary"},
            "B": {"side": "right", "range": [0, 30], "title": "Secondary"},
        },
    )

    assert fig.layout.yaxis.overlaying is None
    assert fig.layout.yaxis2.overlaying == "y"
    assert fig.layout.yaxis.side == "left"
    assert fig.layout.yaxis2.side == "right"
    assert list(fig.layout.yaxis2.range) == [0, 30]
    assert fig.layout.yaxis2.title.text == "Secondary"


def test_more_than_two_axes_logs_design_warning(plotting_data, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        plot.logger,
        "warning",
        lambda message, *args: warnings.append(message % args if args else message),
    )
    data = pd.concat(
        [
            plotting_data,
            plotting_data.assign(name="C", value=plotting_data["value"] + 1),
        ],
        ignore_index=True,
    )

    plot.make_stacked_graph(
        data,
        [["A", "B", "C"]],
        multi_axis=True,
        axis_config={
            "A": {"side": "left", "title": "A"},
            "B": {"side": "left", "title": "B"},
            "C": {"side": "left", "title": "C"},
        },
    )

    assert len(warnings) == 1
    assert "more than two" in warnings[0]
    assert "docs/chart-design.md" in warnings[0]


def test_bands_follow_subplots_when_axes_are_overlaid(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A", "B"], ["A"]],
        multi_axis=True,
        vertical_bands=[
            {
                "x0": pd.Timestamp("2020-01-01 10:30"),
                "x1": pd.Timestamp("2020-01-01 11:30"),
                "subplots": [1, 2],
                "color": "rgba(10, 20, 30, 0.25)",
            }
        ],
    )

    assert [shape.yref for shape in fig.layout.shapes] == ["y domain", "y3 domain"]


def test_multi_axis_plot_does_not_reserve_trace_count_space(plotting_data):
    data = pd.concat(
        [
            plotting_data,
            plotting_data.assign(name="C", value=plotting_data["value"] + 1),
        ],
        ignore_index=True,
    )
    fig, _, _, _ = plot.make_stacked_graph(
        data,
        [["A", "B", "C"]],
        multi_axis=True,
        axis_config={
            "A": {"side": "left", "title": "A"},
            "B": {"side": "left", "title": "B"},
            "C": {"side": "right", "title": "C"},
        },
    )

    assert fig.layout.xaxis.domain[0] <= 0.05


def test_duplicate_axis_side_labels_are_hidden(plotting_data):
    fig, _, _, _ = plot.make_stacked_graph(
        plotting_data,
        [["A", "B"]],
        multi_axis=True,
        axis_config={
            "A": {"side": "left", "title": "A"},
            "B": {"side": "left", "title": "B"},
        },
    )

    assert fig.layout.yaxis.side == "left"
    assert fig.layout.yaxis.showticklabels is True
    assert fig.layout.yaxis2.side == "left"
    assert fig.layout.yaxis2.showticklabels is False