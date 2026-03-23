import pytest
from collections.abc import MutableMapping
from tts_dtat import types

def test_line_type():
    """Test Line TypedDict structure."""
    # TypedDicts are essentially dicts at runtime, but this verifies 
    # the definition exists and allows standard dict usage.
    line: types.Line = {"width": 1.0, "color": "#000000"}
    assert line["width"] == 1.0
    assert line["color"] == "#000000"
    assert isinstance(line, dict)

def test_customized_trace_type():
    """Test CustomizedTrace TypedDict structure."""
    # Create a partial or full dictionary matching the type
    trace: types.CustomizedTrace = {
        "size": 5,
        "symbol": "circle",
        "color": "blue",
        "colorscale": "Viridis",
        "showscale": True,
        "line": {"width": 1.0, "color": "black"},
        "z_var": "some_var",
        "mode": "markers"
    }
    assert trace["size"] == 5
    assert trace["line"]["width"] == 1.0
    assert trace["showscale"] is True

def test_customized_marker_type():
    """Test CustomizedMarker TypedDict structure."""
    marker: types.CustomizedMarker = {
        "size": 10,
        "symbol": "square",
        "color": "red",
        "colorscale": "Jet",
        "showscale": False,
        "line": {"width": 2.0, "color": "white"}
    }
    assert marker["color"] == "red"
    assert marker["line"]["color"] == "white"

def test_customization_options_type():
    """Test CustomizationOptions class properties."""
    # CustomizationOptions inherits from MutableMapping but defines no methods,
    # making it an abstract class primarily for type hinting.
    
    # Verify inheritance
    assert issubclass(types.CustomizationOptions, MutableMapping)
    
    # Verify that instantiation fails because it's abstract (missing __getitem__, etc.)
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        types.CustomizationOptions()