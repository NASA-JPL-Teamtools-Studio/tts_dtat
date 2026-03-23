import pytest
import pandas as pd
from tts_dtat import commonchartfuncs

def test_get_plotly_marker_values_defaults():
    """Test that an empty dictionary gets populated with default marker values."""
    #
    # Input is an empty dict (typed as CustomizedTrace)
    custom_trace = {}
    
    marker = commonchartfuncs.get_plotly_marker_values(custom_trace)
    
    # Check defaults applied
    assert marker["color"] == "#000000"
    assert marker["symbol"] == "circle"
    assert marker["size"] == 8
    assert marker["showscale"] is False
    # Line width defaults to 0.5 when z_var is None
    assert marker["line"]["width"] == 1.0
    # Line color should be derived from palette (Black #000000 -> Black #000000)
    assert marker["line"]["color"] == "#000000"

def test_get_plotly_marker_values_custom():
    """Test that provided values are preserved."""
    custom_trace = {
        "color": "#FF0000",
        "symbol": "square",
        "size": 10,
        "showscale": True
    }
    
    marker = commonchartfuncs.get_plotly_marker_values(custom_trace)
    
    assert marker["color"] == "#FF0000"
    assert marker["symbol"] == "square"
    assert marker["size"] == 10
    assert marker["showscale"] is True

def test_get_plotly_marker_values_with_zvar():
    """Test behavior when a z_var (color dimension) is present."""
    custom_trace = {
        "z_var": "temperature"
    }
    
    marker = commonchartfuncs.get_plotly_marker_values(custom_trace)
    
    #
    # If z_var is present, line width should be 0 (no outline)
    assert marker["line"]["width"] == 0

def test_elapsed_seconds_to_dt_str():
    """Test conversion of seconds since 2018-01-01 to datetime string."""
    #
    # 0 seconds -> 2018-01-01T00:00:00
    assert commonchartfuncs.elapsed_seconds_to_dt_str(0) == "2018-001T00:00:00"
    
    # 1 hour -> 3600 seconds
    assert commonchartfuncs.elapsed_seconds_to_dt_str(3600) == "2018-001T01:00:00"

def test_make_colorbar_dict_simple():
    """Test colorbar creation when no Z variable is involved."""
    data = pd.DataFrame()
    colorbar = commonchartfuncs.make_colorbar_dict(data, None, None, "#000000")
    
    assert colorbar["title"] is None
    # Should not have tick configuration
    assert "tickmode" not in colorbar

def test_make_colorbar_dict_time_type():
    """Test colorbar creation for time-based Z variables."""
    #
    # Requires 'elapsed_seconds' column and a z_var recognized as time (like 'scet')
    data = pd.DataFrame({
        "scet": pd.to_datetime(["2018-01-01 00:00:00", "2018-01-01 06:00:00"]),
        "elapsed_seconds": [0.0, 21600.0] # 0 to 6 hours
    })
    
    colorbar = commonchartfuncs.make_colorbar_dict(data, "scet", "elapsed_seconds", None)
    
    assert colorbar["title"] == "scet"
    assert colorbar["tickmode"] == "array"
    assert len(colorbar["tickvals"]) == 7 # logic creates 6 steps (7 ticks)
    # Check first and last label
    assert colorbar["ticktext"][0] == "2018-001T00:00:00"
    assert colorbar["ticktext"][-1] == "2018-001T06:00:00"

def test_make_colorbar_dict_bins():
    """Test colorbar creation when color is a list (discrete bins)."""
    #
    # When color is a list, it iterates through bins
    data = pd.DataFrame({
        "z_val_col": [0, 100]
    })
    
    # Mocking the color list structure used in palette.make_discrete_colorscale
    # List of (value, color) tuples usually
    bins_color_list = [(0.5, "red")] 
    
    colorbar = commonchartfuncs.make_colorbar_dict(data, "some_z", "z_val_col", bins_color_list)
    
    assert colorbar["tickmode"] == "array"
    # bin_min (0) -> '0.000'
    assert colorbar["tickvals"][0] == '0.000'
    # bin_max (100) -> '100.000'
    assert colorbar["tickvals"][-1] == '100.000'

def test_make_colorbar_dict_categorical():
    """Test colorbar creation for categorical (string) data."""
    #
    # FIX: Define dtype in constructor or use .astype() on DataFrame to avoid ChainedAssignmentError warning
    data = pd.DataFrame({
        "mode": ["ON", "OFF", "ON"],
        "z_numeric": [1, 0, 1]
    })
    data = data.astype({"mode": "string"})
    
    colorbar = commonchartfuncs.make_colorbar_dict(data, "mode", "z_numeric", None)
    
    assert colorbar["tickmode"] == "array"
    # Should use z_numeric unique values for position
    assert set(colorbar["tickvals"]) == {0, 1}
    # Should use actual string values for labels
    assert set(colorbar["ticktext"]) == {"ON", "OFF"}