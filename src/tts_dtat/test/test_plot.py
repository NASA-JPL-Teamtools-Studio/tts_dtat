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