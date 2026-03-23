import pytest
import pandas as pd
from tts_dtat import demo_data

def test_make_time_col_defaults():
    """Test generating time column with default settings."""
    times = demo_data.make_time_col()
    
    # Default length is 1000
    assert len(times) == 1000
    # Should be pandas Timestamps
    assert isinstance(times[0], pd.Timestamp)
    # Should be strictly increasing
    assert times[1] > times[0]

def test_make_time_col_custom_length():
    """Test generating time column with custom length."""
    length = 50
    times = demo_data.make_time_col(length=length)
    assert len(times) == length

def test_instrument_turn_on():
    """Test the instrument_turn_on data generator."""
    df = demo_data.instrument_turn_on()
    
    assert isinstance(df, pd.DataFrame)
    # Structure defined in demo_data.py: 3000 rows (1000 for each of 3 vars)
    assert len(df) == 3000
    
    expected_cols = ["scet", "name", "value", "unit"]
    for col in expected_cols:
        assert col in df.columns
        
    # Check that expected states exist
    states = df["name"].unique()
    assert "Voltage" in states
    assert "Current" in states
    assert "Mode" in states
    
    # Check "Mode" values specifically (should contain TEST, INIT, OPERATIONAL)
    mode_values = df[df["name"] == "Mode"]["value"].unique()
    assert "TEST" in mode_values
    assert "OPERATIONAL" in mode_values

def test_drifting_off_nominal():
    """Test the drifting_off_nominal data generator."""
    df = demo_data.drifting_off_nominal()
    
    assert isinstance(df, pd.DataFrame)
    # 3000 rows
    assert len(df) == 3000
    
    expected_cols = ["scet", "name", "value"]
    for col in expected_cols:
        assert col in df.columns
        
    # Check unique states
    states = df["name"].unique()
    assert "Voltage" in states
    assert "Current" in states
    assert "Mode" in states
    
    # Check numeric values for Voltage are floats (not strings)
    voltage_data = df[df["name"] == "Voltage"]["value"]
    # The generator creates floats
    assert pd.api.types.is_float_dtype(voltage_data) or isinstance(voltage_data.iloc[0], float)