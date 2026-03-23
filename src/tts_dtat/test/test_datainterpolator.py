import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from tts_dtat import datainterpolator

@pytest.fixture
def sample_data():
    """Creates a simple dataframe for testing interpolation."""
    return pd.DataFrame({
        "scet": pd.to_datetime(["2023-01-01 12:00", "2023-01-01 12:01", "2023-01-01 12:02"]),
        "name": ["Voltage", "Voltage", "Voltage"],
        "value": [1.0, np.nan, 3.0],
        # A column that simulates a state with gaps
        "mode": ["A", None, "B"] 
    })

def test_make_column_values_existing_clean(sample_data):
    """Test that existing valid numeric columns are left alone."""
    # Setup data where the column 'Voltage' already exists and is full
    df = sample_data.copy()
    df["Voltage"] = [1.0, 2.0, 3.0]
    df["z_numeric"] = [1.0, 2.0, 3.0]
    
    interpolator = datainterpolator.DefaultInterpolator(df)
    # - Should short circuit
    result = interpolator.make_column_values("Voltage")
    
    pd.testing.assert_frame_equal(df, result)

def test_make_column_values_time_elapsed(sample_data):
    """Test conversion of time column to elapsed seconds."""
    df = sample_data.copy()
    interpolator = datainterpolator.DefaultInterpolator(df)
    
    # 'scet' is a known time type in datachecker
    result = interpolator.make_column_values("scet", elapsed_seconds=True)
    
    assert "elapsed_seconds" in result.columns
    # Check values: 2023-01-01 vs 2018-01-01 reference date
    # Just check that it calculated floats and they are increasing
    assert result["elapsed_seconds"].dtype == float
    assert result["elapsed_seconds"].iloc[1] > result["elapsed_seconds"].iloc[0]

def test_make_num_col_from_state_numeric_interpolation(sample_data):
    """Test interpolation of numeric values (filling NaNs)."""
    # sample_data has a NaN in the middle of 'value'
    # We need to restructure it slightly to match how the code expects 'name'/'value' pairs
    # or just use the logic that looks for 'name' rows.
    
    # The code filters where data.name == state
    df = sample_data.copy()
    # Ensure value col has explicit None/NaN
    df.loc[1, "value"] = None
    
    interpolator = datainterpolator.DefaultInterpolator(df)
    
    # This should trigger make_num_col_from_state -> interpolate
    # It creates a new column named "Voltage"
    result = interpolator.make_column_values("Voltage")
    
    assert "Voltage" in result.columns
    assert "z_numeric" in result.columns
    
    # Pad then backfill logic
    # 1.0, None, 3.0 -> Pad -> 1.0, 1.0, 3.0
    expected_mid_value = 1.0 
    assert result["Voltage"].iloc[1] == expected_mid_value
    assert result["z_numeric"].iloc[1] == expected_mid_value

def test_make_num_col_from_state_string_mapping():
    """Test converting string states to numeric codes."""
    df = pd.DataFrame({
        "scet": pd.to_datetime(["2023-01-01 12:00", "2023-01-01 12:01", "2023-01-01 12:02"]),
        "name": ["Mode", "Mode", "Mode"],
        "value": ["OFF", "ON", "OFF"]
    })
    
    interpolator = datainterpolator.DefaultInterpolator(df)
    result = interpolator.make_column_values("Mode")
    
    assert "Mode" in result.columns
    assert "z_numeric" in result.columns
    
    # Should map unique strings to ints. 
    # Usually "OFF" -> 0, "ON" -> 1 (order of appearance)
    z_vals = result["z_numeric"].tolist()
    assert z_vals[0] == z_vals[2] # OFF should equal OFF
    assert z_vals[0] != z_vals[1] # OFF should not equal ON
    assert isinstance(z_vals[0], (int, float))

def test_make_num_vals_from_strings_logic():
    """Test the specific helper method for string-to-int conversion."""
    df = pd.DataFrame() # Empty df, just testing the method
    interpolator = datainterpolator.DefaultInterpolator(df)
    
    col_data = ["A", "B", "A", "C"]
    #
    # lookup: A=0, B=1, C=2
    result = interpolator.make_num_vals_from_strings(col_data)
    
    assert result == [0, 1, 0, 2]

def test_missing_state_returns_unmodified(sample_data):
    """Test behavior when requesting a state that doesn't exist."""
    interpolator = datainterpolator.DefaultInterpolator(sample_data)
    result = interpolator.make_column_values("NonExistentState")
    
    # Should return original data unmodified
    pd.testing.assert_frame_equal(sample_data, result)