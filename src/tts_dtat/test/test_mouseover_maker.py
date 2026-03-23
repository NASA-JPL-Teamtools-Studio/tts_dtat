import pytest
import pandas as pd
from tts_dtat import mouseover_maker

@pytest.fixture
def sample_data():
    """Creates a simple dataframe for testing make_meta."""
    return pd.DataFrame({
        "scet": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "value": [10, 20, 30],
        "temperature": [98.6, 99.1, 98.4],
        "mode": ["A", "B", "A"]
    })

def test_default_hovertemplate():
    """Test the default hovertemplate string."""
    template = mouseover_maker.default_hovertemplate()
    assert "X: %{x}" in template
    assert "Y: %{y}" in template
    assert "<br>" in template

def test_make_meta_with_zvar(sample_data):
    """Test make_meta when a valid Z-variable is provided."""
    #
    meta = mouseover_maker.make_meta("temperature", sample_data)
    
    assert isinstance(meta, list)
    assert len(meta) == 3
    # Check structure: [z_value, scet_value]
    assert meta[0] == [98.6, "2023-01-01"]
    assert meta[1] == [99.1, "2023-01-02"]

def test_make_meta_without_zvar(sample_data):
    """Test make_meta when zvar is None."""
    #
    meta = mouseover_maker.make_meta(None, sample_data)
    
    assert isinstance(meta, list)
    assert len(meta) == 3
    # Check structure: [None, scet_value]
    assert meta[0] == [None, "2023-01-01"]

def test_make_meta_missing_zvar(sample_data):
    """Test make_meta when zvar is provided but not in columns."""
    # Should behave like None if column missing
    meta = mouseover_maker.make_meta("missing_col", sample_data)
    
    assert meta[0][0] is None
    assert meta[0][1] == "2023-01-01"

def test_ht_X_Y_Z_names_generic():
    """Test hovertemplate with generic (non-time) axes."""
    #
    template = mouseover_maker.ht_X_Y_Z_names(xaxis="Voltage", yaxis="Current", zaxis="Mode")
    
    # Verify axis labels are present
    assert "X: Voltage" in template
    assert "Y: Current" in template
    assert "Z: Mode" in template
    # Verify standard plotly formatting codes are used (no time formatting)
    assert "%{x}" in template
    assert "%{y}" in template
    # Should use meta[0] for Z
    assert "%{meta[0]}" in template

def test_ht_X_Y_Z_names_with_time():
    """Test hovertemplate when axes are time types."""
    # 'scet' is a known time type in datachecker
    template = mouseover_maker.ht_X_Y_Z_names(xaxis="scet", yaxis="value", zaxis=None)
    
    # Check for time formatting pipe
    assert "%{x|%Y-%jT%H:%M:%S.%L}" in template
    # Y axis is not time, should be standard
    assert "%{y}" in template
    # Z axis is None, should not be in string
    assert "Z:" not in template

def test_ht_X_Y_Z_time_names():
    """Test the time-specific hovertemplate generator."""
    #
    template = mouseover_maker.ht_X_Y_Z_time_names(xaxis="scet", yaxis="value", zaxis="temperature")
    
    # Should include X, Y, Z
    assert "X: scet" in template
    assert "Y: value" in template
    assert "Z: temperature" in template
    
    # Should explicitly include the Time: scet field at the bottom
    # derived from meta[1]
    assert "Time: scet: %{meta[1]|%Y-%jT%H:%M:%S.%L}" in template