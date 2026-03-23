import pytest
import pandas as pd
import datetime
from tts_dtat import datachecker

def test_constants_return_lists():
    """Test that the constant provider functions return lists."""
    assert isinstance(datachecker.header(), list)
    assert isinstance(datachecker.min_header(), list)
    assert isinstance(datachecker.valid_value_col_names(), list)
    assert isinstance(datachecker.valid_time_type_cols(), list)

def test_verify_header_valid():
    """Test verify_header with a valid DataFrame."""
    # Create a dataframe with the minimum required headers
    df = pd.DataFrame(columns=["scet", "name", "value"])
    # Should return True and not raise exception
    assert datachecker.verify_header(df) is True

def test_verify_header_invalid():
    """Test verify_header raises exception when columns are missing."""
    df = pd.DataFrame(columns=["scet", "name"]) # Missing 'value'
    with pytest.raises(Exception) as excinfo:
        datachecker.verify_header(df)
    assert "Invalid column headers" in str(excinfo.value)

def test_is_time_type():
    """Test identification of time-type column names."""
    # Known time types
    assert datachecker.is_time_type("scet") is True
    assert datachecker.is_time_type("ert") is True
    assert datachecker.is_time_type("doy") is True
    
    # Non-time types
    assert datachecker.is_time_type("value") is False
    assert datachecker.is_time_type("voltage") is False
    assert datachecker.is_time_type("random_string") is False

def test_make_datetime_column_standard():
    """Test converting standard format strings to datetime."""
    # Standard format: %Y-%jT%H:%M:%S.%f
    times = ["2020-001T12:00:00.123", "2020-001T12:00:01.456"]
    series = pd.Series(times)
    
    result = datachecker.make_datetime_column(series)
    
    assert pd.api.types.is_datetime64_any_dtype(result)
    assert result[0].year == 2020
    assert result[0].microsecond == 123000

def test_make_datetime_column_no_microseconds():
    """Test converting strings without microseconds."""
    # Format: %Y-%jT%H:%M:%S
    times = ["2020-001T12:00:00", "2020-001T12:00:01"]
    series = pd.Series(times)
    
    result = datachecker.make_datetime_column(series)
    
    assert pd.api.types.is_datetime64_any_dtype(result)
    assert result[0].second == 0

def test_make_datetime_column_mixed():
    """Test converting a mix of formats (with and without subseconds)."""
    # This triggers the fallback to handle_mixed_time_formats
    times = ["2020-001T12:00:00.123", "2020-001T12:00:01"]
    series = pd.Series(times)
    
    result = datachecker.make_datetime_column(series)
    
    assert pd.api.types.is_datetime64_any_dtype(result)
    assert result[0].microsecond == 123000
    assert result[1].second == 1

def test_handle_mixed_time_formats_direct():
    """Test the helper function for individual timestamps."""
    # Test with microseconds
    ts1 = "2023-001T01:00:00.500"
    dt1 = datachecker.handle_mixed_time_formats(ts1)
    assert isinstance(dt1, datetime.datetime)
    assert dt1.microsecond == 500000

    # Test without microseconds
    ts2 = "2023-001T01:00:00"
    dt2 = datachecker.handle_mixed_time_formats(ts2)
    assert isinstance(dt2, datetime.datetime)
    assert dt2.microsecond == 0

    # Test invalid format
    with pytest.raises(ValueError):
        datachecker.handle_mixed_time_formats("not-a-date")

def test_find_value_header():
    """Test finding the value column in a list of headers."""
    # Should find 'value'
    cols = ["scet", "name", "value", "unit"]
    assert datachecker.find_value_header(cols) == "value"
    
    # Should return None if 'value' is missing
    cols_missing = ["scet", "name", "data"]
    assert datachecker.find_value_header(cols_missing) is None